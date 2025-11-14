#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据脚本生成器核心逻辑 - 纯脚本生成版
不需要数据库连接，根据用户选择生成Python脚本
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime


class ScriptGenerator:
    """数据脚本生成器 - 纯脚本生成版"""
    
    def __init__(self):
        self.supported_functions = [
            "query_data",      # 查询数据
            "count_data",      # 统计数据
            "insert_data",     # 插入数据
            "update_data",     # 更新数据
            "delete_data",     # 删除数据
            "batch_insert",    # 批量插入
            "batch_update",    # 批量更新
            "batch_delete"     # 批量删除
        ]
    
    def generate_script(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """生成Python脚本"""
        try:
            # 验证配置
            validation_result = self._validate_generation_config(config)
            if not validation_result["valid"]:
                return {"success": False, "message": validation_result["message"]}
            
            # 生成Python脚本
            return self._generate_python_script(config)
                
        except Exception as e:
            return {"success": False, "message": f"生成脚本失败: {str(e)}"}
    
    def _validate_generation_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证生成配置"""
        required_fields = ["table_name", "fields", "selected_functions"]
        
        for field in required_fields:
            if field not in config or not config[field]:
                return {"valid": False, "message": f"缺少必要字段: {field}"}
        
        return {"valid": True, "message": "配置验证通过"}
    
    def _generate_python_script(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """生成Python脚本"""
        try:
            script_content = self._build_python_script(config)
            
            return {
                "success": True,
                "script": script_content,
                "filename": f"{config['table_name']}_data_script.py",
                "language": "python"
            }
        except Exception as e:
            return {"success": False, "message": f"生成Python脚本失败: {str(e)}"}
    
    def _build_python_script(self, config: Dict[str, Any]) -> str:
        """构建Python脚本内容"""
        table_name = config["table_name"]
        fields = config["fields"]
        selected_functions = config["selected_functions"]
        db_config = config.get("db_config", {})
        custom_conditions = config.get("custom_conditions", {})
        
        # 生成字段列表
        field_names = [field["name"] for field in fields]
        field_types = {field["name"]: field.get("type", "str") for field in fields}
        
        # 生成脚本模板
        script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{table_name} 数据操作脚本
自动生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

import pymysql
import json
from typing import List, Dict, Any, Optional


class {table_name.title().replace('_', '')}DataScript:
    """{table_name} 数据操作类"""
    
    def __init__(self):
        # 数据库配置 - 请根据实际情况修改
        self.db_config = {json.dumps(db_config, indent=8, ensure_ascii=False)}
        self.table_name = "{table_name}"
        self.connection = None
        
        # 表字段定义
        self.fields = {json.dumps(field_names, ensure_ascii=False)}
        self.field_types = {json.dumps(field_types, ensure_ascii=False)}
    
    def connect(self):
        """连接数据库"""
        try:
            self.connection = pymysql.connect(
                host=self.db_config.get("host", "localhost"),
                port=self.db_config.get("port", 3306),
                user=self.db_config.get("username", "root"),
                password=self.db_config.get("password", ""),
                database=self.db_config.get("database", ""),
                charset=self.db_config.get("charset", "utf8mb4")
            )
            print("✅ 数据库连接成功")
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {{e}}")
            return False
    
    def __del__(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            print("✅ 数据库连接已关闭")

'''
        
        # 根据用户选择的功能生成对应的方法
        if "query_data" in selected_functions:
            script += self._generate_query_data_method(table_name, field_names, custom_conditions)
        
        if "count_data" in selected_functions:
            script += self._generate_count_data_method(table_name, custom_conditions)
        
        if "insert_data" in selected_functions:
            script += self._generate_insert_data_method(table_name, field_names)
        
        if "update_data" in selected_functions:
            script += self._generate_update_data_method(table_name, field_names, custom_conditions)
        
        if "delete_data" in selected_functions:
            script += self._generate_delete_data_method(table_name, custom_conditions)
        
        if "batch_insert" in selected_functions:
            script += self._generate_batch_insert_method(table_name, field_names)
        
        if "batch_update" in selected_functions:
            script += self._generate_batch_update_method(table_name, field_names, custom_conditions.get("batch_update_conditions", []))
        
        if "batch_delete" in selected_functions:
            script += self._generate_batch_delete_method(table_name, custom_conditions.get("batch_delete_conditions", []))
        
        # 添加使用示例
        script += self._generate_usage_example(table_name, selected_functions)
        
        return script
    
    def _generate_query_data_method(self, table_name: str, field_names: List[str], custom_conditions: Dict[str, Any]) -> str:
        """生成查询数据方法"""
        # 获取查询配置
        query_config = custom_conditions.get('query_conditions', {})
        default_limit = query_config.get('limit', 100)
        default_offset = query_config.get('offset', 0)
        order_by = query_config.get('order_by', '')
        order_direction = query_config.get('order_direction', 'ASC')
        where_conditions = query_config.get('where_conditions', [])
        
        # 判断是否全选字段（简化逻辑：如果字段数量大于等于5个就使用SELECT *）
        use_select_all = len(field_names) >= 5
        fields_sql = "*" if use_select_all else ", ".join([f"`{field}`" for field in field_names])
        
        # 生成字段验证逻辑
        field_validation = ""
        if not use_select_all:
            field_validation = f'''
        # 验证查询字段是否在表字段中
        invalid_fields = [field for field in self.fields if field not in {json.dumps(field_names, ensure_ascii=False)}]
        if invalid_fields:
            print(f"警告：以下字段不在查询范围内: {{invalid_fields}}")'''
        
        # 构建ORDER BY子句
        order_by_clause = ""
        if order_by:
            order_by_clause = f'''
                
                # 添加排序
                sql += f" ORDER BY `{order_by}` {order_direction}"'''
        
        method = f'''
    def query_data(self, limit: int = {default_limit}, offset: int = {default_offset}, where_clause: str = "") -> List[Dict[str, Any]]:
        """查询数据（分批查询）"""
        if not self.connection:
            print("请先连接数据库")
            return []
        
        {field_validation}
        
        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = f"SELECT {fields_sql} FROM `{{self.table_name}}`"
                
                if where_clause:
                    sql += f" WHERE {{where_clause}}"{order_by_clause}
                
                sql += f" LIMIT {{limit}} OFFSET {{offset}}"
                
                cursor.execute(sql)
                results = cursor.fetchall()
                print(f"查询完成，获取 {{len(results)}} 条记录")
                return results
                
        except Exception as e:
            print(f"查询失败: {{e}}")
            return []
'''
        
        # 添加批量查询方法
        method += f'''
    
    def query_all_data(self, where_clause: str = "", batch_size: int = {default_limit}) -> List[Dict[str, Any]]:
        """批量查询所有数据（自动分批处理）"""
        if not self.connection:
            print("请先连接数据库")
            return []
        
        all_results = []
        offset = 0
        batch_count = 0
        
        print(f"开始批量查询，每批 {{batch_size}} 条")
        
        while True:
            batch_count += 1
            batch_results = self.query_data(limit=batch_size, offset=offset, where_clause=where_clause)
            
            if not batch_results:
                break
                
            all_results.extend(batch_results)
            offset += batch_size
            
            if len(batch_results) < batch_size:
                break
        
        print(f"批量查询完成，共获取 {{len(all_results)}} 条记录")
        return all_results
'''
        
        # 添加预定义查询条件
        if where_conditions:
            method += f'''
    
    def query_by_conditions(self) -> List[Dict[str, Any]]:
        """根据预定义条件查询数据"""
        if not self.connection:
            return []
        
        results = []
        for condition in {json.dumps(where_conditions, ensure_ascii=False)}:
            data = self.query_data(where_clause=condition)
            results.extend(data)
        
        return results
'''
        
        return method
    
    def _generate_count_data_method(self, table_name: str, custom_conditions: Dict[str, Any]) -> str:
        """生成统计数据方法"""
        count_config = custom_conditions.get('count_conditions', {})
        where_conditions = count_config.get('where_conditions', [])
        
        method = f'''
    def count_data(self, where_clause: str = "") -> int:
        """统计数据条数"""
        if not self.connection:
            print("请先连接数据库")
            return 0
        
        try:
            with self.connection.cursor() as cursor:
                sql = f"SELECT COUNT(*) FROM `{{self.table_name}}`"
                if where_clause:
                    sql += f" WHERE {{where_clause}}"
                cursor.execute(sql)
                count = cursor.fetchone()[0]
                print(f"数据总数: {{count}}")
                return count
        except Exception as e:
            print(f"统计失败: {{e}}")
            return 0
'''
        
        # 添加预定义统计条件
        if where_conditions:
            method += f'''
    
    def count_by_conditions(self) -> Dict[str, int]:
        """根据预定义条件统计数据"""
        if not self.connection:
            return {{}}
        
        counts = {{}}
        for condition in {json.dumps(where_conditions, ensure_ascii=False)}:
            counts[condition] = self.count_data(where_clause=condition)
        return counts
'''
        
        return method
    
    def _generate_insert_data_method(self, table_name: str, field_names: List[str]) -> str:
        """生成插入数据方法"""
        return f'''
    def insert_data(self, data: Dict[str, Any]) -> bool:
        """插入数据"""
        if not self.connection:
            print("请先连接数据库")
            return False
        
        # 验证字段是否在表字段中
        invalid_fields = [field for field in data.keys() if field not in self.fields]
        if invalid_fields:
            print(f"警告：以下字段不在表字段中: {{invalid_fields}}")
            return False
        
        try:
            with self.connection.cursor() as cursor:
                fields = list(data.keys())
                values = list(data.values())
                placeholders = ", ".join(["%s"] * len(fields))
                sql = f"INSERT INTO `{{self.table_name}}` ({{', '.join([f'`{{f}}`' for f in fields])}}) VALUES ({{placeholders}})"
                cursor.execute(sql, values)
                self.connection.commit()
                print(f"插入成功，影响行数: {{cursor.rowcount}}")
                return True
        except Exception as e:
            print(f"插入失败: {{e}}")
            self.connection.rollback()
            return False
'''
    
    def _generate_update_data_method(self, table_name: str, field_names: List[str], custom_conditions: Dict[str, Any]) -> str:
        """生成更新数据方法"""
        update_config = custom_conditions.get('update_conditions', {})
        where_conditions = update_config.get('where_conditions', [])
        
        method = f'''
    def update_data(self, data: Dict[str, Any], where_clause: str) -> bool:
        """更新数据"""
        if not self.connection:
            print("请先连接数据库")
            return False
        
        # 验证字段是否在表字段中
        invalid_fields = [field for field in data.keys() if field not in self.fields]
        if invalid_fields:
            print(f"警告：以下字段不在表字段中: {{invalid_fields}}")
            return False
        
        try:
            with self.connection.cursor() as cursor:
                set_clause = ", ".join([f"`{{k}}` = %s" for k in data.keys()])
                sql = f"UPDATE `{{self.table_name}}` SET {{set_clause}} WHERE {{where_clause}}"
                cursor.execute(sql, list(data.values()))
                self.connection.commit()
                print(f"更新成功，影响行数: {{cursor.rowcount}}")
                return True
        except Exception as e:
            print(f"更新失败: {{e}}")
            self.connection.rollback()
            return False
'''
        
        # 添加预定义更新条件
        if where_conditions:
            method += f'''
    
    def update_by_conditions(self, data: Dict[str, Any]) -> Dict[str, bool]:
        """根据预定义条件更新数据"""
        if not self.connection:
            return {{}}
        
        results = {{}}
        for condition in {json.dumps(where_conditions, ensure_ascii=False)}:
            results[condition] = self.update_data(data, condition)
        return results
'''
        
        return method
    
    def _generate_delete_data_method(self, table_name: str, custom_conditions: Dict[str, Any]) -> str:
        """生成删除数据方法"""
        delete_config = custom_conditions.get('delete_conditions', {})
        where_conditions = delete_config.get('where_conditions', [])
        
        method = f'''
    def delete_data(self, where_clause: str) -> bool:
        """删除数据"""
        if not self.connection:
            print("请先连接数据库")
            return False
        
        try:
            with self.connection.cursor() as cursor:
                sql = f"DELETE FROM `{{self.table_name}}` WHERE {{where_clause}}"
                cursor.execute(sql)
                self.connection.commit()
                print(f"删除成功，影响行数: {{cursor.rowcount}}")
                return True
        except Exception as e:
            print(f"删除失败: {{e}}")
            self.connection.rollback()
            return False
'''
        
        # 添加预定义删除条件
        if where_conditions:
            method += f'''
    
    def delete_by_conditions(self) -> Dict[str, bool]:
        """根据预定义条件删除数据"""
        if not self.connection:
            return {{}}
        
        results = {{}}
        for condition in {json.dumps(where_conditions, ensure_ascii=False)}:
            results[condition] = self.delete_data(condition)
        return results
'''
        
        return method
    
    def _generate_batch_insert_method(self, table_name: str, field_names: List[str]) -> str:
        """生成批量插入方法"""
        return f'''
    def batch_insert_data(self, data_list: List[Dict[str, Any]]) -> bool:
        """批量插入数据"""
        if not self.connection:
            print("请先连接数据库")
            return False
        
        if not data_list:
            print("数据列表为空")
            return False
        
        # 验证所有数据的字段是否在表字段中
        all_fields = set()
        for data in data_list:
            all_fields.update(data.keys())
        
        invalid_fields = [field for field in all_fields if field not in self.fields]
        if invalid_fields:
            print(f"警告：以下字段不在表字段中: {{invalid_fields}}")
            return False
        
        try:
            with self.connection.cursor() as cursor:
                first_data = data_list[0]
                fields = list(first_data.keys())
                placeholders = ", ".join(["%s"] * len(fields))
                sql = f"INSERT INTO `{{self.table_name}}` ({{', '.join([f'`{{f}}`' for f in fields])}}) VALUES ({{placeholders}})"
                
                values_list = []
                for data in data_list:
                    values_list.append([data.get(field, None) for field in fields])
                
                cursor.executemany(sql, values_list)
                self.connection.commit()
                print(f"批量插入成功，影响行数: {{cursor.rowcount}}")
                return True
        except Exception as e:
            print(f"批量插入失败: {{e}}")
            self.connection.rollback()
            return False
'''
    
    def _generate_batch_update_method(self, table_name: str, field_names: List[str], conditions: List[str]) -> str:
        """生成批量更新方法"""
        return f'''
    def batch_update_data(self, data: Dict[str, Any], where_clause: str) -> bool:
        """批量更新数据"""
        if not self.connection:
            print("请先连接数据库")
            return False
        
        # 验证字段是否在表字段中
        invalid_fields = [field for field in data.keys() if field not in self.fields]
        if invalid_fields:
            print(f"警告：以下字段不在表字段中: {{invalid_fields}}")
            return False
        
        try:
            with self.connection.cursor() as cursor:
                set_clause = ", ".join([f"`{{k}}` = %s" for k in data.keys()])
                sql = f"UPDATE `{{self.table_name}}` SET {{set_clause}} WHERE {{where_clause}}"
                cursor.execute(sql, list(data.values()))
                self.connection.commit()
                print(f"批量更新成功，影响行数: {{cursor.rowcount}}")
                return True
        except Exception as e:
            print(f"批量更新失败: {{e}}")
            self.connection.rollback()
            return False
'''
    
    def _generate_batch_delete_method(self, table_name: str, conditions: List[str]) -> str:
        """生成批量删除方法"""
        return f'''
    def batch_delete_data(self, where_clause: str) -> bool:
        """批量删除数据"""
        if not self.connection:
            print("请先连接数据库")
            return False
        
        try:
            with self.connection.cursor() as cursor:
                sql = f"DELETE FROM `{{self.table_name}}` WHERE {{where_clause}}"
                cursor.execute(sql)
                self.connection.commit()
                print(f"批量删除成功，影响行数: {{cursor.rowcount}}")
                return True
        except Exception as e:
            print(f"批量删除失败: {{e}}")
            self.connection.rollback()
            return False
'''
    
    def _generate_usage_example(self, table_name: str, selected_functions: List[str]) -> str:
        """生成使用示例"""
        example = f'''

def main():
    # 创建数据操作实例
    script = {table_name.title().replace('_', '')}DataScript()
    
    # 连接数据库
    if not script.connect():
        return
    
    try:'''
        
        if "query_data" in selected_functions:
            example += f'''
        # 查询数据
        print("=== 查询数据 ===")
        all_data = script.query_all_data(batch_size=100)  # 批量查询所有数据'''
        
        if "count_data" in selected_functions:
            example += f'''
        # 统计数据
        print("=== 统计数据 ===")
        total_count = script.count_data()'''
        
        if "insert_data" in selected_functions:
            example += f'''
        # 插入数据
        print("=== 插入数据 ===")
        # script.insert_data({{"field1": "value1"}})'''
        
        if "update_data" in selected_functions:
            example += f'''
        # 更新数据
        print("=== 更新数据 ===")
        # script.update_data({{"field1": "new_value"}}, "id = 1")'''
        
        if "delete_data" in selected_functions:
            example += f'''
        # 删除数据
        print("=== 删除数据 ===")
        # script.delete_data("id = 1")'''
        
        if "batch_insert" in selected_functions:
            example += f'''
        # 批量插入
        print("=== 批量插入 ===")
        # script.batch_insert_data([{{"field1": "value1"}}])'''
        
        example += f'''
        
    finally:
        # 关闭数据库连接
        script.close()


if __name__ == "__main__":
    main()
'''
        
        return example