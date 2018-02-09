#coding=utf-8
from flask import Flask
from weixinInterface import WeixinInterface
import testfunc
import config
import flask

app = Flask(__name__)
weixin = WeixinInterface()

@app.route('/')
def hello_world():
    return 'Hello World'

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
    return flask.send_file(file_name, mimetype='image/gif')

if __name__ == '__main__':
    #app.run()
    app.run(host="0.0.0.0", port=80)
    pass