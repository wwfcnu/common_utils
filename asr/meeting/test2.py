def match_intervals_with_text(ref_intervals, ref_texts, hyp_intervals, hyp_texts):
    result = []
    i, j = 0, 0

    while i < len(ref_intervals) and j < len(hyp_intervals):
        current_ref_group = [ref_intervals[i]]
        current_hyp_group = [hyp_intervals[j]]
        
        current_ref_texts = [ref_texts[i]]
        current_hyp_texts = [hyp_texts[j]]
        
        ref_end = ref_intervals[i][1]
        hyp_end = hyp_intervals[j][1]
        
        while (i + 1 < len(ref_intervals) and hyp_end >= ref_intervals[i + 1][0]) or (j + 1 < len(hyp_intervals) and ref_end >= hyp_intervals[j + 1][0]):
            if i + 1 < len(ref_intervals) and hyp_end >= ref_intervals[i + 1][0]:
                i += 1
                current_ref_group.append(ref_intervals[i])
                current_ref_texts.append(ref_texts[i])
                ref_end = ref_intervals[i][1]
            
            if j + 1 < len(hyp_intervals) and ref_end >= hyp_intervals[j + 1][0]:
                j += 1
                current_hyp_group.append(hyp_intervals[j])
                current_hyp_texts.append(hyp_texts[j])
                hyp_end = hyp_intervals[j][1]
        
        result.append((current_ref_group, current_hyp_group, current_ref_texts, current_hyp_texts))
        i += 1
        j += 1
    
    return result

def print_matched_intervals_with_text(result):
    for ref_group, hyp_group, ref_texts, hyp_texts in result:
        ref_str = ', '.join([f"[{ref[0]}, {ref[1]}]" for ref in ref_group])
        hyp_str = ', '.join([f"[{hyp[0]}, {hyp[1]}]" for hyp in hyp_group])
        
        merged_ref_text = ' '.join(ref_texts)
        merged_hyp_text = ' '.join(hyp_texts)
        
        print(f"Ref: {ref_str} -> Hyp: {hyp_str}")
        print(f"Ref Text: {merged_ref_text}")
        print(f"Hyp Text: {merged_hyp_text}")
        print()

# 示例数据
ref_intervals = [[0, 11080.0], [12080.0, 14920.0], [15920.0, 22670.0], [23670.0, 26170.0], [27170.0, 30580.0], [31580.0, 33650.0], [34650.0, 36190.0], [37190.0, 42209.99999999999], [43209.99999999999, 72530.0]]
ref_texts = ["Text1", "Text2", "Text3", "Text4", "Text5", "Text6", "Text7", "Text8", "Text9"]

hyp_intervals = [[0, 11850], [11870, 16040], [16060, 26630], [26650, 45220], [45240, 65410], [65430, 73440], [73460, 77630]]
hyp_texts = ["HText1", "HText2", "HText3", "HText4", "HText5", "HText6", "HText7"]

matched_result_with_text = match_intervals_with_text(ref_intervals, ref_texts, hyp_intervals, hyp_texts)
print_matched_intervals_with_text(matched_result_with_text)
