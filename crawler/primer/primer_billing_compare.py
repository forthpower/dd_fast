"""
对 Primer 账单（Excel）和平台 SelectDB 数据做对账比对的脚本。
"""
import os
import argparse
import csv
import datetime
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pymysql
import logging

import pandas as pd
import requests

from crawler.THREE_DS.three_ds_workflow import PrimerInfo

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(f'primer_billing_compare.log')  # 本脚本运行日志文件
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s :%(lineno)d - %(levelname)s - %(message)s')

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)



class GenerateData:
    def __init__(self):
        self.db_connection = None
        self.cursor = None
        # 文件写入锁，用于多线程安全写入
        self.file_lock = threading.Lock()

    def get_data_from_selectdb(self, start_time, end_time):
        config = {
            "host": "selectdb-cluster-tcp-18731f6a6a8c802c.elb.us-west-2.amazonaws.com",  # 内网访问地址
            "user": "backend",
            "password": "8NOvntHJ",
            "port": 9030,
            "database": "backend_pf",
        }
        print(int(time.time()))
        connection = pymysql.connect(
            cursorclass=pymysql.cursors.DictCursor,
            **config,
        )
        all_data = []
        cursor = connection.cursor()
        time_format = '%Y-%m-%d %H:%M:%S'
        start_datetime = datetime.datetime.strptime(start_time, time_format)
        end_datetime = datetime.datetime.strptime(end_time, time_format)
        current_date = start_datetime
        while current_date < end_datetime:
            current_date_str = current_date.strftime(time_format)
            current_date_next = current_date + datetime.timedelta(days=1)
            current_date_next_str = current_date_next.strftime(time_format)
            sql = f"""select * from backend_pf.primer_transaction_data where date >= "{current_date_str}" and date < "{current_date_next_str}" """
            # sql = f"""select * from backend_pf.primer_transaction_data where id = "6sDOIj0lE" """
            # sql = f"""select * from backend_pf.primer_transaction_data where id = "01m3Tx74o" """
            logger.info(sql)
            cursor.execute(sql)
            rows = cursor.fetchall()
            all_data.extend(rows)
            current_date = current_date_next
        return all_data

    def anaysis_platform_data(self, start_time, end_time):
        """
        平台侧数据分析：
        - 优先从本地 CSV 文件读取（如果存在）
        - 否则从 SelectDB 拉取并写入 CSV 文件
        """
        # 根据时间拼接 CSV 文件名（缓存平台原始交易数据）
        csv_filename = f"primer_selectdb_{start_time[:10]}_{end_time[:10]}.csv"

        if os.path.exists(csv_filename):
            logger.info(f"从本地 CSV 文件读取平台数据: {csv_filename}")
            all_data = []
            with open(csv_filename, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    all_data.append(row)
            logger.info(f"从 CSV 文件读取了 {len(all_data)} 条数据")
        else:
            logger.info(f"本地 CSV 文件不存在，开始从 SelectDB 拉取数据: {start_time} ~ {end_time}")
            all_data = self.get_data_from_selectdb(start_time, end_time)
            
            # 写入 CSV 文件
            if all_data:
                fieldnames = all_data[0].keys()
                with open(csv_filename, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(all_data)
                logger.info(f"平台数据已写入 CSV 文件: {csv_filename}，共 {len(all_data)} 条数据")
            else:
                logger.warning(f"从 SelectDB 查询到的数据为空，未生成 CSV 文件")

        no_failed_count, nt_order, db_order_info = 0, [], {}
        for item in all_data:
            id = item['id']
            status = item['status']
            card_token_type = item['cardTokenType']
            # 1. 未开启 2. 可绕过 3. 不可绕过
            bypass_3ds = item['metadata_bypass_3ds']
            whether_fallback = item['whether_fallback']
            translate = {
                '1': "1-未开启绕过 3DS",
                '2': "2-Adaptive 3DS",
                '3': "3-Always Run 3DS",
            }
            threeds_result = item['paymentMethod_threeDSecureAuthentication_responseCode']
            if status != 'FAILED':
                no_failed_count += 1

            if card_token_type == 'NETWORK_TOKEN' and status != "FAILED":
                nt_order.append(id)
            db_order_info[id] = {
                "bypass_3ds": translate[bypass_3ds],
                "threeds_result": threeds_result,
                "card_token_type": card_token_type,
                "whether_fallback": whether_fallback,
                "finished_adaptive_3ds": item['finished_adaptive_3ds'],
                "fallback_process": json.dumps([item['init_processor'], item['fallback_processor']]),
                "status": status
            }
            # print(threeds_order_info)

        return no_failed_count, nt_order, db_order_info

    def get_data_from_csv(self, file_path):
        with open(file_path, 'r') as f:
            csv_reader = csv.reader(f)
            for item in csv_reader:
                print(item)

    def get_transtions(self, uuid, month="10"):
        print(f'uuid: {uuid} request primer')
        new_file = 'transaction_info_10.json'
        url = f"https://api.primer.io/payments/{uuid}"
        headers = {
            'X-API-KEY': 'f467b28f-241e-4bf9-9153-4267a72ae575',
            'X-Api-Version': '2.4',
        }
        try:
            result = requests.get(url, headers=headers, timeout=10).json()
            transactions = result.get('transactions')
            status = result['status']
            # 使用锁保护文件写入，确保多线程安全
            with self.file_lock:
                with open(new_file, 'a+', encoding='utf-8') as f:
                    data = json.dumps({"uuid": uuid, "transactions": transactions, "status": status}, ensure_ascii=False)
                    f.write(data)
                    f.write('\n')
                    f.flush()  # 强制刷新缓冲区，确保立即写入
            logger.info(f"成功写入 transaction_info: {uuid}")
            print(f"✓ 成功写入: {uuid}")
            return True
        except Exception as error:
            logger.error(f"获取 transaction_info 失败 {uuid}: {error}")
            print(f"✗ 失败 {uuid}: {error}")
            return False

    def get_get_from_transaction(self):
        filename = 'transaction_info_10.json'
        with open(filename, 'r') as f:
            result = f.read()
        transaction_info = {}
        with open(filename, 'r', encoding='utf-8') as f:
            result = f.read()
        
        # 如果文件为空，直接返回空字典
        if not result.strip():
            logger.info(f"transaction_info 文件为空，返回空字典")
            return transaction_info
        
        for item in result.split('\n'):
            if not item:
                continue
            item = json.loads(item)
            uuid = item['uuid']
            transactions = item['transactions']
            processor_list = [transaction['processorName'] for transaction in transactions]
            transaction_info[uuid] = processor_list
        return transaction_info

    def get_data_from_excel(self, file_path):
        df_excel = pd.read_excel(file_path)
        no_failed_count, nt_order, threeds_order_info = 0, [], {}

        for index, row in df_excel.iterrows():
            row_info = dict(row)
            status = row_info['PAYMENT_STATUS']
            id = row_info['MERCHANT_PAYMENT_ID']
            nt = row_info['IS_NETWORK_TOKEN_USED']
            usd_amount = row_info['PAYMENT_AMOUNT_CAPTURED_USD']
            gbp_amount = row_info['PAYMENT_AMOUNT_CAPTURED_GBP']
            use_fallback = row_info['USED_A_FALLBACK']
            fallback_recovered = row_info['IS_PAYMENT_FALLBACK_RECOVERED']
            three_ds_call = row_info['NUM_THREE_DS_CALLS']
            adaptive_3ds_recover = row_info['RECOVERED_AMOUNT_USD_BY_ADAPTIVE_3DS']
            if status != "FAILED":
                no_failed_count += 1
            if nt in (1, "1", "TRUE", "True"):
                nt_order.append(id)

            threeds_order_info[id] = {
                "ts": row_info['CREATED_AT'],
                "usd_amount": usd_amount,
                "gbp_amount": gbp_amount,
                "three_ds_call": three_ds_call,
                "adaptive_3ds_recover": adaptive_3ds_recover,
                "use_fallback": use_fallback,
                "use_nt": nt,
                "fallback_recovered": fallback_recovered,
                "status": status,
            }

        # 提取 Usage Fee
        def _extract_usage_fee(df, patterns):
            for col in df.columns:
                col_lower = str(col).lower()
                if any(p in col_lower for p in patterns) and df[col].dtype in ['float64', 'int64']:
                    return float(df[col].sum())
            return 0.0
        
        usage_fees = {
            'fee_per_payment': _extract_usage_fee(df_excel, ['fee_per_payment', 'fee per payment']),
            'three_ds_calls': _extract_usage_fee(df_excel, ['3ds_calls', '3ds calls', 'three_ds_calls']),
            'fallbacks': _extract_usage_fee(df_excel, ['fallback']),
            'token_usage_fee': _extract_usage_fee(df_excel, ['token_usage', 'token usage']),
        }

        return no_failed_count, nt_order, threeds_order_info, usage_fees


    def generate_transaction_info(self, file_path, max_workers=10):
        """
        生成 transaction_info，使用多线程并发请求 Primer API
        :param file_path: Excel 账单文件路径（Primer 导出的 billing 报表）
        :param max_workers: 最大并发线程数，默认 10
        """
        # 保存 Primer API 原始返回(JSONL，每行一条记录)
        transaction_info_file = 'transaction_info_10.json'
        if not os.path.exists(transaction_info_file):
            with open(transaction_info_file, 'w', encoding='utf-8') as f:
                pass  # 创建空文件
        else:
            return
        
        df_excel = pd.read_excel(file_path)
        api_transfer = {
            "259ea0a9-69c8-425f-90f8-ca532d6b3318": "f467b28f-241e-4bf9-9153-4267a72ae575",
            # "9c396d40-ea06-445f-89ae-4fcb123d77c2": "",   # da,
            # "bcfa9e72-ab36-4747-b86b-86cb4c19a943": "", # got
        }
        
        # 第一步：收集所有需要查询的订单 ID
        request_primer = False
        order_ids_to_query = []
        
        for index, row in df_excel.iterrows():
            row_info = dict(row)
            id = row_info['MERCHANT_PAYMENT_ID']
            account_id = row_info['PRIMER_ACCOUNT_ID']
            fallback = row_info['IS_PAYMENT_FALLBACK_RECOVERED']
            threeds_calls = row_info['NUM_THREE_DS_CALLS']
            
            # if id == "04CyYJMGc":
            #     request_primer = True
            #     print(f"找到起始订单 {id}，开始收集后续订单")
            #
            # if not request_primer:
            #     continue

            if account_id not in api_transfer:
                continue

            if fallback in ("True", 1, '1', "true", True) or threeds_calls in ("True", 1, '1', "true", True):
                order_ids_to_query.append(id)
        
        total_orders = len(order_ids_to_query)
        print(f"共收集到 {total_orders} 个订单需要查询，开始多线程并发请求...")

        # 第二步：使用线程池并发查询
        success_count = 0
        fail_count = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_order = {executor.submit(self.get_transtions, order_id): order_id 
                              for order_id in order_ids_to_query}
            
            # 处理完成的任务
            for future in as_completed(future_to_order):
                order_id = future_to_order[future]
                try:
                    result = future.result()
                    if result:
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as exc:
                    logger.error(f"订单 {order_id} 查询异常: {exc}")
                    fail_count += 1
                
                # 显示进度
                completed = success_count + fail_count
                if completed % 10 == 0 or completed == total_orders:
                    print(f"进度: {completed}/{total_orders} (成功: {success_count}, 失败: {fail_count})")
        
        logger.info(f"transaction_info 生成完成，共处理 {total_orders} 个订单 (成功: {success_count}, 失败: {fail_count})")
        print(f"transaction_info 生成完成，共处理 {total_orders} 个订单 (成功: {success_count}, 失败: {fail_count})")

    def run(self, start_time, end_time, file_path):
        obc_result_path = os.path.join(os.path.dirname(__file__), 'obc_result.csv')
        if os.path.exists(obc_result_path):
            return
        self.generate_transaction_info(file_path)
        no_failed_count, nt_order, db_order_info = self.anaysis_platform_data(start_time, end_time)
        csv_no_failed_count, csv_nt_order, csv_order_info, usage_fees = self.get_data_from_excel(file_path)
        process_info = self.get_get_from_transaction()
        db_key_demo = ['bypass_3ds', 'threeds_result', 'card_token_type', 'whether_fallback', 'finished_adaptive_3ds', 'fallback_process', 'status']

        csv_key_demo = ['ts', 'usd_amount', 'gbp_amount', 'three_ds_call', 'adaptive_3ds_recover', 'use_fallback', 'use_nt', 'fallback_recovered', 'status']


        process_threeds_order_id = set()
        header_list = ['order_id'] + [f"csv_{key}" for key in csv_key_demo] + [f"db_{key}" for key in db_key_demo] + ["process_info"]
        # 最终对账结果文件：平台 vs Excel + Primer 处理器信息
        with open('obc_result.csv', 'a+', encoding='utf-8', newline='') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(header_list)

            for order_id in csv_order_info:
                current_csv_order_info = csv_order_info[order_id]
                csv_values = [current_csv_order_info[key] for key in csv_key_demo]

                current_db_order_info = db_order_info.get(order_id)
                if current_db_order_info:
                    db_values = [current_db_order_info[key] for key in db_key_demo]
                else:
                    db_values = [None] * len(db_key_demo)
                order_process_info = process_info.get(order_id, [])
                csv_writer.writerow([order_id] + csv_values + db_values + [json.dumps(order_process_info)])
                process_threeds_order_id.add(order_id)

            for order_id in db_order_info:
                if order_id in process_threeds_order_id:
                    continue
                current_db_order_info = db_order_info[order_id]
                db_values = [current_db_order_info[key] for key in db_key_demo]

                current_csv_order_info = csv_order_info.get(order_id)
                if current_csv_order_info:
                    csv_values = [current_csv_order_info[key] for key in csv_key_demo]
                else:
                    csv_values = [None] * len(csv_key_demo)
                csv_writer.writerow([order_id] + csv_values + db_values + [json.dumps(['', ''])])
                process_threeds_order_id.add(order_id)


        # 保存 usage_fees 供 CompareData 使用
        usage_fees_file = 'usage_fees.json'
        with open(usage_fees_file, 'w', encoding='utf-8') as f:
            json.dump(usage_fees, f, ensure_ascii=False)
        
        print('nt csv 比 selectdb 多的: ', set(csv_nt_order) - set(nt_order))
        print('nt selectdb 比 csv 多的: ', set(nt_order) - set(csv_nt_order))
        print("selectdb 中非失败的数量：", no_failed_count, "csv 中非失败的数量: ", csv_no_failed_count)


class CompareData:
    """
    只做“对账/校验”的类。
    输入一般是已经整理好的集合或字典（由 GenerateData 产出），
    每个方法对应一类对账场景。
    """

    # 一、NT 相关对账

    def check_nt_csv_more_than_db(self, csv_nt_order: set, db_nt_order: set) -> set:
        """csv 比 selectdb 多的 NT 订单"""
        diff = csv_nt_order - db_nt_order
        print(f"【NT 对账】csv 比 selectdb 多的 NT 订单数量: {len(diff)}")
        # if diff:
        #     print(f"  订单: {', '.join(sorted(diff))}")
        return diff

    def check_nt_db_more_than_csv(self, csv_nt_order: set, db_nt_order: set) -> set:
        """selectdb 比 csv 多的 NT 订单"""
        diff = db_nt_order - csv_nt_order
        print(f"【NT 对账】selectdb 比 csv 多的 NT 订单数量: {len(diff)}")
        # if diff:
        #     print(f"  订单: {', '.join(sorted(diff))}")
        return diff

    # 二、非失败交易数量对账

    def check_non_failed_ratio(self, db_non_failed_count: int, csv_non_failed_count: int,
                               threshold: float = 0.01) -> float:
        """
        3. selectdb 中非失败数量 vs csv 中非失败数量 的差值占比：
        - 目标：对整体 volume 做 sanity check，差值占比超过 1% 视为异常。
        - 返回：差值占比 ratio（csv-db）/db_non_failed_count。
        """
        if db_non_failed_count == 0:
            print("【Volume 对账】selectdb 非失败数量为 0，无法计算占比")
            return 0.0
        diff = csv_non_failed_count - db_non_failed_count
        ratio = diff / db_non_failed_count
        print(f"【Volume 对账】selectdb 非失败: {db_non_failed_count}, csv 非失败: {csv_non_failed_count}, 差值占比: {ratio:.4%}")
        # if abs(ratio) > threshold:
        #     print(f"【Volume 对账】警告：差值占比超过阈值 {threshold:.2%}")
        return ratio

    # 三、订单状态一致性对账

    def check_status_mismatch(self, csv_status_map: dict, db_status_map: dict) -> set:
        """检查 csv_status 和 db_status 不一致的订单"""
        mismatched = {oid for oid, csv_status in csv_status_map.items() 
                     if db_status_map.get(oid) != csv_status}
        print(f"【状态对账】不一致订单数量: {len(mismatched)}")
        # for oid in sorted(mismatched):
        #     print(f"  {oid}: csv={csv_status_map[oid]}, db={db_status_map.get(oid)}")
        return mismatched

    # 四、Fallback & PSP 路由一致性对账（成功订单）

    def check_fallback_psp_consistency(self, csv_use_fallback_map: dict, db_fallback_process_map: dict) -> set:
        """PSP 数量与 csv_use_fallback 不一致的订单"""
        def _to_bool(v):
            return v in (True, "True", "true", 1, "1", "TRUE")
        invalid = set()
        for oid, use_fallback in csv_use_fallback_map.items():
            procs = db_fallback_process_map.get(oid, [])
            psp_count = len({p for p in procs if p}) if procs else 0
            use_fb = _to_bool(use_fallback)
            if (not use_fb and psp_count != 1) or (use_fb and psp_count < 2):
                invalid.add(oid)
        print(f"【Fallback 对账】PSP 数量不一致的订单数量: {len(invalid)}")
        # if invalid:
        #     print(f"  订单: {', '.join(sorted(invalid))}")
        return invalid

    def check_fallback_flag_consistency(self, csv_use_fallback_map: dict, db_whether_fallback_map: dict) -> set:
        """csv_use_fallback vs db_whether_fallback 不一致的订单"""
        def _to_bool(v):
            return v in (True, "True", "true", 1, "1", "TRUE") if v else False
        mismatched = {oid for oid, csv_flag in csv_use_fallback_map.items()
                     if _to_bool(csv_flag) != _to_bool(db_whether_fallback_map.get(oid, None)) or db_whether_fallback_map.get(oid, None) is None}
        print(f"【Fallback 对账】标志不一致的订单数量: {len(mismatched)}")
        # if mismatched:
        #     print(f"  订单: {', '.join(sorted(mismatched))}")
        return mismatched

    # 五、与 Primer PDF Usage fee 一致性对账（7–10：需根据合同/费率 PDF 硬编码规则）
    def check_usage_fee_consistency(
        self,
        csv_status_map: dict,
        csv_three_ds_call_map: dict,
        csv_use_fallback_map: float,
        csv_use_nt_map: dict,
        expected_fee_per_payment: float,
        expected_three_ds_calls: float,
        expected_fallbacks: float,
        expected_token_usage_fee: float,
        threshold: float = 0.01,
    ) -> dict:
        """
        7–10. Usage fee 相关对账（四类 Usage）：
        传入四个「实际 Usage 金额」和「期望金额」，进行对比：
          7. Fee Per Payment Pricing
          8. 3DS Calls
          9. Fallbacks
         10. Token Usage Fee

        :param expected_fee_per_payment: 期望的 Fee Per Payment 金额（从 PDF/合同）
        :param expected_three_ds_calls: 期望的 3DS Calls 金额
        :param expected_fallbacks: 期望的 Fallbacks 金额
        :param expected_token_usage_fee: 期望的 Token Usage Fee 金额
        :param threshold: 允许的相对误差阈值（默认 1%）
        :return: 每一项的差值/占比结果字典
        """

        def _to_bool(v):
            return v in (True, "True", "true", 1, "1")
        
        # 统计实际数量
        fee_per_payment_usage = len([s for s in csv_status_map.values() if s and s != "FAILED"])
        three_ds_calls_usage = len([c for c in csv_three_ds_call_map.values() if c and str(c) not in ("0", "None", "")])
        fallbacks_usage = int(csv_use_fallback_map)
        token_usage_fee = len([nt for nt in csv_use_nt_map.values() if _to_bool(nt)])

        def _calc_diff(actual: float, expected: float) -> tuple[float, float]:
            if expected == 0:
                return actual - expected, 0.0
            diff_val = actual - expected
            ratio = diff_val / expected
            return diff_val, ratio

        results = {}
        for name, actual, expected in [
            ("Fee Per Payment", fee_per_payment_usage, expected_fee_per_payment),
            ("3DS Calls", three_ds_calls_usage, expected_three_ds_calls),
            ("Fallbacks", fallbacks_usage, expected_fallbacks),
            ("Token Usage Fee", token_usage_fee, expected_token_usage_fee),
        ]:
            diff, ratio = _calc_diff(actual, expected)
            key = name.lower().replace(" ", "_")
            results[key] = {"actual": actual, "expected": expected, "diff": diff, "ratio": ratio}
            print(f"【Usage 对账】{name} - 实际: {actual}, 期望: {expected}, 差值占比: {ratio:.4%}")
            # if abs(ratio) > threshold and expected != 0:
            #     print(f"  -> 警告：{name} 偏差超过阈值")

        return results

    # 六、3DS 相关一致性对账

    def check_3ds_consistency(self,
                              csv_three_ds_call_map: dict,
                              db_threeds_result_map: dict) -> set:
        """
        11. csv_three_ds_call vs db_threeds_result 是否对等：
        - csv_three_ds_call = 1 表示这笔订单调用了 3DS；
        - db_threeds_result in ('auth_success', 'auth_failed') 表示平台侧记录到 3DS 结果；
        - 其他结果码（或缺失）视为“未知 / 未触发”，具体枚举可按 primer 后台结果补充。
        - 返回：3DS 调用与结果记录“不对等”的 order_id 集合。
        """
        problem_orders = set()
        for order_id, calls in csv_three_ds_call_map.items():
            if calls == '0':
                continue
            db_result = db_threeds_result_map.get(order_id)
            if db_result and db_result.lower() in ("auth_success", "auth_failed"):
                continue
            # 仅标记“明显不对等”的情况
            problem_orders.add(order_id)
        print(f"【3DS 对账】不对等的订单数量: {len(problem_orders)}")
        # if problem_orders:
        #     print(f"  订单: {', '.join(sorted(problem_orders))}")
        return problem_orders

    # 获取 3DS 调用结果
    @staticmethod
    def get_three_ds_result(order_id, key: str):  
        return PrimerInfo(order_id_list=[order_id]).get_three_d_reason(order_id, key)

    # 综合 run：从现有文件中加载数据并执行上述对账

    def run(self, start_time: str, end_time: str, file_path: str):
        """
        从已经生成的文件里加载数据并执行一轮完整对账：
        - 平台缓存 CSV：primer_selectdb_YYYY-MM-DD_YYYY-MM-DD.csv
        - Excel 账单：file_path
        - 对账结果 CSV：obc_result.csv（仅用于状态字段时也可直接用 db/csv map）
        
        :param start_time: 开始时间
        :param end_time: 结束时间
        :param file_path: Excel 账单文件路径
        """
        start_date = start_time[:10]
        end_date = end_time[:10]

        # 1. 从 obc_result.csv 读取所有数据
        obc_result_file = 'obc_result.csv'
        db_nt_order = set()
        db_non_failed_count = 0
        db_status_map: dict[str, str] = {}
        db_fallback_process_map: dict[str, list] = {}
        db_whether_fallback_map: dict[str, str] = {}
        db_threeds_result_map: dict[str, str] = {}
        csv_nt_order = set()
        csv_non_failed_count = 0
        csv_status_map: dict[str, str] = {}
        csv_use_fallback_amount: float = 0
        csv_use_fallback_map: dict[str, bool | str | int] = {}
        csv_three_ds_call_map: dict[str, int | str] = {}
        csv_use_nt_map: dict[str, bool | str | int] = {}

        def _get_val(row, key):
            val = (row.get(key) or "").strip()
            return val if val and val != "None" else None

        with open(obc_result_file, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                order_id = (row.get("order_id") or "").strip()
                if not order_id or row.get('csv_status') != 'SETTLED':
                    continue

                # DB 侧数据
                db_status = _get_val(row, "db_status")
                db_card_token_type = _get_val(row, "db_card_token_type")
                if db_status:
                    db_status_map[order_id] = db_status
                    if db_status != "FAILED":
                        db_non_failed_count += 1
                        if db_card_token_type == "NETWORK_TOKEN":
                            db_nt_order.add(order_id)
                
                db_whether_fallback_map[order_id] = _get_val(row, "db_whether_fallback")
                
                db_fallback_process = _get_val(row, "db_fallback_process")
                if db_fallback_process:
                    try:
                        db_fallback_process_map[order_id] = json.loads(db_fallback_process)
                    except:
                        db_fallback_process_map[order_id] = [db_fallback_process, ""]
                
                db_threeds_result_map[order_id] = _get_val(row, "db_threeds_result")
                
                # CSV 侧数据
                csv_status = _get_val(row, "csv_status")
                if csv_status:
                    csv_status_map[order_id] = csv_status
                    if csv_status != "FAILED":
                        csv_non_failed_count += 1
                
                csv_use_nt = _get_val(row, "csv_use_nt")
                if csv_use_nt and str(csv_use_nt) in ("1", "TRUE", "True", "true"):
                    csv_nt_order.add(order_id)

                csv_use_fallback_val = _get_val(row, "csv_use_fallback")
                csv_use_fallback_map[order_id] = csv_use_fallback_val
                if csv_use_fallback_val == 'True':
                    csv_use_fallback_amount += float(row.get("csv_usd_amount", 0) or 0)
                csv_three_ds_call_map[order_id] = _get_val(row, "csv_three_ds_call")
                csv_use_nt_map[order_id] = _get_val(row, "csv_use_nt")

        # 3. 执行对账并收集结果
        print("========== 开始对账 ==========")
        
        # 执行各项对账
        nt_csv_more = self.check_nt_csv_more_than_db(csv_nt_order, db_nt_order)
        nt_db_more = self.check_nt_db_more_than_csv(csv_nt_order, db_nt_order)
        status_mismatch = self.check_status_mismatch(csv_status_map, db_status_map)
        fallback_psp_invalid = self.check_fallback_psp_consistency(csv_use_fallback_map, db_fallback_process_map)
        fallback_flag_mismatch = self.check_fallback_flag_consistency(csv_use_fallback_map, db_whether_fallback_map)
        three_ds_inconsistent = self.check_3ds_consistency(csv_three_ds_call_map, db_threeds_result_map)
        
        # 收集所有有问题的订单ID和字段
        error_orders = {
            'csv_nt': sorted(nt_csv_more),
            'db_nt': sorted(nt_db_more),
            'status': sorted(status_mismatch),
            'fallback_flag': sorted(fallback_flag_mismatch),
            'fallback_psp': sorted(fallback_psp_invalid),
            'three_ds': sorted(three_ds_inconsistent),
        }
        
        # 读取已有记录，避免重复
        compare_result_file = 'compare_result_final.csv'
        all_records = set()
        existing_records = set()
        if os.path.exists(compare_result_file):
            with open(compare_result_file, 'r', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    all_records.add((row.get('order_id', ''), row.get('field', '')))
                    if row['final_result'] == 'PASSED':
                        existing_records.add((row.get('order_id', ''), row.get('field', '')))
        print('已经识别成功的订单数量: ', len(existing_records))
        
        # 准备待处理任务
        def _get_psp_count(oid):
            procs = db_fallback_process_map.get(oid, [])
            return len({p for p in procs if p}) if procs else 0
        
        tasks = []
        field_configs = {
            'csv_nt': {'csv_value': lambda oid: 'Y', 'db_value': lambda oid: 'N' if oid not in db_nt_order else 'Y',
                      'reason': 'csv标记为NT但db中不是NT'},
            'db_nt': {'csv_value': lambda oid: 'N' if oid not in csv_nt_order else 'Y', 'db_value': lambda oid: 'Y',
                     'reason': 'db标记为NT但csv中不是NT'},
            'status': {'csv_value': lambda oid: csv_status_map.get(oid, ''), 'db_value': lambda oid: db_status_map.get(oid, ''),
                      'reason': '状态不一致'},
            'fallback_flag': {'csv_value': lambda oid: str(csv_use_fallback_map.get(oid, '')),
                            'db_value': lambda oid: str(db_whether_fallback_map.get(oid, '')),
                            'reason': 'fallback标志不一致'},
            'fallback_psp': {'csv_value': lambda oid: str(csv_use_fallback_map.get(oid, '')),
                           'db_value': lambda oid: f'PSP数量={_get_psp_count(oid)}',
                           'reason': 'PSP数量与fallback标志不匹配'},
            'three_ds': {'csv_value': lambda oid: str(csv_three_ds_call_map.get(oid, '')),
                        'db_value': lambda oid: str(db_threeds_result_map.get(oid, '')),
                        'reason': '3DS调用与结果不对等'},
        }
        
        for field, oids in error_orders.items():
            for oid in oids:
                if (oid, field) not in existing_records:
                    tasks.append((oid, field, field_configs[field]))

        # 处理任务并分批写入
        fieldnames = ['order_id', 'field', 'csv_value', 'db_value', 'reason', 'real_db_value', 'final_result']
        file_exists = os.path.exists(compare_result_file)
        batch_size = 20
        write_lock = threading.Lock()
        processed = 0
        total_tasks = len(tasks)
        
        def process_task(oid, field, config):
            csv_val = config['csv_value'](oid)
            record = {
                'order_id': oid, 'field': field,
                'csv_value': csv_val,
                'db_value': config['db_value'](oid),
                'reason': config['reason']
            }
            time.sleep(0.1)  # 防止请求过快被屏蔽
            real_db_value = self.get_three_ds_result(oid, field)
            if real_db_value == '403':
                time.sleep(60)
                return process_task(oid, field, config)
            record['real_db_value'] = real_db_value
            
            # fallback_psp 特殊判断：csv_value FALSE -> real_db_value 应该是 1，TRUE -> 应该是 2
            if field == 'fallback_psp':
                expected_value = '2' if str(csv_val).upper() == 'TRUE' else '1'
                record['final_result'] = "FAILED" if str(real_db_value) != expected_value else "PASSED"
            else:
                record['final_result'] = "FAILED" if str(csv_val) != str(real_db_value) else "PASSED"
            
            print('order_id: ', oid, 'field: ', field, 'csv_value: ', csv_val, 'db_value: ', config['db_value'](oid), 'real_db_value: ', real_db_value, 'final_result: ', record['final_result'])
            return record

        def write_records(new_records):
            """写入或更新记录"""
            if not new_records:
                return
            
            with write_lock:
                # 读取所有现有记录
                existing_data = {}
                if os.path.exists(compare_result_file):
                    with open(compare_result_file, 'r', encoding='utf-8', newline='') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            key = (row.get('order_id', ''), row.get('field', ''))
                            existing_data[key] = row
                
                # 更新或添加新记录
                for record in new_records:
                    key = (record.get('order_id', ''), record.get('field', ''))
                    existing_data[key] = record
                
                # 写回所有记录
                with open(compare_result_file, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(existing_data.values())
                    f.flush()
        
        batch = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(process_task, oid, field, config): (oid, field) for oid, field, config in tasks}
            for future in as_completed(futures):
                record = future.result()
                if record:
                    batch.append(record)
                    processed += 1
                    
                    if len(batch) >= batch_size:
                        write_records(batch)
                        batch = []
                    
                    if processed % 10 == 0 or processed == total_tasks:
                        print(f"进度: {processed}/{total_tasks} ({processed*100//total_tasks}%)")
        
        if batch:
            write_records(batch)
        
        print(f"检查结果已保存到: {compare_result_file}，处理 {processed} 条记录")
        print("========== 对账结束 ==========")


if __name__ == '__main__':
    # 直接硬编码参数运行，无需命令行传参
    start_date = "2025-11-01"
    end_date = "2025-12-01"
    # Excel 账单文件（Primer 导出的当月 Billing 报表）
    file_path = os.path.join(os.path.dirname(__file__), "CenturyGamesBilling_November.xlsx")
    start_time = start_date + " 00:00:00"
    end_time = end_date + " 00:00:00"

    # ====== TODO: 按实际 Primer 合同 / PDF 填入四个期望值（示例为占位） ======
    EXPECTED_FEE_PER_PAYMENT = 141216
    EXPECTED_3DS_CALLS = 55715
    EXPECTED_FALLBACKS = 78697.72
    EXPECTED_TOKEN_USAGE_FEE = 7050

    # 第一步：拉取/缓存原始数据 + 生成 obc_result
    GenerateData().run(start_time, end_time, file_path)

    # 第二步：基于生成的中间文件做对账
    CompareData().run(
        start_time, end_time, file_path
    )
