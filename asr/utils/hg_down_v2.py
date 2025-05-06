
import os
import requests
from scrapy import Selector
import json
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue,Empty
from tqdm import tqdm
import argparse
import sys
import subprocess
# 屏蔽warning信息
requests.packages.urllib3.disable_warnings()


headers = {
    "authority": "huggingface.co",
    "accept": "text/html,application/xhtml+xml,application/xml,application/zip;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "zh-CN,zh;q=0.9",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "sec-ch-ua": "\"Not A(Brand\";v=\"99\", \"Google Chrome\";v=\"121\", \"Chromium\";v=\"121\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}
# cookies = {
#     "__stripe_mid": "f98ccf50-0d23-47ac-bd17-7488bb004fadd80798",
#     "token": "gIosPKGgbuUcphgmoBRcokfKlftQEoLJyloawGzIkaXLEaAuGNFoccLusPucmhEJXvXdfsqRDmKkSOwfgAnpBMdiYsoCyZzaiZBfkXFqeVLojWzcbJvZYOFkfBjqPfvj",
#     "_ga": "GA1.1.954514292.1668501649",
#     "_ga_R4JMGZWPD9": "GS1.1.1701931745.1.1.1701932458.0.0.0",
#     "_ga_8Q63TH4CSL": "GS1.1.1706688201.161.1.1706688249.12.0.0",
#     "hf-chat": "ac0b61d6-597f-4adc-8c79-a8bfd604f7d8",
#     "__stripe_sid": "ad8bab16-980f-4b2a-9cfc-8f418db8725a806630",
#     "aws-waf-token": "a23d300b-0547-4038-9f4e-168536d25e99:AAoAknYV04ULAAAA:9oM0Jd+wYTPIilC3pH7KsNzLT/Mz5jQnwbLhGtyEUm8GNJTSJzZCuiesAZzNZLoT9i2rPVMWYmJuLQ5b7U9cqsXZLvvRmFs+ZFmKuC1sdXOXp/uQCQH6cdGaRvLS+GOtN+Sw8t8Sv+SuSaTngJmXtFXV6Nb/9gNSQ9cUO8ukn6S0+mOmfLcY1SA6yFA9z1QNDhbnlLcOeJfzkrGLATaUNHT/hQqOOVcTsn8KuFVy5ue8/8Ecpm8YQ/cvSocd3RehOJhZKqU="
# }
cookies = {
    "__stripe_mid": "03d3e3c7-2767-4343-9fd1-8f730a177380012078",
    "token": "AOppEoGOOuogZrDoytoCTIPlYywDyrARPsWWyTqVsVnsikGmOqwwniyOInciddOvPFcqXGDKcpLTmsetVnvwqoRblWJISUjalcjHumtNioiiMwjPlWcQjnlCvwaOAsKa",
    "_ga_8Q63TH4CSL": "GS1.1.1711004406.129.1.1711005406.60.0.0",
    "_ga": "GA1.2.1127549579.1692929477",
    "__stripe_sid": "d25f9104-e6ca-49ac-999f-f6ecfbe5b885766675",
    "aws-waf-token": "051fc46e-ebc5-4df0-be34-05919ddf87a0:EwoA43RBJHA4AAAA:3HypLuZl9OeNI2dNCgSPJwjGxjdRlHaIVr0s/7Ng9b5oploC03VtHleq9WudcHgsnqg3T6TMIJeg+Df4AIMcv8nO6ChO6fdvhYTTddN9RqeCc0CefKH9L4QphIau2m1GwTd1ionbY3s6bxY3hm+eRvEiCSaAP6aO2brVVFNs4IS8uDLZwLLrQkS+p7EOH3rBiodrTgRRTeXaxLHaviO1T2LC+1t5c3aTs2ydP6RQy5LWf3J/gs4wXXpzzbrD0TOj1LZ9MM/r4DZoPRHWRTc="
}

# 删除文件
def delete_file(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        print(f"文件 '{file_path}' 已被删除，重新下载")
    except OSError as e:
        print(f"删除文件时出错: {e.strerror},{file_path}")

def down_file(work_id):
        # 从队列中获取数据
        while data_queue.qsize():
            try:  
                data = data_queue.get() 
            except Empty:
                # 如果队列为空，可以处理异常或者返回
                return None
            
            file_path,file_url,size =data.split("^")
            if os.path.exists(file_path) and size == os.path.getsize(file_path):
                print(f"{file_path} down_file() already exists")
                continue
            retry = 1
            while True:
                time.sleep(1)
                try:
                    with requests.get(file_url, stream=True, headers=headers,cookies=cookies,timeout=120) as response:
                        # 请求文件的大小单位字节B
                        if response.status_code==200:
                            total_size = int(response.headers.get('content-length',0))
                            with tqdm(total=total_size, unit='B', unit_scale=True, desc=f'--work_id:{work_id}  [{total_task-data_queue.qsize()}/{total_task}] Downloading {file_path}') as pbar:
                                with open(file_path, 'wb') as f:   
                                    for content in response.iter_content(chunk_size=1024):
                                        f.write(content)
                                        pbar.update(len(content))   
                            print(f"{file_path},在第{retry}次成功下载,--work_id:{work_id} total_size:,{total_size}")
                            break
                        else:
                             retry+=1               
                except Exception as e :
                    print(e)
                    retry+=1
        return f"--work_id:{work_id} finish!"
            

def down_file_V2(work_id):
    # 从队列中获取数据
    while data_queue.qsize():
        try:  
            data = data_queue.get_nowait()
        except Empty:
            # 如果队列为空，可以处理异常或者返回
            return None
        
        file_path,url,total_size =data.split("^")
        total_size = int(total_size)

        # 重置请求头
        local_headers = headers.copy()


        if os.path.exists(file_path) and total_size == os.path.getsize(file_path):
            print(f"{file_path} down_file() already exists")
            continue
    
        if os.path.exists(file_path):
            temp_size = os.path.getsize(file_path)  # 本地已经下载的文件大小
            # 核心部分，这个是请求下载时，从本地文件已经下载过的后面下载
            # headers = {'Range': 'bytes=%d-' % temp_size}
            local_headers.update({'Range': 'bytes=%d-' % temp_size})
        else:
            temp_size = 0
        if temp_size == 0:
            local_headers.pop('Range', None)  # 确保没有 Range 头

        # 显示一下下载了多少
        print(f"已经下载了{temp_size}/{total_size} {file_path}")
        
        # 重新请求网址，加入新的请求头的
        try:
            r = requests.get(url, stream=True, verify=False,cookies=cookies, headers=local_headers,timeout=10)
            # print(r.status_code)
            # print(r.headers)
            # print(r.content)
            if int(r.status_code) not in [200,206]:
                return f"--work_id:{work_id} finish! status_code={r.status_code},{url}"
            with open(file_path, "ab") as f,tqdm(total=total_size,unit='B', unit_scale=True,initial=temp_size,leave=True,desc=f'--work_id:{work_id}  [{total_task-data_queue.qsize()}/{total_task}] Downloading {file_path}') as bar:
                for content in r.iter_content(chunk_size=1024):
                    if content:
                        f.write(content)
                        f.flush()
                        bar.update(len(content)) 
        except Exception as e:
            print(e)
            print(f"--work_id:{work_id} 下载失败")
            continue
        # 下载完成，保存记录
    return f"--work_id:{work_id} finish!"


def download_wget(work_id):
    
    # 从队列中获取数据
    while data_queue.qsize():
        try:  
            data = data_queue.get() 
        except Empty:
            # 如果队列为空，可以处理异常或者返回
            return None
        
        file_path,url,total_size =data.split("^")
        total_size = int(total_size)
        if os.path.exists(file_path) and total_size == os.path.getsize(file_path):
            print(f"{file_path} down_file() already exists")
            continue
        process = subprocess.Popen(
            ["wget", "-c", "--no-check-certificate","-O",file_path, url],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True  # 使输出为字符串而不是字节
        )

        # 实时处理输出
        for line in iter(process.stdout.readline, ''):
            # 用回车符覆盖同一行
            sys.stdout.write('\r' + line.replace('\n', '').replace('\r', ''))
            sys.stdout.flush()

        # 等待子进程结束
        process.stdout.close()
        process.wait()
    return f"--work_id:{work_id} finish!"


def get_net_URL(url):
    if "huggingface.co" in url:
        url = url.replace("huggingface.co","hf-mirror.com")
    res_list = []
    while 1:
        try:
            time.sleep(0.5)
            res = requests.get(url,headers=headers,cookies=cookies,timeout=10)
            if res.status_code == 200:
                break
        except Exception as e:
            print(e)

    js = res.json()
    res_list+=js
    Link =  res.headers.get("Link","")
    if Link:
        next_url = Link.split(';')[0][1:-1]
        res_list+=get_net_URL(next_url)
    return res_list

def get_files(url):
    file_list = []
    entries_list = []

    while 1:
        try:
            time.sleep(0.5)
            res = requests.get(url,headers=headers,cookies=cookies,timeout=10)
            if res.status_code == 200:
                break
        except Exception as e:
            print(e)
    sel = Selector(res)
    ModelHeader = sel.css('[data-target=ViewerIndexTreeList]')
    js = json.loads(ModelHeader.css('div::attr(data-props)').get())
    nextURL = js["nextURL"]
    tmp_res = []
    if nextURL:
        nextURL = "https://hf-mirror.com"+nextURL
        tmp_res = get_net_URL(nextURL)
        entries_list+=tmp_res
    entries = js["entries"]
    entries_list+=entries
    entries+=tmp_res
    for e in entries:
        type = e["type"]
        file_name = e["path"]
        if type == "file": 
            file_url =  f"https://hf-mirror.com/{model_id}/resovle/main/"+file_name
            # file_path = f"{model_id}/{file_name}"
            # resume_download(file_url, file_path)
            # print(file_url)
            file_list.append(file_url)
        if type == "directory":
            url = f"https://hf-mirror.com/{model_id}/tree/main/"+file_name
            f,en = get_files(url)
            file_list+=f
            entries_list+=en
            # print(file_name,len(en))
    return file_list,entries_list


if __name__ == '__main__':

    # 创建一个ArgumentParser对象
    parser = argparse.ArgumentParser(description="huggingface 下载程序，使用镜像地址：https://hf-mirror.com")

    # 添加一个命令行参数
    parser.add_argument("-t", "--hg_type", type=str, help="下载的数据类型，model or datasets",choices=['model', 'datasets'], required=True)
    parser.add_argument("-id", "--hg_id",type=str, help="待下载的ID，可在网页上复制（例子：miqudev/miqu-1-70b）", required=True)
    parser.add_argument("-redown", "--redown",type=str, help="是否重新下载:1是，0否）",default=1, required=False)
    parser.add_argument("-o", "--output_folder",type=str, help="输出路径）",required=True)
    # 解析命令行参数
    args = parser.parse_args()
    print(parser)
    if args.hg_type=="model":
        model_id=args.hg_id
        # output_folder = "/home/share/models/"
    elif args.hg_type=="datasets":
        model_id=f"datasets/{args.hg_id}"
        # output_folder = "/home/share/dataset/"
    output_folder = args.output_folder
    # model_id = "openlm-research/open_llama_3b_v2"
    # model_id = "datasets/Ejafa/ye-pop"
    # model_id = "miqudev/miqu-1-70b"
    # model_id = "datasets/codeparrot/github-code"
        
    
    url = f"https://hf-mirror.com/{model_id}/tree/main"

    out_dir = os.path.join(output_folder,args.hg_id.split('/')[1])
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    #1.下载元数据,如果元数据存在，则不下载
    hg_down_info_path = f"{out_dir}/hg_down_info.json"
    if args.redown=="1":
        file_list,entries = get_files(url)  
        with open(hg_down_info_path,"w") as w:
            json.dump(entries,w,ensure_ascii=False,indent=4)
    else:
        pass
    if not os.path.exists(hg_down_info_path):
        file_list,entries = get_files(url)  
        with open(hg_down_info_path,"w") as w:
            json.dump(entries,w,ensure_ascii=False,indent=4)
    # import sys
    # sys.exit(1)

    while True:
        #2.把需要下载的文件加入到Queue队列，并创建好子目录
        data_queue = Queue()
        with open(hg_down_info_path,"r") as r:
            js = json.load(r)
            to_be_down = []
            for line in js:
                type = line["type"]
                if type == "directory":
                    sub_folder = os.path.join(out_dir,line["path"])
                    if not os.path.exists(sub_folder):
                        os.makedirs(sub_folder)
                elif type == "file":
                    file_path = os.path.join(out_dir,line["path"])
                    if ".gitattributes" in file_path:
                        continue
                    file_url =  f"https://hf-mirror.com/{model_id}/resolve/main/"+line["path"]
                    if os.path.exists(file_path) and line['size'] == os.path.getsize(file_path):
                        # print(f"{file_path} already exists")
                        pass
                    elif os.path.exists(file_path) and line['size'] < os.path.getsize(file_path):
                        os.remove(file_path)
                        data_queue.put(f"{file_path}^{file_url}^{line['size']}")
                    
                    else:
                        data_queue.put(f"{file_path}^{file_url}^{line['size']}")
            
        #3.下载数据
        max_workers = 3
        total_task = data_queue.qsize()
        if data_queue.qsize() == 0:
            print("total_task:",total_task)
            break
        print("total_task:",total_task)
        if total_task>max_workers:
            pass
        else:
            max_workers = total_task
        with ThreadPoolExecutor(max_workers=max_workers) as executor:  # 指定最大工作线程
            # 使用executor.submit()提交任务
            futures = [executor.submit(down_file_V2, work_id) for work_id in range(max_workers)]
            # 等待所有任务完成并获取结果
            for future in futures:
                result = future.result()
                if result is not None:
                    print(f"Result from worker: {result}")

    
