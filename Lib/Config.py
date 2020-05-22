import logging
import os
from utils import *

class Config:
    '''class to handle device and host specific config parameters
        reads config file
        config file should be in the form:
        KEY1=VALUE1
        KEY2=VALUE2
        ...
        stores all key-vals in dict
    '''

    # config keys
    DEVICE='DEVICE'
    USE_SIM='USESIM'
    BUILD_ROOT='BUILD_ROOT'
    DEV_BUILD_ROOT='DEV_BUILD_ROOT'
    REL_BUILD_ROOT='REL_BUILD_ROOT'
    SERIAL_PORT='SERIAL_PORT'
    USER='USER'
    PASSWORD='PASSWORD'
    DLOG_FOLDER='DLOG_FOLDER'

    UPDATE_DEVICE_FILE='updateDevice'
    MENDER_FILE='device.mender'
    DEVICE_UPDATE_PATH='/data/' + UPDATE_DEVICE_FILE
    DEVICE_MENDER_PATH='/data/update/' + MENDER_FILE
    DEVICE_LOG_PATH='/data/log/'

    def __init__(self, configFile: str):
        self.configFile = configFile
        with open(self.configFile, 'rt') as configFile:
            self._configs = dict(line.rstrip().split('=') for line in configFile \
                if len(line.strip()) > 0 and line.lstrip()[0] != '#')
        self._buildRoot = self._configs[Config.BUILD_ROOT]
        self._DEV_BUILD_PATH = lambda _buildNum: os.path.join(self._buildRoot + self._configs[Config.DEV_BUILD_ROOT], _buildNum, 'Build')
        self._REL_BUILD_PATH = lambda _buildNum: os.path.join(self._buildRoot + self._configs[Config.REL_BUILD_ROOT], _buildNum, 'Build')
        self._DEV_BUILD_LIST = None
        self._REL_BUILD_LIST = None

    #
    # build version strings look like a.b.c.d, with a,b,c,d integers
    #   a,b,c are likely to be small numbers (0, 1, 2)
    #   d is the build number assigned by TFS and can go into thousands
    #
    # in this form, build version string can be compared (<, >, ==) using
    # function version_sort_key(version)
    #  version_sort_key(v1) < version_sort_key(v2) means v1 is earlier (older) than v2
    #

    def get_dev_build_list(self):
        # go through the folder list
        # extract the nnn part, take only if it's a number
        # get folder list, 
        if self._DEV_BUILD_LIST is None:
            buildList = [ build for build in os.listdir(self._buildRoot + self._configs[Config.DEV_BUILD_ROOT]) \
                if build.split('.')[-1].isdigit() and 
                   os.path.exists(f'{self._DEV_BUILD_PATH(build)}{os.path.sep}updateDevice') ]
            # sort it based on build number (digits after last period, latest will be last)
            self._DEV_BUILD_LIST = sorted(buildList, key=version_sort_key)
            logging.debug(buildList)
        return self._DEV_BUILD_LIST

    def get_latest_dev_build_version(self) -> str:
        return self.get_dev_build_list()[-1]

    def get_dev_build_updateDevice_path(self, buildVersion:str = None) -> str:
        '''
        returns string for the full path to updateDevice file
        if no arg buildVersion supplied, use latest build found
        '''
        if buildVersion is None:
            buildVersion = self.get_latest_dev_build_version()
        return os.path.join(self._DEV_BUILD_PATH(buildVersion), Config.UPDATE_DEVICE_FILE)

    def get_rel_build_list(self):
        if self._REL_BUILD_LIST is None:
            buildList = [ build for build in os.listdir(self._buildRoot + self._configs[Config.REL_BUILD_ROOT]) \
                if build.split('.')[-1].isdigit() and
                   os.path.exists(f'{self._REL_BUILD_PATH(build)}{os.path.sep}device.mender')]
            self._REL_BUILD_LIST = sorted(buildList, key=version_sort_key)
            logging.debug(buildList)
        return self._REL_BUILD_LIST

    def get_latest_rel_build_version(self) -> str:
        return self.get_rel_build_list()[-1]

    def get_rel_build_menderUpdate_path(self, buildVersion:str = None) -> str:
        if buildVersion is None:
            buildVersion = self.get_latest_rel_build_version()
        return os.path.join(
            self._REL_BUILD_PATH(buildVersion),
            Config.MENDER_FILE)

    def __getitem__(self, key: str) -> str:
        return self._configs[key]