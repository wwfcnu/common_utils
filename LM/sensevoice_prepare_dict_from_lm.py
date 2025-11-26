#!/usr/bin/env python3
# encoding: utf-8

import sys
import json

# sys.argv[1]: e2e model unit file(tokens.json)
# sys.argv[2]: lm.arpa
# sys.argv[3]: output lexicon file
# sys.argv[4]: bpemodel（chn_jpn_yue_eng_ko_spectok.bpe.model）

unit_table = set()
with open(sys.argv[1], 'r', encoding='utf8') as fin:
    tokens = json.load(fin)
    for token in tokens:
        unit_table.add(token)


def contain_oov(units):
    for unit in units:
        if unit not in unit_table:
            return True
    return False

bpemode = len(sys.argv) >= 5
if bpemode:
    import sentencepiece as spm
    sp = spm.SentencePieceProcessor()
    sp.Load(sys.argv[4])

lexicon_table = set()
special_words = set(['<s>', '</s>', '<unk>', 'SIL', '<UNK>', '<SPOKEN_NOISE>'])

with open(sys.argv[2], 'r', encoding='utf8') as fin, \
        open(sys.argv[3], 'w', encoding='utf8') as fout:
    unigram_start = False
    for line in fin:
        if line.startswith('\\1-grams:'):
            unigram_start = True
            continue

        if unigram_start and line.strip():
            if line.startswith('\\2-grams:'):
                break
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            word = parts[1].strip()
            if word in special_words or word.startswith('#'):
                continue
            
            if word in lexicon_table:
                continue
            
            if bpemode:
                # 使用 BPE 模型对词汇进行编码
                if "'" in word or (word.encode('utf8').isalpha() and '▁' in unit_table):
                    pieces = sp.encode_as_pieces(("▁"+word).lower())
                    if contain_oov(pieces):
                        print(
                            'BPE,Ignoring words {}, which contains oov unit'.format(word)
                        )
                        continue
                    chars = ' '.join(
                        [p if p in unit_table else '<unk>' for p in pieces])
                else:
                    if contain_oov(word):
                        print(
                            'Ignoring words {}, which contains oov unit'.format(
                                ''.join(word).strip('▁'))
                        )
                        continue
                    chars = ' '.join(word)
            else:
                # 不使用 BPE 模型，按字符处理
                # 检查是否包含 OOV 字符
                if contain_oov(word):
                    print('Ignoring words {}, which contains oov unit'.format(word))
                    continue
                # 如果是纯英文字母且 unit_table 中包含 ▁，保持原样
                if word.encode('utf8').isalpha() and '▁' in unit_table:
                    word = word
                chars = ' '.join(word)  # word 按字符分割
                    
            fout.write('{} {}\n'.format(word, chars))
            lexicon_table.add(word)
