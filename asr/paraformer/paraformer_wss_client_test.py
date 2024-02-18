# -*- encoding: utf-8 -*-
import os
import time
import websockets, ssl
import asyncio
# import threading
import argparse
import json
import traceback
from multiprocessing import Process
# from funasr.fileio.datadir_writer import DatadirWriter
import ffmpeg
import numpy as np
from subprocess import CalledProcessError, run


def load_audio(file: str, sr: int):
        """
        Open an audio file and read as mono waveform, resampling as necessary
        Parameters
        ----------
        file: str
            The audio file to open

        sr: int
            The sample rate to resample the audio if necessary

        Returns
        -------
        A NumPy array containing the audio waveform, in float32 dtype.
        """

        # This launches a subprocess to decode audio while down-mixing
        # and resampling as necessary.  Requires the ffmpeg CLI in PATH.
        # fmt: off
        cmd = [
            "ffmpeg",
            "-nostdin",
            "-threads", "0",
            "-i", file,
            "-f", "s16le",
            "-ac", "1",
            "-acodec", "pcm_s16le",
            "-ar", str(sr),
            "-"
        ]
        # fmt: on
        try:
            out = run(cmd, capture_output=True, check=True).stdout
        except CalledProcessError as e:
            raise RuntimeError(f"Failed to load audio: {e.stderr.decode()}") from e

        # return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0
        return out




import logging

logging.basicConfig(level=logging.ERROR)

parser = argparse.ArgumentParser()
parser.add_argument("--host",
                    type=str,
                    default="localhost",
                    required=False,
                    help="host ip, localhost, 0.0.0.0")
parser.add_argument("--port",
                    type=int,
                    default=10095,
                    required=False,
                    help="grpc server port")
parser.add_argument("--chunk_size",
                    type=str,
                    default="5, 10, 5",
                    help="chunk")
parser.add_argument("--chunk_interval",
                    type=int,
                    default=10,
                    help="chunk")
parser.add_argument("--hotword",
                    type=str,
                    default="",
                    help="hotword file path, one hotword perline (e.g.:阿里巴巴 20)")
parser.add_argument("--audio_in",
                    type=str,
                    default=None,
                    help="audio_in")
parser.add_argument("--audio_fs",
                    type=int,
                    default=16000,
                    help="audio_fs")
parser.add_argument("--send_without_sleep",
                    action="store_true",
                    default=True,
                    help="if audio_in is set, send_without_sleep")
parser.add_argument("--thread_num",
                    type=int,
                    default=1,
                    help="thread_num")
parser.add_argument("--words_max_print",
                    type=int,
                    default=10000,
                    help="chunk")
parser.add_argument("--output_dir",
                    type=str,
                    default=None,
                    help="output_dir")
parser.add_argument("--ssl",
                    type=int,
                    default=1,
                    help="1 for ssl connect, 0 for no ssl")
parser.add_argument("--use_itn",
                    type=int,
                    default=1,
                    help="1 for using itn, 0 for not itn")
parser.add_argument("--mode",
                    type=str,
                    default="2pass",
                    help="offline, online, 2pass")

args = parser.parse_args()
args.chunk_size = [int(x) for x in args.chunk_size.split(",")]
print(args)
# voices = asyncio.Queue()


from queue import Queue

voices = Queue()
offline_msg_done=False

if args.output_dir is not None:
    # if os.path.exists(args.output_dir):
    #     os.remove(args.output_dir)
        
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)


async def record_microphone():
    is_finished = False
    import pyaudio
    # print("2")
    global voices
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    chunk_size = 60 * args.chunk_size[1] / args.chunk_interval
    CHUNK = int(RATE / 1000 * chunk_size)

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    # hotwords
    fst_dict = {}
    hotword_msg = ""
    if args.hotword.strip() != "":
        f_scp = open(args.hotword)
        hot_lines = f_scp.readlines()
        for line in hot_lines:
            words = line.strip().split(" ")
            if len(words) < 2:
                print("Please checkout format of hotwords")
                continue
            try:
                fst_dict[" ".join(words[:-1])] = int(words[-1])
            except ValueError:
                print("Please checkout format of hotwords")
        hotword_msg=json.dumps(fst_dict)

    use_itn=True
    if args.use_itn == 0:
        use_itn=False
    
    message = json.dumps({"mode": args.mode, "chunk_size": args.chunk_size, "chunk_interval": args.chunk_interval,
                          "wav_name": "microphone", "is_speaking": True, "hotwords":hotword_msg, "itn": use_itn})
    #voices.put(message)
    await websocket.send(message)
    while True:
        data = stream.read(CHUNK)
        message = data
        #voices.put(message)
        await websocket.send(message)
        await asyncio.sleep(0.005)

