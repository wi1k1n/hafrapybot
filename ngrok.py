import subprocess, os, signal, requests, socket, urllib.parse
from config_options import *
from util.os_utils import *

g_Process: subprocess.Popen = None

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

def RunAdditionalCommand(cmd: ConfigOptionType, link: str):
    try:
        subprocess.run(repr(cmd).format(link), shell=True)
    except:
        return False
    return True

def RunNgrok(cmdList, timeout):
    global g_Process

    # TODO: if windows/linux
    try:
        if Windows():
            g_Process = subprocess.Popen(cmdList, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        elif Linux():
            g_Process = subprocess.Popen(cmdList, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, preexec_fn=os.setsid)
    except:
        return False

    return True

def StopNgrok(ngrokKey: str):
    global g_Process

    if not g_Process:
        return True

    try:
        g_Process.send_signal(signal.SIGTERM)
        os.killpg(os.getpgid(g_Process.pid), signal.SIGTERM)
    except:
        pass

    # TODO: check with searching for pid

    return IsNgrokTunnelsEmpty(ngrokKey)
