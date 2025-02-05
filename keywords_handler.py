import pandas as pd
import nltk
from nltk.stem import WordNetLemmatizer

# Initialize NLTK lemmatizer
nltk.download('wordnet')
lemmatizer = WordNetLemmatizer()

def load_and_process_keywords_from_csv(file_path):
    '''
    Load keywords from CSV file and group them by category.
    Extend the list of keywords by their lemmas using NLTK library: lemmatization (e.g. smoking -> smoke).
    Convert to dictionary: { category [keywords_list] }.
    '''
    try:
        df = pd.read_csv(file_path)

        # Group keywords by category and convert to dict { category [keywords_list] }
        keywords_by_category = df.groupby("category")["keyword"].apply(list).to_dict()

        keywords_extended = {}

        # Apply NLTK to each keyword
        for category, keywords in keywords_by_category.items():  # iterate over tuples of (key, value) pairs
            variations_of_keywords = set()  # store vriation of keywords of current category
            print(f"Appling NTLT to keywords...")

            for keyword in keywords:
                variations_of_keywords.add(keyword)  # add original keyword

                lemma = lemmatizer.lemmatize(keyword)

                if keyword != lemma:
                    print(f"Original keyword {keyword} vs. its lemma {lemma}")

                variations_of_keywords.add(lemma)  # add lemma of the original keyword
            keywords_extended[category] = list(variations_of_keywords)  # convert set to list

        print(f"Extended list of keywords: {keywords_extended}")	
        return keywords_extended  #  return dict { "Mental Health": ["depression", "anxiety"]}
    except Exception as e:
        print(f"Error loading and processing keywords with NLTK from CSV: {e}")
        return {}