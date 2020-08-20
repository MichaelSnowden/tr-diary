import json
import typing
import uuid

from flask import Flask, render_template
from flask_sockets import Sockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket.websocket import WebSocket

app = Flask(__name__)
sockets = Sockets(app)


class Page:
    def __init__(self, page_id):
        self.page_id = page_id
        self.sockets: typing.List[WebSocket] = []

    def add(self, socket):
        self.sockets.append(socket)

    def remove(self, socket):
        print("socket removed")
        self.sockets.remove(socket)

    def send(self, source, message):
        good_sockets = []
        for socket in self.sockets:
            if socket != source:
                try:
                    socket.send(message)
                except WebSocket as e:
                    print("failed to send message on websocket {}".format(e))
                    socket.close(message="something went wrong {}".format(e))
                    continue
            good_sockets.append(socket)
        self.sockets = good_sockets


pages = {
}


@sockets.route('/socket/<page_id>')
def page_socket(socket: WebSocket, page_id):
    try:
        page = pages[page_id]
    except KeyError:
        socket.close(message="page {} does not exist".format(page_id))
        return
    socket.send(json.dumps({"type": "num_peers", "num_peers": len(page.sockets)}))
    page.add(socket)
    print("num sockets", len(page.sockets))
    while not socket.closed:
        message = socket.receive()
        if message is None:
            continue
        page.send(socket, message)

    page.remove(socket)


@app.route('/')
@app.route('/<page_id>')
def page_view(page_id=None):
    if page_id is None:
        page_id = "default"
    if page_id not in pages:
        pages[page_id] = Page(page_id)
    page = pages[page_id]
    return render_template("index.html", page_id=page_id, my_id=str(uuid.uuid1()))


if __name__ == '__main__':
    pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler).serve_forever()
