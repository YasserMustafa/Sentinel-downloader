# -*- coding: utf-8 -*-
import urllib2
import sys
import os
import errno
import logging
import imp
import signal
import time

# http://stackoverflow.com/questions/2028517/python-urllib2-progress-hook
# http://stackoverflow.com/questions/5783517/downloading-progress-bar-urllib2-python
# http://stackoverflow.com/questions/1517616/stream-large-binary-files-with-urllib2-to-file
# The 3rd link explain how to write a file by chunk. Indeed the second link is
# not adapted for large since the entire file is read and loaded into the memory before
# writing.

module_path = os.path.dirname(os.path.realpath(__file__)) 
sys.path.append(module_path)

import misc_tools
imp.reload(misc_tools)

if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(funcName)s ' +
                              '- %(levelname)s - %(message)s')
    steam_handler = logging.StreamHandler()
    steam_handler.setFormatter(formatter)
    steam_handler.setLevel(logging.DEBUG)
    logger.addHandler(steam_handler)
else:
    logger = logging.getLogger('sentinel_dl')

#--------------------------------timout class---------------------------------#
# I've noticed that in rare case, the read operation inside chunk_read3 function
# hangs forever, thus freezing the whole script
# A workaround has been found on the following link:
# http://stackoverflow.com/questions/8464391/what-should-i-do-if-socket-setdefaulttimeout-is-not-working
# I'm currently using the alarm workaround which only work under unix systems.
# I need to implement the cross plateform solution but it looks complicated
# so i'll do it later

class Timeout():
  """Timeout class using ALARM signal"""
  class Timeout(Exception): pass

  def __init__(self, sec):
    self.sec = sec

  def __enter__(self):
    signal.signal(signal.SIGALRM, self.raise_timeout)
    signal.alarm(self.sec)

  def __exit__(self, *args):
    signal.alarm(0) # disable alarm

  def raise_timeout(self, *args):
    raise Timeout.Timeout()

#--------------------------------chunk_report---------------------------------#
def chunk_report(bytes_so_far, chunk_size, total_size):
    """Function that display a download progress status in the standard output.
    ex: Downloaded 181403648 of 1069547520 bytes (16.96%)

    args:
        bytes_so_far (int): number of bytes already downloaded
        chunk_size (int): number of bytes to read and write at each iteration
        total_size (int): size of the file currently downloaded
    """
    percent = float(bytes_so_far) / total_size
    percent = round(percent*100, 2)
    sys.stdout.write("Downloaded %d of %d bytes (%0.2f%%)\r" % 
       (bytes_so_far, total_size, percent))
    sys.stdout.flush()
    if bytes_so_far >= total_size:
        sys.stdout.write('\n')

#---------------------------------chunk_read3----------------------------------#
def chunk_read3(response, destination_path, checksumReal, chunk_size=8192, report_hook=None):
    """Function that read a file from an uri and write it to the hard drive.
    
    args:
        response (??): url handler (returned by urlopen())
        destination_path (string): path to write the file
        chunk_size (int): number of bytes to read and write at each iteration
        report_hook: Pass a function name. If None, the progress status will not
                    be shown.

    return:
        True if the there is no spaceleft of the disk. False otherwise.
    """
    # If there is no spaceleft on the disk, the file which is currently being
    # written is removed from the disk.
    total_size = response.info().getheader('Content-Length').strip()
    total_size = int(total_size)
    fulldisk = False
    filesize = 0
    readTimeout = 300

    # The function readresponse is just a wrapper fonction that has been created
    # to avoid repetition and is placed inside the chunk_read3 function because it
    # is only used here. 
    def readresponse(destination_path2, chunk_size2, total_size2, report_hook2):
        bytes_so_far = 0
        fulldisk2 = False
        with open(destination_path2, 'wb') as f:
            while True:
                try:
                    with Timeout(readTimeout):
                        chunk = response.read(chunk_size2)
                except Timeout.Timeout:
                    logger.error('Alarm, Read timeout(%s)'% str(readTimeout))
                    chunk = 0
                if not chunk:
                    break
                bytes_so_far += len(chunk) 
                try:
                    f.write(chunk)
                except IOError as e:
                    print 'errno:', e.errno
                    print 'err message:', os.strerror(e.errno)
                    if e.errno == errno.ENOSPC:
                        os.remove(destination_path2)
                        fulldisk2 = True
                    break
                if report_hook2:
                    report_hook2(bytes_so_far, chunk_size2, total_size2)
        return fulldisk2
    
    try:
       filesize = os.path.getsize(destination_path) 
    except OSError as e:
        logger.debug('errno: %s err message: %s'% (str(e.errno), os.strerror(e.errno)))
        fulldisk = readresponse(destination_path, chunk_size, total_size, report_hook)
    else:
        logger.debug('Generating checksum md5…')
        md5generated = misc_tools.generate_file_md5(os.path.dirname(destination_path),
                                                    os.path.basename(destination_path),
                                                    chunk_size)
        logger.debug('checksum real: %s'% md5generated)
        if checksumReal == md5generated:
            logger.info('The file has already been well downloaded.')
        else:
            logger.info('The file has already been downloaded but is corrupted or incomplete. ' +
                        'Redownloading the file…')
            fulldisk = readresponse(destination_path, chunk_size, total_size, report_hook) 
    return fulldisk

#------------------------------------test-------------------------------------#
if __name__ == '__main__':
    base_path = os.path.dirname(module_path)
    destination_path = base_path + "/testfile/ubuntuiso.zip"
    test_url = 'http://www.blog.pythonlibrary.org/wp-content/uploads/2012/06/wxDbViewer.zip'
    #destination_path =  "/home/andrestumpf/Documents/scihub/cours python/script_python/mkonig/SentinelDownloads/ubuntuiso.zip"
    test_url2 = 'http://releases.ubuntu.com/14.04.4/ubuntu-14.04.4-desktop-amd64.iso?_ga=1.131277711.1865819736.1456999850'
    checksumReal1 = '9d8c8dac21597019cf5dbe75951b72b9'
    checksumReal2 = '807fa1f246b719d28d0b362fd2f31855'
    # test_url is a small file
    # test_url2 is an ubuntu iso of around 1GB.
    # Change the url in try statement accordingly.
    # Fill your hard drive to trigger the errno.ENOSPC error (no spaceleft
    # on disk)
    try:
        handle = urllib2.urlopen(test_url2)
    except IOError, e:
        if hasattr(e, 'reason'):
            print 'Nous avons échoué à joindre le serveur.'
            print 'Raison: ', e.reason
        elif hasattr(e, 'code'):
            print 'Le serveur n\'a pu satisfaire la demande.'
            print 'Code d\' erreur : ', e.code
    else:
        result = chunk_read3(handle, destination_path, checksumReal2, 2**23, report_hook=chunk_report)
        print 'no spaceleft: ', result
