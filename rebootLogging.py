import sys
import logging
import time
import os
import argparse
from DeviceSerial import DeviceSerial

#
# script to simply log output from a boot sequence
#
def main():

    # create logger with current module namespace
    logFile = 'bootup.log'
    LOG_LEVEL = logging.INFO
    logging.basicConfig(level=LOG_LEVEL)

    logger = logging.getLogger()
    fh = logging.FileHandler(logFile)
    fh.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
    fh.setLevel(LOG_LEVEL)
    logger.addHandler(fh)
    logger.info('Log file name: ' + logFile)

    # init serial
    deviceSerial = DeviceSerial('COM8')
    deviceSerial.login()
    #currentDeviceBuildVersion = 'VERSION_' + deviceSerial.get_versions()[0]
    #if len(currentDeviceBuildVersion) == 0:
    #    currentDeviceBuildVersion = "NO_VERSION"

    # start boot sequence
    deviceSerial.reboot(False, False)


if __name__ == '__main__':
    main()