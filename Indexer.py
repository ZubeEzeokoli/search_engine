import os
import json
import time
from collections import defaultdict
import math

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from bs4 import BeautifulSoup

# (index structure)
#     "token1": {
#         "doc_list" :
#             "0/99": {    // doc_id
#                 "tf": 3, // term freq - raw count
#                 "tf_idf": 0.045, // tf_idf score calculated at the end
#                 "weight_sum": 5.0, // sum of all weights for this token in this doc
#                 "weight_average": 1.67 // weighted average of all weights for this token in this doc - use for ranking
#             },
#             "1/143": {
#                 ...
#             }
#         }
#     }

# run in python3 environment to download the stopwords from nltk library
# import nltk
# nltk.download('stopwords')
# troubleshooting for downloading: https://stackoverflow.com/questions/38916452/nltk-download-ssl-certificate-verify-failed
# you'll know you have the stopwords installed when interpretor doesn't crash :)

# weights for title, bold, and headings - change values if needed
weights = {
    'title': 2.0,
    'b': 1.5,
    'h1': 1.2,
    'h2': 1.2,
    'h3': 1.2
}

# this file is meant to be run once to build an inverted index of the corpus
# once the inverted index is built, it can then be used to answer search queries
class Indexer:
    def __init__(self, bookkeeping_file, data_folder):
        self.bookkeeping_file = bookkeeping_file # stores bookeeping file
        self.data_folder = data_folder           # stores folder of document data
        self.inverted_index = defaultdict(lambda: { "doc_list" : defaultdict(dict) }) # create dictionary to represent inverted index - originally used for ONE grams - 2gram index is currently being used
        self.inverted_index_2gram = defaultdict(lambda: { "doc_list" : defaultdict(dict) })

        self.doc_word_counts = defaultdict(int) # stores the total number of words for each document
        self.total_docs = 0                     # stores the total number of documents

    def get_tokens(self, content):
        """
        Processes a document by tokenizing and weighting terms found inside the document.
        @param content: webpage document to be processed
        @return res: list of (token, weight) pairs found in the document
        """

        stop_words = set(stopwords.words('english'))   # stop word set from nltk
        lem = WordNetLemmatizer()                      # lemmatizer from nltk
        parsed = BeautifulSoup(content, 'html.parser') # parse using BeautifulSoup
        res = []

        # extract content that is a title, bolded, or a heading
        for tag_type, weight in weights.items():
            text = ' '.join([item.get_text() for item in parsed.find_all(tag_type)]) # extract ALL content with a heavier weighted tag
            if text:
                # tokenize the text. then for every tokenized word check if it is alphanumeric and not a stop word. then put it through the
                # lemmatizer and append the token and corresponding weight to res
                tokens = [lem.lemmatize(word.lower()) for word in word_tokenize(text) if word.lower() not in stop_words and word.isalpha()]
                tokens = self.refine_tokens(tokens)
                res.extend([(word, weight) for word in tokens])

        # remove content from parsed BeautifulSoup tree with title, bolded, or a heading tags since this was already processed above
        # so that these are not double processed
        for match in parsed.find_all([tag for tag in weights.keys()]): # find everything that matches the tags
            match.decompose() # remove tag from the BeautifulSoup tree and destroy it

        text = parsed.get_text() # extract text content after removing unwanted tags

        # tokenize the text. then for every tokenized word check if it is alphanumeric and not a stop word. then put it through the
        # lemmatizer. all of these words have a weight of 1.0 since they were not a title, bolded, or a heading
        tokens = [lem.lemmatize(word.lower()) for word in word_tokenize(text) if word.lower() not in stop_words and word.isalpha()]
        tokens = self.refine_tokens(tokens)
        res.extend([(word, 1.0) for word in tokens]) # add to list

        return res

    def build_index(self):
        """
        Iterates over every document in the WEBPAGES_RAW folder directories.
        For every word in the document, add the document if it does not already exist in the index. Update the
        word's postings list and corresponding metadata fields.
        """

        # open bookkeeping file
        with open(self.bookkeeping_file, 'r', encoding='utf-8') as file:
            data = json.load(file)      # load bookkeeping data as a dict
            self.total_docs = len(data) # number of docs = number of lines in bookkeeping

            # iterate over all the webpages; process each webpage and update the inverted index
            # “folder_number/file_number” is a unique identifier for each document - use in posting list to represent the doc
            for doc_id, _ in data.items():
                folder, file = map(int, doc_id.split('/'))                         # split “folder_number/file_number”
                file_path = os.path.join(self.data_folder, str(folder), str(file)) # join into full path

                # read HTML content
                with open(file_path, "r", encoding='utf-8') as webpage:
                    content = webpage.read() # open the document
                    tokens = self.get_tokens(content) # get all tokens and weights from the document

                word_freq = defaultdict(int) # stores the freq of each word in the current document
                total_words = 0              # total words in current document
        
                for word, _ in tokens: # update word freq and word count
                    word_freq[word] += 1
                    total_words += 1

                self.doc_word_counts[doc_id] = total_words # store word count for this document - not currently used; could possibly be used for ranking

                # get a list of anchor_words by finding the href and getting the words in between
                anchor_words = []
                anchor_words_missed = 0
                for line in content.split():
                    if "href" in line:
                        try:
                            first = line.index("=") + 2
                            if ">" in line:
                                second = line.index(">")-1
                            elif "\"" in line[first:]:
                                second = -2
                            else:
                                second = len(line)
                            anchor_words.append(line[first: second])
                        except:
                            anchor_words_missed += 1

                # adding to index for ONE grams
                # for word, weight in tokens: # iterate over each token and add to index
                #     entry = self.inverted_index[word]["doc_list"][doc_id]  # get document entry for this word or automatically create one if it doesnt exist
                #     entry["tf"] = word_freq[word]                           # update the raw count of this token

                #     # metadata about the weight of the token (i.e. it was a title, in bold, or a heading)
                #     entry["weighted_sum"] = entry.get("weighted_sum", 0) + weight
                #     entry["weighted_average"] = round(entry["weighted_sum"] / entry["tf"], 4)

                # adding to index for TWO grams
                for i in range(len(tokens) - 1): # iterate over each 2-gram and add to the 2-gram index
                    entry = self.inverted_index_2gram[tokens[i][0] + " " + tokens[i+1][0]]["doc_list"][doc_id]  # get document entry for this word or automatically create one if it doesnt exist
                    entry["tf"] = word_freq[tokens[i][0]] + word_freq[tokens[i+1][0]]                         # update the raw count of this token

                    # metadata about the weight of the token (i.e. it was a title, in bold, or a heading)
                    entry["weighted_sum"] = entry.get("weighted_sum", 0) + tokens[i][1] + tokens[i+1][1]
                    entry["weighted_average"] = round(entry["weighted_sum"] / entry["tf"], 4)
                
                self.inverted_index_2gram["anchor_words"][doc_id] = anchor_words # add anchor words to the inverted_index by doc id

        self.calc_tf_idf_scores() # calculate all tf_idf scores
        self.inverted_index_2gram = dict(sorted(self.inverted_index_2gram.items())) # sort the 2-gram index alphabetically

    def calc_tf_idf_scores(self):
        """
        Calculates the term frequency-inverse document frequency value for every single document under every word in the index.
        Term frequency is how often a word occurs in a document. We use the raw count.
        Inverse document frequency is a measure the importance of a word across the entire corpus.
        """
        
        # update tf_idf score - for one grams
        # for _, data in self.inverted_index.items():
        #     doc_freq = len(data['doc_list'])          # number of documents that contain the current word
        #     try:
        #         idf = math.log(self.total_docs / doc_freq) # number of total corpus docs / number of documents that contain the word
        #     except ZeroDivisionError:
        #         pass #This mean docs length is zero

        #     # calculate tf_idf for each document for the current word
        #     for _, doc_data in data['doc_list'].items():
        #         doc_data['tf_idf'] = round(doc_data['tf'] * idf, 4) # round to 4 decimal places
        
        #update tf_idf score - for 2 grams
        for _, data in self.inverted_index_2gram.items():
            doc_freq = len(data['doc_list'])               # number of documents that contain the current word
            try:
                idf = math.log(self.total_docs / doc_freq) # number of total corpus docs / number of documents that contain the word
            except ZeroDivisionError:
                pass # tried to divide by zero

            # calculate tf_idf for each document for the current word
            for _, doc_data in data['doc_list'].items():
                doc_data['tf_idf'] = round(doc_data['tf'] * idf, 4) # round to 4 decimal places

    def refine_tokens(self, words):
        """
        Further refines the tokens after being parsed by the lemmatizer to ensure only valid tokens are stored in the index.
        Note: Reused our code from Project2 Web Crawler.
        @param words: list of tokens to be processed
        @return res: list of processed tokens
        """
        res = [] # stores tokens
        cur = "" # current token

        # clean every word 
        for word in words:
            cur = ""
            try:  # try to process the word
                for c in word:
                    val = ord(c.lower())
                    if 97 <= val <= 122:  # ensure the ASCII value is part of the English alphabet
                        cur += c.lower() 
                    else:  # do not add the current character; if curr is a non-empty string, add it to the token list
                        if cur:
                            res.append(cur)
                            cur = ""
            except Exception:  # some error occurred, append the current string and reset
                if cur:
                    res.append(cur)
            res.append(cur)
        # edge case
        if cur:
            res.append(cur)

        return res

    def write_index(self, output_file, output_file2):
        """
        Writes self.inverted_index to a file and stores it as json for reusability.
        @param output_file: name of the file to store the index in
        """

        with open(output_file2, "w") as file: # open file
            json.dump(self.inverted_index_2gram, file, indent=4) # save inverted_index as json

        print(f'Number of documents indexed: {self.total_docs}')
            
if __name__ == '__main__':

    start_time = time.time()
    
    bookkeeping_file = "/Users/z/Desktop/WEBPAGES_RAW/bookkeeping.json" # replace with location of bookkeeping.json
    data_folder = "/Users/z/Desktop/WEBPAGES_RAW"                       # replace with location of WEBPAGES_RAW

    indexer = Indexer(bookkeeping_file, data_folder) # create Indexer object
    indexer.build_index()                            # build the index
    indexer.write_index("inverted_index.json", "inverted_index_2gram.json")       # save the index

    end_time = time.time()
    print(f'Time taken: {(end_time - start_time) / 60} mins')
