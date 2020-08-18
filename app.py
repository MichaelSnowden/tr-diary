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


class Canvas:
    def __init__(self, canvas_id):
        self.canvas_id = canvas_id
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


canvases = {
}


@sockets.route('/socket/<canvas_id>')
def canvas_socket(socket: WebSocket, canvas_id):
    try:
        canvas = canvases[canvas_id]
    except KeyError:
        socket.close(message="canvas {} does not exist".format(canvas_id))
        return
    socket.send(json.dumps({"type": "num_peers", "num_peers": len(canvas.sockets)}))
    canvas.add(socket)
    print("num sockets", len(canvas.sockets))
    while not socket.closed:
        message = socket.receive()
        if message is None:
            continue
        canvas.send(socket, message)

    canvas.remove(socket)


@app.route('/')
@app.route('/<canvas_id>')
def canvas_view(canvas_id=None):
    if canvas_id is None:
        canvas_id = "default"
    if canvas_id not in canvases:
        canvases[canvas_id] = Canvas(canvas_id)
    canvas = canvases[canvas_id]
    return render_template("index.html", canvas_id=canvas_id, my_id=str(uuid.uuid1()))


if __name__ == '__main__':
    pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler).serve_forever()
