import os
import sys
def generate_wav_scp(directory):
    wav_scp_content = ""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".m4a"):
                wav_path = os.path.join(root, file)
                utt_id = os.path.splitext(file)[0]
                wav_scp_content += f"{utt_id}\t{wav_path}\n"

    return wav_scp_content

def save_wav_scp(wav_scp_content, output_file):
    with open(output_file, "w") as file:
        file.write(wav_scp_content)

if __name__ == "__main__":
    # 设置包含 WAV 文件的目录
    input_directory = sys.argv[1]  #"/mnt/data1/AudioDataset/lm/data/wuhanjinying/audio"
   
    # 生成 WAV.scp 内容
    wav_scp_content = generate_wav_scp(input_directory)

    # 设置输出文件路径
    output_file = sys.argv[2]   #"/mnt/data1/AudioDataset/lm/data/wuhanjinying/wav.scp"

    # 将 WAV.scp 内容保存到文件
    save_wav_scp(wav_scp_content, output_file)

    print(f"{output_file} 文件已生成。")
