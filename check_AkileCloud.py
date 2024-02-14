#!/usr/bin/python3
# coding=utf-8
"""
Author: Xe
time: 2024/2/14
cron: 0 25 * * * *
new Env('监控AkileCloud');
"""
import requests
import json
import os
import time
from notify import send
title = os.getenv('TITLE') or '监控_AkileCloud'
url = "https://api.akile.io/api/v1/store/GetVpsStore"
headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"}
counter = 0
is_Get_data_succes = False
need_send_msg = False
check_nodes = []
while counter < 10:
    response = requests.get(url=url,headers=headers)
    if response.ok == True:
        data_json = response.json()
        #stack = response_json['data'][5]['nodes'][-2]['plans'][0]['stock']
        for item in data_json['data']:
            for node in item['nodes']:
                for plan in node['plans']:
                    if plan['price_datas'][0]['price'] < 1700:
                        nodes_price = {
                            'name':plan['plan_name'],
                            'stock':plan['stock'],
                            'price':plan['price_datas'][0]['price'] / 100
                            }
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
    print("暂无更新")
    exit()
msg = ""
for each in difference:
    msg = msg + f"节点类型：{each['name']}🖥️ 价格：{each['price']}💰 数量；{each['stock']}✅\n"
send(title,msg)