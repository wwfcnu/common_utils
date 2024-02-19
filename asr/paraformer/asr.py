import concurrent.futures
#import soundfile
import os
import multiprocessing
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from modelscope.utils.logger import get_logger
import logging
from tqdm import tqdm
#import whisper
import torch
import numpy as np
from subprocess import CalledProcessError, run

SAMPLE_RATE = 16000
def load_audio(file: str, sr: int = SAMPLE_RATE):
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

    return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0


inference_pipeline = pipeline(
        task=Tasks.auto_speech_recognition,
        model='damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch',
        ngpu = 0)
# 
def get_data(user):
    wav_scp_path = {}
    with open(f"/mnt/data1/AudioDataset/wair/data/network/{user}/wav.scp") as f1:
        for line in f1:
             
            wav_id, wav_path = line.strip().split(" ", 1)
            file_path = os.path.join("/mnt/data1/AudioDataset/wair/process/network/", user, "result_test", wav_id + ".txt")
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                print(f"{file_path} already exists, skipping")
            else:
                wav_scp_path[wav_id] = wav_path


    data = {}
    with open(f'/mnt/data1/AudioDataset/wair/data/network/{user}/segments', 'r') as f:
        for line in f:
            line = line.strip().split() 
            keys =  data.keys()  
            # print(data)
            if line[1] in wav_scp_path:   
                if line[1] in data:
                    value = data.get(line[1])
                    value.append((line[1],line[0],line[2],line[3]))
                    data.update(
                        {
                            line[1]:value
                        }
                    )
                else:
                    data[line[1]] = [(line[1],line[0],line[2],line[3])]
            
    return data,wav_scp_path

def process_segment(audio_id,data,wav_scp_path):
    # 使用全局的 inference_pipeline
    #global inference_pipeline
    
    segments  = data.get(audio_id)

    audio_path = wav_scp_path.get(audio_id)

    # dirname = os.path.dirname(audio_path)
    # user = os.path.basename(dirname)

    
    output_dir = f"/mnt/data1/AudioDataset/wair/process/network/dialect_game_car_dy/result_test"
    # Construct the full file path using os.path.join
    file_path = os.path.join(output_dir, f"{audio_id}.txt")
    # Create the necessary directories if they don't exist
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    # ('YOU1000000044', 'YOU1000000044_S0001776', '8961.561', '8962.861')
    waveform = load_audio(audio_path)
    with open(file_path,"w") as w:
        for segment in tqdm(segments,total=len(segments),desc=f"processing file {audio_id}"):
            # print(segment[1],segment[0],segment[2])
            try:
                sample_rate = 16000
                beg_idx = float(segment[2]) * sample_rate
                end_idx = float(segment[3])* sample_rate
                wav_segment_id = segment[1]
                waveform_slice = waveform[int(beg_idx):int(end_idx)]
                #print(waveform_slice)
                result_segments = inference_pipeline(audio_in=waveform_slice)
                hypothesis = result_segments["text"]
                # print(wav_segment_id, hypothesis)
                #return (wav_segment_id, hypothesis)
                w.write(f"{wav_segment_id} {hypothesis}\n")
            except Exception as e:
                print(f"------------------报错信息-----------------{e}")
                continue

def main(user):
    data,wav_scp_path = get_data(user)
#     # with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
#     #      list(executor.map(process_segment, data.keys(),[data] * len(data), [wav_scp_path] * len(data)))
#     #multiprocessing.set_start_method('spawn')
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        #list(executor.map(process_segment, data.keys(),[data] * len(data), [wav_scp_path] * len(data)))
        list(tqdm(executor.map(process_segment, data.keys(),[data] * len(data), [wav_scp_path] * len(data))))

    

if __name__ == "__main__":
   

  
    user = 'dialect_game_car_dy'
    # 进一步不合并看一下
    # meishi修改vad.yaml为300000

    multiprocessing.set_start_method('spawn')
    #for user in users:
        # logger = get_logger(log_level=logging.CRITICAL)
        # logger.setLevel(logging.CRITICAL)
        
    main(user)