async def record_from_segment(wav_path,timestamp):
    # hotwords
    fst_dict = {}
    hotword_msg = ""
    if args.hotword.strip() != "":
        f_scp = open(args.hotword)
        hot_lines = f_scp.readlines()
        for line in hot_lines:
            words = line.strip().split(" ")
            if len(words) < 2:
                print("Please checkout format of hotwords")
                continue
            try:
                fst_dict[" ".join(words[:-1])] = int(words[-1])
            except ValueError:
                print("Please checkout format of hotwords")
        hotword_msg=json.dumps(fst_dict)
        print (hotword_msg)

    sample_rate = args.audio_fs
    wav_format = "pcm"
    use_itn=True
    if args.use_itn == 0:
        use_itn=False

    raw_data = load_audio(wav_path, sample_rate)
    stride = int(60 * args.chunk_size[1] / args.chunk_interval / 1000 * sample_rate * 2)
    segment_result = []

    wav_name = timestamp.split()[0]
    start_byte = int(float(timestamp.split()[1]) * sample_rate *2)
    end_byte = int(float(timestamp.split()[2]) * sample_rate *2)
   
    audio_bytes = raw_data[start_byte:end_byte]
    chunk_num = (len(audio_bytes) - 1) // stride + 1
    if args.ssl == 1:
        ssl_context = ssl.SSLContext()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        uri = "wss://{}:{}".format(args.host, args.port)
    else:
        uri = "ws://{}:{}".format(args.host, args.port)
        ssl_context = None
    print("connect to", uri)
    message = json.dumps({"mode": args.mode, "chunk_size": args.chunk_size, "chunk_interval": args.chunk_interval, "audio_fs":sample_rate,
                    "wav_name": wav_name, "wav_format": wav_format, "is_speaking": True, "hotwords":hotword_msg, "itn": use_itn})
        
    async with websockets.connect(uri, subprotocols=["binary"], ping_interval=None, ssl=ssl_context) as websocket:
        await websocket.send(message)
        is_speaking = True
        for i in range(chunk_num):
            beg = i * stride
            data = audio_bytes[beg:beg + stride]
            message = data
            #voices.put(message)
            await websocket.send(message)
            if i == chunk_num - 1:
                is_speaking = False
                message = json.dumps({"is_speaking": is_speaking})
                #voices.put(message)
                await websocket.send(message)

            sleep_duration = 0.001 if args.mode == "offline" else 60 * args.chunk_size[1] / args.chunk_interval / 1000
            
            await asyncio.sleep(sleep_duration)
        
       
        if not args.mode=="offline":
            await asyncio.sleep(2)
        
        if args.mode=="offline":
            try:
                while True:
                    # await asyncio.sleep(1)
                    meg = await websocket.recv()
                    meg = json.loads(meg)

                    if 'mode' not in meg:
                        continue
                    else:
                    
                        wav_name = meg.get("wav_name")
                        text = meg["text"]
                        

                        mode_type = meg.get("mode", "")
                    
                        offline_msg_done = meg.get("is_final", False)
                        print(f"meg:{meg}")
                    
                        text_write_line = "{}\t{}\n".format(wav_name,text)
                
                        print(f"result:{text_write_line}")
                        segment_result.append(text_write_line)
                        break

            except Exception as e:
                print("Exception:", e)
        await websocket.close()


    return segment_result


async def record_from_scp(chunk_begin, chunk_size):
    is_finished = False
    if args.audio_in.endswith(".scp"):
        f_scp = open(args.audio_in)
        wavs = f_scp.readlines()
    # data.list
    elif args.audio_in.endswith(".list"):
        f_list = open(args.audio_in)
        wavs = f_list.readlines()

    else:
        wavs = [args.audio_in]

     
    if chunk_size > 0:
        wavs = wavs[chunk_begin:chunk_begin + chunk_size]

    final_result = []
    for wav in wavs:
        wav_splits = wav.strip().split('\t')
        wav_path = wav_splits[0]
        #wav_timestamps = wav_splits[1].split('|')
        if '|' in wav_splits[1]:
            wav_timestamps = wav_splits[1].strip().split('|')
        else:
            wav_timestamps = [wav_splits[1]]

        if not len(wav_path.strip())>0:
           continue
     
      
        # send first time
        for timestamp in wav_timestamps:
            task = asyncio.create_task(record_from_segment(wav_path,timestamp))

            seg_result = await task
            final_result.append(seg_result)
    return final_result
          
async def ws_client(id, chunk_begin, chunk_size):
  if args.audio_in is None:
       chunk_begin=0
       chunk_size=1
  
  # ibest_writer = open(os.path.join(args.output_dir, "text.{}".format(id)), "a+", encoding="utf-8")
  with open(os.path.join(args.output_dir, "text.{}".format(id)), "a",encoding="utf-8")as ibest_writer :
    for i in range(chunk_begin,chunk_begin+chunk_size):
        if args.audio_in is not None:
            task = asyncio.create_task(record_from_scp(i, 1))
            
        results = await task
        
        
        #with open(os.path.join(args.output_dir, "text.{}".format(id)), "a+")as w:
        for result in results:
            for final in result:        
                ibest_writer.write(final)
                ibest_writer.flush()

  

        
  exit(0)
    

def one_thread(id, chunk_begin, chunk_size):
    asyncio.get_event_loop().run_until_complete(ws_client(id, chunk_begin, chunk_size))
    asyncio.get_event_loop().run_forever()

if __name__ == '__main__':
    # for microphone
    if args.audio_in is None:
        p = Process(target=one_thread, args=(0, 0, 0))
        p.start()
        p.join()
        print('end')
    else:
        # calculate the number of wavs for each preocess
        if args.audio_in.endswith(".scp"):
            f_scp = open(args.audio_in)
            wavs = f_scp.readlines()
            # data.list
        elif args.audio_in.endswith(".list"):
            f_list = open(args.audio_in)
            wavs = f_list.readlines()
        else:
            wavs = [args.audio_in]
      
        total_len = len(wavs)
        print(f"total_len-----------{total_len}")
        if total_len >= args.thread_num:
            chunk_size = int(total_len / args.thread_num)
            remain_wavs = total_len - chunk_size * args.thread_num
        else:
            chunk_size = 1
            remain_wavs = 0

        process_list = []
        chunk_begin = 0
        for i in range(args.thread_num):
            now_chunk_size = chunk_size
            if remain_wavs > 0:
                now_chunk_size = chunk_size + 1
                remain_wavs = remain_wavs - 1
            # process i handle wavs at chunk_begin and size of now_chunk_size
            p = Process(target=one_thread, args=(i, chunk_begin, now_chunk_size))
            chunk_begin = chunk_begin + now_chunk_size
            p.start()
            process_list.append(p)

        for i in process_list:
            p.join()

        print('end')
