import logging
import serial
import re
import time
import sys
from utils import *

PROMPT = 'root@'
LOGIN = 'login'
LOGOUT = 'logout'
logger = None
APPLICATION = '/usr/local/etc/config/Application'
NETWORKINFO = '/data/config/NetworkInfo'
VISTA_SERVER = 'Usbwsutsvr01.bct.gambro.net'

class DeviceSerial:
    """class for handling serial port connection to device"""

    def __init__(self, serialPort):
        self._serialPort = serialPort
        self._ser = serial.Serial(serialPort, 115200, timeout=1)
        #
        global logger
        logger = logging.getLogger(__name__)

    def __del__(self):
        self._ser.close()

    def reset_buffers(self):
        self._ser.reset_input_buffer()
        self._ser.reset_output_buffer()

    def decoded_output(self):
        return [ line.decode('ISO-8859-1').strip() for line in self._ser.readlines() ]
    
    def enterString(self, commandString: str):
        '''type string and hit enter'''
        time.sleep(1)
        self._ser.write(str.encode(commandString + '\n'))
        time.sleep(2)

    def get_last_output_line(self):
        output = self.decoded_output()
        logger.debug(output)
        logger.debug('Number of lines in output read: ' + str(len(output)))
        if len(output) > 0:
            return output[-1]
        return None

    def checkDeviceType(self, deviceType: str) -> bool:
        self.enterString(f'grep deviceType /usr/local/etc/protocol/*.xml|grep -i {deviceType}')
        if len(self.decoded_output()) >2:
            print('----------------DeviceType ' + deviceType)
            return True
        # given deviceType not found in protocol files, printout what is found
        self.enterString(r'''grep -o 'deviceType="[^"]\+"' /usr/local/etc/protocol/*.xml''')
        list(map(logger.info, [s for s in self.decoded_output() 
                                if 'deviceType' in s and not 'grep' in s]))
        return False

    def read_single_line(self):
        return self._ser.readline().decode('utf-8').strip()

    def outputContains(self, chkString: str) -> bool:
        outputList = self.decoded_output()
        list(map(logging.info, outputList))
        return any(chkString in line for line in outputList)

    def outputContainsExact(self, chkString: str) -> bool:
        outputList = self.decoded_output()
        list(map(logging.info, outputList))
        return any(chkString == line.strip() for line in outputList)

    def logout(self):
        self._ser.write(b'\n\n')
        if self.outputContains(LOGIN): return
        self.enterString('exit')
        self._ser.write(b'\n\n')
        #assert self.outputContains(LOGOUT)

    def login(self, user='root', password='!C0vF3F3', firstTry = True) -> bool:
        '''log in (if not already)'''
        self.user = user
        self.password = password
        self._ser.write(b'\n\n')
        if self.outputContains(PROMPT): 
            logger.info('Already logged in')
            return True
        succeeded = False
        logger.info('not logged in, logging in now...')
        self.enterString(user)
        outputList = self.decoded_output()
        if any(PROMPT in line for line in outputList):
            # already got prompt (no password needed), so we are done
            return True
        if any('Password' in line for line in outputList):
            if self.executeCommandAndVerifyOutput(password + '\n', PROMPT, False):
                return True
            else:
                time.sleep(1)
                logger.info('Command prompt not seen, trying again with another <enter>')
                self._ser.write(b'\n')
                succeeded = self.outputContains(PROMPT)
        if not succeeded and firstTry:
            logger.error('Login failed on 1st try!')
            # if failed on 1st try, make a second attempt
            return self.login(user, password, False)
        return succeeded

    def reboot(self, killInternalUI: bool = True, waitForIP = True):
        '''
        reboots device, wait until login: prompt seen, then log again
        '''
        self.enterString('reboot')
        # expected reboot time (to get to a login prompt) shouldn't be >1min
        poll_wait_until(self.get_output_contains_function('login:'), 120)
        if not self.login(self.user, self.password):
            logging.error('Login failed after 2 attempts!')
            sys.exit(1)
        logging.info('waiting a bit for processes to start...')
        time.sleep(10)
        if killInternalUI:
            logging.info('checking if internal ui process is running...')
            if not self.executeCommandAndVerifyOutput('ps -ef|grep -v grep|grep nwjs|wc -l', '0'):
                logging.info('ui (nwjs) process running, killing it...')
                self.enterString('lxc-attach -n net -- systemctl stop ui')
        # poll/wait until device app IP shows up
        if waitForIP:
            if not poll_wait_until(lambda : self.get_ip_addresses()[1] is not None, 100):
                logging.warn('Did not see device IP, possibly problem with network interface')
        logging.info('Device rebooting done')

    def setup_dhcp_network(self) -> bool:
        '''
        checks if /etc/systemd/network/eth.network is setup for SSH
        if not, add the necessary DHCP config and reboot to activate
        '''
        netFile = '/etc/systemd/network/eth.network'
        if self.executeCommandAndVerifyOutput('grep -i dhcp ' + netFile, 'DHCP=', False):
            if poll_wait_until(lambda : self.get_ip_addresses()[0] is not None, 50):
                logger.info('DHCP already setup')
                return True
            else:
                # DHCP seems to be setup but no host IP found
                logger.info(f'DHCP found in network file {netFile}, but no host IP found, trying a reboot...')
        else:
            logger.info('DHCP not setup in network config, setting up...')
            # no DHCP info in network config, set it up
            self.enterString(r'echo -e "[Match]\nName=eth*\n\n[Network]\nDHCP=v4\n\n[DHCPv4]\nUseHostname=false" > ' + netFile)
            logger.info('DHCP configured, rebooting to take effect...')
        self.reboot()
        logger.info('Rebooting done, check IP addresses again...')
        if not poll_wait_until(lambda : self.get_ip_addresses()[0] is not None, 100):
            logger.error('Setup DHCP failed, maybe check network connection?')
            return False
        logger.info(f'Device IP setup via DHCP: {self.get_ip_addresses()[0]}')
        return True

    def poll_ip_addresses(self):
        '''Host(Driver) and net container IP addresses as tuple'''
        self.enterString('lxc-ls -f')
        driverIP = None
        netIP = None
        for line in self.decoded_output():
            if line.startswith('driver'):
                s = re.split(r',?\s+', line)[4]
                if len(s) >= 7:
                    driverIP = s
                    logger.debug(f"Host IP: {s}")
            if line.startswith('net'):
                s = re.split(r',?\s+', line)[4]
                if len(s) >= 7:
                    netIP = s
                    logger.debug(f"Appl IP: {s}")
        return (driverIP, netIP)

    def get_ip_addresses(self, rebootIfNone:bool = False, timeout:int = 300):
        # wait up to 300s for both IP addresses to show up
        poll_wait_until(lambda : self.poll_ip_addresses()[0] is not None, timeout)
        poll_wait_until(lambda : self.poll_ip_addresses()[1] is not None, timeout)
        driverIP, netIP = self.poll_ip_addresses()
        if driverIP is not None and netIP is not None:
            # IP addresses found, do a quick ping out to Vista server
            pass
