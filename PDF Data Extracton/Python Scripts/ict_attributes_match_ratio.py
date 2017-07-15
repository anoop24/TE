from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter#process_pdf
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
import nltk
from nltk.corpus import words
import string
import re
from cStringIO import StringIO
import nltk.corpus
import nltk.tokenize.punkt
import nltk.stem.snowball
import string


def pdf_to_text(pdfname):

    # PDFMiner boilerplate
    rsrcmgr = PDFResourceManager()
    sio = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, sio, codec=codec, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    # Extract text
    fp = file(pdfname, 'rb')
    pageNumber = 0
    for page in PDFPage.get_pages(fp):
        interpreter.process_page(page)
    fp.close()

    # Get text from StringIO
    text = sio.getvalue()

    # Cleanup
    device.close()
    sio.close()

    return text

def remove_non_ascii(text):
    return ''.join([i if ord(i) < 128 else '' for i in text])

## converting pdf catalog to txt format
pdfname = 'C:/Users/Aanoop.Sharma/Desktop/OCR/ICT - Full Catalog.pdf'
raw = pdf_to_text(pdfname)
with open('raw.txt', 'w') as output:
     output.write(raw)

lines = [line.rstrip('\n').lower() for line in open('raw.txt')]
potential_atttributes = []
for line in lines:
    if line == '' or any(char.isdigit() for char in line) or len(re.findall(r'\w+', line)) > 5 or len(line) < 4:
        continue    ## removing the line if it is blank || contains a number value || has more than 5 tokens || less than 4 characters
    else:
        potential_atttributes.append(remove_non_ascii(line))    ## keeping the rest of the phrases as potential attributes

actual_attributes = [remove_non_ascii(line.rstrip('\n').lower()) for line in open('ict_attirbutes_list.txt')]   ## actual list of ict attributes
potential_atttributes = list(set(potential_atttributes))    ## derived list of potential ict attributes from the catalog


# Get default English stopwords and extend with punctuation
stopwords = nltk.corpus.stopwords.words('english')
stopwords.extend(string.punctuation)
stopwords.append('')

# Create tokenizer and stemmer
# tokenizer = nltk.tokenize.punkt.PunktWordTokenizer()
stemmer = nltk.stem.snowball.SnowballStemmer('english')

## function to get fuzzy matching ratio between two phrases
def get_match_ratio(s1, s2):
    tokens_s1 = [token for token in nltk.word_tokenize(s1.lower())]
    tokens_s2 = [token for token in nltk.word_tokenize(s2.lower())]
    stems_s1 = [stemmer.stem(token) for token in tokens_s1]
    stems_s2 = [stemmer.stem(token) for token in tokens_s2]

    ratio = len(set(stems_s1).intersection(stems_s2)) / float(len(set(stems_s1).union(stems_s2)))
    return ratio

with open('match_list.txt', 'a') as output:
    output.write('actual_attribute' + '\t' + 'potential_atttribute' + '\t' + 'match_ratio' + '\n')

## getting the match_ratio for each of the combinations of actual vs potential attribute
for actual_attribute in actual_attributes:
    for potential_atttribute in potential_atttributes:
        print actual_attribute
        print potential_atttribute
        print '\n\n'
        match_ratio = get_match_ratio(actual_attribute, potential_atttribute)
        with open('match_list.txt', 'a') as output:
            output.write(actual_attribute + '\t' + potential_atttribute + '\t' + str(match_ratio) + '\n')
