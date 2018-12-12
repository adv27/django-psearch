# -*- coding: utf-8 -*-
import math
import os
import pickle
import re
import string

import jieba
import numpy
import pandas as pd
from gensim import parsing


def tokenizeWholeCorpora(pathToCorpora):
    doc_count=0
    train_set = []
    doc_mapping={}
    walk = os.walk(pathToCorpora)
    for root, dirs, files in walk:
        for name in files:        
            f = open(os.path.join(root, name), 'r')
            raw = f.read()
            f.close()
            # call preprocessing function
            preprocessed_text = preprocessing(raw)
            # Skip document length < min_length
            if len(preprocessed_text) < min_length or name=='.DS_Store':
                continue
            tokens = tokenize(preprocessed_text,stopwords,full_mode,HMM_mode_on)
            train_set.append(list(tokens))
            
            # Build doc-mapping
            doc_mapping[doc_count] = name
            doc_count = doc_count+1

    return doc_count,train_set,doc_mapping

def getOrderedDict(dic):
    from operator import itemgetter
    from collections import OrderedDict
    sorteddict = OrderedDict(sorted(dic.items(), key=itemgetter(1),reverse=True))
    return sorteddict
    
    
def convertListToDict(anylist):
    convertedDict = {}
    for pair in anylist:
        topic = pair[0]
        weight = pair[1]
        convertedDict[topic] = weight
    return convertedDict

def dotprod(a, b):
    """ Compute dot product
    Args:
        a (dictionary): first dictionary of record to value
        b (dictionary): second dictionary of record to value
    Returns:
        dotProd: result of the dot product with the two input dictionarieyes
    """
    dotProd = 0
    for token in a:
        if b.has_key(token):
            dotProd = dotProd + a[token]*b[token]
            #dotProd = dotProd + math.pow(a[token]*b[token],2)
            
    return dotProd

def norm(a):
    """ Compute square root of the dot product
    Args:
        a (dictionary): a dictionary of record to value
    Returns:
        norm: a dictionary of tokens to its TF values
    """
    sumTotal = 0
    for key in a:
        sumTotal = sumTotal + a[key] ** 2
    return math.sqrt(sumTotal)

def cossim(a, b):
    """ Compute cosine similarity
    Args:
        a (dictionary): first dictionary of record to value
        b (dictionary): second dictionary of record to value
    Returns:
        cossim: dot product of two dictionaries divided by the norm of the first dictionary and
                then by the norm of the second dictionary
    """
    dotProd = dotprod(a,b)
    sumOfA = norm(a)
    sumOfB = norm(b)
    
    return dotProd / (sumOfA * sumOfB)
    #return dotProd


def get_stop_words_list(path_dict_for_stopwords):
    walk = os.walk(path_dict_for_stopwords)
    list_of_stop_words = set()
    for root,dirs,files in walk:
        for name in files:
            if 'complete' in name:
                csv_path = os.path.join(root,name)
                file = open(csv_path,'r')
                x = file.readlines()
                ox = set()
                for i in x:
                    i = i.replace('\n','')
                    ox.add(i)
                list_of_stop_words = list_of_stop_words.union(ox)
            if ('csv' in name) and not ('complete' in name):
                csv_path = os.path.join(root,name)
                df = pd.read_csv(csv_path)
                current_set_of_stopwords = set(df.word)
                list_of_stop_words = list_of_stop_words.union(current_set_of_stopwords)
    
    decoded_tokens = set()
    for token in list_of_stop_words:
        decoded_tokens.add(token.decode('utf8'))
    return decoded_tokens

def preprocessing(content):
    remove_punc = ('。 ； 。 、 」 「 ， （ ） —').split(' ')
    ## preprocessing #1 : remove XXenglishXX and numbers
    preprocessing_1 = re.compile(r'\d*',re.L)  ## only substitute numbers
    #preprocessing_1 = re.compile(r'\w*',re.L)  ## substitute number & English
    content = preprocessing_1.sub("",content)
    ## preprocessing #2 : remove punctuation
    preprocessing_2 = re.compile('[%s]' % re.escape(string.punctuation))
    content = preprocessing_2.sub("",content)
    ## preprocessing #3 : remove Chinese punctuation and multiple whitspaces
    content = content.replace('\n','')
    for punc in remove_punc:
        content = content.replace(punc,'')
    try:
        content = parsing.strip_multiple_whitespaces(content)
    except:
        print('Warning : failed to strip whitespaces @ ')   
    
    return content


def tokenize(content,stopwords,full_mode,HMM_mode_on):
    word_list = set(jieba.cut(content, cut_all = full_mode,HMM=HMM_mode_on))
    removed_words_only_1_character = set([words for words in word_list if len(words)>=2])
    #removed_words_only_1_character = word_list
    #remove stop words
    removed_words_only_1_character.difference_update(stopwords)
    return removed_words_only_1_character
    
def savePickleFile(fileName,objectName):
    fileName= './LDAmodel/'+fileName+'.pickle'
    mappingFile = open(fileName,'w')
    pickle.dump(objectName,mappingFile)
    mappingFile.close()
    print('saved at {0}'.format(fileName))
    
def loadPickleFile(fileName):
    fileName = './LDAmodel/'+fileName+'.pickle'
    mappingFile = open(fileName,'rb')
    objectName = pickle.load(mappingFile)
    mappingFile.close() 
    return objectName

def fill_list_from_dict(a,topics):
    result = [0] * topics
    for k,v in a.items():
        result[k-1] = v
    return result

def KLDivergenceSim(a,b,topics):
    from scipy.stats import entropy
    import math
    a = fill_list_from_dict(a,topics)
    b = fill_list_from_dict(b,topics)
    entropyOf_A_to_B = entropy(a,b)
    entropyOf_B_to_A = entropy(b,a)
    minusSummedEntropy = -(entropyOf_A_to_B+entropyOf_B_to_A)
    return math.exp(minusSummedEntropy)
    
def pearson_correlation(a,b,topics):
    from scipy.stats import pearsonr
    a = fill_list_from_dict(a,topics)
    b = fill_list_from_dict(b,topics)
    return pearsonr(a,b)[0]  