#            if not self.pingToRemote(VISTA_SERVER):
#                logger.warn(f'Unable to ping from device or net container to {VISTA_SERVER}')
        else:
            logger.warn('Unable to see one or both host/net IP addresses!')
            if rebootIfNone:
                # if no IPs are found, try a reboot
                if driverIP is None and netIP is None:
                    self.reboot()
                    return self.get_ip_addresses()
        return (driverIP, netIP)

    def get_versions(self):
        '''Build/OS version strings as tuple'''
        self.enterString('grep _VERSION /usr/local/etc/ProjectInfo.txt')
        output = self.decoded_output()
        logger.debug(output)
        build = os_version = None
        for line in output:
            if 'BUILD_VERSION' in line:
                build = line.split('"')[1]
            elif 'OS_VERSION' in line:
                os_version = line.split('"')[1]
        return (build, os_version)

    def output_nonempty(self) -> bool:
        '''
        small function retrieving and checking serial output buffer
        (from device)
        primarily meant to be used for poll_wait_while_true() call
        '''
        outputList = self.decoded_output()
        list(map(logging.info, outputList))
        return len(outputList) and any([len(s)>0 for s in outputList]) > 0

    def get_output_contains_function(self, targetString: str):
        def func():
            return self.outputContains(targetString)
        return func

    #
    # utility functions below modifies device configuration
    # returns True/False indicating whether a device reboot is needed to take effect
    #

    def killSoundPlayer(self) -> bool:
        logging.info('killing SoundlPlayer if present')
        self.enterString('ps -ef|grep SoundPlayer|grep -v grep|awk \'{print "kill",$2}\'|sh')
        return False

    #
    # enable/disables NTP using /data/config/NetworkInfo.xml
    # input is an int, if <=0 NTP is disabled, otherwise NTP is enabled with timeout set to the int
    #
    # returns True/False indicating whether a reboot is needed for changes to take effect
    #
    def enableNTP(self, NTPtimeout: int = 45) -> bool:
        ntpIsEnabled = self.bachExecuteCommand(f'grep EnableNTP {NETWORKINFO}.xml|grep -i true > /dev/null')
        if NTPtimeout <= 0: 
            wantEnabled = False 
        else: 
            wantEnabled = True
            # get current NTPTimeoutSeconds setting
            self.enterString(f'grep NTPTimeoutSeconds {NETWORKINFO}.xml|grep -oP \'(?<=value=")\d+\'')
            outDigits = [out for out in self.decoded_output() if out.isdigit()]
            if len(outDigits) == 0:
                raise Exception(f'Unable to get NTPTimeoutSeconds value from {NETWORKINFO}.xml')
            currentTimeout = int(outDigits[0])

        if (not ntpIsEnabled and not wantEnabled) or \
            (ntpIsEnabled and wantEnabled and currentTimeout == NTPtimeout):
            logging.info(f'NTP is already set at: {wantEnabled}')
            return False
        if ntpIsEnabled != wantEnabled:
            if ntpIsEnabled and not wantEnabled:
                _from = 'true'
                _to = 'false'
            else:
                _from = 'false'
                _to = 'true'
            logging.info(f'NTP set to: {wantEnabled}')
            self.enterString(
                f"sed -i 's/\(.*EnableNTP.*value=\"\){_from}\(.*\)/\\1{_to}\\2/' {NETWORKINFO}.xml")
        if currentTimeout != NTPtimeout:
            logging.info(f'NTP timeout set to: {NTPtimeout}')
            self.enterString(
                f"sed -i 's/\(.*NTPTimeoutSeconds.*value=\"\).*\(\".*\)/\\1{NTPtimeout}\\2/' {NETWORKINFO}.xml")
        self.enterString(f"sha256sum {NETWORKINFO}.xml > {NETWORKINFO}.sha256sum")

        return True

    def setCPA(self, ip: str) -> bool:
        # check if Applcation xml file exists
        if not self.bachExecuteCommand(f'[ -e {APPLICATION}.xml ]'):
            logging.info(f'device does not have {APPLICATION}.xml')
            return False
        if self.executeCommandAndVerifyOutput(f'grep -i IPAddress {APPLICATION}.xml', ip, False):
            logging.info(f'CPA already set to: {ip}')
            return False
        logging.info(f'setting CPA to: {ip}')
        self.enterString(
            f"sed -i 's/\(IPAddress.*value=\"\).*\(\".*\)/\\1{ip}\\2/' {APPLICATION}.xml; sha256sum {APPLICATION}.xml > {APPLICATION}.sha256sum")
        return True

    def pingToRemote(self, remote: str = VISTA_SERVER) -> bool:
        '''
        pings out from device to given IP/hostname, tries 3 times, each ping sends 3 packets
        returns boolean indicating success/failure
        this method is mainly used to mitigate (hopefully) network problems in Vista lab
        '''
        for i in range(3):
            result1 = self.bachExecuteCommand(f'ping -c 3 {remote} > /dev/null')
            if result1: break
            time.sleep(5)
        for i in range(3):
            result2 = self.bachExecuteCommand(f'lxc-attach -n net -- ping -c 3 {remote} > /dev/null')
            if result2: break
            time.sleep(5)
        return result1 and result2

    #
    # executes the command line string, and check if output contains the expected string,
    # optional flags indicates whether to match exact (an output string is exact match)
    # or to just check any output string (default: True)
    # contains expected string
    #
    def executeCommandAndVerifyOutput(self, commandString: str, outputString: str, exact: bool = True) -> bool:
        self.enterString(commandString)
        if exact:
            return self.outputContainsExact(outputString)
        return self.outputContains(outputString)

    #
    # executes the input bash command and return the exit status
    #
    def bachExecuteCommand(self, commandString: str) -> bool:
        self.enterString(commandString)
        if not commandString.strip().endswith('echo $?'):
            commandString = commandString + '; echo $?'
        return self.executeCommandAndVerifyOutput(commandString, '0')