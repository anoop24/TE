import PIL
from PIL import Image, ImageOps
import subprocess, sys, os, glob
from operator import itemgetter
import pytesseract
pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files (x86)/Tesseract-OCR/tesseract.exe'
from operator import add
import pandas as pd
import numpy as np
directory = os.getcwd()
#------------------------------------------------------------------------------------------------------------------------------------------------#
def remove_non_ascii(text):
    return ''.join([i if ord(i) < 128 else '' for i in text])
#------------------------------------------------------------------------------------------------------------------------------------------------#
def convertPdfToImage(pdf):
    prefix = pdf[:-4]
    cmd = '"C:\\Program Files\\gs\\gs9.21\\bin\\gswin64c.exe" -o "' + prefix + '_GS.pdf" -sDEVICE=pdfwrite -dFILTERIMAGE -dDELAYBIND -dWRITESYSTEMDICT remove-images.ps ' + pdf
    subprocess.call(cmd, shell=True)
    newPdf = prefix + '_GS.pdf'
    cmd = "convert -density 600 " + newPdf + " " + prefix + ".jpg"
    subprocess.call(cmd, shell=True)
    subprocess.call('cls', shell=True)
    return [f for f in glob.glob(os.path.join('working', '%s*' % prefix)) if '.jpg' in f]
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getImageData(pdfImage):
    image = PIL.Image.open(pdfImage[0])
    rgbImage = image.convert('RGB')
    pixel = rgbImage.load()
    width, height = image.size
    return width, height, pixel
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getVerticalBorders(imageData):
    w, h, p = imageData[0], imageData[1], imageData[2]
    vLines = []
    for x in range(w):
        greyPoints = []
        for y in range(h):
            r, g, b = p[x,y][0], p[x,y][1], p[x,y][2]
            if r < 150 and g < 150 and b < 150:
                greyPoints.append([x,y])
            else:
                if len(greyPoints) > 100:
                    vLines.append([greyPoints[0][0], greyPoints[0][1], greyPoints[-1][1]])
                greyPoints = []
    vBorders = []
    vBorder = []
    vLines = sorted(vLines, key=itemgetter(1))
    for vLine in vLines:
        vLineX = vLine[0]
        vLineY1 = vLine[1]
        vLineY2 = vLine[2]
        nextVLine = vLines[vLines.index(vLine)+1] if vLines.index(vLine) < len(vLines)-1 else vLine
        nextVLineX = vLines[vLines.index(vLine)+1][0] if vLines.index(vLine) < len(vLines)-1 else vLine[0]
        nextVLineY1 = vLines[vLines.index(vLine)+1][1] if vLines.index(vLine) < len(vLines)-1 else vLine[1]
        nextVLineY2 = vLines[vLines.index(vLine)+1][2] if vLines.index(vLine) < len(vLines)-1 else vLine[2]
        # print vLine, nextVLine
        if (nextVLineX - vLineX) == 1 and abs(vLineY1 - nextVLineY1) < 10 and abs(vLineY2 - nextVLineY2) < 10:
            vBorder = [vLineX, nextVLineX, min(vLineY1, nextVLineY1), max(vLineY2, nextVLineY2)] if len(vBorder) == 0 else [min(vBorder[0], nextVLineX), nextVLineX, min(vBorder[2], nextVLineY1), max(vBorder[3], nextVLineY2)]
        else:
            if len(vBorder) > 0: vBorders.append(vBorder)
            vBorder = []
    # vBorders = sorted(vBorders, key=itemgetter(0,2))
    return vBorders
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getPotentialTables(verticalBorders):
    tables = []
    table = []
    verticalBorders = sorted(verticalBorders, key=itemgetter(3))
    for vBorder in verticalBorders:
        nextVBorder = verticalBorders[verticalBorders.index(vBorder)+1] if verticalBorders.index(vBorder) < len(verticalBorders)-1 else vBorder
        vBorderY2 = vBorder[3]
        nextVBorderY2 = verticalBorders[verticalBorders.index(vBorder)+1][3] if verticalBorders.index(vBorder) < len(verticalBorders)-1 else vBorder[3]
        if len(table) == 0: table.append(vBorder)
        if abs(vBorderY2 - nextVBorderY2) <= 10 and vBorder != nextVBorder:
            table.append(nextVBorder)
        else:
            tables.append(sorted(table, key=itemgetter(0)))
            table = []
    return tables   #returns lists of vertical borders
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getHorizontalBorders(imageData, potentialTable):
    w, h, p = imageData[0], imageData[1], imageData[2]
    vBorderY1, vBorderY2 = [], []
    verticalBorders = potentialTable
    for vBorder in verticalBorders:
        vBorderY1.append(vBorder[2])
        vBorderY2.append(vBorder[3])
    minY, maxY = min(vBorderY1), max(vBorderY2)
    hLines = []
    for y in range(minY, maxY):
        greyPoints = []
        for x in range(w):
            r, g, b = p[x,y][0], p[x,y][1], p[x,y][2]
            if r < 150 and g < 150 and b < 150:
                greyPoints.append([x,y])
            else:
                if len(greyPoints) > 300:
                    hLines.append([greyPoints[0][0], greyPoints[-1][0], greyPoints[-1][1]])
                greyPoints = []
    # print hLines
    hLines = sorted(hLines, key=itemgetter(0))
    hBorders = []
    hBorder = []
    for hLine in hLines:
        hLineY = hLine[2]
        hLineX1 = hLine[0]
        hLineX2 = hLine[1]
        nextHLineY = hLines[hLines.index(hLine)+1][2] if hLines.index(hLine) < len(hLines)-1 else hLine[2]
        nextHLineX1 = hLines[hLines.index(hLine)+1][0] if hLines.index(hLine) < len(hLines)-1 else hLine[0]
        nextHLineX2 = hLines[hLines.index(hLine)+1][1] if hLines.index(hLine) < len(hLines)-1 else hLine[1]
        if (nextHLineY - hLineY) == 1 and abs(hLineX1 - nextHLineX1) < 10 and abs(hLineX2 - nextHLineX2) < 10:
            hBorder = [min(hLineX1, nextHLineX1), max(hLineX2, nextHLineX2), hLineY, nextHLineY] if len(hBorder) == 0 else [min(hBorder[0], nextHLineX1), max(hBorder[1], nextHLineX2), min(hBorder[2], nextHLineY), nextHLineY]
        else:
            hBorder = [min(hLineX1, nextHLineX1), max(hLineX2, nextHLineX2), hLineY, nextHLineY] if len(hBorder) == 0 else hBorder
            hBorders.append(hBorder)
            hBorder = []
    return hBorders
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getActualTables(imageData, potentialTables):
    tables = []
    for potentialTable in potentialTables:
        horizontalBorders = getHorizontalBorders(imageData, potentialTable)
        if len(horizontalBorders) > 0:
            # adding the external vertical borders
            potentialTable = [[horizontalBorders[0][0], horizontalBorders[0][0]+1, horizontalBorders[0][2], horizontalBorders[1][3]]] + potentialTable
            potentialTable.append([horizontalBorders[-1][1], horizontalBorders[-1][1]-1, horizontalBorders[-1][2], horizontalBorders[-1][3]])
            tables.append(potentialTable)
    return tables
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getSplitHorizontalBorders(actualTable, imageData):
    horizontalBorders = getHorizontalBorders(imageData, actualTable)
    hSplitBorders = []
    for vBorder in actualTable:
        nextVBorder = actualTable[actualTable.index(vBorder)+1] if actualTable.index(vBorder) < len(actualTable)-1 else vBorder
        for hBorder in horizontalBorders:
            hBorderX1, hBorderX2 = hBorder[0], hBorder[1]
            vBorderX1, nextVBorderX2 = vBorder[0], nextVBorder[1]
            if vBorderX1 >= hBorderX1 and nextVBorderX2 <= hBorderX2 and vBorder != nextVBorder:
                hSplitBorders.append([vBorderX1, nextVBorderX2, hBorder[2], hBorder[3]])
    hSplitBorders = sorted(hSplitBorders, key=itemgetter(0,2))
    return hSplitBorders
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getActualCells(hSplitBorders):
    actualCells = []
    for hSplitBorder in hSplitBorders:
        nextHSplitBorder = hSplitBorders[hSplitBorders.index(hSplitBorder)+1] if hSplitBorders.index(hSplitBorder) < len(hSplitBorders)-1 else hSplitBorder
        if nextHSplitBorder[3] - hSplitBorder[2] < 10:
            continue
        actualCells.append([hSplitBorder[0], hSplitBorder[1], hSplitBorder[2], nextHSplitBorder[3]])
    return actualCells
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getFinalCells(actualCells, pdfImage):
    finalCells = []
    cellHeight = []
    for actualCell in actualCells:
        cellHeight.append(actualCell[3] - actualCell[2])
    minCellHeight = min(cellHeight)
    for actualCell in actualCells:
        cellMergeCount = int(round(1.0*(actualCell[3]-actualCell[2])/(1.0*minCellHeight)))
        image = PIL.Image.open(pdfImage[0])
        imageCrop = image.crop((actualCell[0], actualCell[2], actualCell[1], actualCell[3]))
        cellValue = pytesseract.image_to_string(imageCrop)
        finalCells.append([actualCell, cellValue, cellMergeCount])
    return finalCells
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getColumnValues(imageData, finalCells, actualTable):
    colCount = len(actualTable) - 1
    columns = []
    column = []
    finalCells = sorted(finalCells, key=itemgetter(0,2))
    for finalCell in finalCells:
        cellValue, cellMergeCount = finalCell[1], finalCell[2]
        nextFinalCell = finalCells[finalCells.index(finalCell) + 1] if finalCells.index(finalCell) < len(finalCells)-1 else finalCell
        if finalCell[0][0] == nextFinalCell[0][0] and finalCell[0] != nextFinalCell[0]:
            for i in range(cellMergeCount):
                column.append(remove_non_ascii(cellValue))
        else:
            for i in range(cellMergeCount):
                column.append(remove_non_ascii(cellValue))
            columns.append(column)
            column = []
    return columns
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getColumnNames(pdfImage, imageData, actualTable, actualCells, prevTableBottom):
    w, h, p = imageData[0], imageData[1], imageData[2]
    headerCells = []
    parentHeaderCells = []
    parentHeaderFlags = []
    headerZoneY = []
    actualTable = sorted(actualTable, key=itemgetter(0))
    minY = actualCells[0][2]
    for vBorder in actualTable:
        vBorder[2] = minY
        nextVBorder = actualTable[actualTable.index(vBorder)+1] if actualTable.index(vBorder) < len(actualTable)-1 else vBorder
        nextVBorder[2] = minY
        vBorderX1, nextVBorderX2, vBorderY1 = vBorder[0], nextVBorder[1], vBorder[2]
        bluePoints = []
        greyPoints = []
        # print vBorderX1, nextVBorderX2, vBorderY1, prevTableBottom
        if vBorder == nextVBorder: continue
        for x in range(vBorderX1+10, nextVBorderX2-10):
            for y in range(vBorderY1-10, prevTableBottom, -1):
                r, g, b = p[x,y][0], p[x,y][1], p[x,y][2]
                if b-r > 50 and b-g > 50 and b>100:
                    bluePoints.append(y)
                elif r<150 and g<150 and b<150:
                    greyPoints.append(y)
        bluePoints = list(set(bluePoints))
        greyPoints = list(set(greyPoints))
        headerZoneY.append(min(bluePoints))
        if len(greyPoints) > 0:
            parentHeaderFlags.append(1)
        else:
            parentHeaderFlags.append(0)
            greyPoints = [0]
        headerCells.append([vBorderX1, nextVBorderX2, max(min(bluePoints), max(greyPoints)), vBorderY1])

    headerZone = [actualTable[0][0], actualTable[-1][1], min(headerZoneY), actualTable[0][2]]
    headerValues =  []
    for headerCell in headerCells:
        image = PIL.Image.open(pdfImage[0])
        imageCrop = image.crop((headerCell[0], headerCell[2], headerCell[1], headerCell[3]))
        headerCellValue = pytesseract.image_to_string(imageCrop)
        headerValues.append(remove_non_ascii(headerCellValue))
    return headerZone, headerValues
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getParentHeaders(headerZone, imageData, actualTable, pdfImage):
    hLines = []
    p = imageData[2]
    for y in range(headerZone[2], headerZone[3]):
        greyPoints = []
        for x in range(headerZone[0]-10, headerZone[1]+10):
            r, g, b = p[x,y][0], p[x,y][1], p[x,y][2]
            if r < 150 and g < 150 and b < 150:
                greyPoints.append([x,y])
            else:
                if len(greyPoints) > 300:
                    hLines.append([greyPoints[0][0], greyPoints[-1][0], greyPoints[-1][1]])
                greyPoints = []

    if len(hLines) == 0: return None
    parentBorder = hLines[0]
    bluePoints = []
    for y in range(headerZone[2], parentBorder[2]):
        for x in range(parentBorder[0], parentBorder[1]):
            r, g, b = p[x,y][0], p[x,y][1], p[x,y][2]
            if b-r > 50 and b-g > 50 and b>100:
                bluePoints.append(x)
    parentHeaders = []
    parentHeader = []
    bluePoints = list(set(bluePoints))
    bluePoints.sort()
    for point in bluePoints:
        nextPoint = bluePoints[bluePoints.index(point)+1] if bluePoints.index(point) < len(bluePoints)-1 else point
        if len(parentHeaders) == 0: parentHeader.append(point)
        if bluePoints.index(point) == len(bluePoints)-1: parentHeaders.append([min(parentHeader), max(parentHeader), headerZone[2], parentBorder[2]])
        if nextPoint - point < 100:
            parentHeader.append(point)
        else:
            parentHeaders.append([min(parentHeader), max(parentHeader), headerZone[2], parentBorder[2]])
            parentHeader = []

    finalParentHeaders = []
    minX = parentBorder[0]
    for header in parentHeaders:
        offsetLeft = header[0] - minX
        offsetRight = offsetLeft
        finalParentHeaders.append([minX, header[1] + offsetRight, header[2], header[3]])
        minX = header[1] + offsetRight

    parentHeaderValues = []
    for vBorder in actualTable:
        nextVBorder = actualTable[actualTable.index(vBorder)+1] if actualTable.index(vBorder) < len(actualTable)-1 else vBorder
        cellValue = ''
        for header in finalParentHeaders:
            if vBorder[0] >= header[0]-10 and nextVBorder[1] <= header[1]+10:
                image = PIL.Image.open(pdfImage[0])
                imageCrop = image.crop((header[0], header[2], header[1], header[3]))
                cellValue = pytesseract.image_to_string(imageCrop)
        if actualTable.index(vBorder) < len(actualTable)-1:
            parentHeaderValues.append(remove_non_ascii(cellValue))
    return parentHeaderValues
