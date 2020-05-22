import logging
import os
from Config import Config
import regr

CONFIG_FILE = 'ORION.INI'
# get config info
configs = Config(CONFIG_FILE)
logging.basicConfig(level=logging.INFO)

'''
PyTest tests for config setup
'''

def test_get_latest_build():
    lastDevBuildVersion = configs.get_latest_dev_build_version()
    assert len(lastDevBuildVersion) > 0
    logging.info(f'Latest successful Dev build: {lastDevBuildVersion}')
    lastRelBuildVersion = configs.get_latest_rel_build_version()
    assert len(lastRelBuildVersion) > 0
    logging.info(f'Latest successful Rel build: {lastRelBuildVersion}')

def test_get_config_item():
    logging.info('Dev root path: ' + configs[Config.DEV_BUILD_ROOT])

def test_get_updateDevice_path():
    updateDevice = configs.get_dev_build_updateDevice_path()
    logging.info('latest Dev build updateDevice: ' + updateDevice)
    assert os.path.exists(updateDevice)

def test_get_menderUpdate_path():
    menderUpdate = configs.get_rel_build_menderUpdate_path()
    logging.info('latest Rel build mender.update: ' + menderUpdate)
    assert os.path.exists(menderUpdate)
