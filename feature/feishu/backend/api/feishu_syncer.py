#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import csv
import json
import re
import os
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    response = requests.post(url, json={"app_id": app_id, "app_secret": app_secret}, timeout=10)
    result = response.json()
    if result.get("code") == 0:
        return result.get("tenant_access_token")
    raise Exception(f"获取token失败: {result.get('msg')}")


def get_feishu_table_info_from_url(url: str) -> dict:
    app_token_match = re.search(r'/base/([^/?]+)', url)
    table_id_match = re.search(r'table=([^&]+)', url)
    if app_token_match and table_id_match:
        return {"app_token": app_token_match.group(1), "table_id": table_id_match.group(1)}
    raise ValueError("无法从URL中提取app_token和table_id")


def get_latest_csv_file(dir_path: str) -> str:
    path = Path(dir_path)
    csv_files = list(path.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"目录中没有找到CSV文件: {dir_path}")
    return str(max(csv_files, key=lambda f: f.stat().st_mtime))


def read_csv_data(csv_file: str) -> list:
    data = []
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            data.append(row)
    return data


def convert_date_to_timestamp(date_str: str) -> int:
    """
    将日期字符串转换为 Feishu 需要的时间戳（毫秒）
    
    支持的格式：
    - YYYY/MM/DD (如: 2025/07/17)
    - YYYY-MM-DD (如: 2025-07-17)
    - 其他常见日期格式
    
    Args:
        date_str: 日期字符串
        
    Returns:
        时间戳（毫秒），如果转换失败返回 None
    """
    if not date_str or not date_str.strip():
        return None
    
    date_str = date_str.strip()
    
    # 尝试多种日期格式
    date_formats = [
        "%Y/%m/%d",      # 2025/07/17
        "%Y-%m-%d",      # 2025-07-17
        "%Y/%m/%d %H:%M:%S",  # 2025/07/17 12:00:00
        "%Y-%m-%d %H:%M:%S",  # 2025-07-17 12:00:00
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # 转换为时间戳（毫秒）
            timestamp_ms = int(dt.timestamp() * 1000)
            return timestamp_ms
        except ValueError:
            continue
    
    # 如果所有格式都失败，记录警告并返回 None
    logger.warning(f"无法解析日期格式: {date_str}")
    return None


def convert_to_feishu_record(row: dict, field_map: dict = None) -> dict:
    fields = {}
    number_fields = ["Adyen", "Stripe", "Airwallex"]
    # 日期字段名称（中文和英文）
    date_fields = ["日期", "date", "Date", "DATE", "时间", "time", "Time", "TIME"]
    
    if not field_map:
        for key, value in row.items():
            # 处理数字字段
            if key in number_fields:
                if not value or not value.strip():
                    fields[key] = 0
                else:
                    try:
                        fields[key] = int(value.strip())
                    except:
                        fields[key] = 0
                continue
            
            # 处理日期字段
            if key in date_fields:
                timestamp = convert_date_to_timestamp(value)
                if timestamp is not None:
                    fields[key] = timestamp
                # 如果转换失败，跳过该字段（不添加）
                continue
            
            # 处理其他字段
            if not value or not value.strip():
                continue
            fields[key] = value.strip()
    else:
        for csv_key, feishu_field in field_map.items():
            # 处理数字字段
            if csv_key in number_fields:
                if csv_key not in row or not row[csv_key] or not row[csv_key].strip():
                    fields[feishu_field] = 0
                else:
                    try:
                        fields[feishu_field] = int(row[csv_key].strip())
                    except:
                        fields[feishu_field] = 0
                continue
            
            # 处理日期字段
            if csv_key in date_fields:
                value = row.get(csv_key, "")
                timestamp = convert_date_to_timestamp(value)
                if timestamp is not None:
                    fields[feishu_field] = timestamp
                # 如果转换失败，跳过该字段
                continue
            
            # 处理其他字段
            if csv_key not in row or not row[csv_key]:
                continue
            fields[feishu_field] = row[csv_key].strip()
    
    return {"fields": fields}


def batch_create_records(app_token: str, table_id: str, access_token: str, records: list) -> bool:
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    
    for i in range(0, len(records), 500):
        batch = records[i:i + 500]
        try:
            response = requests.post(url, json={"records": batch}, headers=headers, timeout=30)
            if response.status_code != 200:
                logger.error(f"创建记录失败: HTTP状态码 {response.status_code}, 响应: {response.text}")
                return False
            result = response.json()
            if result.get("code") != 0:
                error_msg = result.get("msg", "未知错误")
                error_code = result.get("code")
                logger.error(f"创建记录失败: Feishu API错误码 {error_code}, 错误信息: {error_msg}")
                logger.debug(f"完整响应: {json.dumps(result, ensure_ascii=False)}")
                return False
        except Exception as e:
            logger.error(f"创建记录时发生异常: {str(e)}", exc_info=True)
            return False
    return True


def delete_all_records(app_token: str, table_id: str, access_token: str) -> bool:
    record_ids = _get_all_record_ids(app_token, table_id, access_token)
    if not record_ids:
        return True
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_delete"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    
    for i in range(0, len(record_ids), 500):
        batch = record_ids[i:i + 500]
        try:
            response = requests.post(url, json={"records": batch}, headers=headers, timeout=30)
            if response.status_code != 200:
                logger.error(f"删除记录失败: HTTP状态码 {response.status_code}, 响应: {response.text}")
                return False
            result = response.json()
            if result.get("code") != 0:
                error_msg = result.get("msg", "未知错误")
                error_code = result.get("code")
                logger.error(f"删除记录失败: Feishu API错误码 {error_code}, 错误信息: {error_msg}")
                logger.debug(f"完整响应: {json.dumps(result, ensure_ascii=False)}")
                return False
        except Exception as e:
            logger.error(f"删除记录时发生异常: {str(e)}", exc_info=True)
            return False
    return True


def _get_all_record_ids(app_token: str, table_id: str, access_token: str) -> list:
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    
    all_record_ids = []
    page_token = None
    
    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            if response.status_code != 200:
                logger.error(f"获取记录ID失败: HTTP状态码 {response.status_code}, 响应: {response.text}")
                break
            
            try:
                result = response.json()
            except:
                try:
                    result = json.loads(response.content.decode('utf-8'))
                except Exception as e:
                    logger.error(f"解析响应JSON失败: {str(e)}")
                    break
            
            if result.get("code") != 0:
                error_msg = result.get("msg", "未知错误")
                error_code = result.get("code")
                logger.error(f"获取记录ID失败: Feishu API错误码 {error_code}, 错误信息: {error_msg}")
                break
            
            data = result.get("data", {})
            for record in data.get("items", []):
                record_id = record.get("record_id")
                if record_id:
                    all_record_ids.append(record_id)
            
            page_token = data.get("page_token")
            if not page_token:
                break
        except Exception as e:
            logger.error(f"获取记录ID时发生异常: {str(e)}", exc_info=True)
            break
    
    return all_record_ids


def sync_currency_maintenance_to_feishu(
    csv_dir: str = None,
    csv_file: str = None,
    app_token: str = None,
    table_id: str = None,
    access_token: str = None,
    field_map: dict = None
) -> bool:
    try:
        if csv_file:
            csv_file_path = csv_file
        elif csv_dir:
            csv_file_path = get_latest_csv_file(csv_dir)
        else:
            raise ValueError("必须提供 csv_dir 或 csv_file 参数")
        logger.info(f"使用文件: {csv_file_path}")
        print(f"使用文件: {csv_file_path}")
        
        csv_data = read_csv_data(csv_file_path)
        logger.info(f"读取到 {len(csv_data)} 条记录")
        print(f"读取到 {len(csv_data)} 条记录")
        
        logger.info("删除旧数据...")
        print("删除旧数据...")
        if not delete_all_records(app_token, table_id, access_token):
            logger.error("删除旧数据失败")
            return False
        
        records = [convert_to_feishu_record(row, field_map) for row in csv_data]
        logger.info(f"准备创建 {len(records)} 条新记录...")
        print(f"创建 {len(records)} 条新记录...")
        
        # 记录第一条记录的结构用于调试
        if records:
            logger.debug(f"第一条记录示例: {json.dumps(records[0], ensure_ascii=False)}")
        
        if not batch_create_records(app_token, table_id, access_token, records):
            logger.error("创建新记录失败")
            return False
        
        logger.info(f"✓ 成功同步 {len(records)} 条记录")
        print(f"✓ 成功同步 {len(records)} 条记录")
        return True
    except Exception as e:
        logger.error(f"同步过程中发生异常: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    table_url = "https://centurygames.feishu.cn/base/ZjWjbTdQQaX22VsaMQzcGSLbnyc?table=tblKHfdMJyrVonxS&view=vew9fRbXDD"
    csv_dir = os.path.join(os.path.dirname(__file__), "../../../workflow/currency maintenance")
    
    app_id = "cli_a99e862024e7100e"
    app_secret = "Yog0pVLeTiyjsfxtga7ltbxgd3uVbg0j"
    
    print("正在获取 access_token...")
    access_token = get_tenant_access_token(app_id, app_secret)
    print("✓ 成功获取 access_token")
    
    table_info = get_feishu_table_info_from_url(table_url)
    app_token = table_info["app_token"]
    table_id = table_info["table_id"]
    
    success = sync_currency_maintenance_to_feishu(
        csv_dir=csv_dir,
        app_token=app_token,
        table_id=table_id,
        access_token=access_token,
        field_map=None
    )
    
    if success:
        print("✓ 同步完成")
    else:
        print("✗ 同步失败")
