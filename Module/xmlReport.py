# -*- coding: utf-8 -*-
"""This module contains functions to generate, update and read an xml files that
will contains informations about dowloaded product (uuid, title, dowload_link,
checkum, status, and cloudcoverpercentage) on element of a product (path,
download link, status, checksum). The status tag tell wether the
download was successful, corrupted.
"""

from lxml import etree
import os
import logging
from shutil import copyfile

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

#-----------------------------------createXml----------------------------------#
def createXml(xml_path):
    """Function that create an xml file that contains an empty root tag

    parameters:
        xml_path (string): Path of the xml file
        rootname (string): name of the root tag
    return:
        True if the file has been created or False if the file was already
        created.
    """
    created = False
    if os.path.isfile(xml_path) == False:
        new_feed = etree.Element('feed')
        f = open(xml_path, 'w')
        f.write(etree.tostring(new_feed, pretty_print=True))
        f.close()
        created = True
    return created

#--------------------------------addProductEntry---------------------------------#
def addProductEntry(xml_path, title, uuid, dl_link, status, checksum, year):
    """Function that append an image entry tag as a subelement of the root
    tag, to an existing xml file. An image entry is composed of different sub element
    describing the image.

    parameters:
        xml_path (string) : Path of the xml file
        title (string) : title of the image ex:'S2A_OPER_PRD_MSIL1C_PDMC_20160222T115941_R008_V20160218T104104_20160218T104104'
        uuid (string) : identifier of the image. ex: "0282b16c-310a-408b-aad6-85fdfa02a5da"
        dl_link (string) : download link of the image. ex: "https://scihub.copernicus.eu/dhus/odata/v1/Products('0282b16c-310a-408b-aad6-85fdfa02a5da')/$value"
        status (string) : current information about the image. 'corrupted', 'checksum ok',...
        checksum (string) : real checksum of the image.
        nuage (string) : Start sensing year
    """
    tree = etree.parse(xml_path)
    root = tree.getroot()
    new_entry = etree.SubElement(root, 'entry')
    titre = etree.SubElement(new_entry, 'title')
    titre.text = title
    uniqueid = etree.SubElement(new_entry, 'id')
    uniqueid.text = uuid
    url_dl = etree.SubElement(new_entry, 'link')
    url_dl.text = dl_link
    checkmd5 = etree.SubElement(new_entry, 'checksum')
    checkmd5.text = checksum
    status_bis = etree.SubElement(new_entry, 'status')
    status_bis.text = status
    startyear = etree.SubElement(new_entry, 'year')
    startyear.text = year
    f = open(xml_path, 'w')
    f.write(etree.tostring(tree, pretty_print=True))
    f.close()

#-------------------------------addInfoTag-------------------------------#
def addInfoTag(xml_path, position, tagname, value):
    """Function that add a specified tag to a specified position, right under the root tag.

    parameters:
        xml_path (string) : Path of the xml file
        position (int) : index specifing the position of the tag
        tagname (string) : name of the new tag to insert
        value (int) : value of the tag

    exemple:

    # Add the total number of product tag at the first position (right under the root tag). 
    xml_path = '/home/andrestumpf/Documents/scihub/projet_final/test.xml'
    position = 0
    tagname = 'numb_tot_prod'
    value = 20
    addInfoTag(xml_path, position, tagname, value)
    """
    tree = etree.parse(xml_path)
    root = tree.getroot()
    new_elem = etree.Element(tagname)
    new_elem.text = str(value)
    root.insert(position, new_elem)
    f = open(xml_path, 'w')
    f.write(etree.tostring(tree, pretty_print=True))
    f.close()

#---------------------------------changeStatus---------------------------------#
# Not used anymore, replaced by updateImageValue function
def changeStatus(xml_path, uuid, new_satus):
    """Function that modify the status tag of an image identified by its uuid.

    parameters:
        xml_path (string) : Path of the xml file
        uuid (string) : identifier of the image. ex: "0282b16c-310a-408b-aad6-85fdfa02a5da"
        new_status (string) : replace current status with new status
    """
    tree = etree.parse(xml_path)
    root = tree.getroot()
    comma = "'"
    status_element = tree.xpath("/feed/entry[id=%s%s%s]/status"% (comma, uuid, comma))
    status_element[0].text = new_status
    f = open(xml_path, 'w')
    f.write(etree.tostring(tree, pretty_print=True))
    f.close()

