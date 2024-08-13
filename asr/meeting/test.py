import json
# ref的结果文件和hyp的结果文件
# 首先构建代码逻辑：寻找两个序列的重叠部分。
# hyp的文件内容：
# {"text": "目前是联通这边", "speaker": [{"id": "0", "name": "", "start": 337200, "end": 459870}, {"id": "2", "name": "", "start": 460130, "end": 493600}], "global_start": 456980, "global_end": 460830}

# ref的文件内容：
# {"text": "对然后以训训推集成大月份训推集成开源大模型的一个", "start": 221960.0, "end": 227370.0, "speaker": [{"start": 221960.0, "end": 222428.7004608295, "id": "sp1"}, {"start": 222722.88479262672, "end": 227210.44239631336, "id": "sp1"}, {"start": 222458.61751152074, "end": 222725.37788018433, "id": "sp2"}]}


# def merge_intervals(a, b):
#     result = []
#     i = 0
#     j = 0
#     len_a = len(a)
#     len_b = len(b)
    
#     while j < len_b and i < len_a:
#         global_start, global_end = b[j]
#         global_length = global_end - global_start
        
#         merged_start = a[i][0]
#         merged_end = a[i][1]
#         merged_length = merged_end - merged_start
        
#         i += 1
        
#         while merged_length < global_length and i < len_a:
#             merged_end = a[i][1]
#             merged_length = merged_end - merged_start
#             i += 1
        
#         result.append([merged_start, merged_end])
#         j += 1
#     print(result)
#     return result

# def match_intervals(ref_intervals, hyp_intervals):
#     matches = []
#     i, j = 0, 0

#     while i < len(ref_intervals) and j < len(hyp_intervals):
#         ref_start, ref_end = ref_intervals[i]
#         hyp_start, hyp_end = hyp_intervals[j]

#         # 检查是否有重叠
#         if ref_end >= hyp_start and hyp_end >= ref_start:
#             matches.append((ref_intervals[i], hyp_intervals[j]))

#         # 处理多重重叠情况
#         if ref_end < hyp_end:
#             i += 1  # 移动到下一个 ref_interval
#         elif hyp_end < ref_end:
#             j += 1  # 移动到下一个 hyp_interval
#         else:
#             # 当 ref_interval 和 hyp_interval 的结束时间相同时，移动两个指针
#             i += 1
#             j += 1

#     return matches

def get_ref_interval(file):
    intervals = []
    with open(file)as f:
        for line in f:
            line = line.strip()
            line_ = json.loads(line)
            start = line_['start']
            end = line_['end']
            interval = [start,end]
            # 这个intervals里的interval按照start进行排序的
            intervals.append(interval)
        
            # Sort the intervals by the start time
    intervals = sorted(intervals, key=lambda x: x[0])
    
    return intervals

def get_hyp_interval(file):
    intervals = []
    with open(file)as f:
        for line in f:
            line = line.strip()
            line_ = json.loads(line)
            start = line_['global_start']
            end = line_['global_end']
            interval = [start,end]
            # 这个intervals里的interval按照start进行排序的
            intervals.append(interval)
        
            # Sort the intervals by the start time
    intervals = sorted(intervals, key=lambda x: x[0])
    
    return intervals


def match_intervals(ref_intervals, hyp_intervals):
    result = []
    i, j = 0, 0

    while i < len(ref_intervals) and j < len(hyp_intervals):
        current_ref_group = [ref_intervals[i]]
        current_hyp_group = [hyp_intervals[j]]
        
        ref_end = ref_intervals[i][1]
        hyp_end = hyp_intervals[j][1]
        
        while (i + 1 < len(ref_intervals) and hyp_end >= ref_intervals[i + 1][0]) or (j + 1 < len(hyp_intervals) and ref_end >= hyp_intervals[j + 1][0]):
            if i + 1 < len(ref_intervals) and hyp_end >= ref_intervals[i + 1][0]:
                i += 1
                current_ref_group.append(ref_intervals[i])
                ref_end = ref_intervals[i][1]
            
            if j + 1 < len(hyp_intervals) and ref_end >= hyp_intervals[j + 1][0]:
                j += 1
                current_hyp_group.append(hyp_intervals[j])
                hyp_end = hyp_intervals[j][1]
        
        result.append((current_ref_group, current_hyp_group))
        i += 1
        j += 1
    
    return result

def print_matched_intervals(result):
    for ref_group, hyp_group in result:
        ref_str = ', '.join([f"[{ref[0]}, {ref[1]}]" for ref in ref_group])
        hyp_str = ', '.join([f"[{hyp[0]}, {hyp[1]}]" for hyp in hyp_group])
        print(f"Ref: {ref_str} -> Hyp: {hyp_str}")


def main(filename):
    ref_file = f"/home/wangweifei/repository/wair/baseline_test_datasets/data/meeting_datasets/wav_scp/ref/{filename}.txt"
    hyp_file = f"/home/wangweifei/repository/wair/baseline_test_datasets/data/meeting_datasets/result_new/1s/{filename}.txt"
    ref_intervals = get_ref_interval(ref_file)
    hyp_intervals = get_hyp_interval(hyp_file)

    # matched_intervals = match_intervals(ref_intervals, hyp_intervals)
    # print(len(matched_intervals))
    # for ref, hyp in matched_intervals:
    #     print(f"Ref interval: {ref}, Hyp interval: {hyp}")
    #     break

    # 示例使用
    # ref_intervals = [[0, 11080.0], [12080.0, 14920.0], [15920.0, 22670.0], [23670.0, 26170.0], [27170.0, 30580.0], [31580.0, 33650.0], [34650.0, 36190.0], [37190.0, 42209.99999999999], [43209.99999999999, 72530.0]]
    # hyp_intervals = [[0, 11850], [11870, 16040], [16060, 26630], [26650, 45220], [45240, 65410], [65430, 73440], [73460, 77630]]

    matched_result = match_intervals(ref_intervals, hyp_intervals)
    print(len(matched_result))


if __name__=="__main__":
    datasets = [
        "2024-03-11(2号会议室)",
        "2024-04-22(2号会议室)",
        "2024-05-20(2号会议室)",
        "2024-5-29(商务会议室1)",
        "2024-05-29(商务会议室2)",
        "2024-06-17(2号会议室)",
        "2024-6-18(商务会议室3)",
        "2024-06-19(mac麦克风)",
        "培训室腾讯会议(常万里RAG)",
        "培训室腾讯会议录音(徐志祥)"
    ]
    for dataset in datasets:
        print(f"processing ---------{dataset}-----------")
        main(dataset)
