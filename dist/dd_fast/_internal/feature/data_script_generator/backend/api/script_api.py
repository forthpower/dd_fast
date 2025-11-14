#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据脚本生成器API接口 - 纯脚本生成版
"""

from flask import Blueprint, request, jsonify
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from feature.data_script_generator.backend.generator.script_generator import ScriptGenerator
from feature.data_script_generator.backend.database.db_config import DatabaseConfig

# 创建蓝图
script_api = Blueprint('script_api', __name__)

# 初始化组件
script_generator = ScriptGenerator()
db_config = DatabaseConfig()


@script_api.route('/api/generate', methods=['POST'])
def generate_script():
    """生成数据脚本"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "message": "请求数据不能为空"
            }), 400
        
        # 验证必要字段
        required_fields = ['table_name', 'fields', 'selected_functions']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    "success": False,
                    "message": f"缺少必要字段: {field}"
                }), 400
        
        # 生成脚本
        result = script_generator.generate_script(data)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"生成脚本失败: {str(e)}"
        }), 500


@script_api.route('/api/functions', methods=['GET'])
def get_supported_functions():
    """获取支持的功能列表"""
    try:
        functions = script_generator.supported_functions
        return jsonify({
            "success": True,
            "data": functions
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取功能列表失败: {str(e)}"
        }), 500


@script_api.route('/api/field-types', methods=['GET'])
def get_field_types():
    """获取支持的字段类型"""
    try:
        field_types = [
            {"value": "str", "label": "字符串 (str)"},
            {"value": "int", "label": "整数 (int)"},
            {"value": "float", "label": "浮点数 (float)"},
            {"value": "bool", "label": "布尔值 (bool)"},
            {"value": "datetime", "label": "日期时间 (datetime)"},
            {"value": "date", "label": "日期 (date)"},
            {"value": "text", "label": "长文本 (text)"},
            {"value": "json", "label": "JSON (json)"}
        ]
        return jsonify({
            "success": True,
            "data": field_types
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取字段类型失败: {str(e)}"
        }), 500


@script_api.route('/api/configs', methods=['GET'])
def get_configs():
    """获取所有数据库配置"""
    try:
        configs = db_config.get_all_configs()
        return jsonify({
            "success": True,
            "data": configs
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取配置失败: {str(e)}"
        }), 500


@script_api.route('/api/configs', methods=['POST'])
def save_config():
    """保存数据库配置"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({
                "success": False,
                "message": "配置名称不能为空"
            }), 400
        
        # 添加默认的MySQL配置
        config_data = {
            "type": "mysql",
            "host": data.get("host", "localhost"),
            "port": data.get("port", 3306),
            "username": data.get("username", "root"),
            "password": data.get("password", ""),
            "database": data.get("database", ""),
            "charset": data.get("charset", "utf8mb4"),
            "description": data.get("description", "")
        }
        
        success = db_config.add_config(data['name'], config_data)
        
        if success:
            return jsonify({
                "success": True,
                "message": "配置保存成功"
            })
        else:
            return jsonify({
                "success": False,
                "message": "配置保存失败"
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"保存配置失败: {str(e)}"
        }), 500


@script_api.route('/api/configs/<name>', methods=['DELETE'])
def delete_config(name):
    """删除数据库配置"""
    try:
        success = db_config.delete_config(name)
        
        if success:
            return jsonify({
                "success": True,
                "message": "配置删除成功"
            })
        else:
            return jsonify({
                "success": False,
                "message": "配置删除失败"
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"删除配置失败: {str(e)}"
        }), 500


@script_api.route('/api/configs/<name>/tables', methods=['GET'])
def get_tables(name):
    """获取指定数据库的表列表"""
    try:
        config = db_config.get_config(name)
        if not config:
            return jsonify({
                "success": False,
                "message": "配置不存在"
            }), 404
        
        tables = _get_mysql_tables(config)
        return jsonify({
            "success": True,
            "data": tables
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取表列表失败: {str(e)}"
        }), 500


@script_api.route('/api/configs/<name>/tables/<table_name>/fields', methods=['GET'])
def get_table_fields(name, table_name):
    """获取指定表的字段信息"""
    try:
        config = db_config.get_config(name)
        if not config:
            return jsonify({
                "success": False,
                "message": "配置不存在"
            }), 404
        
        fields = _get_mysql_table_fields(config, table_name)
        return jsonify({
            "success": True,
            "data": fields
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取字段信息失败: {str(e)}"
        }), 500


def _get_mysql_tables(config):
    """获取MySQL表列表"""
    import pymysql
    
    try:
        connection = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['username'],
            password=config['password'],
            database=config['database'],
            charset=config['charset']
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            
        connection.close()
        return tables
        
    except Exception as e:
        raise Exception(f"连接数据库失败: {str(e)}")


def _get_mysql_table_fields(config, table_name):
    """获取MySQL表字段信息"""
    import pymysql
    
    try:
        connection = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['username'],
            password=config['password'],
            database=config['database'],
            charset=config['charset']
        )
        
        with connection.cursor() as cursor:
            cursor.execute(f"DESCRIBE `{table_name}`")
            fields = []
            
            for row in cursor.fetchall():
                field_name = row[0]
                field_type = row[1]
                is_null = row[2]
                key = row[3]
                default = row[4]
                extra = row[5]
                
                # 转换MySQL类型到Python类型
                python_type = _convert_mysql_type_to_python(field_type)
                
                fields.append({
                    "name": field_name,
                    "type": python_type,
                    "mysql_type": field_type,
                    "is_null": is_null == "YES",
                    "is_key": key != "",
                    "default": default,
                    "extra": extra
                })
            
        connection.close()
        return fields
        
    except Exception as e:
        raise Exception(f"获取字段信息失败: {str(e)}")


def _convert_mysql_type_to_python(mysql_type):
    """将MySQL类型转换为Python类型"""
    mysql_type = mysql_type.lower()
    
    if 'int' in mysql_type:
        return 'int'
    elif 'float' in mysql_type or 'double' in mysql_type or 'decimal' in mysql_type:
        return 'float'
    elif 'bool' in mysql_type or 'tinyint(1)' in mysql_type:
        return 'bool'
    elif 'date' in mysql_type and 'time' not in mysql_type:
        return 'date'
    elif 'datetime' in mysql_type or 'timestamp' in mysql_type:
        return 'datetime'
    elif 'text' in mysql_type or 'longtext' in mysql_type or 'mediumtext' in mysql_type:
        return 'text'
    elif 'json' in mysql_type:
        return 'json'
    else:
        return 'str'


@script_api.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "data_script_generator",
        "version": "2.0.0"
    })