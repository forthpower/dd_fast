#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workflow API
处理workflow文件上传和解析
"""

from flask import Blueprint, request, jsonify
from pathlib import Path
import sys
import json
import csv
import logging
from datetime import datetime

from feature.workflow import WorkflowParser
from feature.workflow.docx_reader import DocxReader
from feature.workflow.split_comparator import SplitComparator
from feature.feishu.backend.api.feishu_syncer import (
    sync_currency_maintenance_to_feishu,
    get_tenant_access_token as fetch_feishu_tenant_access_token,
    get_feishu_table_info_from_url as fetch_feishu_table_info,
)

# 添加上级目录到路径
current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir))

workflow_api = Blueprint('workflow_api', __name__)

FEISHU_TABLE_URL = "https://centurygames.feishu.cn/base/ZjWjbTdQQaX22VsaMQzcGSLbnyc?table=tblKHfdMJyrVonxS&view=vew9fRbXDD"
UPDATE_LOG_TABLE_URL = "https://centurygames.feishu.cn/base/ZjWjbTdQQaX22VsaMQzcGSLbnyc?table=tbl4vNZC0TvupOj9&view=vew4y8PbUr"
FEISHU_APP_ID = "cli_a99e862024e7100e"
FEISHU_APP_SECRET = "Yog0pVLeTiyjsfxtga7ltbxgd3uVbg0j"
CURRENCY_MAINTENANCE_DIR = str(current_dir / "currency_maintenance")
UPDATE_LOG_DIR = str(current_dir / "update log")


def _sync_currency_maintenance(logger, csv_file: str = None) -> None:
    try:
        access_token = fetch_feishu_tenant_access_token(FEISHU_APP_ID, FEISHU_APP_SECRET)
        table_info = fetch_feishu_table_info(FEISHU_TABLE_URL)
        synced = sync_currency_maintenance_to_feishu(
            csv_file=csv_file if csv_file else None,
            csv_dir=CURRENCY_MAINTENANCE_DIR if not csv_file else None,
            app_token=table_info["app_token"],
            table_id=table_info["table_id"],
            access_token=access_token,
            field_map=None,
        )
        if synced:
            logger.info("Feishu多维表格同步成功")
        else:
            logger.warning("Feishu多维表格同步失败")
    except Exception as exc:
        import traceback
        logger.error("Feishu多维表格同步异常: %s", exc, exc_info=True)
        logger.error("异常堆栈: %s", traceback.format_exc())


def _sync_update_log(logger, csv_file: str) -> None:
    """同步更新日志到飞书多维表格"""
    try:
        access_token = fetch_feishu_tenant_access_token(FEISHU_APP_ID, FEISHU_APP_SECRET)
        table_info = fetch_feishu_table_info(UPDATE_LOG_TABLE_URL)
        synced = sync_currency_maintenance_to_feishu(
            csv_file=csv_file,
            csv_dir=None,
            app_token=table_info["app_token"],
            table_id=table_info["table_id"],
            access_token=access_token,
            field_map=None,
        )
        if synced:
            logger.info("Feishu更新日志同步成功")
        else:
            logger.warning("Feishu更新日志同步失败")
    except Exception as exc:
        import traceback
        logger.error("Feishu更新日志同步异常: %s", exc, exc_info=True)
        logger.error("异常堆栈: %s", traceback.format_exc())


def load_should_keep_data() -> dict:
    """
    加载 should_keep 的数据（不符合删除条件的数据）
    
    Returns:
        should_keep 数据字典: {支付方式: {币种: [Adyen%, Stripe%, Airwallex%]}}
    """
    should_keep_data = {}
    payment_method_mapping = {
        'Card': 'CARD',
        'Apple Pay': 'AP',
        'Google Pay': 'GP'
    }
    
    current_dir = Path(__file__).parent.parent.parent
    changelog_dir = current_dir / "currency_maintenance"
    csv_files = list(changelog_dir.glob("*.csv"))
    
    if csv_files:
        latest_csv = max(csv_files, key=lambda f: f.stat().st_mtime)
        try:
            with open(latest_csv, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    payment_method = row.get('支付方式', '').strip()
                    currency = row.get('币种', '').strip()
                    network = row.get('Network', '').strip()
                    tokenized = row.get('Network Tokenized？', '').strip()
                    
                    if not payment_method or not currency:
                        continue
                    
                    # 判断是否符合删除条件（需要删除的）
                    should_delete = False
                    if payment_method == 'Apple Pay':
                        # 所有的 Apple Pay 都要删除
                        should_delete = True
                    elif payment_method == 'Card' and network == 'Mastercard Visa JCB':
                        # Network 为 Mastercard Visa JCB 的 Card 要删除
                        should_delete = True
                    elif payment_method == 'Google Pay' and network == '非Amex' and tokenized == 'TRUE':
                        # Network = 非Amex 且 Network Tokenized = TRUE 的 Google Pay 要删除
                        should_delete = True
                    
                    # 不符合删除条件的，保留下来
                    if not should_delete:
                        pm_key = payment_method_mapping.get(payment_method)
                        if pm_key:
                            try:
                                adyen = int(row.get('Adyen', '') or 0)
                                stripe = int(row.get('Stripe', '') or 0)
                                airwallex = int(row.get('Airwallex', '') or 0)
                                percentages = (adyen, stripe, airwallex)
                                
                                if pm_key not in should_keep_data:
                                    should_keep_data[pm_key] = {}
                                if currency not in should_keep_data[pm_key]:
                                    should_keep_data[pm_key][currency] = []
                                should_keep_data[pm_key][currency].append(percentages)
                            except (ValueError, TypeError):
                                pass
        except:
            pass
    
    return should_keep_data


def generate_simple_steps_description(changes, summary, merged_to_other=None, should_keep_data=None) -> str:
    """
    生成简化的步骤描述
    
    Args:
        changes: 变更列表（格式：{"action": "add/remove/modify", "payment_method": "...", "currency": "...", "old": [...], "new": [...]}）
        summary: 摘要信息
        merged_to_other: 被合并到"其他币种"的币种信息 {支付方式: [币种列表]}
        should_keep_data: should_keep 数据字典 {支付方式: {币种: [[Adyen%, Stripe%, Airwallex%], ...]}}
        
    Returns:
        简化的步骤描述字符串
    """
    if not changes and not merged_to_other:
        return "无需调整，配置已是最新状态"
    
    # 如果没有提供 should_keep_data，则加载
    if should_keep_data is None:
        should_keep_data = load_should_keep_data()
    
    # 支付方式显示名称映射
    payment_method_display = {
        "CARD": "CARD",
        "AP": "Apple Pay",
        "GP": "Google Pay"
    }
    
    # 按支付方式分组
    steps_by_method = {}
    
    # 统计各类操作
    adds = [c for c in changes if c.get("action") == "add"]
    removes = [c for c in changes if c.get("action") == "remove"]
    modifies = [c for c in changes if c.get("action") == "modify"]
    
    # 添加操作
    for change in adds:
        pm = change.get("payment_method", "")
        curr = change.get("currency", "")
        new_pct = change.get("new", [])
        if new_pct and len(new_pct) >= 3:
            if pm not in steps_by_method:
                steps_by_method[pm] = []
            
            # 查询 should_keep 数据中是否有相同的分量
            matching_currencies = set()
            if pm in should_keep_data:
                pct_tuple = tuple(new_pct)
                for keep_currency, keep_percentages_list in should_keep_data[pm].items():
                    for keep_pct in keep_percentages_list:
                        if tuple(keep_pct) == pct_tuple and keep_currency != curr:
                            matching_currencies.add(keep_currency)
            
            step_text = f"  添加 {curr}: Adyen {new_pct[0]}% | Stripe {new_pct[1]}% | Airwallex {new_pct[2]}%"
            if matching_currencies:
                step_text += f"（该分量与保留数据中的 {', '.join(sorted(matching_currencies))} 相同）"
            steps_by_method[pm].append(step_text)
    
    # 删除操作
    for change in removes:
        pm = change.get("payment_method", "")
        curr = change.get("currency", "")
        if pm not in steps_by_method:
            steps_by_method[pm] = []
        steps_by_method[pm].append(f"  删除 {curr}")
    
    # 修改操作
    for change in modifies:
        pm = change.get("payment_method", "")
        curr = change.get("currency", "")
        old_pct = change.get("old", [])
        new_pct = change.get("new", [])
        if old_pct and new_pct and len(old_pct) >= 3 and len(new_pct) >= 3:
            if pm not in steps_by_method:
                steps_by_method[pm] = []
            
            # 查询 should_keep 数据中是否有相同的分量
            matching_currencies = set()
            if pm in should_keep_data:
                pct_tuple = tuple(new_pct)
                for keep_currency, keep_percentages_list in should_keep_data[pm].items():
                    for keep_pct in keep_percentages_list:
                        if tuple(keep_pct) == pct_tuple and keep_currency != curr:
                            matching_currencies.add(keep_currency)
            
            step_text = f"  修改 {curr}: {old_pct[0]}:{old_pct[1]}:{old_pct[2]}% → {new_pct[0]}:{new_pct[1]}:{new_pct[2]}%"
            if matching_currencies:
                step_text += f"（该分量与保留数据中的 {', '.join(sorted(matching_currencies))} 相同）"
            steps_by_method[pm].append(step_text)
    
    # 合并操作
    summary_merge = summary.get("currencies_to_merge", [])
    for merge_info in summary_merge:
        pm = merge_info.get("payment_method", "")
        currencies = merge_info.get("currencies", [])
        if currencies:
            if pm not in steps_by_method:
                steps_by_method[pm] = []
            steps_by_method[pm].append(f"  合并 {', '.join(currencies)}")
    
    # 显示被合并到"其他币种"的币种
    if merged_to_other:
        for payment_method, currencies in merged_to_other.items():
            if currencies:
                if payment_method not in steps_by_method:
                    steps_by_method[payment_method] = []
                currencies_str = ', '.join(currencies)
                steps_by_method[payment_method].append(f"  {currencies_str}: 无需操作，被纳入其他币种之中")
    
    # 按支付方式组织输出
    result_lines = []
    # 按CARD、AP、GP的顺序输出
    payment_order = ["CARD", "AP", "GP"]
    for pm in payment_order:
        if pm in steps_by_method and steps_by_method[pm]:
            display_name = payment_method_display.get(pm, pm)
            result_lines.append(f"{display_name}")
            result_lines.extend(steps_by_method[pm])
            result_lines.append("")  # 空行分隔
    
    # 处理其他支付方式（如果有）
    for pm, steps in steps_by_method.items():
        if pm not in payment_order and steps:
            display_name = payment_method_display.get(pm, pm)
            result_lines.append(f"{display_name}")
            result_lines.extend(steps)
            result_lines.append("")
    
    # 移除最后的空行
    if result_lines and result_lines[-1] == "":
        result_lines.pop()
    
    return "\n".join(result_lines) if result_lines else "无需调整"


def format_comparison_result_as_text(old_config, new_config, changes, summary) -> str:
    """
    将对比结果格式化为文本格式
    
    Args:
        old_config: 旧配置
        new_config: 新配置
        changes: 变更列表
        summary: 摘要信息
        
    Returns:
        格式化的文本字符串
    """
    lines = []
    lines.append("=" * 60)
    lines.append("分量调整对比结果")
    lines.append("=" * 60)
    lines.append("")
    
    # 旧分量情况
    lines.append("【旧分量情况】")
    lines.append("-" * 60)
    for payment_method, currencies in sorted(old_config.items()):
        lines.append(f"\n{payment_method}:")
        for currency, percentages in sorted(currencies.items()):
            if percentages:
                lines.append(f"  {currency}: Adyen {percentages[0]}% | Stripe {percentages[1]}% | Airwallex {percentages[2]}%")
    lines.append("")
    
    # 新分量情况
    lines.append("【新分量情况】")
    lines.append("-" * 60)
    for payment_method, currencies in sorted(new_config.items()):
        lines.append(f"\n{payment_method}:")
        for currency, percentages in sorted(currencies.items()):
            if percentages:
                lines.append(f"  {currency}: Adyen {percentages[0]}% | Stripe {percentages[1]}% | Airwallex {percentages[2]}%")
    lines.append("")
    
    # 需要调整的币种
    if changes:
        lines.append("【需要调整的币种】")
        lines.append("-" * 60)
        
        # 按操作类型分组
        adds = [c for c in changes if c.get("action") == "add"]
        removes = [c for c in changes if c.get("action") == "remove"]
        modifies = [c for c in changes if c.get("action") == "modify"]
        
        if adds:
            lines.append("\n需要添加的币种:")
            for change in adds:
                pm = change.get("payment_method", "")
                curr = change.get("currency", "")
                new_pct = change.get("new", {}).get("percentages", [])
                if new_pct:
                    lines.append(f"  {pm} - {curr}: Adyen {new_pct[0]}% | Stripe {new_pct[1]}% | Airwallex {new_pct[2]}%")
        
        if removes:
            lines.append("\n需要删除的币种:")
            for change in removes:
                pm = change.get("payment_method", "")
                curr = change.get("currency", "")
                lines.append(f"  {pm} - {curr}")
        
        if modifies:
            lines.append("\n需要修改的币种:")
            for change in modifies:
                pm = change.get("payment_method", "")
                curr = change.get("currency", "")
                old_pct = change.get("current", {}).get("percentages", [])
                new_pct = change.get("new", {}).get("percentages", [])
                if old_pct and new_pct:
                    lines.append(f"  {pm} - {curr}:")
                    lines.append(f"    原来: Adyen {old_pct[0]}% | Stripe {old_pct[1]}% | Airwallex {old_pct[2]}%")
                    lines.append(f"    现在: Adyen {new_pct[0]}% | Stripe {new_pct[1]}% | Airwallex {new_pct[2]}%")
        
        lines.append("")
    
    # 调整摘要
    lines.append("【调整摘要】")
    lines.append("-" * 60)
    
    summary_add = summary.get("currencies_to_add", {})
    summary_remove = summary.get("currencies_to_remove", {})
    summary_modify = summary.get("currencies_to_modify", {})
    summary_merge = summary.get("currencies_to_merge", [])
    
    if summary_add:
        lines.append("\n需要添加的币种:")
        for pm, currencies in summary_add.items():
            if currencies:
                lines.append(f"  {pm}: {', '.join(currencies)}")
    
    if summary_remove:
        lines.append("\n需要删除的币种:")
        for pm, currencies in summary_remove.items():
            if currencies:
                lines.append(f"  {pm}: {', '.join(currencies)}")
    
    if summary_modify:
        lines.append("\n需要修改的币种:")
        for key, change_info in summary_modify.items():
            pm = change_info.get("payment_method", "")
            curr = change_info.get("currency", "")
            lines.append(f"  {pm} - {curr}")
    
    if summary_merge:
        lines.append("\n需要合并的币种:")
        for merge_info in summary_merge:
            pm = merge_info.get("payment_method", "")
            currencies = merge_info.get("currencies", [])
            if currencies:
                lines.append(f"  {pm}: {'/'.join(currencies)}")
    
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def read_csv_config(csv_path: str) -> dict:
    """
    从CSV文件读取配置
    
    Args:
        csv_path: CSV文件路径
        
    Returns:
        配置字典: {支付方式: {币种: [Adyen%, Stripe%, Airwallex%]}}
    """
    config = {}
    
    # 支付方式名称映射（CSV中的名称 -> 标准名称）
    payment_method_mapping = {
        'Card': 'CARD',
        'Apple Pay': 'AP',
        'Google Pay': 'GP'
    }
    
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                payment_method = row.get('支付方式', '').strip()
                currency = row.get('币种', '').strip()
                # 适配新的列名（Adyen, Stripe, Airwallex 而不是 Adyen%, Stripe%, Airwallex%）
                adyen_pct = int(row.get('Adyen', row.get('Adyen%', 0)) or 0)
                stripe_pct = int(row.get('Stripe', row.get('Stripe%', 0)) or 0)
                airwallex_pct = int(row.get('Airwallex', row.get('Airwallex%', 0)) or 0)
                
                if payment_method and currency:
                    # 标准化支付方式名称
                    payment_method = payment_method_mapping.get(payment_method, payment_method.upper())
                    
                    # 处理合并的币种（用/分隔的）
                    currencies = [c.strip() for c in currency.split('/')]
                    for curr in currencies:
                        if curr:
                            if payment_method not in config:
                                config[payment_method] = {}
                            config[payment_method][curr] = [adyen_pct, stripe_pct, airwallex_pct]
    except Exception as e:
        print(f"读取CSV文件失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    return config


def write_csv_config(config: dict, csv_path: str):
    """
    将配置写入CSV文件（合并相同分量的币种，保留符合条件的旧数据）
    
    Args:
        config: 配置字典: {支付方式: {币种: [Adyen%, Stripe%, Airwallex%]}}
        csv_path: CSV文件路径
    """
    payment_method_reverse_mapping = {
        'CARD': 'Card',
        'AP': 'Apple Pay',
        'GP': 'Google Pay'
    }
    
    fieldnames = ['支付方式', 'Network', '币种', '开启Affinity', 'Adaptive 3DS', '备注', 'Network Tokenized？', 'Adyen', 'Stripe', 'Airwallex']
    
    # 读取旧数据，只保留不符合删除条件的数据
    old_rows = []
    current_dir = Path(__file__).parent.parent.parent
    changelog_dir = current_dir / "currency_maintenance"
    csv_files = list(changelog_dir.glob("*.csv"))
    
    if csv_files:
        latest_csv = max(csv_files, key=lambda f: f.stat().st_mtime)
        try:
            with open(latest_csv, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    payment_method = row.get('支付方式', '').strip()
                    currency = row.get('币种', '').strip()
                    network = row.get('Network', '').strip()
                    tokenized = row.get('Network Tokenized？', '').strip()
                    
                    if not payment_method or not currency:
                        continue
                    
                    # 判断是否符合删除条件（需要删除的）
                    should_delete = False
                    if payment_method == 'Apple Pay':
                        # 所有的 Apple Pay 都要删除
                        should_delete = True
                    elif payment_method == 'Card' and network == 'Mastercard Visa JCB':
                        # Network 为 Mastercard Visa JCB 的 Card 要删除
                        should_delete = True
                    elif payment_method == 'Google Pay' and network == '非Amex' and tokenized == 'TRUE':
                        # Network = 非Amex 且 Network Tokenized = TRUE 的 Google Pay 要删除
                        should_delete = True
                    
                    # 不符合删除条件的，保留下来
                    if not should_delete:
                        old_rows.append(row.copy())
        except:
            pass
    
    # 生成新数据
    rows = []
    
    # 先添加保留的旧数据
    rows.extend(old_rows)
    
    # 生成新配置的数据（这些数据将替换符合删除条件的旧数据）
    for payment_method in sorted(config.keys()):
        currencies = config[payment_method]
        display_payment_method = payment_method_reverse_mapping.get(payment_method, payment_method)
        
        # 按分量分组币种
        percentages_to_currencies = {}
        for currency in sorted(currencies.keys()):
            percentages = tuple(currencies[currency])
            if percentages not in percentages_to_currencies:
                percentages_to_currencies[percentages] = []
            percentages_to_currencies[percentages].append(currency)
        
        # 对每个分量组，合并币种
        for percentages, currency_list in percentages_to_currencies.items():
            merged_currency = '/'.join(currency_list)
            first_currency = currency_list[0]
            
            # 根据支付方式设置默认值
            if payment_method == 'AP':  # Apple Pay
                row = {
                    '支付方式': display_payment_method,
                    'Network': '',
                    '币种': merged_currency,
                    '开启Affinity': '是' if first_currency != '其他' else '否',
                    'Adaptive 3DS': '否',
                    '备注': '',
                    'Network Tokenized？': '',
                    'Adyen': percentages[0] if percentages[0] > 0 else '',
                    'Stripe': percentages[1] if percentages[1] > 0 else '',
                    'Airwallex': percentages[2] if percentages[2] > 0 else ''
                }
                rows.append(row)
                
            elif payment_method == 'GP':  # Google Pay
                row = {
                    '支付方式': display_payment_method,
                    'Network': '非Amex',
                    '币种': merged_currency,
                    '开启Affinity': '是',
                    'Adaptive 3DS': '否',
                    '备注': '',
                    'Network Tokenized？': 'TRUE',
                    'Adyen': percentages[0] if percentages[0] > 0 else '',
                    'Stripe': percentages[1] if percentages[1] > 0 else '',
                    'Airwallex': percentages[2] if percentages[2] > 0 else ''
                }
                rows.append(row)
                
            elif payment_method == 'CARD':  # Card
                row = {
                    '支付方式': display_payment_method,
                    'Network': 'Mastercard Visa JCB',
                    '币种': merged_currency,
                    '开启Affinity': '是',
                    'Adaptive 3DS': '部分开启',
                    '备注': '',
                    'Network Tokenized？': '',
                    'Adyen': percentages[0] if percentages[0] > 0 else '',
                    'Stripe': percentages[1] if percentages[1] > 0 else '',
                    'Airwallex': percentages[2] if percentages[2] > 0 else ''
                }
                rows.append(row)
    
    # 写入CSV文件
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def get_latest_changelog_csv() -> Path:
    """
    从币种维护目录获取最新的CSV文件（按修改时间）
    
    Returns:
        CSV文件的Path对象
    """
    current_dir = Path(__file__).parent.parent.parent
    changelog_dir = current_dir / "currency_maintenance"
    
    if not changelog_dir.exists():
        changelog_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取所有CSV文件，按修改时间排序，返回最新的
    csv_files = list(changelog_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError("币种维护目录中没有找到CSV文件")
    
    # 按修改时间排序，返回最新的
    return max(csv_files, key=lambda f: f.stat().st_mtime)


def get_latest_update_log_csv() -> Path:
    """从更新日志目录获取最新的CSV文件"""
    update_log_dir = Path(UPDATE_LOG_DIR)
    if not update_log_dir.exists():
        raise FileNotFoundError("更新日志目录不存在")
    csv_files = list(update_log_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError("更新日志目录中没有找到CSV文件")
    return max(csv_files, key=lambda f: f.stat().st_mtime)


def parse_adjustment_sections(adjustment_text: str) -> dict:
    """将adjustment_text拆分为CARD/AP/GP原始文本"""
    if not adjustment_text:
        return {}
    sections = {}
    current_key = None
    buffer = []
    valid_keys = {"CARD", "AP", "GP"}
    for raw_line in adjustment_text.splitlines():
        line = raw_line.rstrip("\r")
        upper = line.strip().upper()
        if upper in valid_keys:
            if current_key and buffer:
                sections[current_key] = "\n".join(buffer).strip()
            current_key = upper
            buffer = []
            continue
        if current_key:
            buffer.append(line)
    if current_key and buffer:
        sections[current_key] = "\n".join(buffer).strip()
    return {k: v for k, v in sections.items() if v}


def save_update_log_with_adjustment(adjustment_text: str) -> str:
    """基于最新文件追加新的调整记录并生成时间戳CSV"""
    sections = parse_adjustment_sections(adjustment_text)
    if not sections:
        raise ValueError("adjustment_text 中未找到CARD/AP/GP记录，无法生成更新日志")
    update_log_dir = Path(UPDATE_LOG_DIR)
    update_log_dir.mkdir(parents=True, exist_ok=True)
    latest_csv = get_latest_update_log_csv()
    rows = []
    fieldnames = None
    with open(latest_csv, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or ['支付方式', '日期', '日志内容', '修改内容']
        for row in reader:
            rows.append(row)
    existing_count = len(rows)
    date_str = datetime.now().strftime("%Y/%m/%d")
    payment_method_mapping = {
        'CARD': 'Card',
        'AP': 'Apple Pay',
        'GP': 'Google Pay'
    }
    for key, content in sections.items():
        display_name = payment_method_mapping.get(key)
        if not display_name:
            continue
        rows.append({
            '支付方式': display_name,
            '日期': date_str,
            '日志内容': content.strip(),
            '修改内容': ''
        })
    if len(rows) == existing_count:
        raise ValueError("调整方案中没有有效的CARD/AP/GP内容用于记录更新日志")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_csv_path = update_log_dir / f"Update log_{timestamp}.csv"
    with open(new_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return str(new_csv_path)


def normalize_currency_name(currency: str) -> str:
    """
    标准化币种名称，处理"其他币种"和"其他"的映射
    
    Args:
        currency: 币种名称
        
    Returns:
        标准化后的币种名称
    """
    # 币种名称映射
    currency_mapping = {
        "其他币种": "其他",
        "其他": "其他"
    }
    return currency_mapping.get(currency, currency)


def merge_currencies_to_other(config: dict) -> tuple[dict, dict]:
    """
    将分量与"其他币种"相同的币种合并到"其他币种"中
    
    如果某个币种的分量和"其他币种"的分量相同，则将该币种从配置中移除
    （因为"其他币种"已经包含了这个分量）
    
    Args:
        config: 配置字典 {支付方式: {币种: [Adyen%, Stripe%, Airwallex%]}}
        
    Returns:
        (merged_config, merged_info)
        - merged_config: 合并后的配置字典
        - merged_info: 被合并的币种信息 {支付方式: [币种列表]}
    """
    merged_config = {}
    merged_info = {}
    
    for payment_method, currencies in config.items():
        merged_config[payment_method] = {}
        
        # 检查是否有"其他"币种配置
        other_currency_pct = None
        if "其他" in currencies:
            other_currency_pct = currencies["其他"]
        
        # 遍历所有币种
        for currency, percentages in currencies.items():
            # 如果是"其他"币种，直接保留
            if currency == "其他":
                merged_config[payment_method][currency] = percentages
            # 如果存在"其他"币种配置，且当前币种的分量和"其他"相同，则跳过（合并到"其他"中）
            elif other_currency_pct is not None and percentages == other_currency_pct:
                # 记录被合并的币种
                if payment_method not in merged_info:
                    merged_info[payment_method] = []
                merged_info[payment_method].append(currency)
            else:
                # 其他情况，正常添加
                merged_config[payment_method][currency] = percentages
    
    return merged_config, merged_info


def compare_csv_configs(old_config: dict, new_config: dict) -> list:
    """
    对比两个配置，生成调整步骤
    
    Args:
        old_config: 旧配置 {支付方式: {币种: [Adyen%, Stripe%, Airwallex%]}}
        new_config: 新配置 {支付方式: {币种: [Adyen%, Stripe%, Airwallex%]}}
        
    Returns:
        变更列表
    """
    changes = []
    
    # 创建标准化后的配置映射（用于对比）
    normalized_old_config = {}
    normalized_new_config = {}
    
    # 标准化旧配置
    for payment_method, currencies in old_config.items():
        normalized_old_config[payment_method] = {}
        for currency, percentages in currencies.items():
            normalized_currency = normalize_currency_name(currency)
            normalized_old_config[payment_method][normalized_currency] = percentages
    
    # 标准化新配置
    for payment_method, currencies in new_config.items():
        normalized_new_config[payment_method] = {}
        for currency, percentages in currencies.items():
            normalized_currency = normalize_currency_name(currency)
            normalized_new_config[payment_method][normalized_currency] = percentages
    
    # 获取所有支付方式
    all_payment_methods = set(list(normalized_old_config.keys()) + list(normalized_new_config.keys()))
    
    for payment_method in all_payment_methods:
        old_currencies = normalized_old_config.get(payment_method, {})
        new_currencies = normalized_new_config.get(payment_method, {})
        
        # 获取所有币种
        all_currencies = set(list(old_currencies.keys()) + list(new_currencies.keys()))
        
        for currency in all_currencies:
            old_pct = old_currencies.get(currency)
            new_pct = new_currencies.get(currency)
            
            if old_pct and new_pct:
                # 需要修改
                if old_pct != new_pct:
                    changes.append({
                        "action": "modify",
                        "payment_method": payment_method,
                        "currency": currency,
                        "old": old_pct,
                        "new": new_pct
                    })
            elif old_pct and not new_pct:
                # 需要删除
                changes.append({
                    "action": "remove",
                    "payment_method": payment_method,
                    "currency": currency,
                    "old": old_pct
                })
            elif not old_pct and new_pct:
                # 需要添加
                changes.append({
                    "action": "add",
                    "payment_method": payment_method,
                    "currency": currency,
                    "new": new_pct
                })
    
    return changes

@workflow_api.route('/parse', methods=['POST'])
def parse_workflow():
    """解析workflow文件"""
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({"error": "没有上传文件"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "文件名为空"}), 400
        
        if not file.filename.endswith('.json'):
            return jsonify({"error": "请上传JSON格式文件"}), 400
        
        # 读取文件内容
        file_content = file.read()
        
        try:
            json_data = json.loads(file_content.decode('utf-8'))
        except json.JSONDecodeError as e:
            return jsonify({"error": f"JSON解析失败: {str(e)}"}), 400
        
        # 解析workflow
        parser = WorkflowParser()
        result = parser.parse_json(json_data)
        
        # 获取摘要
        summary = parser.get_summary()
        
        # 获取CSV格式数据
        csv_format_data = parser.get_csv_format_data()
        
        return jsonify({
            "success": True,
            "data": {
                "nodes": result["nodes"],
                "conditions": result["conditions"],
                "connections": result["connections"],
                "splits": result["splits"],  # 添加splits数据
                "csv_format": csv_format_data  # 添加CSV格式数据
            },
            "summary": summary
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"解析失败: {str(e)}"}), 500


@workflow_api.route('/compare-split', methods=['POST'])
def compare_split():
    """对比split配置并生成修改建议"""
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({"error": "没有上传文件"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "文件名为空"}), 400
        
        if not file.filename.endswith('.json'):
            return jsonify({"error": "请上传JSON格式文件"}), 400
        
        # 获取调整方案文本
        adjustment_text = request.form.get('adjustment_text', '')
        if not adjustment_text:
            return jsonify({"error": "请提供调整方案文本"}), 400
        
        # 获取调整模式（默认为更新调整）
        adjustment_mode = request.form.get('adjustment_mode', 'update')
        if adjustment_mode not in ['update', 'override']:
            adjustment_mode = 'update'
        
        # 读取文件内容
        file_content = file.read()
        
        try:
            json_data = json.loads(file_content.decode('utf-8'))
        except json.JSONDecodeError as e:
            return jsonify({"error": f"JSON解析失败: {str(e)}"}), 400
        
        # 对比配置
        comparator = SplitComparator()
        result = comparator.compare_configurations(json_data, adjustment_text, adjustment_mode)
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"对比失败: {str(e)}"}), 500


@workflow_api.route('/compare-doc-split', methods=['POST'])
def compare_doc_split():
    """对比doc文件中的split配置并生成修改建议"""
    try:
        # 获取调整方案文本
        adjustment_text = request.form.get('adjustment_text', '')
        if not adjustment_text:
            return jsonify({"error": "请提供调整方案文本"}), 400
        
        # 获取调整模式（默认为更新调整）
        adjustment_mode = request.form.get('adjustment_mode', 'update')
        if adjustment_mode not in ['update', 'override']:
            adjustment_mode = 'update'
        
        # 自动读取项目中的primer workflow文件
        current_dir = Path(__file__).parent.parent.parent
        docx_path = current_dir / "Primer Workflow - GOF.docx"
        
        if not docx_path.exists():
            return jsonify({"error": "找不到Primer Workflow文档文件"}), 404
        
        # 读取docx文件
        reader = DocxReader()
        current_config = reader.read_docx(str(docx_path))
        
        # 将配置转换为split_comparator需要的格式
        formatted_current_config = {}
        for payment_method, currencies in current_config.items():
            formatted_current_config[payment_method] = {}
            for currency, percentages in currencies.items():
                formatted_current_config[payment_method][currency] = {
                    "percentages": percentages,
                    "routes": ["Adyen", "Stripe", "AWX"],
                    "split_id": None
                }
        
        # 解析调整方案
        comparator = SplitComparator()
        new_config = comparator.parse_adjustment_text(adjustment_text)
        
        # 生成最终配置
        final_config = comparator._generate_final_config(
            formatted_current_config,
            new_config,
            adjustment_mode
        )
        
        # 生成对比结果
        comparison_result = {
            "current_config": formatted_current_config,
            "new_config": new_config,
            "changes": [],
            "summary": {
                "currencies_to_add": {},
                "currencies_to_remove": {},
                "currencies_to_modify": {},
                "currencies_to_merge": []
            }
        }
        
        # 对比每个支付方式
        all_payment_methods = set(list(new_config.keys()) + list(formatted_current_config.keys()))
        
        for payment_method in all_payment_methods:
            current_currencies = formatted_current_config.get(payment_method, {})
            new_currencies = new_config.get(payment_method, {})
            
            all_currencies = set(list(current_currencies.keys()) + list(new_currencies.keys()))
            
            for currency in all_currencies:
                current_config_currency = current_currencies.get(currency)
                new_config_currency = new_currencies.get(currency)
                
                change_info = {
                    "payment_method": payment_method,
                    "currency": currency,
                    "action": None,
                    "current": None,
                    "new": None,
                    "instructions": []
                }
                
                if current_config_currency and new_config_currency:
                    # 需要修改
                    current_pct = current_config_currency.get("percentages", [])
                    new_pct = new_config_currency
                    
                    if current_pct != new_pct:
                        change_info["action"] = "modify"
                        change_info["current"] = {
                            "percentages": current_pct,
                            "routes": current_config_currency.get("routes", [])
                        }
                        change_info["new"] = {
                            "percentages": new_pct,
                            "routes": ["Adyen", "Stripe", "AWX"]
                        }
                        change_info["instructions"] = [
                            f"将 {payment_method} - {currency} 的分量从 {':'.join(map(str, current_pct))}% 修改为 {':'.join(map(str, new_pct))}%"
                        ]
                        comparison_result["changes"].append(change_info)
                        comparison_result["summary"]["currencies_to_modify"][f"{payment_method}_{currency}"] = change_info
                
                elif current_config_currency and not new_config_currency:
                    # 需要删除
                    change_info["action"] = "remove"
                    change_info["current"] = {
                        "percentages": current_config_currency.get("percentages", []),
                        "routes": current_config_currency.get("routes", []),
                        "split_id": current_config_currency.get("split_id")
                    }
                    change_info["instructions"] = [
                        f"删除 {payment_method} - {currency} 的split配置"
                    ]
                    comparison_result["changes"].append(change_info)
                    if payment_method not in comparison_result["summary"]["currencies_to_remove"]:
                        comparison_result["summary"]["currencies_to_remove"][payment_method] = []
                    comparison_result["summary"]["currencies_to_remove"][payment_method].append(currency)
                
                elif not current_config_currency and new_config_currency:
                    # 需要添加
                    change_info["action"] = "add"
                    change_info["new"] = {
                        "percentages": new_config_currency,
                        "routes": ["Adyen", "Stripe", "AWX"]
                    }
                    change_info["instructions"] = [
                        f"添加 {payment_method} - {currency} 的split配置，分量为 {':'.join(map(str, new_config_currency))}%"
                    ]
                    comparison_result["changes"].append(change_info)
                    if payment_method not in comparison_result["summary"]["currencies_to_add"]:
                        comparison_result["summary"]["currencies_to_add"][payment_method] = []
                    comparison_result["summary"]["currencies_to_add"][payment_method].append(currency)
        
        # 检查需要合并的币种
        for payment_method, currencies in new_config.items():
            for currency_key, percentages in currencies.items():
                if '/' in currency_key:
                    currency_list = currency_key.split('/')
                    comparison_result["summary"]["currencies_to_merge"].append({
                        "payment_method": payment_method,
                        "currencies": currency_list,
                        "percentages": percentages
                    })
        
        # 生成完整的分量对比
        before_formatted = comparator._format_config_for_display(formatted_current_config)
        after_formatted = comparator._format_config_for_display(final_config)
        
        before_formatted, after_formatted = comparator._merge_comparison_configs(
            before_formatted,
            after_formatted,
            formatted_current_config,
            final_config
        )
        
        comparison_result["full_comparison"] = {
            "before": before_formatted,
            "after": after_formatted
        }
        
        return jsonify({
            "success": True,
            "data": comparison_result
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"对比失败: {str(e)}"}), 500

@workflow_api.route('/save-adjustment', methods=['POST'])
def save_adjustment():
    """保存调整方案到文件"""
    try:
        adjustment_text = request.form.get('adjustment_text', '')
        file_format = request.form.get('format', 'txt')  # txt, json, md
        
        if not adjustment_text:
            return jsonify({"error": "调整方案内容为空"}), 400
        
        # 生成文件名（带时间戳）
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"adjustment_{timestamp}.{file_format}"
        
        # 保存到adjustments目录
        current_dir = Path(__file__).parent.parent.parent.parent
        adjustments_dir = current_dir / "adjustments"
        adjustments_dir.mkdir(exist_ok=True)
        file_path = adjustments_dir / filename
        
        try:
            # 保存文件
            if file_format == "json":
                import json
                try:
                    data = json.loads(adjustment_text)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                except:
                    # 如果不是JSON，按文本保存
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(adjustment_text)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(adjustment_text)
            
            return jsonify({
                "success": True,
                "file_path": str(file_path),
                "filename": filename
            })
        except Exception as e:
            return jsonify({"error": f"保存文件失败: {str(e)}"}), 500
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"保存失败: {str(e)}"}), 500


@workflow_api.route('/load-adjustment', methods=['POST'])
def load_adjustment():
    """从文件加载调整方案"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "没有上传文件"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "文件名为空"}), 400
        
        # 读取文件内容
        file_content = file.read()
        content = file_content.decode('utf-8')
        
        return jsonify({
            "success": True,
            "content": content
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"加载失败: {str(e)}"}), 500


