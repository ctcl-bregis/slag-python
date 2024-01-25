# SLAG - CTCL 2024
# File: app.py
# Purpose: Functions used by the bot, similar to lib.rs 
# Created: January 25, 2024
# Modified: January 25, 2024

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

# Reused code from ctclsite-python
def csv_log(data, header, filename):
    # print(list(data.keys()))
    # print(log_header[1:])

    validated_data = {}
    # Convert everything to a string and replace any strings that are too long
    for key, value in data.items():
        if len(str(value)) < 16384:
            validated_data[key] = str(value)
        else:
            validated_data[key] = f"!! {key} too long !!"

    # This is probably very inefficient
    if not os.path.exists(filename):
        with open(filename, "w", encoding='UTF8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames = header)
            writer.writeheader()

    # Timestamp is separate from the sent data
    now = datetime.now()
    timestr = now.strftime("%Y-%b-%d-%k-%M-%S").lower()
    validated_data["time"] = timestr

    # TODO: Speed this up?
    #count = 0
    #with open(log_latest, "r") as f:
    #    for count, line in enumerate(f):
    #        pass

    # If the log is currently too long, back it up
    #if count > log_max_length:
    #    arc_name = f"{log_dir}log_{timestr}"

        # Rename current log file before adding it to the archive
        #os.rename(log_latest, f"{arc_name}.csv")

        # Create tar file with gzip compression
        #tar = tarfile.open(f"{arc_name}.tar.gz", "w:gz", compresslevel=9)
        #tar.add(f"{arc_name}.csv")
        #tar.close()

        # Remove the old log file
        #os.remove(f"{arc_name}.csv")

        # Create another current log file
        #with open(log_latest, "w", encoding='UTF8', newline='') as f:
        #    writer = csv.writer(f)
        #    writer.writerow(log_header)

    if not os.path.exists(filename):
        writer = csv.DictWrtier(f, fieldnames = header)
        writer.writeheader()

    with open(filename, "a") as f:
        writer = csv.DictWriter(f, fieldnames = header)
        writer.writerow(validated_data)

def kb2hsize(size_bytes):
    size_bytes = int(size_bytes)

    if size_bytes == 0:
       return "0 KB"
    size_name = ("KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])