# -*- coding: utf-8 -*-
"""This module provides functionnalities build around the urllib2 library. More
specifically, it deals with with requests around both protocol provided by sci-
hub: open search (os) and open data (od). The open search query are used to
retrieve xml file of product list (as in a catalog) while the open data ones
are used to download products. More information about open search and open data
protocole can be found on the scihub API documention:
https://scihub.copernicus.eu/twiki/do/view/SciHubUserGuide/5APIsAndBatchScripting#Open_Search
This module currently use urllib2. Maybe it could have been better to use the
easier and higher level request http library:
http://requests.readthedocs.org/en/master/
"""

import urllib2
import urllib
import time
import os
import sys
import imp
import logging

module_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(module_path)

import misc_tools
import xml_tools
import progressbar
imp.reload(misc_tools)
imp.reload(xml_tools)
imp.reload(progressbar)

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

#--------------------------------authenticate---------------------------------#
def authenticate(username, password, url):
    """Function that install a specific opener for accessing scihub through the
    API. (https://docs.python.org/2.7/howto/urllib2.html)

    args:
        username (string): username at the scihub webpage
        password (string): password at the scihub webpage
        url (string): url of the scihub webpage.
                        'https://scihub.copernicus.eu/dhus'
    """
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, url, username, password)
    handler = urllib2.HTTPBasicAuthHandler(password_mgr)
    opener = urllib2.build_opener(handler)
    urllib2.install_opener(opener)
    passed = False
    
    # After insalling the opener, we try to send a request to see if it works.
    # If it didn't for whatever reason, then the function return False.
    # The special case of http 401 error is handled to test if the credentials
    # are valid.
    urlRequest = url + "/search?q=*"
    urlRequestFormat = urllib.quote(urlRequest, ':()[]/?=,&')
    try:
        handle = urllib2.urlopen(urlRequestFormat)
    except IOError, e:
        logger.debug('error %s: %s'% (e.code, e.reason))
        if e.code == 401:
            logger.error('Unauthorized or basic authentication failed. Please check '
                  + 'your username and password or make sure your account is '
                  + 'eligible for using the API.')
        passed = False
    else:
        passed = True
    return passed

#-------------------------------getproductlist--------------------------------#
def getproductlist(urlRequest, nbRetry, waitTime, xmlPath):
    """Function that send an open search query and retrieve the server response
    (i.e. xml file)

    args:
        urlRequest (string): raw (non formatted) url query.
        nbRetry (int): number of time the client will try to contact the
                        server.
        waitTime (int): time in second to wait between tries
        xmlPath (string): path where the xml response file will be saved

    return:
        passed: Boolean stating if the query was successful or not
    """
    i = 0
    passed = False
    urlRequestFormat = urllib.quote(urlRequest, ':()[]/?=,&')
    while True:
        try:
            handle = urllib2.urlopen(urlRequestFormat)
        except IOError, e:
            i += 1
            if hasattr(e, 'reason'):
                print 'Nous avons échoué à joindre le serveur.'
                print 'Raison: ', e.reason
            elif hasattr(e, 'code'):
                print 'Le serveur n\'a pu satisfaire la demande.'
                print 'Code d\' erreur : ', e.code
            logger.info('Waiting %s seconds…'% str(waitTime))
            time.sleep(waitTime)
        else:
            page = handle.read()
            textfile = open(xmlPath, 'w')  
            textfile.write(page)
            textfile.close()
            passed = True
            break
        if i >= nbRetry:
            break
    return passed

