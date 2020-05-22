import logging
import time
from DeviceSerial import DeviceSerial
from Config import Config

'''
PyTest tests for trialing device setup and connections
'''
CONFIG_FILE = 'FINIA.INI'
# get config info
configs = Config(CONFIG_FILE)
# serial connection
deviceSerial = DeviceSerial(configs[Config.SERIAL_PORT])
deviceSerial.login(configs[Config.USER], configs[Config.PASSWORD])

def test_serial_get_ips():
    (driverIP, netIP) = deviceSerial.get_ip_addresses()
    logging.info('hostIP: ' + driverIP)
    logging.info(' netIP: ' + netIP)
    #assert driverIP != None
    assert netIP != None

def test_serial_get_versions():
    versions = deviceSerial.get_versions()
    logging.info('build version: ' + versions[0])
    logging.info('   os version: ' + versions[1])

def test_login():
    deviceSerial.login(configs[Config.USER], configs[Config.PASSWORD])

def test_logout():
    deviceSerial.logout()

def test_logout_login():
    deviceSerial.logout()
    assert deviceSerial.login(configs[Config.USER], configs[Config.PASSWORD])

def test_check_device_type():
    assert deviceSerial.checkDeviceType(configs[Config.DEVICE])

def test_check_wrong_device_type():
    assert not deviceSerial.checkDeviceType('NON_EXISTENT')

def test_setup_dhcp():
    assert deviceSerial.setup_dhcp_network()

def test_reboot():
    deviceSerial.reboot()

def test_pingToRemote():
    assert deviceSerial.pingToRemote()