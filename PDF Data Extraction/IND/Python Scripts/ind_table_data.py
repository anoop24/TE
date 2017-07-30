import PIL
from PIL import Image, ImageOps
import subprocess, sys, os, glob
from operator import itemgetter
import pytesseract
pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files (x86)/Tesseract-OCR/tesseract.exe'
from operator import add
import pandas as pd
import numpy as np
import ind_text_blocks
from ind_text_blocks import getTextBlocks
directory = os.getcwd()
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
def getHorizontalLines(imageData):
    w, h, p = imageData[0], imageData[1], imageData[2]
    hLines = []
    for y in range(h):
        greyPoints = []
        for x in range(w):
            r, g, b = p[x,y][0], p[x,y][1], p[x,y][2]
            if r < 150 and g < 150 and b < 150:
                greyPoints.append([x,y])
            else:
                if len(greyPoints) > 500:
                    hLines.append([greyPoints[0][0], greyPoints[-1][0], greyPoints[-1][1]])
                greyPoints = []
    finalHLines = []
    finalHLine = []
    hLines = sorted(hLines, key=itemgetter(2))
    for hLine in hLines:
        hLineX1 = hLine[0]
        hLineX2 = hLine[1]
        hLineY = hLine[2]
        nextHLine = hLines[hLines.index(hLine)+1] if hLines.index(hLine) < len(hLines)-1 else hLine
        nextHLineY = hLines[hLines.index(hLine)+1][2] if hLines.index(hLine) < len(hLines)-1 else hLine[2]
        nextHLineX1 = hLines[hLines.index(hLine)+1][0] if hLines.index(hLine) < len(hLines)-1 else hLine[0]
        nextHLineX2 = hLines[hLines.index(hLine)+1][1] if hLines.index(hLine) < len(hLines)-1 else hLine[1]
        if (nextHLineY - hLineY) == 1 and abs(hLineX1 - nextHLineX1) < 10 and abs(hLineX2 - nextHLineX2) < 10:
            finalHLine = [min(hLineX1, nextHLineX1), max(hLineX2, nextHLineX2), hLineY, nextHLineY] if len(finalHLine) == 0 else [min(finalHLine[0], nextHLineX1), max(finalHLine[1], nextHLineX2), min(finalHLine[2], nextHLineY), nextHLineY]
        else:
            if len(finalHLine) > 0: finalHLines.append(finalHLine)
            finalHLine = []
    return finalHLines
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getPotentialHorizontalBorders(horizontalLines):
    horizontalLines = sorted(horizontalLines, key=itemgetter(2))
    potentialHorizontalBorders = []
    counter = 0
    for hLine in horizontalLines:
        if hLine[3] - hLine[2] >= 20:
            counter += 1
        if counter == 1:
            potentialHorizontalBorders.append(hLine)
    return potentialHorizontalBorders[2:]
