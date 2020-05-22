import sys
import logging
import time
import os
import argparse
from Lib.DeviceSerial import DeviceSerial
from Lib.DeviceSSH import DeviceSSH
from Lib.Config import Config
from Lib.DeoWebSocket import DeoWebSocket
from Lib.Installs import *
from utils import *

def define_args():

    # parse through commmand line options
    aparser = argparse.ArgumentParser(
            epilog='Script tool to download and install rel/dev build on device, requires serial and ssh access'
        )

    # 1 positional arg specifying device
    aparser.add_argument('device', 
                         help='specify device type: ORION, FINIA, ERIC, CWCE, etc'
                         )

    # specifying rel/dev build options are mutually exclusive
    mgroup = aparser.add_mutually_exclusive_group()

    # installs specified rel (mender) build, no subsequent dev build checked for
    # this is an unconditional mender install, will do it no matter what
    # KYL 05/19/2020: if arg string contains '.mender' it will be interpreted as pointing to a mender file to install
    mgroup.add_argument('-r', '--rel', dest='relBuild', help='specify rel (mender) build to install')

    # installs specified dev build, will check to see if a mender build is required
    # will NOT install if device's current build is newer (warning printed)
    # KYL 05/19/2020: if arg string starts with 'device' it will interpreted as pointing to an updateDevice* file to install
    mgroup.add_argument('-d', '--dev', dest='devBuild', help='specify mender build to install')

    # specify CPA address; do nothing if already set, changing requires a reboot
    aparser.add_argument('-c', '--cpa', dest='cpaIP', help='specify CPA IP address')

    # specify NTP on/off; if not used, nothing is done, if need to change, requires a reboot
    # argument should be a integer representing the desired NTP timeout in seconds,
    # set to 0 or <0 to indicate NTP should be off
    aparser.add_argument('-t', '--ntp', dest='ntpState', help='explicitly specify NTP timeout, set = 0 to indicate NTP off')

    # default is to always try to install test build (device.mender.T<DEVICE>, updateDevice.T<DEVICE>)
    # this option specify normal install
    aparser.add_argument('-n', '--noTestInstall', 
                         dest='noTestInstall', 
                         action='store_true', 
                         help='install regular instead of test build (TORION, TFINIA, etc)')

    aparser.add_argument('-k', '--killSound', 
                         dest='soundKill', 
                         action='store_true', 
                         help='kill SoundPlayer process if present')

    aparser.add_argument('-s', '--serial', dest='serial', help="serial port to connect to device overrides what's in <DEVICE.INI> file")

    return aparser.parse_args()

