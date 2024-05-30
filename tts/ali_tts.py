import http.client
import urllib.parse
import json
import os
import time
import logging
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from tqdm import tqdm
import codecs
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
APP_KEY = ""
ACCESS_KEY_ID = ""
ACCESS_KEY_SECRET = ""
AUDIO_SAVE_DIR = "/mnt/lustre/wangweifei/tuwenyin/"
MAX_WORKERS = 2

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AliTTS:
    def __init__(self, app_key, access_key_id, access_key_secret):
        self.appKey = app_key
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.host = 'nls-gateway-cn-shanghai.aliyuncs.com'
        self.token = None
        self.expireTime = 0

    def get_token(self):
        client = AcsClient(self.access_key_id, self.access_key_secret, "cn-shanghai")
        request = CommonRequest()
        request.set_method('POST')
        request.set_domain('nls-meta.cn-shanghai.aliyuncs.com')
        request.set_version('2019-02-28')
        request.set_action_name('CreateToken')

        try:
            response = client.do_action_with_exception(request)
            response_json = json.loads(response)
            if 'Token' in response_json and 'Id' in response_json['Token']:
                self.token = response_json['Token']['Id']
                self.expireTime = response_json['Token']['ExpireTime']
                logging.info(f"Token obtained: {self.token}, expires at {self.expireTime}")
        except Exception as e:
            logging.error(f"Failed to get token: {e}")

    def process_get_request(self, text, audio_save_file, format='mp3', sample_rate=16000):
        if time.time() >= self.expireTime:
            self.get_token()

        url = f"https://{self.host}/stream/v1/tts?appkey={self.appKey}&token={self.token}&text={text}&format={format}&sample_rate={sample_rate}"
        conn = http.client.HTTPSConnection(self.host)

        try:
            conn.request('GET', url)
            response = conn.getresponse()
            content_type = response.getheader('Content-Type')
            body = response.read()
            if content_type == 'audio/mpeg':
                with open(audio_save_file, 'wb') as f:
                    f.write(body)
                #logging.info(f"Audio saved to {audio_save_file}")
            else:
                logging.error(f"Failed to get audio: {body}")
        except Exception as e:
            logging.error(f"Error in process_get_request: {e}")
        finally:
            conn.close()

def text_to_speech(temp, tts):
    temp = temp.strip()
    if len(temp.split("\t")) == 2:
        key, text = temp.split("\t", maxsplit=1)
        text_urlencode = urllib.parse.quote_plus(text).replace("+", "%20").replace("*", "%2A").replace("%7E", "~")
        audio_save_file = os.path.join(AUDIO_SAVE_DIR, key.replace(".jpg", ".mp3"))
        tts.process_get_request(text_urlencode, audio_save_file)
    else:
        logging.warning(f"Invalid line: {temp}")

def get_data(wav_scp):
    with codecs.open(wav_scp, 'r', 'utf8') as source_info_list:
        unprocess_list = [
            line for line in source_info_list
            if not (os.path.exists(audio_path := os.path.join(AUDIO_SAVE_DIR, line.split("\t")[0].replace(".jpg", ".mp3"))) and os.path.getsize(audio_path) > 0)
        ]
    return unprocess_list

def main(wav_scp):
    unprocess_list = get_data(wav_scp)
    logging.info(f"Number of unprocessed texts: {len(unprocess_list)}")

    tts = AliTTS(APP_KEY, ACCESS_KEY_ID, ACCESS_KEY_SECRET)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(text_to_speech, temp, tts) for temp in tqdm(unprocess_list)]
        for _ in tqdm(as_completed(futures), total=len(futures), desc="Processing"):
            pass

if __name__ == '__main__':
    wav_scp = "/home/wangweifei/repository/wair/tts_project/zh_image_question.txt"
    main(wav_scp)
