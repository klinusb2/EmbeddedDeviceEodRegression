import logging
import DeoWebSocket
import json
import time

IP = '10.183.176.232'
deoWS = DeoWebSocket.DeoWebSocket(IP)

def test_ws_get_data():
    deoJson = json.loads(deoWS.getWSData())
    logging.info('Number of structures: ' + str(len(deoJson[DeoWebSocket.DEVICE_DATA_CONFIG])))

    #time.sleep(5)
    # should an empty override JSON
    logging.info(deoWS.getWSData())

    # subsequent messages should come in at 1s intervals
    for i in range(10):
        data = deoWS.getWSData(0.25)
        if len(data) > 0:
            deoJson = json.loads(data)
            logging.info('Number of structures: ' + str(len(deoJson[DeoWebSocket.DEVICE_DATA])))
            list(map(logging.info, deoWS.getDeoContainerByName(deoJson[DeoWebSocket.DEVICE_DATA], 
                                                     'ActiveConstraintsData')))
            logging.info('time: ' + deoJson[DeoWebSocket.SYSTEM_TIME])
        else:
            logging.info('No new data...')

    logging.info('Wrapping up...')
    deoWS.closeSession()
    #

def test_ws_deo_update():
    time.sleep(5)
    deoJson = json.loads(deoWS.getLatestDeoData())
    logging.info('Number of structures: ' + str(len(deoJson[DeoWebSocket.DEVICE_DATA])))
    logging.info('time: ' + deoJson[DeoWebSocket.SYSTEM_TIME])
    time.sleep(5)
    deoJson = json.loads(deoWS.getLatestDeoData())
    logging.info('Number of structures: ' + str(len(deoJson[DeoWebSocket.DEVICE_DATA])))
    logging.info('time: ' + deoJson[DeoWebSocket.SYSTEM_TIME])
    alarm0 = deoWS.getCurrentAlarm0Condition()
    logging.info(f'=={alarm0}==')
    assert len(alarm0) == 0
