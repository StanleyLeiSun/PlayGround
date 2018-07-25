# -*- coding: utf-8 -*-

import time
import sys
import urllib.request

i = 1
heartbeaturl = 'http://127.0.0.1/heartbeat'
while True:
    print (i)
    i += 1
    urllib.request.urlopen(heartbeaturl).read()
    time.sleep(60*5)
