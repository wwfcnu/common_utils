#encoding:utf8
import requests
import json
import pandas as pd
from tqdm import tqdm
import uuid
import csv

def GPT4(q):
    try:
        if not q:
            pass
        token = ""
        url = f"http://43.153.59.172:30002/openai"
        para = {
            "question": q,
            "token":token
        }
        answer = requests.post(url=url, json=para).text
        return answer
    except Exception as e:
        if "Internal Server err" in e:
            pass
def GPT35(q):
    try:
        if not q:
            pass
        token = ""
        url = f"http://43.153.59.172:30001/openai"
        para = {
            "question": q,
            "token":token
        }
        answer = requests.post(url=url, json=para).text
        return answer
    except Exception as e:
        if "Internal Server err" in e:
            pass
if __name__ == '__main__':

   

    # 读取CSV文件
    df = pd.read_csv("/mnt/data/music_audioset/Music_genre/genre_eval_segments_match.csv")

    data = []

    # 遍历DataFrame的每一行
    for index, row in df.iterrows():
        # 获取当前行的数据
        YTID = row['YTID']
        positive_labels = row['positive_labels']
        
        # 将当前行数据转换为字典，并添加到data列表中
        data_dict = {"YTID": YTID, "positive_labels": positive_labels}
        data.append(data_dict)

   
        


    
    

    with open("music_audioset_genre_eval_gpt4.txt", "w") as f:
        for item in tqdm(data):    
            YTID = item["YTID"]
            label = item["positive_labels"]
            label_list = label.split("\t")
              
            text = '''
            I will give you a list containing sound events. Write an one-sentence audio caption to describe these sounds.
            Make sure you are using grammatical subject-verb-object sentences. Directly describe the sounds and avoid using the word “heard”. The caption should be less than 20 words.
            The list is:{caption}
            The format of each output sentence is as follows:
            Caption:"",Chinese Translation:"".
            
            '''.format(
                caption=label_list
            )
        
            caption = GPT4(text)
            print(caption)
            f.write(f"{YTID}\t{caption}\n")
            f.flush()
            
            

    
