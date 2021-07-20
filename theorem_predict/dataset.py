#!/usr/bin/env python
# coding: utf-8

import json
import torch
from torch.utils.data import Dataset
from random import choice

class GeometryDataset(Dataset):
    """Geometry dataset."""

    def __init__(self, split, diagram_logic_file, text_logic_file, seq_file, tokenizer):

        self.tokenizer = tokenizer
        self.split = split
        assert self.split in ['train', 'val']

        if self.split == 'train':
            self.pid_lst = range(0, 2101)
        elif self.split == 'val':
            self.pid_lst = range(2101, 2401)

        with open(diagram_logic_file) as f:
            diagram_logic_forms = json.load(f)
        with open(text_logic_file) as f:
            text_logic_forms = json.load(f)

        self.combined_logic_forms = {}
        for pid in self.pid_lst:
            self.combined_logic_forms[pid] = diagram_logic_forms[str(pid)]['diagram_logic_forms'] + \
                                             text_logic_forms[str(pid)]['text_logic_forms']

        with open(seq_file) as f:
            self.sequence = json.load(f)
        self.keys = sorted([int(i) for i in list(self.sequence.keys())])
        print(len(self.keys))
        print(max(self.keys))

        self.valid_lst = [pid for pid in self.pid_lst if pid in self.keys ]
        self.data = { i: self.combined_logic_forms[i] for i in self.pid_lst if i in self.keys }
        self.sequences = { i: self.sequence[str(i)] for i in self.pid_lst if i in self.keys }


    def __len__(self):
        return len(self.valid_lst)

    def __getitem__(self, idx):

        # print(idx)
        pid = self.valid_lst[idx]

        ## input logic form sequence
        input = str(self.combined_logic_forms[pid])
        tokenized_inp = self.tokenizer.encode(input)
        if len(tokenized_inp) > 500:
            tokenized_inp = tokenized_inp[:500]

        torch.LongTensor(tokenized_inp)

        ## target theorem sequence
        targets = self.sequences[pid]['seqs']
        # target = choice(targets) # random choice one sequence
        target = targets[0]  # min length

        tokenized_tar = self.tokenizer.encode(str(target))
        # print(tokenized_inp, tokenized_tar)

        return tokenized_inp, tokenized_tar