def extract_adjustment_from_request(raw_data: str) -> tuple[str, str]:
    """
    从请求数据中提取调整方案文本和调整模式
    
    Args:
        raw_data: 原始请求数据字符串
        
    Returns:
        (adjustment_text, adjustment_mode)
        
    Raises:
        ValueError: 如果无法提取调整方案
    """
    import re
    
    raw_data = raw_data.strip()
    if not raw_data:
        raise ValueError("请求体为空")
    
    # 查找 "adjustment_text": 后面的内容
    start_marker = '"adjustment_text"'
    start_idx = raw_data.find(start_marker)
    
    if start_idx == -1:
        raise ValueError("无法找到adjustment_text字段，请确保请求中包含 adjustment_text 字段")
    
    # 找到冒号的位置
    colon_idx = raw_data.find(':', start_idx)
    if colon_idx == -1:
        raise ValueError("adjustment_text字段格式错误，无法找到冒号分隔符")
    
    # 从冒号后开始提取，直到最后一个}之前
    value_start = colon_idx + 1
    last_brace = raw_data.rfind('}')
    if last_brace <= value_start:
        raise ValueError("adjustment_text字段格式错误，无法找到结束的大括号")
    
    # 提取原始文本
    adjustment_text_raw = raw_data[value_start:last_brace].strip()
    
    # 从文本中提取CARD、AP、GP部分
    card_match = re.search(r'CARD\s*\n(.*?)(?=\n(?:AP|GP|$))', adjustment_text_raw, re.DOTALL | re.IGNORECASE)
    ap_match = re.search(r'AP\s*\n(.*?)(?=\n(?:GP|$))', adjustment_text_raw, re.DOTALL | re.IGNORECASE)
    gp_match = re.search(r'GP\s*\n(.*?)$', adjustment_text_raw, re.DOTALL | re.IGNORECASE)
    
    # 构建调整方案文本
    parts = []
    if card_match:
        card_content = card_match.group(1).strip()
        parts.append(f"CARD\n{card_content}")
    if ap_match:
        ap_content = ap_match.group(1).strip()
        parts.append(f"AP\n{ap_content}")
    if gp_match:
        gp_content = gp_match.group(1).strip()
        parts.append(f"GP\n{gp_content}")
    
    if not parts:
        adjustment_text = adjustment_text_raw
    else:
        adjustment_text = '\n\n'.join(parts)
    
    if not adjustment_text or not adjustment_text.strip():
        raise ValueError("adjustment_text 字段为空或未找到CARD/AP/GP配置")
    
    # 提取adjustment_mode
    adjustment_mode = 'update'
    if 'adjustment_mode' in raw_data:
        mode_match = re.search(r'"adjustment_mode"\s*:\s*"(\w+)"', raw_data)
        if mode_match:
            adjustment_mode = mode_match.group(1)
    
    if adjustment_mode not in ['update', 'override']:
        adjustment_mode = 'update'
    
    return adjustment_text, adjustment_mode


