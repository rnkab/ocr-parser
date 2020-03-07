import os
import xml.etree.ElementTree as ET
import re
import json
from hocr_objects import Word
from hocr_objects import LineObject
import hocr_util
from flask import Flask, request, jsonify, Response

app = Flask(__name__)
port = int(os.environ.get('PORT', 3000))

@app.route('/', methods=['GET', 'POST'])
def index():
    return "Use parseOCR for parsing"

@app.route('/parseFormOCR', methods=['GET','POST'])
def parseFormOCR():
    #assuming form with key values in single line. Can be enhanced to merge lines with specific horizontal distances later.
    params = request.form
    hOCR = params.get('hocr')
    keys = params.get('keys')

    if(not(hOCR) or not(len(hOCR) > 0)):
        return Response(json.dumps({'Error': 'No hOCR input'}), status=400, mimetype="application/json")

    if(not(keys) or not(len(keys) > 0)):
        return Response(json.dumps({'Error': 'No bounding box input'}), status=400, mimetype="application/json")

    tree = ET.fromstring(hOCR)
    # tree = ET.fromstring(getTxtForFormParsing())

    pageCoords = getPageCoords(tree)
    lines = parseLines(tree)


    parsed_output = {"data":[]}  
    bbData = json.loads(keys)
    # bbData = getKeys()

    linesForKeys = {}

    for key in bbData['data']:
        key = key['key']
        lineForKey = getLineforKey(lines, key)
        if(lineForKey):
            linesForKeys[key] = lineForKey
        else:
            linesForKeys[key] = None

    parsed_output['data'] = prepareResponse(linesForKeys)
    parsed_output['pageCoords'] = pageCoords
    
    return jsonify(parsed_output)

@app.route('/parseBBoxOCR', methods=['GET','POST'])
def parseBBoxOCR():
    # Parse HOCR with key value bbox values
    params = request.form
    hOCR = params.get('hocr')
    bbox = params.get('bbox')

    if(not(hOCR) or not(len(hOCR) > 0)):
        return Response(json.dumps({'Error': 'No hOCR input'}), status=400, mimetype="application/json")

    if(not(bbox) or not(len(bbox) > 0)):
        return Response(json.dumps({'Error': 'No bounding box input'}), status=400, mimetype="application/json")

    tree = ET.fromstring(hOCR)

    pageCoords = getPageCoords(tree)
    lines = parseLines(tree)

    parsed_output = {"data":[]}  
    bbData = json.loads(bbox)

    elemData = {}
    for region in bbData['regions']:
        bbox_key_posLeft = region['key']['boundingBox']['posLeft']
        bbox_key_posTop = region['key']['boundingBox']['posTop']
        bbox_key_posRight = region['key']['boundingBox']['posRight']
        bbox_key_posBottom = region['key']['boundingBox']['posBottom']

        bbox_value_posLeft = region['value']['boundingBox']['posLeft']
        bbox_value_posTop = region['value']['boundingBox']['posTop']
        bbox_value_posRight = region['value']['boundingBox']['posRight']
        bbox_value_posBottom = region['value']['boundingBox']['posBottom']

        region_id = region['id']

        linesinBB_Key = getLinesinBB(lines, bbox_key_posLeft, bbox_key_posTop, bbox_key_posRight, bbox_key_posBottom)
        linesinBB_Value = getLinesinBB(lines, bbox_value_posLeft, bbox_value_posTop, bbox_value_posRight, bbox_value_posBottom)

        elemData[region_id] = {}
        elemData[region_id]['key'] = {}
        elemData[region_id]['value'] = {}

        elemData[region_id]['key']['text'] = getElementValuefromBB(linesinBB_Key, bbox_key_posLeft, bbox_key_posTop, bbox_key_posRight, bbox_key_posBottom)
        elemData[region_id]['key']['posLeft'] = bbox_key_posLeft
        elemData[region_id]['key']['posTop'] = bbox_key_posTop
        elemData[region_id]['key']['posRight'] = bbox_key_posRight
        elemData[region_id]['key']['posBottom'] = bbox_key_posBottom

        elemData[region_id]['value']['text'] = getElementValuefromBB(linesinBB_Value, bbox_value_posLeft, bbox_value_posTop, bbox_value_posRight, bbox_value_posBottom)
        elemData[region_id]['value']['posLeft'] = bbox_value_posLeft
        elemData[region_id]['value']['posTop'] = bbox_value_posTop
        elemData[region_id]['value']['posRight'] = bbox_value_posRight
        elemData[region_id]['value']['posBottom'] = bbox_value_posBottom
        
        # parsed_output['data'].append(elemData)
        
    # writeToFile("output.txt", value, 'w+')
    parsed_output['data'] = elemData
    parsed_output['pageCoords'] = pageCoords
    writeJSONToFile("output.txt", parsed_output)
    return jsonify(parsed_output)

@app.route('/parseOCR', methods=['GET','POST'])
def parseOCR():
    # Parse HOCR with key value bbox values
    params = request.form
    hOCR = params.get('hocr')
    bbox = params.get('bbox')

    if(not(hOCR) or not(len(hOCR) > 0)):
        return Response(json.dumps({'Error': 'No hOCR input'}), status=400, mimetype="application/json")

    if(not(bbox) or not(len(bbox) > 0)):
        return Response(json.dumps({'Error': 'No bounding box input'}), status=400, mimetype="application/json")

    tree = ET.fromstring(hOCR)
    lines = parseLines(tree)

    parsed_output = {"data":[]}  
    bbData = json.loads(bbox)

    for region in bbData['regions']:
        bbox_key_posLeft = region['key']['boundingBox']['posLeft']
        bbox_key_posTop = region['key']['boundingBox']['posTop']
        bbox_key_posRight = region['key']['boundingBox']['posRight']
        bbox_key_posBottom = region['key']['boundingBox']['posBottom']

        bbox_value_posLeft = region['value']['boundingBox']['posLeft']
        bbox_value_posTop = region['value']['boundingBox']['posTop']
        bbox_value_posRight = region['value']['boundingBox']['posRight']
        bbox_value_posBottom = region['value']['boundingBox']['posBottom']

        region_id = region['id']

        linesinBB_Key = getLinesinBB(lines, bbox_key_posLeft, bbox_key_posTop, bbox_key_posRight, bbox_key_posBottom)
        linesinBB_Value = getLinesinBB(lines, bbox_value_posLeft, bbox_value_posTop, bbox_value_posRight, bbox_value_posBottom)

        elemData = {}
        elemData['id'] = region_id
        elemData['key'] = getElementValuefromBB(linesinBB_Key, bbox_key_posLeft, bbox_key_posTop, bbox_key_posRight, bbox_key_posBottom)
        elemData['value'] = getElementValuefromBB(linesinBB_Value, bbox_value_posLeft, bbox_value_posTop, bbox_value_posRight, bbox_value_posBottom)

        parsed_output['data'].append(elemData)
        
    # writeToFile("output.txt", value, 'w+')
    writeJSONToFile("output.txt", parsed_output)
    return jsonify(parsed_output)

def getBBData():
    with open('bbox.json') as json_file:
        data = json.load(json_file)
    
    return data

def writeToFile(path, text, mode='a'):
    f = open(path, mode)
    f.write(text)

def writeJSONToFile(path, data):
    with open(path, 'w') as f:
        json.dump(data, f)

def getLineforKey(lines, key):
    foundLine = None
    for line in lines:
        wordConcat = ' '
        wordTextArray = []
        words = line.words
        for word in words:
            wordTextArray.append(word.text)
        wordConcat = wordConcat.join(wordTextArray)
        line.lineText = wordConcat
        if(wordConcat.find(key) == 0):
            foundLine = line
            break
    return foundLine

def prepareResponse(linesForKeys):
    result = {}

    for key in linesForKeys:
        #result = {}
        result[key] = {}
        result[key]['value'] = {}
        keyText = ''
        valueText = ''
        foundKey = False
        line = linesForKeys[key]
        result[key]['posTop'] = line.posTop
        result[key]['posBottom'] = line.posBottom
        result[key]['value']['posTop']=line.posTop
        result[key]['value']['posBottom'] = line.posBottom
        result[key]['value']['posLeft'] = None
        result[key]['value']['posRight'] = None

        words = line.words

        for i in range(len(words)):
            if(i == 0):
                keyText = words[i].text
                result[key]['posLeft'] = words[i].posLeft
            elif(i>0 and not(foundKey)):
                keyText = keyText + ' ' + words[i].text
                result[key]['posRight'] = words[i].posRight
            elif(i>0 and foundKey):
                if(not(result[key]['value']['posLeft'])):
                    result[key]['value']['posLeft'] = words[i].posLeft
                valueText = valueText + ' ' + words[i].text
                result[key]['value']['posRight']=words[i].posRight

            if(not(foundKey) and (len(keyText) >= len(key)) and (keyText.find(key) == 0)):
                result[key]['posRight'] = words[i].posRight
                foundKey = True
                continue

        if(foundKey):
            result[key]['text']=keyText
            result[key]['value']['text']=valueText.strip()

        #responseData.append(result)

    return result

