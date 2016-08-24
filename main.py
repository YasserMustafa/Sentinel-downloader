# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------#
#------------------------------------MAIN-------------------------------------#
#-----------------------------------------------------------------------------#
import imp
import sys
import csv
import os
import logging
from logging.handlers import RotatingFileHandler
import traceback


base_path = os.path.dirname(os.path.realpath(__file__))
module_path = base_path + "/Module"

sys.path.append(module_path)

import osodrequest
import misc_tools
import xml_tools
import xmlReport
import manifestSafe
imp.reload(osodrequest)
imp.reload(misc_tools)
imp.reload(xml_tools)
imp.reload(xmlReport)
imp.reload(manifestSafe)

#------------------------------------------------------------------------------#
# http://sametmax.com/ecrire-des-logs-en-python/
logger = logging.getLogger('sentinel_dl')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(module)s - %(funcName)s ' +
                              '- %(levelname)s - %(message)s')
log_path = base_path + '/activity.log'
file_handler = RotatingFileHandler(log_path, 'a', 2000000, 2)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
steam_handler = logging.StreamHandler()
steam_handler.setLevel(logging.INFO)
logger.addHandler(steam_handler)


def main():
    #------------------------------------------------------------------------------#
    # The code only support 'S1' and 'S2' for the moment
    sat_dict = {'S1':'platformname:Sentinel-1', 'S2':'platformname:Sentinel-2'}
    chunk_size = 2**23 # maximum number of byte to read when downloading something
                       # in order not to load a whole heavy file into the memory.
    fulldisk = False
    config_path = base_path + "/config.cfg"
    conf_dict = misc_tools.readconf(config_path)
    request_path = base_path + "/requete.csv"

    #------------------------------------------------------------------------------#
    logger.info('Starting authentication…')
    auth_succeed = osodrequest.authenticate(conf_dict['log']['user'],
                                            conf_dict['log']['pw'],
                                            conf_dict['log']['auth_url'])
    if not auth_succeed:
        logger.warning('closing script')
        sys.exit()
    else:
        logger.info('Authentication succeed')
    #------------------------------------------------------------------------------#    
    # Each request contained in the request.csv file is processed one after
    # the other (outer for loop). There si two main section. The first one consists
    # in re downloading products/parts that were not downloaded or that were 
    # corrupted the last time the script got launched. The second section consists
    # in checking if new products are available then downloaded. To determine if new
    # products have been published, the total number of product that a request returns
    # is compared to the total number of product the request returned the last time
    # the script was run. For each request, a xml report is writen which contains
    # informations about each images and whether the archives
    # got well downloaded or not. In the case tiles or bands are specified, an
    # additional xml report is written containing each parts and whether those parts
    # have been well retrieved or not. Thus, in the main report, if the status of a
    # product is 'archive corrupted' it means that at least one part is corrupted.
    #------------------------------------------------------------------------------#
    with open(request_path, 'rb') as csvfile:
        requestreader = csv.reader(csvfile, delimiter=';')
        next(requestreader)
        for row in requestreader:
            logger.info('Processing the following request: %s…'% row[1])
            if fulldisk:
                logger.warning('The hard drive is full. Skipping the remaining ' +
                               'requests.')
                break
            
            sat = misc_tools.findSat(row[1], sat_dict)
            if sat=='':
                logger.warning('The current request is not valid. It must ' +
                                'contains %s or %s. Skipping to the next request'%
                               (sat_dict['S1'], sat_dict['S2']))
                continue
            
            urlrequest = conf_dict['log']['auth_url'] + "/search?q=" + row[1]
            logger.debug('Current request: %s'% urlrequest)
            
            xml_product_path = base_path + "/cur_prod_list" + "/product_list.xml"
            misc_tools.create_directory(os.path.dirname(xml_product_path))
            logger.debug('Current xml product file temp path: %s'% xml_product_path) 

            cur_dl_path_base = conf_dict['param']['dl_dir'] + "/" + row[0]
            misc_tools.create_directory(cur_dl_path_base)
            logger.debug('Current download base path: %s'% cur_dl_path_base)
            
            report_path = cur_dl_path_base + '/rep_' + row[0][:5] + '_' + sat + '.xml'
            misc_tools.create_directory(os.path.dirname(report_path))
            logger.debug('Current report path: %s'% report_path)
            
            if not os.path.isfile(report_path):
                logger.debug('First time processing the current request.')
                xmlReport.createXml(report_path)
                xmlReport.addInfoTag(report_path, 0, 'number_past_product', 0)
                
            #-------------------------------Retrieving past failed product-----------------------------#
            past_prod_list = xmlReport.readXml(report_path)
            past_prod_list_filt = xmlReport.filterProductEntry(past_prod_list, 4)
            if (not past_prod_list_filt) and (len(past_prod_list) > 0):
                logger.info('All the past products are ok.')
            else:
                logger.info('Number of past product to be retrieved: %s'% len(past_prod_list_filt))
                for element in past_prod_list_filt:
                    #Ajouter ici un test qui permet de savoir si le scihub est indisponible pour éviter de rentrer dans chaque produit.
                    #Si indisponible alors ajouter un continue. peut être se réauthentifier pour voir ?
                    if (sat == 'S2') and ((row[3] != '') or (row[4] != '')): #tiles and/or bands case
                        bandsandtiles = misc_tools.extractBandsTiles(row[3], row[4])
                        base_prod_path = cur_dl_path_base + '/' + sat + '/' + element[5] + '/' + element[0]
                        xml_manifest_path = base_prod_path + '/' + 'manifest.safe' + '.xml'
                        report_part_path = cur_dl_path_base + '/rep_' + element[0] + '.xml'
                        misc_tools.create_directory(os.path.dirname(xml_manifest_path))
                        logger.debug('current status: %s'% element[4])
                        xmlReport.createXml(report_part_path)
                        if element[4] == 'missing manifest':
                            #repeat code 3 begin---------------------
                            if not fulldisk:
                                result = osodrequest.getmanifest(element[2], element[0],
                                                                 int(conf_dict['param']['nb_retry']),
                                                                 int(conf_dict['param']['wait_time']),
                                                                 xml_manifest_path)
                                if result:
                                    logger.info('Manifest.safe successfully retrieved')
                                    logger.info('reading manifest file…') 
                                    product_parts = manifestSafe.readmanifest(xml_manifest_path)
                                    logger.info('Filtering elements of the product…')
                                    size_before_filt = len(product_parts)
                                    logger.info('Number of parts before filtering: %s'% str(size_before_filt))
                                    product_parts = manifestSafe.filterelementS2(product_parts,
                                                                                 bandsandtiles[0],
                                                                                 bandsandtiles[1])
                                    size_after_filt = len(product_parts)
                                    logger.info('Number of parts after filtering: %s'% str(size_after_filt))
                                    if size_before_filt == size_after_filt:
                                        logger.info('No bands or tiles correspond to the specified bands and tiles ' +
                                                    'for the current product')
                                        xmlReport.removeProductEntry(report_path, element[1])
                                        continue
                                    logger.info('Generating product parts uri…')
                                    product_parts = manifestSafe.generateuri(product_parts,
                                                                             element[2],
                                                                             element[0])
                                    for i, part in enumerate(product_parts):
                                        if not fulldisk:
                                            part_path = base_prod_path + part[0][1:]
                                            misc_tools.create_directory(os.path.dirname(part_path))
                                            logger.info('download %s out of %s\n file : %s'
                                                         % (str(i+1), str(len(product_parts)), part_path))
                                            result = osodrequest.getimagefile(part[2],
                                                                              int(conf_dict['param']['nb_retry']),
                                                                              int(conf_dict['param']['wait_time']),
                                                                              part_path,
                                                                              chunk_size,
                                                                              part[1].lower())
                                            fulldisk = result[1]
                                            if result[0]:
                                                logger.info('Generating checksum md5…') 
                                                md5generated = misc_tools.generate_file_md5(os.path.dirname(part_path),
                                                                                            os.path.basename(part_path),
                                                                                            chunk_size)
                                                if md5generated.lower() == part[1].lower():
                                                    logger.info('The current product part has been successfully retrieved')
                                                    cur_part_status = 'checksum ok'
                                                else:
                                                    logger.warning('The current product part is corrupted')
                                                    cur_part_status = 'corrupted file'
                                            else:
                                                logger.warning('The current product part could not be retrieved.') 
                                                cur_part_status = 'corrupted file'
                                        else:
                                            logger.warning('The current product part has not been retrieved because the disk is full') 
                                            cur_part_status = 'corrupted file'
                                        xmlReport.removeElementEntry(report_part_path, part[0])
                                        xmlReport.addElementEntry(report_part_path, part[0],
                                                                  part[2], part[1],
                                                                  cur_part_status)
                                    count = xmlReport.statusFrequency(report_part_path)
                                    if (sum(count.values()) - count['checksum ok']) == 0:
                                        cur_prod_status = 'checksum ok'
                                    else:
                                        cur_prod_status = 'corrupted archive' 
                                else:
                                    logger.warning('Failed to retrieve the manifest.safe file')
                                    cur_prod_status = 'missing manifest'
                            else:
                                cur_prod_status = 'missing manifest'
                            #repeat code 3 end---------------------
                        elif element[4] == 'corrupted archive':
                            product_parts = xmlReport.readXmlPart(report_part_path)
                            product_parts = xmlReport.filterProductEntry(product_parts, 3)
                            #repeat code 4 begin--------------------- 
                            for i, part in enumerate(product_parts):
                                if not fulldisk:
                                    part_path = base_prod_path + part[0][1:]
                                    misc_tools.create_directory(os.path.dirname(part_path))
                                    logger.info('download %s out of %s\n file : %s'
                                                % (str(i+1), str(len(product_parts)), part_path))
                                    result = osodrequest.getimagefile(part[2],
                                                                      int(conf_dict['param']['nb_retry']),
                                                                      int(conf_dict['param']['wait_time']),
                                                                      part_path,
                                                                      chunk_size,
                                                                      part[1].lower())
                                    fulldisk = result[1]
                                    if result[0]:
                                        logger.info('Generating checksum md5…')
                                        md5generated = misc_tools.generate_file_md5(os.path.dirname(part_path),
                                                                                    os.path.basename(part_path),
                                                                                    chunk_size)
                                        if md5generated.lower() == part[1].lower():
                                            logger.info('The current product part has been successfully retrieved')
                                            cur_part_status = 'checksum ok'
                                        else:
                                            logger.warning('The current product part is corrupted')
                                            cur_part_status = 'corrupted file'
                                    else:
                                        logger.warning('The current product part could not be retrieved.') 
                                        cur_part_status = 'corrupted file'
                                else:
                                    logger.warning('The current product part has not been retrieved because the disk is full') 
                                    cur_part_status = 'corrupted file'
                                xmlReport.changeElementEntry(report_part_path, part[0],
                                                             'status', cur_part_status)
                            count = xmlReport.statusFrequency(report_part_path)
                            if (sum(count.values()) - count['checksum ok']) == 0:
                                cur_prod_status = 'checksum ok'
                            else:
                                cur_prod_status = 'corrupted archive'
                            #repeat code 4 end--------------------- 
                        else:
                            logger.debug('Problem past product. Unknown status.')
                            cur_prod_status = 'corrupted archive'
                        xmlReport.updateImageValue(report_path, element[1], 'status', cur_prod_status)
                    else: #entire product case
                        cur_dl_path_file = cur_dl_path_base + '/' + sat + '/' + element[5] + '/' + element[0] + ".zip"
                        misc_tools.create_directory(os.path.dirname(cur_dl_path_file))
                        logger.info('Current file path: %s'% cur_dl_path_file)
                        if element[4] == 'missing checksum':
                            #code reapeat 1 begin------------------------------
                            checksum_real = osodrequest.getmd5(element[2], int(conf_dict['param']['nb_retry']),
                                                               int(conf_dict['param']['wait_time']))
                            logger.debug('checksum_real value: %s'% str(checksum_real[0])) 
                            if checksum_real[0]:
                                xmlReport.updateImageValue(report_path, element[1], 'checksum', checksum_real[1]) 
                                #code reapeat 2 begin
                                if not fulldisk:
                                    logger.info('Downloading image %s to path: %s…'% (element[0], cur_dl_path_file))
                                    result = osodrequest.getimagefile(element[2],
                                                                      int(conf_dict['param']['nb_retry']),
                                                                      int(conf_dict['param']['wait_time']),
                                                                      cur_dl_path_file,
                                                                      chunk_size,
                                                                      checksum_real[1].lower())
                                    fulldisk = result[1]
                                    if result[0]:
                                        logger.info('Generating checksum md5…') 
                                        checksum_calculated = misc_tools.generate_file_md5(os.path.dirname(cur_dl_path_file),
                                                                                           os.path.basename(cur_dl_path_file),
                                                                                           blocksize=2**20)
                                        logger.debug('checksum calculated: %s'% checksum_calculated.lower())
                                        logger.debug('checksum real: %s'% checksum_real[1].lower())
                                        if (checksum_real[1].lower() == checksum_calculated.lower()):
                                            logger.info('The current product has been successfully retrieved')
                                            cur_prod_status = 'checksum ok'
                                        else:
                                            logger.warning('The current product part is corrupted') 
                                            cur_prod_status = 'corrupted archive'
                                    else:
                                        logger.warning('The current product could not be retrieved.')
                                        cur_prod_status = 'corrupted archive'
                                else:
                                    logger.warning('The current product has not been retrieved because the disk is full') 
                                    cur_prod_status = 'corrupted archive'
                                #code reapeat 2 end
                            else:
                                logger.warning('The checksum could not be retrived. Skipping to the next product')
                                cur_prod_status = 'missing checksum'
                            #code reapeat 1 end--------------------------------
                        elif element[4] == 'corrupted archive':
                            #code reapeat 2 begin
                            if not fulldisk:
                                logger.info('Downloading image %s to path: %s…'% (element[0], cur_dl_path_file)) 
                                result = osodrequest.getimagefile(element[2],
                                                                  int(conf_dict['param']['nb_retry']),
                                                                  int(conf_dict['param']['wait_time']),
                                                                  cur_dl_path_file,
                                                                  chunk_size,
                                                                  element[3].lower())
                                fulldisk = result[1]
                                if result[0]:
                                    logger.info('Generating checksum md5…')
                                    checksum_calculated = misc_tools.generate_file_md5(os.path.dirname(cur_dl_path_file),
                                                                                       os.path.basename(cur_dl_path_file),
                                                                                       blocksize=2**20)
                                    logger.debug('checksum calculated: %s'% checksum_calculated.lower())
                                    logger.debug('checksum real: %s'% element[3].lower())
                                    if (element[3].lower() == checksum_calculated.lower()):
                                        logger.info('The current product has been successfully retrieved')
                                        cur_prod_status = 'checksum ok'
                                    else:
                                        logger.warning('The current product part is corrupted')
                                        cur_prod_status = 'corrupted archive'
                                else:
                                    logger.warning('The current product could not be retrieved.')
                                    cur_prod_status = 'corrupted archive'
                            else:
                                logger.warning('The current product has not been retrieved because the disk is full') 
                                cur_prod_status = 'corrupted archive'
                            #code reapeat 2 end
                        else:
                            logger.debug('Problem past product. Unknown status.')
                            cur_prod_status = 'corrupted archive'
                        xmlReport.updateImageValue(report_path, element[1], 'status', cur_prod_status) 
            #-----------------------------------Retrieving new product---------------------------------#                   
            logger.info('Retrieving the number of product in the database for the current request…')                 
            result = osodrequest.getproductlist(urlrequest,
                                                int(conf_dict['param']['nb_retry']),
                                                int(conf_dict['param']['wait_time']),
                                                xml_product_path)
            if result == False:
                logger.warning('Failed to retrieve the number of product. The ' +
                               'server may be currently unavailable. Skipping to ' +
                               'the next request')
                logger.debug('request: %s'% urlrequest)
                continue
            numb_prod = xml_tools.getnumbprod(xml_product_path)
            logger.info('The total number of product for the current request is %s'% str(numb_prod))
            logger.info('Retrieving the entire list of products currently available in the scihub ' +
                        'database…')
            totalProduct = osodrequest.browseprod(urlrequest,
                                                  sat,
                                                  numb_prod,
                                                  int(conf_dict['param']['max_items']),
                                                  int(conf_dict['param']['nb_retry']),
                                                  int(conf_dict['param']['wait_time']),
                                                  xml_product_path)
            if not totalProduct:
                logger.warning('Failed to retrieve the list of product. The server may be ' +
                                'currently unavailable. Skipping to the next request')
                continue
            if sat != 'S1' and row[2].isdigit():
                totalProduct = misc_tools.cloudfilter(totalProduct, sat, int(row[2]))
                logger.info('Number of product corresponding to a cloud cover percentage of %s: %s'%
                            (row[2], str(len(totalProduct))))
            current_list = osodrequest.filternewproduct(past_prod_list, totalProduct)
            if not current_list:
                logger.info('No new products were found for the current request. Skipping to the next request.')
                continue
            else:
                logger.info('%s new product(s) were published for the current request.'% str(len(current_list)))
            for element in current_list:
                cur_prod_status = '' # ne devrais pas être nécessaire normalement d'initialiser les variables.
                cur_part_status = ''
                if (sat == 'S2') and ((row[3] != '') or (row[4] != '')):#tiles and/or bands case
                    bandsandtiles = misc_tools.extractBandsTiles(row[3], row[4])
                    logger.debug('type year: %s'% str(type(element[3])))
                    base_prod_path = cur_dl_path_base + '/' + sat + '/' + element[3] + '/' + element[0]
                    xml_manifest_path = base_prod_path + '/' + 'manifest.safe' + '.xml'
                    report_part_path = cur_dl_path_base + '/rep_' + element[0] + '.xml'
                    misc_tools.create_directory(os.path.dirname(xml_manifest_path))
                    xmlReport.createXml(report_part_path)
                    #repeat code 3 begin---------------------
                    if not fulldisk:
                        result = osodrequest.getmanifest(element[2], element[0],
                                                         int(conf_dict['param']['nb_retry']),
                                                         int(conf_dict['param']['wait_time']),
                                                         xml_manifest_path)
                        if result:
                            logger.info('Manifest.safe successfully retrieved')
                            logger.info('reading manifest file…') 
                            product_parts = manifestSafe.readmanifest(xml_manifest_path)
                            logger.info('Filtering elements of the product…')
                            size_before_filt = len(product_parts)
                            logger.info('Number of parts before filtering: %s'% str(size_before_filt))
                            product_parts = manifestSafe.filterelementS2(product_parts,
                                                                         bandsandtiles[0],
                                                                         bandsandtiles[1])
                            size_after_filt = len(product_parts)
                            logger.info('Number of parts after filtering: %s'% str(size_after_filt))
                            if size_before_filt == size_after_filt:
                                logger.info('No bands or tiles correspond to the specified bands and tiles ' +
                                            'for the current product')
                                continue
                            logger.info('Generating product parts uri…')
                            product_parts = manifestSafe.generateuri(product_parts,
                                                                     element[2],
                                                                     element[0])
                            #repeat code 4 begin--------------------- 
                            for i, part in enumerate(product_parts):
                                if not fulldisk:
                                    part_path = base_prod_path + part[0][1:]
                                    misc_tools.create_directory(os.path.dirname(part_path))
                                    logger.info('download %s out of %s\n file : %s'
                                                 % (str(i+1), str(len(product_parts)), part_path))
                                    result = osodrequest.getimagefile(part[2],
                                                                      int(conf_dict['param']['nb_retry']),
                                                                      int(conf_dict['param']['wait_time']),
                                                                      part_path,
                                                                      chunk_size,
                                                                      part[1].lower())
                                    fulldisk = result[1]
                                    if result[0]:
                                        md5generated = misc_tools.generate_file_md5(os.path.dirname(part_path),
                                                                                    os.path.basename(part_path),
                                                                                    chunk_size)
                                        if md5generated.lower() == part[1].lower():
                                            logger.info('The current product part has been successfully retrieved')
                                            cur_part_status = 'checksum ok'
                                        else:
                                            logger.warning('The current product part is corrupted')
                                            cur_part_status = 'corrupted file'
                                    else:
                                        logger.warning('The current product part could not be retrieved.') 
                                        cur_part_status = 'corrupted file'
                                else:
                                    logger.warning('The current product part has not been retrieved because the disk is full') 
                                    cur_part_status = 'corrupted file'
                                xmlReport.removeElementEntry(report_part_path, part[0]) # ensure there is not any duplicated entry
                                xmlReport.addElementEntry(report_part_path, part[0],
                                                          part[2], part[1],
                                                          cur_part_status)
                            count = xmlReport.statusFrequency(report_part_path)
                            if (sum(count.values()) - count['checksum ok']) == 0:
                                cur_prod_status = 'checksum ok'
                            else:
                                cur_prod_status = 'corrupted archive'
                            #repeat code 4 end--------------------- 
                        else:
                            logger.warning('Failed to retrieve the manifest.safe file')
                            cur_prod_status = 'missing manifest'
                    else:
                        cur_prod_status = 'missing manifest'
                    #repeat code 3 end---------------------
                    xmlReport.removeProductEntry(report_path, element[1]) # Make sure there is no duplicated entry
                    xmlReport.addProductEntry(report_path, element[0],
                                            element[1], element[2], cur_prod_status, 'not needed', element[3])
                else: #entire product case
                    cur_dl_path_file = cur_dl_path_base + '/' + sat + '/' + element[3] + '/' + element[0] + ".zip"
                    logger.info('Current file path: %s'% cur_dl_path_file)
                    misc_tools.create_directory(os.path.dirname(cur_dl_path_file))
                    #code reapeat 1 begin-------------------------------------
                    checksum_real = osodrequest.getmd5(element[2], int(conf_dict['param']['nb_retry']),
                                                       int(conf_dict['param']['wait_time']))
                    if checksum_real[0]:
                        #code reapeat 2 begin
                        if not fulldisk:
                            logger.info('Downloading image %s to path: %s…'% (element[0], cur_dl_path_file))
                            result = osodrequest.getimagefile(element[2],
                                                              int(conf_dict['param']['nb_retry']),
                                                              int(conf_dict['param']['wait_time']),
                                                              cur_dl_path_file,
                                                              chunk_size,
                                                              checksum_real[1].lower())
                            fulldisk = result[1]
                            if result[0]:  
                                checksum_calculated = misc_tools.generate_file_md5(os.path.dirname(cur_dl_path_file),
                                                                                   os.path.basename(cur_dl_path_file),
                                                                                   blocksize=2**20)
                                logger.debug('checksum calculated: %s'% checksum_calculated.lower())
                                logger.debug('checksum real: %s'% checksum_real[1].lower())
                                if (checksum_real[1].lower() == checksum_calculated.lower()):
                                    logger.info('The current product has been successfully retrieved')
                                    cur_prod_status = 'checksum ok'
                                else:
                                    logger.warning('The current product is corrupted') 
                                    cur_prod_status = 'corrupted archive'
                            else:
                                logger.warning('The current product could not be retrieved.')
                                cur_prod_status = 'corrupted archive'
                        else:
                            logger.warning('The current product has not been retrieved because the disk is full') 
                            cur_prod_status = 'corrupted archive'
                       #code reapeat 2 end 
                    else:
                        logger.warning('The checksum could not be retrived. Skipping to the next product')
                        cur_prod_status = 'missing checksum'
                    #code reapeat 1 end-----------------------------------------
                    xmlReport.removeProductEntry(report_path, element[1])
                    xmlReport.addProductEntry(report_path, element[0],
                                              element[1], element[2], cur_prod_status,
                                              checksum_real[1], element[3])
            xmlReport.updateRootValue(report_path, 'number_past_product', str(numb_prod))

#-----------------------------------execute main---------------------------------#    
try:
    main()
except Exception as e:
    logger.error('A problem occured')
    logger.error(traceback.format_exc())
else:
    logger.info('Everything ran fine')
finally:
    logger.info('End script')