def load_old_config_from_changelog() -> dict:
    """
    从币种维护文件加载旧配置（仅加载特定条件的数据）
    加载条件：
    1. 所有的 Apple Pay
    2. Network 为 Mastercard Visa JCB 的 Card
    3. Network = 非Amex 且 Network Tokenized = True 的 Google Pay
    
    Returns:
        旧配置字典（仅包含需要对比的数据）
        
    Raises:
        FileNotFoundError: 如果找不到币种维护CSV文件
        Exception: 如果读取失败
    """
    old_csv_path = get_latest_changelog_csv()
    
    # 直接按照筛选条件读取配置，而不是先读取所有数据
    filtered_config = {}
    payment_method_mapping = {
        'Card': 'CARD',
        'Apple Pay': 'AP',
        'Google Pay': 'GP'
    }
    
    try:
        with open(old_csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                payment_method = row.get('支付方式', '').strip()
                currency = row.get('币种', '').strip()
                network = row.get('Network', '').strip()
                tokenized = row.get('Network Tokenized？', '').strip()
                
                if not payment_method or not currency:
                    continue
                
                pm_key = payment_method_mapping.get(payment_method)
                
                # 判断是否符合加载条件
                should_load = False
                if payment_method == 'Apple Pay':
                    # 所有的 Apple Pay
                    should_load = True
                elif payment_method == 'Card' and network == 'Mastercard Visa JCB':
                    # Network 为 Mastercard Visa JCB 的 Card
                    should_load = True
                elif payment_method == 'Google Pay' and network == '非Amex' and tokenized == 'TRUE':
                    # Network = 非Amex 且 Network Tokenized = True 的 Google Pay
                    should_load = True
                
                if should_load and pm_key:
                    # 适配新的列名（Adyen, Stripe, Airwallex 而不是 Adyen%, Stripe%, Airwallex%）
                    adyen_pct = int(row.get('Adyen', row.get('Adyen%', 0)) or 0)
                    stripe_pct = int(row.get('Stripe', row.get('Stripe%', 0)) or 0)
                    airwallex_pct = int(row.get('Airwallex', row.get('Airwallex%', 0)) or 0)
                    
                    if pm_key not in filtered_config:
                        filtered_config[pm_key] = {}
                    
                    # 处理合并的币种（用/分隔的）
                    for curr in currency.split('/'):
                        curr = curr.strip()
                        if curr:
                            filtered_config[pm_key][curr] = [adyen_pct, stripe_pct, airwallex_pct]
    except Exception as e:
        print(f"读取CSV文件失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    return filtered_config


def format_config_for_comparator(config: dict) -> dict:
    """
    将CSV配置转换为split_comparator需要的格式，并标准化币种名称
    
    Args:
        config: CSV配置字典 {支付方式: {币种: [Adyen%, Stripe%, Airwallex%]}}
        
    Returns:
        格式化后的配置字典
    """
    formatted_config = {}
    for payment_method, currencies in config.items():
        formatted_config[payment_method] = {}
        for currency, percentages in currencies.items():
            normalized_currency = normalize_currency_name(currency)
            formatted_config[payment_method][normalized_currency] = {
                "percentages": percentages,
                "routes": ["Adyen", "Stripe", "AWX"],
                "split_id": None
            }
    return formatted_config


def process_adjustment_and_generate_steps(old_config: dict, formatted_old_config: dict, 
                                          adjustment_text: str, adjustment_mode: str) -> tuple[dict, list, dict, str]:
    """
    处理调整方案并生成调整步骤
    
    根据旧配置和调整方案，生成新配置，并对比生成调整步骤
    
    Args:
        old_config: 旧配置（CSV格式）
        formatted_old_config: 格式化后的旧配置（comparator格式）
        adjustment_text: 调整方案文本
        adjustment_mode: 调整模式
        
    Returns:
        (new_config, changes, summary, steps_description)
        - new_config: 新配置（CSV格式）
        - changes: 变更列表
        - summary: 摘要信息
        - steps_description: 步骤描述文本
    """
    # 1. 解析调整方案
    comparator = SplitComparator()
    adjustment_config = comparator.parse_adjustment_text(adjustment_text)
    
    # 调试：打印原始解析结果
    import json
    print("=== 调整方案解析（原始）===")
    print(json.dumps(adjustment_config, ensure_ascii=False, indent=2))
    
    # 2. 标准化调整方案中的币种名称
    normalized_adjustment_config = {}
    for payment_method, currencies in adjustment_config.items():
        normalized_adjustment_config[payment_method] = {}
        for currency, percentages in currencies.items():
            # 处理合并的币种（用/分隔的）
            if '/' in currency:
                # 对于合并的币种，拆分成单独的币种，每个都设置相同的百分比
                currency_list = currency.split('/')
                for curr in currency_list:
                    normalized_curr = normalize_currency_name(curr.strip())
                    normalized_adjustment_config[payment_method][normalized_curr] = percentages
            else:
                normalized_currency_key = normalize_currency_name(currency)
                normalized_adjustment_config[payment_method][normalized_currency_key] = percentages
    
    # 调试：打印标准化后的调整方案
    print("=== 调整方案解析（标准化后）===")
    print(json.dumps(normalized_adjustment_config, ensure_ascii=False, indent=2))
    
    # 3. 生成调整后的新配置
    new_config_dict = comparator._generate_final_config(
        formatted_old_config,
        normalized_adjustment_config,
        adjustment_mode
    )
    
    # 4. 将新配置转换为CSV格式的配置字典
    new_config = {}
    for payment_method, currencies in new_config_dict.items():
        new_config[payment_method] = {}
        for currency, config_item in currencies.items():
            if isinstance(config_item, dict):
                percentages = config_item.get("percentages", [])
            else:
                percentages = config_item
            new_config[payment_method][currency] = percentages
    
    # 5. 合并相同分量的币种到"其他币种"中
    new_config, merged_to_other = merge_currencies_to_other(new_config)
    
    # 调试：打印生成的配置
    formatted_old_config_simple = {}
    for k, currencies in formatted_old_config.items():
        formatted_old_config_simple[k] = {c: v.get('percentages') for c, v in currencies.items()}
    print("=== 调试信息 ===")
    print(f"旧配置（标准化后）: {json.dumps(formatted_old_config_simple, ensure_ascii=False, indent=2)}")
    print(f"新配置（合并后）: {json.dumps(new_config, ensure_ascii=False, indent=2)}")
    print(f"被合并到其他币种: {json.dumps(merged_to_other, ensure_ascii=False, indent=2)}")
    print("================")
    
    # 6. 对比两个CSV配置，生成调整步骤
    changes = compare_csv_configs(old_config, new_config)
    
    # 7. 生成调整步骤描述
    summary = {
        "currencies_to_add": {},
        "currencies_to_remove": {},
        "currencies_to_modify": {},
        "currencies_to_merge": []
    }
    
    # 整理summary信息
    for change in changes:
        pm = change["payment_method"]
        curr = change["currency"]
        
        if change["action"] == "add":
            if pm not in summary["currencies_to_add"]:
                summary["currencies_to_add"][pm] = []
            summary["currencies_to_add"][pm].append(curr)
        elif change["action"] == "remove":
            if pm not in summary["currencies_to_remove"]:
                summary["currencies_to_remove"][pm] = []
            summary["currencies_to_remove"][pm].append(curr)
        elif change["action"] == "modify":
            summary["currencies_to_modify"][f"{pm}_{curr}"] = change
    
    # 加载 should_keep 数据
    should_keep_data = load_should_keep_data()
    
    # 生成简化的步骤描述（包含被合并到"其他币种"的信息，以及 should_keep 数据中的相同分量信息）
    steps_description = generate_simple_steps_description(changes, summary, merged_to_other, should_keep_data)
    
    return new_config, changes, summary, steps_description


def normalize_config_for_csv(config: dict) -> dict:
    """
    标准化配置中的币种名称，用于保存CSV
    
    Args:
        config: 配置字典
        
    Returns:
        标准化后的配置字典
    """
    normalized_config = {}
    for payment_method, currencies in config.items():
        normalized_config[payment_method] = {}
        for currency, percentages in currencies.items():
            normalized_currency = normalize_currency_name(currency)
            normalized_config[payment_method][normalized_currency] = percentages
    return normalized_config


def save_new_config_to_changelog(new_config: dict) -> str:
    """
    保存新配置到币种维护目录（使用时间戳文件名，不删除旧文件）
    
    Args:
        new_config: 新配置字典
        
    Returns:
        保存的文件路径
        
    Raises:
        Exception: 如果保存失败
    """
    from datetime import datetime
    
    current_dir = Path(__file__).parent.parent.parent
    changelog_dir = current_dir / "currency_maintenance"
    changelog_dir.mkdir(parents=True, exist_ok=True)
    
    # 使用时间戳文件名，不覆盖旧文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = changelog_dir / f"currency_maintenance_{timestamp}.csv"
    
    # 保存CSV文件（会保留原有文件的其他列信息）
    write_csv_config(new_config, str(csv_path))
    
    return str(csv_path)


@workflow_api.route('/feishu-webhook', methods=['POST'])
def feishu_webhook():
    """接收飞书机器人的调整方案请求，返回对比结果"""
    logger = logging.getLogger(__name__)
    
    try:
        adjustment_text, adjustment_mode = extract_adjustment_from_request(request.get_data(as_text=True))
        logger.info("Feishu webhook: mode=%s", adjustment_mode)
        
        old_csv_path = get_latest_changelog_csv()
        old_config = load_old_config_from_changelog()
        new_config, changes, _, steps_description = process_adjustment_and_generate_steps(
            old_config, format_config_for_comparator(old_config), adjustment_text, adjustment_mode
        )
        logger.info("Feishu webhook: processed %s change(s)", len(changes))
        
        csv_file_path = save_new_config_to_changelog(normalize_config_for_csv(new_config))
        update_log_csv_path = save_update_log_with_adjustment(adjustment_text)
        
        _sync_currency_maintenance(logger, csv_file=csv_file_path)
        _sync_update_log(logger, csv_file=update_log_csv_path)
        
        return jsonify({
            "success": True,
            "steps": steps_description,
            "old_config": old_csv_path.name,
            "new_config": Path(csv_file_path).name,
            "update_log": Path(update_log_csv_path).name
        })
        
    except ValueError as e:
        logger.error("参数错误: %s", e)
        return jsonify({"success": False, "error": str(e)}), 400
    except FileNotFoundError as e:
        logger.error("文件未找到: %s", e)
        return jsonify({"success": False, "error": "找不到币种维护CSV文件", "message": str(e)}), 404
    except Exception as e:
        import traceback
        logger.error("处理Webhook请求时发生错误: %s", e, exc_info=True)
        error_msg = str(e)
        error_map = {
            ("读取", "read"): "读取币种维护CSV文件失败",
            ("保存", "save", "write"): "保存币种维护CSV文件失败"
        }
        for keywords, msg in error_map.items():
            if any(kw in error_msg or kw in error_msg.lower() for kw in keywords):
                return jsonify({"success": False, "error": msg, "message": error_msg}), 500
        return jsonify({"success": False, "error": f"处理失败: {error_msg}"}), 500


@workflow_api.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "ok"})

