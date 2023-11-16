# 还可以导入retrying模块



import requests
import re
import json
from bs4 import BeautifulSoup
import time

def get_text(id, max_retries=3):
    retries = 0

    while retries < max_retries:
        try:
            url = f"https://m.ximalaya.com/sound/{id}"
            params = {
                "source": "pc_jump"
            }
            response = requests.get(url, headers=headers, cookies=cookies, params=params)
            response.raise_for_status()  # Raises an exception for 4xx and 5xx status codes

            pattern = r'window.__INITIAL_STATE__ = (\{.*?\});'
            match = re.search(pattern, response.text)

            if match:
                initial_state_text = match.group(1)
            else:
                print("未找到__INITIAL_STATE__的内容")
                return None

            data_info = json.loads(initial_state_text)
            rich_info = data_info["store"]["trackPage"]["trackRichInfo"]["richIntro"]

            # 使用BeautifulSoup解析HTML内容
            soup = BeautifulSoup(rich_info, 'html.parser')

            # 提取纯文本内容
            text_only = soup.get_text()

            return text_only

        except Exception as e:
            print(f"发生错误: {e}")
            retries += 1
            if retries < max_retries:
                print(f"等待{retries}秒后重试...")
                time.sleep(retries)
    
    print(f"无法获取内容，已达到最大重试次数 ({max_retries})")
    return None

# 创建一个字典来存储id和对应的text
    
    # data_dict = {}

    # for id in id_list:
    #     text = get_text(id)
    #     if text is not None:
    #         data_dict[id] = text

    # # 将字典写入JSON文件
    # output_json_file = "output.json"
    # with open(output_json_file, "w", encoding="utf-8") as json_file:
    #     json.dump(data_dict, json_file, ensure_ascii=False, indent=4)

    # print(f"写入JSON文件完成: {output_json_file}")
