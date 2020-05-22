#
# Script to loop rebooting the device over serial connection indefinitely,
# keeping count of successful reboots (be able to login and get to command
# prompt after reboot)
#
# exit with Crtl-c
#

import sys
import logging
from DeviceSerial import DeviceSerial
from Config import Config
from utils import *

# designate logging LEVEL
LOG_LEVEL = logging.INFO
logging.basicConfig(level=LOG_LEVEL)

# only going to use login/pw, which should be the same for all devices, and serial port
DEVICE='ERIC'
CONFIG_FILE = DEVICE + '.INI'
# get config info
configs = Config(CONFIG_FILE)

# serial connection
deviceSerial = DeviceSerial(configs[Config.SERIAL_PORT])
if not deviceSerial.login(configs[Config.USER], configs[Config.PASSWORD]):
    logging.error("Unable to log in to device over serial connection")
    exit(-1)

def output_nonempty() -> bool:
    '''
    small function retrieving and checking serial output buffer
    (from device)
    primarily meant to be used for poll_wait_while_true() call
    '''
    outputList = deviceSerial.decoded_output()
    list(map(logging.info, outputList))
    return len(outputList) > 0


######################################################################
#
# main() entry point
#
######################################################################
def main():
    rebootCounter = 0
    # loop rebooting until end condition
    while True:
        deviceSerial.enterString('reboot')
        poll_wait_while_true(output_nonempty)
        if deviceSerial.login(configs[Config.USER], configs[Config.PASSWORD]):
            rebootCounter += 1
            logging.info(f'Successful reboot: {rebootCounter}')
        else:
            logging.error('Login failed after 2 attempts! Reboot may have failed (device froze?)...')
            sys.exit(1)
        print("Sleeping 10s before next reboot, hit Ctrl-c to quit")
        time.sleep(10)

if __name__ == '__main__':
    main()
