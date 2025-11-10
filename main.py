#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : justin.郑
# @mail     : 3907721@qq.com
# @Time     : 2025/10/22 13:48
# @File     : main.py
# @Desc     : 工作流


import hashlib
import concurrent.futures
from handle_execl import HandleExecl
from eva_questions import EvaQuestions


# 1 输入表格路径、执行大模型名称
sample_xls = "测评模版.xlsx"
model_list = ['deepseek', 'doubao']
result_list = []
cal_list = []

# 2、 读取execl表格内容,获得df
df = HandleExecl().read_excel(sample_xls)
# 获得维度列表
dimension_list = HandleExecl().get_dimension_list(df)

# 3、 检查表格必填列是否存在. is_required_columns是Ture执行下面内容，如果为False，打印错误信息
is_required_columns, e = HandleExecl().check_required_columns(df)
def process_model_questions(llm_name, questions_list):
    """处理单个模型的所有问题"""
    model_results = []
    for question in questions_list:
        result = EvaQuestions(model_name=llm_name).eva_question(question)
        model_results.append(result)
    return model_results

if is_required_columns:
    # 4、获取表格列表
    questions_list = HandleExecl().get_questions_list(df)

    # 5、使用线程池并行执行不同模型的评测
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(model_list)) as executor:
        # 为每个模型提交任务
        future_to_model = {
            executor.submit(process_model_questions, llm_name, questions_list): llm_name
            for llm_name in model_list
        }

        # 按照model_list的顺序收集结果
        model_results_dict = {}
        for future in concurrent.futures.as_completed(future_to_model):
            llm_name = future_to_model[future]
            try:
                model_results = future.result()
                model_results_dict[llm_name] = model_results
                print(f"模型 {llm_name} 评测完成，共处理 {len(model_results)} 个题目")
            except Exception as exc:
                print(f"模型 {llm_name} 评测时发生异常: {exc}")

        # 按照原有model_list的顺序将结果添加到result_list
        for llm_name in model_list:
            if llm_name in model_results_dict:
                result_list.extend(model_results_dict[llm_name])
else:
    e_str = ",".join(e)
    print(f"输入表格缺少必填列: {e_str}")


# 6、将result_list写入execl表格
encoded_query = sample_xls.encode('utf-8')
filename = hashlib.md5(encoded_query).hexdigest()
file_path = f"{filename}.xlsx"
HandleExecl().write_excel(result_list, file_path)


# 7、读取写入的execl表格内容,获得df
df_result = HandleExecl().read_excel(file_path)


# 8、按model_list分别获取df_result的内容
for llm_name in model_list:
    df_result_llm = df_result[df_result['llm_name'] == llm_name]
    print(f"模型 {llm_name} 的评测结果:")
    tmp = { "模型": llm_name }
    total_points = 0
    # 9、 计算每个维度的score总分和full_mark总分，并计算score总分除以full_mark总分的百分比
    for dimension in dimension_list:
        score_sum = df_result_llm[df_result_llm['q_dimension'] == dimension]['score'].sum()
        full_mark_sum = df_result_llm[df_result_llm['q_dimension'] == dimension]['full_mark'].sum()
        avg_score = round(score_sum / full_mark_sum * 100, 2)
        print(f"维度 {dimension} 的score总分: {score_sum:.2f}")
        print(f"维度 {dimension} 的full_mark总分: {full_mark_sum:.2f}")
        print(f"维度 {dimension} 的平均分: {avg_score:.2f}%")
        tmp[dimension] = avg_score
        total_points += avg_score
    tmp["总分"] = round(total_points / len(dimension_list), 2)
    cal_list.append(tmp)
    print(df_result_llm)
    print("\n" + "="*50 + "\n")  # 分隔线


# 10、cal_list列表按总分排序倒序，
cal_list = sorted(cal_list, key=lambda x: x["总分"], reverse=True)

print(cal_list)