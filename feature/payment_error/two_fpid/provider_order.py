"""RPC helper for provider_order related operations."""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Tuple

import requests

TOKEN = 'eyJhbGciOiJIUzUxMiIsImlhdCI6MTc2MjkxNjgzNiwiZXhwIjoxNzY0NzMxMjM2fQ.eyJ1c2VyX2lkIjozODYzLCJ1c2VybmFtZSI6InlvbmdqaWFuLmRhaSJ9.7OFOOzK-PV0wfz5_RwgemGIipMBA1aU6yOxqS46pHYD5KPsvaGpGnNoMy1CLOc_QQ5x2S3JBs8b8XKP17QJyxQ'
URL = 'https://cgc-admin-manager.campfiregames.cn/api/v1/op/projects/2/rpc'
APP_ID = '84'


def _build_headers() -> Dict[str, str]:
    return {"token": TOKEN}


class Payment:
    """Wrapper around provider_order + wechat_tool models."""

    def __init__(self, fpid: int | str, gt: str, lt: str) -> None:
        self.fpid = str(fpid)
        self.gt = str(gt)
        self.lt = str(lt)
        self.url = URL
        self.header = _build_headers()

    def _post(self, payload: Dict[str, Any]) -> requests.Response:
        form_payload = {'payload': (None, json.dumps(payload), 'application/json')}
        response = requests.post(self.url, headers=self.header, files=form_payload, timeout=10)
        response.raise_for_status()
        return response

    def get_order_id_and_amount(self) -> Tuple[List[str], float]:
        """Return order ids and aggregated amount."""
        try:
            ts_ms = int(time.time() * 1000)
            payload = {
                "op": "OP_QUERY",
                "payload": {
                    "HEADER": {"op": "OP_QUERY", "ts": ts_ms},
                    "model_name": "provider_order",
                    "model_id": 19,
                    "number_to_skip": 0,
                    "number_to_return": 50,
                    "query": {
                        "$query": {
                            "$and": [
                                {"uid": self.fpid},
                                {"ctime": {"$gt": self.gt, "$lt": self.lt}},
                            ]
                        }
                    },
                },
            }
            response = self._post(payload)
            order_id_list: List[str] = []
            amount = 0.0
            documents: List[Dict[str, Any]] = response.json()['data']['documents']
            for document in documents:
                if document['appid'] == APP_ID and document['status'] == 9:
                    order_id_list.append(document.get('orderid', ''))
                    amount += float(document.get('amount', 0))
            return order_id_list, amount
        except Exception as exc:
            print(f"Exception: {exc}")
            return [], 0.0

    def get_balance(self) -> float:
        """Return balance from midas tool."""
        try:
            ts_ms = int(time.time() * 1000)
            payload = {
                "op": "OP_AJAX",
                "payload": {
                    "HEADER": {"op": "OP_AJAX", "ts": ts_ms},
                    "model_name": "wechat_tool",
                    "model_id": 332,
                    "document": {
                        "tool_type": "midas_balance",
                        "provider_id": "180",
                        "fpid": self.fpid,
                    },
                    "action_name": "ajax",
                },
            }
            response = self._post(payload)
            documents = response.json()['data']['documents']
            balance = float(str(documents[0]).split('：')[1])
            return balance
        except Exception as exc:
            print(f"Exception: {exc}")
            return 0.0
