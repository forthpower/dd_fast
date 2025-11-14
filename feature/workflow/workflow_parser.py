#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workflow JSON解析器
解析workflow JSON文件，提取节点、条件、分支等结构信息
"""

import json
from typing import Dict, List, Any, Optional


class WorkflowParser:
    """Workflow解析器类"""
    
    def __init__(self):
        self.nodes = []  # 解析后的节点列表
        self.conditions = []  # 条件列表
        self.connections = []  # 连接关系列表
        self.splits = []  # Split节点列表
        self.raw_data = None  # 原始数据
        
    def parse_json(self, json_data: Dict) -> Dict:
        """
        解析JSON数据
        
        Args:
            json_data: workflow JSON数据
            
        Returns:
            解析后的结构数据
        """
        self.raw_data = json_data
        
        # 清空之前的数据
        self.nodes = []
        self.conditions = []
        self.connections = []
        self.splits = []
        
        # 遍历解析
        if isinstance(json_data, list):
            for workflow in json_data:
                self._parse_workflow(workflow)
        elif isinstance(json_data, dict):
            self._parse_workflow(json_data)
        
        # 分析split节点
        self._analyze_splits()
        
        return {
            "nodes": self.nodes,
            "conditions": self.conditions,
            "connections": self.connections,
            "splits": self.splits,
            "raw_data": self.raw_data
        }
    
    def _parse_workflow(self, workflow: Dict):
        """解析单个workflow"""
        workflow_source = workflow.get("workflow_source", {})
        
        # 获取 workflow.blocks 列表
        workflow_blocks = workflow_source.get("workflow", {})
        blocks = workflow_blocks.get("blocks", [])
        
        if not blocks:
            return
        
        # 解析trigger（通常是第一个block）
        trigger = workflow_source.get("trigger", {})
        trigger_name = trigger.get("name", "Trigger")
        trigger_description = trigger.get("description", "")
        
        # 遍历所有blocks
        for block in blocks:
            block_id = block.get("id")
            block_type = block.get("type", "unknown")
            
            # 如果是trigger类型，使用trigger信息
            if block_type == "TRIGGER":
                name = trigger_name
                description = trigger_description
            else:
                # 其他类型从action中获取信息
                action = block.get("action", {})
                name = action.get("name", "Component")
                description = action.get("description", "")
            
            # 创建节点
            node = self._create_node(
                id_=block_id,
                name=name,
                type_=block_type,
                block_type=block_type,
                description=description,
                data=block
            )
            
            if node:
                self.nodes.append(node)
                
                # 解析outcomes（连接）
                self._parse_block_outcomes(block_id, block)
    
    def _parse_block_outcomes(self, block_id: str, block: Dict):
        """解析block的outcomes"""
        outcomes = block.get("outcomes")
        
        # 如果outcomes为空或不合法，跳过
        if not outcomes or not isinstance(outcomes, dict):
            return
        
        # 解析conditional outcomes
        conditional = outcomes.get("conditional", [])
        for cond in conditional:
            condition_info = None
            
            # 提取条件信息
            condition = cond.get("condition", {})
            if condition:
                condition_info = self._extract_condition_info(condition)
                self.conditions.append(condition_info)
            
            # 创建连接
            next_id = cond.get("next")
            if next_id:
                self.connections.append({
                    "from": block_id,
                    "to": next_id,
                    "label": cond.get("name", "Condition"),
                    "type": "conditional",
                    "condition": condition_info
                })
        
        # 解析default outcome
        default = outcomes.get("default", {})
        if default and isinstance(default, dict):
            next_id = default.get("next")
            if next_id:
                self.connections.append({
                    "from": block_id,
                    "to": next_id,
                    "label": "Default",
                    "type": "default"
                })
    
    def _create_node(self, id_: Any, name: str, type_: str, block_type: str, 
                    description: str, data: Dict) -> Optional[Dict]:
        """创建节点"""
        if not id_:
            return None
            
        return {
            "id": str(id_),
            "name": name,
            "type": type_ or "unknown",
            "block_type": block_type or "unknown",
            "description": description,
            "data": data
        }
    
    def _extract_condition_info(self, condition: Dict) -> Dict:
        """提取条件信息"""
        condition_info = {
            "operator": condition.get("operator", ""),
            "operands": []
        }
        
        operands = condition.get("operands", [])
        for operand in operands:
            operand_info = {
                "type": operand.get("type", ""),
                "operator": operand.get("operator", ""),
                "expression": operand.get("expression", {}),
                "operand": operand.get("operand", {})
            }
            condition_info["operands"].append(operand_info)
        
        return condition_info
    
    def load_from_file(self, file_path: str) -> Dict:
        """
        从文件加载并解析JSON
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            解析后的结构数据
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        return self.parse_json(json_data)
    
    def _analyze_splits(self):
        """分析所有split节点"""
        # 构建blocks索引
        workflow_source = self.raw_data.get("workflow_source", {}) if isinstance(self.raw_data, dict) else {}
        if isinstance(self.raw_data, list) and self.raw_data:
            workflow_source = self.raw_data[0].get("workflow_source", {})
        
        workflow = workflow_source.get("workflow", {})
        blocks = workflow.get("blocks", [])
        
        # 创建blocks索引
        blocks_dict = {block["id"]: block for block in blocks}
        
        # 找到所有ROUTE_SPLITTER节点
        split_blocks = [b for b in blocks if b.get("type") == "ROUTE_SPLITTER"]
        
        for split_block in split_blocks:
            split_info = self._parse_split_block(split_block, blocks_dict)
            if split_info:
                self.splits.append(split_info)
    
    def _parse_split_block(self, split_block: Dict, blocks_dict: Dict) -> Optional[Dict]:
        """解析单个split block"""
        split_id = split_block.get("id")
        split_name = split_block.get("route_splitter_name", "Unknown Split")
        
        # 获取split outcomes
        outcomes = split_block.get("outcomes", [])
        if not outcomes or not isinstance(outcomes, list):
            return None
        
        # 解析每个outcome的分量信息
        routes = []
        for outcome in outcomes:
            split_eval = outcome.get("split_evaluation", {})
            routes.append({
                "name": outcome.get("name", "Unknown"),
                "percentage": split_eval.get("value", 0),
                "type": split_eval.get("type", "PERCENTAGE"),
                "next": outcome.get("next")
            })
        
        # 查找连接到这个split的条件
        condition_info = self._find_split_condition(split_id, blocks_dict)
        
        split_info = {
            "id": split_id,
            "name": split_name,
            "routes": routes,
            "condition": condition_info,
            "total_percentage": sum(r["percentage"] for r in routes),
            "data": split_block  # 保存原始数据以便后续分析
        }
        
        return split_info
    
    def _find_split_condition(self, split_id: str, blocks_dict: Dict) -> Optional[Dict]:
        """查找连接到split的条件"""
        for block_id, block in blocks_dict.items():
            outcomes = block.get("outcomes")
            if not outcomes or not isinstance(outcomes, dict):
                continue
            
            # 检查conditional outcomes
            conditional = outcomes.get("conditional", [])
            for cond in conditional:
                if cond.get("next") == split_id:
                    # 提取条件信息
                    condition = cond.get("condition", {})
                    return {
                        "name": cond.get("name", "Unknown Condition"),
                        "expression": self._extract_condition_expression(condition),
                        "condition": condition
                    }
        
        return None
    
    def _extract_condition_expression(self, condition: Dict) -> str:
        """提取可读的条件表达式"""
        if not condition:
            return ""
        
        operands = condition.get("operands", [])
        if not operands:
            return ""
        
        # 提取第一个操作数作为主要条件
        operand = operands[0]
        expression = operand.get("expression", {})
        operator = operand.get("operator", "")
        operand_value = operand.get("operand", {})
        
        # 提取字段路径 - 处理expression可能是dict或list的情况
        path = ""
        if isinstance(expression, dict):
            path = expression.get("path", "")
        elif isinstance(expression, list) and expression:
            # 如果是列表，尝试从第一个元素获取path
            if isinstance(expression[0], dict):
                path = expression[0].get("path", "")
        
        # 提取值 - 处理operand_value可能是dict或list的情况
        value = ""
        if isinstance(operand_value, dict):
            value = operand_value.get("label") or operand_value.get("value", "")
        elif isinstance(operand_value, list):
            # 如果是列表，尝试转换为字符串或提取第一个元素
            if operand_value:
                if isinstance(operand_value[0], dict):
                    value = operand_value[0].get("label") or operand_value[0].get("value", "")
                else:
                    value = str(operand_value[0])
            else:
                value = ""
        elif operand_value:
            # 其他类型直接转换为字符串
            value = str(operand_value)
        
        # 格式化显示
        if operator and path and value:
            return f"{path} {operator} {value}"
        
        return json.dumps(operand, ensure_ascii=False)
    
    def get_summary(self) -> Dict:
        """获取解析摘要"""
        return {
            "total_nodes": len(self.nodes),
            "total_conditions": len(self.conditions),
            "total_connections": len(self.connections),
            "total_splits": len(self.splits),
            "node_types": list(set([node["type"] for node in self.nodes])),
            "condition_operators": list(set([cond["operator"] for cond in self.conditions]))
        }
