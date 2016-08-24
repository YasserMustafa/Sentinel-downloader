# -*- coding: utf-8 -*-
"""This module contains some basic functions
"""
import os
import ConfigParser
import urllib
import hashlib
import logging

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
    
#----------------------------create_directory-----------------------------#
def create_directory(dir_path):
    """Function that create a directory

    parameters:
        dir_path (string): Path of the futur directory
    
    return:
        True if the directory existed, False otherwise
    """
    did_exist = True
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        did_exist = False      
    return did_exist

#---------------------------------findSat--------------------------------------#
def findSat(request, sat_dict):
    """Function that find the satellite from a request

    parameters:
        request (string): open search request
        sat_dict (dictionary):{'S1':'platformname:Sentinel-1', 'S2':'platformname:Sentinel-2'} 
    return:
        return 'S1' or 'S2' wether the request contained 'plateformname:Sentinel-1/2'
        or '' if nothing was found.
    """
    sat = ''
    for element in sat_dict:
        if sat_dict[element] in request:
            sat = element
            logger.debug('satellite: %s'% sat)
            break
    return sat

#---------------------------------readconf-------------------------------------#
def readconf(config_path):
    """Function that read a configuration file

    parameters:
        config_path (string): path of the configuration file
    return:
        dictionary: a dictionary of dictionary that contains the different
                    section and parameter:value. The higher level dictionary
                    contains the section as key and a dictionary as value.
                    This lower dictionary contains the parameter as key and
                    the value of the parameter as value.
    """ 
    config = ConfigParser.RawConfigParser()
    config.read(config_path)
    dictionary = {}
    for section in config.sections():
        dictionary[section] = {}
        for option in config.options(section):
            dictionary[section][option] = config.get(section, option)
    return dictionary

#---------------------------------buildreq-------------------------------------#
def buildreq(url_request_raw, row, start):
    """Function that append 2 keywords for a base request. This new request
    allows to navigate through the catalog

    parameters:
        url_request_raw (string): non formated base request
        row (int): number of item to display in a request
        start (int): index from which
    return:
        url with appended keywords and values
    """
# Follow the link for more information about the 'rows' and 'start' parameters:
# https://scihub.copernicus.eu/twiki/do/view/SciHubUserGuide/5APIsAndBatchScripting#Discover_the_list_of_the_product
    url_request_raw = url_request_raw + "&rows=" + str(row) + "&start=" + str(start)
    url_request = urllib.quote(url_request_raw, ':()[]/?=,&')
    return url_request

#---------------------------------cloudfilter----------------------------------#
def cloudfilter(prod_list, sat, maxcloudperc):
    """Function that filter a product list base on the maximum cloud percentage
    specified

    parameters:
        prod_list (list of list): list of product
        sat (string): satellite 'S1' or 'S2'
        maxclouperc (int): maximum cloud percentage allowed
    return:
        filtered product list that contains only the product that match the
        cloud percentage condition.
    """
    if sat != 'S1':
        prod_list_filter = [elem for elem in prod_list if elem[-1] <= maxcloudperc]
    else:
        prod_list_filter = prod_list
    return prod_list_filter

#---------------------------------generate_file_md5----------------------------------#
# http://stackoverflow.com/questions/1131220/get-md5-hash-of-big-files-in-python
def generate_file_md5(rootdir, filename, blocksize=2**20):
    """Function that calculate the checksum md5 of a file.

    parameters:
        rootdir (string): directory of the file
        filename (string): name of the file
        blocksize (int): chunk size to read.
    return:
        the checksum md5 returned is '' if a problem happened.
    """
    checksum = ''
    m = hashlib.md5()
    #logger.debug('filepath: %s'% os.path.join(rootdir, filename))
    try:
        f = open(os.path.join(rootdir, filename), "rb")
    except IOError as e:
        logger.error('errno: %s err message: %s'% (str(e.errno), os.strerror(e.errno)))
    else:
        logger.debug('file size: %s'% os.path.getsize(os.path.join(rootdir, filename)))
        with f:
            while True:
                buf = f.read(blocksize)
                if not buf:
                    break
                m.update(buf)
            checksum = m.hexdigest() 
    return checksum

