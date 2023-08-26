# xf-bot

## A ChatBot UI for Xunfei Spark Model API using the Gradio library and websocket


### How to use (standalone)

1. Apply for APPID and other stuff on xunfei official website https://xinghuo.xfyun.cn/

2. Fulfill the placeholders for APPID and other stuff in app.py

3. Start the service and have fun:
```
python xf-bot/src/app.py
```


### How to use (kubernetes)

1. Apply for APPID and other stuff on xunfei official website https://xinghuo.xfyun.cn/

2. Fulfill the placeholders for APPID and other stuff in Dockerfile or k8s configMap

3. Create and config both deployment.yaml and service.yaml 

4. Start the service with kubectl and have fun!

