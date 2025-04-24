# 语言模型训练流程
- Step 1: Prepare dictionary from language model
python tools/fst/prepare_dict_from_lm.py $dir/dict/units.txt $dir/lm/lm.arpa $dir/dict/lexicon.txt $dir/train_unigram5000.model
- Step 2: Compile lexicon token FST
bash tools/fst/compile_lexicon_token_fst.sh $dir/dict $dir/tmp $dir/lang

- Step 3: Make TLG
bash tools/fst/make_tlg.sh $dir/lm $dir/lang $dir/tlg
