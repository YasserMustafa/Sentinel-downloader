# -*- coding: utf-8 -*-
"""This module contains functions related to reading and processing the
informations contained in the manifest.safe xml file
"""

from lxml import etree
import os
import logging
import itertools
import imp
import re
module_path = os.path.dirname(os.path.realpath(__file__))
base_path = os.path.dirname(module_path)

import osodrequest
import misc_tools
imp.reload(osodrequest)
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
    
#------------------------------------------------------------------------------#
#---------------------------FUNCTIONS------------------------------------------#
#------------------------------------------------------------------------------#

#--------------------------------function: readmanifest------------------------#
def readmanifest(xml_path):
    """Function that read a manifest.safe xml file and return the entire list of
    file contained within the product.

    parameters:
        xml_path (string): Path of the manifest.safe xml file
    
    return:
        List of list. Each higher list element correspond to a file and each
        sublist contains different informations about the element (directory
        and checksum)
    """
    elements = []
    tree = etree.parse(xml_path)
    checksum_list = tree.xpath('//checksum')
    location_list = tree.xpath('//fileLocation')
    logger.debug('Number of element found inside the current product: %s'%
                 str(len(checksum_list)))
    for location, checksum in zip(location_list, checksum_list):
        elements.append([location.get('href'), checksum.text])
    return elements

#--------------------------------function: generateuri-------------------------#
def generateuri(elements, urlRequest, title):
    """Function that build odata download uri based on the manifest.safe
    element path.

    args:
        elements (list): list of parts of a product (return of readmanifest)
        urlRequest (string): raw (non formatted) opendata download uri of the
                            entire product.
        title (string): name of the product
    return:
        elements: input elements + appended generated uri for each part of the
                product
    """
    # Exemple:
    # an element path from the manifest.safe: './HTML/UserProduct_index.html'
    # generated uri for this element: <ServiceRootUri>/Products('UUID')
    # /Nodes('Filename')/Nodes('HTML')/Nodes('UserProduct_index.html')/$value
    baseuri = os.path.dirname(urlRequest) + "/Nodes('%s.SAFE')"% title
    logger.debug('base uri: %s'% baseuri)
    for element in elements:
        currenturi = baseuri
        for i, part in enumerate(element[0].split("/")):
            if i != 0:
                currenturi += "/Nodes('%s')"% part
        currenturi += '/$value'
        element.append(currenturi)
        #logger.debug('uri dl:%s'% currenturi)
    return elements

#---------------------------function: filterelementS2---------------------------#
# def filterelementS2(elements, tiles, bands):
    # """Function that filter the element of the product depending on the tiles and
    # bands specified by the user in the request.csv file. Only for Sentinel-2

    # args:
        # elements (list): list of product's part (return of readmanifest)
        # tiles (list of string): name of the tiles to keep
                                # exemple ['T31TEJ','T31TDJ','T31TFK']
        # bands (list of string): list of bands to keep
                                # exemple: ['B01', 'B02']
    # return:
        # elements_gra (list): filtered input elements
    # """
    # elements_gra = [elem for elem in elements if 'GRANULE' in elem[0]]
    # elements_ngra = [elem for elem in elements if 'GRANULE' not in elem[0]]
    # if tiles[0] == '' and bands[0] != '':
        # logger.debug('keeping all tiles and only bands %s'% ', '.join(bands))
        # elements_gra = [elem for elem in elements_gra
                        # if any(word in elem[0] for word in bands)]
        # if len(elements_gra) == 0: 
            # logger.debug('no bands match the selected band filter: %s.'
                         # % ', '.join(bands))
            # elements_filtered = elements
        # else:
            # elements_gra.extend(elements_ngra)
            # elements_filtered = elements_gra
    # elif tiles[0] == '' and bands[0] == '':
        # logger.debug('no match. Empty filter')
        # elements_filtered = elements
    # else:
        # elements_gra = [elem for elem in elements_gra
                        # if any(word in elem[0] for word in tiles)]
        # if len(elements_gra) == 0:
            # logger.debug('no tiles match the selected tile filter.')
            # elements_filtered = elements
        # else:
            # if tiles[0] != '' and bands[0] == '':
                # logger.debug('keeping all bands and only tiles %s'
                             # % ', '.join(tiles))
                # elements_gra.extend(elements_ngra)
                # elements_filtered = elements_gra
            # else:
                # logger.debug('keeping tiles %s and bands %s'
                             # % (', '.join(tiles), ', '.join(bands)))
                # elements_gra = [elem for elem in elements_gra
                                # if any(word in elem[0] for word in bands)]
                # if len(elements_gra) == 0: 
                    # logger.debug('no bands match the selected band filter: %s.'
                                 # % ', '.join(bands))
                    # elements_filtered = elements
                # else:
                    # elements_gra.extend(elements_ngra)
                    # elements_filtered = elements_gra
    # return elements_filtered


