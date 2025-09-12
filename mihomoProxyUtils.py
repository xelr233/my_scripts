import httpx
import json

class ProxyUtils:
    session = httpx.Client(http2=True)

    def __init__(self, proxyhost, proxy_auth, panel_public_key):
        self.proxyurl = f"http://{proxyhost}"
        self.proxy_auth = proxy_auth
        self.panel_public_key = panel_public_key
        self.__headers__ = {
            "Host": proxyhost,
            "Connection": "keep-alive",
            "Accept": "application/json",
            "Content-Type": "text/plain;charset=UTF-8",
            "DNT": "1",
            "authorization": f"Bearer {proxy_auth}",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; RMX3800) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36",
            "Referer": f"{self.proxyurl}/ui/",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }
        cookies = {
            "panel_public_key": self.panel_public_key
        }
        self.session.headers.update(self.__headers__)
        self.session.cookies.update(cookies)

    def connectPanel(self):
        url = self.proxyurl + "/version"
        response = self.session.get(url)
        if response.status_code != 200:  # 尝试连接面板
            raise Exception("连接面板失败")
        elif response.json().get("meta") == False:
            raise Exception("面板未启用")
        return response.json().get("version")

    def changeToLoadBalance(self):
        url = self.proxyurl + "/proxies/GLOBAL"
        data = {
            "name": "负载均衡"
        }
        data = json.dumps(data, separators=(',', ':'))
        response = self.session.put(url=url, data=data)
        if response.status_code != 204:
            raise Exception("切换到负载均衡失败")
            return False
        return True

    def changeToDirect(self):
        url = self.proxyurl + "/proxies/GLOBAL"
        data = {
            "name": "DIRECT"
        }
        data = json.dumps(data, separators=(',', ':'))
        response = self.session.put(url=url, data=data)
        if response.status_code != 204:
            raise Exception("切换到直连失败")
            return False
        
    def changeToProxy(self,proxystiename):
        url = self.proxyurl + "/proxies/GLOBAL"
        data = {
            "name": proxystiename
        }
        data = json.dumps(data, separators=(',', ':'))
        response = self.session.put(url=url, data=data)
        if response.status_code != 204:
            raise Exception("切换到代理失败")
            return False
        
    def getProxies(self):
        url = self.proxyurl + "/providers/proxies"
        response = self.session.get(url=url)
        try:
            data = response.json().get("providers",{}).get("default",{}).get("proxies",[])
            return data
        except Exception as e:
            raise Exception(f"解析数据失败，错误信息：{e}")
            return None
    def getProxiesNames(self):
        data = self.getProxies()
        ProxyNames = list(map(lambda x: x.get("name"), data))
        return ProxyNames


