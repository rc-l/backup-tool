"""
Backup tool for windows
"""

#TODO: backup root directory through cli parameter
#TODO: logging to screen to show progress of script
#TODO: backup integrity check based on hash sums
#TODO: cleanup mode to remove files from backup that do not exist in origin

import logging
import os
import socket
from shutil import copy2


### LOGGING ###
logger = logging.getLogger("screenlog")
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('{message}', style='{')
ch.setFormatter(formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)

create_log_msg = lambda file, status: "{file:{width}}{status}".format(file=file, status=status, width=os.get_terminal_size()[0]-len(status)-2)

### FUNCTIONS ###
make_backuppath = lambda x: os.path.join(backupdir, x.replace(":", "", 1))

def backup(origin):
    """
    Put file or folder on the backup medium
    """
    assert type(origin) is str
    backuppath = make_backuppath(origin)
    if os.path.isdir(origin):
        if not os.path.isdir(backuppath):
            logging.info(origin, "ADD")
            os.makedirs(backuppath)
    else:
        if os.path.isfile(backuppath):
            if os.path.getmtime(backuppath) >= os.path.getmtime(origin):
                logger.debug(create_log_msg(origin, "SKIP"))
                return
            else:
                logger.warning(create_log_msg(origin, "UPDATE"))
        else:
            logger.warning(create_log_msg(origin, "ADD"))
        #copy2(origin, backuppath)

### MAIN PROCESS ###
backupdrive = "H"
backupdir = os.path.join(f"{backupdrive}:", "backup_" + socket.gethostname())

if not os.path.isdir(backupdir):
    os.mkdir(backupdir)

with open(os.path.join(os.path.abspath(os.curdir), 'paths.txt'), 'r') as f:
    paths = f.read().splitlines()

for path in paths:
    backup(path)
    for file in os.listdir(path):
        originpath = os.path.join(path, file)
        if os.path.isdir(originpath) and originpath not in paths:
            paths.append(originpath)
            backup(originpath)
        elif os.path.isfile(originpath):
            backup(originpath)