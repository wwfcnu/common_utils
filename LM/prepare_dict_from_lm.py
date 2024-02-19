#!/usr/bin/env python3
# encoding: utf-8

import sys

# sys.argv[1]: e2e model unit file(lang_char.txt)
# sys.argv[2]: raw lexicon file
# sys.argv[3]: output lexicon file
# sys.argv[4]: bpemodel

unit_table = set()
with open(sys.argv[1], 'r', encoding='utf8') as fin:
    for line in fin:
        unit = line.split()[0]
        unit_table.add(unit)


def contain_oov(units):
    for unit in units:
        if unit not in unit_table:
            return True
    return False

bpemode = len(sys.argv) >= 4
if bpemode:
    import sentencepiece as spm
    sp = spm.SentencePieceProcessor()
    sp.Load(sys.argv[4])
lexicon_table = set()
special_words = set(['<s>', '</s>', '<unk>', 'SIL', '<UNK>', '<SPOKEN_NOISE>'])
with open(sys.argv[2], 'r', encoding='utf8') as fin, \
        open(sys.argv[3], 'w', encoding='utf8') as fout:
    unigram_start=False
    for line in fin:
        if line.startswith('\\1-grams:'):
            unigram_start = True
            continue

        if unigram_start and line.strip():
            if line.startswith('\\2-grams:'):
                break
            word = line.strip().split()[1].strip()
            if word in special_words or word.startswith('#'):
                    continue
            else:
                if word in lexicon_table:
                    continue
                if bpemode:
                    if "'" in word or (word.encode('utf8').isalpha() and '▁' in unit_table):
                        pieces = sp.encode_as_pieces(word)
                        print(pieces)
                        if contain_oov(pieces):
                            print(
                                'Ignoring words {}, which contains oov unit'.format(
                                    ''.join(word).strip('▁'))
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
                    # ignore words with OOV
                    if contain_oov(word):
                        print('Ignoring words {}, which contains oov unit'.format(word))
                        continue
                    # Optional, append ▁ in front of english word
                    # we assume the model unit of our e2e system is char now.
                    if word.encode('utf8').isalpha() and '▁' in unit_table:
                        # word = '▁' + word
                        word = word
                    chars = ' '.join(word)  # word is a char list
                    
                fout.write('{} {}\n'.format(word, chars))
                lexicon_table.add(word)
