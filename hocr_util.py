import xml.etree.ElementTree as ET
import re
import json


def main():
    return

def getPageCoords(node):
    return getTitle(node).split("bbox ")[1].split(";")[0].split(" ")

def getBoundingBox(node):
    return re.findall(r'\d+', getTitle(node))


def getText(node):
    if('class' in getAttrib(node)):
        if(getClass(node) == 'ocrx_word'):
            for child in node.iter():
                if(child.tag.endswith("em")):
                    return child.text
            return node.text

def getId(node):
    return getAttrib(node)['id']


def getClass(node):
    return getAttrib(node)['class']


def getTitle(node):
    return getAttrib(node)['title']


def getAttrib(node):
    return node.attrib


if __name__ == "__main__":
    main()
