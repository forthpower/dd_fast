#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库配置管理
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path


class DatabaseConfig:
    """数据库配置管理类"""
    
    def __init__(self, config_file: str = "db_configs.json"):
        self.config_file = Path(__file__).parent.parent.parent / config_file
        self.configs = self._load_configs()
    
    def _load_configs(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return {}
        return {}
    
    def save_configs(self) -> bool:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.configs, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def add_config(self, name: str, config: Dict[str, Any]) -> bool:
        """添加数据库配置"""
        try:
            # 验证配置格式
            if not self._validate_config(config):
                return False
            
            self.configs[name] = {
                "name": name,
                "type": "mysql",  # 固定为MySQL
                "host": config.get("host", "localhost"),
                "port": config.get("port", 3306),
                "username": config.get("username", ""),
                "password": config.get("password", ""),
                "database": config.get("database", ""),
                "charset": config.get("charset", "utf8mb4"),
                "description": config.get("description", ""),
                "created_at": config.get("created_at", ""),
                "updated_at": config.get("updated_at", "")
            }
            
            return self.save_configs()
        except Exception as e:
            print(f"添加配置失败: {e}")
            return False
    
    def update_config(self, name: str, config: Dict[str, Any]) -> bool:
        """更新数据库配置"""
        if name not in self.configs:
            return False
        
        try:
            # 保留原有配置，只更新提供的字段
            original_config = self.configs[name]
            for key, value in config.items():
                if key in original_config:
                    original_config[key] = value
            
            original_config["updated_at"] = self._get_current_time()
            
            return self.save_configs()
        except Exception as e:
            print(f"更新配置失败: {e}")
            return False
    
    def delete_config(self, name: str) -> bool:
        """删除数据库配置"""
        if name in self.configs:
            del self.configs[name]
            return self.save_configs()
        return False
    
    def get_config(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指定配置"""
        return self.configs.get(name)
    
    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.configs
    
    def get_config_names(self) -> List[str]:
        """获取所有配置名称"""
        return list(self.configs.keys())
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置格式"""
        required_fields = ["host", "port", "username", "database"]
        
        for field in required_fields:
            if field not in config or not config[field]:
                print(f"配置缺少必要字段: {field}")
                return False
        
        # 验证端口号
        try:
            port = int(config["port"])
            if port <= 0 or port > 65535:
                print("端口号必须在1-65535之间")
                return False
        except (ValueError, TypeError):
            print("端口号必须是数字")
            return False
        
        return True
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
