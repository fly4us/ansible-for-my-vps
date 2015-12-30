#!/usr/bin/env python
# -*- coding:utf-8 -*-
import hashlib, urllib, urllib2, re, time, json, os
import xml.etree.ElementTree as ET
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename


app_root_path = "{{ web_app_path }}"
app_token = "{{ app_token }}"
app_port = {{ app_port }}

app = Flask(__name__)
app.debug = False
app.secret_key = "{{ app_secret_key }}"


@app.route('/wxapp', methods=['GET'])
def weixin_access_verify():
    echostr = request.args.get('echostr')
    if verification(request) and echostr is not None:
        return echostr
    return 'access verification fail'


@app.route('/wxapp', methods=['POST'])
def weixin_msg():
    if verification(request):
        data = request.data
        msg = parse_msg(data)

        if user_subscribe_event(msg):
            return help_info(msg)
        elif is_text_msg(msg):
            content = msg['Content']
            if content == u'?':
                return help_info(msg)

            if content == u'!rp':
                return plans_info(msg)

            if content == u'!fh':
                return fhplans_info(msg)

            rmsg = response_text_msg(msg, content)
            return rmsg

    return 'message processing fail'


@app.route('/plans', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app_root_path, filename))
            return 'S'
    return 'E'


def verification(request):
    try:
        signature = request.args.get('signature')
        timestamp = request.args.get('timestamp')
        nonce = request.args.get('nonce')

        token = app_token
        tmplist = [token, timestamp, nonce]
        tmplist.sort()
        tmpstr = ''.join(tmplist)
        hashstr = hashlib.sha1(tmpstr).hexdigest()

        if hashstr == signature:
            return True
    except:
        pass
    return False


def allowed_file(filename):
    return filename == 'plans.txt' or filename == 'fhplans.txt'


def parse_msg(rawmsgstr):
    root = ET.fromstring(rawmsgstr)
    msg = {}
    for child in root:
        msg[child.tag] = child.text
    return msg


def is_text_msg(msg):
    return msg['MsgType'] == 'text'


def user_subscribe_event(msg):
    return msg['MsgType'] == 'event' and msg['Event'] == 'subscribe'


HELP_INFO = \
u"""
欢迎关注自助系统^_^
请直接发送相关指令
"""

def help_info(msg):
    return response_text_msg(msg, HELP_INFO)


def plans_info(msg):
    info = "FETCH FAILED!"

    try:
        file = open(app_root_path + "plans.txt", "r")
        lines = file.readlines()
        info = " ".join(lines)
    finally:
        file.close()

    return response_text_msg(msg, info[:2000])


def fhplans_info(msg):
    info = "FETCH FAILED!"

    try:
        file = open(app_root_path + "fhplans.txt", "r")
        lines = file.readlines()
        info = " ".join(lines)
    finally:
        file.close()

    return response_text_msg(msg, info[:2000])


TEXT_MSG_TPL = \
u"""
<xml>
<ToUserName><![CDATA[%s]]></ToUserName>
<FromUserName><![CDATA[%s]]></FromUserName>
<CreateTime>%s</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[%s]]></Content>
<FuncFlag>0</FuncFlag>
</xml>
"""

def response_text_msg(msg, content):
    s = TEXT_MSG_TPL % (
            msg['FromUserName'],
            msg['ToUserName'],
            str(int(time.time())),
            content
        )
    return s


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=app_port)
