#!/usr/bin/env python3
"""Simple Tkinter UI for running the two FPID diagnostic."""

from __future__ import annotations

import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT.parent))

from feature.payment_error.two_fpid.two_fpid import run_two_fpid_check  # noqa: E402


class DatePicker(ttk.Frame):
    """Simple spinbox based date selector."""

    def __init__(self, master: tk.Widget, initial: datetime | None = None) -> None:
        super().__init__(master)
        initial = initial or datetime.now()
        self.year_var = tk.StringVar(value=str(initial.year))
        self.month_var = tk.StringVar(value=f"{initial.month:02d}")
        self.day_var = tk.StringVar(value=f"{initial.day:02d}")

        year_spin = ttk.Spinbox(self, from_=2000, to=2100, width=5, textvariable=self.year_var)
        month_spin = ttk.Spinbox(self, from_=1, to=12, width=3, textvariable=self.month_var, format="%02.0f")
        day_spin = ttk.Spinbox(self, from_=1, to=31, width=3, textvariable=self.day_var, format="%02.0f")

        year_spin.pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(self, text="年").pack(side=tk.LEFT)
        month_spin.pack(side=tk.LEFT, padx=(4, 4))
        ttk.Label(self, text="月").pack(side=tk.LEFT)
        day_spin.pack(side=tk.LEFT, padx=(4, 4))
        ttk.Label(self, text="日").pack(side=tk.LEFT)

    def get_date_str(self) -> str:
        year = int(self.year_var.get())
        month = int(self.month_var.get())
        day = int(self.day_var.get())
        return f"{year:04d}-{month:02d}-{day:02d}"


class PaymentErrorApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("支付错误排查工具")
        self.root.geometry("640x360")
        self.root.resizable(False, False)

        self._build_widgets()

    def _build_widgets(self) -> None:
        padding = {'padx': 12, 'pady': 6}
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(main_frame, text="FPID A (充值 FPID)").grid(row=0, column=0, sticky=tk.W, **padding)
        self.fpid_a_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.fpid_a_var).grid(row=0, column=1, sticky=tk.EW, **padding)

        ttk.Label(main_frame, text="FPID B (被充值 FPID)").grid(row=1, column=0, sticky=tk.W, **padding)
        self.fpid_b_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.fpid_b_var).grid(row=1, column=1, sticky=tk.EW, **padding)

        ttk.Label(main_frame, text="开始日期").grid(row=2, column=0, sticky=tk.W, **padding)
        self.gt_picker = DatePicker(main_frame)
        self.gt_picker.grid(row=2, column=1, sticky=tk.EW, **padding)

        ttk.Label(main_frame, text="结束日期").grid(row=3, column=0, sticky=tk.W, **padding)
        self.lt_picker = DatePicker(main_frame)
        self.lt_picker.grid(row=3, column=1, sticky=tk.EW, **padding)

        main_frame.columnconfigure(1, weight=1)

        self.result_text = tk.Text(main_frame, height=8, state=tk.DISABLED)
        self.result_text.grid(row=4, column=0, columnspan=2, sticky=tk.NSEW, padx=12, pady=12)

        ttk.Button(main_frame, text="开始诊断", command=self._run_check).grid(row=5, column=0, columnspan=2, padx=12, pady=6)

    def _append_result(self, text: str) -> None:
        self.result_text.configure(state=tk.NORMAL)
        self.result_text.insert(tk.END, text + "\n")
        self.result_text.configure(state=tk.DISABLED)
        self.result_text.see(tk.END)

    def _run_check(self) -> None:
        fpid_a = self.fpid_a_var.get().strip()
        fpid_b = self.fpid_b_var.get().strip()
        gt = f"{self.gt_picker.get_date_str()} 00:00:00"
        lt = f"{self.lt_picker.get_date_str()} 23:59:59"

        if not all([fpid_a, fpid_b, gt, lt]):
            messagebox.showwarning("缺少参数", "请填写所有必填参数")
            return

        def worker() -> None:
            try:
                result = run_two_fpid_check(fpid_a, fpid_b, gt, lt)
                self._append_result(str(result))
            except Exception as exc:
                self._append_result(f"执行失败: {exc}")

        threading.Thread(target=worker, daemon=True).start()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = PaymentErrorApp()
    app.run()


if __name__ == "__main__":
    main()

