import unittest
import logging
import os
import json
from utils import *

# logging setup
#
# designate log file
logging.basicConfig(level=logging.INFO, 
                    filename=os.sep.join(['log',__name__ + '.log'])
                    )
# create logger with current module namespace
logger = logging.getLogger(__name__)
# add console handler to go along with file output
logger.addHandler(logging.StreamHandler())

CONFIG_FILE = 'ORION.INI'

count = 0
def counting():
    global count
    count += 1
    logger.info('count ' + str(count))
    return count < 3

def print1():
    print(1)

def print2():
    print(2)

functionList = [print1, print2]

jsonStr = '{"DeviceData":[{"structureData":{"_activeAlarmsList0":"","_activeAlarmsList1":"","_activeAlarmsList2":"","_activeAlarmsList3":"","_activeAlarmsList4":"","_activeAlarmsList5":"","_activeAlarmsList6":"","_activeAlarmsList7":"","_activeAlarmsList8":"","_activeAlarmsList9":"","_alarmAllowableActions":"","_alarmConditionState":false,"_alarmConstraint":"","_alarmName":"","_alarmPriority":"","_alarmType":"","_notificationType":""},"structureName":"AlarmManagerData"},{"structureData":{"_blue":0.0,"_dutyCyclePct":0.0,"_frequencyHz":0.0,"_green":0.0,"_red":0.0},"structureName":"AlarmLightData"}],"systemTime":"05/31/2019 19:19:34"}'
simpleJson = '{"first":1, "second":"data"}'

class Test_test1(unittest.TestCase):
    '''
    Unit tests for the device automation script regr.py.
    All must pass locally, self-contained with no external requirement
    run from IDE (Visual Studio) or from command line, from project root folder:
    $ python test1.py
    '''

    def test_config_file_string_exists(self):
        self.assertTrue(len(CONFIG_FILE) > 0, f'parameter CONFIG_FILE not defined')

    def test_config_file_exists(self):
        self.assertTrue(os.path.exists(CONFIG_FILE), f'Config file: {CONFIG_FILE} does not exists!')

    def test_poll_wait_false(self):
        poll_wait_while_true(lambda: False)

    def test_poll_wait_true_then_false(self):
        poll_wait_while_true(counting)

    def test_bytes(self):
        print(bytes([53,1,4,0,83,53,1,63,83]).decode('utf-8'))

    def test_function_list(self):
        [x() for x in functionList]

    def test_json_parse(self):
        jsonData = json.loads(jsonStr)
        print(jsonData['DeviceData'][0]['structureName'])
        print(jsonData['DeviceData'][0]['structureData']['_activeAlarmsList0'])

    def test_logging(self):
        logger.info('Testing logging ========!')

    def test_version_compare(self):
        self.assertTrue(second_build_is_newer('1.0.0.1', '2.0'))
        self.assertTrue(second_build_is_newer('1.0.0.1', '1.0.0.2'))
        self.assertTrue(second_build_is_newer('1.0.0', '1.0.0.1'))
        self.assertTrue(second_build_is_newer('2', '2.1'))
        self.assertTrue(second_build_is_newer('2.0.0', '2.1.0'))
        self.assertTrue(second_build_is_newer('2.3', '2.3.0.1'))
        self.assertFalse(second_build_is_newer('1.0.0.101', '1.0.0.99'))
        self.assertFalse(second_build_is_newer('1.0.0.101', '1.0.0.101'))
        self.assertFalse(second_build_is_newer('1.0.0.1140', '1.0.0.1140'))

if __name__ == '__main__':
    unittest.main()