#------------------------------------------------------------------------------------------------------------------------------------------------#
def combineTextBlocks(textBlocks):
    def getKey(item):return item[2][2], item[2][0]
    textBlocks = sorted(textBlocks, key=getKey)

    combinedBlocks = []
    doneBlocks = []
    for block_1 in textBlocks:
        text_1 = block_1[0]
        font_1 = block_1[1]
        text = text_1.strip(' ')
        font = font_1
        block_1_x1, block_1_x2, block_1_y1, block_1_y2 = block_1[2][0], block_1[2][1], block_1[2][2], block_1[2][3]
        x1, x2, y1, y2 = block_1_x1, block_1_x2, block_1_y1, block_1_y2
        if block_1 in doneBlocks: continue
        for block_2 in textBlocks:
            text_2 = block_2[0].strip(' ')
            font_2 = block_2[1]
            block_2_x1, block_2_x2, block_2_y1, block_2_y2 = block_2[2][0], block_2[2][1], block_2[2][2], block_2[2][3]
            block_1_meanX, block_2_meanX = int(round((block_1_x1 + block_1_x2)/2)), int(round((block_2_x1 + block_2_x2)/2))

            if block_1 == block_2  or len(text) <= 1: continue
            if block_2_y1 - block_1_y2 <= 30 and block_2_y1 - block_1_y2 > 0 and (abs(block_1_x1 - block_2_x1) <= 20 or abs(block_1_x2 - block_2_x2) <= 20 or abs(block_1_meanX - block_2_meanX) <= 20):
                text = text + '\n' + text_2
                x1, x2, y1, y2 = min(block_1[2][0], block_2[2][0]), max(block_1[2][1], block_2[2][1]), min(block_1[2][2], block_2[2][2]), max(block_1[2][3], block_2[2][3])
                block_1_x1, block_1_x2, block_1_y1, block_1_y2 = x1, x2, y1, y2
                doneBlocks.append(block_2)
        if text != '':
            combinedBlocks.append([text, font, (x1, x2, y1, y2)])

    return combinedBlocks
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getHeaderTextBlocks(textBlocks, horizontalLines):
    def getKey(item):return item[2][2], item[2][0]
    textBlocks = sorted(textBlocks, key=getKey)

    headerBlocks = []
    for block in textBlocks:
        prevBlock = textBlocks[textBlocks.index(block)-1] if textBlocks.index(block) > 0 else block
        if block[2][3] - block[2][2] >= 80:
            headerBlocks.append(block)

    finalHeaderBlocks = combineTextBlocks(headerBlocks)

    return finalHeaderBlocks
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getNonHeaderTextBlocks(textBlocks, headerTextBlocks):
    nonHeaderBlocks = [block for block in textBlocks if block not in headerTextBlocks]
    return nonHeaderBlocks
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getTables(horizontalLines, headerTextBlocks, nonHeaderTextBlocks):
    allPageElements = [['hLine', '', tuple(hLine)] for hLine in horizontalLines] + [['plainText', block[0], block[2]] for block in nonHeaderTextBlocks] + [['header', block[0], block[2]] for block in headerTextBlocks]
    def getKey(item):return item[2][2]
    allPageElements = sorted(allPageElements, key=getKey)

    minX = min([hLine[0] for hLine in horizontalLines])
    maxX = max([hLine[1] for hLine in horizontalLines])
    # keeping only the text between thick horizontal borders
    indices = []
    for elem in allPageElements:
        if elem[0] == 'hLine' and abs(elem[2][0] - minX) <= 50 and abs(elem[2][1] - maxX) <= 50:
            indices.append(allPageElements.index(elem))
    allPageElements = allPageElements[indices[0]+1:indices[-1]]

    indices = []
    for elem in allPageElements:
        if elem[0] == 'hLine':
            indices.append(allPageElements.index(elem))
    lastHLineIndex = indices[-1]

    allTables = []
    table = []
    for elem in allPageElements:
        if allPageElements.index(elem) > lastHLineIndex:
            if len(table)>= 4 :
                allTables.append(table)
            break
        if elem[0] == 'header':
            if len(table)>= 4 :
                allTables.append(table)
            table = []
            table.append(elem)
        else:
            table.append(elem)
            if allPageElements.index(elem) == len(allPageElements) - 1:
                allTables.append(table)
        if len(allTables) > 0:
            if allTables[-1][1][0] == 'plainText':
                del allTables[-1]

    return allTables
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getTableColumnNames(table):
    minX = min([elem[2][0] for elem in table if elem[0] == 'hLine'])
    maxX = max([elem[2][1] for elem in table if elem[0] == 'hLine'])

    tableHLines = []
    for elem in table:
        if elem[0] == 'hLine' and elem[2][0] == minX and elem[2][1] == maxX and len(tableHLines) < 2:
            tableHLines.append(elem)

    counter = 0
    textColumnElements = []
    lineColumnElements = []
    for elem in table:
        if elem in tableHLines:
            counter+= 1
            continue
        if counter == 1:
            if elem[0] == 'plainText':
                textColumnElements.append(elem)
            if elem[0] == 'hLine':
                lineColumnElements.append(elem)

    columnNameElements = []
    doneElements = []
    for lineElem in lineColumnElements:
        parentElement = []
        childElements = []
        for textElem in textColumnElements:
            if textElem in doneElements: continue

            if textElem[2][0] >= lineElem[2][0] and textElem[2][1] <= lineElem[2][1]:
                if textElem[2][3] <= lineElem[2][2]:
                    parentElement = textElem
                    doneElements.append(textElem)
                elif textElem[2][2] >= lineElem[2][3]:
                    childElements.append(textElem)
                    doneElements.append(textElem)

        for childElement in childElements:
            columnNameElements.append(['plainText', parentElement[1] + ' - ' + childElement[1], childElement[2]])

    for textElem in textColumnElements:
        if textElem not in doneElements:
            columnNameElements.append(textElem)

    finalColumnNameElements = []
    doneElements = []
    for elem_1 in columnNameElements:
        counter = 0
        mean_1_x = int(round((elem_1[2][0] + elem_1[2][1])/2))

        if elem_1 in doneElements: continue
        for elem_2 in columnNameElements:
            if elem_1 == elem_2: continue
            mean_2_x = int(round((elem_2[2][0] + elem_2[2][1])/2))
            if abs(mean_1_x - mean_2_x) <= 20:
                counter = 1
                x1, x2, y1, y2 = min(elem_1[2][0], elem_2[2][0]), max(elem_1[2][1], elem_2[2][1]), elem_1[2][2], elem_2[2][3]
                finalColumnNameElements.append(['plainText', elem_1[1] + ' / ' + elem_2[1], (x1,x2,y1,y2)])
                doneElements.append(elem_2)

        if counter == 0:
            finalColumnNameElements.append(elem_1)
        doneElements.append(elem_1)

    def getKey(item):return item[2][0]
    finalColumnNameElements = sorted(finalColumnNameElements, key=getKey)
    columnNamesText = []
    for colElem in finalColumnNameElements:
        columnNamesText.append(remove_non_ascii(colElem[1].replace('\n', ' ')))
        print columnNamesText[-1]


    return columnNamesText, finalColumnNameElements
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getTableColumnValues(table, tableColumnNames):
    columnNames= tableColumnNames
    maxY = max([columnName[2][3] for columnName in columnNames])

    def getKey(item):return item[2][2]
    table = sorted(table, key=getKey)

    allColumnValues = []
    for elem in table:
        if elem[2][3] > maxY:
            allColumnValues.append(elem)

    currentRowElements = []
    rows = []
    columnValuesText = []
    def getKey(item):return item[2][0]
    for elem in allColumnValues:
        if elem[0] == 'hLine':
            row = []
            for colElem in columnNames:
                rowText = ''
                x1, x2, y1, y2 = colElem[2][0], colElem[2][1], colElem[2][2], colElem[2][3]
                for rowElem in currentRowElements:
                    colElem_x1, colElem_x2, rowElem_x1, rowElem_x2 = colElem[2][0], colElem[2][1], rowElem[2][0], rowElem[2][1]
                    if (colElem_x1 >= rowElem_x1 and colElem_x1 <= rowElem_x2) or (colElem_x2 >= rowElem_x1 and colElem_x2 <= rowElem_x2) or (rowElem_x1 >= colElem_x1 and rowElem_x1 <= colElem_x2) or (rowElem_x2 >= colElem_x1 and rowElem_x2 <= colElem_x2):
                        rowText = rowText + ' / ' + rowElem[1]
                        x1, x2, y1, y2 = min(x1, rowElem[2][0]), min(x2, rowElem[2][1]), min(y1, rowElem[2][2]), min(y2, rowElem[2][3])
                row.append(['plainText', rowText.strip(' / '), (x1,x2,y1,y2)])

            currentRowElements = []
            if allColumnValues.index(elem) == len(allColumnValues)-1:
                if len(row) > 0:
                    row = sorted(row, key=getKey)
                    rows.append(row)
                    columnValuesText.append([cell[1] for cell in row])

        else:
            if len(row) > 0:
                row = sorted(row, key=getKey)
                rows.append(row)
                columnValuesText.append([cell[1] for cell in row])
                row = []
            currentRowElements.append(elem)


    del columnValuesText[0]

    return columnValuesText, rows
