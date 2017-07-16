import PIL
from PIL import Image, ImageOps
import subprocess, sys, os, glob
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
                if len(greyPoints) > 300:
                    vLines.append([greyPoints[0], greyPoints[-1]])
                greyPoints = []
    vBorders = []
    vBorder = []
    for vLine in vLines:
        vLineX = vLine[0][0]
        vLineY1 = vLine[0][1]
        vLineY2 = vLine[1][1]
        nextVLineX = vLines[vLines.index(vLine)+1][0][0] if vLines.index(vLine) < len(vLines)-1 else vLine[0][0]
        nextVLineY1 = vLines[vLines.index(vLine)+1][0][1] if vLines.index(vLine) < len(vLines)-1 else vLine[0][1]
        nextVLineY2 = vLines[vLines.index(vLine)+1][1][1] if vLines.index(vLine) < len(vLines)-1 else vLine[1][1]
        if (nextVLineX - vLineX) == 1 and abs(vLineY1 - nextVLineY1) < 10 and abs(vLineY2 - nextVLineY2) < 10:
            vBorder = [vLineX, nextVLineX, min(vLineY1, nextVLineY1), max(vLineY2, nextVLineY2)] if len(vBorder) == 0 else [min(vBorder[0], nextVLineX), nextVLineX, min(vBorder[2], nextVLineY1), max(vBorder[3], nextVLineY2)]
        else:
            vBorders.append(vBorder)
            vBorder = []
    return vBorders
#------------------------------------------------------------------------------------------------------------------------------------------------#
def getHorizontalBorders(imageData, verticalBorders):
    w, h, p = imageData[0], imageData[1], imageData[2]
    vBorderY1, vBorderY2 = [], []
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
                    hLines.append([greyPoints[0], greyPoints[-1]])
                greyPoints = []

    for hLine in hLines:
        print hLine
#------------------------------------------------------------------------------------------------------------------------------------------------#

directory = os.getcwd()
pdf = directory + '/ICT_Catalog_16.pdf'
pdfImage = convertPdfToImage(pdf)
imageData = getImageData(pdfImage)
verticalBorders = getVerticalBorders(imageData)
horizontalBorders = getHorizontalBorders(imageData, verticalBorders)
print verticalBorders
print horizontalBorders
