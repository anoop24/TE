import nltk
from nltk.corpus import words
import string

raw = open('ict_1.txt').read()
english_words = [x.encode('UTF8').lower() for x in words.words()]
tokens = [token.encode('UTF8') for token in nltk.word_tokenize(raw.decode('UTF8').lower())]
unique_tokens = list(set(tokens))
non_english_tokens = [token for token in unique_tokens if token not in english_words]
raw = non_english_tokens
tokens = [token.replace('\n','') for token in raw]
tokens = [token for token in tokens if any(char.isdigit() for char in token) and '!' not in token and '@' not in token and '#' not in token and '$' not in token and '%' not in token and '^' not in token and '&' not in token and '*' not in token and '(' not in token and ')' not in token and '_' not in token and '+' not in token and '=' not in token and '{' not in token and '}' not in token and '\\' not in token and '|' not in token and ':' not in token and ';' not in token and '"' not in token and ',' not in token and '.' not in token and '<' not in token and '>' not in token and '?' not in token and '/' not in token]
tokens = [filter(lambda x: x in set(string.printable), token.upper()) for token in tokens if len(token) > 5 ]
tokens = list(set(tokens))
parts_file = open('ict_parts.txt', 'w')
for token in tokens:
  parts_file.write('%s\n' % token)
