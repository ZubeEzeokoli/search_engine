import json
from collections import defaultdict
from collections import namedtuple
import time
import Indexer
# BOOKKEEPING_FILE = "/Users/z/Desktop/WEBPAGES_RAW/bookkeeping.json"
# BOOKKEEPING_FILE = "/Users/pablorodriguez/Desktop/CS121/cs121-Project3/WEBPAGES_RAW/bookkeeping.json"
BOOKKEEPING_FILE = "/Users/joshuabergeron/Desktop/WEBPAGES_RAW/bookkeeping.json"

Link = namedtuple('Link',['link', 'rank_id'])
class Retriever:
    def __init__(self, index_file):

        with open(index_file, 'r') as file:
            self.inverted_index = json.load(file)
        
        with open(BOOKKEEPING_FILE, 'r') as file:
            self.bookkeeping_file = json.load(file)
    
    def search_query(self, query_list):
        query_dict = defaultdict(set) # a set of all doc_ids to intersect in the future

        res = []
        for query in query_list:
            for token in self.inverted_index.keys(): # you want the token string so you can check if query shows up anywhere in the token string
                if query in token:
                    # get all the doc ids and save it in a set for the defaultdict specifieds key
                    for doc_id, doc_details in self.inverted_index[token]["doc_list"].items():
                        tf_idf_score = int(doc_details['tf_idf'])
                        weighted_average = int(doc_details['weighted_average'])
                        query_dict[query].add(Link(doc_id, int(weighted_average) + int(tf_idf_score)))

        starting_set = list(query_dict.values())[0]

        for val in query_dict.values():
            res = list(x for x in starting_set.intersection(val)) # intersect all the doc_ids so if there is a query of multiple words it returns the doc_ids containing all the words

        t = time.time()

        res = list(set(res)) # get rid of duplicates

        res.sort(key = lambda x: x.rank_id, reverse = True) # sort result by rank_id value
        
        # get rid of duplicates
        temp = set()
        i = 0
        while i < len(res):
            if res[i].link not in temp:
                temp.add(res[i].link)
                i += 1
            else:
                res.pop(i)
        
        s = time.time()
        print(f'the time it took to run is : {s- t}')
        return res

    def print_urls(self, url_list):
        # print(f'Numer of unique words: {len(self.inverted_index.keys())}')
        print(f"Number of results found: {len(url_list)}")
        count = 0

        # print first 10 results
        for url in url_list:
            if count == 20: break
            count += 1
            print(f'{self.bookkeeping_file.get(url.link, "URL not found")}\n')

if __name__ == '__main__':

    # create Retriever object
    # retriever = Retriever("/Users/z/Library/Mobile Documents/com~apple~CloudDocs/compsci_121/cs121-Project3/inverted_index.json")
    retriever = Retriever("/Users/z/Library/Mobile Documents/com~apple~CloudDocs/compsci_121/cs121-Project3/inverted_index_2gram.json")
    # retriever = Retriever("/Users/pablorodriguez/Desktop/CS121/cs121-Project3/inverted_index.json")
    # retriever = Retriever("/Users/joshuabergeron/Documents/cs121-Project3/inverted_index_2gram.json")

    # request user to enter a query
    # call search_query to process query and search in the index
    # output result
    while True:
        q = input("Query: ").lower().split()
        if  q == [] or q[0].lower() == "quit":
            break
        res = retriever.search_query(q)
        retriever.print_urls(res)