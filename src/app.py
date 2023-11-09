import gradio as gr
import _thread as thread
import os
import time
import json
import openai
from utils import Ws_Param
from urllib.parse import urlparse
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
import websocket

radio_index = 0
answer = ""
history_list = []
openai.api_key = os.environ.get('OPENAI')

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


def xunfei(message, history):
    global history_list
    print(radio_index)
    if radio_index == 0:
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
    else:
        history_list.append({"role": "user", "content": message})
        response = openai.ChatCompletion.create(
            model = 'gpt-4-1106-preview',
            messages=history_list,
            temperature=0.2,
        )
        response_msg = response.choices[0].message.content
        history_list = history_list + [{"role":'assistant', 'content': response_msg}]
        print(f'Msg: {response_msg}')
        for i in range(len(response_msg)):
            time.sleep(0.05)
            yield response_msg[: i+1]

def change_textbox(choice):
    print(choice)
    global radio_index, history_list
    radio_index = choice
    history_list = []
    return [], []
    
with gr.Blocks().queue() as demo:
        with gr.Row():
            with gr.Column(scale=1):
                radio = gr.Radio(value="Xunfei", choices=["Xunfei", "ChatGPT"], type="index", label="请选择大模型服务", info="Which model?")
            with gr.Column(scale=4):
                uu = gr.ChatInterface(xunfei).queue()
        radio.change(fn=change_textbox, inputs=radio, outputs=[uu.chatbot, uu.chatbot_state])
        
    
if __name__ == "__main__":
    demo.launch(share="False", server_name = '0.0.0.0', server_port=8888)