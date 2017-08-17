from __future__ import division
import pdfminer
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator

import PIL
from PIL import Image, ImageOps
import subprocess, sys, os, glob
from operator import itemgetter
import pytesseract
pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files (x86)/Tesseract-OCR/tesseract.exe'

#------------------------------------------------------------------------------------------------------------------------------------------------#
def remove_non_ascii(text):
    return ''.join([i if ord(i) < 128 else '' for i in text])
#------------------------------------------------------------------------------------------------------------------------------------------------#
def convertPdfToImage(pdf):
    prefix = pdf[:-4]
    cmd = "convert -density 600 " + pdf + " " + prefix + ".jpg"
    subprocess.call(cmd, shell=True)
    return [f for f in glob.glob(os.path.join('working', '%s*' % prefix)) if '.jpg' in f]
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getImageData(pdfImage):
    image = PIL.Image.open(pdfImage[0])
    rgbImage = image.convert('RGB')
    pixel = rgbImage.load()
    width, height = image.size
    return width, height, pixel
#------------------------------------------------------------------------------------------------------------------------------------------------#
def extract_layout_by_page(pdf_path):
    laparams = LAParams()

    fp = open(pdf_path, 'rb')
    parser = PDFParser(fp)
    document = PDFDocument(parser)

    if not document.is_extractable:
        raise PDFTextExtractionNotAllowed

    rsrcmgr = PDFResourceManager()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    layouts = []
    for page in PDFPage.create_pages(document):
        interpreter.process_page(page)
        layouts.append(device.get_result())
    return layouts

#------------------------------------------------------------------------------------------------------------------------------------------------#
def flatten(lst):
    return [subelem for elem in lst for subelem in elem]
#------------------------------------------------------------------------------------------------------------------------------------------------#
def extract_characters(element):
    if isinstance(element, pdfminer.layout.LTChar): return [element]
    if any(isinstance(element, i) for i in TEXT_ELEMENTS): return flatten([extract_characters(e) for e in element])
    if isinstance(element, list): return flatten([extract_characters(l) for l in element])
    return []
#------------------------------------------------------------------------------------------------------------------------------------------------#
TEXT_ELEMENTS = [
    pdfminer.layout.LTTextBox,
    pdfminer.layout.LTTextBoxHorizontal,
    pdfminer.layout.LTTextLine,
    pdfminer.layout.LTTextLineHorizontal
]
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getTextBlocks(pdf, horizontalLines):

    pdfImage = convertPdfToImage(pdf)
    imageData = getImageData(pdfImage)
    pdfImageWidth, pdfImageHeight = imageData[0], imageData[1]

    page_layouts = extract_layout_by_page(pdf)

    objects_on_page = set(type(o) for o in page_layouts[0])
    objects_on_page

    current_page = page_layouts[0]
    pdfWidth, pdfHeight = current_page.width, current_page.height

    texts = []
    rects = []
    for e in current_page:
        if isinstance(e, pdfminer.layout.LTTextBoxHorizontal):
            texts.append(e)
        elif isinstance(e, pdfminer.layout.LTRect):
            rects.append(e)

    minX = min([hLine[0] for hLine in horizontalLines])
    maxX = max([hLine[1] for hLine in horizontalLines])

    characters = extract_characters(texts)
    textBlocks = []
    x1, x2, y1, y2 = minX, maxX, 0, 0
    text = ''
    # diffX = []
    for char in  characters:
        # print char
        prevChar = characters[characters.index(char)-1] if characters.index(char) > 0 else char
        if text == '' or characters.index(char) == 0:
            text += char.get_text()
            x1, y1, x2, y2 = char.x0, char.y0, maxX*pdfWidth/pdfImageWidth, char.y1
        elif text != '' and ((char.y0 >= prevChar.y0 and char.y1 <= prevChar.y1) or (char.y0 <= prevChar.y0 and char.y1 >= prevChar.y1)) and int(round(char.x0 - prevChar.x1)) <= 5:
            text += char.get_text()
            x2 = char.x1
        else:
            # if int(round(char.x0 - prevChar.x1)) > 0: diffX.append(int(round(char.x0 - prevChar.x1)))
            x1,y1,x2,y2 = x1*pdfImageWidth/pdfWidth, (pdfHeight-y2)*pdfImageHeight/pdfHeight, x2*pdfImageWidth/pdfWidth, (pdfHeight-y1)*pdfImageHeight/pdfHeight
            x1,y1,x2,y2 = int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))
            textBlocks.append([remove_non_ascii(text), prevChar.fontname, (x1, x2, y1, y2)])
            text = char.get_text()
            x1, y1, x2, y2 = char.x0, char.y0, char.x1, char.y1

    textBlocks = [block for block in textBlocks if block[2][0] >= minX and block[2][0] <= maxX and block[2][1] <= maxX]
    # for block in textBlocks:
    #     print block
    return textBlocks
#------------------------------------------------------------------------------------------------------------------------------------------------#
