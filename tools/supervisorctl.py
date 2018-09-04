

import subprocess

def restart_beat():
    s = subprocess.check_call('supervisorctl restart celery-beat',shell=True)
    if s == 0:
        return True
    else:
        return False