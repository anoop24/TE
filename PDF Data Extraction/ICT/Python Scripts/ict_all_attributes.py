'''
INPUT DATA
1. ICT - Full Catalog Raw file in TXT format

OUTPUT DATA
1. ICT Parts Data
2. ICT Attributes Data
3. ICT Parts-Attributes Mapping
'''


import pandas
import nltk
from nltk.corpus import words
import string
import sys
import time
import os

script_directory = os.getcwd()
input_directory = script_directory[:script_directory.rindex('\\')] + '\\Input Data'
output_directory = script_directory[:script_directory.rindex('\\')] + '\\Output Data'

def remove_non_ascii(text):
    return ''.join([i if ord(i) < 128 else '' for i in text])


def isNonColonAttribute(line):
    if not line.strip('\n').istitle() or any([char.isdigit() for char in line]) or len(line) > 40 or len(list(set(line.strip('\n')))) < 3:
        return False
    else:
        return True

def isColonAttribute(line):
    if ':' in line:
        return True
    else:
        return False

def extract_headers(page):
    headers = []
    for line in page:
        if any([char.islower() for char in line]):
            continue
        elif 'SPECIFICATIONS' in line:
            headers.append([line, page.index(line)])
    return headers

###########################################################################################################################

ict_raw = [remove_non_ascii(line) for line in open(input_directory + '\\ict_raw.txt')]
pages = []
page_headers = []
lines = []
page = 0
for line in ict_raw:
    lines.append(line)
    if '///' in line or 'PAGE ' in line:
        pages.append(lines)
        if len(lines) > 0: page_headers.append(lines[0])
        lines = []
        page += 1

page_headers = []
for page in pages:
    page_headers.append([pages.index(page), extract_headers(page)])

page_attributes = []
print 'Extracting Page Attributes...'
for page in pages:
    page_number = pages.index(page)
    page_header_list = page_headers[page_number]
    product_category = page[0].strip('\n')
    if product_category in ['Additional Resources', 'Glossary', 'Index']: continue
    attributes = []
    print '\r',
    print '\tCurrent Page Number : ' + str(page_number),
    if len(page_header_list[1]) > 0:
        for header in page_header_list[1]:
            header_value = header[0]
            header_location = header[1]
            if page_header_list[1].index(header) == len(page_header_list[1]) - 1:
                next_header_location = len(page)
            else:
                next_header_location = page_header_list[1][page_header_list[1].index(header) + 1][1]

            attribute = ''
            for i in range(header_location, next_header_location):
                line = page[i]
                if i == next_header_location - 1:
                    next_line = page[i]
                else:
                    next_line = page[i+1]

                if isColonAttribute(line):
                    attribute += line
                    if isColonAttribute(next_line) and (not 'note:' in attribute.lower()):
                        attributes.append(attribute.replace('\n', '').replace(': ',':'))
                        attribute = ''
                    else:
                        attribute = attribute

                elif isNonColonAttribute(line):
                    attribute += line + ':'

                elif (not isNonColonAttribute(line)) and (not isColonAttribute(line)) and attribute != '':
                    attribute += line
                    if (isColonAttribute(next_line) or isNonColonAttribute(next_line))  and (not 'note:' in attribute.lower()):
                        attributes.append(attribute.replace('\n', '').replace(': ',':'))
                        attribute = ''
                    else:
                        attribute = attribute
        if len(attributes) > 0:
            page_attributes.append([page_number, product_category, attributes])

data = []
for page_attribute in page_attributes:
    product_category = page_attribute[1]
    attributes = page_attribute[2]
    for attribute in attributes:
        attribute_name = attribute[:attribute.index(':')].strip(' ')
        attribute_value = attribute[attribute.index(':') + 1:].strip(' ')
        data.append([product_category, attribute_name, attribute_value])

cols = ['product_category', 'attribute_name', 'attribute_value']
attribute_data = pandas.DataFrame(data=data, columns=cols, index=None)

###########################################################################################################################

data = []
print '\nExtracting Parts from Page...'
english_words = [x.encode('UTF8').lower() for x in words.words()]
for page in pages:
    page_number = pages.index(page)
    print '\r',
    print '\tCurrent Page Number : ' + str(page_number),
    product_category = page[0].strip('\n')
    if product_category in ['Additional Resources', 'Glossary', 'Index']: continue
    raw_page = ''.join(page)
    tokens = [token.encode('UTF8') for token in nltk.word_tokenize(raw_page.decode('UTF8').lower())]
    unique_tokens = list(set(tokens))
    non_english_tokens = [token for token in unique_tokens if token not in english_words]
    raw = non_english_tokens
    tokens = [token.replace('\n','') for token in raw]
    tokens = [token for token in tokens if any(char.isdigit() for char in token) and '!' not in token and '@' not in token and '#' not in token and '$' not in token and '%' not in token and '^' not in token and '&' not in token and '*' not in token and '(' not in token and ')' not in token and '_' not in token and '+' not in token and '=' not in token and '{' not in token and '}' not in token and '\\' not in token and '|' not in token and ':' not in token and ';' not in token and '"' not in token and ',' not in token and '.' not in token and '<' not in token and '>' not in token and '?' not in token and '/' not in token]
    tokens = [filter(lambda x: x in set(string.printable), token.upper()) for token in tokens if len(token) > 5 ]
    tokens = list(set(tokens))
    for token in tokens:
      data.append([product_category, token.strip('\n')])

cols = ['product_category', 'part_number']
part_data = pandas.DataFrame(data=data, columns=cols)

###########################################################################################################################

attribute_data.to_csv(output_directory + '\\attribute_data.txt', sep='\t', encoding='utf-8')
part_data.to_csv(output_directory + '\\part_data.txt', sep='\t', encoding='utf-8')

###########################################################################################################################
