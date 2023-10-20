import os
import pandas as pd



from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm


import requests
import json
from requests_toolbelt.multipart import MultipartEncoder
import time
import os

# batch推理

# 2023.02.16 NOTE：更新modelscope，pip install modelscope --upgrade -i  https://pypi.tuna.tsinghua.edu.cn/simple

# 温馨提示: 使用pipeline推理及在线体验功能的时候，尽量输入单句文本，如果是多句长文本建议人工分句，否则可能出现漏译或未译等情况！！！

from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks


import json
import os
import re
from tqdm import tqdm
import concurrent.futures
import logging
import sys
os.environ['CUDA_VISIBLE_DEVICES'] = "6"

logging.disable(sys.maxsize) #关闭日志

pipeline_ins = pipeline(task=Tasks.translation, model="damo/nlp_csanmt_translation_en2zh")

def replace_underscore(tag): 
    
    tag = re.sub(r"-+", " ",tag)
    return tag
def modelscope_trans(batch_input_sequences):

    # batch_input_sequences = [
    #     "Elon Musk, co-founder and chief executive officer of Tesla Motors.",
    #     "Alibaba Group's mission is to let the world have no difficult business",
    #     "What's the weather like today?"
    # ]
    input_sequence = '<SENT_SPLIT>'.join(batch_input_sequences)   # 用特定的连接符<SENT_SPLIT>，将多个句子进行串联

    #pipeline_ins = pipeline(task=Tasks.translation, model="damo/nlp_csanmt_translation_en2zh")
    outputs = pipeline_ins(input=input_sequence)

    #print(outputs['translation'].split('<SENT_SPLIT>')) # ['特斯拉汽车公司联合创始人兼首席执行官埃隆 · 马斯克。', '阿里巴巴集团的使命是让世界没有困难的生意', '今天的天气怎么样？']
    return outputs['translation'].split('<SENT_SPLIT>')


'''
多个文件循环翻译，翻译label

'''
# 读取文件
def read_file(file):
    '''
    tags是合并了genres，moods，instruments

    '''

    # 读取CSV文件
    df = pd.read_csv(file)

    # 定义一个函数，用于处理genres，moods和instruments字段
    def combine_tags(row):
        genres = eval(row['genres']) if pd.notna(row['genres']) else []
        moods = eval(row['moods']) if pd.notna(row['moods']) else []
        instruments = eval(row['instruments']) if pd.notna(row['instruments']) else []
        
        # 合并所有的标签
        tags = genres + moods + instruments
        return tags

    # 使用apply函数将处理后的tags字段添加到DataFrame中
    df['tags'] = df.apply(combine_tags, axis=1)

    # 将DataFrame转换为列表字典
    data_list = df[['id','description', 'tags']].to_dict(orient='records')
    # 创建最终的JSON数据
    final_data = {"data": data_list}
    return final_data




#英文批量翻译中文
def translate_xiaochu_batch(text):
    """
    [summary]

    Args:
        line ([type]): [description]
        mention ([type], optional): [description]. Defaults to None.
        port (int, optional): [description]. Defaults to 8080.

    Returns:
        [type]: [description]
    """
    origin_text = text
    # 输入为list类型，批量翻译
    if "list" in str(type(text)):
        my_list = [x.replace('\n', '') for x in text]
        text = "\n".join(my_list)
        my_url = 'http://159.226.21.8:7008/'
        data = {
            "txt": str(text),
            "tgtLang": "zh"
        }
        my_params = MultipartEncoder(data)
        header = {'Content-Type': my_params.content_type}
        try:
            r = requests.post(url=my_url, data=my_params, headers=header)
            json_result = json.loads(r.text)
            trans_result = json_result['data']
            split_str = '\n'
            trans_result = list(trans_result.split('\n'))
            return trans_result
        except Exception as e:
            print("trans error: " + str(e))
            return origin_text
    # 输入为str类型，单个翻译
    else:
        my_url = 'http://159.226.21.8:7008/'
        origin_text = text
        data = {
            "txt": str(text),
            "tgtLang": "zh"
        }
        my_params = MultipartEncoder(data)
        header = {'Content-Type': my_params.content_type}

        try:
            r = requests.post(url=my_url, data=my_params, headers=header)
            json_result = json.loads(r.text)
            trans_result = json_result['data']
            print("origin_text:" + str(origin_text) + "\t" + "trans_result: " + str(trans_result))
            return trans_result
        except Exception as e:
            print("trans error: " + str(e))
            return origin_text




# 定义任务函数 translate_file
def translate_file(batch):

    tags_list = []
    js_caption = []
    for js in batch:
       
        caption = js["description"]     
        js_caption.append(caption)

        tags = js["tags"]
        tags_list.append(tags)  
    

    # 批次翻译caption
    caption_zh = translate_xiaochu_batch(js_caption)
    print(caption_zh)
    #js["description_zh"] = caption_zh

  
    # 批次翻译label(tag),将多个tags列表相加形成一个列表,每个tags:List
    combined_tags_list = sum(tags_list, [])
    tags_zh_list = translate_xiaochu_batch(combined_tags_list)
    print(combined_tags_list)
    print(tags_zh_list)

    # 恢复tags结构
    restored_tags_list = []
   
    start = 0

    # 按照原始结构恢复tags_list
    for sublist in tags_list:
        sublist_len = len(sublist)
        restored_tags_list.append(tags_zh_list[start:start+sublist_len])
        start += sublist_len

    
    #caption_zh_list = translate_xiaochu_batch(caption_list)

    # 更新翻译结果
    for i, js in enumerate(batch):
        js["tags_zh"] = restored_tags_list[i]
        js["description_zh"] = caption_zh[i]
    
    return batch

def split_batch(js_data):
# 按照字符长度将输入列表分成多个批次
    batch_size_limit = 1000
    batches = []
    current_batch = []
    current_length = 0

    for item in js_data:
        
        #caption_len =len(item["text"])
        #item_length = max(description_len,tags_len,caption_len)
        tag_len = ' '.join(item["tags"])
        item_length = len(tag_len)
        
        if current_length + item_length <= batch_size_limit:
            current_batch.append(item)
            current_length += item_length
        else:
            batches.append(current_batch)
            current_batch = [item]
            current_length = item_length

    if current_batch:
        batches.append(current_batch)

    return batches

if __name__ == "__main__":

    
    split = "/mnt/data1/AudioDataset/download/modelscope_trans/shutter/shutter_1.csv"
    print(f"正在翻译{split}")
    data_dict = read_file(f"{split}")

    # 访问"data"键的值
    js_data = data_dict["data"]

    batches = split_batch(js_data)
    


    translated_file_list = []
    for batch in tqdm(batches):
        translated_file = translate_file(batch)
        translated_file_list.append(translated_file)

    # translated_file_list = []
    # with concurrent.futures.ThreadPoolExecutor(max_workers = 20) as executor:
    #     translated_file_list = list(executor.map(translate_file, batches))


    #data_dict["data"] = translated_file_list

    combined_list = [item for batch in translated_file_list for item in batch]

    # 创建新的JSON文件并将更新后的数据写入其中
    with open('shutter_modelscope_translate.json', 'w') as file:
        json.dump(combined_list, file,ensure_ascii=False)
