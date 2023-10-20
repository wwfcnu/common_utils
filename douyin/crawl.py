import requests
import execjs
import pandas as pd
import time
from fake_useragent import UserAgent
import random
import os
from urllib.parse import urlencode
from loguru import logger
from retrying import retry
ua = UserAgent()

@retry(stop_max_attempt_number=5, wait_exponential_multiplier=1000, wait_exponential_max=20000)
def fetch_data(user_id, user_name, headers, cookies, params):
 
    url = "https://www.douyin.com/aweme/v1/web/aweme/post/"
  
    response = requests.get(url, headers=headers, cookies=cookies, params=params)
    response.raise_for_status()  # Raise an exception for 4xx and 5xx errors
    response_json = response.json()  # Convert response to JSON
    return response_json

@retry(stop_max_attempt_number=5, wait_exponential_multiplier=1000, wait_exponential_max=20000)
def download_url(url,user_id,user_name,aweme_id,headers, cookies,params):
   
    output_dir = "/obsfs/asr_datasets/network_datasets/douyin/video/news"
    os.makedirs(f"/obsfs/asr_datasets/network_datasets/douyin/video/news/{user_name}",exist_ok=True)
    video_path = os.path.join(output_dir,f"{user_name}/{aweme_id}.mp4")

    if os.path.exists(video_path):
        print(f"Skipped {user_name}: {url} (File already exists)")
    else:
        video = requests.get(url,  headers=headers, cookies=cookies, params=params).content
        
        with open(video_path, 'wb') as f:
            f.write(video)
            f.flush()
            print(f"下载完成{user_name}: {aweme_id}")



