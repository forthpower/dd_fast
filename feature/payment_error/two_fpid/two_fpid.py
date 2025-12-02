"""双 FPID 支付诊断入口。"""

from __future__ import annotations

import argparse
import logging
from typing import Dict, List

from feature.payment_error.two_fpid.logs import PaymentLogs
from feature.payment_error.two_fpid.provider_order import Payment


def run_two_fpid_check(fpid_a: int | str, fpid_b: int | str, gt: str, lt: str) -> Dict[str, object]:
    """按给定参数执行原有排查流程。"""
    def fail(message: str, **extra: object) -> Dict[str, object]:
        payload = {'code': 'fail', 'message': message}
        payload.update(extra)
        return payload

    provider_order = Payment(fpid=fpid_a, gt=gt, lt=lt)
    try:
        order_ids, ideal_amount = provider_order.get_order_id_and_amount()
    except Exception as exc:
        logging.exception("获取预订单失败：%s", exc)
        return fail(str(exc))

    logging.info(
        "Order id list: %s number: %s, ideal amount: %s",
        order_ids,
        len(order_ids),
        ideal_amount,
    )

    logs = PaymentLogs(fpid=fpid_b, gt=gt, lt=lt)
    try:
        has_logs = logs.has_insufficient_balance_log()
    except Exception as exc:
        logging.exception("查询日志失败：%s", exc)
        return fail(str(exc), order_ids=order_ids, ideal_amount=ideal_amount)

    if not has_logs:
        return fail("logs中没有虚拟币不足的日志", order_ids=order_ids, ideal_amount=ideal_amount)

    try:
        real_balance = provider_order.get_balance()
    except Exception as exc:
        logging.exception("查询余额失败：%s", exc)
        return fail(str(exc), order_ids=order_ids, ideal_amount=ideal_amount, has_logs=has_logs)

    logging.info("real_balance: %s", real_balance)

    if real_balance != ideal_amount:
        return fail(
            '预订单中虚拟币与账号中虚拟币不一致',
            order_ids=order_ids,
            ideal_amount=ideal_amount,
            has_logs=has_logs,
            real_balance=real_balance,
        )

    return {
        'code': 'success',
        'order_ids': order_ids,
        'ideal_amount': ideal_amount,
        'has_logs': has_logs,
        'real_balance': real_balance,
        'message': '成功找出错误🏅',
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="两次 FPID 虚拟币诊断工具")
    parser.add_argument('--fpid-a', required=True, help='用于 provider_order 查询的 FPID')
    parser.add_argument('--fpid-b', required=True, help='用于 payment_log 查询的 FPID')
    parser.add_argument('--gt', required=True, help='开始时间 (YYYY-MM-DD HH:MM:SS)')
    parser.add_argument('--lt', required=True, help='结束时间 (YYYY-MM-DD HH:MM:SS)')
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    args = _build_arg_parser().parse_args()
    result = run_two_fpid_check(args.fpid_a, args.fpid_b, args.gt, args.lt)
    print(result)


if __name__ == "__main__":
    main()
