#-*- coding: utf-8 -*-
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def index():
	return "this is relay server"

@app.route("/relay", methods=["POST"])
def relay():
    param = request.json
    if "mode" in param:
        mode = param["mode"]

        if mode == "sendmsg":
            sendto = param["sendto"]
            sendfrom = param["sendfrom"]
            msg = param["msg"]

            return "aa"
    else:
        return "[relay server] mode parameter doesn't exist"


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=9091, debug=True)
    except Exception as ex:
        print(ex)