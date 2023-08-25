import gradio as gr
import _thread as thread
import os
import base64
import datetime
import hashlib
import hmac
import time
import json
from urllib.parse import urlparse
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
import websocket
answer = ""
history_list = []

class Ws_Param(object):

    # 初始化
    def __init__(self, APPID, APIKey, APISecret, Spark_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(Spark_url).netloc
        self.path = urlparse(Spark_url).path
        self.Spark_url = Spark_url

      

    # 生成url
    def create_url(self):
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"

        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'

        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        # 拼接鉴权参数，生成url
        url = self.Spark_url + '?' + urlencode(v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        return url


# events on websocket errors ocurred
def on_error(ws, error):
    print("### error:", error)


# events on websocket closed
def on_close(ws,one,two):
    print(" ")


# events on websocket connection
def on_open(ws):
    thread.start_new_thread(run, (ws,))


def run(ws, *args):
    global answer
    answer = ""
    data = json.dumps(gen_params(appid=ws.appid, domain= ws.domain,question=ws.question))
    ws.send(data)


# events on message actions
def on_message(ws, message):
    # print(message)
    data = json.loads(message)
    code = data['header']['code']
    if code != 0:
        print(f'请求错误: {code}, {data}')
        ws.close()
    else:
        choices = data["payload"]["choices"]
        status = choices["status"]
        content = choices["text"][0]["content"]
        print(content,end ="")
        global answer
        answer += content
        print(answer)
        # print(1)
        if status == 2:
            ws.close()


def gen_params(appid, domain,question):
    """
    The input schema of Xunfei Spark LLM API 
    """
    data = {
        "header": {
            "app_id": appid,
            "uid": "1234"
        },
        "parameter": {
            "chat": {
                "domain": domain,
                "random_threshold": 0.5,
                "max_tokens": 2048,
                "auditing": "default"
            }
        },
        "payload": {
            "message": {
                "text": question
            }
        }
    }
    return data


def greet(message, history):
    AppID = os.environ.get('APPID')
    APIKey = os.environ.get('APIKEY')
    APISecret = os.environ.get('APISECRET')
    APIUrl = os.environ.get('APIURL')
    print(f'Appid: {AppID}, Apikey: {APIKey}, ApiSecret: {APISecret}, APIUrl: {APIUrl}')
    wsParam = Ws_Param(AppID, APIKey, APISecret, APIUrl)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
    ws.appid = AppID
    history_list.append({"role": "user", "content": message})
    ws.question = history_list
    ws.domain = "generalv2"

    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    history_list.append({"role": "assistant", "content": answer})
    for i in range(len(answer)):
        time.sleep(0.05)
        yield answer[: i+1]

demo = gr.ChatInterface(greet).queue()
    
if __name__ == "__main__":
    demo.launch(share="True", inbrowser=True, server_name = '0.0.0.0', server_port=8888)