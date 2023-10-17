import os
import glob
import concurrent.futures
from tqdm import tqdm
import subprocess

# Define a dictionary to map Chinese usernames to English usernames
username_mapping = {
    '新闻夜班': 'News_Night_Shift',
    '珠江新闻': 'Pearl_River_News',
    '每日经济新闻': 'Daily_Economic_News',
    'BRTV新闻': 'BRTV_News',
    '动静新闻': 'Dynamic_News',
    '潮新闻': 'Tide_News',
    '高度新闻': 'Altitude_News',
    '青豆新闻': 'Green_Bean_News',
    '今日热点': "Today_Hot_Topics",
    '荔枝新闻': 'Lychee_News',
    '闪电新闻': 'Lightning_News',
    '极光新闻': 'Aurora_News',
    '陕视新闻': 'Shanxi_TV_News',
    '新闻快车': 'News_Express',
    '央视军事报道': 'CCTV_Military_Report',
    '新华网': 'Xinhua_News',
    '凤凰卫视': 'Phoenix_Satellite_TV',
    '看看新闻Knews': 'Knews',
    '环球网': 'Global_Network',
}

def extract_audio(video_path, output_file):
    try:
        command = ["ffmpeg", "-i", video_path, "-vn", "-c:a", "aac", "-strict", "experimental", output_file]
        subprocess.run(command, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"提取{video_path}失败")

def main(video_path):
    aweme_id = video_path.split("/")[-1].split(".")[0]
    username = video_path.split("/")[-2]  # Extract the username from the path
    if username in username_mapping:
        username_en = username_mapping[username]
        output_dir = os.path.dirname(video_path).replace(username, username_en).replace("video", "audio")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{aweme_id}.m4a")
        if not os.path.exists(output_file):  # Check if the output file already exists
            extract_audio(video_path, output_file)
        else:
            print(f"{output_file} 已存在，跳过提取。")

if __name__ == "__main__":
    usernames = ['新闻夜班','珠江新闻','每日经济新闻','BRTV新闻','动静新闻','潮新闻','高度新闻','青豆新闻','今日热点','荔枝新闻','闪电新闻','极光新闻','陕视新闻','新闻快车','央视军事报道','新华网','凤凰卫视','看看新闻Knews','环球网']
    for username in usernames:
        print(f"正在提取的用户{username}")
        video_list = glob.glob(f"/obsfs/asr_datasets/network_datasets/douyin/video/news/{username}/*.mp4")
        max_workers = 10
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            list(tqdm(executor.map(main, video_list), total=len(video_list)))
