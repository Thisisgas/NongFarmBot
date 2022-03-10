#!/usr/bin/python
#-*-coding: utf-8 -*-
##from __future__ import absolute_import
###
from flask import Flask, jsonify, render_template, request
import json
import numpy as np
import time
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,TemplateSendMessage,ImageSendMessage, StickerSendMessage, AudioSendMessage
)
from linebot.models.template import *
from linebot import (
    LineBotApi, WebhookHandler
)

import pika, os

app = Flask(__name__)

lineaccesstoken = 'qO8wBr70W/QMoC8SOVxEJP9d96Celz5OhpLAB/s/0Sez9mtNc3hOunsuTlYeDgtQbgTQwox0NnGB0Y+iV1GQDFD6YHTHxrgs8qJrEufc3q08wBTxEuWXWcOOe0e/nSKaAwGB8uFbPE6fdEFLbc9wjAdB04t89/1O/w1cDnyilFU='
line_bot_api = LineBotApi(lineaccesstoken)

####################### new ########################
@app.route('/')
def index():
    return "Hello World!"


@app.route('/webhook', methods=['POST'])
def callback():
    json_line = request.get_json(force=False,cache=False)
    json_line = json.dumps(json_line)
    decoded = json.loads(json_line)
    no_event = len(decoded['events'])
    for i in range(no_event):
        event = decoded['events'][i]
        event_handle(event)
    return '',200


def event_handle(event):
    print(event)
    url = os.environ.get('CLOUDAMQP_URL', 'amqps://hglnowqe:5jS2oETw_Hcny6yhsPee8xuN6L9EQU7w@baboon.rmq.cloudamqp.com/hglnowqe')
    params = pika.URLParameters(url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel() # start a channel
    channel.queue_declare(queue='/hello') # Declare a queue

    channel.queue_declare(queue='/sensors') # Declare a queue
    channel.queue_bind(
        exchange='amq.topic', queue='/sensors', routing_key='Sensor')

    try:
        userId = event['source']['userId']
    except:
        print('error cannot get userId')
        return ''

    try:
        rtoken = event['replyToken']
    except:
        print('error cannot get rtoken')
        return ''
    try:
        msgId = event["message"]["id"]
        msgType = event["message"]["type"]
    except:
        print('error cannot get msgID, and msgType')
        sk_id = np.random.randint(1,17)
        replyObj = StickerSendMessage(package_id=str(1),sticker_id=str(sk_id))
        line_bot_api.reply_message(rtoken, replyObj)
        return ''
    def callback2(ch, method, properties, body):
        replyObj = TextSendMessage(text=body.decode("utf-8", "ignore"))
        line_bot_api.reply_message(rtoken, replyObj)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    if msgType == "text":
        msg = str(event["message"]["text"])
        if msg=="สภาพอากาศ" or msg == "ความชื้นในดิน" or msg == "ความเข้มแสง":
            channel.basic_publish(exchange='amq.topic',
                      routing_key='hello',
                      body=msg)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue='/sensors', on_message_callback=callback2, auto_ack=True)
            channel.start_consuming()
        else :
            replyObj = TextSendMessage(text=msg)
            line_bot_api.reply_message(rtoken, replyObj)
            channel.basic_publish(exchange='amq.topic',
                      routing_key='hello',
                      body=msg)
        connection.close()
    else:
        sk_id = np.random.randint(1,17)
        replyObj = StickerSendMessage(package_id=str(1),sticker_id=str(sk_id))
        line_bot_api.reply_message(rtoken, replyObj)
        channel.basic_publish(exchange='amq.topic',
                      routing_key='hello',
                      body='sticker')
        connection.close()
    return ''

if __name__ == '__main__':
    app.run(debug=True)
