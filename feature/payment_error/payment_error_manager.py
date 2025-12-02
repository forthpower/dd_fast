#!/usr/bin/env python3
"""Manager that exposes the payment error helper to the tray app."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


class PaymentErrorManager:
    """Responsible for launching the payment error standalone UI."""

    def __init__(self) -> None:
        current_dir = Path(__file__).resolve().parent
        self._entrypoint = current_dir / "payment_error_standalone.py"

    def open_feature(self) -> None:
        """Open the payment error helper in a detached process."""
        try:
            subprocess.Popen(
                [sys.executable, str(self._entrypoint)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            print("支付错误排查工具已启动")
        except Exception as exc:
            print(f"启动支付错误排查工具失败: {exc}")

