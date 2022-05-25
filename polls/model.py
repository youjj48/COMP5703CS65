import numpy as np
import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
from torchcrf import CRF # We need this encapsulated for complicated CRF components
import torchcrf

# Run in CPU
device = torch.device('cpu')
# Run in GPU
# device = torch.device('cuda')

class BERTBiLSTMCRF(nn.Module):
    def __init__(self, num_tags=None):
        super(BERTBiLSTMCRF, self).__init__()
        bert_model = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext"
        self.base_model = AutoModel.from_pretrained(bert_model)
        # The hyper-parameters for LSTM
        self.word_embeds = 768  # output dimensions from FinBERT
        self.hidden_dim = 1024  # double-layer: 2* actual hidden_size
        self.num_tags = num_tags  # the number of unique labels
        # build the lstm
        self.lstm = nn.LSTM(self.word_embeds, self.hidden_dim // 2,
                            num_layers=1, bidirectional=True, batch_first=True)
        # map from the dimension of lstm outputs to the dimension of num_tags
        self.hidden2tag = nn.Linear(self.hidden_dim, self.num_tags)
        # build the CRF
        self.crf = torchcrf.CRF(self.num_tags, batch_first=True)

    def forward(self, sequence=None, labels=None, maskings=None):
        # Get the batch_size
        batch_size = sequence.size()[0]
        # add maskings, because various input lengths and the corresponding paddings
        outputs = self.base_model(sequence,
                                  attention_mask=maskings)  # output tuple:(LastLayerSequenceOuput,PoolerOutput)

        #The process to help LSTM get rid of padding

        lengths = []  # the list to store the real length of each input
        for i in range(batch_size):
            lengths.append(maskings[i, :].tolist().count(1))
        # pack_padded_sequence so that padded items in the sequence won't be shown to the LSTM
        X = torch.nn.utils.rnn.pack_padded_sequence(outputs[0], torch.Tensor(lengths).long(), batch_first=True)
        # reset the LSTM hidden state. Must be done before you run a new batch. Otherwise the LSTM will treat
        # a new batch as a continuation of a sequence
        hidden_state = torch.randn(2, batch_size, self.hidden_dim // 2).to(device)
        cell_state = torch.randn(2, batch_size, self.hidden_dim // 2).to(device)
        # now run through LSTM
        X = self.lstm(X, (hidden_state, cell_state))[0]  # The output of lstm is (hidden_output, cell_output)
        # undo the packing operation
        X = torch.nn.utils.rnn.pad_packed_sequence(X, batch_first=True)[0]
        X = X.contiguous()
        # print(X.shape,sequence.size()[1],X.shape[2])
        X = X.view(-1, sequence.size()[1], X.shape[2])

        # lstm_outputs = self.lstm(outputs[0])[0]


        emission_scores = self.hidden2tag(X)  # map from 1024 to 9
        # decode and get the predicted labels
        predictions = self.crf.decode(emission_scores, mask=maskings.bool())  # bool()!!!!!
        # calculate losses
        if labels is not None:
            loss = -self.crf.forward(emission_scores, labels, mask=maskings.bool(), reduction='sum')
            return (loss, predictions)
        else:
            return predictions