#------------------------------------------------------------------------------------------------------------------------------------------------#
def isTopRowHeaders(actualTable, actualCells, imageData):
    p = imageData[2]
    actualCells = sorted(actualCells, key=itemgetter(2))
    colCount = len(actualTable) - 1
    x1, x2 = actualCells[0][0], actualCells[colCount-1][1]
    y1, y2 = actualCells[0][2], actualCells[colCount-1][3]
    bluePoints = []
    for y in range(y1, y2):
        for x in range(x1, x2):
            r, g, b = p[x,y][0], p[x,y][1], p[x,y][2]
            if b-r > 50 and b-g > 50 and b>100:
                bluePoints.append([x,y])
    if len(bluePoints) > 0:
        for i in range(colCount):
            del actualCells[0]
    return actualCells
#------------------------------------------------------------------------------------------------------------------------------------------------#

directory = os.getcwd()
for pdfPage in range(18, 19):
    pdf = directory + '\\Catalogs\\ICT_Catalog_%d.pdf' %(pdfPage)
    subprocess.call('cls', shell=True)
    try:
        pdfImage = convertPdfToImage(pdf)
        product_category = pytesseract.image_to_string(PIL.Image.open(pdfImage[0]).crop((0,0,5000,500)))
        imageData = getImageData(pdfImage)
        verticalBorders = getVerticalBorders(imageData)
        potentialTables = getPotentialTables(verticalBorders)
        actualTables = getActualTables(imageData, potentialTables)
        counter = 0
        print 'Page : ' + str(pdfPage)
        for actualTable in actualTables:
            counter += 1
            sys.stdout.write("\033[K")
            sys.stdout.write("Table: %d ...getting previous table bottom" % (counter))
            sys.stdout.flush()
            if actualTables.index(actualTable) > 0:
                prevActualTable = actualTables[actualTables.index(actualTable)-1]
                prevTableBottom = prevActualTable[0][3]
            else:
                prevTableBottom = 500

            sys.stdout.write("\033[K")
            sys.stdout.write("Table: %d ...getting horizontal split borders" % (counter))
            sys.stdout.flush()
            hSplitBorders = getSplitHorizontalBorders(actualTable, imageData)

            sys.stdout.write("\033[K")
            sys.stdout.write("Table: %d ...getting actual cells" % (counter))
            sys.stdout.flush()
            actualCells = getActualCells(hSplitBorders)

            sys.stdout.write("\033[K")
            sys.stdout.write("Table: %d ...getting actual cells after removing top header row" % (counter))
            sys.stdout.flush()
            actualCells = isTopRowHeaders(actualTable, actualCells, imageData)

            sys.stdout.write("\033[K")
            sys.stdout.write("Table: %d ...getting final cells" % (counter))
            sys.stdout.flush()
            finalCells = getFinalCells(actualCells, pdfImage)

            sys.stdout.write("\033[K")
            sys.stdout.write("Table: %d ...getting column values" % (counter))
            sys.stdout.flush()
            columnValues = getColumnValues(imageData, finalCells, actualTable)

            sys.stdout.write("\033[K")
            sys.stdout.write("Table: %d ...getting header values" % (counter))
            sys.stdout.flush()
            headerZone, headerValues = getColumnNames(pdfImage, imageData, actualTable, actualCells, prevTableBottom)[0], getColumnNames(pdfImage, imageData, actualTable, actualCells, prevTableBottom)[1]

            sys.stdout.write("\033[K")
            sys.stdout.write("Table: %d ...getting parent header values" % (counter))
            sys.stdout.flush()
            parentHeaderValues = getParentHeaders(headerZone, imageData, actualTable, pdfImage)

            sys.stdout.write("\033[K")
            sys.stdout.write("Table: %d ...getting final combined header values" % (counter))
            sys.stdout.flush()
            if parentHeaderValues is not None:
                columnNames = []
                for i in range(len(headerValues)):
                    finalHeaderValue = (str(parentHeaderValues[i]) + ' - ' + str(headerValues[i])).strip(' - ')
                    columnNames.append(finalHeaderValue.replace('\n', ' ').strip(' '))
            else:
                columnNames = [headerValue.replace('\n', ' ').strip(' ') for headerValue in headerValues]

            sys.stdout.write("\033[K")
            sys.stdout.write("Table: %d \r...getting results into dataframes and exporting as txt" % (counter))
            sys.stdout.flush()
            dataRows = []
            for i in range(len(columnValues[0])):
                dataRow = []
                dataRow.append(product_category)
                for j in range(len(columnNames)):
                    dataRow.append(columnValues[j][i].replace('\n', ' '))
                dataRows.append(dataRow)
            columnNames = ['product_category'] + columnNames
            df = pd.DataFrame(data=dataRows, columns=columnNames)
            df.set_index('product_category', inplace=True)
            print '\rTable : ' + str(counter) + '...exporting the dataframe',
            fileName = directory + '\\OUTPUT\\%d_%d.txt' % (pdfPage, counter)
            df.to_csv(fileName, sep='\t', encoding='utf-8')
    except:
        print 'No Data'
        pass
