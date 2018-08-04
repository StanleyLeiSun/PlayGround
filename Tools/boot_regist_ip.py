import kazoo.client as kc
import socket
import datetime as dt

zk = kc.KazooClient(hosts='zk1.staging.srv:2181 ')
zk.start()

def update():
    zk.ensure_path('/users/stansun')
    zk.ensure_path('/users/stansun/ipmapping')
    zk.ensure_path('/users/stansun/ipmapping/stansun-pc')
    zk.ensure_path('/users/stansun/ipmapping/stansun-pc-lastupdate')

    ip = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]
    print("Set ip to %s"%ip)

    zk.set('/users/stansun/ipmapping/stansun-pc', ip.encode())
    zk.set('/users/stansun/ipmapping/stansun-pc-lastupdate', dt.datetime.now().strftime("%c").encode() )

def get_latest():
    latestip = zk.get('/users/stansun/ipmapping/stansun-pc')
    print(latestip)

if __name__ == '__main__':
    get_latest()