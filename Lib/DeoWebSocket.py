import logging
import asyncio
import json
import time
from aiohttp import ClientSession
from utils import *

logger = None

# DEO top level JSON fields
DEVICE_DATA_CONFIG='DeviceDataConfig'
DEVICE_DATA='DeviceData'
# container fields
STRUCTURE_NAME='structureName'
STRUCTURE_DATA='structureData'
SYSTEM_TIME='systemTime'

class DeoWebSocket():
    """description of class"""

    def __init__(self, IP: str):
        self.URL = f'ws://{IP}:8080/'
        self.session = ClientSession()
        self.ws = None
        self.evtLoop = asyncio.get_event_loop()
        self.evtLoop.run_until_complete(self.connect())
        self.__receivedData = None
        #
        global logger
        logger = logging.getLogger(__name__)

    def __delete__(self):
        self.closeSession()
        self.evtLoop.close()

    async def connect(self):
        if self.ws is not None: return
        self.ws = await self.session.ws_connect(self.URL)

    async def receive(self, receiveTimeout = None):
        await self.connect()
        # set __receiveData, empty if timed out
        try:
            self.__receivedData = (await self.ws.receive(receiveTimeout)).data
        except asyncio.TimeoutError:
            self.__receivedData = ''

    async def getLastMsg(self, receiveTimeout:float):
        '''
        call ws.receive() until timeout encountered, then return last msg
        empties buffer
        '''
        if receiveTimeout is None:
            receiveTimeout = 0.5
        await self.connect()
        bufferEmpty = False
        data = ''
        while not bufferEmpty:
            try:
                data = (await self.ws.receive(receiveTimeout)).data
            except asyncio.TimeoutError:
                bufferEmpty = True
        self.__receivedData = data

    def getWSData(self, receiveTimeout = None) -> str:
        '''
        retrieves a msg from WS (from head of buffer)
        '''
        self.evtLoop.run_until_complete(self.receive(receiveTimeout))
        return self.__receivedData

    def getLatestDeoData(self) -> str:
        '''
        retrieves last DEO msg from WS (from tail of buffer)
        sleeps 1s to guarantee at least 1 DEO update
        '''
        time.sleep(1)
        self.evtLoop.run_until_complete(self.getLastMsg(0.5))
        return self.__receivedData

    def getDeoContainerByName(self, jsonList, containerName:str):
        '''
        input should be a JSON array with each object having a field 'structureName'
        returns new list of JSON objects filtered on the input name matching the field
        '''
        return list(filter(lambda obj: obj[STRUCTURE_NAME]==containerName, jsonList))

    def getCurrentContainerValue(self, container_value: str):
        '''
        returns container.value
        input container_value parameter is assumed to be in this form
        '''
        (container, value) = container_value.split('.')
        deoJson = json.loads(self.getLatestDeoData())
        while DEVICE_DATA not in deoJson:
            deoJson = json.loads(self.getLatestDeoData())
        containerJson = self.getDeoContainerByName(deoJson[DEVICE_DATA], container)[0]
        logger.debug(containerJson[STRUCTURE_DATA])
        return containerJson[STRUCTURE_DATA][value]

    def getCurrentAlarm0Condition(self):
        '''
        poll DEO to get latest update
        returns value found for AlarmManagerData._activeAlarmsList0
        '''
        return self.getCurrentContainerValue('AlarmManagerData._activeAlarmsList0')

    def getAlarms(self) -> list:
        '''
        returns list of alarms
        '''
        alarms = []
        for n in range(0,10):
            alarm = self.getCurrentContainerValue(f'AlarmManagerData._activeAlarmsList{n}')
            if len(alarm) > 0:
                alarms.append(alarm)
            else:
                break
        return alarms

    def closeSession(self):
        logger.info('Closing session...')
        self.evtLoop.run_until_complete(self.session.close())

    @staticmethod
    def pollDeoAlarm(netIP: str, pollTime: int) -> bool:
        '''
        poll DEO through WebSocket to check alarm conditions
        return True means an alarm was seen, otherwise, no alarm happened in the polling period
        '''
        logging.info('Connecting to DEO WebSocket, check if any alarms raised...')
        # try a couple of times to connect
        tries = 3
        try:
            for i in range(0,tries):
                try:
                    logging.info('connecting...')
                    deoWS = DeoWebSocket(netIP)
                    # if we get here, it means the connection succeeded, break from loop
                    break
                except:
                    if i < (tries - 1):
                        logging.error('Connection attempt to DEO websocket failed, wait and try again...')
                        time.sleep(10)
                    else:
                        logging.error(f'Unable to connect to DEO websocket after {tries} attempts, aborting')
                        raise Exception('Cannot poll for alarms ==> unable to make websocket connnection to DEO')

            def isAlarm0():
                alarms = deoWS.getAlarms()
                if len(alarms) == 0:
                    logging.info('No alarms...')
                    return False
                else:
                    logging.info('Alarms seen: ' + str(alarms))
                    return True

            # poll for alarms for up to pollTime seconds at 30s intervals
            return poll_wait_until(isAlarm0, pollTime, 30)

        finally:
            deoWS.closeSession()




