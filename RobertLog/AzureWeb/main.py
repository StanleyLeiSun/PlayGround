from flask import Flask
app = Flask(__name__)

from weixinInterface import WeixinInterface
weixin = WeixinInterface()

@app.route('/')
def hello_world():
  return 'Hello, World!'

@app.route('/weixin', methods=['GET'])
def weixin_get():
  return weixin.GET()

@app.route('/weixin', methods=['POST'])
def weixin_post():
  return weixin.POST()

if __name__ == '__main__':
  app.run()
