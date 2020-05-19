import xarray as xr
import numpy as np
import os
import sys
import pandas as pd
from urllib.request import urlopen #python3
import json
import glob
import argparse
import logging
import time
import pdb

logger = logging.getLogger()
logging.basicConfig(level = logging.INFO)
parser = argparse.ArgumentParser(description='Check tiles for errors.')
parser.add_argument("newpath", help="Path to new tiles.")

args = parser.parse_args()
newloc = args.newpath
error_found = False
alltiles = glob.glob(os.path.join(newloc, "*.nc"))

def log_tile_errs(msg, filename):
    logger.error("{} {}".format(msg, filename))

# pdb.set_trace()

for tile in alltiles:
    logger.info(tile)
    try:
        ds_new = xr.open_dataset(tile)
    except Exception as e:
        logger.error("Problem opening {}: {}".format(oldfile, str(e)))
        error_found = True
        continue

    t1 = ds_new.time
    # round by adding 500ms then truncating the subseconds
    t1round = (t1 + np.timedelta64(500, 'ms')).astype('datetime64[s]')

    t_first = pd.Timestamp(t1round[0].values, tz='UTC')
    t_last = pd.Timestamp(t1round[-1].values, tz='UTC')
    
    logger.info("Time span: {} to {}".format(t_first, t_last))

    # are there repeat timestamps?
    if len(np.unique(t1round)) != len(t1round):
        log_tile_errs("Possible repeat timestamps in new tile.", tile)
        error_found = True
    else:
        logger.info("OK: no repeat timestamps")

    # are times strictly increasing?
    if np.any(np.diff(t1.astype(int), 1)<0):
        log_tile_errs("Times not strictly increasing in new tile.", tile)
        error_found = True
    else:
        logger.info("OK: times strictly increasing")
    
    # take time differences, round and look for unique values - should only be one - 3600 sec
    if len(np.unique(np.diff(t1round, 1).astype(int)/1.0e9)) != 1:
        log_tile_errs("Time dimension not all hourly.", tile)
        error_found = True
    else:
        logger.info("OK: all time steps are 1 hour")

    ds_new.close()

# this allows us to return status to bash shell
exit(error_found)
