# License : GPLv2.0
# copyright (c) 2023  Dave Bailey
# Author: Dave Bailey (dbisu, @daveisu)
# FeatherS2 board support

import socketpool
import time
import os
import storage

import wsgiserver as server
from adafruit_wsgi.wsgi_app import WSGIApp
import wifi

from duckyinpython import *

notepad_content = ""

payload_html = """<!DOCTYPE html>
<html>
<head>
    <title>Payload</title>
</head>
<body>
    <form method="POST" action="/Run/">
        <textarea rows="30" cols="58.5" name="scriptData" required>{}</textarea>
        <br><br>
        <button style="width: 150px; height: 50px;" type="submit">Run</button>
    </form>
</body>
</html>
"""

def ducky_main(request):

    response = payload_html.format(notepad_content)

    return(response)

_hexdig = '0123456789ABCDEFabcdef'
_hextobyte = None

def cleanup_text(string):
    """unquote('abc%20def') -> b'abc def'."""
    global _hextobyte

    if not string:
        return b''

    if isinstance(string, str):
        string = string.encode('utf-8')

    bits = string.split(b'%')
    if len(bits) == 1:
        return string

    res = [bits[0]]
    append = res.append

    if _hextobyte is None:
        _hextobyte = {(a + b).encode(): bytes([int(a + b, 16)])
                      for a in _hexdig for b in _hexdig}

    for item in bits[1:]:
        try:
            append(_hextobyte[item[:2]])
            append(item[2:])
        except KeyError:
            append(b'%')
            append(item)

    return b''.join(res).decode().replace('+',' ')

web_app = WSGIApp()

@web_app.route("/")
def index(request):
    response = ducky_main(request)
    return("200 OK", [('Content-Type', 'text/html')], response)

@web_app.route("/Run/",methods=["POST"])
def Run(request):
    global notepad_content

    data = request.body.getvalue()
    fields = data.split("&")
    form_data = {}
    for field in fields:
        key,value = field.split('=')
        form_data[key] = value

    #print(form_data)
    textbuffer = form_data['scriptData']
    textbuffer = cleanup_text(textbuffer)
    notepad_content = textbuffer
    previousLine = ""

    lines = textbuffer.split('\n')
    for line in lines:
        line = line.strip()
        if(line[0:6] == "REPEAT"):
            for i in range(int(line[7:])):
                parseLine(previousLine)
                time.sleep(float(defaultDelay)/1000)
        else:
            parseLine(line)
            previousLine = line
            time.sleep(float(defaultDelay)/1000)

    response = ducky_main(request)
    return(f"200 OK", [('Content-Type', 'text/html')], response)

async def startWebService():

    HOST = repr(wifi.radio.ipv4_address_ap)
    PORT = 80        # Port to listen on
    print(HOST,PORT)

    wsgiServer = server.WSGIServer(80, application=web_app)

    print(f"open this IP in your browser: http://{HOST}:{PORT}/")

    # Start the server
    wsgiServer.start()
    while True:
        wsgiServer.update_poll()
        await asyncio.sleep(0)