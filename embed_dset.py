from transformers import BertModel, DistilBertModel
from transformers import pipeline
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import datasets
import numpy as np
import pickle as pkl
import os
from os.path import join as oj
from spacy.lang.en import English
import argparse
path_to_current_file = os.path.dirname(os.path.abspath(__file__))


def generate_decomposed_ngrams(sentence, all_ngrams=False):
    """seq of sequences to input (can do this better - stemming, etc.)
    
    Params
    ------
    args.ngrams: int
    all_ngrams: bool
        whether to include all n-grams up to n or just n
    """
    
    # unigrams_list = sentence.split(' ')
    if args.ngrams == 1:
        return [str(x) for x in simple_tokenizer(sentence)]
    
    seqs = []
    unigrams_list = [x for x in simple_tokenizer(sentence)]
    if all_ngrams:
        ngram_lengths = range(1, args.ngrams + 1)
#         seqs = [str(x) for x in simple_tokenizer(sentence)] # precompute length 1
    else:
        ngram_lengths = range(args.ngrams, args.ngrams + 1)
        
        
    for ngram_length in ngram_lengths:
        for idx_starting in range(0, len(unigrams_list) + 1 - ngram_length):
            idx_ending = idx_starting + ngram_length
            seq = ''.join([t.text + t.whitespace_
                                 for t in unigrams_list[idx_starting: idx_ending]]).strip()
            if len(str) > 0 and not str.isspace(): # str is not just whitespace
                seqs.append(seq)
    # print('seqs', seqs)
    return seqs

def embed_and_sum_function(example):
    """
    Params
    ------
    args.padding: True, "max_length"
    """
    sentence = example['sentence']
    # seqs = sentence

    if isinstance(sentence, str):
        seqs = generate_decomposed_ngrams(sentence)
    elif isinstance(sentence, list):
        raise Exception('batched mode not supported')
        # seqs = list(map(generate_decomposed_ngrams, sentence))
    # print('seqs', type(seqs), seqs)
    
                            
    # maybe a smarter way to deal with pooling here?
    tokens = tokenizer(seqs, padding=args.padding, truncation=True, return_tensors="pt")
    # print('tokens', tokens['input_ids'].shape, tokens['input_ids'])
    output = model(**tokens) # has two keys, 'last_hidden_state', 'pooler_output'
    embs = output['pooler_output'].cpu().detach().numpy()
    # print('embs', embs.shape)
    
    # sum over the embeddings
    embs = embs.sum(axis=0).reshape(1, -1)
    # print('embs', embs.shape)    
    
    return {'embs': embs}

if __name__ == '__main__':
    
    # hyperparams
    # models
    # "bert-base-uncased", 'textattack/bert-base-uncased-SST-2'
    # distilbert-base-uncased, , "distilbert-base-uncased-finetuned-sst-2-english"
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--checkpoint', type=str, help='name of model checkpoint', default='bert-base-uncased')
    parser.add_argument('--ngrams', type=int, help='dimensionality of ngrams', default=1)
    parser.add_argument('--subsample', type=int, help='whether to only keep only this many training samples', default=-1)
    args = parser.parse_args()
    args.padding = True # 'max_length' # True
    print('\n\nhyperparams', 'sub', args.subsample, args.checkpoint, 'ngrams', args.ngrams, 'padding', args.padding, '\n\n')
    
    
    # set up model
    nlp = English()
    simple_tokenizer = nlp.tokenizer # for our word-finding
    tokenizer = AutoTokenizer.from_pretrained(args.checkpoint) # for actually passing things to the model
    if 'distilbert' in args.checkpoint:
        model = DistilBertModel.from_pretrained(args.checkpoint)
    elif 'bert-base' in args.checkpoint:
        model = BertModel.from_pretrained(args.checkpoint)
    
    
    # set up data
    dataset = datasets.load_dataset('sst2')
    del dataset['test'] # speed things up for now
    if args.subsample > 0:
        dataset['train'] = dataset['train'].select(range(args.subsample))

    # run 
    embedded_dataset = dataset.map(embed_and_sum_function) #, batched=True)
    
    # save
    dir_name = f"ngram={args.ngrams}_" + 'sub=' + str(args.subsample) + '_' + args.checkpoint # + "_" + padding
    save_dir = oj(path_to_current_file, 'data/processed', dir_name)
    os.makedirs(save_dir, exist_ok=True)
    embedded_dataset.save_to_disk(save_dir)
    """
    for k in ['train', 'validation', 'test']:
        embs = np.array(dataset[k]['embs']).squeeze()
        pkl.dump(embs, open(oj(save_dir, 'embs_' + k + '.pkl'), 'wb'))
    """