def getPageCoords(tree):
    pageCoordObject = {}
    pagecoords = None
    for node in tree.iter():
        if('class' in node.attrib):
            cl = hocr_util.getClass(node)
            if(cl == "ocr_page"):
                pagecoords = hocr_util.getPageCoords(node)
                break
    
    if pagecoords:
        pageCoordObject['posLeft'] = pagecoords[0]
        pageCoordObject['posTop'] = pagecoords[1]
        pageCoordObject['posRight'] = pagecoords[2]
        pageCoordObject['posBottom'] = pagecoords[3]

    return pageCoordObject

def parseLines(tree):
    """
    create Line objects from the ocr output
    """
    lines = []
    for node in tree.iter():
        if('class' in node.attrib):
            cl = hocr_util.getClass(node)
            if(cl == "ocr_line"):
                line_id = hocr_util.getId(node)
                bbox = hocr_util.getBoundingBox(node)
                line = LineObject(line_id, bbox[0], bbox[1], bbox[2], bbox[3])
                children = node.getchildren()
                for child in children:
                    if('class' in child.attrib):
                        cl = hocr_util.getClass(child)
                        if(cl == "ocrx_word"):
                            text = hocr_util.getText(child)
                            bbox = hocr_util.getBoundingBox(child)
                            word = Word(text, bbox[0], bbox[1], bbox[2], bbox[3])
                            line.addWord(word)
                lines.append(line)
    return lines

def getWordsinBB(tree, BBOX_LEFT, BBOX_TOP, BBOX_RIGHT, BBOX_BOTTOM):
    """
    get all the words from the ocr output within the BBox
    """
    words = []
    for node in tree.iter():
        if('class' in node.attrib):
            cl = hocr_util.getClass(node)
            if(cl == "ocrx_word"):
                text = hocr_util.getText(node)
                bbox = hocr_util.getBoundingBox(node)
                if(int(bbox[0]) >= BBOX_LEFT and int(bbox[1]) >= BBOX_TOP and int(bbox[2]) <= BBOX_RIGHT and int(bbox[3]) <= BBOX_BOTTOM):
                    word = Word(text, bbox[0], bbox[1], bbox[2], bbox[3])
                    words.append(word)
    return words

def getLinesinBB(lines, BBOX_LEFT, BBOX_TOP, BBOX_RIGHT, BBOX_BOTTOM):
    """
    get all the lines which fall within the BBox
    """
    linesinBB = []
    for i in range(len(lines)):
        curLine = lines[i]
        if(curLine.posTop >= BBOX_TOP and curLine.posBottom <= BBOX_BOTTOM):
            linesinBB.append(curLine)
    return linesinBB

def getElementValuefromBB(linesinBB, BBOX_LEFT, BBOX_TOP, BBOX_RIGHT, BBOX_BOTTOM):
    """
    get all the lines which fall within the BBox
    """
    elementValue = ''
    foundWord = False
    for i in range(len(linesinBB)):
        curLine = linesinBB[i]
        for j in range(len(curLine.words)):
            curWord = curLine.words[j]
            if(curWord.posLeft >= BBOX_LEFT and curWord.posRight <= BBOX_RIGHT):
                elementValue += curWord.text + ' '
                foundWord = True
        if(foundWord):
            foundWord = False
            elementValue += '\n'
    return elementValue

def getKeys():
    with open('keys.json') as keys_file:
        keys = json.load(keys_file)
    return keys

