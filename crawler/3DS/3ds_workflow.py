import requests

URL = "https://payment-timeline.api.production.core.primer.io/v1/payments/{order_id}/timeline"
headers = {
    'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIzMTFhMDYyYS1iOWQ3LTQxNzMtODk3MS00ZjY3YjVmMTI2MmYiLCJleHAiOjE3NjQyMzExMDkuMzczNTY3LCJzY29wZXMiOiJhY2NvdW50czpyZWFkIGFjY291bnRzOnN3aXRjaCBhY2NvdW50czp3cml0ZSBhcGlfa2V5czpyZWFkIGFwaV9rZXlzOndyaXRlIGJpbGxpbmc6cmVhZCBjaGVja291dC1jb25maWc6cmVhZCBjaGVja291dC1jb25maWc6d3JpdGUgZGlzcHV0ZXM6cmVhZCBldGwtcGlwZWxpbmVzOnJlYWQgZXRsLXBpcGVsaW5lczp3cml0ZSBpbnZpdGF0aW9uczpyZWFkIGludml0YXRpb25zOndyaXRlIG1ldHJpY3M6cmVhZCBub3RpZmljYXRpb25zOnJlYWQgbm90aWZpY2F0aW9uczp3cml0ZSBvbmJvYXJkaW5nOnJlYWQgb25ib2FyZGluZzp3cml0ZSBwYXltZW50X21ldGhvZHM6cmVhZCBwYXltZW50X21ldGhvZHM6d3JpdGUgcGlpOnJlYWQgcHJpbWVyLWFkYXB0OnJlYWQgcHJvY2Vzc29yczpyZWFkIHByb2Nlc3NvcnM6d3JpdGUgcHJvZmlsZTpyZWFkIHByb2ZpbGU6d3JpdGUgcmVjb25jaWxpYXRpb246cmVhZCByZWNvbmNpbGlhdGlvbjp3cml0ZSB0aHJlZV9kczpvbmJvYXJkIHRyYW5zYWN0aW9uczpjYW5jZWwgdHJhbnNhY3Rpb25zOnJlYWQgdHJhbnNhY3Rpb25zOnJlZnVuZCB1c2VyLXJvbGVzOndyaXRlIHVzZXJfcm9sZXM6d3JpdGUgdXNlcnM6cmVhZCB1c2Vyczp3cml0ZSB3YWxsZXQtY29udmVyc2lvbnM6d3JpdGUgd2FsbGV0LXF1b3Rlczp3cml0ZSB3YWxsZXQtdHJhbnNmZXJzOndyaXRlIHdhbGxldHM6cmVhZCB3b3JrZmxvd3M6cmVhZCB3b3JrZmxvd3M6d3JpdGUiLCJ1c2VyX2lkIjoiMzExYTA2MmEtYjlkNy00MTczLTg5NzEtNGY2N2I1ZjEyNjJmIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInVzZXJfdHlwZSI6Ik1FUkNIQU5UIiwicHJpbWVyX2FjY291bnRfaWQiOiIyNTllYTBhOS02OWM4LTQyNWYtOTBmOC1jYTUzMmQ2YjMzMTgifQ.93ncUc2mAbn0H51g6JO5mmHXWarV9L8Z764c3eMCiDw'
}


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
    # print(get_three_d_reason("hsBAIDK6U")) # 1 unknown
    # print(get_three_d_reason("AjjVRlVIn")) # 2 skipped:unknown acs
    # print(get_three_d_reason("zDlHAaKOw")) # 4 skipped transaction data not valid
    # print(get_three_d_reason("NYRRwrVNQ")) # 5 Transaction timed out
    # print(get_three_d_reason("3ha98yyZ4")) # 6 skipped access denied
    # print(get_three_d_reason("eA4DOFoX5")) # 7 skipped malform
    order_id_list = ['jTmhU9d1v', '8ExDQ5K43', 'Qpg32aD4d', '6yY2Fw1a4', 'GMHSr9T0m', 'gugGDYFI1', '5KQtnscx5', 'Hwl8mExcp', 'sFzw1MKzF', 'HAADTpm5e', 'aHB9c7yao', '8m2U2CPZQ', 'JVV0dVw6Q', 'zkHYFB5v5', 'LGsgxTFYs', 'J4rpYpcH8', 'j1DummOpr', 'TT7b4msem', 'dohWjwaFT', '4axdv51CA', 'TuxpzHc8j', 'H7LqSFWBS', 'W6ZLpQipc', 'VKom5g2iz', 'YT0ZRu02P', '3CBYJUcxG', 'xPvo6dkdd', 'OV2Bi87mh', '9pWeKvP7b', 'HH8w8eUm8', 'vkhyDUj3P', 'ipFiFoqhx', 'E1SMMk1va', '4kOXUMdNF', 'mRTL8Bc9d', 'A0aRDrGXP', 'wWe3mtZcF', 'aT6Od7eLd', 'mi0T7W1f1', 'cnndqfKJl', 'NjshrCDZu']
    for order_id in order_id_list:
        print(get_three_d_reason(order_id))
