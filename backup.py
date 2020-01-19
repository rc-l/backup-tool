"""
Backup tool for windows
"""

# TODO: cleanup mode to remove files from backup that do not exist in origin
# TODO: count of integrity check

import logging
import os
import socket
import argparse
import hashlib
from shutil import copy2

### CONSTANTS ###
BUF_SIZE = 1048576  # 1 MB

### ARGUMENT PARSING ###
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('-b', '--backup', action='store_true',
                    help='create backup')
parser.add_argument('-c', '--check', action='store_true',
                    help='check integrity of the backup based on hashes')
parser.add_argument('-v', action='count', default=0, dest='verbosity',
                    help='set the verbosity level of the console output')
parser.add_argument('-q', '--quiet', action='store_true', default=False,
                    help='no console output')
args = parser.parse_args()

# Default to creating backup
if not any(vars(args).values()):
    args.backup = True

### LOGGING ###
log_levels = {
    0: logging.WARNING,
    1: logging.INFO,
    2: logging.DEBUG
}
logger = logging.getLogger("screenlog")
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('{message}', style='{')
ch.setFormatter(formatter)
if args.verbosity > 2:
    args.verbosity = 2
logger.setLevel(log_levels[args.verbosity])
logger.addHandler(ch)
logger.disabled = args.quiet

create_log_msg = lambda file, status: "{file:{width}}{status}".format(file=file, status=status, width=os.get_terminal_size()[0]-len(status)-2)

### FUNCTIONS ###
make_backuppath = lambda x: os.path.join(backupdir, x.replace(":", "", 1))

def backup(origin):
    """
    Put file or folder on the backup medium
    """
    assert type(origin) is str
    # Exit if not running in backup mode. Put it here since this is the most generic place.
    if not args.backup:
        return
    
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

def check_integrity(origin):
    """
    Check the hash of the origin file and the destination file.
    """
    # Check if the file exists
    backuppath = make_backuppath(origin)
    if not os.path.isfile(backuppath):
        logger.warning(create_log_msg(backuppath, "MISSING"))
    else:
        backuphash = hashlib.sha1()
        with open(backuppath, 'rb') as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                backuphash.update(data)    

        originhash = hashlib.sha1()
        with open(origin, 'rb') as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                originhash.update(data)
        if backuphash.hexdigest() == originhash.hexdigest():
            logger.info(create_log_msg(backuppath, "OK"))
        else:
            logger.error(create_log_msg(backuppath, "CORRUPTED"))

### MAIN PROCESS ###
backupdrive = "H"
backupdir = os.path.join(f"{backupdrive}:", "backup_" + socket.gethostname())

if not os.path.isdir(backupdir):
    os.mkdir(backupdir)

with open(os.path.join(os.path.abspath(os.curdir), 'paths.txt'), 'r') as f:
    paths = f.read().splitlines()

# Backup
for path in paths:
    backup(path)
    for file in os.listdir(path):
        originpath = os.path.join(path, file)
        if os.path.isdir(originpath) and originpath not in paths:
            paths.append(originpath)
            backup(originpath)
        elif os.path.isfile(originpath):
            backup(originpath)
            check_integrity(originpath)