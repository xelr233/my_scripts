#!/usr/bin/python
# coding=utf-8
"""
File: check_AkileCloud.py
Author: Xe
Data: 2024/2/8 21:00
cron 0 25 */2 * * *
"""
import requests
import json
import time

###
token = "62871993f33d4750b4a6e6ddafc2d035"
title = "监控_AkileCloud"
###
url = "https://api.akile.io/api/v1/store/GetVpsStore"
headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"}
counter = 0
is_Get_data_succes = False
#slack = None
check_nodes = []
while counter < 10:
    response = requests.get(url=url,headers=headers)
    if response.ok == True:
        response_json = json.loads(response.text)
        #stack = response_json['data'][5]['nodes'][-2]['plans'][0]['stock']
        for item in response_json['data']:
            for node in item['nodes']:
                for plan in node['plans']:
                    if plan['price_datas'][0]['price'] < 1200:
                        nodes_price = {'name':plan['plan_name']}
                        nodes_price['price'] = plan['price_datas'][0]['price'] / 100
                        check_nodes.append(nodes_price)
        is_Get_data_succes = True
        break
    else:
        counter +=1
        time.sleep(5)
if is_Get_data_succes == False:
    print("获取失败")
    exit()
msg = ""
for each in check_nodes:
    msg = msg + f"节点类型：{each['name']}🖥️ 价格：{each['price']}💰\n"
send_url = "http://www.pushplus.plus/send/"
body = {
    "token":token,
    "title": title,
    "content":f"当前时间是{time.asctime(time.localtime())}\n{msg}",
    "template":"html"
}
response = requests.post(url = send_url,headers=headers,params=body)
if response.ok == True:
    print("发送成功")
else:
    print("发送失败")