def getTxtForFormParsing():
    """
    Will give example text from ocr output. ocr output needs to be modified slightly, so I just copied fixed versions below for testing.
    """
    txt = '''
        <html:html xmlns:html=\"http://www.w3.org/1999/xhtml\" lang=\"en\" xml:lang=\"en\">\n <html:head>\n  <html:title />\n<html:meta content=\"text/html;charset=utf-8\" http-equiv=\"Content-Type\" />\n  <html:meta content=\"tesseract 4.0.0\" name=\"ocr-system\" />\n  <html:meta content=\"ocr_page ocr_carea ocr_par ocr_line ocrx_word ocrp_wconf\" name=\"ocr-capabilities\" />\n</html:head>\n<html:body>\n  <html:div class=\"ocr_page\" id=\"page_1\" rotation=\"0\" title=\"image &quot;/tmp/c02c3bab-0ab4-47c9-9241-812fac3d3cae0/Columbus_Laminate_COA_for_Batch_193430454_page_11.png&quot;; bbox 0 0 2481 3507; ppageno 0\">\n   <html:div class=\"ocr_carea\" id=\"block_1_1\" title=\"bbox 691 110 712 131\">\n    <html:p class=\"ocr_par\" id=\"par_1_1\" lang=\"eng\" title=\"bbox 691 110 712 131\">\n     <html:span class=\"ocr_line\" id=\"line_1_1\" title=\"bbox 691 110 712 131; baseline 0 0; x_size 29.333334; x_descenders 7.3333335; x_ascenders 7.3333335\">\n      <html:span class=\"ocrx_word\" id=\"word_1_1\" title=\"bbox 691 110 712 131; x_wconf 92\">®</html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_2\" title=\"bbox 822 181 2185 239\">\n    <html:p class=\"ocr_par\" id=\"par_1_2\" lang=\"eng\" title=\"bbox 822 181 2185 239\">\n     <html:span class=\"ocr_line\" id=\"line_1_2\" title=\"bbox 822 181 2185 239; baseline 0.001 -2; x_size 74.14286; x_descenders 18.535715; x_ascenders 18.535715\">\n      <html:span class=\"ocrx_word\" id=\"word_1_2\" title=\"bbox 822 182 1143 239; x_wconf 96\">Laminate</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_3\" title=\"bbox 1169 181 1659 239; x_wconf 96\">CERTIFICATE</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_4\" title=\"bbox 1686 181 1785 239; x_wconf 96\">OF</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_5\" title=\"bbox 1810 181 2185 239; x_wconf 96\">ANALYSIS</html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_3\" title=\"bbox 113 307 687 509\">\n    <html:p class=\"ocr_par\" id=\"par_1_3\" lang=\"eng\" title=\"bbox 113 307 687 509\">\n     <html:span class=\"ocr_line\" id=\"line_1_3\" title=\"bbox 113 307 687 352; baseline 0 0; x_size 52.123077; x_descenders 8.1230774; x_ascenders 10.83077\">\n      <html:span class=\"ocrx_word\" id=\"word_1_6\" title=\"bbox 113 307 373 352; x_wconf 95\">BUILDING</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_7\" title=\"bbox 394 307 687 352; x_wconf 96\">PRODUCTS</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_4\" title=\"bbox 114 378 620 409; baseline 0 0; x_size 36.877552; x_descenders 5.8775511; x_ascenders 7\">\n      <html:span class=\"ocrx_word\" id=\"word_1_8\" title=\"bbox 114 378 181 409; x_wconf 96\">600</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_9\" title=\"bbox 198 378 281 409; x_wconf 96\">East</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_10\" title=\"bbox 297 378 504 409; x_wconf 96\">Bethlehem</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_11\" title=\"bbox 522 378 620 409; x_wconf 96\">Road</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_5\" title=\"bbox 115 423 614 461; baseline 0 -6; x_size 38; x_descenders 6; x_ascenders 8\">\n      <html:span class=\"ocrx_word\" id=\"word_1_12\" title=\"bbox 115 423 326 461; x_wconf 95\">Columbus,</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_13\" title=\"bbox 343 424 487 455; x_wconf 96\">Kansas</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_14\" title=\"bbox 501 424 614 455; x_wconf 96\">66725</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_6\" title=\"bbox 115 471 396 509; baseline 0 -7; x_size 38.5; x_descenders 6; x_ascenders 8\">\n      <html:span class=\"ocrx_word\" id=\"word_1_15\" title=\"bbox 115 471 209 509; x_wconf 96\">(888)</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_16\" title=\"bbox 223 471 396 502; x_wconf 96\">250-1800</html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_4\" title=\"bbox 110 563 1850 952\">\n    <html:p class=\"ocr_par\" id=\"par_1_4\" lang=\"eng\" title=\"bbox 110 563 1850 651\">\n     <html:span class=\"ocr_line\" id=\"line_1_7\" title=\"bbox 110 563 1850 591; baseline 0 -8; x_size 25.652174; x_descenders 5.652174; x_ascenders 7.3913045\">\n      <html:span class=\"ocrx_word\" id=\"word_1_17\" title=\"bbox 110 570 245 591; x_wconf 89\">Product</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_18\" title=\"bbox 257 576 261 590; x_wconf 89\">:</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_19\" title=\"bbox 1243 564 1397 583; x_wconf 94\">LAMINATE</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_20\" title=\"bbox 1423 563 1576 583; x_wconf 92\">21000542</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_21\" title=\"bbox 1610 563 1696 587; x_wconf 92\">(3-18</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_22\" title=\"bbox 1722 566 1738 582; x_wconf 96\">+</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_23\" title=\"bbox 1765 563 1850 587; x_wconf 92\">6-18)</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_8\" title=\"bbox 110 628 1396 651; baseline 0 -2; x_size 25.652174; x_descenders 5.652174; x_ascenders 7.3913045\">\n      <html:span class=\"ocrx_word\" id=\"word_1_24\" title=\"bbox 110 630 167 649; x_wconf 85\">BOL</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_25\" title=\"bbox 192 628 221 651; x_wconf 84\">#:</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_26\" title=\"bbox 1245 629 1396 649; x_wconf 96\">81745511</html:span>\n     </html:span>\n    </html:p>\n\n    <html:p class=\"ocr_par\" id=\"par_1_5\" lang=\"eng\" title=\"bbox 110 689 1416 710\">\n     <html:span class=\"ocr_line\" id=\"line_1_9\" title=\"bbox 110 689 1416 710; baseline 0 -1; x_size 25.652174; x_descenders 5.652174; x_ascenders 7.3913045\">\n      <html:span class=\"ocrx_word\" id=\"word_1_27\" title=\"bbox 110 689 207 710; x_wconf 95\">Batch</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_28\" title=\"bbox 233 690 281 709; x_wconf 96\">ID:</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_29\" title=\"bbox 1245 689 1416 709; x_wconf 96\">193430454</html:span>\n     </html:span>\n    </html:p>\n\n    <html:p class=\"ocr_par\" id=\"par_1_6\" lang=\"eng\" title=\"bbox 110 746 1437 771\">\n     <html:span class=\"ocr_line\" id=\"line_1_10\" title=\"bbox 110 746 1437 771; baseline 0 -3; x_size 28.275862; x_descenders 6.2758622; x_ascenders 8\">\n      <html:span class=\"ocrx_word\" id=\"word_1_30\" title=\"bbox 110 748 207 769; x_wconf 96\">Batch</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_31\" title=\"bbox 230 749 321 769; x_wconf 96\">Date:</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_32\" title=\"bbox 1245 746 1437 771; x_wconf 96\">10/09/2019</html:span>\n     </html:span>\n    </html:p>\n\n    <html:p class=\"ocr_par\" id=\"par_1_7\" lang=\"eng\" title=\"bbox 110 806 1556 831\">\n     <html:span class=\"ocr_line\" id=\"line_1_11\" title=\"bbox 110 806 1556 831; baseline 0 -3; x_size 28.275862; x_descenders 6.2758622; x_ascenders 8\">\n      <html:span class=\"ocrx_word\" id=\"word_1_33\" title=\"bbox 110 808 207 829; x_wconf 96\">Batch</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_34\" title=\"bbox 232 809 341 829; x_wconf 96\">Start:</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_35\" title=\"bbox 1245 806 1437 831; x_wconf 96\">10/09/2019</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_36\" title=\"bbox 1464 808 1556 828; x_wconf 96\">08:42</html:span>\n     </html:span>\n    </html:p>\n\n    <html:p class=\"ocr_par\" id=\"par_1_8\" lang=\"eng\" title=\"bbox 110 865 1556 890\">\n     <html:span class=\"ocr_line\" id=\"line_1_12\" title=\"bbox 110 865 1556 890; baseline 0 -3; x_size 25.652174; x_descenders 5.652174; x_ascenders 7.3913045\">\n      <html:span class=\"ocrx_word\" id=\"word_1_37\" title=\"bbox 110 867 207 888; x_wconf 95\">Batch</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_38\" title=\"bbox 230 867 301 887; x_wconf 95\">End:</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_39\" title=\"bbox 1245 865 1437 890; x_wconf 95\">10/09/2019</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_40\" title=\"bbox 1464 867 1556 887; x_wconf 95\">12:18</html:span>\n     </html:span>\n    </html:p>\n\n    <html:p class=\"ocr_par\" id=\"par_1_9\" lang=\"eng\" title=\"bbox 112 924 1557 952\">\n     <html:span class=\"ocr_line\" id=\"line_1_13\" title=\"bbox 112 924 1557 952; baseline 0 -6; x_size 25.652174; x_descenders 5.652174; x_ascenders 7.3913045\">\n      <html:span class=\"ocrx_word\" id=\"word_1_41\" title=\"bbox 112 925 187 952; x_wconf 96\">Ship</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_42\" title=\"bbox 210 927 301 947; x_wconf 96\">Date:</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_43\" title=\"bbox 1245 924 1437 949; x_wconf 95\">10/09/2019</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_44\" title=\"bbox 1464 926 1557 946; x_wconf 94\">14:19</html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_5\" title=\"bbox 111 1044 405 1071\">\n    <html:p class=\"ocr_par\" id=\"par_1_10\" lang=\"eng\" title=\"bbox 111 1044 405 1071\">\n     <html:span class=\"ocr_line\" id=\"line_1_14\" title=\"bbox 111 1044 405 1071; baseline -0.003 -5; x_size 25; x_descenders 4; x_ascenders 7\">\n      <html:span class=\"ocrx_word\" id=\"word_1_45\" title=\"bbox 111 1044 247 1071; x_wconf 95\">Quality</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_46\" title=\"bbox 269 1044 405 1065; x_wconf 95\">Metrics</html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_6\" title=\"bbox 111 1104 2060 1665\">\n    <html:p class=\"ocr_par\" id=\"par_1_11\" lang=\"eng\" title=\"bbox 111 1104 2060 1665\">\n     <html:span class=\"ocr_line\" id=\"line_1_15\" title=\"bbox 111 1104 2060 1131; baseline 0 -6; x_size 27; x_descenders 6; x_ascenders 7\">\n      <html:span class=\"ocrx_word\" id=\"word_1_47\" title=\"bbox 111 1104 266 1126; x_wconf 96\">Laminate</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_48\" title=\"bbox 290 1104 507 1126; x_wconf 95\">Penetration</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_49\" title=\"bbox 530 1105 627 1131; x_wconf 96\">Depth</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_50\" title=\"bbox 1244 1105 1277 1125; x_wconf 96\">39</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_51\" title=\"bbox 1944 1105 1996 1125; x_wconf 96\">0.1</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_52\" title=\"bbox 2020 1111 2060 1125; x_wconf 96\">mm</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_16\" title=\"bbox 111 1163 2037 1190; baseline 0 -6; x_size 27; x_descenders 6; x_ascenders 7\">\n      <html:span class=\"ocrx_word\" id=\"word_1_53\" title=\"bbox 111 1163 266 1185; x_wconf 95\">Laminate</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_54\" title=\"bbox 292 1163 468 1190; x_wconf 95\">Softening</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_55\" title=\"bbox 490 1163 585 1184; x_wconf 95\">Point</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_56\" title=\"bbox 1244 1164 1297 1184; x_wconf 95\">226</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_57\" title=\"bbox 1942 1164 1999 1190; x_wconf 91\">deg</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_58\" title=\"bbox 2021 1165 2037 1184; x_wconf 90\">F</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_17\" title=\"bbox 111 1222 1996 1249; baseline 0 -6; x_size 27; x_descenders 6; x_ascenders 7\">\n      <html:span class=\"ocrx_word\" id=\"word_1_59\" title=\"bbox 111 1222 266 1244; x_wconf 95\">Laminate</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_60\" title=\"bbox 289 1222 467 1249; x_wconf 95\">Viscosity</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_61\" title=\"bbox 1245 1223 1317 1243; x_wconf 94\">1053</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_62\" title=\"bbox 1942 1224 1996 1249; x_wconf 89\">Cps</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_18\" title=\"bbox 111 1281 1957 1303; baseline 0 -1; x_size 27.275862; x_descenders 6.2758622; x_ascenders 7\">\n      <html:span class=\"ocrx_word\" id=\"word_1_63\" title=\"bbox 111 1281 266 1303; x_wconf 95\">Laminate</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_64\" title=\"bbox 292 1282 387 1303; x_wconf 95\">Shear</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_65\" title=\"bbox 410 1283 469 1302; x_wconf 96\">RPM</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_66\" title=\"bbox 490 1283 526 1302; x_wconf 95\">WP</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_67\" title=\"bbox 549 1281 647 1302; x_wconf 95\">Mixer</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_68\" title=\"bbox 672 1282 685 1302; x_wconf 95\">2</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_69\" title=\"bbox 1245 1282 1296 1302; x_wconf 96\">100</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_70\" title=\"bbox 1943 1282 1957 1302; x_wconf 91\">%</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_19\" title=\"bbox 111 1341 1957 1363; baseline 0 -1; x_size 27.275862; x_descenders 6.2758622; x_ascenders 7\">\n      <html:span class=\"ocrx_word\" id=\"word_1_71\" title=\"bbox 111 1341 266 1363; x_wconf 95\">Laminate</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_72\" title=\"bbox 292 1342 387 1363; x_wconf 96\">Shear</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_73\" title=\"bbox 410 1343 469 1362; x_wconf 96\">RPM</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_74\" title=\"bbox 490 1343 526 1362; x_wconf 95\">WP</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_75\" title=\"bbox 549 1341 647 1362; x_wconf 95\">Mixer</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_76\" title=\"bbox 673 1342 685 1362; x_wconf 96\">1</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_77\" title=\"bbox 1245 1342 1296 1362; x_wconf 96\">100</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_78\" title=\"bbox 1943 1342 1957 1362; x_wconf 91\">%</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_20\" title=\"bbox 111 1400 2037 1427; baseline 0 -6; x_size 27; x_descenders 6; x_ascenders 7\">\n      <html:span class=\"ocrx_word\" id=\"word_1_79\" title=\"bbox 111 1400 266 1422; x_wconf 95\">Laminate</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_80\" title=\"bbox 292 1401 387 1422; x_wconf 96\">Shear</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_81\" title=\"bbox 411 1402 626 1427; x_wconf 95\">Temperature</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_82\" title=\"bbox 650 1402 686 1421; x_wconf 95\">WP</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_83\" title=\"bbox 709 1400 807 1421; x_wconf 95\">Mixer</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_84\" title=\"bbox 832 1401 845 1421; x_wconf 95\">2</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_85\" title=\"bbox 1244 1401 1296 1421; x_wconf 96\">392</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_86\" title=\"bbox 1942 1401 1999 1427; x_wconf 91\">deg</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_87\" title=\"bbox 2021 1402 2037 1421; x_wconf 90\">F</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_21\" title=\"bbox 111 1460 2037 1487; baseline 0 -6; x_size 27; x_descenders 6; x_ascenders 7\">\n      <html:span class=\"ocrx_word\" id=\"word_1_88\" title=\"bbox 111 1460 266 1482; x_wconf 95\">Laminate</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_89\" title=\"bbox 292 1461 387 1482; x_wconf 96\">Shear</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_90\" title=\"bbox 411 1462 626 1487; x_wconf 95\">Temperature</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_91\" title=\"bbox 650 1462 686 1481; x_wconf 95\">WP</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_92\" title=\"bbox 709 1460 807 1481; x_wconf 95\">Mixer</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_93\" title=\"bbox 833 1461 845 1481; x_wconf 95\">1</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_94\" title=\"bbox 1244 1461 1296 1481; x_wconf 96\">392</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_95\" title=\"bbox 1942 1461 1999 1487; x_wconf 91\">deg</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_96\" title=\"bbox 2021 1462 2037 1481; x_wconf 90\">F</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_22\" title=\"bbox 111 1519 2057 1541; baseline 0 -1; x_size 27.275862; x_descenders 6.2758622; x_ascenders 7\">\n      <html:span class=\"ocrx_word\" id=\"word_1_97\" title=\"bbox 111 1519 266 1541; x_wconf 95\">Laminate</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_98\" title=\"bbox 292 1520 387 1541; x_wconf 96\">Shear</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_99\" title=\"bbox 411 1519 486 1540; x_wconf 95\">Time</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_100\" title=\"bbox 510 1521 546 1540; x_wconf 96\">WP</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_101\" title=\"bbox 569 1519 667 1540; x_wconf 96\">Mixer</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_102\" title=\"bbox 692 1520 705 1540; x_wconf 96\">2</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_103\" title=\"bbox 1245 1520 1296 1540; x_wconf 96\">118</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_104\" title=\"bbox 1940 1519 2057 1541; x_wconf 96\">Minute</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_23\" title=\"bbox 111 1578 2057 1600; baseline 0 -1; x_size 27.275862; x_descenders 6.2758622; x_ascenders 7\">\n      <html:span class=\"ocrx_word\" id=\"word_1_105\" title=\"bbox 111 1578 266 1600; x_wconf 96\">Laminate</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_106\" title=\"bbox 292 1579 387 1600; x_wconf 96\">Shear</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_107\" title=\"bbox 411 1578 486 1599; x_wconf 95\">Time</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_108\" title=\"bbox 510 1580 546 1599; x_wconf 96\">WP</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_109\" title=\"bbox 569 1578 667 1599; x_wconf 96\">Mixer</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_110\" title=\"bbox 693 1579 705 1599; x_wconf 96\">1</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_111\" title=\"bbox 1245 1579 1296 1599; x_wconf 96\">118</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_112\" title=\"bbox 1940 1578 2057 1600; x_wconf 96\">Minute</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_24\" title=\"bbox 111 1638 2037 1665; baseline 0 -6; x_size 27; x_descenders 6; x_ascenders 7\">\n      <html:span class=\"ocrx_word\" id=\"word_1_113\" title=\"bbox 111 1638 266 1660; x_wconf 95\">Laminate</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_114\" title=\"bbox 292 1638 448 1665; x_wconf 95\">Shipping</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_115\" title=\"bbox 471 1640 686 1665; x_wconf 94\">Temperature</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_116\" title=\"bbox 710 1640 746 1659; x_wconf 95\">WP</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_117\" title=\"bbox 769 1638 867 1659; x_wconf 95\">Mixer</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_118\" title=\"bbox 892 1639 906 1659; x_wconf 95\">3</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_119\" title=\"bbox 1244 1639 1296 1659; x_wconf 96\">391</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_120\" title=\"bbox 1942 1639 1999 1665; x_wconf 91\">deg</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_121\" title=\"bbox 2021 1640 2037 1659; x_wconf 90\">F</html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_7\" title=\"bbox 110 1757 1296 1838\">\n    <html:p class=\"ocr_par\" id=\"par_1_12\" lang=\"eng\" title=\"bbox 110 1757 1296 1838\">\n     <html:span class=\"ocr_line\" id=\"line_1_25\" title=\"bbox 110 1757 585 1779; baseline 0 -1; x_size 26.310345; x_descenders 5.3103447; x_ascenders 7\">\n      <html:span class=\"ocrx_word\" id=\"word_1_122\" title=\"bbox 110 1758 207 1779; x_wconf 95\">Batch</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_123\" title=\"bbox 229 1757 427 1779; x_wconf 96\">Automation</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_124\" title=\"bbox 449 1757 585 1778; x_wconf 95\">Metrics</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_26\" title=\"bbox 110 1818 1296 1838; baseline 0 -1; x_size 24.310345; x_descenders 5.3103447; x_ascenders 5\">\n      <html:span class=\"ocrx_word\" id=\"word_1_125\" title=\"bbox 110 1818 149 1837; x_wconf 96\">EM</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_126\" title=\"bbox 169 1818 247 1838; x_wconf 96\">Auto</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_127\" title=\"bbox 1243 1818 1296 1837; x_wconf 95\">Yes</html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_8\" title=\"bbox 112 1876 1296 1897\">\n    <html:p class=\"ocr_par\" id=\"par_1_13\" lang=\"eng\" title=\"bbox 112 1876 1296 1897\">\n     <html:span class=\"ocr_line\" id=\"line_1_27\" title=\"bbox 112 1876 1296 1897; baseline 0 -1; x_size 25.310345; x_descenders 5.3103447; x_ascenders 6\">\n      <html:span class=\"ocrx_word\" id=\"word_1_128\" title=\"bbox 112 1876 288 1897; x_wconf 96\">Scheduled</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_129\" title=\"bbox 310 1876 407 1897; x_wconf 95\">Batch</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_130\" title=\"bbox 430 1876 568 1897; x_wconf 95\">Enabled</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_131\" title=\"bbox 1243 1877 1296 1896; x_wconf 95\">Yes</html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n  </html:div>\n </html:body>\n</html:html>
    '''
    return txt

