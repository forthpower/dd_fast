#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Split配置对比器
解析用户提供的调整方案，对比workflow中的split配置，生成修改建议
"""

import re
from typing import Dict, List, Any, Optional, Tuple
try:
    from workflow_parser import WorkflowParser
except ImportError:
    from feature.workflow.workflow_parser import WorkflowParser


class SplitComparator:
    """Split配置对比器"""
    
    def __init__(self):
        self.parser = WorkflowParser()
    
    def parse_adjustment_text(self, text: str) -> Dict[str, Dict[str, Dict[str, List[int]]]]:
        """
        解析调整方案文本
        
        格式示例:
        CARD
        USD - 20%：40%：40%
        KRW/EUR/AED - 40%：20%：40%
        
        Args:
            text: 调整方案文本
            
        Returns:
            解析后的配置字典: {支付方式: {币种: [Adyen%, Stripe%, AWX%]}}
        """
        result = {}
        current_payment_method = None
        
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('@') or line.startswith('【') or line.startswith('*'):
                continue
            
            # 检测支付方式（CARD, AP, GP等）
            # 支持全大写字母的支付方式名称
            payment_match = re.match(r'^([A-Z]+)$', line)
            if payment_match:
                payment_name = payment_match.group(1)
                # 标准化支付方式名称
                if payment_name == 'CARD':
                    current_payment_method = 'CARD'
                elif payment_name == 'AP':
                    current_payment_method = 'AP'
                elif payment_name == 'GP':
                    current_payment_method = 'GP'
                else:
                    current_payment_method = payment_name
                result[current_payment_method] = {}
                continue
            
            # 检测币种和分量配置
            # 格式: 币种 - 20%：40%：40% 或 币种1/币种2/币种3 - 20%：40%：40% 或 - 币种 - 20%：40%：40%
            if current_payment_method:
                # 匹配币种和百分比（支持中文币种名称，支持行首的 `- ` 前缀）
                # 币种部分：可以包含字母、数字、中文字符、斜杠
                # 支持格式：`TWD - 30%：30%：40%` 或 `- TWD - 30%：30%：40%`
                # 先去除行首的 `- ` 前缀（如果存在）
                line_cleaned = line.strip()
                if line_cleaned.startswith('- '):
                    line_cleaned = line_cleaned[2:].strip()
                
                pattern = r'^([A-Za-z0-9\u4e00-\u9fa5/]+)\s*-\s*(\d+)%[：:]\s*(\d+)%[：:]\s*(\d+)%'
                match = re.match(pattern, line_cleaned)
                if match:
                    currencies_str = match.group(1)
                    adyen_pct = int(match.group(2))
                    stripe_pct = int(match.group(3))
                    awx_pct = int(match.group(4))
                    
                    # 分割多个币种
                    currencies = [c.strip() for c in currencies_str.split('/')]
                    
                    for currency in currencies:
                        if currency not in result[current_payment_method]:
                            result[current_payment_method][currency] = []
                        result[current_payment_method][currency] = [adyen_pct, stripe_pct, awx_pct]
        
        return result
    
    def extract_current_splits(self, workflow_data: Dict) -> Dict[str, List[Dict]]:
        """
        从workflow数据中提取当前的split配置
        
        Args:
            workflow_data: workflow JSON数据
            
        Returns:
            {支付方式: [split配置列表]}
        """
        # 解析workflow
        parsed = self.parser.parse_json(workflow_data)
        
        # 按支付方式和币种组织split数据
        splits_by_method = {}
        
        for split in parsed.get("splits", []):
            # 从split名称或条件中提取支付方式和币种信息
            split_name = split.get("name", "")
            condition = split.get("condition", {})
            
            # 尝试从条件表达式中提取信息
            expression = condition.get("expression", "") if condition else ""
            
            # 解析split名称和条件来确定支付方式和币种
            # 这里需要根据实际的workflow结构来调整
            payment_method, currency = self._extract_payment_info(split_name, expression, split)
            
            if not payment_method:
                payment_method = "UNKNOWN"  # 其他币种
            if not currency:
                currency = "UNKNOWN"  # 其他币种
            
            key = f"{payment_method}_{currency}"
            if payment_method not in splits_by_method:
                splits_by_method[payment_method] = {}
            
            if currency not in splits_by_method[payment_method]:
                splits_by_method[payment_method][currency] = []
            
            splits_by_method[payment_method][currency].append({
                "id": split.get("id"),
                "name": split_name,
                "routes": split.get("routes", []),
                "condition": condition,
                "expression": expression
            })
        
        return splits_by_method
    
    def _extract_payment_info(self, split_name: str, expression: str, split: Dict) -> Tuple[Optional[str], Optional[str]]:
        """
        从split信息中提取支付方式和币种
        
        Args:
            split_name: split名称
            expression: 条件表达式
            split: split完整数据
            
        Returns:
            (支付方式, 币种)
        """
        payment_method = None
        currency = None
        
        # 尝试从split名称中提取
        name_upper = split_name.upper()
        if 'CARD' in name_upper or 'CREDIT' in name_upper or 'DEBIT' in name_upper:
            payment_method = 'CARD'
        elif 'AP' in name_upper or 'APPLE' in name_upper or 'APPLEPAY' in name_upper:
            payment_method = 'AP'
        elif 'GP' in name_upper or 'GOOGLE' in name_upper or 'GOOGLEPAY' in name_upper:
            payment_method = 'GP'
        
        # 尝试从条件表达式中提取币种和支付方式
        if expression:
            # 查找币种代码（3个大写字母，排除常见的非币种词）
            currency_pattern = r'\b([A-Z]{3})\b'
            currency_matches = re.findall(currency_pattern, expression)
            # 常见的币种代码
            common_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CNY', 'KRW', 'AUD', 'CAD', 'CHF', 
                               'NZD', 'SGD', 'HKD', 'TWD', 'THB', 'AED', 'PHP', 'INR', 'BRL']
            for match in currency_matches:
                if match in common_currencies:
                    currency = match
                    break
            
            # 从表达式中提取支付方式
            if not payment_method:
                expr_upper = expression.upper()
                if 'CARD' in expr_upper or 'CREDIT' in expr_upper or 'DEBIT' in expr_upper:
                    payment_method = 'CARD'
                elif 'AP' in expr_upper or 'APPLE' in expr_upper:
                    payment_method = 'AP'
                elif 'GP' in expr_upper or 'GOOGLE' in expr_upper:
                    payment_method = 'GP'
        
        # 尝试从routes名称中提取信息
        routes = split.get("routes", [])
        for route in routes:
            route_name = route.get("name", "").upper()
            if not payment_method:
                if 'CARD' in route_name or 'CREDIT' in route_name or 'DEBIT' in route_name:
                    payment_method = 'CARD'
                elif 'AP' in route_name or 'APPLE' in route_name:
                    payment_method = 'AP'
                elif 'GP' in route_name or 'GOOGLE' in route_name:
                    payment_method = 'GP'
            
            # 从route名称中提取币种
            if not currency:
                currency_matches = re.findall(r'\b([A-Z]{3})\b', route_name)
                common_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CNY', 'KRW', 'AUD', 'CAD', 'CHF', 
                                   'NZD', 'SGD', 'HKD', 'TWD', 'THB', 'AED', 'PHP', 'INR', 'BRL']
                for match in currency_matches:
                    if match in common_currencies:
                        currency = match
                        break
        
        # 尝试从split的原始数据中提取
        split_data = split.get("data", {})
        if isinstance(split_data, dict):
            # 查找条件块
            condition_data = split_data.get("condition", {})
            if condition_data:
                # 从operands中提取信息
                operands = condition_data.get("operands", [])
                for operand in operands:
                    expr = operand.get("expression", {})
                    if isinstance(expr, dict):
                        path = expr.get("path", "")
                        path_upper = path.upper()
                        if not payment_method:
                            if 'CARD' in path_upper or 'CREDIT' in path_upper or 'DEBIT' in path_upper:
                                payment_method = 'CARD'
                            elif 'AP' in path_upper or 'APPLE' in path_upper:
                                payment_method = 'AP'
                            elif 'GP' in path_upper or 'GOOGLE' in path_upper:
                                payment_method = 'GP'
                        
                        # 从path中提取币种
                        if not currency:
                            currency_matches = re.findall(r'\b([A-Z]{3})\b', path)
                            common_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CNY', 'KRW', 'AUD', 'CAD', 'CHF', 
                                               'NZD', 'SGD', 'HKD', 'TWD', 'THB', 'AED', 'PHP', 'INR', 'BRL']
                            for match in currency_matches:
                                if match in common_currencies:
                                    currency = match
                                    break
                    
                    # 从operand值中提取币种
                    operand_value = operand.get("operand", {})
                    if isinstance(operand_value, dict):
                        value = operand_value.get("value", "")
                        if isinstance(value, str):
                            currency_matches = re.findall(r'\b([A-Z]{3})\b', value.upper())
                            common_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CNY', 'KRW', 'AUD', 'CAD', 'CHF', 
                                               'NZD', 'SGD', 'HKD', 'TWD', 'THB', 'AED', 'PHP', 'INR', 'BRL']
                            if not currency:
                                for match in currency_matches:
                                    if match in common_currencies:
                                        currency = match
                                        break
        
        return payment_method, currency
    
    def compare_configurations(self, workflow_data: Dict, adjustment_text: str, adjustment_mode: str = "update") -> Dict[str, Any]:
        """
        对比当前配置和调整方案，生成修改建议
        
        Args:
            workflow_data: workflow JSON数据
            adjustment_text: 调整方案文本
            adjustment_mode: 调整模式，"update"（更新调整）或 "override"（覆盖调整）
            
        Returns:
            对比结果和建议
        """
        # 解析调整方案
        new_config = self.parse_adjustment_text(adjustment_text)
        
        # 提取当前配置
        current_splits = self.extract_current_splits(workflow_data)
        
        # 生成对比结果
        comparison_result = {
            "current_config": {},
            "new_config": new_config,
            "changes": [],
            "summary": {
                "payment_methods_to_add": [],
                "payment_methods_to_remove": [],
                "currencies_to_add": {},
                "currencies_to_remove": {},
                "currencies_to_modify": {},
                "currencies_to_merge": []
            }
        }
        
        # 组织当前配置以便对比
        for payment_method, currencies in current_splits.items():
            comparison_result["current_config"][payment_method] = {}
            for currency, splits in currencies.items():
                # 提取当前的分量配置
                routes = splits[0].get("routes", []) if splits else []
                percentages = [r.get("percentage", 0) for r in routes]
                comparison_result["current_config"][payment_method][currency] = {
                    "percentages": percentages,
                    "routes": [r.get("name") for r in routes],
                    "split_id": splits[0].get("id") if splits else None
                }
        
        # 对比每个支付方式
        all_payment_methods = set(list(new_config.keys()) + list(comparison_result["current_config"].keys()))
        
        for payment_method in all_payment_methods:
            current_currencies = comparison_result["current_config"].get(payment_method, {})
            new_currencies = new_config.get(payment_method, {})
            
            all_currencies = set(list(current_currencies.keys()) + list(new_currencies.keys()))
            
            for currency in all_currencies:
                current_config = current_currencies.get(currency)
                new_config_currency = new_currencies.get(currency)
                
                change_info = {
                    "payment_method": payment_method,
                    "currency": currency,
                    "action": None,
                    "current": None,
                    "new": None,
                    "instructions": []
                }
                
                if current_config and new_config_currency:
                    # 需要修改
                    current_pct = current_config.get("percentages", [])
                    new_pct = new_config_currency
                    
                    if current_pct != new_pct:
                        change_info["action"] = "modify"
                        change_info["current"] = {
                            "percentages": current_pct,
                            "routes": current_config.get("routes", [])
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
                
                elif current_config and not new_config_currency:
                    # 需要删除
                    change_info["action"] = "remove"
                    change_info["current"] = {
                        "percentages": current_config.get("percentages", []),
                        "routes": current_config.get("routes", []),
                        "split_id": current_config.get("split_id")
                    }
                    change_info["instructions"] = [
                        f"删除 {payment_method} - {currency} 的split配置"
                    ]
                    comparison_result["changes"].append(change_info)
                    if payment_method not in comparison_result["summary"]["currencies_to_remove"]:
                        comparison_result["summary"]["currencies_to_remove"][payment_method] = []
                    comparison_result["summary"]["currencies_to_remove"][payment_method].append(currency)
                
                elif not current_config and new_config_currency:
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
        
        # 检查需要合并的币种（在调整方案中用/分隔的）
        for payment_method, currencies in new_config.items():
            for currency_key, percentages in currencies.items():
                if '/' in currency_key:
                    # 多个币种使用相同配置，需要合并
                    currency_list = currency_key.split('/')
                    comparison_result["summary"]["currencies_to_merge"].append({
                        "payment_method": payment_method,
                        "currencies": currency_list,
                        "percentages": percentages
                    })
        
        # 生成完整的分量对比（之前 vs 现在）
        final_config = self._generate_final_config(
            comparison_result["current_config"],
            new_config,
            adjustment_mode
        )
        
        # 格式化显示配置，相同分量的币种合并
        before_formatted = self._format_config_for_display(comparison_result["current_config"])
        after_formatted = self._format_config_for_display(final_config)
        
        # 确保所有币种都出现在对比中（包括未调整的）
        before_formatted, after_formatted = self._merge_comparison_configs(
            before_formatted, 
            after_formatted, 
            comparison_result["current_config"],
            final_config
        )
        
        comparison_result["full_comparison"] = {
            "before": before_formatted,
            "after": after_formatted
        }
        
        return comparison_result
    
    def _generate_final_config(self, current_config: Dict, new_config: Dict, adjustment_mode: str) -> Dict:
        """
        根据调整模式生成最终配置
        
        Args:
            current_config: 当前配置
            new_config: 新配置
            adjustment_mode: 调整模式，"update"或"override"
            
        Returns:
            最终配置
        """
        final_config = {}
        
        if adjustment_mode == "override":
            # 覆盖调整：完全按照新配置
            for payment_method, currencies in new_config.items():
                final_config[payment_method] = {}
                for currency_key, percentages in currencies.items():
                    # 处理合并的币种（用/分隔的）
                    if '/' in currency_key:
                        currency_list = currency_key.split('/')
                        for currency in currency_list:
                            currency = currency.strip()
                            final_config[payment_method][currency] = {
                                "percentages": percentages.copy()
                            }
                    else:
                        final_config[payment_method][currency_key] = {
                            "percentages": percentages.copy()
                        }
        else:
            # 更新调整：只更新需要调整的，其他保持原样
            # 先复制当前配置
            for payment_method, currencies in current_config.items():
                final_config[payment_method] = {}
                for currency, config in currencies.items():
                    final_config[payment_method][currency] = {
                        "percentages": config.get("percentages", []).copy()
                    }
            
            # 应用新配置
            for payment_method, currencies in new_config.items():
                if payment_method not in final_config:
                    final_config[payment_method] = {}
                
                for currency_key, percentages in currencies.items():
                    # 处理合并的币种（用/分隔的）
                    if '/' in currency_key:
                        currency_list = currency_key.split('/')
                        for currency in currency_list:
                            currency = currency.strip()
                            final_config[payment_method][currency] = {
                                "percentages": percentages.copy()
                            }
                    else:
                        final_config[payment_method][currency_key] = {
                            "percentages": percentages.copy()
                        }
        
        return final_config
    
    def _format_config_for_display(self, config: Dict) -> Dict[str, Dict[str, List[int]]]:
        """
        格式化配置用于显示，将UNKNOWN改为"其他币种"，并将相同分量的币种合并
        
        Args:
            config: 配置字典
            
        Returns:
            格式化后的配置，相同分量的币种用'/'分隔
        """
        formatted = {}
        for payment_method, currencies in config.items():
            formatted_payment = "其他币种" if payment_method == "UNKNOWN" else payment_method
            formatted[formatted_payment] = {}
            
            # 按分量分组币种
            percentages_to_currencies = {}
            for currency, config_data in currencies.items():
                formatted_currency = "其他币种" if currency == "UNKNOWN" else currency
                percentages = config_data.get("percentages", [])
                if percentages:
                    # 将百分比列表转换为元组作为key
                    pct_key = tuple(percentages)
                    if pct_key not in percentages_to_currencies:
                        percentages_to_currencies[pct_key] = []
                    percentages_to_currencies[pct_key].append(formatted_currency)
            
            # 将相同分量的币种合并，用'/'分隔
            for pct_key, currency_list in percentages_to_currencies.items():
                if len(currency_list) == 1:
                    # 只有一个币种，直接使用
                    formatted[formatted_payment][currency_list[0]] = list(pct_key)
                else:
                    # 多个币种，用'/'分隔
                    currency_key = '/'.join(sorted(currency_list))
                    formatted[formatted_payment][currency_key] = list(pct_key)
        
        return formatted
    
    def _merge_comparison_configs(self, before_formatted: Dict, after_formatted: Dict, 
                                   before_raw: Dict, after_raw: Dict) -> Tuple[Dict, Dict]:
        """
        合并对比配置，确保所有币种都出现，包括未调整的
        相同分量的币种合并显示，用'/'分隔
        
        Args:
            before_formatted: 格式化后的之前配置
            after_formatted: 格式化后的之后配置
            before_raw: 原始之前配置
            after_raw: 原始之后配置
            
        Returns:
            (合并后的之前配置, 合并后的之后配置)
        """
        # 获取所有支付方式和币种
        all_payment_methods = set(list(before_raw.keys()) + list(after_raw.keys()))
        
        merged_before = {}
        merged_after = {}
        
        for payment_method in all_payment_methods:
            formatted_payment = "其他币种" if payment_method == "UNKNOWN" else payment_method
            
            before_currencies = before_raw.get(payment_method, {})
            after_currencies = after_raw.get(payment_method, {})
            
            # 收集所有币种（包括单独的币种和合并的币种）
            all_currency_items = set()
            
            # 从之前配置中收集所有币种
            for currency_key in before_formatted.get(formatted_payment, {}).keys():
                all_currency_items.add(currency_key)
            
            # 从之后配置中收集所有币种
            for currency_key in after_formatted.get(formatted_payment, {}).keys():
                all_currency_items.add(currency_key)
            
            # 从原始配置中收集所有单独的币种（用于处理未调整的币种）
            for currency in before_currencies.keys():
                formatted_currency = "其他币种" if currency == "UNKNOWN" else currency
                # 检查这个币种是否已经在合并的键中
                found = False
                for existing_key in all_currency_items:
                    if formatted_currency in existing_key.split('/'):
                        found = True
                        break
                if not found:
                    all_currency_items.add(formatted_currency)
            
            for currency in after_currencies.keys():
                formatted_currency = "其他币种" if currency == "UNKNOWN" else currency
                found = False
                for existing_key in all_currency_items:
                    if formatted_currency in existing_key.split('/'):
                        found = True
                        break
                if not found:
                    all_currency_items.add(formatted_currency)
            
            # 构建合并后的配置
            merged_before[formatted_payment] = {}
            merged_after[formatted_payment] = {}
            
            # 处理每个币种项（可能是单个币种或合并的币种）
            for currency_item in all_currency_items:
                # 从之前配置中获取分量
                if currency_item in before_formatted.get(formatted_payment, {}):
                    merged_before[formatted_payment][currency_item] = before_formatted[formatted_payment][currency_item]
                else:
                    # 如果不在格式化配置中，尝试从原始配置中查找
                    # 检查是否是合并的币种
                    currencies_in_item = currency_item.split('/')
                    if len(currencies_in_item) == 1:
                        # 单个币种，从原始配置查找
                        original_currency = currencies_in_item[0]
                        # 需要找到原始币种名（可能是UNKNOWN）
                        for orig_curr, config_data in before_currencies.items():
                            formatted_curr = "其他币种" if orig_curr == "UNKNOWN" else orig_curr
                            if formatted_curr == original_currency:
                                pct = config_data.get("percentages", [])
                                if pct:
                                    merged_before[formatted_payment][currency_item] = pct
                                break
                
                # 从之后配置中获取分量
                if currency_item in after_formatted.get(formatted_payment, {}):
                    merged_after[formatted_payment][currency_item] = after_formatted[formatted_payment][currency_item]
                else:
                    # 如果不在格式化配置中，检查是否应该保持原样（未调整的币种）
                    currencies_in_item = currency_item.split('/')
                    if len(currencies_in_item) == 1:
                        # 单个币种，检查是否在之前存在
                        if currency_item in merged_before[formatted_payment]:
                            # 未调整的币种，保持原样
                            merged_after[formatted_payment][currency_item] = merged_before[formatted_payment][currency_item]
                        else:
                            # 新添加的币种，从原始配置查找
                            original_currency = currencies_in_item[0]
                            for orig_curr, config_data in after_currencies.items():
                                formatted_curr = "其他币种" if orig_curr == "UNKNOWN" else orig_curr
                                if formatted_curr == original_currency:
                                    pct = config_data.get("percentages", [])
                                    if pct:
                                        merged_after[formatted_payment][currency_item] = pct
                                    break
        
        return merged_before, merged_after

