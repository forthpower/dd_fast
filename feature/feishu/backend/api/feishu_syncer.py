#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import csv
import json
import re
import os
from pathlib import Path


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


def convert_to_feishu_record(row: dict, field_map: dict = None) -> dict:
    fields = {}
    number_fields = ["Adyen", "Stripe", "Airwallex"]
    
    if not field_map:
        for key, value in row.items():
            if key in number_fields:
                if not value or not value.strip():
                    fields[key] = 0
                else:
                    try:
                        fields[key] = int(value.strip())
                    except:
                        fields[key] = 0
                continue
            if not value or not value.strip():
                continue
            fields[key] = value.strip()
    else:
        for csv_key, feishu_field in field_map.items():
            if csv_key in number_fields:
                if csv_key not in row or not row[csv_key] or not row[csv_key].strip():
                    fields[feishu_field] = 0
                else:
                    try:
                        fields[feishu_field] = int(row[csv_key].strip())
                    except:
                        fields[feishu_field] = 0
                continue
            if csv_key not in row or not row[csv_key]:
                continue
            fields[feishu_field] = row[csv_key].strip()
    
    return {"fields": fields}


def batch_create_records(app_token: str, table_id: str, access_token: str, records: list) -> bool:
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    
    for i in range(0, len(records), 500):
        batch = records[i:i + 500]
        response = requests.post(url, json={"records": batch}, headers=headers, timeout=30)
        if response.status_code != 200:
            return False
        result = response.json()
        if result.get("code") != 0:
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
        response = requests.post(url, json={"records": batch}, headers=headers, timeout=30)
        if response.status_code != 200:
            return False
        result = response.json()
        if result.get("code") != 0:
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
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code != 200:
            break
        
        try:
            result = response.json()
        except:
            try:
                result = json.loads(response.content.decode('utf-8'))
            except:
                break
        
        if result.get("code") != 0:
            break
        
        data = result.get("data", {})
        for record in data.get("items", []):
            record_id = record.get("record_id")
            if record_id:
                all_record_ids.append(record_id)
        
        page_token = data.get("page_token")
        if not page_token:
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
    if csv_file:
        csv_file_path = csv_file
    elif csv_dir:
        csv_file_path = get_latest_csv_file(csv_dir)
    else:
        raise ValueError("必须提供 csv_dir 或 csv_file 参数")
    print(f"使用文件: {csv_file_path}")
    
    csv_data = read_csv_data(csv_file_path)
    print(f"读取到 {len(csv_data)} 条记录")
    
    print("删除旧数据...")
    if not delete_all_records(app_token, table_id, access_token):
        return False
    
    records = [convert_to_feishu_record(row, field_map) for row in csv_data]
    
    print(f"创建 {len(records)} 条新记录...")
    if not batch_create_records(app_token, table_id, access_token, records):
        return False
    
    print(f"✓ 成功同步 {len(records)} 条记录")
    return True


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
