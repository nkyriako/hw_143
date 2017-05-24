import zipfile, os
import re, nltk, operator
from collections import OrderedDict

# delete line below when combining into one file
#from baseline_stub import get_sentences, get_bow, find_phrase, baseline
locative_Prep = {'on', 'under', 'in', 'along'}
article = {'a', 'the'}
###############################################################################
## Utility Functions ##########################################################
###############################################################################

# returns a dictionary where the question numbers are the key
# and its items are another dict of difficulty, question, type, and answer
# e.g. story_dict = {'fables-01-1': {'Difficulty': x, 'Question': y, 'Type':}, 'fables-01-2': {...}, ...}
def getQA(filename):
    content = open(filename, 'rU', encoding='latin1').read()
    question_dict = {}
    for m in re.finditer(r"QuestionID:\s*(?P<id>.*)\nQuestion:\s*(?P<ques>.*)\n(Answer:\s*(?P<answ>.*)\n){0,1}Difficulty:\s*(?P<diff>.*)\nType:\s*(?P<type>.*)\n*", content):
        qid = m.group("id")
        question_dict[qid] = {}
        question_dict[qid]['Question'] = m.group("ques")
        question_dict[qid]['Answer'] = m.group("answ")
        question_dict[qid]['Difficulty'] = m.group("diff")
        question_dict[qid]['Type'] = m.group("type")
    return question_dict

def get_data_dict(fname):
    data_dict = {}
    data_types = ["story", "sch", "questions"]
    parser_types = ["par", "dep"]
    for dt in data_types:
        data_dict[dt] = read_file(fname + "." + dt)
        for tp in parser_types:
            data_dict['{}.{}'.format(dt, tp)] = read_file(fname + "." + dt + "." + tp)
    return data_dict

# Read the file from disk
# filename can be fables-01.story, fables-01.sch, fables-01-.story.dep, fables-01.story.par
def read_file(filename):
    fh = open(filename, 'r')
    text = fh.read()
    fh.close()
    return text

###############################################################################
## Question Answering Functions Baseline ######################################
###############################################################################


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
            
       #adding the sentence if theres no best fit answer gives higher recall but slightly lower f score:         
#    if(result==""):
#        result  = ' '.join(t[0].lower() for t in best_answer)
    return result
#######################################################################

if __name__ == '__main__':

    # ported over from baseline_stub, not totally relevant
    stopwords = set(nltk.corpus.stopwords.words("english"))


    # Loop over the files in fables and blogs in order.
    output_file = open("train_my_answers.txt", "w", encoding="utf-8")
    cname_size_dict = OrderedDict()
    cname_size_dict.update({"fables":2})
    cname_size_dict.update({"blogs":1})
    for cname, size in cname_size_dict.items():
        for i in range (0, size):
            # File format as fables-01, fables-11
            fname = "{0}-{1:02d}".format(cname, i+1)
            #print("File Name: " + fname)
            data_dict = get_data_dict(fname)

            questions = getQA("{}.questions".format(fname))
            for j in range(0, len(questions)):
                qname = "{0}-{1}".format(fname, j+1)
                if qname in questions:
                    print("QuestionID: " + qname)
                    question = questions[qname]['Question']
                    print(question)
                    qtypes = questions[qname]['Type']

                    # get question in the form of a set, probably want to change to a list
                    qbow = get_bow(get_sentences(question)[0], stopwords)

                    # Read the content of fname.questions.par, fname.questions.dep for hint.
                    question_par = data_dict["questions.par"]
                    question_dep = data_dict["questions.dep"]

                    answer = None
                    # qtypes can be "Story", "Sch", "Sch | Story"
                    for qt in qtypes.split("|"):
                        qt = qt.strip().lower()
                        # These are the text data where you can look for answers.
                        raw_text = data_dict[qt]
                        # Not relevant for Homework 1
                        # par_text = data_dict[qt + ".par"]
                        # dep_text = data_dict[qt + ".dep"]

                        # Access POS tagged tokenized sentences
                        sentences = get_sentences(raw_text)


                        # for third param, true= sch false=.story
                        answer = baseline(qbow, sentences, True) 
                        # Remove if baseline returns a string instead of list of tokens
                        answer = "".join(t[0] for t in answer)

                        print("Answer: " + str(answer))
                        print("")

                    # Save your results in output file.
                    output_file.write("QuestionID: {}\n".format(qname))
                    output_file.write("Answer: {}\n\n".format(answer))
    output_file.close()





