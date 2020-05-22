import logging
import os
from Config import Config
from DeviceSerial import DeviceSerial
from DeviceSSH import DeviceSSH

CONFIG_FILE = 'ORION.INI'
configs = Config(CONFIG_FILE)
CHECK_PROCESSES_SCRIPT = 'checkProcesses.sh'
deviceSerial = DeviceSerial(configs[Config.SERIAL_PORT])
deviceSerial.login(configs[Config.USER], configs[Config.PASSWORD])

TEST_FILE='ORION.INI'
TEST_DIR='tmp'
deviceIP = deviceSerial.get_ip_addresses()[0]
deviceSSH = DeviceSSH(deviceIP, configs[Config.USER], configs[Config.PASSWORD])

def test_ssh_command():
    (out, err) = deviceSSH.executeCommand('ls -la')
    assert len(err) == 0
    assert len(out) > 0
    logging.info(out)
    logging.info(err)

def test_scp_upload_default_target():
    # remove remote target file if there
    deviceSSH.removeRemoteFile(TEST_FILE)
    assert not deviceSSH.checkRemoteFileExists(TEST_FILE)
    deviceSSH.upload_file(TEST_FILE)
    assert deviceSSH.checkRemoteFileExists(TEST_FILE)

def test_scp_upload():
    # make sure target folder exists
    (out, err) = deviceSSH.executeCommand('mkdir -p ' + TEST_DIR)
    path = TEST_DIR + '/bar.ini'
    # remove remote target file if there
    deviceSSH.removeRemoteFile(path)
    # check remote target file not there
    assert not deviceSSH.checkRemoteFileExists(path)
    deviceSSH.upload_file(TEST_FILE, path)
    # check remote target file now there
    assert deviceSSH.checkRemoteFileExists(path)

def test_download_dlog():
    path = configs[Config.DLOG_FOLDER]
    dlogFile = deviceSSH.download_current_dlog(path, 999)
    assert os.path.exists(os.path.join(path, dlogFile))

def test_color_term():
    list(map(logging.info, deviceSSH.executeCommand('sh ' + CHECK_PROCESSES_SCRIPT)[0]))
