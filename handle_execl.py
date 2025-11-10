#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : justin.郑
# @mail     : 3907721@qq.com
# @Time     : 2025/10/22 10:44
# @File     : handle_execl.py
# @Desc     : 处理Excel

import os
import pandas as pd


class HandleExecl:
    def __init__(self):
        pass

    def read_excel(self, file_path: str, sheet_name=None):
        """
        读取 .xls 或 .xlsx
        :param file_path: 文件路径
        :param sheet_name: None 表示读取第一个 Sheet；也可指定名称或索引
        :return: DataFrame
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(file_path)

        # 根据后缀选择引擎
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".xls":
            engine = "xlrd"
        elif ext == ".xlsx":
            engine = "openpyxl"
        else:
            raise ValueError("仅支持 .xls 或 .xlsx 格式")

        df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine)
        # 当 sheet_name 未指定时返回 DataFrame；否则可能是 OrderedDict
        if isinstance(df, dict):  # 用户传入 sheet_name=None 但文件含多 Sheet
            df = next(iter(df.values()))  # 取第一个
        return df

    def check_required_columns(self, df: pd.DataFrame):
        """
        检查 DataFrame 是否包含所需的列名
        :param df: DataFrame
        :return: tuple (bool, list) - (是否包含所有列, 缺少的列名列表)
        """
        if df is None or df.empty:
            return False, ["DataFrame 为空"]

        required_columns = ["维度", "题目", "题目类型", "打分标准"]
        existing_columns = df.columns.tolist()
        missing_columns = [col for col in required_columns if col not in existing_columns]

        if not missing_columns:
            return True, []
        else:
            return False, missing_columns

    def get_dimension_list(self, df: pd.DataFrame):
        """
        获取表格中"维度"列的内容，相同内容合并
        :param df: DataFrame
        :return: list - 去重后的维度列表
        """
        if df is None or df.empty:
            return []
        if "维度" not in df.columns:
            return []
        # 获取维度列，去除空值，然后去重
        dimension_list = df["维度"].dropna().unique().tolist()
        # 排序（可选）
        dimension_list.sort()
        return dimension_list

    def get_questions_list(self, df: pd.DataFrame):
        """
        获取每行数据，输出指定格式的字典列表
        :param df: DataFrame
        :return: list - 包含题目信息的字典列表
        """
        if df is None or df.empty:
            return []

        # 检查必需的列是否存在
        required_columns = ["题目类型", "题目", "打分标准", "维度"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return []

        questions_list = []

        for index, row in df.iterrows():
            # 跳过空行
            if row.isnull().all():
                continue

            question_dict = {
                "q_type": row["题目类型"] if pd.notna(row["题目类型"]) else "",
                "q_title": row["题目"] if pd.notna(row["题目"]) else "",
                "q_standard_answer": "",  # 如果有"标准答案"列，可以从这里获取
                "q_standard": row["打分标准"] if pd.notna(row["打分标准"]) else "",
                "q_dimension": row["维度"] if pd.notna(row["维度"]) else ""
            }

            # 如果存在"标准答案"列，则添加到字典中
            if "标准答案" in df.columns and pd.notna(row["标准答案"]):
                question_dict["q_standard_answer"] = row["标准答案"]

            questions_list.append(question_dict)

        return questions_list

    def write_excel(self, result_list: list, file_path: str):
        """
        将结果列表写入 Excel 文件
        :param result_list: 包含结果的列表，每个元素是一个字典
        :param file_path: 输出文件路径（.xls 或 .xlsx）
        """
        if not result_list:
            print("结果列表为空，无法写入文件")
            return

        # 将列表转换为 DataFrame
        df = pd.DataFrame(result_list)

        # 根据文件扩展名选择引擎
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".xls":
            engine = "xlrd"
        elif ext == ".xlsx":
            engine = "openpyxl"
        else:
            raise ValueError("仅支持 .xls 或 .xlsx 格式")

        # 写入 Excel 文件
        df.to_excel(file_path, index=False, engine=engine)
        print(f"结果已成功写入 {file_path}")


if __name__ == "__main__":
    sample_xls = "data/客观题01.xlsx"
    result_list = [
        {"a": 1, "b": 2, "c": 3},
        {"a": 4, "b": 5, "c": 6},
    ]
    handle_execl = HandleExecl()
    df1 = handle_execl.write_excel(result_list, sample_xls)

    pass
