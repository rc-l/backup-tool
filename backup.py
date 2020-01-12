"""
Backup tool for windows
"""

import os
import socket

make_backuppath = lambda x: os.path.join(backupdir, x.replace(":", "", 1))

def backup(origin):
    """
    Put file or folder on the backup medium
    """
    assert type(origin) is str
    backuppath = make_backuppath(path)
    if os.path.isdir(origin):
        if not os.path.isdir(backuppath):
            os.makedirs(backuppath)
    else:
        

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
            pass