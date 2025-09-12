import httpx
class pushme:
    url = 'https://push.i-i.me'

    def __init__(self,push_key) -> None:
        self.push_key = push_key

    def sendNotify(self,title,content):
        data = {
            "push_key": self.push_key,
            "title": title,
            "content": content,
            "type":'text'
        }
        with httpx.Client(http2=True) as client:
            response = client.post(self.url, data=data)
            if response.status_code == 200:
                return True
        
        return False


