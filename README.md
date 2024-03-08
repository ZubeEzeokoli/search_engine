# cs121-Project3

Search Engine

In order to run the code you must install the below libraries:

`python3 -m pip install nltk`<br />
`python3 -m pip install beautifulsoup4`<br />

you need to install nltk stopwords
run in python3 environment to download the stopwords from nltk library
import nltk
nltk.download('stopwords')
troubleshooting for downloading: https://stackoverflow.com/questions/38916452/nltk-download-ssl-certificate-verify-failed
you'll know you have the stopwords installed when interpretor doesn't crash :)

run this in a terminal and run it using python3 [name_of_file]:
    import nltk
    import ssl

    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context

    nltk.download('stopwords')
    nltk.download('punkt')
    nltk.download('wordnet')

Indexer.py is meant to be run once to build an inverted_index of the corpus. The index is stored as a JSON file. This process should take around 6-10 mins.<br />
`python3 Indexer.py`

Run Retriever.py to query searches.<br />
`python3 Retriever.py`
