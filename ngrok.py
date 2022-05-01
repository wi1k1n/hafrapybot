import subprocess, os, signal, requests, socket, urllib.parse
import time

from config_options import *
from util.os_utils import *

g_Process: subprocess.Popen = None
g_alreadyRunning: bool = False

def _requestNgrokTunnels(ngrokKey: str) -> object:
    url = 'https://api.ngrok.com/tunnels'
    headers = {
        'Authorization': 'Bearer {}'.format(ngrokKey),
        'Ngrok-Version': '2'
    }
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return None
    return r.json()

def IsNgrokTunnelsEmpty(ngrokKey: str) -> bool:
    response = _requestNgrokTunnels(ngrokKey)
    if not response\
        or not ('tunnels' in response)\
        or not isinstance(response['tunnels'], list):
        return None
    return not len([t for t in response['tunnels'] if ('metadata' in t and t['metadata'] == 'homeassistant')])

def GetNgrokLink(ngrokKey: str) -> str:
    response = _requestNgrokTunnels(ngrokKey)
    if not response\
        or not ('tunnels' in response)\
        or not isinstance(response['tunnels'], list) \
        or not len(response['tunnels'])\
        or not isinstance(response['tunnels'][0], dict)\
        or not ('metadata' in response['tunnels'][0])\
        or not isinstance(response['tunnels'][0]['metadata'], str)\
        or not response['tunnels'][0]['metadata'] == 'homeassistant'\
        or not ('public_url' in response['tunnels'][0])\
        or not isinstance(response['tunnels'][0]['public_url'], str):
        return ''
    addr = response['tunnels'][0]['public_url']
    try:
        parsed_url = urllib.parse.urlparse(addr)
    except:
        return ''
    return addr
    # return addr + ' (' + socket.gethostbyname(parsed_url.netloc) + ')'

def RunCommand(cmd: str) -> bool:
    try:
        subprocess.run(cmd, shell=True)
    except:
        return False
    return True

def RunNgrok(cmdList: list[str], ngrokKey: str) -> bool:
    global g_Process, g_alreadyRunning

    if g_alreadyRunning:
        if not StopNgrok(ngrokKey):
            return False
    try:
        g_Process = subprocess.Popen(cmdList, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, preexec_fn=os.setsid if Linux() else None)
        g_alreadyRunning = True
    except:
        g_alreadyRunning = False

    return g_alreadyRunning

def StopNgrok(ngrokKey: str) -> bool:
    global g_Process, g_alreadyRunning

    if not g_Process:
        g_alreadyRunning = False
        return True

    try:
        g_Process.send_signal(signal.SIGTERM)
    except:
        return False

    # Just to double check
    try:
        time.sleep(0.1)
        os.killpg(os.getpgid(g_Process.pid), signal.SIGTERM)
    except:
        pass

    # TODO: check with searching for pid

    responseAPI = IsNgrokTunnelsEmpty(ngrokKey)
    g_alreadyRunning = True if responseAPI is None else not responseAPI
    return not g_alreadyRunning
