import unittest
import logging
import os
import time
from Config import Config
from DeviceSerial import DeviceSerial
from DeviceSSH import DeviceSSH
from DeoWebSocket import DeoWebSocket

class pytest_sanity_base(unittest.TestCase):
    """description of class"""

    configs = DEVICE_serial = DEVICE_Ssh = DEVICE_IP = NET_IP = DEO_WS = None 

    # global setup
    @classmethod
    def setup(cls, config_file, containers, processes):
        super().setUpClass()
        configs = Config(config_file)
        cls.DEVICE_serial = DeviceSerial(configs[Config.SERIAL_PORT])
        cls.DEVICE_serial.login(configs[Config.USER], configs[Config.PASSWORD])

        cls.DEVICE_IP, cls.NET_IP = cls.DEVICE_serial.get_ip_addresses()
        build, os_version = cls.DEVICE_serial.get_versions()
        logging.info(f'====> Device build version: {build}  os version: {os_version}')
        logging.info(f'====> Device host IP: {cls.DEVICE_IP}   app (net) IP: {cls.NET_IP}')
        cls.DEVICE_Ssh = DeviceSSH(cls.DEVICE_IP, configs[Config.USER], configs[Config.PASSWORD])

    # global teardown
    @classmethod
    def teardown(cls):
        if cls.DEO_WS is not None: cls.DEO_WS.closeSession()
        super().tearDownClass()

    @classmethod
    def _test_containers(cls, self):
        (stdout, stderr) = cls.DEVICE_Ssh.executeCommand("lxc-ls -f|grep RUNNING|cut -f1 -d' '")
        self.assertEqual(len(stderr), 0)
        self.assertEqual(set(stdout), cls.containers)

    @classmethod
    def _test_processes(cls, self):
        (stdout, stderr) = cls.DEVICE_Ssh.executeCommand("ps -ef|grep '/usr/local/sbin'|cut -f5 -d'/'")
        for p in cls.processes:
            if p not in stdout:
                logging.error(f'Process {p} not running on device')
        self.assertEqual(len(stderr), 0)
        self.assertTrue(cls.processes.issubset(set(stdout)))

    @classmethod
    def _test_any_alarms_presence(cls, self):
        if cls.DEO_WS is None: cls.DEO_WS = DeoWebSocket(cls.NET_IP)
        logging.info('Sleeping 30s for any delayed alarms to show up...')
        time.sleep(30)
        logging.info('Awake! Checking for alarms in DEO...')
        alarms = cls.DEO_WS.getAlarms()
        if len(alarms) > 0:
            logging.error(f'alarm(s) seen: {alarms}')
        else:
            logging.info('No alarms!')
        self.assertEqual(len(alarms), 0)