#-------------------------------------readXml----------------------------------#
def readXml(xml_path):
    """Function that read an xml end return the list of product.

    parameters:
        xml_path (string) : Path of the xml file

    return:
        prod_list (list) : List of list. The length of the list correspond to the number
        of image entry in the xml file. And each sublist contains the different tag values
        of an image entry.
    """
    prod_list = []
    tree = etree.parse(xml_path)
    root = tree.getroot()
    entries = root.findall('entry')
    for entry in entries:
        entry_list = []
        title = entry.find('title')
        uuid = entry.find('id')
        dl_link = entry.find('link')
        checksum = entry.find('checksum')
        status = entry.find('status')
        year = entry.find('year')
        entry_list.extend([title.text, uuid.text, dl_link.text, checksum.text, status.text, year.text])
        prod_list.append(entry_list)
    return prod_list

#-----------------------------filterProductEntry-------------------------------#
def filterProductEntry(prod_list, index):
    """Function that filters out product that have been downloaded without
    problems from a list.

    parameters:
        prod_list (list) : product list returned by the readXml function
        index (int) : position of the status value

    return:
        prod_list_filt (list) : filtered prod_list.
    """
    prod_list_filt = [elem for elem in prod_list if elem[index] != 'checksum ok']
    return prod_list_filt

#--------------------------------statusFrequency-------------------------------#
def statusFrequency(xml_path):
    """Function that count the frequency of the different status

    parameters:
        xml_path (string) : Path of the xml file

    return:
        count (dictionary): Countains the frequency of the different values of the
        satus tag.
    """
    count = {}
    tree = etree.parse(xml_path)
    root = tree.getroot()
    entries = root.findall('entry')
    for entry in entries:
        checksum = entry.find('status').text
        if checksum in count:
            count[checksum] += 1
        else:
            count[checksum] = 1  
    return count

#-------------------------------countNbImage-------------------------------#
#redondant avec statusFrequency, il est facile d'obtenir le nombre d'image
#a partir du dictionnaire
def countNbImage(xml_path):
    """Function that count the number of "entry" tag in an xml file. The
    number of entry represent either the number of product or the number of
    products elements depending on the considered xml file.

    parameters:
        xml_path (string) : Path of the xml file

    return:
        nbEntries (int): Number of image entries found in the xml file.
    """
    tree = etree.parse(xml_path)
    root = tree.getroot()
    entries = root.findall('entry')
    nbEntries = len(entries)
    return nbEntries

#-------------------------------imageExist-------------------------------#
def imageExist(xml_path, uuid):
    """Function that check if a specifique image exists in the xml file.

    parameters:
        xml_path (string) : Path of the xml file
        uuid (string) : identifier of the image.
        
    return:
        Boolean : True if exists, False otherwise
    """
    tree = etree.parse(xml_path)
    root = tree.getroot()
    comma = "'"
    status_element = tree.xpath("/feed/entry[id=%s%s%s]"% (comma, uuid, comma))
    if not status_element:
        exist = False
    else:
        exist = True 
    return exist

#-------------------------------updateImageValue-------------------------------#
def updateImageValue(xml_path, uuid, tag, new_value):
    """Function that modify a tag of an image identified by its uuid.

    parameters:
        xml_path (string) : Path of the xml file
        uuid (string) : identifier of the image. ex: "0282b16c-310a-408b-aad6-85fdfa02a5da"
        tag (string): name of the tag
        new_value (string) : new value to assign to the tag
    """
    tree = etree.parse(xml_path)
    root = tree.getroot()
    comma = "'"
    tag_element = tree.xpath("/feed/entry[id=%s%s%s]/%s"% (comma, uuid, comma, tag))
    tag_element[0].text = new_value
    f = open(xml_path, 'w')
    f.write(etree.tostring(tree, pretty_print=True))
    f.close()

#---------------------------------readTagValue---------------------------------#
def readTagValue(xml_path, tag):
    """Function that read a children's root tag value 

    parameters:
        xml_path (string) : Path of the xml file
        tag (string): name of the tag 

    return:
         the value of the specified tag
    """
    tree = etree.parse(xml_path)
    tag_element = tree.xpath("/feed/%s"% tag)
    tag_value = tag_element[0].text
    return tag_value

