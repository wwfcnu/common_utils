# common_utils

代码工具库，记录一下基础脚本

记录一下目前最新的环境
#!/bin/bash
# Copyright (c) 2024 Amphion.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

conda install ffmpeg -y
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia -y
pip install -r requirements.txt
pip install onnxruntime-gpu --extra-index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-12/pypi/simple/

librosa
numpy
tqdm
pydub
pyannote.audio
pandas
git+https://github.com/m-bain/whisperx.git # needs torch >= 2.0.0
（安装whisperx失败，采用开发者安装模式，另外安装onnxruntime-gpu报错，就删除所有onnxruntime相关的，重新装）
安装cudnn 8的版本
# 安装fuansr和modelscope
本地安装funasr
pip install modelscope[audio] -f https://modelscope.oss-cn-beijing.aliyuncs.com/releases/repo.html