#---------------------------------browseprod----------------------------------#
def browseprod(urlRequest, sat, numbProd, maxItem, nbRetry, waitTime, xmlPath):
    """Function that browse numbProd products from the begining of the catalog
    for a specified query, read the returned xml file and store the list of
    product in a list.

    args:
        urlRequest (string): raw (non formatted) url query.
        sat (string): name of the satellite, either 'S1' or 'S2'
        numbProd (int): total number of product to retrieve
        maxItem (string): maximum number of product to retrieve in an
                        open search query.
        nbRetry (int): number of time the client will try to contact the
                        server.
        waitTime (int): time in second to wait between tries
        xmlPath (string): path where the xml response file will be saved

    return:
        a list of list where each element of the higher level list correpond
        to one product and each element of the sublist contains different info-
        rmations about the product (title, uuid, download link (open data link)
        of the whole archive, cloud percentage if 'S2')
    """
    
    # Depending on the maxItem parameter, the function will either retrieve all
    # product in one time or piece by piece. For exemple if the total number of
    # product numbProd = 1200 and maxItem = 500, the catalog will be browsed 3
    # times to retrieve all the product. If maxItem = 2000, then, only one pass
    # is necessary. This function browse the entire catalog.
    product_list = []
    quotient = numbProd // maxItem
    reste = numbProd % maxItem
    if reste == numbProd:
        logger.debug('Retrieving %s product(s) in one query…'% str(numbProd))
        current_url = misc_tools.buildreq(urlRequest, reste, 0)
        result = getproductlist(current_url, nbRetry, waitTime, xmlPath)
        if result == True:
            product_list = xml_tools.getprodlist(xmlPath, sat)
            logger.debug('List of product successfully retrieved.')
    else:
        if reste != 0:
            nb_iter = quotient + 1
        else:
            nb_iter = quotient
        logger.debug('Retrieving %s product(s) in %s queries…'% (str(numbProd),
                                                                 str(nb_iter)))
        for i in range(0, nb_iter):
            if (reste != 0) and (i == (nb_iter - 1)):
                logger.debug('%s\%s. retreiving only the reste (%s) for the last iteration'
                             % (str(i+1), str(nb_iter), str(reste))) 
                current_url = misc_tools.buildreq(urlRequest, reste, i*maxItem)
            else:
                logger.debug('%s\%s. retreiving %s items'% (str(i+1),
                                                            str(nb_iter),
                                                            str(maxItem)))
                current_url = misc_tools.buildreq(urlRequest, maxItem, i*maxItem)
            result = getproductlist(current_url, nbRetry, waitTime, xmlPath)
            if result == True:
                product_list.extend(xml_tools.getprodlist(xmlPath, sat))
                logger.debug('iteration %s\%s succeed'% (str(i+1),str(nb_iter)))
            else:
                logger.debug('iteration %s\%s failed'% (str(i+1),str(nb_iter)))
                product_list = [] 
                break
    numb_prod_fin = xml_tools.getnumbprod(xmlPath)
    logger.debug('total number of prouduct before: %s'% (str(numbProd)))
    logger.debug('total number of prouduct after: %s'% (str(numb_prod_fin)))
    if numb_prod_fin != numbProd:
        logger.warning('The number of total products seems to have changed during the operation.')
        product_list = []
    else:
        logger.debug('Browse product ok')
    return product_list

#--------------------------------getimagefile---------------------------------#
def getimagefile(urlRequest, nbRetry, waitTime, filePath, chunkSize, checksumReal):
    """Function that download the product specified by urlRequest into the
    disk.

    args:
        urlRequest (string): raw (non formatted) opendata url. (Works well
                            without formatting with quote). Any url that finishes with
                            '$/value'
            ex: https://scihub.copernicus.eu/dhus/odata/v1/Products('0282b16c-310a-408b-aad6-85fdfa02a5da')/$value
        nbRetry (int): number of time the client will try to contact the
                        server.
        waitTime (int): time in second to wait between tries
        filePath (string): path where the file will be saved
        chunkSize (int): bytes to read and write. (a file is written on the disk
                        piece by piece.)

    return:
        passed (boolean): True if the urlopen was successful. False otherwise.
        diskspace (boolean): True if the current file couldn't be wrote because
                            no left space on the hard drive. False otherwise.

    note: if (True, True) is returned, it doesn't neccessarly mean that the
    download was successful.
    """
    i = 0
    passed = False
    fulldisk = False
    while True:
        try:
            handle = urllib2.urlopen(urlRequest)
        except IOError, e:
            i += 1
            if hasattr(e, 'reason'):
                print 'Nous avons échoué à joindre le serveur.'
                print 'Raison: ', e.reason
            elif hasattr(e, 'code'):
                print 'Le serveur n\'a pu satisfaire la demande.'
                print 'Code d\' erreur : ', e.code
            logger.info('Waiting %s seconds…'% str(waitTime))
            time.sleep(waitTime)
        else:
            fulldisk = progressbar.chunk_read3(handle, filePath, checksumReal, chunkSize, report_hook=progressbar.chunk_report)
            passed = True
            break
        if i >= nbRetry:
            break        
    return (passed, fulldisk)

