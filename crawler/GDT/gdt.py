import time

import requests

URL = "https://api.e.qq.com/v3.0/pre_attribute/get"
timestamp = str(int(time.time()))
PARAMS = {
    "access_token": "9bf1a8c4d01257ee5c9dda3d62a6c451",# old
    "timestamp": timestamp,
    "nonce": timestamp,
    "app_id": '6478492012', # new
    "device_os_type": "1",
    "optimization_goal": "OPTIMIZATIONGOAL_APP_ACTIVATE",
    "action_time": '1764069909',
    "account_id": "41219721", # old
    # "account_id": "68903241",
    # "idfv": "C23A4FDC-61C9-4D04-956B-76827842A940", # old
    "idfv": "77FED66F-085C-40C4-BC77-150938861017"
}

if __name__ == "__main__":
    resp = requests.get(URL, params=PARAMS)
    print(resp.text)