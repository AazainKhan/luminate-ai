# -*- coding: utf-8 -*-
"""
Created on Fri Aug 28 11:46:03 2020


"""

import nltk 
from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize
stop_words = set(stopwords.words('english')) 
# Dummy text 
text = "Mark, Amani and Amal are my good colllegues. " \
    "Mark has a new job. " \
    "A new job is exciting." \
    "He will work with a very large firm in the financial industry. " \
    "Amani and Amal both work at a bank. " \
    "They both work in the same department.  " 
tokenized_words = nltk.word_tokenize(text) 

wordsList = [w for w in tokenized_words if not w in stop_words] 
 #  Using a Tagger. Which is part-of-speech  
    # tagger or POS-tagger.  
tagged_POS = nltk.pos_tag(wordsList) 
  
print(tagged_POS) 