#-----------------------------------getmd5------------------------------------#
def getmd5(urlRequest, nbRetry, waitTime):
    """Function that retrieve the real md5checksum of the complete archive.

    args:
        urlRequest (string): raw (non formatted) opendata url. (Works well
                            without formatting with quote). This url corresponds to
                            the odata uri to download the whole product.
            ex: https://scihub.copernicus.eu/dhus/odata/v1/Products('0282b16c-310a-408b-aad6-85fdfa02a5da')/$value
        nbRetry (int): number of time the client will try to contact the
                        server.
        waitTime (int): time in second to wait between tries

    return:
        passed (boolean): True if the urlopen was successful. False otherwise.
        checksum_md5 (string): the checksum, equal '' if a problem happened
    """
    i = 0
    passed = False
    checksum_md5 = ''
    checksum_url = os.path.dirname(urlRequest)
    checksum_url = checksum_url + '/Checksum/Value/$value'
    while True:
        try:
            handle = urllib2.urlopen(checksum_url)
        except IOError, e:
            i += 1
            if hasattr(e, 'reason'):
                print 'Nous avons échoué à joindre le serveur.'
                print 'Raison: ', e.reason
            elif hasattr(e, 'code'):
                print 'Le serveur n\'a pu satisfaire la demande.'
                print 'Code d\' erreur : ', e.code
            logger.info('Waiting %s seconds…'% str(waitTime))
            time.sleep(waitTime)
        else:
            checksum_md5 = handle.read()
            passed = True
            break
        if i >= nbRetry:
            break            
    return (passed, checksum_md5)

#---------------------------------getmanifest---------------------------------#
def getmanifest(urlRequest, title, nbRetry, waitTime, xmlPath):
    """Function that retrieve the manifest.safe xml file of a product.

    args:
        urlRequest (string): raw (non formatted) opendata url of the download.
                            This url corresponds to the odata uri to download the
                            whole product.
        title (string): name of the product
        nbRetry (int): number of time the client will try to contact the
                        server.
        waitTime (int): time in second to wait between tries
        xmlPath (string): path where the xml response file will be saved

    return:
        passed (boolean): True if the urlopen was successful. False otherwise.
    """
    # This fuction build the uri of the manifest.safe file based on the
    # download link of the product.
    # Example:
    # dl_link: <ServiceRootUri> /Products('UUID')/$value
    # manifest.safe: <ServiceRootUri> /Products('UUID')/Nodes('Filename')/Nodes('manifest.safe')/$value
    manifest_uri = os.path.dirname(urlRequest)
    logger.debug('baseuri: %s'% manifest_uri)
    manifest_uri = manifest_uri + "/Nodes('%s.SAFE')/Nodes('manifest.safe')/$value"% title
    logger.debug('baseuri: %s'% manifest_uri)
    result = getproductlist(manifest_uri, nbRetry, waitTime, xmlPath)
    return result

#---------------------------------filternewproducts---------------------------------#
def filternewproduct(oldProduct, totalProduct):
    """This function compare two list of products and retrieve the ones that are in
    totalProduct but not in oldProduct. Thus allowing to find the new products in
    the scihub opensearch database. The uuid (unique identifier) is used to identify
    and filter the totalProduct list.

    args:
        oldProduct (list of list): list of product previously downloaded
        totalProduct (list of list): list of products currently in the database which
                                    comprises the previous product + potentially new
                                    published products.
    return:
        The filtered totalProduct containing only the products that are not in
        oldProduct
    
    """
    #extract uuid of products previously downloaded (corrupted or not)
    oldUuid = [elem[1] for elem in oldProduct]
    #print(oldUuid)
    newProduct = [elem for elem in totalProduct if elem[1] not in oldUuid]
    return newProduct
 
