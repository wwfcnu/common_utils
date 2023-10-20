import argparse
import os
os.environ['CUDA_VISIBLE_DEVICES']="6"
import torch
from util.misc import *
import llama
from data.utils import load_and_transform_audio_data
from fastapi import FastAPI, Form
from pydantic import BaseModel

app = FastAPI()
parser = argparse.ArgumentParser()
parser.add_argument("--model", default="./ckpts/checkpoint.pth", type=str, help="Name of or path to the trained checkpoint")
parser.add_argument("--llama_type", default="7B", type=str, help="Type of llama original weight")
parser.add_argument("--llama_dir", default="./ckpts/LLaMA", type=str, help="Path to LLaMA pretrained checkpoint")
parser.add_argument("--mert_path", default="./ckpts/MERT-v1-330M", type=str, help="Path to MERT pretrained checkpoint")
parser.add_argument("--knn_dir", default="./ckpts", type=str, help="Path to directory with KNN Index")
args = parser.parse_args()


model = llama.load(args.model, args.llama_dir, mert_path=args.mert_path, knn=True, knn_dir=args.knn_dir, llama_type=args.llama_type)
model.eval()

# Define a function for generating text from audio and a question
def multimodal_generate(audio_path, audio_weight, prompt, cache_size, cache_t, cache_weight, max_gen_len, gen_t, top_p):
    
    
    inputs = {}
    audio = load_and_transform_audio_data([audio_path])
    inputs['Audio'] = [audio, audio_weight]
    text_output = None
    prompts = [llama.format_prompt(prompt)]
    prompts = [model.tokenizer.encode(x, bos=True, eos=False) for x in prompts]
    with torch.cuda.amp.autocast():
        results = model.generate(inputs, prompts, max_gen_len=max_gen_len, temperature=gen_t, top_p=top_p, cache_size=cache_size, cache_t=cache_t, cache_weight=cache_weight)
    text_output = results[0].strip()
    return text_output


class info(BaseModel):
    audio_path:str
    question:str
# Define a route for generating text
@app.post('/generate_text')
async def generate_text(rev_data:info):
    audio_path = rev_data.audio_path
    question = rev_data.question
    try:
        text_output = multimodal_generate(audio_path, 1, question, 100, 20.0, 0.0, 512, 0.6, 0.8)
        return {"result": text_output}
    except Exception as e:
        return {"error": str(e)}

if __name__ == '__main__':
  
    import uvicorn
    uvicorn.run(app="llama_music_api:app", host="0.0.0.0", port=18200)#reload=True