def regexpfilter(elem_list, filt_list):
    """Filter an list of element based on a regexp filter list

    :arg1: TODO
    :returns: TODO

    """
    elem_list_filt = []
    re_filt_list = re.compile('|'.join(filt_list))
    for elem in elem_list:
        match = re.search(re_filt_list, elem[0])
        if match:
            elem_list_filt.append(elem)
    return elem_list_filt

#---------------------------function: filterelementS2---------------------------#
def filterelementS2(elements, tiles, bands):
    """Function that filter the element of the product depending on the tiles and
    bands specified by the user in the request.csv file. Only for Sentinel-2

    args:
        elements (list): list of product's part (return of readmanifest)
        tiles (list of string): name of the tiles to keep
                                exemple ['T31TEJ','T31TDJ','T31TFK']
        bands (list of string): list of bands to keep
                                exemple: ['B01', 'B02']
    return:
        elements_gra (list): filtered input elements
    """
    elements_gra = [elem for elem in elements if 'GRANULE' in elem[0]]
    elements_ngra = [elem for elem in elements if 'GRANULE' not in elem[0]]
    regexp_list_tiles_xml = []
    regexp_list_tiles = []
    regexp_list_bands = []
    regexp_list_bandsandtiles = []

    if tiles[0] == '' and bands[0] != '':
        regexp_list_tiles_xml.append('.*T[0-9]{2}[a-zA-Z]{3}\.xml$')
        # re_tiles_xml = re.compile('|'.join(regexp_list_tiles_xml))
        for band in bands:
            regexp_list_bands.append('.*(' + str(band) + ').*')
        # re_bands = re.compile('|'.join(regexp_list_bands))
        logger.debug('keeping all tiles and only bands %s'% ', '.join(bands))
        elements_gra_temp = regexpfilter(elements_gra, regexp_list_bands)
        if len(elements_gra_temp) == 0: 
            logger.debug('no bands match the selected band filter: %s.'
                         % ', '.join(bands))
            elements_filtered = elements
        else:
            element_gra = regexpfilter(elements_gra, (regexp_list_tiles_xml,
                regexp_list_bands))
            elements_gra.extend(elements_ngra)
            elements_filtered = elements_gra
    elif tiles[0] == '' and bands[0] == '':
        logger.debug('no match. Empty filter')
        elements_filtered = elements
    else:
        for tile in tiles:
            regexp_list_tiles.append('.*(' + str(tile) + ').*')
        # re_tiles = re.compile('|'.join(regexp_list_tiles))
        elements_gra = regexpfilter(elements_gra, regexp_list_tiles)
        if len(elements_gra) == 0:
            logger.debug('no tiles match the selected tile filter.')
            elements_filtered = elements
        else:
            if tiles[0] != '' and bands[0] == '':
                logger.debug('keeping all bands and only tiles %s'
                             % ', '.join(tiles))
                elements_gra.extend(elements_ngra)
                elements_filtered = elements_gra
            else:
                for band in bands:
                    regexp_list_bands.append('.*(' + str(band) + ').*')
                # re_bands = re.compile('|'.join(regexp_list_bands))
                elements_gra_temp = regexpfilter(elements_gra, regexp_list_bands)
                logger.debug('keeping tiles %s and bands %s'
                             % (', '.join(tiles), ', '.join(bands)))
                if len(elements_gra_temp) == 0: 
                    logger.debug('no bands match the selected band filter: %s.'
                                 % ', '.join(bands))
                    elements_filtered = elements
                else:
                    for tile in tiles:
                        regexp_list_tiles_xml.append('.*(' + str(tile) +
                                ')\.xml')
                        for band in bands:
                            regexp_list_bandsandtiles.append('.*(' + str(tile) +
                                    ').*(' + str(band) + ').*')
                    # re_tiles_xml = re.compile('|'.join(regexp_list_tiles_xml))
                    # re_bandsandtiles = re.compile('|'.join(regexp_list_bandsandtiles))
                    elements_gra = regexpfilter(elements_gra,
                            (regexp_list_tiles_xml + regexp_list_bandsandtiles))
                    elements_gra.extend(elements_ngra)
                    elements_filtered = elements_gra
    return elements_filtered

