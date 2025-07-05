import nltk
from nltk.corpus import stopwords

nltk.download('punkt_tab')
nltk.download('stopwords')

from nltk.tokenize import word_tokenize
text = "This is a sample movie review."
tokens = word_tokenize(text)
print(tokens)
stop_words = set(stopwords.words('english'))
print(stop_words)


