from pytest_sanity_base import pytest_sanity_base

class TestOrionSanity(pytest_sanity_base):

    # List expected containers running
    containers = set(['driver', 
                      'net', 
                      'ntp',
                      'proc',
                      'supervisor'])

    # List expected processes
    processes = set(['JournalCapture',
                     'ProcessLogger',
                     'UpdateManager',
                     'Thanos',
                     'Loki',
                     'Datalogger',
                     'ConfigWriter',
                     'DeoServerApp',
                     'AlarmDisplayApp',
                     'DeviceGUIManager',
                     'ServiceGUIManager',
                     'Procedure', 
                     'AlarmManager',
                     'SystemStatusMonitor',
                     'Driver', 
                     'timesetup',
                     'Supervisor',
                     ])

    CONFIG_FILE = 'ORION.INI'

    # global setup
    @classmethod
    def setUpClass(cls):
        return super().setup(cls.CONFIG_FILE, cls.containers, cls.processes)

    @classmethod
    def tearDownClass(cls):
        return super().teardown()

    def test_containers(self):
        super()._test_containers(self)

    def test_processes(self):
        super()._test_processes(self)

    def test_any_alarms_presence(self):
        super()._test_any_alarms_presence(self)