#---------------------------function: filterelementS2---------------------------#
# version 2: prendre en compte le fichier xml de la granule.
# petit problème: les regex sont un peu lente.
#TODO: gérer les différents cas de la version 1.
# def filterelementS2(elements, tiles, bands):
    # """Function that filter the element of the product depending on the tiles and
    # bands specified by the user in the request.csv file. Only for Sentinel-2

    # args:
        # elements (list): list of product's part (return of readmanifest)
        # tiles (list of string): name of the tiles to keep
                                # exemple ['T31TEJ','T31TDJ','T31TFK']
        # bands (list of string): list of bands to keep
                                # exemple: ['B01', 'B02']
    # return:
        # elements_gra (list): filtered input elements
    # """
    # elements_gra = [elem for elem in elements if 'GRANULE' in elem[0]]
    # elements_ngra = [elem for elem in elements if 'GRANULE' not in elem[0]]
    # regexp_list_tiles = []
    # regexp_list_bands
    # for tile in tiles:
        # regexplist.append('.*(' + str(tile) + ').xml')
        # for band in bands:
            # regexplist.append('.*(' + str(tile) + ').*(' + str(band) + ').*')
    # bandsandtiles = re.compile('|'.join(regexplist))
    # elements_gra_filt = [] 
    # for elem in elements_gra:
        # match = re.search(bandsandtiles, elem[0])
        # if match:
            # elements_gra_filt.append(elem)
    # elements_gra_filt.extend(elements_ngra)
    # return elements_gra_filt
 
#------------------------------------------------------------------------------#
#---------------------------TESTS----------------------------------------------#
#------------------------------------------------------------------------------#
if __name__ == '__main__':
    
    config_path = base_path + "/config.cfg"
    conf_dict = misc_tools.readconf(config_path)
    nbretry = 1
    waittime = 5
    dl_product = "https://scihub.copernicus.eu/dhus/odata/v1/Products('0282b16c-310a-408b-aad6-85fdfa02a5da')/$value"
    name_product = 'S2A_OPER_PRD_MSIL1C_PDMC_20160222T115941_R008_V20160218T104104_20160218T104104'
    uuid = '0282b16c-310a-408b-aad6-85fdfa02a5da'
    # xmlmanifestpath = base_path + "/testfile/testmanifest.xml"
    xmlmanifestpath = base_path + "/testfile/manifest.safe.xml"
    # tiles = ['T31TEJe','T31TDJt','T31TFKe']
    # bands = ['']
    tiles = ['T31TEJ','T31TDJ','T31TFK']
    # tiles = ['']
    bands = ['B02', 'B03', 'B04']
    # bands = ['B02e', 'B03e', 'B0a4']
    # set test
    list_function = ['readmanifest','generateuri', 'filterelementprod','download an image']
    test_function = ['filterelementprod'] # insert function(s) from list_function to test

#--------------------------------test: readmanifest----------------------------#
    if(list_function[0] in test_function):
        print('#--------------test: %s--------------#'% list_function[0])
        logger.debug('authenticating…')
        res = osodrequest.authenticate(conf_dict['log']['user'],
                                       conf_dict['log']['pw'],
                                       conf_dict['log']['auth_url'])
        logger.debug('authentication succeed: %s'% res)
        logger.debug('downloading manifest.safe…')
        result = osodrequest.getmanifest(dl_product, name_product, nbretry,
                                         waittime, xmlmanifestpath)
        logger.debug('get manifest succeed: %s'% result)
        logger.debug('reading manifest.safe…')
        elements = readmanifest(xmlmanifestpath)
        for element in elements:
            logger.debug('%s : %s'% (element[0], element[1]))
            
