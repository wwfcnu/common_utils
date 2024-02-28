#encoding:utf8
import requests
import json
import pandas as pd
from tqdm import tqdm
import uuid


def GPT4(q):
    try:
        if not q:
            pass
        token = "AooHHycGrgORgDx8T3BlbkFJkq2efbrjIXJMLm5w"
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

if __name__ == '__main__':

    
    with open("/mnt/data1/AudioDataset/download/clotho/clotho_val_translate.txt") as f:
        lines = f.readlines()
        data = []
        for line in lines:
            line = line.strip().split("\t")
            id = line[0]
            caption_1 = line[1]
            caption_2 = line[2]
            caption_3 = line[3]
            caption_4 = line[4]
            caption_5 = line[5]
            item = {
                "id": id,
                "caption_1": caption_1,
                "caption_2": caption_2,
                "caption_3": caption_3,
                "caption_4": caption_4,
                "caption_5": caption_5
            }
            data.append(item)

    
    
    with open("clotho_test_gpt4.txt", "w") as f:
        for item in tqdm(data):
            id = item["id"]
            caption_1 = item["caption_1"]
            caption_2 = item["caption_2"]
            caption_3 = item["caption_3"]
            caption_4 = item["caption_4"]
            caption_5 = item["caption_5"]
            #text = f"create a single English caption that encompasses the content of the following five captions, which describe a piece of audio:\n1. {caption_1}\n2. {caption_2}\n3. {caption_3}\n4. {caption_4}\n5. {caption_5}\nJust output the single English caption and its corresponding Chinese translation"
            text = '''
            Compose a single english description and chinese description that encompasses the content of the following five captions, which describe a piece of audio
            1. {caption_1}
            2. {caption_2}
            3. {caption_3}
            4. {caption_4}
            5. {caption_5}
            Example (Output Format):
            English Caption: [ english description ]
            Chinese Caption:[ chinese description ]
            '''.format(
                caption_1=caption_1,caption_2=caption_2,caption_3=caption_3,caption_4=caption_4,caption_5=caption_5
            )
        
            caption = GPT4(text)
            print(caption)
            f.write(f"{id}\t{caption}\n")
            f.flush()


            # English Description: [Provide a concise summary of the audio content in English]
            # Chinese Description: [在中文中提供对音频内容的简要总结]
