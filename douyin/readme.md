# douyin 基于用户名进行采集
>1. crawl.py 采集数据，引入retry库
>2. extract.py 提取视频中的音频
>3. x-b.js 验证x-bogus参数



## mstoken、xbogus

python douyin_download_tools.py --csv_path /home/wangweifei/repository/wair/spider/douyin/douyin_renminribao.csv  --output_dir /home/wangweifei/asr_datasets/douyin/renminribao/audio --cpu_num 1 --json_file True

# 参考库
https://github.com/xishandong/crawlProject
https://github.com/NearHuiwen/TiktokDouyinCrawler/issues
https://github.com/ShilongLee/Crawler

https://github.com/Evil0ctal/Douyin_TikTok_Download_API
https://github.com/HZhertz/ByteDance-a_bogus-parameter
/mnt/data1/AudioDataset/download/douyin/crawl/wushanchu_down1017.py 


## 下载情况20250730
https://github.com/JoeanAmier/TikTokDownloader/ 
3090,43 运行环境环境douyin，python=3.12