#------------------------------------------------------------------------------------------------------------------------------------------------#

directory = os.getcwd()
pageNumber = 0
for pdfPage in range(40, 41):
    pageNumber += 1
    pdf = directory + '\\PDF_Split\\IND_Catalog_%d.pdf' %(pdfPage)
    pdfImage = convertPdfToImage(pdf)
    imageData = getImageData(pdfImage)
    pdfImageWidth, pdfImageHeight = imageData[0], imageData[1]
    horizontalLines = getHorizontalLines(imageData)
    textBlocks = getTextBlocks(pdf, horizontalLines)
    combinedTextBlocks = combineTextBlocks(textBlocks)
    headerTextBlocks = getHeaderTextBlocks(textBlocks, horizontalLines)
    nonHeaderTextBlocks = getNonHeaderTextBlocks(combinedTextBlocks, headerTextBlocks)
    tables = getTables(horizontalLines, headerTextBlocks, nonHeaderTextBlocks)

    tableNumber = 0
    for table in tables:
        tableNumber += 1
        tableColumnNamesText = getTableColumnNames(table)[0]
        tableColumnNames = getTableColumnNames(table)[1]
        tableColumnValuesText = getTableColumnValues(table, tableColumnNames)[0]
        tableColumnValues = getTableColumnValues(table, tableColumnNames)[1]

        data = pd.DataFrame(data=tableColumnValuesText, columns=tableColumnNamesText)
        data.to_csv(directory + '/Output/' + str(pageNumber) + '_' + str(tableNumber) + '.txt', sep='\t', encoding='utf-8', index=None)
        print '\n\n'
