# -*- coding: utf-8 -*-
from lxml import etree
import sys

NSMAP = {None: 'http://www.w3.org/2005/Atom'}
#new_feed = etree.Element('feed', nsmap=NSMAP)
new_feed = etree.Element('feed')
entry = etree.SubElement(new_feed, 'entry')
print(type(entry))
id = etree.SubElement(entry, 'id')
id.text = '1'
titre = etree.SubElement(entry, 'titre')
titre.text = 'titre1'
entry = etree.SubElement(new_feed, 'entry')
print(etree.tounicode(new_feed))
id = etree.SubElement(entry, 'id')
id.text = '2'
titre = etree.SubElement(entry, 'titre')
titre.text = 'titre2'
print(etree.tounicode(new_feed))
print(etree.tounicode(new_feed, pretty_print=True))

f = open('out3.xml', 'w')
f.write(etree.tostring(new_feed, pretty_print=True))
f.close()

tree = etree.parse('out3.xml')
root = tree.getroot()
for element in root:
    print(element)


#modification d'une entrée dont l'id est 2
entre_id = "2"
entry = tree.xpath("/feed/entry[id=%s]/titre"% entre_id)
print(entry[0].text)
entry[0].text = 'nouveau titre'
print(entry[0].text)

f = open('out4.xml', 'w')
f.write(etree.tostring(tree, pretty_print=True))
f.close()

# Ajout d'une entrée
tree = etree.parse('out4.xml')
root = tree.getroot()
for element in root:
    print(element)
print(type(root))
new_entry = etree.SubElement(root, 'entry')
id = etree.SubElement(new_entry, 'id')
id.text = '3'
titre = etree.SubElement(new_entry, 'titre')
titre.text = 'titre3'

newKid = etree.Element('c-1', laugh="Hi!")
root.insert(0, newKid)


f = open('out5.xml', 'w')
f.write(etree.tostring(tree, pretty_print=True))
f.close()
#user = tree.xpath("/feed/title[id='1']")
#print(user.text)
#entry = tree.xpath("/feed/title[type='xml']")
#print (entry)


