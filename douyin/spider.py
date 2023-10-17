import requests
import execjs
import pandas as pd
import time
from fake_useragent import UserAgent
import random
import os
from urllib.parse import urlencode
ua = UserAgent()


def fetch_data(user_id, user_name, headers, cookies, params):
    max_retry = 20
    url = "https://www.douyin.com/aweme/v1/web/aweme/post/"
    for retry in range(max_retry + 1):
        try:
            response = requests.get(url, headers=headers, cookies=cookies, params=params)
            response.raise_for_status()  # Raise an exception for 4xx and 5xx errors
            response_json = response.json()  # Convert response to JSON
            return response_json
        except Exception as e:
            print(f"Error fetching data for user {user_name} ({user_id}): {e}")
            if retry < max_retry:
                print(f"Retrying... (Attempt {retry + 1}/{max_retry})")
                #time.sleep(2)
                time.sleep(random.uniform(2,8))
            else:
                print("Max retries reached. Skipping.")
                return None

def download_url(url,user_id,user_name,aweme_id,headers, cookies,params):
    max_retry = 5
    for retry in range(max_retry + 1):
        output_dir = "/obsfs/asr_datasets/network_datasets/douyin/video/news"
        os.makedirs(f"/obsfs/asr_datasets/network_datasets/douyin/video/news/{user_name}",exist_ok=True)
        video_path = os.path.join(output_dir,f"{user_name}/{aweme_id}.mp4")

        if os.path.exists(video_path):
            print(f"Skipped {user_name}: {url} (File already exists)")
        else:
            try:
                video = requests.get(url,  headers=headers, cookies=cookies, params=params).content
                
                with open(video_path, 'wb') as f:
                    f.write(video)
                    f.flush()
                    print(f"下载完成{user_name}: {aweme_id}")
            except Exception as e:
                print(f"Error Download data for user {user_name} ({user_id}): {e}")
                if retry < max_retry:
                    print(f"Retrying... (Attempt {retry + 1}/{max_retry})")
                    #time.sleep(2)
                    time.sleep(random.uniform(4,8))
                else:
                    print("Max retries reached. Skipping.")
                    return None




headers = {
    "authority": "www.douyin.com",
    "referer": "https://www.douyin.com/",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
    #"user-agent":ua.random
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
    "volume_info": "%7B%22isUserMute%22%3Afalse%2C%22isMute%22%3Atrue%2C%22volume%22%3A0.5%7D",
    "SEARCH_RESULT_LIST_TYPE": "%22single%22",
    "xgplayer_user_id": "558166833851",
    "_bd_ticket_crypt_doamin": "3",
    "__security_server_data_status": "1",
    "store-region": "cn-hb",
    "store-region-src": "uid",
    "my_rd": "2",
    "pwa2": "%220%7C0%7C3%7C1%22",
    "publish_badge_show_info": "%221%2C0%2C0%2C1695312182479%22",
    "FOLLOW_LIVE_POINT_INFO": "%22MS4wLjABAAAAGNle4U279CjTBB0o3_Zod9ViG_oba3OOWh7rQR36vOc%2F1695398400000%2F0%2F0%2F1695312921473%22",
    "FOLLOW_NUMBER_YELLOW_POINT_INFO": "%22MS4wLjABAAAAGNle4U279CjTBB0o3_Zod9ViG_oba3OOWh7rQR36vOc%2F1695398400000%2F0%2F1695312321474%2F0%22",
    "download_guide": "%223%2F20230921%2F1%22",
    "d_ticket": "79759c8784b9f2d954550149b9e5de701ef7a",
    "FORCE_LOGIN": "%7B%22videoConsumedRemainSeconds%22%3A180%2C%22isForcePopClose%22%3A1%7D",
    "n_mh": "9-mIeuD4wZnlYrrOvfzG3MuT6aQmCUtmr8FxV8Kl8xY",
    "passport_auth_status": "728d29f3a02ef67c7d559452134ba4ec%2C0c66e52363a396f40818ecb75474788f",
    "passport_auth_status_ss": "728d29f3a02ef67c7d559452134ba4ec%2C0c66e52363a396f40818ecb75474788f",
    "_bd_ticket_crypt_cookie": "6d2691e90050ca9fd72070ebd32d0d4f",
    "bd_ticket_guard_client_data": "eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCRnNkTW8yVmxuczQrNnJ2Qno1TDlUME10NmtXMEJMc2l0eGNKU251RmYwdFF0ZnExbFRRU216aHUzS1ZjQWR3Vm11MUJJeFRvSzZ4ckNZM2Q1OUI1cTg9IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoxfQ==",
    "LOGIN_STATUS": "0",
    "odin_tt": "a7edf80ba6ad465148b5b06e7c742a4a0f98fb3269ede7da152bab8a8068ad9d",
    "__ac_nonce": "0651384d900c325a287e3",
    "__ac_signature": "_02B4Z6wo00f01DvwoTAAAIDDa4flytXTMAQ70KWAAGv2fVh8UCx9U6B8NJxI5DyWZE2YOgEDlZPzqByj.fs02bsfwNOJIOxASV.qG4d99FHqOsDNxYhCXtx4gpdXa2z.y8yXth-JIhAUiNB4da",
    "strategyABtestKey": "%221695778010.997%22",
    "VIDEO_FILTER_MEMO_SELECT": "%7B%22expireTime%22%3A1696382811742%2C%22type%22%3A1%7D",
    "stream_recommend_feed_params": "%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1512%2C%5C%22screen_height%5C%22%3A982%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A8%2C%5C%22device_memory%5C%22%3A8%2C%5C%22downlink%5C%22%3A10%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A100%7D%22",
    "IsDouyinActive": "true",
    "home_can_add_dy_2_desktop": "%221%22",
    #"msToken": "11JXVDuAJccUnkLrllLAQxjPeK3XYLmE01esuX_xKV2ixA3n3SxRULHF3AUc-HD-NCaSdq60yYF7DKfmztSZC0h6qXH3PYECGvfef7k64urHPS3rZEz7AYaXUjhHP1oi",
    "tt_scid": "qCrE23UNJd37YYxmCUgX6uRF-KLin3ff3lIZUkeVFJ1qiFCiJs88XcWbNJORTwlq40f0"
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
