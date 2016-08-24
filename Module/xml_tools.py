# -*- coding: utf-8 -*-

from lxml import etree # lxml sensé être plus rapide que les autres.
import os
import logging
import dateutil.parser as parser

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

# Définition d'un dictionnaire contanant les espaces de noms
# Attention à l'ordre du dictionnaire qui se retrouve inversé après enregistrement dans la variable ns
ns = {'os': 'http://a9.com/-/spec/opensearch/1.1/',
      'default': 'http://www.w3.org/2005/Atom'}

#-------------------------------getnumbprod-------------------------------#
def getnumbprod(xml_path):
    tree = etree.parse(xml_path)
    root = tree.getroot()
    element = root.find(ns.keys()[1]+':totalResults', ns)
    return int(element.text)

#-------------------------------getprodlist-------------------------------#
def getprodlist(xml_path, sat):
    prod_list = []
    entry_list = []
    tree = etree.parse(xml_path)
    root = tree.getroot()
    entries = root.findall(ns.keys()[0]+':entry', ns)
    for entry in entries:
        entry_list = []
        title = entry.find('default:title', ns)
        uuid = entry.find('default:id', ns)
        dl_link = entry.find('default:link', ns) # recherche da la première balise link. il y en a 3
        date = entry.find('{' + ns['default'] + '}' + "*[@name='beginposition']") 
        begindate = date.text
        logger.debug('begin date:%s'% begindate)
        begindate = parser.parse(begindate).year
        logger.debug('begin date:%s'% begindate)
        entry_list.extend([title.text, uuid.text, dl_link.get('href'), str(begindate)])
        if(sat == 'S2'):
            cloud = entry.find('{' + ns['default'] + '}' + "*[@name='cloudcoverpercentage']")
            entry_list.append(float(cloud.text))
        prod_list.append(entry_list)
    return prod_list

#-----------------------------------Test------------------------------------#

if __name__ == '__main__':
    module_path = os.path.dirname(os.path.realpath(__file__))
    base_path = os.path.dirname(module_path)
    xmlpath1 = base_path + "/testfile/test_S1.xml"
    xmlpath2 = base_path + "/testfile/test_S2.xml"

    # set test
    list_function = ['getnumbprod', 'getprodlist']
    test_function = [list_function[1]] # insert function(s) from list_function to test
    
    if(list_function[0] in test_function):
        print('#--------------test: %s--------------#'% list_function[0]) 
        totalnumprod = getnumbprod(xmlpath1)
        print(totalnumprod)
        print(type(totalnumprod))
        totalnumprod = getnumbprod(xmlpath2)
        print(totalnumprod)
        
    if(list_function[1] in test_function):
        print('#--------------test: %s--------------#'% list_function[1])
        prod_list = getprodlist(xmlpath1, 'S1')
        print(len(prod_list))
        for element in prod_list:
            print(element)

        prod_list = getprodlist(xmlpath2, 'S2')
        print(len(prod_list))
        for element in prod_list:
            print(element)
