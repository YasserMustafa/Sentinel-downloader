# -*- coding: utf-8 -*-
from lxml import etree
import sys

tree = etree.parse('test_gen.xml')
root = tree.getroot()


#modification d'une entrée dont l'id est 2
entre_id = "'0282b16c-310a-408b-aad6-546fh564uiu'"
print("/feed/entry[id=%s]/status"% entre_id)
entry = tree.xpath("/feed/entry[id=%s]/status"% entre_id)
print(entry)
print(entry[0].text)
#entry[0].text = 'nouveau titre'
#print(entry[0].text)

#f = open('out4.xml', 'w')
#f.write(etree.tostring(tree, pretty_print=True))
#f.close()

