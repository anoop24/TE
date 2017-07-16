import pandas
from operator import itemgetter
import nltk
from nltk.corpus import words
import string

def remove_non_ascii(text):
    return ''.join([i if ord(i) < 128 else '' for i in text])

ict_raw = [remove_non_ascii(line) for line in open('ict_raw.txt')]
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

universal_attributes_df = pandas.read_excel('attribute_list_final.xlsx', sheetname="Ending with Colon")
universal_attributes = list(set([remove_non_ascii(attribute) for attribute in universal_attributes_df['Attribute']]))
attribute_position = []


for page in pages:
    for line in page:
        for attribute in universal_attributes:
            if line.lower().startswith(attribute.lower()) and len(attribute) < 40:
                attribute_position.append([pages.index(page), attribute, page.index(line)])

###########################################################################################################################

data = []
for i in range(len(attribute_position)):
    attribute_page = attribute_position[i][0]
    product_category = pages[attribute_page][0].strip('\n') # Attribute Product Category
    if product_category == 'Glossary': continue
    if i < len(attribute_position) - 1:
        next_attribute_page = attribute_position[i+1][0]
        next_attribute_location = attribute_position[i+1][2]
    else:
        next_attribute_page = attribute_page
        next_attribute_location = attribute_location

    attribute_name = attribute_position[i][1].strip('\n').strip(':').title()   # Attribute Name
    attribute_location = attribute_position[i][2]
    attribute_value = ''
    if next_attribute_page > attribute_page:
        attribute_value = pages[attribute_page][attribute_location].replace('\n', '')
    else:
        for j in range(attribute_location, next_attribute_location):
            attribute_value += pages[attribute_page][j].replace('\n', '')
    if attribute_value != '':
        attribute_value = attribute_value[attribute_value.index(':')+2:]
    data.append([product_category, attribute_name, attribute_value])

cols = ['product_category', 'attribute_name', 'attribute_value']
attribute_data = pandas.DataFrame(data=data, columns=cols)

###########################################################################################################################

data = []
english_words = [x.encode('UTF8').lower() for x in words.words()]
for page in pages:
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
print part_data

###########################################################################################################################

attribute_data.to_csv('attribute_data.txt', sep='\t', encoding='utf-8')
part_data.to_csv('part_data.txt', sep='\t', encoding='utf-8')

###########################################################################################################################
