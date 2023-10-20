from concurrent.futures import ProcessPoolExecutor
import argparse
import os
from tqdm import tqdm
os.environ['CUDA_VISIBLE_DEVICES']="7"
import torch.cuda
import multiprocessing

import llama
from util.misc import *
from data.utils import load_and_transform_audio_data


parser = argparse.ArgumentParser()
parser.add_argument(
    "--model", default="./ckpts/checkpoint.pth", type=str,
    help="Name of or path to the trained checkpoint",
)
parser.add_argument(
    "--llama_type", default="7B", type=str,
    help="Type of llama original weight",
)
parser.add_argument(
    "--llama_dir", default="./ckpts/LLaMA", type=str,
    help="Path to LLaMA pretrained checkpoint",
)
parser.add_argument(
    "--mert_path", default="./ckpts/MERT-v1-330M", type=str,
    help="Path to MERT pretrained checkpoint",
)
parser.add_argument(
    "--knn_dir", default="./ckpts", type=str,
    help="Path to directory with KNN Index",
)

# parser.add_argument(
#     "--audio_path", required=True, type=str,
#     help="Path to the input music file",
# )
parser.add_argument(
    "--question", default="Describe the music in detail", type=str,
    help="Question to ask the model",
)

args = parser.parse_args()
# 加载模型
model = llama.load(args.model, args.llama_dir, mert_path=args.mert_path, knn=True, knn_dir=args.knn_dir, llama_type=args.llama_type)
model.eval()

def multimodal_generate(
        audio_path,
        audio_weight,
        prompt,
        cache_size,
        cache_t,
        cache_weight,
        max_gen_len,
        gen_t, top_p
):
    inputs = {}
    audio = load_and_transform_audio_data([audio_path])
    inputs['Audio'] = [audio, audio_weight]
    image_prompt = prompt
    text_output = None
    prompts = [llama.format_prompt(prompt)]
    prompts = [model.tokenizer.encode(x, bos=True, eos=False) for x in prompts]
    with torch.cuda.amp.autocast():
        results = model.generate(inputs, prompts, max_gen_len=max_gen_len, temperature=gen_t, top_p=top_p,
                                     cache_size=cache_size, cache_t=cache_t, cache_weight=cache_weight)
    text_output = results[0].strip()
    return text_output


# 
def get_data(dataset):
    wav_scp_path = {}
    with open(f"{dataset}/wav.scp") as f1:
        for line in f1:
            wav_id, wav_path = line.strip().split(" ", 1)
            wav_scp_path[wav_id] = wav_path

            
    return wav_scp_path

# def process_music(audio_id,wav_scp_path):
  
#     audio_path = wav_scp_path.get(audio_id)
#     # dirname = os.path.dirname(audio_path)
#     # dataset = os.path.basename(dirname)

    
#     output_dir = f"/home/wangweifei/repository/wair/MU-LLaMA/MU-LLaMA/pond5/output"
#     # Construct the full file path using os.path.join
#     file_path = os.path.join(output_dir, f"{audio_id}.txt")
#     # Create the necessary directories if they don't exist
#     os.makedirs(os.path.dirname(file_path), exist_ok=True)
   

#     with open(file_path,"w") as w:   
#             try:
#                 result =  multimodal_generate(audio_path, 1, args.question, 100, 20.0, 0.0, 512, 0.6, 0.8)
#                 answer = result["text"]               
#                 w.write(f"{audio_id} {answer}\n")
#             except Exception as e:
#                 print(e)
#                 return (None,None)

# def main(dataset):
#     wav_scp_path = get_data(dataset)
#     audio_ids = list(wav_scp_path.keys())

#     with tqdm(total=len(audio_ids), desc="Music QA", dynamic_ncols=True) as pbar:
#         with ProcessPoolExecutor(max_workers=2) as executor:
#             for audio_id in audio_ids:
#                 result = executor.submit(process_music,audio_id, wav_scp_path)

#                 pbar.update(1)  # 更新进度条

# if __name__ == "__main__":
 
#     multiprocessing.set_start_method('spawn')
#     dataset = "/home/wangweifei/repository/wair/MU-LLaMA/MU-LLaMA/pond5"
#     # Define the question prompt
#     #args.question = "Describe the Audio"
#     main(dataset)

def process_music(audio_id, wav_scp_path, results):
    audio_path = wav_scp_path.get(audio_id)
    try:
        answer = multimodal_generate(audio_path, 1, args.question, 100, 20.0, 0.0, 512, 0.6, 0.8)
        
        results.append(f"{audio_id} {answer}\n")
    except Exception as e:
        print(e)

def main(dataset):
    wav_scp_path = get_data(dataset)
    audio_ids = list(wav_scp_path.keys())
    result_list = []  # List to store results

    # with tqdm(total=len(audio_ids), desc="Music QA", dynamic_ncols=True) as pbar:
    #     with ProcessPoolExecutor(max_workers=2) as executor:
    #         for audio_id in audio_ids:
    #             executor.submit(process_music, model,audio_id, wav_scp_path, result_list)
    #             pbar.update(1)  # Update progress bar
    for audio_id in tqdm(audio_ids):
        process_music(audio_id,wav_scp_path, result_list)
    # Write all the results to a single file
    output_dir = "/home/wangweifei/repository/wair/MU-LLaMA/MU-LLaMA/pond5"
    output_file_path = os.path.join(output_dir, "results.txt")
    with open(output_file_path, "w") as output_file:
        for result in result_list:
            output_file.write(result)

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')
    dataset = "/home/wangweifei/repository/wair/MU-LLaMA/MU-LLaMA/pond5"

   

    main(dataset)
