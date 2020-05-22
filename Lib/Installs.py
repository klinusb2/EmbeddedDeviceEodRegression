
import sys
import logging
from Lib.DeviceSerial import DeviceSerial
from Lib.DeviceSSH import DeviceSSH
from Lib.Config import Config
from Lib.DeoWebSocket import DeoWebSocket
from utils import *

def updateDevice(deviceSerial: DeviceSerial, deviceSSH: DeviceSSH, updateDevicePath:str, postProcessFunctions:list = []):
    '''
    Function to perform an updateDevice
    Inputs:
    * deviceSerial
    * deviceSSH
    * updateDevicePath - full path/name to updateDevice file
    * [Optional] postProcessFunctions - list of functions to be executed after install
                    each function should take no argument and return bool indicating whether any changes were made

    '''

    remotePath = Config.DEVICE_UPDATE_PATH
    logging.debug(f'Uploading {updateDevicePath} to {remotePath}')
    deviceSSH.removeRemoteFile(remotePath) # make sure no existing file there
    deviceSSH.upload_file(updateDevicePath, remotePath)

    # upload done, first reboot, deviceSSH will lose connection
    logging.info('Uploading done, proceed to 1st reboot')
    # first reboot won't see any IP addresses assigned
    deviceSerial.reboot(True, False)
    # wait for update device process to start, up to a minute and half
    poll_wait_until(deviceSerial.get_output_contains_function('Reboot when ready'), 90)

    [x() for x in postProcessFunctions]
    # 2nd reboot, we expect IP addresses now
    deviceSerial.reboot()

def menderInstall(deviceSerial: DeviceSerial, deviceSSH: DeviceSSH, menderPath:str, postProcessFunctions:list = []):
    '''
    Function to perform a mender install
    * deviceSerial
    * deviceSSH
    * menderPath - full path/name to mender file
    * [Optional] postProcessFunctions - list of functions to be executed after install
                    each function should take no argument and return bool indicating whether any changes were made
    '''

    # upload device.mender
    remotePath = Config.DEVICE_MENDER_PATH
    logging.debug(f'Uploading {menderPath} to {remotePath}')
    deviceSSH.removeRemoteFile(remotePath) # make sure no existing file there
    deviceSSH.upload_file(menderPath, remotePath)

    # upload done, start request mender script
    logging.info('Uploading done, start mender install')
    deviceSerial.enterString('/usr/local/sbin/requestMenderUpdate.sh')

    # first wait until message of Mender succeeded, before reboot
    waitForMenderSucceeded = 36000
    if not poll_wait_until(deviceSerial.get_output_contains_function('menderCommonPostInstall'), waitForMenderSucceeded):
        logging.error(f'Failed to get to Mender succeeded message after {waitForMenderSucceeded}s')
        sys.exit(1)
    # second message comes after a reboot
    waitForMenderCommit = 150
    if not poll_wait_until(deviceSerial.get_output_contains_function('Mender commit succeeded'), waitForMenderCommit):
        logging.warn(f'Failed to get to Mender commit message after {waitForMenderCommit}s')
        logging.warn('Unable to verify Mender commit')
    # should be ready for login at this point
    if not deviceSerial.login():
        logging.error('Login failed after 2 attempts!')
        sys.exit(1)

    if any([x() for x in postProcessFunctions]):
        # 2nd reboot for post processing to take effect, and make sure partition switch stuck
        deviceSerial.reboot()

