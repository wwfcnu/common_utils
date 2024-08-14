# 对match后的文件进行处理，生成matched的ref和hyp; 然后计算每一条的speaker的识别正确率



def is_interval_inclusive(a_start, a_end, b_start, b_end):
    """
    判断区间 [a_start, a_end] 是否被 [b_start, b_end] 包含，或者相反。
    """
    return (b_start <= a_start and b_end >= a_end) or (a_start <= b_start and a_end >= b_end)

def check_intervals(a_list, b_list, delta):
    num = 0 
    length_a = len(a_list)
    length_b = len(b_list)
    if length_a != length_b:
        acc = 0
    else:
        # 首先检查未调整的区间
        for a in a_list:
            a_start, a_end = a['start'], a['end']
            for b in b_list:
                b_start, b_end = b['start'], b['end']
                if is_interval_inclusive(a_start, a_end, b_start, b_end):
                    num += 1
                else:
                    # 如果未调整区间不满足条件，检查调整后的区间
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
        acc = num //length_a
    return acc

# 问题：
不能循环对比，而是对a，b先按照start排序；排序之后
比较a，b的第一个区间，