#------------------------------------Test-------------------------------------#
if __name__ == '__main__':

    base_path = os.path.dirname(module_path)
    config_path = base_path + "/config.cfg"

    # Assuming the readconf function has already been tested
    conf_dict = misc_tools.readconf(config_path)
    # print(conf_dict)

    # Variable
    xmlpath = base_path + "/testfile/testbrowseprod.xml"
    xmlmanifestpath = base_path + "/testfile/testmanifest.xml"
    nbretry = 2
    waittime = 10
    requestS1 = 'https://scihub.copernicus.eu/dhus/search?q=platformname:Sentinel-1 AND footprint:"Intersects(POLYGON((6.55 44.31, 6.55 44.47, 6.86 44.47, 6.86 44.31, 6.55 44.31)))"'
    requestS2 = 'https://scihub.copernicus.eu/dhus/search?q=platformname:Sentinel-2 AND footprint:"Intersects(POLYGON((6.55 44.31, 6.55 44.47, 6.86 44.47, 6.86 44.31, 6.55 44.31)))"'
    a_product = "https://scihub.copernicus.eu/dhus/odata/v1/Products('0282b16c-310a-408b-aad6-85fdfa02a5da')/$value"
    name_of_a_product = 'S2A_OPER_PRD_MSIL1C_PDMC_20160222T115941_R008_V20160218T104104_20160218T104104'
    checksum_prod = 'c9f8fa21f7506da1a4255616e002670a'
    file_path_test = base_path + "/testfile/" + name_of_a_product + ".zip"
    
    # set test
    list_function = ['authenticate', 'getproductlist', 'browseprod',
                     'getimagefile', 'getmd5', 'getmanifest',
                     'filternewproducts']
    test_function = [list_function[6]] # insert function(s) from list_function to test
    request = requestS2 # requestS1 or requestS2

    if(list_function[0] in test_function):
        print('#--------------test: %s--------------#'% list_function[0])
        urlrequest = urllib.quote(requestS1, ':()[]/?=,&')
        # Comment in and out the authentication lines below to see if it is
        # working properly
        passed = authenticate(conf_dict['log']['user'], conf_dict['log']['pw'],
                     conf_dict['log']['auth_url'])
        #passed = authenticate('lalala', 'lilili',
        #             conf_dict['log']['auth_url'])
        print 'authentication succeed:', passed 
        
    if(list_function[1] in test_function):
        print('#--------------test: %s--------------#'% list_function[1])
        authenticate(conf_dict['log']['user'], conf_dict['log']['pw'],
                     conf_dict['log']['auth_url'])
        misc_tools.create_directory(os.path.dirname(xmlpath))
        result = getproductlist(request, nbretry, waittime, xmlpath)
        print 'Succeed:', result
        # You can check if the file was created in the testfile folder
        
    if(list_function[2] in test_function):
        print('#--------------test: %s--------------#'% list_function[2])
        sat_dict = {'S1':'platformname:Sentinel-1', 'S2':'platformname:Sentinel-2'}
        authenticate(conf_dict['log']['user'], conf_dict['log']['pw'],
                     conf_dict['log']['auth_url']) 
        sat = misc_tools.findSat(request, sat_dict)
        result = getproductlist(request, nbretry, waittime, xmlpath)
        print 'Succeed get product list:', result
        numb_prod = xml_tools.getnumbprod(xmlpath)
        max_item = 6
        print(sat)
        print(numb_prod)
        product_list = browseprod(request, sat, numb_prod, max_item, nbretry, waittime, xmlpath)
        print 'product list size: ', len(product_list)
        max_item = 1000
        product_list2 = browseprod(request, sat, int(numb_prod), max_item, nbretry, waittime, xmlpath)
        print 'Same_list ?:', product_list == product_list2
        if product_list == product_list2:
            for element in product_list:
                for subelement in element:
                    print subelement
                print('\n')
        
    if(list_function[3] in test_function):
        print('#--------------test: %s--------------#'% list_function[3])
        chunk_size = 10000 * 1024
        authenticate(conf_dict['log']['user'], conf_dict['log']['pw'],
                     conf_dict['log']['auth_url'])
        result = getimagefile(a_product, nbretry, waittime, file_path_test, chunk_size, checksum_prod)
        print 'Succeed handle:', result[0]
        print 'no diskspace left:', result[1]

    if(list_function[4] in test_function):
        print('#--------------test: %s--------------#'% list_function[4])
        authenticate(conf_dict['log']['user'], conf_dict['log']['pw'],
                     conf_dict['log']['auth_url'])
        result = getmd5(a_product, nbretry, waittime)
        print 'succeed:', result[0]
        print 'checksum of %s: '% name_of_a_product, result[1]

    if(list_function[5] in test_function):
        print('#--------------test: %s--------------#'% list_function[5])
        authenticate(conf_dict['log']['user'], conf_dict['log']['pw'],
                     conf_dict['log']['auth_url'])
        result = getmanifest(a_product, name_of_a_product, nbretry, waittime, xmlmanifestpath)
        logger.debug('get manifest succeed: %s'% result)

    if(list_function[6] in test_function):
        print('#--------------test: %s--------------#'% list_function[6])
        sat_dict = {'S1':'platformname:Sentinel-1', 'S2':'platformname:Sentinel-2'}
        authenticate(conf_dict['log']['user'], conf_dict['log']['pw'],
                     conf_dict['log']['auth_url']) 
        sat = misc_tools.findSat(request, sat_dict)
        result = getproductlist(request, nbretry, waittime, xmlpath)
        print 'Succeed get product list:', result
        numb_prod = xml_tools.getnumbprod(xmlpath)
        max_item = 500
        print(sat)
        print(numb_prod)
        product_list = browseprod(request, sat, numb_prod, max_item, nbretry, waittime, xmlpath)
        print 'product list size: ', len(product_list)
        print '\nnew prod 1'
        newprod1 = filternewproduct(product_list, product_list)
        print '\nnew prod 2'
        newprod2 = filternewproduct(product_list[:5], product_list)
        print '\nnew prod 3'
        newprod3 = filternewproduct([], product_list)  
        for i, newprod in enumerate([newprod1, newprod2, newprod3]):
            print('list %s'% str(i+1))
            if not newprod:
                print('no new product found')
            else:
                print('new product found: %s'% str(len(newprod)))
                for elem in newprod:
                    print(elem)
