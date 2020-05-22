from pytest_sanity_base import pytest_sanity_base

class TestFiniaSanity(pytest_sanity_base):

    # List expected containers running
    containers = set(['driver', 
                      'net', 
                      'ntp',
                      'proc'])

    # List expected processes
    processes = set(['JournalCapture',
                     'ProcessLogger',
                     'UpdateManager',
                     'Datalogger',
                     'ConfigWriter',
                     'DeoServerApp',
                     'AlarmDisplayApp',
                     'FiniaGUIManager',
                     'ServiceGUIManager',
                     'Procedure', 
                     'AlarmManager',
                     'SystemStatusMonitor',
                     'Driver', 
                     #'timesetup',
                     ])

    CONFIG_FILE = 'FINIA.INI'

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
