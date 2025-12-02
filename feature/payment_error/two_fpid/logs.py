"""RPC helper for querying payment logs."""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List

import requests

TOKEN = 'eyJhbGciOiJIUzUxMiIsImlhdCI6MTc2MjkxNjgzNiwiZXhwIjoxNzY0NzMxMjM2fQ.eyJ1c2VyX2lkIjozODYzLCJ1c2VybmFtZSI6InlvbmdqaWFuLmRhaSJ9.7OFOOzK-PV0wfz5_RwgemGIipMBA1aU6yOxqS46pHYD5KPsvaGpGnNoMy1CLOc_QQ5x2S3JBs8b8XKP17QJyxQ'
URL = 'https://cgc-admin-manager.campfiregames.cn/api/v1/op/projects/7/rpc'
APP_ID = '84'


def _build_headers() -> Dict[str, str]:
    return {"token": TOKEN}


class PaymentLogs:
    """Wrapper around payment_log model RPC."""

    def __init__(self, fpid: int | str, gt: str, lt: str) -> None:
        self.fpid = str(fpid)
        self.gt = gt
        self.lt = lt
        self.url = URL
        self.header = _build_headers()
        ts_ms = int(time.time() * 1000)
        self.payload = {
            "op": "OP_QUERY",
            "payload": {
                "HEADER": {"op": "OP_QUERY", "ts": ts_ms},
                "model_name": "payment_log",
                "model_id": 54,
                "number_to_skip": 0,
                "number_to_return": 50,
                "query": {
                    "$query": {
                        "$and": [
                            {"user": self.fpid},
                            {"created": {"$gt": self.gt, "$lt": self.lt}},
                        ]
                    }
                },
            },
        }

    def _post(self) -> requests.Response:
        form_payload = {'payload': (None, json.dumps(self.payload), 'application/json')}
        response = requests.post(self.url, headers=self.header, files=form_payload, timeout=10)
        response.raise_for_status()
        return response

    def has_insufficient_balance_log(self) -> bool:
        """Return True if log entries contain insufficient balance message."""
        try:
            documents: List[Dict[str, Any]] = self._post().json()['data']['documents']
            for document in documents:
                if document.get('app_id') == APP_ID and 'insufficient balance traceid' in document.get('response', ''):
                    return True
        except Exception as exc:
            print(f"Exception: {exc}")
        return False