#---------------------------------extractBandsTiles----------------------------------#
def extractBandsTiles(tiles, bands):
    """Function that extract the bands and tiles specified in the request.csv

    parameters:
        tiles (string): exemple 'tile1, tile2, tile5'
        bands (string): exemple 'B01, B02, B05'
    return:
        (tuple): the first element contains a list of tiles and the second one,
                a list of bands.
                exemple (['tiles1', 'tiles2', 'tiles5'],['B01', 'B02', 'B05'])
    """ 
    tiles = tiles.replace(" ", "")
    bands = bands.replace(" ", "")
    l_bands = bands.split(",")
    l_tiles = tiles.split(",")
    return l_tiles, l_bands
    
#-----------------------------------Test------------------------------------#
if __name__ == '__main__':
          
    # Récupération du repertoire principal
    module_path = os.path.dirname(os.path.realpath(__file__))
    base_path = os.path.dirname(module_path)

    # Some variable
    requestS1 = 'https://scihub.copernicus.eu/dhus/search?q=platformname:Sentinel-1 AND footprint:"Intersects(POLYGON((6.55 44.31, 6.55 44.47, 6.86 44.47, 6.86 44.31, 6.55 44.31)))"'
    requestS2 = 'https://scihub.copernicus.eu/dhus/search?q=platformname:Sentinel-2 AND footprint:"Intersects(POLYGON((6.55 44.31, 6.55 44.47, 6.86 44.47, 6.86 44.31, 6.55 44.31)))"'
    sat_dict = {'S1':'platformname:Sentinel-1', 'S2':'platformname:Sentinel-2'}
    tiles1 = 'T31TGJ, T31TGK, T31TDL'
    bands1 = 'B01, B02, B03'
    tiles2 = 'T31TGJ,T31TGK,T31TDL'
    bands2 = 'B01,B02, B03'
    tiles3 = ''
    bands3 = 'B01,B02, B03' 
    # set test
    list_function = ['create_directory', 'findSat', 'readconffile',
                     'buildreq', 'cloudfilter', 'generate_file_md5',
                     'extractBandsTiles']
    test_function = [list_function[5]] # insert function(s) from list_function to test
    request = requestS2 # requestS1 or requestS2 
    
    if(list_function[0] in test_function):
        print('#--------------test: %s--------------#'% list_function[0])
            # Create test directory
        test_path = base_path + "/testtempdir"

            # Test create_directory function
        exist = create_directory(test_path)
        print(exist)

            # Test create_directory function
        exist = create_directory(test_path)
        print(exist)

    if(list_function[1] in test_function):
        print('#--------------test: %s--------------#'% list_function[1])
        request1 = 'https://scihub.copernicus.eu/dhus/search?q=platformname:Sentinel-1 AND footprint:"Intersects(POLYGON((6.55 44.31, 6.55 44.47, 6.86 44.47, 6.86 44.31, 6.55 44.31)))"'
        request2 = 'https://scihub.copernicus.eu/dhus/search?q=platformname:Sentinel-2 AND footprint:"Intersects(POLYGON((6.55 44.31, 6.55 44.47, 6.86 44.47, 6.86 44.31, 6.55 44.31)))"'
        request3 = 'https://scihub.copernicus.eu/dhus/search?q=platformname:Sentinel-8 AND footprint:"Intersects(POLYGON((6.55 44.31, 6.55 44.47, 6.86 44.47, 6.86 44.31, 6.55 44.31)))"'
        sat = findSat(request1, sat_dict)
        print('satellite: %s'% sat)
        sat = findSat(request2, sat_dict)
        print('satellite: %s'% sat)
        sat = findSat(request3, sat_dict)
        if sat == '':
            sat = 'none'
        print('satellite: %s'% sat)

    if(list_function[2] in test_function):
        print('#--------------test: %s--------------#'% list_function[2])
        config_path = base_path + "/config.cfg"
        print 'chemin du module: ', module_path
        print 'chemin du script principal: ', base_path
        settings = readconf(config_path)
        print(settings)

    if(list_function[3] in test_function):
        print('#--------------test: %s--------------#'% list_function[3])
        url_raw = 'https://scihub.copernicus.eu/dhus/search?q=platformname:Sentinel-1 AND footprint:"Intersects(POLYGON((6.55 44.31, 6.55 44.47, 6.86 44.47, 6.86 44.31, 6.55 44.31)))"'
        print(url_raw)
        url = buildreq(url_raw, 5, 0)
        print(url)

    if(list_function[4] in test_function):
        print('#--------------test: %s--------------#'% list_function[4])

        # Import module
        import sys
        import imp 

       #Import module
        # Ajout du chemin du dossier contenant les modules dans la liste des chemins du système
        sys.path.append(module_path)
        # Import
        import osodrequest
        imp.reload(osodrequest)
        import xml_tools
        imp.reload(xml_tools)
        
        # Build configuration path
        config_path = base_path + "/config.cfg"
        #print(config_path)

        # Read configuration file
        conf_dict = readconf(config_path)
        #print(conf_dict)

        # Authentication at scihub webpage
        osodrequest.authenticate(conf_dict['log']['user'], conf_dict['log']['pw'], conf_dict['log']['auth_url'])

        # Variable
        xmlpath = base_path + "/testfile/testbrowseprod.xml"
        nbretry = 2
        waittime = 120
        maxitem = 1000
        maxcloudperc = 20
        sat = findSat(request, sat_dict)
        # Get number of product
        urlrequest = urllib.quote(request, ':()[]/?=,&') 
        result = osodrequest.getproductlist(urlrequest, nbretry, waittime, xmlpath)
        print 'Succeed:', result
        if result == True:
            # Get the number of product of the current request
            numb_prod = xml_tools.getnumbprod(xmlpath)
            print 'nombre de produit de la requête: ', numb_prod
            # Get product list
            prod_list = osodrequest.browseprod(request, sat, numb_prod, maxitem, nbretry, waittime, xmlpath)
            # Filter the list
            filtered_prod_list = cloudfilter(prod_list, sat, maxcloudperc)
            same_list = (prod_list == filtered_prod_list)
            if same_list == True:
                print('Pas de filtrage de la liste (%s)\nTaille: %s'% (sat, str(len(filtered_prod_list))))
            else:
                print('Filtrage de la liste effectué.\nTaille initial: %s\nTaille après filtrage: %s'% (str(len(prod_list)), str(len(filtered_prod_list))))
            for element in filtered_prod_list:
                print element

    if(list_function[5] in test_function):
        print('#--------------test: %s--------------#'% list_function[5])
        rootdir = base_path + '/testfile'
        filename = '7z1514-extra.7z'
        file_md5 = generate_file_md5(rootdir, filename, blocksize=2**20)
        logger.info('checksum: %s'% file_md5)
        file_md5 = generate_file_md5(rootdir, 'blabla.xyz', blocksize=2**20)
        logger.info('checksum: %s'% file_md5)
        file_md5 = generate_file_md5(rootdir, '', blocksize=2**20)
        logger.info('checksum: %s'% file_md5)
        file_md5 = generate_file_md5('/blabla/blibli', '', blocksize=2**20)
        logger.info('checksum: %s'% file_md5)
        file_md5 = generate_file_md5('', '', blocksize=2**20)
        logger.info('checksum: %s'% file_md5)
        rootdir1 = '/media/sentinel/projet_final/sentinel_dl/Barcelonnette2/S2/2016/'
        filename1 = 'S2A_OPER_PRD_MSIL1C_PDMC_20160113T193242_R065_V20160113T103004_20160113T103004.zip'
        file_md5 = generate_file_md5(rootdir1, filename1, blocksize=2**27) 
        
    if(list_function[6] in test_function):
        print('#--------------test: %s--------------#'% list_function[6])
        extract = extractBandsTiles(tiles1, bands1)
        print(extract[0])
        print(extract[1])
        extract = extractBandsTiles(tiles2, bands2)
        print(extract[0])
        print(extract[1]) 
        extract = extractBandsTiles(tiles3, bands3)
        print(extract[0])
        print(extract[1])
