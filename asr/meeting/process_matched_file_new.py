def is_interval_inclusive(a_start, a_end, b_start, b_end):
    """
    判断区间 [a_start, a_end] 是否被 [b_start, b_end] 包含，或者相反。
    """
    return (b_start <= a_start and b_end >= a_end) or (a_start <= b_start and a_end >= b_end)


def check_intervals(a_list, b_list, delta):
    # 对 a_list 和 b_list 按 start 进行排序
    a_list_sorted = sorted(a_list, key=lambda x: x['start'])
    b_list_sorted = sorted(b_list, key=lambda x: x['start'])

    length_a = len(a_list_sorted)
    length_b = len(b_list_sorted)

    # 如果长度不相等，直接返回 0，因为 acc 只有在长度相等时才有意义
    if length_a != length_b:
        return 0

    num = 0

    # 当 a_list 和 b_list 长度相同时进行比较
    for i in range(length_a):
        a_start, a_end = a_list_sorted[i]['start'], a_list_sorted[i]['end']
        b_start, b_end = b_list_sorted[i]['start'], b_list_sorted[i]['end']
        
        if is_interval_inclusive(a_start, a_end, b_start, b_end):
            num += 1
        else:
            # 定义所有可能的调整后的区间
            adjustments = [
                (b_start - delta, b_end),
                (b_start - delta, b_end + delta),
                (b_start - delta, b_end - delta),
                (b_start + delta, b_end),
                (b_start + delta, b_end + delta),
                # 添加有效性检查
                (b_start + delta, b_end - delta) if b_start + delta <= b_end - delta else None,
                (b_start, b_end + delta),
                (b_start, b_end - delta)
            ]
            # 过滤掉无效的区间
            adjustments = [adj for adj in adjustments if adj is not None and adj[0] <= adj[1]]
            
            for b_start_adj, b_end_adj in adjustments:
                if is_interval_inclusive(a_start, a_end, b_start_adj, b_end_adj):
                    num += 1
                    break  # 只要找到一个满足的调整就可以跳出循环
    
    # 计算 acc 作为 num 和 length_a 的比例
    acc = num / length_a
    return acc

# 示例列表和阈值
a = [{"start": 5, "end": 10}, {"start": 20, "end": 25}]
b = [{"start": 4, "end": 12}, {"start": 15, "end": 22}]
delta = 2

# 进行检查
acc_value = check_intervals(a, b, delta)
print(f"Acc 值: {acc_value}")
