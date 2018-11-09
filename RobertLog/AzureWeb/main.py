#coding=utf-8
from flask import Flask
from weixinInterface import WeixinInterface
#import testfunc
import config
import flask
import reporting
import logging
import logging.config
import time

app = Flask(__name__)
weixin = WeixinInterface()

heartbeatcount = 0

log_filename = "robertlogging.log"
logging.basicConfig(level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename = log_filename,
    filemode='a')

@app.route('/heartbeat')
def hello_world():
    global heartbeatcount
    heartbeatcount += 1
    return 'Hello, the {0} times.'.format(heartbeatcount)

@app.route('/weixin', methods=['GET'])
def weixin_get():
    return weixin.callback_get()

@app.route('/weixin', methods=['POST'])
def weixin_post():
    return weixin.callback_post()

@app.route('/robert_image', methods=['GET'])
def get_image():
    name = flask.request.args.get('name')
    file_name = config.ImageRoot + name
    return flask.send_file(file_name, mimetype='image/jpeg')

if __name__ == '__main__':
    #reporting.chart_for_last_days(90)
    app.run(host="0.0.0.0", port=80)
    pass