import httpx
import json
import logging
from datetime import datetime
from pushme import pushme
import os
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

headers = {
    "Host": "xqh5.17wanxiao.com",
    "user-agent": "Mozilla/5.0 (Linux; Android 12; M2012K11AC Build/SKQ1.211006.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/96.0.4664.104 Mobile Safari/537.36 Wanxiao/5.7.2",
    "content-type": "application/x-www-form-urlencoded",
    "accept": "*/*",
    "origin": "https://xqh5.17wanxiao.com",
    "x-requested-with": "com.newcapec.mobile.ncp",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "referer": "https://xqh5.17wanxiao.com/userwaterelecmini/index.html",
    "accept-encoding": "gzip, deflate",
    "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
}


def getBindRoom(account):
    url = 'https://xqh5.17wanxiao.com/smartWaterAndElectricityService/SWAEServlet'    
    param = {
        "cmd": "getbindroom",
        "account": account,
        "timestamp": datetime.now().strftime("%Y%m%d%H%M%S%f")
    }
    data = {
        "param": json.dumps(param),
        "customercode": "610",
        "method": "getbindroom",
        "command": "JBSWaterElecService"
    }
    with httpx.Client(http2=True) as client:
        response = client.post(url, data=data, headers=headers)
        try:
            data = json.loads(response.json().get("body"))
            roomverify = data.get("roomlist",[None])[-1].get("roomverify")
            return roomverify
        except Exception as e:
            logger.error(f"解析数据失败，错误信息：{e}")
            return None



def getData(roomverify, account):
    url = "https://xqh5.17wanxiao.com/smartWaterAndElectricityService/SWAEServlet"
    param = {
        "cmd": "h5_getstuindexpage",
        "roomverify": roomverify,
        "account": account,
        "timestamp": datetime.now().strftime("%Y%m%d%H%M%S%f")
    }
    data = {
        "param": json.dumps(param),
        "customercode": "610",
        "method": "h5_getstuindexpage",
        "command": "JBSWaterElecService"
    }

    with httpx.Client(http2=True) as client:
        response = client.post(url, data=data, headers=headers)
        try:
            data = json.loads(response.json().get("body"))
            return data
        except Exception as e:
            logger.error(f"解析数据失败，错误信息：{e}")
            return None


def parseData(data):
    roomfullname = data.get("roomfullname")
    odd = data.get("modlist", [None])[0].get("odd")
    todayuse = data.get("modlist", [None])[0].get("todayuse")

    return {
        "roomfullname": roomfullname,
        "odd": odd,
        "todayuse": todayuse
    }


def main():
    push_key = os.getenv('PUSH_KEY')  # PUSH_KEY
    if push_key is None: 
        logger.warning("PUSH_KEY 未设置!!\n取消推送")
    account = os.getenv('ACCOUNT')  # account
    if account is None: 
        logger.error("请填写正确的账号")
        return
    roomverify = getBindRoom(account)
    if roomverify is None: 
        logger.error("未绑定房间，请先绑定房间。")
        return
    data = getData(roomverify=roomverify,account=account)
    if data is None: 
        logger.error("获取数据失败，请检查账号是否正确。")
        return
    parseedData = parseData(data)
    logger.info(
        f"房间号：{parseedData.get('roomfullname')},今日用电量：{parseedData.get('todayuse')},剩余电量：{parseedData.get('odd')}")

    if parseedData.get("odd") <= 15 and push_key is not None:
        logger.warning(f"剩余电量不足15度,请及时充值")
        notity = pushme(push_key)
        if notity.sendNotify("剩余电量不足15度,请及时充值", f"房间号：{parseedData.get('roomfullname')},今日用电量：{parseedData.get('todayuse')},剩余电量：{parseedData.get('odd')}"):
            logger.info("推送成功")
        else:
            logger.errors('推送失败')

    if datetime.now().hour == 12 and push_key is not None:
        logger.info("开始推送通知")
        notity = pushme(push_key)
        if notity.sendNotify("12点推送", f"房间号：{parseedData.get('roomfullname')},今日用电量：{parseedData.get('todayuse')},剩余电量：{parseedData.get('odd')}"):
            logger.info("推送成功")
        else:
            logger.errors('推送失败')
    


if __name__ == '__main__':
    main()