#--------------------------------addElementEntry-------------------------------#
def addElementEntry(xml_path, path, dl_link, checksum, status):
    """Function that add an element entry to an xml file right under the root
    tag. This fonction is used to create a list of dowloaded file with their
    status in the case where tiles or bands filters are specified in the
    request.cvs.

    parameters:
        xml_path (string) : Path of the xml file
        path (string): relative path of an element
        dl_link (string) : download link of the image element.
        status (string) : current information about the image. 'corrupted', 'checksum ok'.
        checksum (string) : real checksum of the product element.
    """
    tree = etree.parse(xml_path)
    root = tree.getroot()
    # Create new entry under the root tag
    new_entry = etree.SubElement(root, 'entry')
    # Add path to new_entry
    pathdir = etree.SubElement(new_entry, 'path')
    pathdir.text = path
    # Add dl_link to new_entry
    url_dl = etree.SubElement(new_entry, 'link')
    url_dl.text = dl_link
    # Add the real checksum to new_entry
    checkmd5 = etree.SubElement(new_entry, 'checksum')
    checkmd5.text = checksum
    # Add status to new_entry
    status_bis = etree.SubElement(new_entry, 'status')
    status_bis.text = status
    # Save new tree
    f = open(xml_path, 'w')
    f.write(etree.tostring(tree, pretty_print=True))
    f.close()

#-------------------------------updateRootValue-------------------------------#
def updateRootValue(xml_path, tag, new_value):
    """Function that modify a children root tag.

    parameters:
        xml_path (string) : Path of the xml file
        tag (string): name of the tag
        new_value (string) : new value to assign to the tag
    """
    tree = etree.parse(xml_path)
    comma = "'"
    tag_element = tree.xpath("/feed/%s"% tag)
    tag_element[0].text = new_value
    f = open(xml_path, 'w')
    f.write(etree.tostring(tree, pretty_print=True))
    f.close()

#-------------------------------------readXmlPart----------------------------------#
def readXmlPart(xml_path):
    """Function that read an xml end return the list of product's elements.

    parameters:
        xml_path (string) : Path of the xml file
    return:
        prod_list (list) : List of list. The length of the list correspond to the number
        of image entry in the xml file. And each sublist contains the different tag values
        of an image entry.
    """
    prod_list = []
    tree = etree.parse(xml_path)
    root = tree.getroot()
    entries = root.findall('entry')
    logger.debug('number of entries: %s'% str(len(entries)))
    for entry in entries:
        entry_list = []
        path = entry.find('path')
        dl_link = entry.find('link')
        checksum = entry.find('checksum')
        status = entry.find('status')
        entry_list.extend([path.text, checksum.text, dl_link.text, status.text])
        prod_list.append(entry_list)
    return prod_list

#--------------------------------changeElementEntry-------------------------------#
def changeElementEntry(xml_path, path, tag, new_value):
    """Function that modifie a children tag entry of a product part based on his
    relative path. The main goal of this function is to modify the status tag of
    a product part in case the user have specified bands and/or tiles to retrieve
    for S2.

    parameters:
        xml_path (string) : Path of the xml file
        path (string): relative path of an element
        tag (string): name of the tag, exemple: 'status'
        new_value (string) : new value to assign to the tag, exemple: 'checksum ok'
    """
    tree = etree.parse(xml_path)
    comma = "'"
    tag_element = tree.xpath("/feed/entry[path=%s%s%s]/%s"% (comma, path, comma, tag))
    tag_element[0].text = new_value
    f = open(xml_path, 'w')
    f.write(etree.tostring(tree, pretty_print=True))
    f.close()

#--------------------------------removeProductEntry-------------------------------#
def removeProductEntry(xml_path, uuid):
    """This function remove a product entry based on its uuid

    parameters:
        xml_path (string) : Path of the xml file
        path (string): relative path of an element
        uuid (string): unique identifier of the object
    """
    tree = etree.parse(xml_path)
    comma = "'"
    element = tree.xpath("/feed/entry[id=%s%s%s]"% (comma, uuid, comma))
    logger.debug('type: %s'% str(type(element)))
    logger.debug('size: %s'% str(len(element)))
    for elem in element:
        elem.getparent().remove(elem)
    f = open(xml_path, 'w')
    f.write(etree.tostring(tree, pretty_print=True))
    f.close()

#--------------------------------removeElementEntry-------------------------------#
def removeElementEntry(xml_path, path):
    """This function remove an element (product part) entry based on its path

    parameters:
        xml_path (string) : Path of the xml file
        path (string): relative path of the element to remove
    """
    tree = etree.parse(xml_path)
    comma = "'"
    element = tree.xpath("/feed/entry[path=%s%s%s]"% (comma, path, comma))
    logger.debug('type: %s'% str(type(element)))
    logger.debug('size: %s'% str(len(element)))
    for elem in element:
        elem.getparent().remove(elem)
    f = open(xml_path, 'w')
    f.write(etree.tostring(tree, pretty_print=True))
    f.close()


