# SLAG - CTCL 2024
# File: app.py
# Purpose: Functions used by the bot, similar to lib.rs 
# Created: January 25, 2024
# Modified: January 29, 2024

import csv
import logging
import os
import math
from datetime import datetime

formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
logging.basicConfig(filemode="a", format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s", datefmt="%H:%M:%S", level=logging.DEBUG)

def logger_setup(name, log_file, level=logging.INFO):
    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

def logger_resetup(logger, log_file, level=logging.INFO):
    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)
    
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

def kb2hsize(size_bytes):
    size_bytes = int(size_bytes)

    if size_bytes == 0:
       return "0 KB"
    size_name = ("KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

def _slicegen(maxchars, stringlist):
    runningcount = 0
    tmpslice = []
    for i, item in enumerate(stringlist):
        runningcount += len(item)
        if runningcount <= int(maxchars):
            tmpslice.append(i)
        else:
            yield tmpslice
            tmpslice = [i]
            runningcount = len(item)
        
    yield(tmpslice)

def msgsplit(maxchars, stringlist):

    slices = list(_slicegen(maxchars, stringlist))
    splitmsg = []

    for slicelist in slices:
        tmp = ""
        for stringslice in slicelist:
            
            tmp += stringlist[stringslice] + "\n"

        splitmsg.append(tmp)

    return splitmsg
    
    