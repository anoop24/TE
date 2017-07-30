import pandas as pd
import os, os.path
import inspect
import nltk
from nltk.corpus import words
import math
#-------------------------------------------------------------------------------------------------------------------------------------------------#
partsData = pd.read_csv('part_data.txt', '\t')
partList = list(partsData['part_number'])
#-------------------------------------------------------------------------------------------------------------------------------------------------#
def isPartNumber(value):
    if value in partList:
        return 1
    else:
        return 0
#-------------------------------------------------------------------------------------------------------------------------------------------------#
def reshapeDataFrame(dataFrame):
    partFields = []
    stackFields = []
    for column in dataFrame.columns:
        tokens = [token for token in [str(cellValue).split(' ') for cellValue in list(dataFrame[column])]]
        finalTokens = []
        for i in range(len(tokens)):
            finalTokens = finalTokens + tokens[i]
        if any(isPartNumber(token) for token in finalTokens):
            partFields.append(column)
        else:
            stackFields.append(column)
    if len(partFields) > 0: dataFrame = pd.melt(dataFrame, id_vars=stackFields, var_name='header_category', value_name='part_number')

    nonAttributeFields = []
    for column in dataFrame.columns:
        if 'position' in column.lower() or 'cavity' in column.lower() or 'product_category' in column.lower() or 'part_number' in column.lower() or 'header_category' in column.lower():
            nonAttributeFields.append(column)
    dataFrame = pd.melt(dataFrame, id_vars=nonAttributeFields, var_name='attribute_name', value_name='attribute_value')
    return dataFrame[dataFrame[dataFrame.columns[1]].notnull()]
#-------------------------------------------------------------------------------------------------------------------------------------------------#
directory = os.getcwd() + '/OUTPUT/'
files = [directory+name for name in os.listdir(directory)]
dataFrames = []
for file in files:
    dataFrame = pd.read_csv(file, '\t')
    if dataFrame['product_category'][0] == 'HDSCS Connectors':
        dataFrames.append(dataFrame)
#-------------------------------------------------------------------------------------------------------------------------------------------------#
dataFrameIndex = 0
reshapedDataFrames = []
mergeDataFrames = []
for dataFrame in dataFrames:
    partFields = []
    stackFields = []
    dataFrameIndex += 1
    dataFrame = reshapeDataFrame(dataFrame)
    reshapedDataFrames.append(dataFrame)
    if dataFrameIndex > 2: continue
    else: mergeDataFrames.append(dataFrame)
    # if any(['position' in column.lower() or 'cavity' in column.lower() for column in list(dataFrame.columns)]): newDataFrames.append(dataFrame)

dimensionData = mergeDataFrames[0]
orderData = mergeDataFrames[1]

dimensionData['Cavity'] = dimensionData['Cavity'].apply(pd.to_numeric, errors='ignore')
orderData['Position'] = orderData['Position'].apply(pd.to_numeric, errors='ignore')

# dimensionData.to_csv('AMPSEAL_Dimension_Data.txt', '\t')
# orderData.to_csv('AMPSEAL_Order_Data.txt', '\t')

mergedData = pd.merge(orderData, dimensionData, left_on=  orderData['Position'], right_on= dimensionData['Cavity'], how = 'inner').reset_index()
mergedData.to_csv('AMPSEAL_Merged_Data.txt', '\t')

import nltk
import nltk.corpus
import nltk.tokenize.punkt
import nltk.stem.snowball
import string

stopwords = nltk.corpus.stopwords.words('english')
stopwords.extend(string.punctuation)
stopwords.append('')

stemmer = nltk.stem.snowball.SnowballStemmer('english')

def get_match_ratio(s1, s2):
    tokens_s1 = [token for token in nltk.word_tokenize(s1.lower())]
    tokens_s2 = [token for token in nltk.word_tokenize(s2.lower())]
    stems_s1 = [stemmer.stem(token) for token in tokens_s1 if len(token) > 2]
    stems_s2 = [stemmer.stem(token) for token in tokens_s2 if len(token) > 2]

    ratio = len(set(stems_s1).intersection(stems_s2)) / float(len(set(stems_s1).union(stems_s2)))
    return ratio

rowsToDelete = []
for row in range(len(mergedData.values)):
    match_ratio = get_match_ratio(mergedData['header_category'][row], mergedData['attribute_name_y'][row])
    if match_ratio == 0: rowsToDelete.append(row)

finalData = mergedData.drop(mergedData.index[rowsToDelete])
finalData.to_csv('AMPSEAL_Final_Data.txt', '\t')
