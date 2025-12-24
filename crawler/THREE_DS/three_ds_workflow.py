import requests
import pymysql
import datetime


class PrimerInfo:

    URL = "https://payment-timeline.api.production.core.primer.io/v1/payments/{order_id}/timeline"
    HEADERS = {
        'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIzMTFhMDYyYS1iOWQ3LTQxNzMtODk3MS00ZjY3YjVmMTI2MmYiLCJleHAiOjE3NjY1NDU2NTAuOTM2MjQ4LCJzY29wZXMiOiJhY2NvdW50czpyZWFkIGFjY291bnRzOnN3aXRjaCBhY2NvdW50czp3cml0ZSBhaS1jb21wbGV0aW9uczp3cml0ZSBhaS1qb2JzOnJlYWQgYWktam9iczp3cml0ZSBhaS1tb2RlbHM6cmVhZCBhcGlfa2V5czpyZWFkIGFwaV9rZXlzOndyaXRlIGJpbGxpbmc6cmVhZCBjaGVja291dC1jb25maWc6cmVhZCBjaGVja291dC1jb25maWc6d3JpdGUgZGlzcHV0ZXM6cmVhZCBldGwtcGlwZWxpbmVzOnJlYWQgZXRsLXBpcGVsaW5lczp3cml0ZSBpbnZpdGF0aW9uczpyZWFkIGludml0YXRpb25zOndyaXRlIG1ldHJpY3M6cmVhZCBub3RpZmljYXRpb25zOnJlYWQgbm90aWZpY2F0aW9uczp3cml0ZSBvbmJvYXJkaW5nOnJlYWQgb25ib2FyZGluZzp3cml0ZSBwYXltZW50X21ldGhvZHM6cmVhZCBwYXltZW50X21ldGhvZHM6d3JpdGUgcGlpOnJlYWQgcHJpbWVyLWFkYXB0OnJlYWQgcHJvY2Vzc29yczpyZWFkIHByb2Nlc3NvcnM6d3JpdGUgcHJvZmlsZTpyZWFkIHByb2ZpbGU6d3JpdGUgcmVjb25jaWxpYXRpb246cmVhZCByZWNvbmNpbGlhdGlvbjp3cml0ZSB0aHJlZV9kczpvbmJvYXJkIHRyYW5zYWN0aW9uczpjYW5jZWwgdHJhbnNhY3Rpb25zOnJlYWQgdHJhbnNhY3Rpb25zOnJlZnVuZCB1c2VyLXJvbGVzOndyaXRlIHVzZXJfcm9sZXM6d3JpdGUgdXNlcnM6cmVhZCB1c2Vyczp3cml0ZSB3YWxsZXQtY29udmVyc2lvbnM6d3JpdGUgd2FsbGV0LXF1b3Rlczp3cml0ZSB3YWxsZXQtc2RrLXNlc3Npb25zOndyaXRlIHdhbGxldC10cmFuc2ZlcnM6d3JpdGUgd2FsbGV0czpyZWFkIHdvcmtmbG93czpyZWFkIHdvcmtmbG93czp3cml0ZSIsInVzZXJfaWQiOiIzMTFhMDYyYS1iOWQ3LTQxNzMtODk3MS00ZjY3YjVmMTI2MmYiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwidXNlcl90eXBlIjoiTUVSQ0hBTlQiLCJwcmltZXJfYWNjb3VudF9pZCI6IjI1OWVhMGE5LTY5YzgtNDI1Zi05MGY4LWNhNTMyZDZiMzMxOCJ9.AarusJOpqclHeZKlPhliflLWWHhFwScS0n6ieqAmGFg'
    }
    def __init__(self, order_id_list):
        self.order_id_list = order_id_list

    @staticmethod
    def get_three_d_reason(order_id, key: str):
        # if key != 'yc5SqMFaP':
        #     return
        url = PrimerInfo.URL.format(order_id=order_id)
        try:
            resp = requests.get(url, headers=PrimerInfo.HEADERS)
            resp.raise_for_status()
        except Exception as e:
            print(f"Error : {order_id}: {e}")
            return e.args[0][0:3]

        resp_json = resp.json()

        if key == 'three_ds':
            threeDSecureAuthentication = resp_json[-1]['paymentInstrumentToken']['threeDSecureAuthentication']['responseCode'] == 'AUTH_SUCCESS'
            result = '1' if threeDSecureAuthentication else '0'
        elif key == 'csv_nt':
            result = 'Y' if resp_json else 'N'
        elif key == 'status':
            result = resp_json[0]['children'][0]['result']
        elif key == 'fallback_flag':
            fallback_num = 0
            for child in resp_json[0]['children']:
                if 'thirdPartyId' in child:
                    fallback_num += 1
            if fallback_num > 1:
                result = 'TRUE'
            elif fallback_num == 1:
                result = 'FALSE'
            else:
                result = 'UNKNOWN'
        elif key == 'fallback_psp':
            result = 0
            for child in resp_json[0]['children']:
                if 'thirdPartyId' in child:
                    result += 1
        else:
            result = None
        return result


    @staticmethod
    def get_data_from_selectdb(order_id, key):
        """从 SelectDB 中根据 order_id 读取对应的参数"""
        config = {
            "host": "selectdb-cluster-tcp-18731f6a6a8c802c.elb.us-west-2.amazonaws.com",
            "user": "backend",
            "password": "8NOvntHJ",
            "port": 9030,
            "database": "backend_pf",
        }
        connection = pymysql.connect(cursorclass=pymysql.cursors.DictCursor, **config)
        try:
            cursor = connection.cursor()
            sql = f"""select * from backend_pf.primer_transaction_data where id = "{order_id}" """
            cursor.execute(sql)
            row = cursor.fetchall()
            return row if row else None
        finally:
            connection.close()

    def run(self):
        for order_id in self.order_id_list:
            print(self.get_three_d_reason(order_id))

if __name__ == "__main__":
    order_id_list = []
    PrimerInfo(order_id_list).run()