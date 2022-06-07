from transformers import AutoTokenizer
from .model import BERTBiLSTMCRF
from .utils import get_entities
import torch
import torch.nn as nn
import nltk

nltk.download('punkt')
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
import nltk.data

device = torch.device('cpu')
bert_model = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext"
Tokenizer = AutoTokenizer.from_pretrained(bert_model, add_special_tokens=False)
model = BERTBiLSTMCRF(num_tags=16).to(device)


# console input the paragraph and title
# input_text, title, title_type = map(str,
#                                     input("Enter the paragraph content, title and title type in sequence, separated "
#                                           "by spaces:").split(' '))
#title = input("Enter the article's title:")
#input_text = input("Enter the content of article:")
#title_type = input("Enter the type of title (DISEASE or SYMPTOM):")

# split txt into sentences
#sentence_lst = sent_tokenize(input_text)
# remove last element
#sentence_lst = sentence_lst[:-1]


def new_word_tokenize(sentence_lst):
    # remove punctuation and common stop words to extract the main token words of the sentence
    result = []
    for sentence in sentence_lst:
        word_lst = word_tokenize(sentence)
        # stop_words = sw.words('english')
        punct_lst = [';',':','[',']','.','|','{','}','+','-','*','/','%','!','&','$','?','#']
        word_token = [word for word in word_lst if not word in punct_lst]
        if word_token:
            result.append(word_token)
    return result


def predict_in_doc(model, sentences):
    # use the model to predict the labels of sentences
    prediction_list = []
    for sentence in sentences:
        test_converted = []
        for x in sentence:
            test_converted.append(Tokenizer.convert_tokens_to_ids(x.lower()))
        masking = torch.Tensor([1 for i in range(len(test_converted))]).long().view(1, -1).to(device)
        sent = torch.Tensor(test_converted).long().view(1, -1).to(device)
        result = model(sequence=sent, maskings=masking)
        res = get_entities(sentence, result[0])
        prediction_list += res
    return prediction_list


#sentences = new_word_tokenize(sentence_lst)
#test = predict_in_doc(model, sentences)
#rst = utils.post_process(title, title_type, test)
#print(rst)
