# 语言模型训练流程
- Step 1: Prepare dictionary from language model
python tools/fst/prepare_dict_from_lm.py $dir/dict/units.txt $dir/lm/lm.arpa $dir/dict/lexicon.txt $dir/train_unigram5000.model
- Step 2: Compile lexicon token FST
bash tools/fst/compile_lexicon_token_fst.sh $dir/dict $dir/tmp $dir/lang

- Step 3: Make TLG
bash tools/fst/make_tlg.sh $dir/lm $dir/lang $dir/tlg






https://www.modelscope.cn/models/thuduj12/speech_sensevoice_ngram_lm_zh-en-fst/files



- sensevoice-small:``` 替换<unk>为<blank> ```


```sh
(base) [wangweifei@localhost wenet]$ more run_sensevoice_small.sh
#!/bin/bash
dir="/mnt/data/laion-ai/language_model/sensevoice_20260120_small"
# dir="/mnt/data/laion-ai/language_model/donghugaoxin_20241205"
# Step 1: Prepare dictionary from language model
# python tools/fst/paraformer_prepare_dict_from_lm.py $dir/dict/units.txt $dir/lm/lm.arpa $dir/dict/lexicon.txt $dir/seg_dict
# python tools/fst/prepare_dict_from_lm.py $dir/dict/units.txt $dir/lm/lm.arpa $dir/dict/lexicon.txt $dir/train_unigram5000.model
# python tools/fst/sensevoice_prepare_dict_from_lm.py $dir/dict/tokens.json $dir/lm/lm.arpa  $dir/dict/lexicon.txt $dir/chn_jpn_yue_eng_ko_spectok.bpe
.model
# Step 2: Compile lexicon token FST
bash tools/fst/compile_lexicon_token_fst.sh $dir/dict $dir/tmp $dir/lang

# Step 3: Make TLG
bash tools/fst/make_tlg.sh $dir/lm $dir/lang $dir/tlg

```
