import PIL
from PIL import Image, ImageOps
import subprocess, sys, os, glob
from operator import itemgetter
import pytesseract
pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files (x86)/Tesseract-OCR/tesseract.exe'
from operator import add
import pandas as pd
import numpy as np
import ind_test
from ind_test import getTextBlocks
import time
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
    print w,h,p
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

    hLines = sorted(hLines, key=itemgetter(2))
    finalHLines = []
    finalHLine = []
    doneLines = []
    for hLine in hLines:
        finalHLine = []
        if hLine in doneLines: continue
        firstHLine = hLine
        for nextHLine in hLines:
            if nextHLine in doneLines: continue
            if hLines.index(hLine) < hLines.index(nextHLine) and nextHLine[2] - hLine[2] == 1 and abs(nextHLine[0] - hLine[0]) <= 10 and abs(nextHLine[1] - hLine[1]) <= 10:
                finalHLine = [min(firstHLine[0], nextHLine[0]), max(firstHLine[1], nextHLine[1]), firstHLine[2], nextHLine[2]]
                hLine = nextHLine
                doneLines.append(nextHLine)
        finalHLines.append(finalHLine)
        doneLines.append(hLine)

    return finalHLines
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getVerticalLines(imageData):
    w, h, p = imageData[0], imageData[1], imageData[2]
    vLines = []
    for x in range(w):
        greyPoints = []
        for y in range(h):
            r, g, b = p[x,y][0], p[x,y][1], p[x,y][2]
            if r < 150 and g < 150 and b < 150:
                greyPoints.append([x,y])
            else:
                if len(greyPoints) > 200:
                    vLines.append([greyPoints[0][0], greyPoints[0][1], greyPoints[-1][1]])
                greyPoints = []
    finalVLines = []
    finalVLine = []
    vLines = sorted(vLines, key=itemgetter(1))
    for vLine in vLines:
        vLineY1 = vLine[1]
        vLineY2 = vLine[2]
        vLineX = vLine[0]
        nextVLine = vLines[vLines.index(vLine)+1] if vLines.index(vLine) < len(vLines)-1 else vLine
        nextVLineX = vLines[vLines.index(vLine)+1][0] if vLines.index(vLine) < len(vLines)-1 else vLine[0]
        nextVLineY1 = vLines[vLines.index(vLine)+1][1] if vLines.index(vLine) < len(vLines)-1 else vLine[1]
        nextVLineY2 = vLines[vLines.index(vLine)+1][2] if vLines.index(vLine) < len(vLines)-1 else vLine[2]
        if (nextVLineX - vLineX) == 1 and abs(vLineY1 - nextVLineY1) < 10 and abs(vLineY2 - nextVLineY2) < 10:
            finalVLine = [vLineX, nextVLineX, min(vLineY1, nextVLineY1), max(vLineY2, nextVLineY2)] if len(finalVLine) == 0 else [min(finalVLine[0], nextVLineX), nextVLineX, min(finalVLine[2], nextVLineY1), max(finalVLine[3], nextVLineY2)]
        else:
            if len(finalVLine) > 0: finalVLines.append(finalVLine)
            finalVLine = []

    def getKey(item):return item[2], item[0]
    finalVLines = sorted(finalVLines, key=getKey)

    return finalVLines
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getFinalHorizontalLines(horizontalLines, verticalLines):
    finalHorizotalLines = []
    for hLine in horizontalLines:
        counter = 0
        for vLine in verticalLines:
            if (hLine[0] <= vLine[0] <= hLine[1] or hLine[0] <= vLine[1] <= hLine[1]) and (vLine[2] <= hLine[2] <= vLine[3] or vLine[2] <= hLine[3] <= vLine[3]):
                counter += 1
                break
        if counter == 0:
            finalHorizotalLines.append(hLine)
    return finalHorizotalLines
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getPotentialTables(horizontalLines):
    def getKey(item):return item[2], item[0]
    horizontalLines = sorted(horizontalLines, key=getKey)

    tables = []
    table = []
    hLineHeight, hLineWidth, headerLineWidth = 0, 0, 0
    counter = 0
    for hLine in horizontalLines:
        hLineHeight = hLine[3] - hLine[2]
        hLineWidth = hLine[1] - hLine[0]
        print hLine, hLineHeight
        if hLineHeight >= 10:
            continue
        elif hLineHeight >= 5 and counter == 0:
            table.append(['tableHeader', hLine])
            headerLineWidth = hLineWidth
            counter += 1
        elif counter == 1 and abs(headerLineWidth - hLineWidth) > 20:
            table.append(['tableHeader', hLine])
        elif counter == 1 and abs(headerLineWidth - hLineWidth) <= 20:
            table.append(['tableHeader', hLine])
            counter += 1
        elif hLineHeight >=5 and counter == 2:
            table.append(['tableFooter', hLine])
            tables.append(table)
            counter = 0
            table = []
        else:
            table.append(['tableLine', hLine])
    print '\n\n'
    for table in tables:
        print table
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
                if any([True if block_1_y2 <= hLine[2] <= block_2_y1 and hLine[0] <= block_1_x1 <= hLine[1] else False for hLine in horizontalLines]): continue
                text = text + '\n' + text_2
                x1, x2, y1, y2 = min(block_1[2][0], block_2[2][0]), max(block_1[2][1], block_2[2][1]), min(block_1[2][2], block_2[2][2]), max(block_1[2][3], block_2[2][3])
                block_1_x1, block_1_x2, block_1_y1, block_1_y2 = x1, x2, y1, y2
                doneBlocks.append(block_2)
        if text != '':
            combinedBlocks.append([text, font, (x1, x2, y1, y2)])

    return combinedBlocks
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getTables(horizontalLines, combinedTextBlocks):
    allPageElements = [['hLine', '', '', hLine] for hLine in horizontalLines] + [['textBlock', block[1], block[0], block[2]] for block in combinedTextBlocks]
    def getKey(item):return item[3][2], item[3][0]
    allPageElements = sorted(allPageElements, key=getKey)

    potentialHeaderElements = []
    for elem in allPageElements:
        # print elem
        if 'bold' in elem[1].lower() or 'hLine' in elem[0]:
            potentialHeaderElements.append(elem)

    potentialHeaderBorders = []
    doneElements = []
    for elem in potentialHeaderElements:
        if elem[0] == 'hLine' and elem[3][3] - elem[3][2] <= 10 and elem not in doneElements:
            hLineWidth = elem[3][1] - elem[3][0]
            for nextElem in potentialHeaderElements:
                if nextElem[0] == 'hLine' and nextElem[3][3] - nextElem[3][2] <= 10 and potentialHeaderElements.index(nextElem) > potentialHeaderElements.index(elem) and abs(nextElem[3][1] - nextElem[3][0] - hLineWidth) <= 20:
                    potentialHeaderBorders.append([elem, nextElem])
                    doneElements.append(elem)
                    # doneElements.append(nextElem)
                    break

    headerZones = []
    headerFont = ''
    for border in potentialHeaderBorders:
        hLine = border[0]
        nextHLine = border[1]
        hLineIndex = allPageElements.index(hLine)
        nextHLineIndex = allPageElements.index(nextHLine)

        potentialHeaderZone = []
        for elem in allPageElements[hLineIndex+1:nextHLineIndex]:
            potentialHeaderZone.append(elem)

        if len(potentialHeaderZone) >= 2:
            if all([True if 'bold' in elem[1].lower() else False for elem in potentialHeaderZone if elem[0] == 'textBlock']):
                if len(headerZones) == 0:
                    headerFont = elem[1]
                if elem[1] == headerFont:
                    headerZone = [hLine] + potentialHeaderZone + [nextHLine]
                    headerZones.append(headerZone)


    for zone in headerZones:
        for elem in zone:
            print elem
        print '\n'
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

    # for elem in allColumnValues:
    #     print elem

    currentRowElements = []
    rows = []
    columnValuesText = []
    def getKey(item):return item[2][0]
    for elem in allColumnValues:
        if elem[0] == 'hLine':
            if elem[2][1] - elem[2][0] <= 4000: continue
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
directory = 'C:\\Users\\Aanoop.Sharma\\Desktop\\IND_DATA_EXTRACTION_1'
pageNumber = 6
for pdfPage in range(19, 20):
    pageNumber += 1
    # try:
    pdf = directory + '\\PDF_Split\\IND_Catalog_1_%d.pdf' %(pdfPage)
    pdfImage = convertPdfToImage(pdf)
    imageData = getImageData(pdfImage)
    pdfImageWidth, pdfImageHeight = imageData[0], imageData[1]
    horizontalLines = getHorizontalLines(imageData)
    verticalLines = getVerticalLines(imageData)
    horizontalLines = getFinalHorizontalLines(horizontalLines, verticalLines)
    textBlocks = getTextBlocks(pdf, horizontalLines)
    combinedTextBlocks = combineTextBlocks(textBlocks)
    # tables = getPotentialTables(horizontalLines)
    tables = getTables(horizontalLines, combinedTextBlocks)
        # print horizontalLines
        # for table in tables:
        #     print table
        #     print '\n\n'
        # headerTextBlocks = getHeaderTextBlocks(textBlocks, horizontalLines)
        # nonHeaderTextBlocks = getNonHeaderTextBlocks(combinedTextBlocks, headerTextBlocks)
        # tables = getTables(horizontalLines, headerTextBlocks, nonHeaderTextBlocks)
        #
        # tableNumber = 0
        # for table in tables:
        #     tableNumber += 1
        #     # print '\b'*(len(cmdString)),
        #     cmdString = 'page number :: ' + str(pageNumber) + ', table number :: ' + str(tableNumber)
        #     for char in cmdString:
        #         print '\b' + char,
        #         print '\b',
        #         time.sleep(0.05)
        #     print '\r'
        #     tableColumnNamesText = getTableColumnNames(table)[0]
        #     tableColumnNames = getTableColumnNames(table)[1]
        #     tableColumnValuesText = getTableColumnValues(table, tableColumnNames)[0]
        #     tableColumnValues = getTableColumnValues(table, tableColumnNames)[1]
        #
        #     data = pd.DataFrame(data=tableColumnValuesText, columns=tableColumnNamesText)
        #     data.to_csv(directory + '/Output/' + str(pageNumber) + '_' + str(tableNumber) + '.txt', sep='\t', encoding='utf-8', index=None)
    # except:
        # pass
