import os
import signal
import subprocess
import time
import requests
import sys
import atexit

cmd = 'gunicorn --bind=0.0.0.0:42069 --chdir=/home/mac/MinigameDungeonServer/MinigameDungeonServer server:app'

pro = None

TIME_DELAY = 5

def start_server():
    global pro
    if not pro:
        pro = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr, shell=True, preexec_fn=os.setsid)

def kill_server():
    global pro
    if pro:
        os.killpg(os.getpgid(pro.pid), signal.SIGKILL)
        pro = None

# kill server on exit
atexit.register(kill_server)

# start server initially
start_server()

while True:
    time.sleep(TIME_DELAY)
    # check if server is up
    print('Checking server status...')
    c = None
    try:
        c = requests.get('http://minecraft.scrollingnumbers.com:42069')
    except requests.exceptions.RequestException:
        pass
    if not c or c.status_code != 200:
        # if server is down, restart it
        print('Server is down, restarting server...')
        kill_server()
        time.sleep(TIME_DELAY)
        start_server()
    else:
        print('Server is up and running.')

