#!/usr/bin/env python
'''
Created on May 14, 2014
@author: reid

Modified on May 21, 2015
'''

import sys, nltk, operator, re

locative_Prep = {'on', 'under', 'in', 'along'}
article = {'a', 'the'}
# Read the file from disk
def read_file(filename):
    fh = open(filename, 'r')
    text = fh.read()
    fh.close()
    
    return text

# The standard NLTK pipeline for POS tagging a document
def get_sentences(text):
    sentences = nltk.sent_tokenize(text)
    sentences = [nltk.word_tokenize(sent) for sent in sentences]
    sentences = [nltk.pos_tag(sent) for sent in sentences]
    
    return sentences	

def get_bow(tagged_tokens, stopwords):
    return ([t[0].lower() for t in tagged_tokens])
	
def find_phrase(tagged_tokens, qbow):
    for i in range(len(tagged_tokens) - 1, 0, -1):
        word = (tagged_tokens[i])[0]
        if word in qbow:
            return tagged_tokens[i+1:]
	
# qtokens: is a list of pos tagged question tokens with SW removed
# sentences: is a list of pos tagged story sentences
# isSch are we reading .sch or .story?
def baseline(qbow, sentences, isSch):
    # Collect all the candidate answers
    result = ''
    answers = []
    lemma = nltk.wordnet.WordNetLemmatizer()

    for sent in sentences:
        sbow = get_bow(sent, stopwords)
        overlap = 0
        
        #lemmatized overlap
        qbow_lemma = [lemma.lemmatize(word, 'v') for word in qbow[1:]]
        sbow_lemma = [lemma.lemmatize(word, 'v') for word in sbow]
        overlap += len(set(qbow_lemma) & set(sbow_lemma))
        answers.append((overlap, sent))
    answers = sorted(answers, key=operator.itemgetter(0), reverse=True)
    best_answer = (answers[0])[1] 
   
    if(qbow[0] == 'where'):
        searchResult = re.search(r'(?:.*) ((on|in|under|along) ((a|the) \w+ (of a \w+)?))', ' '.join(t[0] for t in best_answer))
        if searchResult:
            result = searchResult.group(1)
            
    if(qbow[0] == 'what'):
        pattern = "(a \w+ of \w+ )?(the fox \w+)?(?:(in))? (" + "(.*)".join(qbow[-3:-1]) + "e?d?) (.* )?.?"
        searchResult = re.findall(pattern, ' '.join(t[0] for t in best_answer)) #pattern.decode('utf-8)
        if searchResult:
            if(isSch):
                result = searchResult[0][-1]
            else:
                result = searchResult[0][0]

    if(qbow[0] == 'who'):
        if(qbow[-2] == 'about'):
            searchResult = re.findall(r'a \w+', ' '.join(t[0].lower() for t in best_answer))
            if searchResult:
                result = " ".join(searchResult)
        else:
            searchResult = re.findall(r'the \w+', ' '.join(t[0].lower() for t in best_answer))
            if searchResult:
                result = " ".join([t for t in searchResult if t != ' '.join(qbow[-3:-1])])

    if(qbow[0] == 'when'):
        pattern = "(.*)".join(qbow[-3:-1]) + "e?d? (.* )?.?"
        searchResult = re.findall(pattern, ' '.join(t[0] for t in best_answer)) #pattern decode
        if searchResult:
            result = searchResult[0][-1]
            
    if(qbow[0] == 'why'):
        pattern = "(.*)".join(qbow[-3:-1]) + " \w+ (.* )?.?"
        searchResult = re.findall(pattern, ' '.join(t[0] for t in best_answer)) #pattern.decode
        if searchResult:
            result = searchResult[0][-1]

    return result

if __name__ == '__main__':
    text_file = "fables-02.sch"
	
    stopwords = set(nltk.corpus.stopwords.words("english"))
    text = read_file(text_file)
    question = "What did the lion fear?"

    qbow = get_bow(get_sentences(question)[0], stopwords)
    sentences = get_sentences(text)
	
    answer = baseline(qbow, sentences, True)
	
    print(answer)
