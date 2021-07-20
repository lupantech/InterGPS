from geosolver.utils.prep import sentence_to_words_statements_values

__author__ = 'minjoon'

def test_prep():
    paragraph = r"If \sqrt{x+5}=40.5, what is x+5?"
    print(sentence_to_words_statements_values(paragraph))



if __name__ == "__main__":
    test_prep()