def getTxtForBBoxParsing():
    """
    Will give example text from ocr output. ocr output needs to be modified slightly, so I just copied fixed versions below for testing.
    """
    txt3 = '''
        <html:html xmlns:html=\"http://www.w3.org/1999/xhtml\" lang=\"en\" xml:lang=\"en\">\n <html:head>\n  <html:title />\n<html:meta content=\"text/html;charset=utf-8\" http-equiv=\"Content-Type\" />\n  <html:meta content=\"tesseract 4.0.0\" name=\"ocr-system\" />\n  <html:meta content=\"ocr_page ocr_carea ocr_par ocr_line ocrx_word ocrp_wconf\" name=\"ocr-capabilities\" />\n</html:head>\n<html:body>\n  <html:div class=\"ocr_page\" id=\"page_1\" rotation=\"0\" title=\"image &quot;/tmp/92dfc34f-3797-4a94-9239-aa9e63785aaa0/20190104_Sealant_page_11.png&quot;; bbox 0 0 2550 3300; ppageno 0\">\n   <html:div class=\"ocr_carea\" id=\"block_1_1\" title=\"bbox 384 380 956 562\">\n    <html:p class=\"ocr_par\" id=\"par_1_1\" lang=\"deu\" title=\"bbox 384 380 956 562\">\n     <html:span class=\"ocr_line\" id=\"line_1_1\" title=\"bbox 384 380 956 562; baseline 0.007 -32; x_size 106; x_descenders 28; x_ascenders 21\">\n      <html:span class=\"ocrx_word\" id=\"word_1_1\" title=\"bbox 384 380 579 562; x_wconf 48\">A</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_2\" lang=\"eng\" title=\"bbox 600 456 956 534; x_wconf 95\">Trumbull</html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_2\" title=\"bbox 349 577 598 605\">\n    <html:p class=\"ocr_par\" id=\"par_1_2\" lang=\"eng\" title=\"bbox 349 577 598 605\">\n     <html:span class=\"ocr_line\" id=\"line_1_2\" title=\"bbox 349 577 598 605; baseline 0.004 -1; x_size 35.722221; x_descenders 8.9305553; x_ascenders 8.9305553\">\n      <html:span class=\"ocrx_word\" id=\"word_1_3\" title=\"bbox 349 578 468 605; x_wconf 89\">INNOVATIONS</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_4\" title=\"bbox 482 578 516 605; x_wconf 89\">FOR</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_5\" title=\"bbox 528 577 598 605; x_wconf 89\">LIVING®</html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_3\" title=\"bbox 1463 336 2248 557\">\n    <html:p class=\"ocr_par\" id=\"par_1_3\" lang=\"eng\" title=\"bbox 1463 336 2248 557\">\n     <html:span class=\"ocr_line\" id=\"line_1_3\" title=\"bbox 1464 336 2248 381; baseline 0 -9; x_size 45; x_descenders 9; x_ascenders 10\">\n      <html:span class=\"ocrx_word\" id=\"word_1_6\" title=\"bbox 1464 338 1606 372; x_wconf 96\">Owens</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_7\" title=\"bbox 1621 337 1779 381; x_wconf 96\">Corning</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_8\" title=\"bbox 1795 336 1952 381; x_wconf 91\">Roofing</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_9\" title=\"bbox 1965 337 1997 372; x_wconf 91\">&amp;</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_10\" title=\"bbox 2011 336 2168 380; x_wconf 96\">Asphalt</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_11\" title=\"bbox 2183 338 2248 372; x_wconf 96\">LLC</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_4\" title=\"bbox 1464 393 1837 433; baseline 0 0; x_size 41.472973; x_descenders 8.4729729; x_ascenders 9.3648653\">\n      <html:span class=\"ocrx_word\" id=\"word_1_12\" lang=\"deu\" title=\"bbox 1464 400 1565 433; x_wconf 96\">3400</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_13\" lang=\"deu\" title=\"bbox 1580 400 1633 433; x_wconf 93\">NE</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_14\" lang=\"deu\" title=\"bbox 1646 396 1682 433; x_wconf 89\">4*</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_15\" lang=\"deu\" title=\"bbox 1684 393 1837 433; x_wconf 96\">Street</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_5\" title=\"bbox 1464 459 1991 503; baseline -0.002 -8; x_size 41.472973; x_descenders 8.4729729; x_ascenders 9.3648653\">\n      <html:span class=\"ocrx_word\" id=\"word_1_16\" lang=\"deu\" title=\"bbox 1464 459 1651 495; x_wconf 96\">Oklahoma</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_17\" lang=\"deu\" title=\"bbox 1655 460 1779 503; x_wconf 96\">City,</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_18\" lang=\"deu\" title=\"bbox 1795 461 1854 495; x_wconf 96\">OK</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_19\" lang=\"deu\" title=\"bbox 1868 461 1991 495; x_wconf 96\">73117</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_6\" title=\"bbox 1463 523 1746 557; baseline 0 -1; x_size 41.472973; x_descenders 8.4729729; x_ascenders 9.3648653\">\n      <html:span class=\"ocrx_word\" id=\"word_1_20\" lang=\"deu\" title=\"bbox 1463 523 1746 557; x_wconf 91\">405-235-2491</html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_4\" title=\"bbox 284 701 2298 704\">\n    <html:p class=\"ocr_par\" id=\"par_1_4\" lang=\"eng\" title=\"bbox 284 701 2298 704\">\n     <html:span class=\"ocr_line\" id=\"line_1_7\" title=\"bbox 284 701 2298 704; baseline 0 0; x_size 1.5; x_descenders -0.75; x_ascenders 0.75\">\n      <html:span class=\"ocrx_word\" id=\"word_1_21\" title=\"bbox 284 701 2298 704; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_5\" title=\"bbox 284 701 286 812\">\n    <html:p class=\"ocr_par\" id=\"par_1_5\" lang=\"eng\" title=\"bbox 284 701 286 812\">\n     <html:span class=\"ocr_line\" id=\"line_1_8\" title=\"bbox 284 701 286 812; baseline 0 0; x_size 55.5; x_descenders -27.75; x_ascenders 27.75\">\n      <html:span class=\"ocrx_word\" id=\"word_1_22\" title=\"bbox 284 701 286 812; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_6\" title=\"bbox 880 728 1712 804\">\n    <html:p class=\"ocr_par\" id=\"par_1_6\" lang=\"deu\" title=\"bbox 880 728 1712 804\">\n     <html:span class=\"ocr_line\" id=\"line_1_9\" title=\"bbox 880 728 1712 804; baseline 0 -16; x_size 76; x_descenders 16; x_ascenders 18\">\n      <html:span class=\"ocrx_word\" id=\"word_1_23\" title=\"bbox 880 728 1276 788; x_wconf 96\">Certificate</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_24\" title=\"bbox 1300 728 1378 788; x_wconf 96\">of</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_25\" title=\"bbox 1390 728 1712 804; x_wconf 95\">Analysis</html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_7\" title=\"bbox 284 807 2298 810\">\n    <html:p class=\"ocr_par\" id=\"par_1_7\" lang=\"eng\" title=\"bbox 284 807 2298 810\">\n     <html:span class=\"ocr_line\" id=\"line_1_10\" title=\"bbox 284 807 2298 810; baseline 0 0; x_size 1.5; x_descenders -0.75; x_ascenders 0.75\">\n      <html:span class=\"ocrx_word\" id=\"word_1_26\" title=\"bbox 284 807 2298 810; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_8\" title=\"bbox 284 1103 2298 1106\">\n    <html:p class=\"ocr_par\" id=\"par_1_8\" lang=\"eng\" title=\"bbox 284 1103 2298 1106\">\n     <html:span class=\"ocr_line\" id=\"line_1_11\" title=\"bbox 284 1103 2298 1106; baseline 0 0; x_size 1.5; x_descenders -0.75; x_ascenders 0.75\">\n      <html:span class=\"ocrx_word\" id=\"word_1_27\" title=\"bbox 284 1103 2298 1106; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_9\" title=\"bbox 284 1217 2296 1220\">\n    <html:p class=\"ocr_par\" id=\"par_1_9\" lang=\"eng\" title=\"bbox 284 1217 2296 1220\">\n     <html:span class=\"ocr_line\" id=\"line_1_12\" title=\"bbox 284 1217 2296 1220; baseline 0 0; x_size 1.5; x_descenders -0.75; x_ascenders 0.75\">\n      <html:span class=\"ocrx_word\" id=\"word_1_28\" title=\"bbox 284 1217 2296 1220; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_10\" title=\"bbox 282 1329 2296 1332\">\n    <html:p class=\"ocr_par\" id=\"par_1_10\" lang=\"eng\" title=\"bbox 282 1329 2296 1332\">\n     <html:span class=\"ocr_line\" id=\"line_1_13\" title=\"bbox 282 1329 2296 1332; baseline 0 0; x_size 1.5; x_descenders -0.75; x_ascenders 0.75\">\n      <html:span class=\"ocrx_word\" id=\"word_1_29\" title=\"bbox 282 1329 2296 1332; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_11\" title=\"bbox 380 1120 2156 1414\">\n    <html:p class=\"ocr_par\" id=\"par_1_11\" lang=\"deu\" title=\"bbox 380 1120 2156 1414\">\n     <html:span class=\"ocr_line\" id=\"line_1_14\" title=\"bbox 458 1120 2109 1182; baseline -0.001 -3; x_size 42.733898; x_descenders 6.7338982; x_ascenders 11\">\n      <html:span class=\"ocrx_word\" id=\"word_1_30\" title=\"bbox 458 1144 619 1180; x_wconf 96\">Product</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_31\" title=\"bbox 944 1175 951 1181; x_wconf 28\">.</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_32\" title=\"bbox 986 1120 1102 1151; x_wconf 95\">59884</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_33\" title=\"bbox 1135 1175 1143 1182; x_wconf 34\">.</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_34\" title=\"bbox 1445 1147 1646 1181; x_wconf 96\">Customer</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_35\" title=\"bbox 1981 1147 2109 1179; x_wconf 91\">Tamko</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_15\" title=\"bbox 896 1174 1191 1214; baseline 0 -8; x_size 40; x_descenders 8; x_ascenders 8\">\n      <html:span class=\"ocrx_word\" id=\"word_1_36\" title=\"bbox 896 1174 1033 1214; x_wconf 92\">Shingle</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_37\" title=\"bbox 1047 1176 1191 1214; x_wconf 92\">Coating</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_16\" title=\"bbox 380 1257 2091 1302; baseline 0 -9; x_size 46; x_descenders 9; x_ascenders 12\">\n      <html:span class=\"ocrx_word\" id=\"word_1_38\" title=\"bbox 380 1259 577 1302; x_wconf 91\">Receiving</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_39\" title=\"bbox 592 1258 696 1294; x_wconf 96\">Plant</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_40\" title=\"bbox 937 1260 1146 1293; x_wconf 92\">Tuscaloosa</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_41\" title=\"bbox 1425 1257 1663 1302; x_wconf 92\">Tank/Truck</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_42\" title=\"bbox 1999 1262 2091 1293; x_wconf 96\">9746</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_17\" title=\"bbox 394 1372 2156 1414; baseline -0.001 -7; x_size 42; x_descenders 6; x_ascenders 11\">\n      <html:span class=\"ocrx_word\" id=\"word_1_43\" title=\"bbox 394 1374 489 1407; x_wconf 96\">Date</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_44\" title=\"bbox 504 1372 681 1408; x_wconf 96\">Certified</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_45\" title=\"bbox 930 1372 1155 1413; x_wconf 96\">01/04/2019</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_46\" title=\"bbox 1376 1373 1602 1409; x_wconf 95\">Production</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_47\" title=\"bbox 1620 1375 1714 1409; x_wconf 96\">Date</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_48\" title=\"bbox 1933 1372 2156 1414; x_wconf 96\">01/04/2019</html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_12\" title=\"bbox 790 1104 792 1446\">\n    <html:p class=\"ocr_par\" id=\"par_1_12\" lang=\"eng\" title=\"bbox 790 1104 792 1446\">\n     <html:span class=\"ocr_line\" id=\"line_1_18\" title=\"bbox 790 1104 792 1446; baseline 0 0; x_size 171; x_descenders -85.5; x_ascenders 85.5\">\n      <html:span class=\"ocrx_word\" id=\"word_1_49\" title=\"bbox 790 1104 792 1446; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_13\" title=\"bbox 818 1485 966 1525\">\n    <html:p class=\"ocr_par\" id=\"par_1_13\" lang=\"deu\" title=\"bbox 818 1485 966 1525\">\n     <html:span class=\"ocr_line\" id=\"line_1_19\" title=\"bbox 818 1485 966 1525; baseline 0 0; x_size 45.403507; x_descenders 5.4035087; x_ascenders 12\">\n      <html:span class=\"ocrx_word\" id=\"word_1_50\" title=\"bbox 818 1485 966 1525; x_wconf 30\">SV</html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_14\" title=\"bbox 1292 1104 1296 1446\">\n    <html:p class=\"ocr_par\" id=\"par_1_14\" lang=\"eng\" title=\"bbox 1292 1104 1296 1446\">\n     <html:span class=\"ocr_line\" id=\"line_1_20\" title=\"bbox 1292 1104 1296 1446; baseline 0 0; x_size 171; x_descenders -85.5; x_ascenders 85.5\">\n      <html:span class=\"ocrx_word\" id=\"word_1_51\" title=\"bbox 1292 1104 1296 1446; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_15\" title=\"bbox 1139 1486 1445 1526\">\n    <html:p class=\"ocr_par\" id=\"par_1_15\" lang=\"eng\" title=\"bbox 1139 1486 1445 1526\">\n     <html:span class=\"ocr_line\" id=\"line_1_21\" title=\"bbox 1139 1486 1445 1526; baseline 0.003 -1; x_size 45.403507; x_descenders 5.4035087; x_ascenders 12\">\n      <html:span class=\"ocrx_word\" id=\"word_1_52\" title=\"bbox 1139 1488 1238 1526; x_wconf 96\">Test</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_53\" title=\"bbox 1257 1486 1445 1526; x_wconf 96\">Method</html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_16\" title=\"bbox 1794 1104 1797 1446\">\n    <html:p class=\"ocr_par\" id=\"par_1_16\" lang=\"eng\" title=\"bbox 1794 1104 1797 1446\">\n     <html:span class=\"ocr_line\" id=\"line_1_22\" title=\"bbox 1794 1104 1797 1446; baseline 0 0; x_size 171; x_descenders -85.5; x_ascenders 85.5\">\n      <html:span class=\"ocrx_word\" id=\"word_1_54\" title=\"bbox 1794 1104 1797 1446; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_17\" title=\"bbox 1540 1486 1847 1536\">\n    <html:p class=\"ocr_par\" id=\"par_1_17\" lang=\"eng\" title=\"bbox 1540 1486 1847 1536\">\n     <html:span class=\"ocr_line\" id=\"line_1_23\" title=\"bbox 1540 1486 1847 1536; baseline -0.003 -10; x_size 50; x_descenders 10; x_ascenders 12\">\n      <html:span class=\"ocrx_word\" id=\"word_1_55\" title=\"bbox 1540 1486 1847 1536; x_wconf 96\">Specification</html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_18\" title=\"bbox 278 1442 2300 1568\">\n    <html:p class=\"ocr_par\" id=\"par_1_18\" lang=\"eng\" title=\"bbox 278 1442 2300 1568\">\n     <html:span class=\"ocr_line\" id=\"line_1_24\" title=\"bbox 278 1442 2300 1568; baseline 0 1732; x_size 158.75; x_descenders 39.6875; x_ascenders 39.6875\">\n      <html:span class=\"ocrx_word\" id=\"word_1_56\" title=\"bbox 278 1442 2300 1568; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_19\" title=\"bbox 1991 1483 2200 1534\">\n    <html:p class=\"ocr_par\" id=\"par_1_19\" lang=\"eng\" title=\"bbox 1991 1483 2200 1534\">\n     <html:span class=\"ocr_line\" id=\"line_1_25\" title=\"bbox 1991 1483 2200 1534; baseline -0.005 -8; x_size 50; x_descenders 8; x_ascenders 13\">\n      <html:span class=\"ocrx_word\" id=\"word_1_57\" title=\"bbox 1991 1483 2200 1534; x_wconf 96\">Pass/Fail</html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_20\" title=\"bbox 282 1672 2296 1679\">\n    <html:p class=\"ocr_par\" id=\"par_1_20\" lang=\"eng\" title=\"bbox 282 1672 2296 1679\">\n     <html:span class=\"ocr_line\" id=\"line_1_26\" title=\"bbox 282 1672 2296 1679; baseline 0 0; x_size 3.5; x_descenders -1.75; x_ascenders 1.75\">\n      <html:span class=\"ocrx_word\" id=\"word_1_58\" title=\"bbox 282 1672 2296 1679; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_21\" title=\"bbox 282 1788 2296 1794\">\n    <html:p class=\"ocr_par\" id=\"par_1_21\" lang=\"eng\" title=\"bbox 282 1788 2296 1794\">\n     <html:span class=\"ocr_line\" id=\"line_1_27\" title=\"bbox 282 1788 2296 1794; baseline 0 0; x_size 3; x_descenders -1.5; x_ascenders 1.5\">\n      <html:span class=\"ocrx_word\" id=\"word_1_59\" title=\"bbox 282 1788 2296 1794; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_22\" title=\"bbox 284 1104 287 1904\">\n    <html:p class=\"ocr_par\" id=\"par_1_22\" lang=\"eng\" title=\"bbox 284 1104 287 1904\">\n     <html:span class=\"ocr_line\" id=\"line_1_28\" title=\"bbox 284 1104 287 1904; baseline 0 0; x_size 400; x_descenders -200; x_ascenders 200\">\n      <html:span class=\"ocrx_word\" id=\"word_1_60\" title=\"bbox 284 1104 287 1904; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_23\" title=\"bbox 686 1564 690 1904\">\n    <html:p class=\"ocr_par\" id=\"par_1_23\" lang=\"eng\" title=\"bbox 686 1564 690 1904\">\n     <html:span class=\"ocr_line\" id=\"line_1_29\" title=\"bbox 686 1564 690 1904; baseline 0 0; x_size 170; x_descenders -85; x_ascenders 85\">\n      <html:span class=\"ocrx_word\" id=\"word_1_61\" title=\"bbox 686 1564 690 1904; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_24\" title=\"bbox 1090 1564 1096 1904\">\n    <html:p class=\"ocr_par\" id=\"par_1_24\" lang=\"eng\" title=\"bbox 1090 1564 1096 1904\">\n     <html:span class=\"ocr_line\" id=\"line_1_30\" title=\"bbox 1090 1564 1096 1904; baseline 0 0; x_size 170; x_descenders -85; x_ascenders 85\">\n      <html:span class=\"ocrx_word\" id=\"word_1_62\" title=\"bbox 1090 1564 1096 1904; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_25\" title=\"bbox 748 1900 1428 2026\">\n    <html:p class=\"ocr_par\" id=\"par_1_25\" lang=\"eng\" title=\"bbox 748 1900 1428 2026\">\n     <html:span class=\"ocr_line\" id=\"line_1_31\" title=\"bbox 748 1900 1428 2026; baseline 0 1274; x_size 158.75; x_descenders 39.6875; x_ascenders 39.6875\">\n      <html:span class=\"ocrx_word\" id=\"word_1_63\" title=\"bbox 748 1900 1428 2026; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_26\" title=\"bbox 280 2130 1092 2136\">\n    <html:p class=\"ocr_par\" id=\"par_1_26\" lang=\"eng\" title=\"bbox 280 2130 1092 2136\">\n     <html:span class=\"ocr_line\" id=\"line_1_32\" title=\"bbox 280 2130 1092 2136; baseline 0 0; x_size 3; x_descenders -1.5; x_ascenders 1.5\">\n      <html:span class=\"ocrx_word\" id=\"word_1_64\" title=\"bbox 280 2130 1092 2136; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_27\" title=\"bbox 280 1104 288 2248\">\n    <html:p class=\"ocr_par\" id=\"par_1_27\" lang=\"eng\" title=\"bbox 280 1104 288 2248\">\n     <html:span class=\"ocr_line\" id=\"line_1_33\" title=\"bbox 280 1104 288 2248; baseline 0 0; x_size 572; x_descenders -286; x_ascenders 286\">\n      <html:span class=\"ocrx_word\" id=\"word_1_65\" title=\"bbox 280 1104 288 2248; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_28\" title=\"bbox 1492 1564 1494 1906\">\n    <html:p class=\"ocr_par\" id=\"par_1_28\" lang=\"eng\" title=\"bbox 1492 1564 1494 1906\">\n     <html:span class=\"ocr_line\" id=\"line_1_34\" title=\"bbox 1492 1564 1494 1906; baseline 0 0; x_size 171; x_descenders -85.5; x_ascenders 85.5\">\n      <html:span class=\"ocrx_word\" id=\"word_1_66\" title=\"bbox 1492 1564 1494 1906; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_29\" title=\"bbox 1892 1564 1898 1906\">\n    <html:p class=\"ocr_par\" id=\"par_1_29\" lang=\"eng\" title=\"bbox 1892 1564 1898 1906\">\n     <html:span class=\"ocr_line\" id=\"line_1_35\" title=\"bbox 1892 1564 1898 1906; baseline 0 0; x_size 171; x_descenders -85.5; x_ascenders 85.5\">\n      <html:span class=\"ocrx_word\" id=\"word_1_67\" title=\"bbox 1892 1564 1898 1906; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_30\" title=\"bbox 1490 2134 2294 2136\">\n    <html:p class=\"ocr_par\" id=\"par_1_30\" lang=\"eng\" title=\"bbox 1490 2134 2294 2136\">\n     <html:span class=\"ocr_line\" id=\"line_1_36\" title=\"bbox 1490 2134 2294 2136; baseline 0 0; x_size 1; x_descenders -0.5; x_ascenders 0.5\">\n      <html:span class=\"ocrx_word\" id=\"word_1_68\" title=\"bbox 1490 2134 2294 2136; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_31\" title=\"bbox 338 1574 2223 2215\">\n    <html:p class=\"ocr_par\" id=\"par_1_31\" lang=\"eng\" title=\"bbox 338 1574 2223 2215\">\n     <html:span class=\"ocr_line\" id=\"line_1_37\" title=\"bbox 338 1575 592 1606; baseline 0 -24; x_size 40.650002; x_descenders 5.9499998; x_ascenders 10.5\">\n      <html:span class=\"ocrx_word\" id=\"word_1_69\" title=\"bbox 338 1575 358 1606; x_wconf 82\">S</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_70\" lang=\"deu\" title=\"bbox 465 1575 473 1582; x_wconf 92\">ing</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_71\" title=\"bbox 535 1575 592 1606; x_wconf 94\">Poi</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_38\" title=\"bbox 360 1574 2141 1638; baseline -0.001 0; x_size 62.621902; x_descenders 7.6219006; x_ascenders 24\">\n      <html:span class=\"ocrx_word\" id=\"word_1_72\" title=\"bbox 360 1574 521 1638; x_wconf 93\">oftening</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_73\" title=\"bbox 558 1579 634 1607; x_wconf 96\">Point</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_74\" title=\"bbox 858 1605 925 1636; x_wconf 97\">180</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_75\" title=\"bbox 1250 1605 1337 1636; x_wconf 91\">D-36</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_76\" title=\"bbox 1584 1606 1672 1636; x_wconf 92\">172F</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_77\" title=\"bbox 1683 1620 1707 1626; x_wconf 72\">—</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_78\" title=\"bbox 1719 1606 1807 1637; x_wconf 80\">180F</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_79\" title=\"bbox 2049 1606 2141 1637; x_wconf 96\">PASS</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_39\" title=\"bbox 383 1631 589 1670; baseline 0.005 -8; x_size 40; x_descenders 8; x_ascenders 9\">\n      <html:span class=\"ocrx_word\" id=\"word_1_80\" title=\"bbox 383 1632 465 1670; x_wconf 93\">Ring</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_81\" title=\"bbox 478 1631 508 1663; x_wconf 93\">&amp;</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_82\" title=\"bbox 522 1631 589 1663; x_wconf 96\">Ball</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_40\" title=\"bbox 373 1690 598 1722; baseline 0.004 -1; x_size 36.900826; x_descenders 5.9008265; x_ascenders 7\">\n      <html:span class=\"ocrx_word\" id=\"word_1_83\" title=\"bbox 373 1690 598 1722; x_wconf 96\">Penetration</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_41\" title=\"bbox 421 1719 2141 1783; baseline 0.001 -32; x_size 35.144093; x_descenders 5.1440926; x_ascenders 9.0778093\">\n      <html:span class=\"ocrx_word\" id=\"word_1_84\" title=\"bbox 421 1746 552 1783; x_wconf 92\">@115F</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_85\" title=\"bbox 869 1719 913 1751; x_wconf 96\">33</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_86\" title=\"bbox 1262 1721 1324 1751; x_wconf 92\">D-5</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_87\" title=\"bbox 1642 1721 1748 1752; x_wconf 96\">30-40</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_88\" title=\"bbox 2048 1721 2141 1752; x_wconf 95\">PASS</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_42\" title=\"bbox 392 1832 2141 1867; baseline 0.002 -3; x_size 35.144093; x_descenders 5.1440926; x_ascenders 9.0778093\">\n      <html:span class=\"ocrx_word\" id=\"word_1_89\" title=\"bbox 392 1833 471 1864; x_wconf 96\">COC</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_90\" title=\"bbox 485 1832 579 1865; x_wconf 95\">Flash</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_91\" title=\"bbox 845 1834 936 1865; x_wconf 96\">550+</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_92\" title=\"bbox 1250 1835 1336 1866; x_wconf 90\">D-92</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_93\" title=\"bbox 1649 1835 1739 1867; x_wconf 96\">550+</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_94\" title=\"bbox 2048 1835 2141 1867; x_wconf 96\">PASS</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_43\" title=\"bbox 418 2061 2222 2101; baseline 0 -7; x_size 41; x_descenders 7; x_ascenders 9\">\n      <html:span class=\"ocrx_word\" id=\"word_1_95\" title=\"bbox 418 2061 550 2094; x_wconf 96\">Tester</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_96\" title=\"bbox 727 2061 903 2094; x_wconf 95\">Matthew</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_97\" title=\"bbox 917 2062 1052 2101; x_wconf 95\">Phillips</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_98\" title=\"bbox 0 0 2550 3300; x_wconf 95\">|</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_99\" title=\"bbox 1130 2063 1223 2086; x_wconf 58\">Owens</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_100\" title=\"bbox 1234 2062 1339 2092; x_wconf 95\">Corning</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_101\" title=\"bbox 1349 2062 1454 2092; x_wconf 91\">Roofing</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_102\" title=\"bbox 1629 2061 1758 2096; x_wconf 96\">Phone</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_103\" title=\"bbox 1963 2064 2222 2095; x_wconf 96\">405-235-2491</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_44\" title=\"bbox 1198 2103 1387 2132; baseline 0 -5; x_size 29; x_descenders 5; x_ascenders 6\">\n      <html:span class=\"ocrx_word\" id=\"word_1_104\" title=\"bbox 1198 2103 1219 2127; x_wconf 89\">&amp;</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_105\" title=\"bbox 1227 2103 1334 2132; x_wconf 94\">Asphalt</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_106\" title=\"bbox 1343 2104 1387 2127; x_wconf 96\">LLC</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_45\" title=\"bbox 466 2141 1417 2181; baseline 0 -14; x_size 30.179752; x_descenders 4.1797519; x_ascenders 9\">\n      <html:span class=\"ocrx_word\" id=\"word_1_107\" title=\"bbox 466 2174 473 2181; x_wconf 50\">.</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_108\" title=\"bbox 1168 2144 1234 2167; x_wconf 96\">3400</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_109\" title=\"bbox 1245 2145 1280 2167; x_wconf 93\">NE</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_110\" title=\"bbox 1289 2141 1323 2167; x_wconf 89\">4*</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_111\" title=\"bbox 1332 2144 1417 2167; x_wconf 96\">Street</html:span>\n     </html:span>\n     <html:span class=\"ocr_line\" id=\"line_1_46\" title=\"bbox 437 2173 2223 2215; baseline 0 -7; x_size 41; x_descenders 6; x_ascenders 12\">\n      <html:span class=\"ocrx_word\" id=\"word_1_112\" title=\"bbox 437 2173 530 2208; x_wconf 96\">Title</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_113\" title=\"bbox 802 2177 977 2215; x_wconf 96\">Operator</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_114\" title=\"bbox 1116 2183 1257 2207; x_wconf 84\">Oklahoma</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_115\" title=\"bbox 1267 2184 1326 2213; x_wconf 96\">City,</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_116\" title=\"bbox 1336 2185 1376 2208; x_wconf 96\">OK</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_117\" title=\"bbox 1385 2185 1468 2208; x_wconf 96\">73117</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_118\" title=\"bbox 1660 2177 1728 2210; x_wconf 96\">Fax</html:span>\n      <html:span class=\"ocrx_word\" id=\"word_1_119\" title=\"bbox 1963 2178 2223 2209; x_wconf 96\">405-239-2846</html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_32\" title=\"bbox 686 1564 689 2248\">\n    <html:p class=\"ocr_par\" id=\"par_1_32\" lang=\"eng\" title=\"bbox 686 1564 689 2248\">\n     <html:span class=\"ocr_line\" id=\"line_1_47\" title=\"bbox 686 1564 689 2248; baseline 0 0; x_size 342; x_descenders -171; x_ascenders 171\">\n      <html:span class=\"ocrx_word\" id=\"word_1_120\" title=\"bbox 686 1564 689 2248; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_33\" title=\"bbox 1090 1564 1095 2250\">\n    <html:p class=\"ocr_par\" id=\"par_1_33\" lang=\"eng\" title=\"bbox 1090 1564 1095 2250\">\n     <html:span class=\"ocr_line\" id=\"line_1_48\" title=\"bbox 1090 1564 1095 2250; baseline 0 0; x_size 343; x_descenders -171.5; x_ascenders 171.5\">\n      <html:span class=\"ocrx_word\" id=\"word_1_121\" title=\"bbox 1090 1564 1095 2250; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_34\" title=\"bbox 1490 1564 1496 2250\">\n    <html:p class=\"ocr_par\" id=\"par_1_34\" lang=\"eng\" title=\"bbox 1490 1564 1496 2250\">\n     <html:span class=\"ocr_line\" id=\"line_1_49\" title=\"bbox 1490 1564 1496 2250; baseline 0 0; x_size 343; x_descenders -171.5; x_ascenders 171.5\">\n      <html:span class=\"ocrx_word\" id=\"word_1_122\" title=\"bbox 1490 1564 1496 2250; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_35\" title=\"bbox 1894 1564 1897 2250\">\n    <html:p class=\"ocr_par\" id=\"par_1_35\" lang=\"eng\" title=\"bbox 1894 1564 1897 2250\">\n     <html:span class=\"ocr_line\" id=\"line_1_50\" title=\"bbox 1894 1564 1897 2250; baseline 0 0; x_size 343; x_descenders -171.5; x_ascenders 171.5\">\n      <html:span class=\"ocrx_word\" id=\"word_1_123\" title=\"bbox 1894 1564 1897 2250; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_36\" title=\"bbox 280 2245 2294 2250\">\n    <html:p class=\"ocr_par\" id=\"par_1_36\" lang=\"eng\" title=\"bbox 280 2245 2294 2250\">\n     <html:span class=\"ocr_line\" id=\"line_1_51\" title=\"bbox 280 2245 2294 2250; baseline 0 0; x_size 2.5; x_descenders -1.25; x_ascenders 1.25\">\n      <html:span class=\"ocrx_word\" id=\"word_1_124\" title=\"bbox 280 2245 2294 2250; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_37\" title=\"bbox 2296 702 2298 812\">\n    <html:p class=\"ocr_par\" id=\"par_1_37\" lang=\"eng\" title=\"bbox 2296 702 2298 812\">\n     <html:span class=\"ocr_line\" id=\"line_1_52\" title=\"bbox 2296 702 2298 812; baseline 0 0; x_size 55; x_descenders -27.5; x_ascenders 27.5\">\n      <html:span class=\"ocrx_word\" id=\"word_1_125\" title=\"bbox 2296 702 2298 812; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n   <html:div class=\"ocr_carea\" id=\"block_1_38\" title=\"bbox 2292 1104 2298 2250\">\n    <html:p class=\"ocr_par\" id=\"par_1_38\" lang=\"eng\" title=\"bbox 2292 1104 2298 2250\">\n     <html:span class=\"ocr_line\" id=\"line_1_53\" title=\"bbox 2292 1104 2298 2250; baseline 0 0; x_size 573; x_descenders -286.5; x_ascenders 286.5\">\n      <html:span class=\"ocrx_word\" id=\"word_1_126\" title=\"bbox 2292 1104 2298 2250; x_wconf 95\"> </html:span>\n     </html:span>\n    </html:p>\n   </html:div>\n  </html:div>\n </html:body>\n</html:html>
    '''
    return txt3


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
