"""
模型文件解析器
处理各种格式的模型文件解析
"""

import json
import ast
import re
from typing import Dict, List, Any, Optional, Union


class ModelParser:
    """模型文件解析器"""

    def __init__(self):
        # 类型映射字典
        self.type_mapping = {
            # Python/SQLAlchemy
            "Integer": "Integer",
            "String": "String",
            "Text": "TextArea",
            "Boolean": "Boolean",
            "DateTime": "DateTime",
            "Float": "Float",
            "Date": "DateTime",
            "Time": "String",
            "JSON": "Json",
            "BigInteger": "Integer",
            "SmallInteger": "Integer",
            "Numeric": "Float",
            "Decimal": "Float",
            # SQL
            "INT": "Integer",
            "INTEGER": "Integer",
            "BIGINT": "Integer",
            "SMALLINT": "Integer",
            "VARCHAR": "String",
            "CHAR": "String",
            "TEXT": "TextArea",
            "BOOLEAN": "Boolean",
            "BOOL": "Boolean",
            "DATETIME": "DateTime",
            "TIMESTAMP": "DateTime",
            "DATE": "DateTime",
            "FLOAT": "Float",
            "DOUBLE": "Float",
            "DECIMAL": "Float",
            "JSON": "Json",
            "BLOB": "File",
        }

    def parse_model_file(
        self, content: str, file_type: str = "auto"
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """
        解析模型文件内容，支持多种格式：
        - Python SQLAlchemy Model（支持多个模型）
        - Django Model
        - SQL DDL
        - JSON Schema

        返回格式：
        - 单个模型：返回单个 schema 字典
        - 多个模型：返回包含多个 schema 的列表
        """
        fields = []
        model_name = "imported_model"

        # 自动检测文件类型
        if "class" in content and ("db.Model" in content or "models.Model" in content):
            file_type = "python"
        elif "CREATE TABLE" in content.upper():
            file_type = "sql"
        elif (
            content.strip().startswith("{")
            or "schema" in content
            and "=" in content
            and "{" in content
        ):
            file_type = "json"

        if file_type == "python":
            return self.parse_python_model(content)
        elif file_type == "sql":
            return self.parse_sql_ddl(content)
        elif file_type == "json":
            return self.parse_json_schema(content)

        return None

    def parse_python_model(
        self, content: str
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """解析 Python Model"""
        schemas = []

        # 找到所有的类定义
        class_pattern = r"class\s+(\w+)\s*\([^)]*(?:db\.Model|models\.Model)[^)]*\):\s*\n((?:(?!^class\s).*\n)*)"
        class_matches = re.finditer(class_pattern, content, re.MULTILINE)

        for class_match in class_matches:
            class_name = class_match.group(1)
            class_body = class_match.group(2)

            # 跳过 Mixin 类和工具类
            if "Mixin" in class_name or class_name in ["Tool"]:
                continue

            model_name = class_name.lower()
            model_fields = []

            # 提取 __tablename__
            tablename_match = re.search(
                r'__tablename__\s*=\s*[\'"](\w+)[\'"]', class_body
            )
            if tablename_match:
                model_name = tablename_match.group(1)

            # 提取字段定义
            field_patterns = [
                r"(\w+)\s*=\s*db\.Column\s*\((.*?)\)",
                r"(\w+)\s*=\s*models\.\w+Field\s*\((.*?)\)",
                r"(\w+)\s*=\s*Column\s*\((.*?)\)",
            ]

            for pattern in field_patterns:
                matches = re.finditer(pattern, class_body, re.MULTILINE)
                for match in matches:
                    field_name = match.group(1)
                    field_def = match.group(2)

                    # 跳过私有字段和特殊字段
                    if field_name.startswith("_") or field_name in [
                        "metadata",
                        "query",
                    ]:
                        continue

                    field_config = self.parse_field_definition(field_name, field_def)
                    if field_config:
                        model_fields.append(field_config)

            # 如果有字段，创建 schema
            if model_fields:
                schema = self.create_schema(model_name, class_name, model_fields)
                schemas.append(schema)

        # 如果找到多个模型，返回列表；否则返回单个或空
        if len(schemas) > 1:
            return schemas
        elif len(schemas) == 1:
            return schemas[0]

        return None

    def parse_sql_ddl(self, content: str) -> Optional[Dict[str, Any]]:
        """解析 SQL DDL"""
        # 提取表名
        table_match = re.search(
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?(\w+)`?",
            content,
            re.IGNORECASE,
        )
        model_name = table_match.group(1).lower() if table_match else "imported_model"

        fields = []
        # 提取字段定义
        field_pattern = r"`?(\w+)`?\s+([\w()]+)(?:\s+([^,\n]+))?"
        matches = re.finditer(field_pattern, content)

        for match in matches:
            field_name = match.group(1)
            sql_type = match.group(2).upper()
            constraints = match.group(3) or ""

            # 跳过 PRIMARY KEY, FOREIGN KEY 等约束
            if field_name.upper() in [
                "PRIMARY",
                "FOREIGN",
                "KEY",
                "INDEX",
                "CONSTRAINT",
                "UNIQUE",
            ]:
                continue

            field_config = self.parse_sql_field(field_name, sql_type, constraints)
            if field_config:
                fields.append(field_config)

        if fields:
            return self.create_schema(
                model_name, model_name.replace("_", " ").title(), fields
            )

        return None

    def parse_json_schema(self, content: str) -> Optional[Dict[str, Any]]:
        """解析 JSON Schema"""
        data = None
        parsing_errors = []

        # 直接作为Python代码解析
        try:
            # 直接提取 schema = {...} 的内容，跳过前面的 import 语句
            schema_match = re.search(r"schema\s*=\s*(\{.*\})", content, re.DOTALL)
            if schema_match:
                schema_str = schema_match.group(1)
            else:
                # 如果没有找到 schema = {...}，尝试直接解析整个内容
                schema_str = content

            # 移除Python注释（行尾的 # 注释）
            schema_str = self.remove_comments(schema_str)

            # 处理 copy_rule 的特殊格式
            schema_str = re.sub(
                r'"copy_rule":\s*\{\s*["\']开启["\']\s*\}\s*,?\s*\n?',
                "",
                schema_str,
            )

            # 清理不可打印字符
            schema_str = "".join(
                char for char in schema_str if char.isprintable() or char in "\n\t"
            )

            # 替换常量引用为空列表
            constants_found = []
            schema_str = self.replace_constants(schema_str, constants_found)

            # 尝试解析整个schema
            try:
                data = ast.literal_eval(schema_str)
                
                # 如果有常量引用，记录下来供后续处理
                if constants_found:
                    print(f"     🔍 发现常量引用: {', '.join(constants_found)}")
                    data["_constants_found"] = constants_found
                    
            except (ValueError, SyntaxError) as parse_error:
                print(f"     ⚠️  完整解析失败，尝试部分解析: {parse_error}")
                
                # 如果完整解析失败，尝试部分解析
                data = self.partial_parse_schema(schema_str, constants_found)
                
                if not data:
                    # 如果部分解析也失败，抛出原始错误
                    raise parse_error

        except (ValueError, SyntaxError) as e:
            print(f"     ❌ Python解析错误: {e}")
            parsing_errors.append(f"Python解析错误: {str(e)}")
            return None

        # 如果成功解析了数据
        if data and isinstance(data, dict):
            # 如果是完整的 schema
            if "name" in data:
                # 处理所有有问题的字段和属性，包括常量引用标记
                data = self.clean_problematic_schema(data, parsing_errors)
                return data
            # 如果是字段定义
            elif "properties" in data:
                return self.parse_json_schema_format(data)

        return None

    def partial_parse_schema(self, schema_str: str, constants_found: List[str]) -> Optional[Dict[str, Any]]:
        """部分解析schema，尝试跳过有问题的字段"""
        try:
            # 尝试提取基本信息
            data = {}
            
            # 提取name
            name_match = re.search(r'"name":\s*["\']([^"\']+)["\']', schema_str)
            if name_match:
                data["name"] = name_match.group(1)
            
            # 提取label
            label_match = re.search(r'"label":\s*["\']([^"\']+)["\']', schema_str)
            if label_match:
                data["label"] = label_match.group(1)
            elif data.get("name"):
                data["label"] = data["name"].replace("_", " ").title()
            
            # 提取primary_key
            pk_match = re.search(r'"primary_key":\s*["\']([^"\']+)["\']', schema_str)
            if pk_match:
                data["primary_key"] = pk_match.group(1)
            else:
                data["primary_key"] = "id"
            
            # 提取entry
            entry_match = re.search(r'"entry":\s*["\']([^"\']+)["\']', schema_str)
            if entry_match:
                data["entry"] = entry_match.group(1)
            else:
                data["entry"] = "list"
            
            # 尝试解析parent字段
            parent_match = re.search(r'"parent":\s*([^,}]+)', schema_str)
            if parent_match:
                try:
                    parent_str = parent_match.group(1).strip()
                    if parent_str.startswith('{'):
                        # 尝试解析字典格式的parent
                        # 找到完整的字典
                        brace_count = 0
                        start_pos = schema_str.find('"parent":')
                        if start_pos != -1:
                            pos = schema_str.find('{', start_pos)
                            if pos != -1:
                                brace_count = 1
                                pos += 1
                                while pos < len(schema_str) and brace_count > 0:
                                    if schema_str[pos] == '{':
                                        brace_count += 1
                                    elif schema_str[pos] == '}':
                                        brace_count -= 1
                                    pos += 1
                                if brace_count == 0:
                                    parent_dict_str = schema_str[schema_str.find('{', start_pos):pos]
                                    parent_data = ast.literal_eval(parent_dict_str)
                                    data["parent"] = parent_data
                    elif parent_str.startswith('"'):
                        # 字符串格式的parent
                        data["parent"] = parent_str.strip('"\'')
                except:
                    data["parent"] = ""
            
            # 尝试解析action字段
            action_match = re.search(r'"action":\s*(\[.*?\])', schema_str, re.DOTALL)
            if action_match:
                try:
                    action_str = action_match.group(1)
                    action_data = ast.literal_eval(action_str)
                    data["action"] = action_data
                except:
                    # 如果action解析失败，设置默认值
                    data["action"] = [
                        {"name": "list", "template": "tablebase"},
                        {"name": "create", "template": "formbase"},
                        {"name": "edit", "template": "editbase"},
                        {"name": "delete", "template": "button"}
                    ]
            
            # 尝试解析base_props字段
            base_props_match = re.search(r'"base_props":\s*(\{.*?\})', schema_str, re.DOTALL)
            if base_props_match:
                try:
                    base_props_str = base_props_match.group(1)
                    base_props_data = ast.literal_eval(base_props_str)
                    data["base_props"] = base_props_data
                except:
                    data["base_props"] = {}
            
            # 尝试逐个解析fields字段
            fields_str = self._extract_fields_array(schema_str)
            if fields_str:
                data["fields"] = self.parse_fields_partially(fields_str)
            else:
                data["fields"] = []
            
            # 记录常量引用
            if constants_found:
                data["_constants_found"] = constants_found
                data["_has_parsing_issues"] = True
            
            print(f"     ⚠️  使用部分解析，成功提取基本信息")
            return data
            
        except Exception as e:
            print(f"     ❌ 部分解析也失败: {e}")
            return None

    def parse_fields_partially(self, fields_str: str) -> List[Dict[str, Any]]:
        """部分解析fields字段，跳过有问题的字段"""
        fields = []
        
        # 移除外层的方括号
        fields_str = fields_str.strip()
        if fields_str.startswith('[') and fields_str.endswith(']'):
            fields_str = fields_str[1:-1].strip()
        
        # 使用正则表达式逐个查找字段定义
        # 查找所有以 { 开头，包含 "name" 的字典定义
        pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*"name"[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        
        # 更简单的方法：查找所有可能的字段定义
        field_matches = []
        start_pos = 0
        
        while True:
            # 查找下一个可能的字段开始位置
            brace_start = fields_str.find('{', start_pos)
            if brace_start == -1:
                break
                
            # 查找对应的结束位置
            brace_count = 0
            pos = brace_start
            field_end = -1
            
            while pos < len(fields_str):
                char = fields_str[pos]
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        field_end = pos
                        break
                pos += 1
            
            if field_end != -1:
                field_str = fields_str[brace_start:field_end + 1]
                # 检查是否包含 "name" 字段
                if '"name"' in field_str:
                    field_matches.append(field_str)
                start_pos = field_end + 1
            else:
                # 如果没有找到匹配的结束括号，尝试提取基本信息
                remaining = fields_str[brace_start:]
                if '"name"' in remaining:
                    # 尝试提取到下一个逗号或结束
                    next_comma = remaining.find(',')
                    if next_comma != -1:
                        field_str = remaining[:next_comma].strip()
                        if field_str.endswith('}'):
                            field_str = field_str[:-1] + '}'
                        field_matches.append(field_str)
                        start_pos = brace_start + next_comma + 1
                    else:
                        break
                else:
                    break
        
        # 处理每个字段
        for field_str in field_matches:
            field_str = field_str.strip()
            if not field_str:
                continue
                
            try:
                field_data = ast.literal_eval(field_str)
                if isinstance(field_data, dict) and "name" in field_data:
                    # 确保必要字段存在
                    if "type" not in field_data:
                        field_data["type"] = "String"
                    if "label" not in field_data:
                        field_data["label"] = field_data["name"].replace("_", " ").title()
                    
                    fields.append(field_data)
            except:
                # 如果单个字段解析失败，尝试提取基本信息
                name_match = re.search(r'"name":\s*["\']([^"\']+)["\']', field_str)
                if name_match:
                    field_name = name_match.group(1)
                    type_match = re.search(r'"type":\s*["\']([^"\']+)["\']', field_str)
                    field_type = type_match.group(1) if type_match else "String"
                    label_match = re.search(r'"label":\s*["\']([^"\']+)["\']', field_str)
                    field_label = label_match.group(1) if label_match else field_name.replace("_", " ").title()
                    
                    fields.append({
                        "name": field_name,
                        "type": field_type,
                        "label": field_label,
                        "_has_parsing_issues": True
                    })
        
        return fields

    def _extract_fields_array(self, schema_str: str) -> str:
        """智能提取fields数组，正确处理嵌套的括号和语法错误"""
        # 查找 "fields": 的位置
        fields_start = schema_str.find('"fields":')
        if fields_start == -1:
            return ""
        
        # 找到数组开始的位置
        bracket_start = schema_str.find('[', fields_start)
        if bracket_start == -1:
            return ""
        
        # 使用括号计数来找到完整的数组
        bracket_count = 0
        pos = bracket_start
        
        while pos < len(schema_str):
            char = schema_str[pos]
            
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    # 找到匹配的结束括号
                    return schema_str[bracket_start:pos + 1]
            
            pos += 1
        
        # 如果没有找到匹配的结束括号，返回从开始到字符串结尾
        # 这可能意味着有语法错误，但我们仍然尝试解析
        return schema_str[bracket_start:]

    def clean_problematic_schema(self, data: Dict[str, Any], parsing_errors: List[str]) -> Dict[str, Any]:
        """清理有问题的schema属性，包括fields、parent、action等"""
        schema_errors = []
        
        # 处理常量引用标记
        if "_constants_found" in data:
            constants_found = data["_constants_found"]
            data["_has_constants"] = True
            data["_constants_used"] = constants_found
            del data["_constants_found"]  # 删除临时标记
            
            # 在字段中标记常量引用
            if "fields" in data and isinstance(data["fields"], list):
                for field in data["fields"]:
                    if isinstance(field, dict):
                        field["_has_constants"] = True
                        field["_constant_refs"] = constants_found
        
        # 处理fields字段
        if "fields" in data:
            data = self.clean_problematic_fields(data, schema_errors)
        
        # 处理parent字段
        if "parent" in data:
            data = self.clean_parent_field(data, schema_errors)
        
        # 处理action字段
        if "action" in data:
            data = self.clean_action_field(data, schema_errors)
        
        # 处理base_props字段
        if "base_props" in data:
            data = self.clean_base_props_field(data, schema_errors)
        
        # 记录schema级别的错误
        if schema_errors:
            data["_schema_errors"] = schema_errors
            data["_has_schema_issues"] = True
            print(f"     ⚠️  发现 {len(schema_errors)} 个schema问题")
            
        return data

    def clean_problematic_fields(self, data: Dict[str, Any], schema_errors: List[str]) -> Dict[str, Any]:
        """清理有问题的字段，保留能正常解析的字段"""
        if "fields" not in data or not isinstance(data["fields"], list):
            return data
            
        cleaned_fields = []
        field_errors = []
        
        for i, field in enumerate(data["fields"]):
            if not isinstance(field, dict):
                field_errors.append(f"字段 {i+1}: 不是有效的字典格式")
                continue
                
            # 检查字段的必要属性
            if "name" not in field:
                field_errors.append(f"字段 {i+1}: 缺少name属性")
                continue
                
            if "type" not in field:
                field_errors.append(f"字段 {i+1} ({field.get('name', 'unknown')}): 缺少type属性")
                # 尝试设置默认类型
                field["type"] = "String"
                
            # 检查字段值是否包含常量引用
            field_has_issues = False
            for key, value in field.items():
                if isinstance(value, str) and ("[" in value and "]" in value and len(value) < 10):
                    # 可能是被替换的常量引用
                    field_has_issues = True
                    field[f"_original_{key}"] = value
                    field[key] = ""  # 清空有问题的值
                    
            if field_has_issues:
                field["_has_parsing_issues"] = True
                field_errors.append(f"字段 {field.get('name', 'unknown')}: 包含常量引用或无法解析的值")
                
            cleaned_fields.append(field)
        
        # 更新字段列表
        data["fields"] = cleaned_fields
        
        # 记录字段级别的错误
        if field_errors:
            data["_field_errors"] = field_errors
            data["_has_field_issues"] = True
            schema_errors.extend(field_errors)
            print(f"     ⚠️  发现 {len(field_errors)} 个字段问题，已跳过有问题的字段")
            
        return data

    def clean_parent_field(self, data: Dict[str, Any], schema_errors: List[str]) -> Dict[str, Any]:
        """清理parent字段"""
        parent = data["parent"]
        
        # 如果parent是字符串，尝试解析
        if isinstance(parent, str):
            if parent and parent.strip():
                # 简单的字符串parent，创建基本结构
                data["parent"] = {
                    "label": parent,
                    "name": parent.replace(" ", "_").lower()
                }
            else:
                data["parent"] = ""
        elif isinstance(parent, dict):
            # 检查parent字典的完整性
            if "label" not in parent or "name" not in parent:
                schema_errors.append("parent字段缺少必要的label或name属性")
                # 尝试修复
                if "label" in parent:
                    data["parent"]["name"] = parent["label"].replace(" ", "_").lower()
                elif "name" in parent:
                    data["parent"]["label"] = parent["name"].replace("_", " ").title()
                else:
                    data["parent"] = ""
        else:
            # 无法识别的parent格式
            schema_errors.append("parent字段格式不正确")
            data["parent"] = ""
            
        return data

    def clean_action_field(self, data: Dict[str, Any], schema_errors: List[str]) -> Dict[str, Any]:
        """清理action字段"""
        action = data["action"]
        
        if isinstance(action, list):
            cleaned_actions = []
            action_errors = []
            
            for i, act in enumerate(action):
                if isinstance(act, dict):
                    # 检查action的必要属性
                    if "name" not in act:
                        action_errors.append(f"动作 {i+1}: 缺少name属性")
                        continue
                    if "template" not in act:
                        action_errors.append(f"动作 {i+1} ({act.get('name', 'unknown')}): 缺少template属性")
                        act["template"] = "button"  # 设置默认模板
                    
                    cleaned_actions.append(act)
                else:
                    action_errors.append(f"动作 {i+1}: 不是有效的字典格式")
            
            data["action"] = cleaned_actions
            
            if action_errors:
                data["_action_errors"] = action_errors
                data["_has_action_issues"] = True
                schema_errors.extend(action_errors)
                print(f"     ⚠️  发现 {len(action_errors)} 个动作问题，已跳过有问题的动作")
        else:
            # 如果action不是列表，设置默认值
            schema_errors.append("action字段不是列表格式")
            data["action"] = [
                {"name": "list", "template": "tablebase"},
                {"name": "create", "template": "formbase"},
                {"name": "edit", "template": "editbase"},
                {"name": "delete", "template": "button"}
            ]
            
        return data

    def clean_base_props_field(self, data: Dict[str, Any], schema_errors: List[str]) -> Dict[str, Any]:
        """清理base_props字段"""
        base_props = data["base_props"]
        
        if isinstance(base_props, dict):
            # 检查base_props的常见属性
            cleaned_props = {}
            
            # 处理column_list
            if "column_list" in base_props:
                if isinstance(base_props["column_list"], list):
                    cleaned_props["column_list"] = base_props["column_list"]
                else:
                    schema_errors.append("base_props.column_list不是列表格式")
            
            # 处理form_columns
            if "form_columns" in base_props:
                if isinstance(base_props["form_columns"], list):
                    cleaned_props["form_columns"] = base_props["form_columns"]
                else:
                    schema_errors.append("base_props.form_columns不是列表格式")
            
            # 处理其他属性
            for key, value in base_props.items():
                if key not in ["column_list", "form_columns"]:
                    if isinstance(value, (str, int, float, bool, list, dict)):
                        cleaned_props[key] = value
                    else:
                        schema_errors.append(f"base_props.{key}包含无法识别的数据类型")
            
            data["base_props"] = cleaned_props
        else:
            schema_errors.append("base_props不是字典格式")
            data["base_props"] = {}
            
        return data

    def remove_comments(self, content: str) -> str:
        """移除Python注释"""
        lines = content.split("\n")
        cleaned_lines = []
        for line in lines:
            # 检查是否在字符串内
            in_string = False
            quote_char = None
            cleaned_line = []
            i = 0
            while i < len(line):
                char = line[i]
                # 处理字符串
                if char in ['"', "'"]:
                    if not in_string:
                        in_string = True
                        quote_char = char
                    elif char == quote_char and (i == 0 or line[i - 1] != "\\"):
                        in_string = False
                        quote_char = None
                    cleaned_line.append(char)
                # 处理注释
                elif char == "#" and not in_string:
                    # 遇到注释，跳过剩余部分
                    break
                else:
                    cleaned_line.append(char)
                i += 1
            cleaned_lines.append("".join(cleaned_line))

        return "\n".join(cleaned_lines)

    def replace_constants(self, schema_str: str, constants_found: List[str]) -> str:
        """替换常量引用"""
        # 查找所有常量引用模式
        constant_patterns = [
            r":\s*([A-Za-z_][A-Za-z0-9_]*\.[A-Z_][A-Z0-9_]*)\s*([,\}\]])",  # ClassName.ATTRIBUTE
            r":\s*([A-Z_][A-Z0-9_]*)\s*([,\}\]])",  # CONSTANT_NAME
        ]

        def replace_and_record(match):
            constant_ref = match.group(1)
            if constant_ref not in constants_found:
                constants_found.append(constant_ref)
            return ": []" + match.group(2)

        # 替换常量引用为空列表并记录
        for pattern in constant_patterns:
            schema_str = re.sub(pattern, replace_and_record, schema_str)

        return schema_str

    def parse_field_definition(
        self, field_name: str, field_def: str
    ) -> Optional[Dict[str, Any]]:
        """解析字段定义"""
        # 推断类型
        field_type = "String"  # 默认类型
        for py_type, schema_type in self.type_mapping.items():
            if py_type in field_def:
                field_type = schema_type
                break

        # 特殊处理 JSON 类型
        if "JSON" in field_def or "Json" in field_def:
            field_type = "Json"

        # 提取字段标签
        label_match = re.search(r'comment=[\'"]([^\'"]+)[\'"]', field_def)
        label = (
            label_match.group(1)
            if label_match
            else field_name.replace("_", " ").title()
        )

        # 检查是否必填
        nullable_match = re.search(r"nullable\s*=\s*(False|True)", field_def)
        is_required = nullable_match and nullable_match.group(1) == "False"

        # 检查是否为主键
        is_primary = (
            "primary_key=True" in field_def or "primary_key = True" in field_def
        )

        # 检查默认值
        default_match = re.search(
            r'default\s*=\s*[\'"]?([^\'",()\s]+)[\'"]?', field_def
        )
        default_value = default_match.group(1) if default_match else None

        # 构建字段配置
        field_config = {"name": field_name, "label": label, "type": field_type}

        # 添加验证器
        if is_required and not is_primary:
            field_config["validators"] = [{"name": "data_required"}]

        # 主键设置为只读
        if is_primary:
            field_config["render_kw"] = {"readonly": True}

        if default_value and default_value not in [
            "None",
            "null",
            "datetime.now",
            "datetime.utcnow",
        ]:
            field_config["default"] = default_value

        return field_config

    def parse_sql_field(
        self, field_name: str, sql_type: str, constraints: str
    ) -> Optional[Dict[str, Any]]:
        """解析SQL字段"""
        # 推断类型
        field_type = "String"
        for sql_t, schema_type in self.type_mapping.items():
            if sql_type.startswith(sql_t):
                field_type = schema_type
                break

        # 检查是否必填
        is_required = "NOT NULL" in constraints.upper()

        # 检查默认值
        default_match = re.search(
            r'DEFAULT\s+[\'"]?([^\'",()\s]+)[\'"]?', constraints, re.IGNORECASE
        )
        default_value = default_match.group(1) if default_match else None

        # 检查注释
        comment_match = re.search(
            r'COMMENT\s+[\'"]([^\'"]+)[\'"]', constraints, re.IGNORECASE
        )
        label = comment_match.group(1) if comment_match else field_name

        # 构建字段配置
        field_config = {"name": field_name, "label": label, "type": field_type}

        if is_required:
            field_config["validators"] = [{"name": "data_required"}]

        if default_value and default_value.upper() not in ["NULL", "CURRENT_TIMESTAMP"]:
            field_config["default"] = default_value

        return field_config

    def parse_json_schema_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析JSON Schema格式"""
        model_name = data.get("title", "imported_model").lower()
        fields = []

        for field_name, field_def in data["properties"].items():
            json_type = field_def.get("type", "string")
            field_type = {
                "string": "String",
                "integer": "Integer",
                "number": "Float",
                "boolean": "Boolean",
                "object": "Json",
                "array": "Json",
            }.get(json_type, "String")

            fields.append(
                {
                    "name": field_name,
                    "label": field_def.get("title", field_name),
                    "type": field_type,
                }
            )

        return self.create_schema(
            model_name, model_name.replace("_", " ").title(), fields
        )

    def create_schema(
        self, model_name: str, label: str, fields: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """创建schema结构"""
        # 查找主键字段
        primary_key = "id"
        for field in fields:
            if field.get("render_kw", {}).get("readonly") and field["name"] in [
                "id",
                f"{model_name}_id",
            ]:
                primary_key = field["name"]
                break

        return {
            "name": model_name,
            "label": label,
            "primary_key": primary_key,
            "entry": "list",
            "parent": "",
            "action": [
                {"name": "list", "template": "tablebase"},
                {"name": "create", "template": "formbase"},
                {"name": "edit", "template": "editbase"},
                {"name": "delete", "template": "button"},
            ],
            "fields": fields,
            "base_props": {
                "column_list": [f["name"] for f in fields[:6]],
                "form_columns": [
                    f["name"]
                    for f in fields
                    if not f.get("render_kw", {}).get("readonly")
                ],
                "page_size": 20,
            },
            "custom_actions": [],
        }


# 全局解析器实例
model_parser = ModelParser()