#--------------------------------test: generateuri-----------------------------#
    if(list_function[1] in test_function):
        print('#--------------test: %s--------------#'% list_function[1])
        logger.debug('authenticating…')
        res = osodrequest.authenticate(conf_dict['log']['user'],
                                       conf_dict['log']['pw'],
                                       conf_dict['log']['auth_url'])
        logger.debug('authentication succeed: %s'% res)
        logger.debug('downloading manifest.safe…')
        result = osodrequest.getmanifest(dl_product, name_product, nbretry,
                                         waittime, xmlmanifestpath)
        logger.debug('get manifest succeed: %s'% result)
        logger.debug('reading manifest file…')
        elements = readmanifest(xmlmanifestpath)
        logger.debug('generating download uri for %s product…')
        elements = generateuri(elements, dl_product, name_product)
        for element in elements:
            logger.debug('%s'% ' : '.join(element))

#--------------------------------test: filterelementprod-----------------------#
    if(list_function[2] in test_function):
        print('#--------------test: %s--------------#'% list_function[2])
        # Change tiles and bands variable to test the different cases
        logger.debug('authenticating…')
        # res = osodrequest.authenticate(conf_dict['log']['user'],
                                       # conf_dict['log']['pw'],
                                       # conf_dict['log']['auth_url'])
        # logger.debug('authentication succeed: %s'% res)
        # logger.debug('downloading manifest.safe…')
        # result = osodrequest.getmanifest(dl_product, name_product, nbretry,
                                         # waittime, xmlmanifestpath)
        # logger.debug('get manifest succeed: %s'% result) 
        # logger.debug('reading manifest file…')
        elements = readmanifest(xmlmanifestpath)
        logger.debug('Filtering elements of the product…')
        logger.debug('size before filtering: %s'% str(len(elements)))
        elements2 = filterelementS2(elements, tiles, bands)
        logger.debug('size after filtering: %s'% str(len(elements2)))
        for elem in elements:
            # print(elem[0])
            #logger.debug(elem[0])
            pass
        print('##################################')
        for elem in elements2:
            print(elem)
            # pass
        if sorted(elements) == sorted(elements2):
            print('same')
        else:
            print('not same')

#--------------------------test: download an image-----------------------------#
    if(list_function[3] in test_function):
        print('#--------------test: %s--------------#'% list_function[3])
        tiles = ['T31TEJ', 'T31TDJ']
        bands = ['B02', 'B03', 'B04']
        logger.debug('authenticating…')
        res = osodrequest.authenticate(conf_dict['log']['user'],
                                       conf_dict['log']['pw'],
                                       conf_dict['log']['auth_url'])
        logger.debug('authentication succeed: %s'% res)
        #logger.debug('downloading manifest.safe…')
        #result = osodrequest.getmanifest(dl_product, name_product, nbretry,
        #                                 waittime, xmlmanifestpath)
        #logger.debug('get manifest succeed: %s'% result) 
        logger.debug('reading manifest file…')
        elements = readmanifest(xmlmanifestpath)
        logger.debug('Filtering elements of the product…')
        logger.debug('size before filtering: %s'% str(len(elements)))
        elements = filterelementS2(elements, tiles, bands)
        logger.debug('size after filtering: %s'% str(len(elements)))
        logger.debug('Generating product element uri…')
        elements = generateuri(elements, dl_product, name_product)
        checksum_bool = []
        for i, elem in enumerate(elements):
            filepath = base_path + "/testfile/%s"% name_product + elem[0][1:]
            misc_tools.create_directory(os.path.dirname(filepath))
            logger.debug('download %s out of %s\n file : %s'
                         % (str(i+1), str(len(elements)), filepath))
            result = osodrequest.getimagefile(elem[2], nbretry, waittime, filepath, 2**23, elem[1])
            logger.debug('getimagefile succeed: %s'% str(result[0]))
            if result[0]:
                md5generated = misc_tools.generate_file_md5(os.path.dirname(filepath),
                                                            os.path.basename(filepath),
                                                            blocksize=2**20)
                goodfile = md5generated.lower() == elem[1].lower()
                checksum_bool.append(goodfile)
        logger.debug('%s file downloaded out of %s'% (str(len(checksum_bool)), str(len(elements))))
        logger.debug('%s file good out of %s'% (str(sum(checksum_bool)), str(len(checksum_bool))))
