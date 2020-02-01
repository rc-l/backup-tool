"""
Backup tool for windows
"""

# TODO: logging to a file
# TODO: config file with paths to check and paths to ignore
# TODO: delete excluded/ignored paths from backup that still exist on origin
# TODO: count of integrity check
# TODO: take backup drive as parameter when run

import logging
import os
import socket
import argparse
import hashlib
import shutil
import yaml

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
parser.add_argument('-d', '--delete', action='store_true', default=False,
                    help='delete files from backup drive that do not exist on the origin device')
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
def reverse_backuppath(x):
    """Derive the origin path from the backup path.
    Does the reverse of make_backuppath()
    """
    x = x[len(backupdir):]
    if x[0] == "\\":
        x = x[1:]
    if len(x) == 1:
        x += ":\\"
    else:
        x = x.replace("\\", ":\\", 1)
    return x

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
            logger.info(create_log_msg(origin, "ADD"))
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
        shutil.copy2(origin, backuppath)

def check_integrity(origin):
    """
    Check the hash of the origin file and the destination file.
    """
    # Check if integrity needs to be checked
    if not args.check:
        return
    
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

class Config:
    """Class for configuration info"""
    def __init__(self):
        with open(os.path.join(os.path.abspath(os.curdir), 'config.yaml'), 'r') as f:
            self.config = yaml.load(f)

        self.paths = self.config.get('paths', [])
        self.exclude = self.config.get('exclude', [])

### MAIN PROCESS ###
backupdrive = "H"
backupdir = os.path.join(f"{backupdrive}:", "backup_" + socket.gethostname())

if not os.path.isdir(backupdir):
    os.mkdir(backupdir)

config = Config() 
logger.debug(f"Found following paths in file: {config.paths}")

# Backup
if args.backup or args.check:
    for path in paths:
        backup(path)
        try:
            for file in os.listdir(path):
                originpath = os.path.join(path, file)
                if os.path.isdir(originpath) and originpath not in paths and originpath not in config.exclude:
                    paths.append(originpath)
                    backup(originpath)
                elif os.path.isfile(originpath):
                    backup(originpath)
                    check_integrity(originpath)
        except PermissionError:
            logger.error(create_log_msg(path, "NO ACCESS"))
        except Exception as err:
            logging.critical(err)

paths = list(os.path.join(backupdir, x) for x in os.listdir(backupdir))
# Clean up
if args.delete:
    for path in paths:
        if not os.path.exists(reverse_backuppath(path)):
            logger.error(create_log_msg(path, "DELETE"))
            shutil.rmtree(path)
            continue
        for file in os.listdir(path):
            filepath = os.path.join(path, file)
            if os.path.isdir(filepath):
                paths.append(filepath)
            else:
                if not os.path.exists(reverse_backuppath(filepath)):
                    logger.error(create_log_msg(filepath, "DELETE"))
                    os.remove(filepath)