#-----------------------------------Test------------------------------------#
if __name__ == '__main__':
    # Récupération du chemin du fichier requête xml de test
    module_path = os.path.dirname(os.path.realpath(__file__))
    base_path = os.path.dirname(module_path)
    xmlpath = base_path + "/testfile/test_gen.xml"

    # Some variable
    sat = 'S2'
    title = 'S2A_OPER_PRD_MSIL1C_PDMC_20160222T115941_R008_V20160218T104104_20160218T104104'
    uuid = "0282b16c-310a-408b-aad6-85fdfa02a5da"
    dl_link = "https://scihub.copernicus.eu/dhus/odata/v1/Products('0282b16c-310a-408b-aad6-85fdfa02a5da')/$value"
    status = "checksum ok"
    checksum = "0au365ert51usp4s"
    uuid2 = "0282b16c-310a-408b-aad6-546fh564uiu"
    xmlReportParts1 = base_path + "/testfile/rep_S2A_OPER_PRD_MSIL1C_PDMC_20151230T202002_R008_V20151230T105153_20151230T105153.xml"
    xmlReportParts2 = base_path + "/testfile/rep_S2A_OPER_PRD_MSIL1C_PDMC_20160103T212851_R065_V20160103T103320_20160103T103320.xml"
    xmlReportGlobal = base_path + "/testfile/rep_Barce_S2.xml"

    # set test
    list_function = ['createXml', 'addProductEntry', 'addInfoTag', 'changeStatus', 'readXml',
                     'filterProductEntry', 'statusFrequency', 'countNbImage', 'imageExist',
                     'updateImageValue', 'readTagValue', 'addElementEntry',
                     'updateRootValue', 'readXmlPart', 'changeElementEntry',
                     'removeProductEntry', 'removeElementEntry']
    test_function = [list_function[16]] # insert function(s) from list_function to test

    if(list_function[0] in test_function):
        print('#--------------test: %s--------------#'% list_function[0])
        if os.path.isfile(xmlpath):
            os.remove(xmlpath)
        valeur = createXml(xmlpath)
        print 'fichier crée: ', valeur
        valeur = createXml(xmlpath)
        print 'fichier crée: ', valeur

    if(list_function[1] in test_function):
        print('#--------------test: %s--------------#'% list_function[1])
        if os.path.isfile(xmlpath):
            os.remove(xmlpath)
        valeur = createXml(xmlpath)
        print 'fichier crée: ', valeur
        addProductEntry(xmlpath, title, uuid, dl_link, status, checksum, str(2015))
        addProductEntry(xmlpath, title, uuid2, dl_link, status, checksum, str(2016))

    if(list_function[2] in test_function):
        print('#--------------test: %s--------------#'% list_function[2])
        if os.path.isfile(xmlpath):
            os.remove(xmlpath)
        valeur = createXml(xmlpath)
        print 'fichier crée: ', valeur
        addProductEntry(xmlpath, title, uuid, dl_link, status, checksum, str(2015))
        addProductEntry(xmlpath, title, uuid2, dl_link, status, checksum, str(2016))
        addInfoTag(xmlpath, 0, 'NumbTotProd', 25)

    if(list_function[3] in test_function):
        print('#--------------test: %s--------------#'% list_function[3])
        if os.path.isfile(xmlpath):
            os.remove(xmlpath)
        valeur = createXml(xmlpath)
        print 'fichier crée: ', valeur
        addProductEntry(xmlpath, title, uuid, dl_link, status, checksum, str(2015))
        addProductEntry(xmlpath, title, uuid2, dl_link, status, checksum, str(2016))
        addInfoTag(xmlpath, 0, 'NumbTotProd', 25)
        new_status = 'corrompu'
        changeStatus(xmlpath, uuid2, new_status)

    if(list_function[4] in test_function):
        print('#--------------test: %s--------------#'% list_function[4])
        if os.path.isfile(xmlpath):
            os.remove(xmlpath)
        valeur = createXml(xmlpath)
        print 'fichier crée: ', valeur
        addProductEntry(xmlpath, title, uuid, dl_link, status, checksum, str(2015))
        addProductEntry(xmlpath, title, uuid2, dl_link, status, checksum, str(2016))
        addInfoTag(xmlpath, 0, 'NumbTotProd', 25)
        new_status = 'corrompu'
        changeStatus(xmlpath, uuid2, new_status)
        prod = readXml(xmlpath)
        #print(len(prod))
        #print(prod)
        for element in prod:
            print(element)

    if(list_function[5] in test_function):
        print('#--------------test: %s--------------#'% list_function[5])
        if os.path.isfile(xmlpath):
            os.remove(xmlpath)
        valeur = createXml(xmlpath)
        print 'fichier crée: ', valeur
        addProductEntry(xmlpath, title, uuid, dl_link, status, checksum, str(2015))
        addProductEntry(xmlpath, title, uuid2, dl_link, status, checksum, str(2016))
        addInfoTag(xmlpath, 0, 'NumbTotProd', 25)
        new_status = 'corrompu'
        changeStatus(xmlpath, uuid2, new_status)
        prod = readXml(xmlpath)
        print 'taille liste avant: ', len(prod)
        for element in prod:
            print(element)
        prod_filt = filterProductEntry(prod, 4)
        print 'taille liste après: ', len(prod_filt)
        for element in prod_filt:
            print(element)

    if(list_function[6] in test_function):
        print('#--------------test: %s--------------#'% list_function[6])
        if os.path.isfile(xmlpath):
            os.remove(xmlpath)
        valeur = createXml(xmlpath)
        print 'fichier crée: ', valeur
        addProductEntry(xmlpath, 'image1', '1a', dl_link, 'checksum ok', checksum, str(2016))
        addProductEntry(xmlpath, 'image2', '1b', dl_link, 'corrompu', checksum, str(2016))
        addProductEntry(xmlpath, 'image3', '1c', dl_link, 'checksum ok', checksum, str(2016))
        addProductEntry(xmlpath, 'image4', '1d', dl_link, 'incomplet', checksum, str(2016))
        addInfoTag(xmlpath, 0, 'NumbTotProd', 25)
        count = statusFrequency(xmlpath)
        prod = readXml(xmlpath)
        for element in prod:
            print(element)
        print(count)
        print(sum(count.values()) - count['checksum ok'])

    if(list_function[7] in test_function):
        print('#--------------test: %s--------------#'% list_function[7])
        if os.path.isfile(xmlpath):
            os.remove(xmlpath)
        valeur = createXml(xmlpath)
        print 'fichier crée: ', valeur
        addProductEntry(xmlpath, 'image1', '1a', dl_link, 'checksum ok', checksum, str(2016))
        addProductEntry(xmlpath, 'image2', '1b', dl_link, 'corrompu', checksum, str(2016))
        addProductEntry(xmlpath, 'image3', '1c', dl_link, 'checksum ok', checksum, str(2016))
        addProductEntry(xmlpath, 'image4', '1d', dl_link, 'incomplet', checksum, str(2016))
        addInfoTag(xmlpath, 0, 'NumbTotProd', 25)
        count = statusFrequency(xmlpath)
        print(count)
        nb = countNbImage(xmlpath)
        print('number of image: %s'% nb)

    if(list_function[8] in test_function):
        print('#--------------test: %s--------------#'% list_function[8])
        if os.path.isfile(xmlpath):
            os.remove(xmlpath)
        valeur = createXml(xmlpath)
        print 'fichier crée: ', valeur
        addProductEntry(xmlpath, 'image1', '1a', dl_link, 'checksum ok', checksum, str(2016))
        addProductEntry(xmlpath, 'image2', '1b', dl_link, 'corrompu', checksum, str(2016))
        addProductEntry(xmlpath, 'image3', '1c', dl_link, 'checksum ok', checksum, str(2016))
        addProductEntry(xmlpath, 'image4', '1d', dl_link, 'incomplet', checksum, str(2016))
        addInfoTag(xmlpath, 0, 'NumbTotProd', 25)
        result = imageExist(xmlpath, '1b')
        print 'exist ?: ', result
        result = imageExist(xmlpath, '1att')
        print 'exist ?: ', result

    if(list_function[9] in test_function):
        print('#--------------test: %s--------------#'% list_function[9])
        if os.path.isfile(xmlpath):
            os.remove(xmlpath)
        valeur = createXml(xmlpath)
        print 'fichier crée: ', valeur
        addProductEntry(xmlpath, title, uuid, dl_link, status, checksum, str(2015))
        addProductEntry(xmlpath, title, uuid2, dl_link, status, checksum, str(2016))
        addInfoTag(xmlpath, 0, 'NumbTotProd', 25)
        new_value = 'corrompu'
        tag = 'status'
        updateImageValue(xmlpath, uuid2, tag, new_value)

    if(list_function[10] in test_function):
        print('#--------------test: %s--------------#'% list_function[10])
        if os.path.isfile(xmlpath):
            os.remove(xmlpath)
        valeur = createXml(xmlpath)
        print 'fichier crée: ', valeur
        addProductEntry(xmlpath, title, uuid, dl_link, status, checksum, str(2015))
        addProductEntry(xmlpath, title, uuid2, dl_link, status, checksum, str(2016))
        addInfoTag(xmlpath, 0, 'NumbTotProd', 25)
        nb = readTagValue(xmlpath, 'NumbTotProd')
        print(nb)

    if(list_function[11] in test_function):
        print('#--------------test: %s--------------#'% list_function[11])
        path1 = '/S2A_OPER_PRD_MSIL1C_PDMC_20160222T115941_R008_V20160218T104104_20160218T104104/DATASTRIP/S2A_OPER_MSI_L1C_DS_SGS__20160218T171004_S20160218T104104_N02.01/S2A_OPER_MTD_L1C_DS_SGS__20160218T171004_S20160218T104104.xml'
        path2 = '/S2A_OPER_PRD_MSIL1C_PDMC_20160222T115941_R008_V20160218T104104_20160218T104104/HTML/UserProduct_index.xsl'
        if os.path.isfile(xmlpath):
            os.remove(xmlpath)
        valeur = createXml(xmlpath)
        print 'fichier crée: ', valeur
        addElementEntry(xmlpath, path1, dl_link, checksum, status)
        addElementEntry(xmlpath, path2, dl_link, checksum, status)
        
    if(list_function[12] in test_function):
        print('#--------------test: %s--------------#'% list_function[12])
        if os.path.isfile(xmlpath):
            os.remove(xmlpath)
        valeur = createXml(xmlpath)
        print 'fichier crée: ', valeur
        addProductEntry(xmlpath, title, uuid, dl_link, status, checksum, str(2015))
        addProductEntry(xmlpath, title, uuid2, dl_link, status, checksum, str(2016))
        addInfoTag(xmlpath, 0, 'NumbTotProd', 25)
        updateRootValue(xmlpath, 'NumbTotProd', str(30))

    if(list_function[13] in test_function):
        print('#--------------test: %s--------------#'% list_function[13])
        print(xmlReportParts1)
        print(xmlReportParts2)
        res1 = readXmlPart(xmlReportParts1)
        res2 = readXmlPart(xmlReportParts2)
        print(res1)
        print(res2)

    if(list_function[14] in test_function):
        print('#--------------test: %s--------------#'% list_function[14])
        dst = os.path.dirname(xmlReportParts2)+ '/rep_copie.xml'
        copyfile(xmlReportParts2, dst)
        relpath = './GRANULE/S2A_OPER_MSI_L1C_TL_SGS__20160103T174751_A002779_T32TLQ_N02.01/QI_DATA/S2A_OPER_MSK_DETFOO_SGS__20160103T174751_A002779_T32TLQ_B04_MSIL1C.gml'
        tag = 'status'
        new_value = 'blabla'
        changeElementEntry(dst, relpath, tag, new_value)

    if(list_function[15] in test_function):
        print('#--------------test: %s--------------#'% list_function[15])
        dst = os.path.dirname(xmlReportGlobal)+ '/rep_Barce_S2_copie.xml'
        copyfile(xmlReportGlobal, dst)
        removeProductEntry(dst, 'e1dd5195-9221-4dee-ab27-12da7477a6cc')
        removeProductEntry(dst, 'aaa')

    if(list_function[16] in test_function):
        print('#--------------test: %s--------------#'% list_function[16])
        dst = os.path.dirname(xmlReportParts2)+ '/rep_copie1.xml'
        copyfile(xmlReportParts2, dst)
        relpath = './GRANULE/S2A_OPER_MSI_L1C_TL_SGS__20160103T174751_A002779_T32TLQ_N02.01/QI_DATA/S2A_OPER_MSK_DETFOO_SGS__20160103T174751_A002779_T32TLQ_B04_MSIL1C.gml'
        removeElementEntry(dst, relpath)
