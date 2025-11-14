#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import requests
import json
import re

logger = logging.getLogger(__name__)


def verify_bitable_access(app_token: str, table_id: str, access_token: str) -> bool:
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    
    try:
        response = requests.get(url, headers=headers, params={"page_size": 1}, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return result.get("code") == 0
        return False
    except:
        return False


def delete_all_feishu_table_records(app_token: str, table_id: str, access_token: str) -> bool:
    record_ids = _get_all_record_ids(app_token, table_id, access_token)
    if not record_ids:
        return True
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_delete"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    
    batch_size = 500
    success_count = 0
    
    for i in range(0, len(record_ids), batch_size):
        batch = record_ids[i:i + batch_size]
        response = requests.post(url, json={"records": batch}, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                success_count += len(batch)
            else:
                logger.error(f"删除失败: {result}")
                return False
        else:
            logger.error(f"HTTP错误 {response.status_code}: {response.text}")
            return False
    
    return True


def _get_all_record_ids(app_token: str, table_id: str, access_token: str, page_size: int = 500) -> list:
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    
    all_record_ids = []
    page_token = None
    
    while True:
        params = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"获取记录失败: {response.status_code} - {response.text}")
            break
        
        try:
            result = response.json()
        except:
            try:
                result = json.loads(response.content.decode('utf-8'))
            except:
                logger.error(f"解析响应失败: {response.text[:200]}")
                break
        
        if result.get("code") != 0:
            logger.error(f"API错误: {result}")
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


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    response = requests.post(url, json={"app_id": app_id, "app_secret": app_secret}, timeout=10)
    response.raise_for_status()
    
    result = response.json()
    if result.get("code") == 0:
        return result.get("tenant_access_token")
    else:
        raise Exception(f"获取token失败: {result.get('msg')}")


def get_feishu_table_info_from_url(url: str) -> dict:
    app_token_match = re.search(r'/base/([^/?]+)', url)
    table_id_match = re.search(r'table=([^&]+)', url)
    
    if app_token_match and table_id_match:
        return {"app_token": app_token_match.group(1), "table_id": table_id_match.group(1)}
    else:
        raise ValueError("无法从URL中提取app_token和table_id")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    table_url = "https://centurygames.feishu.cn/base/ZjWjbTdQQaX22VsaMQzcGSLbnyc?table=tblKHfdMJyrVonxS&view=vew9fRbXDD"
    table_info = get_feishu_table_info_from_url(table_url)
    app_token = table_info["app_token"]
    table_id = table_info["table_id"]
    
    app_id = "cli_a99e862024e7100e"
    app_secret = "Yog0pVLeTiyjsfxtga7ltbxgd3uVbg0j"
    
    print("正在获取 access_token...")
    access_token = get_tenant_access_token(app_id, app_secret)
    print(f"✓ 成功获取 access_token")
    
    if not verify_bitable_access(app_token, table_id, access_token):
        print("✗ 权限验证失败: 无法访问该多维表格")
        print("请在多维表格中点击「...」→「添加文档应用」→ 添加您的应用并授予「可编辑」权限")
        exit(1)
    
    print("✓ 权限验证通过")
    print("开始删除表格中的所有记录...")
    
    success = delete_all_feishu_table_records(app_token, table_id, access_token)
    
    if success:
        print("✓ 所有记录已成功删除")
    else:
        print("✗ 删除失败")
