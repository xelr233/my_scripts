#!/usr/bin/python3
# coding=utf-8
"""
Author: Xe
time: 2024/2/9
cron: 0 25 */2 * * *
new Env('监控AkileCloud');
"""
import requests
import json
import time
import os
###
#token = "62871993f33d4750b4a6e6ddafc2d035"
#title = "监控_AkileCloud"

config = {
    'PUSH_PLUS_TOKEN':'',
    'TITLE':'监控_AkileCloud'
}
###
for k in config:
    v = os.getenv(k)
    if v is not None:
        if v == '':
            print(f"环境变量 {k} 为空")
        else:
            print(f"环境变量 {k} 的值为: {v}")
            config[k] = v
    else:
        print(f"缺少环境变量 {k}")
        exit()
url = "https://api.akile.io/api/v1/store/GetVpsStore"
headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"}
counter = 0
is_Get_data_succes = False
need_send_msg = False
check_nodes = []
difference = []
while counter < 10:
    response = requests.get(url=url,headers=headers)
    if response.ok == True:
        response_json = json.loads(response.text)
        #stack = response_json['data'][5]['nodes'][-2]['plans'][0]['stock']
        for item in response_json['data']:
            for node in item['nodes']:
                for plan in node['plans']:
                    if plan['price_datas'][0]['price'] < 1700:
                        nodes_price = {'name':plan['plan_name']}
                        nodes_price['stock'] = plan['stock']
                        nodes_price['price'] = plan['price_datas'][0]['price'] / 100
                        check_nodes.append(nodes_price)
        is_Get_data_succes = True
        break
    else:
        counter +=1
        time.sleep(5)
if not is_Get_data_succes:
    print("获取失败")
    exit()
try:
    with open("result.log",'r+',encoding="UTF-8") as f:
        context = json.loads(f.read())
        difference = [item for item in check_nodes if item not in context]
        if difference:
            f.seek(0)
            f.write(json.dumps(check_nodes))
            f.truncate()
            need_send_msg = True
except Exception:
    print("文件不存在")
    with open("result.log",'w',encoding="UTF-8") as f:
        f.write(json.dumps(check_nodes))
        difference = check_nodes
        need_send_msg = True
if not need_send_msg:
    exit()
msg = ""
for each in difference:
    msg = msg + f"节点类型：{each['name']}🖥️ 价格：{each['price']}💰 数量；{each['stock']}\n"
send_url = "http://www.pushplus.plus/send/"
body = {
    "token":config['PUSH_PLUS_TOKEN'],
    "title": config.get('TITLE','监控_AkileCloud'),
    "content":f"当前时间是{time.asctime(time.localtime())}\n{msg}",
    "template":"html"
}
response = requests.post(url = send_url,headers=headers,params=body)
if json.loads(response.text)['code'] == 200:
    print("发送成功")
else:
    print("发送失败")