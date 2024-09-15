#!/usr/bin/python3
# coding=utf-8
"""
Author: Xe
time: 2024/9/15
cron: 0 25 */2 * * *
new Env('电费查询');
"""
import requests
import json
import logging
from datetime import datetime, timedelta
from retrying import retry
from WxPusher import WxPusher
import os
### 配置 ###
# 日志配置
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='wanmei_electricity.log',
                    filemode='w',
                    encoding='utf-8')  # 编码问题，改为utf-8
logger = logging.getLogger(__name__)
# 日志输出到控制台
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

### 常量 ###
# server酱推送配置
ELECTRICITY_INFO_URL = 'https://xqh5.17wanxiao.com/smartWaterAndElectricityService/SWAEServlet'
WEEKLY_ELECTRICITY_INFO_URL = 'https://xqh5.17wanxiao.com/smartWaterAndElectricityService/SWAEServlet'
# Script 配置
ERROR_FILE = 'wanmei_electricity_error.json'
MAX_RETRIES = 3
WAIT_TIME = 1000
# timestamp exampe: 2024091401014782
TIMESTAMP = str(int(datetime.now().timestamp() * 1000))
# env
CUSTOMERCODE = os.getenv('CUSTOMERCODE')  # customercode
ACCOUNT = os.getenv('ACCOUNT')  # account
ROOMMERIFY = os.getenv('ROOMVERIFY')  # roomverify

# 通知配置
TITLE = '宿舍电费查询'
### 全局变量 ###

getInfo_headers = {
    'Host': 'xqh5.17wanxiao.com',
    'user-agent': 'Mozilla/5.0 (Linux; Android 12; M2012K11AC Build/SKQ1.211006.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/96.0.4664.104 Mobile Safari/537.36 Wanxiao/5.7.2',
    'accept': '*/*',
    'origin': 'https://xqh5.17wanxiao.com',
    'x-requested-with': 'com.newcapec.mobile.ncp',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://xqh5.17wanxiao.com/userwaterelecmini/index.html',
    'accept-encoding': 'gzip, deflate',
    'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
}

weekly_info_format = {
    'date': '',
    'used': 0,
    'speed_of_consumption': 0.0
}
# today = datetime.today().strftime('%m-%d')
# yesterday = (datetime.today() - timedelta(days=1)).strftime('%m-%d')
today = datetime.today()
yesterday = today - timedelta(days=1)


today = today.strftime('%m-%d')
yesterday = yesterday.strftime('%m-%d')
today_hour = datetime.now().hour

msg_list = []
### 方法 ###


@retry(stop_max_attempt_number=MAX_RETRIES, wait_fixed=WAIT_TIME)
def getInfo_electricity():
    params = {"cmd": "getbindroom", "account": ACCOUNT,
              "timestamp": TIMESTAMP}

    data = {
        'param':json.dumps(params),
        'customercode': CUSTOMERCODE,
        'method': 'getbindroom',
        'command': 'JBSWaterElecService',
    }
    try:
        response = requests.post(ELECTRICITY_INFO_URL,
                                 headers=getInfo_headers, data=data)
        response.raise_for_status()  # 检查请求是否成功

        if response.json().get('code_') != 0:
            handle_error_response(response)

        # 解析数据
        return json.loads(response.json()['body']).get('detaillist', [{}])[0].get('sumbuy')

    except (requests.RequestException, KeyError, IndexError, json.JSONDecodeError) as e:
        logger.error(f'获取电量信息失败，错误信息：{e}')
        return None


def handle_error_response(response):
    try:
        resp_data = response.json()
        error_msg = resp_data.get('message_', '未知错误')
        body = resp_data.get('body', {})

        with open(ERROR_FILE, 'w', encoding='utf-8') as f:
            json.dump(body, f, indent=4, ensure_ascii=False)

        logger.error(f'查询失败，错误信息：{error_msg}，错误详情已保存到 {ERROR_FILE}')
    except Exception as e:
        logger.error(f'保存错误详情失败，错误信息：{e}')


@retry(stop_max_attempt_number=MAX_RETRIES, wait_fixed=WAIT_TIME)
def get_weekly_electricity_info():
    params = {"cmd":"h5_getstuindexpage","roomverify":ROOMMERIFY,"account":ACCOUNT,"timestamp":TIMESTAMP}
    data = {
        'param': json.dumps(params),
        'customercode': CUSTOMERCODE,
        'method': 'h5_getstuindexpage',
        'command': 'JBSWaterElecService',
    }
    try:
        response = requests.post(
            WEEKLY_ELECTRICITY_INFO_URL, headers=getInfo_headers, data=data)
        response.raise_for_status()

        if response.json().get('code_') != 0:
            handle_error_response(response)

        weekuselist = json.loads(response.json()['body']).get(
            'modlist', [{}])[0].get('weekuselist', [])
        for info in weekuselist[-3:]:  # 只取最近三条数据
            yield process_weekly_electricity_info(info)

    except (requests.RequestException, KeyError, IndexError, json.JSONDecodeError) as e:
        logger.error(f'获取周电量信息失败，错误信息：{e}')
        return None


def process_weekly_electricity_info(info):
    processed_info = {'date': info.get('date'), 'used': info.get(
        'use'), 'speed_of_consumption': 0.0}

    if processed_info['date'] and processed_info['used'] is not None:
        speed_of_consumption = processed_info['used'] / (
            today_hour if processed_info['date'] == today and today_hour > 0 else 24)
        processed_info['speed_of_consumption'] = round(speed_of_consumption, 2)
    else:
        logger.error('信息缺少日期或用电量，无法处理')
        return None
    return processed_info


def main():
    try:
        electricity_info = getInfo_electricity()
        if electricity_info is None:
            logger.error("无法获取电量信息，终止程序。")
            return

        logger.info(f"获取电费信息成功，电量：{electricity_info} 度")
        msg_list.append(f"电量：{electricity_info} 度\n")

        weekly_electricity_info = tuple(get_weekly_electricity_info())
        if len(weekly_electricity_info) < 3:
            logger.error("未获取到完整的周用电量信息，终止程序。")
            return

        msg_str_today = (f"今日用电量：{weekly_electricity_info[-1]['used']} 度，"
                         f"平均消耗速度 {weekly_electricity_info[-1]['speed_of_consumption']} 度/小时")
        msg_list.append(msg_str_today)

        yesterday_used = weekly_electricity_info[-2]['used']
        day_before_yesterday_used = weekly_electricity_info[-3]['used']
        changed = abs(yesterday_used - day_before_yesterday_used)
        msg_str_changed = "多用" if yesterday_used > day_before_yesterday_used else "节约"

        msg_str_saved = f"昨天比前天{msg_str_changed} {changed} 度"
        msg_list.append(msg_str_saved)

        msg = '\n'.join(msg_list)
        logger.info(msg)

        logger.info("开始推送微信通知")
        pusher = WxPusher()
        if pusher.send_message(TITLE, msg):
            logger.info("微信通知发送成功")
        else:
            logger.error("微信通知发送失败")

    except Exception as e:
        logger.error(f"执行主程序时发生错误：{e}")

### end ###


if __name__ == '__main__':
    main()
