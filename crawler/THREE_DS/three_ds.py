import random
import time

import pandas as pd
import requests

EXCEL_FILE = "../3ds_订单.xlsx"
SHEET_NAMES = "Sheet1"
TARGET_COLUMN = "order_id"
URL = "https://payment-timeline.api.production.core.primer.io/v1/payments/{order_id}/timeline"
headers = {
    'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIzMTFhMDYyYS1iOWQ3LTQxNzMtODk3MS00ZjY3YjVmMTI2MmYiLCJleHAiOjE3NjQyMzExMDkuMzczNTY3LCJzY29wZXMiOiJhY2NvdW50czpyZWFkIGFjY291bnRzOnN3aXRjaCBhY2NvdW50czp3cml0ZSBhcGlfa2V5czpyZWFkIGFwaV9rZXlzOndyaXRlIGJpbGxpbmc6cmVhZCBjaGVja291dC1jb25maWc6cmVhZCBjaGVja291dC1jb25maWc6d3JpdGUgZGlzcHV0ZXM6cmVhZCBldGwtcGlwZWxpbmVzOnJlYWQgZXRsLXBpcGVsaW5lczp3cml0ZSBpbnZpdGF0aW9uczpyZWFkIGludml0YXRpb25zOndyaXRlIG1ldHJpY3M6cmVhZCBub3RpZmljYXRpb25zOnJlYWQgbm90aWZpY2F0aW9uczp3cml0ZSBvbmJvYXJkaW5nOnJlYWQgb25ib2FyZGluZzp3cml0ZSBwYXltZW50X21ldGhvZHM6cmVhZCBwYXltZW50X21ldGhvZHM6d3JpdGUgcGlpOnJlYWQgcHJpbWVyLWFkYXB0OnJlYWQgcHJvY2Vzc29yczpyZWFkIHByb2Nlc3NvcnM6d3JpdGUgcHJvZmlsZTpyZWFkIHByb2ZpbGU6d3JpdGUgcmVjb25jaWxpYXRpb246cmVhZCByZWNvbmNpbGlhdGlvbjp3cml0ZSB0aHJlZV9kczpvbmJvYXJkIHRyYW5zYWN0aW9uczpjYW5jZWwgdHJhbnNhY3Rpb25zOnJlYWQgdHJhbnNhY3Rpb25zOnJlZnVuZCB1c2VyLXJvbGVzOndyaXRlIHVzZXJfcm9sZXM6d3JpdGUgdXNlcnM6cmVhZCB1c2Vyczp3cml0ZSB3YWxsZXQtY29udmVyc2lvbnM6d3JpdGUgd2FsbGV0LXF1b3Rlczp3cml0ZSB3YWxsZXQtdHJhbnNmZXJzOndyaXRlIHdhbGxldHM6cmVhZCB3b3JrZmxvd3M6cmVhZCB3b3JrZmxvd3M6d3JpdGUiLCJ1c2VyX2lkIjoiMzExYTA2MmEtYjlkNy00MTczLTg5NzEtNGY2N2I1ZjEyNjJmIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInVzZXJfdHlwZSI6Ik1FUkNIQU5UIiwicHJpbWVyX2FjY291bnRfaWQiOiIyNTllYTBhOS02OWM4LTQyNWYtOTBmOC1jYTUzMmQ2YjMzMTgifQ.93ncUc2mAbn0H51g6JO5mmHXWarV9L8Z764c3eMCiDw'
}

def main() -> None:
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAMES)
    updates_since_save = 0
    order_100_list = []
    for idx, order_id in df[TARGET_COLUMN].items():
        if pd.isna(order_id) or str(df.at[idx, "mark"]) not in ['-100', 'nan']:
            continue
        order_100_list.append(order_id)
        reason = get_three_d_reason(order_id)
        df.at[idx, "mark"] = reason
        print(f'{order_id}: {reason}')
        updates_since_save += 1

        if updates_since_save and updates_since_save % 100 == 0:
            persist_sheet(df)
            print("已保存最近的100条结果")
    print(order_100_list)
    persist_sheet(df)

def wrong() -> None:
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAMES)
    order_100_list = []
    for idx, order_id in df[TARGET_COLUMN].items():
        if pd.isna(order_id) or str(df.at[idx, "mark"]) in ['-100', 'nan', '0']:
            order_100_list.append(order_id)
            print(f'{order_id}: {df.at[idx, "mark"]}')
    print(len(order_100_list))

def persist_sheet(df: pd.DataFrame) -> None:
    with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df.to_excel(writer, sheet_name=SHEET_NAMES, index=False)

def get_three_d_reason(order_id):
    url = URL.format(order_id=order_id)
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
    except requests.HTTPError as exc:
        reason = '0'
        return reason

    resp_json = resp.json()
    threeDSecureAuthentication = resp_json[-1]['paymentInstrumentToken']['threeDSecureAuthentication']
    reason = '-100'
    if not threeDSecureAuthentication:
        reason = '1-unknown'
    else:
        responseCode = threeDSecureAuthentication['responseCode']
        reasonText = threeDSecureAuthentication['reasonText']
        if responseCode == 'SKIPPED':
            if reasonText == 'Unknown ACS response':
                reason = '2-Skipped: Unknown ACS response'
            elif reasonText == 'Issuer does not support 3DS V2':
                reason = '3-Skipped: Issuer does not support 3DS V2'
            elif reasonText == 'Transaction data not valid':
                reason = '4-Skipped: Transaction data not valid'
            elif reasonText == 'Access denied, invalid endpoint':
                reason = '6-Skipped: Access denied invalid endpoint'
            elif reasonText == 'Malformed response from the ACS':
                reason = '7-Transaction Timed Out At The Acs'
            elif reasonText == 'I/O error on POST request for "https://3ds2.visa.com/VbV2DS2.0/DS2/authenticate": Connection reset':
                reason = '8-I/O error on POST request'
            elif reasonText == 'Permanent System Failure':
                reason = '9-Skipped: Permanent System Failure'
            elif reasonText == 'Format of one or more elements is invalid according to the specification.':
                reason = '10-Skipped: Format of one or more elements is invalid according to the specification'
            elif reasonText == 'Message version not supported.':
                reason = '11-Skipped: Message version not supported'
            elif reasonText == 'Cardholder Account Number is not in a range belonging to Issuer':
                reason = '12-Skipped: Message version not supported'
            else:
                reason = reasonText
        elif responseCode == 'AUTH_FAILED':
            if reasonText == 'Transaction Timed Out At The Acs':
                reason = '5-Transaction Timed Out At The Acs'
        else:
            reason = '-100'
    return reason

if __name__ == "__main__":
    main()
    # wrong()
