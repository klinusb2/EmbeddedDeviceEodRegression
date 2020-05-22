import logging
import paramiko
import os
from scp import SCPClient

logger = None
lastPercent = 0

def progress(filename, size, sent):
    global lastPercent
    if sent*100//size != lastPercent:
        logger.info("%s\'s progress: %d/%d bytes  %.2f%%  \r" % (filename, sent, size, float(sent)/float(size)*100) )
        lastPercent = sent*100//size

class DeviceSSH:
    """SSH and SCP handling"""

    DEVICE_LOG_PATH = '/data/log/'

    def __init__(self, IP, user: str, password: str):
        self._IP = IP
        self._user = user
        self._password = password
        #
        self._sshClient = paramiko.SSHClient()
        #self._sshClient.load_system_host_keys()
        self._sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self._sshClient.connect(IP, username=user, password=password)
        except:
            # if first connect attempt fails, try again with an empty password
            # (because some devices maybe setup with no password)
            self._sshClient.connect(IP, username=user, password="")
        #
        self._scpClient = SCPClient(self._sshClient.get_transport(), progress=progress)
        #
        global logger
        logger = logging.getLogger(__name__)

    def __delete__(self):
        self._scpClient.close()
        self._sshClient.close()

    def executeCommand(self, commandString: str):
        '''
        execute command on SSH session
        returns stdout,stderr output as a tuple of lists of strings
        '''
        logger.debug('Executing command line: ' + commandString)
        stdin,stdout,stderr = self._sshClient.exec_command(commandString)
        return ([s.strip() for s in stdout.readlines()], \
                [s.strip() for s in stderr.readlines()])

    def removeRemoteFile(self, remoteFile: str):
        '''simply make sure the remote file is not there'''
        return self.executeCommand('rm -f ' + remoteFile)

    def upload_file(self, uploadFile, remoteFile:str = None):
        logger.debug('Uploading file: ' + uploadFile)
        if remoteFile == None:
            self._scpClient.put(uploadFile)
        else:
            logger.debug('  Uploading to: ' + remoteFile)
            self._scpClient.put(uploadFile, remoteFile)

    def download_file(self, downloadFile: str, targetPath: str = ''):
        logger.debug(f'Downloading file: {downloadFile}   target: {targetPath}')
        self._scpClient.get(downloadFile, targetPath)

    def download_current_dlog(self, targetPath: str = '', buildVersion: str = '') -> str:
        newestDlog = self.executeCommand('ls -t ' + DeviceSSH.DEVICE_LOG_PATH + '*.dlog|head -1|xargs -n 1 basename')[0][0].strip()
        if len(buildVersion) > 0:
            name, ext = newestDlog.split('.')
            targetFileName = '.'.join((name + '_build_' + buildVersion, ext))
        else:
            targetFileName = newestDlog
        targetPath = os.sep.join((targetPath, targetFileName))
        logger.info('Downloading dlog file: ' + newestDlog + ' ==> ' + targetPath)
        self.download_file(DeviceSSH.DEVICE_LOG_PATH + newestDlog, targetPath)
        return targetPath

    def checkRemoteFileExists(self, remoteFilePath: str) -> bool:
        logger.debug('Checking existence of file: ' + remoteFilePath)
        (out, err) = self.executeCommand('ls -l ' + remoteFilePath)
        logger.debug(out)
        logger.debug(err)
        return len(err) == 0 and len(out) > 0