headers = {
    "authority": "www.douyin.com",
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9",
    "referer": "https://www.douyin.com/",
    "sec-ch-ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"117\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

cookies = {
    "ttwid": "1%7C46Dw0jY9cmyIQYb4lnM6Fhr2n41Od5dF7b4DWp2Ylxs%7C1692934859%7C3e5ef03019b251c2cf2c7715a1f32edd7ce3d6d4a013fa9b56023a48b0c7be6b",
    "passport_csrf_token": "91200abee25ff32891695bb9f023bbe5",
    "passport_csrf_token_default": "91200abee25ff32891695bb9f023bbe5",
    "s_v_web_id": "verify_llq1pouh_z4VahULg_iPPr_41Fd_9V56_1mn17xv7jBSl",
    "douyin.com": "",
    "device_web_cpu_core": "8",
    "device_web_memory_size": "8",
    "webcast_local_quality": "null",
    "csrf_session_id": "6bfd02db565606f0aeff422d3b6809ad",
    "xgplayer_user_id": "558166833851",
    "__security_server_data_status": "1",
    "store-region": "cn-hb",
    "store-region-src": "uid",
    "my_rd": "2",
    "d_ticket": "79759c8784b9f2d954550149b9e5de701ef7a",
    "n_mh": "9-mIeuD4wZnlYrrOvfzG3MuT6aQmCUtmr8FxV8Kl8xY",
    "pwa2": "%220%7C0%7C3%7C1%22",
    "FORCE_LOGIN": "%7B%22videoConsumedRemainSeconds%22%3A180%2C%22isForcePopClose%22%3A1%7D",
    "passport_auth_status": "8b2a0a0546d3dc3e7b18af50e9101b0d%2C728d29f3a02ef67c7d559452134ba4ec",
    "passport_auth_status_ss": "8b2a0a0546d3dc3e7b18af50e9101b0d%2C728d29f3a02ef67c7d559452134ba4ec",
    "FOLLOW_NUMBER_YELLOW_POINT_INFO": "%22MS4wLjABAAAAsrUeTSCm1ahf3QQknHRsdgCh9xlURBdFNqeJPhWU7L52Fy9tjv3qpvKGTZGkz_yn%2F1697558400000%2F0%2F1697537660029%2F0%22",
    "_bd_ticket_crypt_doamin": "2",
    "_bd_ticket_crypt_cookie": "2be1d1b3cdbb6e1549943183331e658b",
    "publish_badge_show_info": "%221%2C0%2C0%2C1697537680775%22",
    "LOGIN_STATUS": "0",
    "odin_tt": "090eb99cc63041da9e92ad04c2bb42c865d039ff6edd9018d59fa6174e3e65d6",
    "__ac_nonce": "0652f73d20020a6a6a2cb",
    "__ac_signature": "_02B4Z6wo00f01AWhsqQAAIDDDdMPUt3wTdgFgbYAAGRNHfJWsKtF0-Ng1wLoEn12MvbV-ZpKzZy.9AjQTSzMvWUYGt726hBB2f4vqtUfQX.p02ttGk53mdwVPRNsERiF-bzPp1NEpi8ggITP01",
    "strategyABtestKey": "%221697608660.914%22",
    "volume_info": "%7B%22isUserMute%22%3Afalse%2C%22isMute%22%3Atrue%2C%22volume%22%3A0.5%7D",
    "SEARCH_RESULT_LIST_TYPE": "%22single%22",
    "download_guide": "%223%2F20231018%2F0%22",
    "VIDEO_FILTER_MEMO_SELECT": "%7B%22expireTime%22%3A1698215024292%2C%22type%22%3A1%7D",
    "IsDouyinActive": "true",
    "stream_recommend_feed_params": "%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1512%2C%5C%22screen_height%5C%22%3A982%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A8%2C%5C%22device_memory%5C%22%3A8%2C%5C%22downlink%5C%22%3A10%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A50%7D%22",
    "home_can_add_dy_2_desktop": "%221%22",
    "bd_ticket_guard_client_data": "eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCRnNkTW8yVmxuczQrNnJ2Qno1TDlUME10NmtXMEJMc2l0eGNKU251RmYwdFF0ZnExbFRRU216aHUzS1ZjQWR3Vm11MUJJeFRvSzZ4ckNZM2Q1OUI1cTg9IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoxfQ%3D%3D",
    #"msToken": "hWp4ferDbWSMN9v--xr7UnjmqZ6FOX6j99OxboPUN1T3GFoi5snjtExZ_RDw7TMa3Kx7UJ3eEECkPTqsX7EkYGUZqq6PfpuOkW0e7gXELrer4dR5fXMkrPq48XsHUrf6",
    "tt_scid": "nyvmnrdPu5q44xiB4zuxPvKwv-UG9k.IJIRGjHC0k3k7kkomNnYXeuw1j.lyVmdwc849"
}

url = "https://www.douyin.com/aweme/v1/web/aweme/post/"

    



users_id_names = []
with open('../user_ids.txt', 'r') as file:
    for line in file:
        user_name, user_id = line.strip().split(' ')
        users_id_names.append((user_id, user_name))
 
for user_id, user_name in users_id_names:
    print(user_id)
    print(user_name)
    # headers = headers_template.copy()
    # headers["Referer"] = f"https://www.douyin.com/user/{user_id}"
    data = pd.DataFrame(columns=['user_id', 'user_name', 'aweme_id', 'desc',"url_list"])
    max_cursor = "0"  # Initial max_cursor value
    # params = {
    #         "device_platform": "webapp",
    #         "aid": "6383",
    #         "channel": "channel_pc_web",
    #         "sec_user_id": user_id,
    #         "max_cursor": "0",
    #         "count": "18",
    #         }
    while True:

        params = {
        "device_platform": "webapp",
        "aid": "6383",
        "channel": "channel_pc_web",
        #"sec_user_id": "MS4wLjABAAAAgq8cb7cn9ByhZbmx-XQDdRTvFzmJeBBXOUO4QflP96M",
        "sec_user_id": user_id,
        "max_cursor": max_cursor,
        "count":"18"
        }

        full_url = urlencode(params)
        # 找到一个可以生成x-b的代码即可
        xb = execjs.compile(open('x-b.js', 'r', encoding='utf-8').read()).call('sign', full_url, headers['user-agent'])
        print(f"--------xb---------:{xb}")
        params['X-Bogus'] = xb
       

        # print(f"-----headers------{headers}")
        # print(f"-----cookies------{cookies}")
        # print(f"-----params------{params}")
        
        #response_json = fetch_data(user_id, user_name, headers, cookies,params)
        response_json = fetch_data(user_id, user_name, headers, cookies,params)
        #print(response_json)


        if response_json is None:
            break  # Exit the loop if fetch failed


        aweme_list = response_json.get('aweme_list')
        has_more = response_json.get('has_more')
        max_cursor = response_json.get('max_cursor')

        aweme_ids = [item.get('aweme_id') for item in aweme_list]
        descs = [item.get('desc') for item in aweme_list]
        url_list = [i["video"]["play_addr"]["url_list"] for i in aweme_list]

        # 下载
        for i in zip(aweme_ids,url_list):
            aweme_id = i[0]
            url = i[1][0]
            download_url(url,user_id,user_name,aweme_id,headers, cookies,params)

        

        new_data = pd.DataFrame({'user_id': [user_id] * len(aweme_ids),
                                 'user_name': [user_name] * len(aweme_ids),
                                 'aweme_id': aweme_ids,
                                 'desc': descs,
                                 'url_list':url_list})
        data = data._append(new_data, ignore_index=True)

        print(f"Fetched {len(aweme_ids)} videos for user {user_name} ({user_id}). Next max_cursor: {max_cursor}")

        if has_more != 1:
            break  # Exit the loop if has_more is not 1

        #time.sleep(1)

        time.sleep(random.uniform(2,8))

    if not data.empty:
        filename = f'douyin_videos_{user_name}.csv'
        data.to_csv(filename, index=False)
        print(f"Data for user {user_name} ({user_id}) saved to '{filename}'.")

print("All data saved.")