######################################################################
#
# main() entry point for device update and regression script
#
# exit code:
#   0 - all attempted tasks successfully completed; device up to date
#       with latest found builds
#  -1 - wrong config (*.INI) file for current device
#   1 - mender install attempted and failed
#   2 - updateDevice attempted and failed
#
######################################################################
def main():
    args = define_args()

    # designate logging LEVEL
    LOG_LEVEL = logging.INFO
    logging.basicConfig(level=LOG_LEVEL)
    if args.serial:
        logging.info(f'look for device serial connection on port {args.serial}')

    DEVICE = args.device.upper()
    CONFIG_FILE = DEVICE + '.INI'

    # get config info, root buildoutput path depends on whether private build requested
    configs = Config(CONFIG_FILE)

    # establish serial connection
    if args.serial:
        deviceSerial = DeviceSerial(args.serial)
    else:
        deviceSerial = DeviceSerial(configs[Config.SERIAL_PORT])
    deviceSerial.login(configs[Config.USER], configs[Config.PASSWORD])
    # check device type
    if not deviceSerial.checkDeviceType(configs[Config.DEVICE]):
        logging.error('Wrong device type found, config INI file is expecting {}; using wrong config INI file?'.format( 
                        configs[Config.DEVICE]))
        sys.exit(-1)

    # decide which rel/dev builds we will be working with
    currentDeviceBuildVersion = deviceSerial.get_versions()[0]

    # figure out the exact build file(s) we will be using
    logging.info(f'Device currently on build: {currentDeviceBuildVersion}')
    deviceMenderPath = None
    updateDevicePath = None
    if args.relBuild:
        # unconditionally installing specified rel build, no dev build needed
        # install even if device is already at requested rel build (force switch partition)
        logging.info(f'installing build: {args.relBuild} on device {args.device}')
        if "mender" in args.relBuild:
            # argument contains 'mender' assume it's pointing directly to the mender file
            deviceMenderPath = args.relBuild
            args.relBuild = None
        else:
            deviceMenderPath = configs.get_rel_build_menderUpdate_path(args.relBuild)
        if not os.path.exists(deviceMenderPath):
            # oops the specified rel build doesn't exist
            logging.error('Requested rel build {} does not exist!'.format(deviceMenderPath))
            sys.exit(1)
        logging.info(f'Installing rel build {args.relBuild}')

    elif args.devBuild:
        # Dev build specified (this option is mutually exclusive with rel build option)
        logging.info(f'installing build: {args.devBuild} on device {args.device}')
        if 'update' in args.devBuild:
            # argument contains 'update' assume it's pointing directly to the updateDevice file
            updateDevicePath = args.devBuild
            args.devBuild = None
        else:
            updateDevicePath = configs.get_dev_build_updateDevice_path(args.devBuild)
        if not os.path.exists(updateDevicePath):
            # oops the specified dev build doesn't exist
            logging.warn('Requested dev build {} does not exist!'.format(updateDevicePath))
            sys.exit(1)
        logging.info(f'Installing dev build {args.devBuild}')

    else:
        logging.info('Updating device to latest builds...')
        # no Rel/Dev build specified, installing latest versions
        lastDevBuild = configs.get_latest_dev_build_version()
        lastRelBuild = configs.get_latest_rel_build_version()
        logging.info(f'Lastest rel build: {lastRelBuild}   dev build: {lastDevBuild}')
        # for a private build, install latest Rel and/or Dev builds unconditionally
        if '.' not in currentDeviceBuildVersion or second_build_is_newer(currentDeviceBuildVersion, lastRelBuild):
            # need mender install
            deviceMenderPath = configs.get_rel_build_menderUpdate_path(lastRelBuild)
            logging.info(f'Will install new rel build {lastRelBuild}')
            if second_build_is_newer(lastRelBuild, lastDevBuild):
                # also needs a Dev install following the Rel install
                updateDevicePath = configs.get_dev_build_updateDevice_path(lastDevBuild)
                logging.info(f'Will install new dev build {lastDevBuild}')
        else:
            # no Rel install needed, check if we just need Dev install
            logging.info(f'No new rel install needed...')
            if second_build_is_newer(currentDeviceBuildVersion, lastDevBuild):
                updateDevicePath = configs.get_dev_build_updateDevice_path(lastDevBuild)
                logging.info(f'Will install new dev build {lastDevBuild}')
            else:
                logging.info('Device is up to date, no new build install needed')
        args.relBuild = lastRelBuild
        args.devBuild = lastDevBuild

        # test build extensions
        if not args.noTestInstall:
            if deviceMenderPath is not None:
                deviceMenderPath = deviceMenderPath + f'.T{DEVICE}'
            if updateDevicePath is not None:
                updateDevicePath = updateDevicePath + f'_T{DEVICE}'


    # this list of functions to be executed after an install to finish up prepping the device
    # add or subtract to list as needed
    processFunctionsList = []
    if args.cpaIP:
        processFunctionsList.append(lambda : deviceSerial.setCPA(args.cpaIP))
    if args.ntpState:
        if not args.ntpState.isdigit():
            args.ntpState = 0
        processFunctionsList.append(lambda : deviceSerial.enableNTP(int(args.ntpState)))
    if args.soundKill:
        processFunctionsList.append(deviceSerial.killSoundPlayer)

    # dict of results summary
    summary = []

    # make sure all log and dlog directories are present
    LOG_DIR = 'log'
    if not os.path.exists(LOG_DIR):
        os.mkdir(LOG_DIR)
    DLOG_DIR = 'dlog'
    if not os.path.exists(DLOG_DIR):
        os.mkdir(DLOG_DIR)
    DLOG_DEVICE_DIR = os.sep.join([DLOG_DIR, DEVICE])
    if not os.path.exists(DLOG_DEVICE_DIR):
        os.mkdir(DLOG_DEVICE_DIR)

    # with dev/rel build numbers, construct a log file name
    logFile = os.sep.join([LOG_DIR, f'{DEVICE}_d{args.devBuild}_r{args.relBuild}.log'])

    # create logger with current module namespace
    logger = logging.getLogger()
    fh = logging.FileHandler(logFile)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    fh.setLevel(LOG_LEVEL)
    logger.addHandler(fh)
    logger.info('Log file name: ' + logFile)

    # define 2 functions to execute before and after mender/updateDevice install
    # they save/restore /etc/systemd/network/eth.network file, which may help expedite network setup;

    def saveEth():
        deviceSerial.enterString('cp /etc/systemd/network/eth.network /data/')
        return False

    def restoreEth():
        deviceSerial.enterString('cp /data/eth.network /etc/systemd/network/')
        return True

    exitCode = 0
    # before attempting SSH login, check if host IP is enabled
    (deviceIP, netIP) = deviceSerial.get_ip_addresses(False, 60)
    if deviceIP == netIP == None:
        # no IP addresses at all seen, try setting up DHCP
        if not deviceSerial.setup_dhcp_network(): sys.exit(1)
        (deviceIP, netIP) = deviceSerial.get_ip_addresses()
    deviceSSH = DeviceSSH(deviceIP, 
                          configs[Config.USER], 
                          configs[Config.PASSWORD])
    currentDeviceBuildVersion = deviceSerial.get_versions()[0]

    if deviceMenderPath:
        # need mender install
        logger.info(f'Mender installing build {deviceMenderPath}')
        saveEth()
        menderInstall(deviceSerial, deviceSSH, deviceMenderPath, [restoreEth])
        currentDeviceBuildVersion = deviceSerial.get_versions()[0]
        if args.relBuild is not None and currentDeviceBuildVersion != args.relBuild:
            logger.warn(f'Device version {currentDeviceBuildVersion} not expected rel build version {args.relBuild}, mender install failed?')
            summary.append('Mender install failed or aborted: did NOT update to Rel build ' + args.relBuild)
            exitCode = 1
        else:
            logger.info('Mender install done!')
            summary.append('Mender install: updated to Rel build ' + deviceMenderPath)

        (deviceIP, netIP) = deviceSerial.get_ip_addresses(False, 60)
        if deviceIP == netIP == None:
            # no IP addresses at all seen, try setting up DHCP
            if not deviceSerial.setup_dhcp_network(): sys.exit(1)
            (deviceIP, netIP) = deviceSerial.get_ip_addresses()
        # ssh login again
        (deviceIP, netIP) = deviceSerial.get_ip_addresses()
        deviceSSH = DeviceSSH(deviceIP, 
                              configs[Config.USER], 
                              configs[Config.PASSWORD])
        # retrieve dlog
        if exitCode == 0:
            summary.append('dlog downloaded to: ' + 
                deviceSSH.download_current_dlog(DLOG_DEVICE_DIR, currentDeviceBuildVersion))

    if exitCode == 0 and updateDevicePath:
        logger.info(f'build {updateDevicePath} updateDevice installing')
        saveEth()
        updateDevice(deviceSerial, deviceSSH, updateDevicePath, [restoreEth])
        currentDeviceBuildVersion = deviceSerial.get_versions()[0]
        if args.devBuild is not None and currentDeviceBuildVersion != args.devBuild:
            logger.warn(f'Device version {currentDeviceBuildVersion} != expected dev version {args.devBuild}, update install failed?')
            summary.append('Dev build install failed or aborted: did NOT update to Dev build ' + args.devBuild)
            exitCode = 2
        else:
            logger.info(f'All done! Device now at version {currentDeviceBuildVersion}')
            summary.append('Dev install: updated to dev build ' + updateDevicePath)

        (deviceIP, netIP) = deviceSerial.get_ip_addresses(False, 60)
        if deviceIP == netIP == None:
            # no IP addresses at all seen, try setting up DHCP
            if not deviceSerial.setup_dhcp_network(): sys.exit(1)
            (deviceIP, netIP) = deviceSerial.get_ip_addresses()
        # ssh login again
        (deviceIP, netIP) = deviceSerial.get_ip_addresses()
        deviceSSH = DeviceSSH(deviceIP, 
                                configs[Config.USER], 
                                configs[Config.PASSWORD])
        # retrieve dlog
        if (exitCode == 0):
            summary.append('dlog downloaded to: ' + 
                deviceSSH.download_current_dlog(DLOG_DEVICE_DIR, currentDeviceBuildVersion))

    # do a system check, this part runs even if no updates done
    if any([x() for x in processFunctionsList]):
        logger.info('Config settings applied, rebooting to take effect...')
        deviceSerial.reboot()
        # check config lambdas again, if any still return True, means one more didn't stick
        if any([x() for x in processFunctionsList]):
            logger.warn('WARNING: one or more config settings may have failed')
        (deviceIP, netIP) = deviceSerial.get_ip_addresses()
        deviceSSH = DeviceSSH(deviceIP, 
                          configs[Config.USER], 
                          configs[Config.PASSWORD])

    # execute showProcessInfo.sh
    (out, err) = deviceSSH.executeCommand('/usr/local/sbin/showProcessInfo.sh')
    logger.info('showProcessInfo stdout')
    list(map(logger.info, out))
    logger.info('showProcessInfo stderr')
    list(map(logger.info, err))
    (out, err) = deviceSSH.executeCommand('/usr/local/sbin/showProcessInfo.sh |grep -v /usr/local|grep ": "|grep -v Running')
    if len(out) > 0:
        logger.warn("****** ====> One or more expected processes no in Running state")

    # poll DEO for alarms
    pollTime = 200
    #try:
    if DeoWebSocket.pollDeoAlarm(netIP, pollTime):
        logger.warn("One or more alarms seen, DLOG downloaded")
        summary.append('**** ALARMS seen ***')
        summary.append('dlog downloaded to: ' + 
            deviceSSH.download_current_dlog(DLOG_DEVICE_DIR, currentDeviceBuildVersion))
    else:
        logger.info(f'All set! No alarms observed in {pollTime} seconds')
        summary.append(f'No alarms seen within {pollTime} seconds')
    #except:
    #    pass

    summary.append(f'Log file: {logFile}')
    summary.append(f'Device (driver) IP: {deviceIP}')
    summary.append(f'            net IP: {netIP}')
    logger.info("\n======================================================\nSummary\n")
    list(map(logger.info, summary))

    sys.exit(exitCode)


if __name__ == '__main__':
    main()