import pandas as pd
import numpy as np
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import make_pipeline

class Classifier:

    def __init__(self, bank = 'rbc'):
        self.bank = bank
        self.loaded_data = False # load_data must be called before trying to predict category
        self.classifier = MultinomialNB()
        self.vectorizer = CountVectorizer()
        self.pipeline = make_pipeline(self.vectorizer, self.classifier)

    def load_data(self, df):
        '''Clean data and load in pipeline'''
        X = df['description']
        y = df['category']

        X = X.apply(self._strip_nonalpha)

        if self.bank == 'rbc':
            X = X.apply(self._rbc_remove_city_province)

        self.pipeline.fit(X, y)
        self.loaded_data = True

    def predict(self, X):
        '''Takes text description input and returns predicted category'''
        if self.loaded_data:
            return self.pipeline.predict(X)
        else:
            return "Data Not Loaded"
    
    def _strip_nonalpha(self, s):
        '''Strip numbers and symbols from the given string'''
        new_s = s.translate({ord(k): None for k in "0123456789'!@#$%^&*'()-_+[]|"})
        new_s = new_s.replace('/', ' ')
        return new_s

    def _rbc_remove_city_province(self, s):
        '''Remove  city and province from description'''
        PROVINCES = ['ON', 'QC', 'NS', 'NB', 'MB', 'BC', 'PE', 'SK', 'AB', 'NL', 'NT', 'YT', 'NU']

        words = s.split()

        # Remove last two words from description if the description ends with a province
        if words[len(words)-1] in PROVINCES:
            new_s = ' '.join(words[:len(words)-2])
            return new_s
        else:
            return s