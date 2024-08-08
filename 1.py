import subprocess
import json
import requests
import time
import hashlib
import hmac
import base64
import urllib.parse

# 执行命令并获取输出
def get_sync_info():
    command = "artelad status | jq .SyncInfo"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout

# 获取公网IP
def get_public_ip():
    result = subprocess.run("curl -s ifconfig.me", shell=True, capture_output=True, text=True)
    return result.stdout.strip()

# 获取公网IP的国家信息
def get_ip_country(ip):
    url = f"https://ipinfo.io/{ip}/json"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("country", "未知")
    else:
        print(f"无法获取IP国家信息，状态码: {response.status_code}")
        return "未知"

# 请求最新区块信息
def get_latest_block_height():
    url = "https://api.artela.dadunode.com/cosmos/base/tendermint/v1beta1/blocks/latest"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()["block"]["header"]["height"]
    else:
        print(f"无法获取最新区块信息，状态码: {response.status_code}")
        return None

# 发送钉钉消息
def send_dingtalk_message(content):
    webhook = 'https://oapi.dingtalk.com/robot/send?access_token=9d809f7243698fedaa07f1852d01ca95069b7a6a96283319061937433ec30789'
    secret = 'SEC394375ddec3c6c64cfaea79626fe4e22eebf95f471dfdd933d89a208085db3e7'

    # 当前时间戳（毫秒）
    timestamp = str(round(time.time() * 1000))

    # 生成签名
    string_to_sign = f"{timestamp}\n{secret}"
    sign = base64.b64encode(hmac.new(secret.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha256).digest()).decode('utf-8')
    sign = urllib.parse.quote_plus(sign)  # URL编码

    # 构建请求URL
    url = f"{webhook}&timestamp={timestamp}&sign={sign}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
    
    # 发送请求
    response = requests.post(url, headers=headers, json=data)
    return response.status_code, response.text

if __name__ == "__main__":
    while True:
        sync_info = get_sync_info()
        sync_info_json = json.loads(sync_info)

        # 获取当前时间和公网IP
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        public_ip = get_public_ip()
        country = get_ip_country(public_ip)  # 获取国家信息

        # 获取最新区块高度
        latest_block_height = sync_info_json['latest_block_height']
        latest_block_height_api = get_latest_block_height()

        if latest_block_height_api is not None:
            # 计算差值
            height_difference = int(latest_block_height_api) - int(latest_block_height)

            # 构建消息内容
            message_content = (
                f"夫拉斯基监控报警：\n"
                f"时间：{current_time}\n"
                f"IP：{public_ip}\n"
                f"国家：{country}\n"
                f"latest_block_height：{latest_block_height}\n"
                f"height：{latest_block_height_api}\n"
                f"差值：{height_difference}\n"
            )

            # 添加警告信息
            if height_difference > 200:
                message_content += "注意注意：服务器跟不上块了！！！\n"

            # 发送消息
            status_code, response_text = send_dingtalk_message(message_content)
            print(f"发送状态: {status_code}, 响应: {response_text}")

        # 每两小时查询一次
        time.sleep(7200)
