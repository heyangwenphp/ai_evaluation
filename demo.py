#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : justin.郑
# @mail     : 3907721@qq.com
# @Time     : 2025/10/22 16:26
# @File     : gradio_demo.py
# @Desc     : Gradio测评工作流程演示系统

import gradio as gr
import pandas as pd
import hashlib
import concurrent.futures
import time
import os
import tempfile
from typing import List, Dict, Tuple, Optional
import traceback

# 导入现有模块
import sys
sys.path.append('..')
from handle_execl import HandleExecl
from eva_questions import EvaQuestions

# 获取当前工作目录（demo文件夹）
CURRENT_DIR = os.getcwd()
DEMO_DIR = os.path.dirname(os.path.abspath(__file__))

# 确保demo文件夹存在
os.makedirs(DEMO_DIR, exist_ok=True)


class EvaluationWorkflow:
    """测评工作流程管理类"""

    def __init__(self):
        self.handle_excel = HandleExecl()
        self.progress_steps = [
            "初始化系统...",
            "读取Excel文件...",
            "验证必填列...",
            "获取问题列表...",
            "获取维度列表...",
            "开始模型评测...",
            "处理模型结果...",
            "计算得分统计...",
            "生成最终结果..."
        ]

    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        return ['deepseek', 'doubao', 'gpt', 'qwen', 'kimi', 'qianfan',
                'baichuan', 'spark', 'zhipu', 'minimax', 'hunyuan', 'claude', 'gemini']

    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """验证上传的文件"""
        if file_path is None:
            return False, "请上传Excel文件"

        if not os.path.exists(file_path):
            return False, "文件不存在"

        # 检查文件扩展名
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ['.xls', '.xlsx']:
            return False, "仅支持.xls或.xlsx格式的Excel文件"

        return True, "文件验证通过"

    def process_model_questions(self, llm_name: str, questions_list: List[Dict]) -> List[Dict]:
        """处理单个模型的所有问题"""
        model_results = []
        for question in questions_list:
            try:
                result = EvaQuestions(model_name=llm_name).eva_question(question)
                model_results.append(result)
            except Exception as e:
                # 创建一个错误结果
                error_result = {
                    "q_title": question.get('q_title', ''),
                    "q_type": question.get('q_type', ''),
                    "anwser_content": f"评测失败: {str(e)}",
                    "q_standard_answer": question.get('q_standard_answer', ''),
                    "q_standard": question.get('q_standard', ''),
                    "score": 0,
                    "full_mark": question.get('full_mark', 5),
                    "according": f"评测过程中发生错误: {str(e)}",
                    "q_dimension": question.get('q_dimension', ''),
                    "llm_name": llm_name
                }
                model_results.append(error_result)
        return model_results

    def run_evaluation(self, file_obj, selected_models: List[str], progress=gr.Progress()) -> Tuple[pd.DataFrame, str, str]:
        """执行完整的测评流程"""
        try:
            # 步骤0: 验证文件
            progress(0.1, desc="验证上传文件...")
            if file_obj is None:
                return pd.DataFrame(), "❌ 错误：请上传Excel文件", ""

            # 保存上传的文件到临时位置
            # 处理不同类型的文件对象
            if isinstance(file_obj, bytes):
                # 如果是bytes类型，直接写入
                file_content = file_obj
            elif hasattr(file_obj, 'read'):
                # 如果是文件对象，读取内容
                file_content = file_obj.read()
            elif hasattr(file_obj, 'name'):
                # 如果有name属性，尝试直接使用文件路径
                tmp_file_path = file_obj.name
                file_content = None
            else:
                return pd.DataFrame(), "❌ 错误：不支持的文件类型", ""

            # 如果需要创建临时文件
            if file_content is not None:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    if isinstance(file_content, bytes):
                        tmp_file.write(file_content)
                    else:
                        # 如果是字符串，需要编码
                        tmp_file.write(file_content.encode('utf-8') if isinstance(file_content, str) else file_content)
                    tmp_file_path = tmp_file.name

            try:
                # 步骤1: 读取Excel文件
                progress(0.2, desc="读取Excel文件...")
                df = self.handle_excel.read_excel(tmp_file_path)

                # 步骤2: 验证必填列
                progress(0.3, desc="验证必填列...")
                is_required_columns, missing_columns = self.handle_excel.check_required_columns(df)

                if not is_required_columns:
                    missing_str = ", ".join(missing_columns)
                    error_msg = f"❌ 错误：输入表格缺少必填列: {missing_str}"
                    return pd.DataFrame(), error_msg, ""

                # 步骤3: 获取维度列表和问题列表
                progress(0.4, desc="获取题目信息...")
                dimension_list = self.handle_excel.get_dimension_list(df)
                questions_list = self.handle_excel.get_questions_list(df)

                if not questions_list:
                    return pd.DataFrame(), "❌ 错误：未找到有效的题目信息", ""

                # 步骤4: 开始模型评测
                progress(0.5, desc="开始模型评测...")
                result_list = []

                # 使用线程池并行执行不同模型的评测
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(selected_models), 3)) as executor:
                    # 为每个模型提交任务
                    future_to_model = {
                        executor.submit(self.process_model_questions, llm_name, questions_list): llm_name
                        for llm_name in selected_models
                    }

                    # 收集结果
                    model_results_dict = {}
                    completed_models = 0

                    for future in concurrent.futures.as_completed(future_to_model):
                        llm_name = future_to_model[future]
                        try:
                            model_results = future.result()
                            model_results_dict[llm_name] = model_results
                            completed_models += 1
                            progress_val = 0.5 + (0.3 * completed_models / len(selected_models))
                            progress(progress_val, desc=f"完成模型 {llm_name} 评测...")
                        except Exception as exc:
                            error_msg = f"模型 {llm_name} 评测时发生异常: {exc}"
                            print(error_msg)
                            # 创建空结果列表以保持结构完整
                            model_results_dict[llm_name] = []

                    # 按照选择顺序将结果添加到result_list
                    for llm_name in selected_models:
                        if llm_name in model_results_dict:
                            result_list.extend(model_results_dict[llm_name])

                # 步骤5: 写入结果Excel文件到demo文件夹
                progress(0.8, desc="保存评测结果...")
                encoded_query = tmp_file_path.encode('utf-8')
                filename = hashlib.md5(encoded_query).hexdigest()
                result_file_path = os.path.join(DEMO_DIR, f"{filename}_result.xlsx")
                self.handle_excel.write_excel(result_list, result_file_path)

                # 步骤6: 读取结果并计算统计
                progress(0.85, desc="计算得分统计...")
                df_result = self.handle_excel.read_excel(result_file_path)
                cal_list = []

                for llm_name in selected_models:
                    df_result_llm = df_result[df_result['llm_name'] == llm_name]
                    tmp = {"llm_name": llm_name}
                    total_points = 0

                    for dimension in dimension_list:
                        # 获取该维度的数据
                        dimension_data = df_result_llm[df_result_llm['q_dimension'] == dimension]

                        # 确保score和full_mark是数值类型，处理可能的字符串转换
                        try:
                            # 转换score列为数值类型
                            scores = pd.to_numeric(dimension_data['score'], errors='coerce').fillna(0)
                            full_marks = pd.to_numeric(dimension_data['full_mark'], errors='coerce').fillna(0)

                            score_sum = scores.sum()
                            full_mark_sum = full_marks.sum()

                            if full_mark_sum > 0:
                                avg_score = round(score_sum / full_mark_sum * 100, 2)
                            else:
                                avg_score = 0
                        except Exception as e:
                            print(f"计算维度 {dimension} 的分数时出错: {e}")
                            avg_score = 0

                        tmp[dimension] = avg_score
                        total_points += avg_score

                    if len(dimension_list) > 0:
                        tmp["总分"] = round(total_points / len(dimension_list), 2)
                    else:
                        tmp["总分"] = 0

                    cal_list.append(tmp)

                # 步骤7: 排序并生成最终结果
                progress(0.95, desc="生成最终结果...")
                cal_list = sorted(cal_list, key=lambda x: x["总分"], reverse=True)

                # 转换为DataFrame用于显示
                if cal_list:
                    result_df = pd.DataFrame(cal_list)

                    # 重新排列列的顺序：第1列是"模型"，第2列是"总分"，后面是其他维度
                    if not result_df.empty:
                        # 获取所有列名
                        columns = result_df.columns.tolist()

                        # 将"llm_name"重命名为"模型"
                        if 'llm_name' in columns:
                            result_df = result_df.rename(columns={'llm_name': '模型'})
                            columns[columns.index('llm_name')] = '模型'

                        # 重新排列列顺序：模型、总分、其他维度
                        new_columns = []
                        if '模型' in columns:
                            new_columns.append('模型')
                        if '总分' in columns:
                            new_columns.append('总分')

                        # 添加其他维度列（排除模型和总分）
                        dimension_columns = [col for col in columns if col not in ['模型', '总分']]
                        new_columns.extend(dimension_columns)

                        # 应用新的列顺序
                        result_df = result_df[new_columns]

                    # 清理临时文件
                    try:
                        os.unlink(tmp_file_path)
                    except:
                        pass

                    progress(1.0, desc="✅ 测评完成！")
                    success_msg = f"✅ 成功完成 {len(selected_models)} 个模型的评测，共处理 {len(questions_list)} 道题目"

                    return result_df, success_msg, result_file_path
                else:
                    return pd.DataFrame(), "⚠️ 警告：未能生成有效的评测结果", ""

            finally:
                # 清理临时文件
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass

        except Exception as e:
            error_msg = f"❌ 系统错误: {str(e)}\n\n详细错误信息:\n{traceback.format_exc()}"
            return pd.DataFrame(), error_msg, ""


def create_demo_interface():
    """创建Gradio演示界面"""

    workflow = EvaluationWorkflow()

    # 定义CSS样式
    css = """
    .container {
        max-width: 1200px;
        margin: 0 auto;
    }
    .header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .progress-container {
        margin: 20px 0;
        padding: 15px;
        border: 1px solid #ddd;
        border-radius: 8px;
        background-color: #f9f9f9;
    }
    .result-table {
        margin-top: 20px;
    }
    .error-message {
        color: #d32f2f;
        background-color: #ffebee;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #d32f2f;
    }
    .success-message {
        color: #2e7d32;
        background-color: #e8f5e8;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #2e7d32;
    }
    """

    with gr.Blocks(css=css, title="AI模型测评演示系统") as demo:
        gr.HTML("""
        <div class="header">
            <h1>🤖 AI模型测评工作流程演示系统</h1>
            <p>基于Gradio的自动化模型评测平台 - 从Excel输入到结果输出的完整流程</p>
        </div>
        """)

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## 📥 输入配置")

                # 文件上传组件
                file_input = gr.File(
                    label="上传测评表格",
                    file_types=[".xls", ".xlsx"]
                )

                gr.Markdown("### 文件格式要求")
                gr.Markdown("""
                Excel文件必须包含以下列：
                - **维度**: 题目所属维度
                - **题目**: 具体的题目内容
                - **题目类型**: 主观题/客观题
                - **打分标准**: 评分标准说明

                可选列：
                - **标准答案**: 客观题的正确答案
                """)

                # 模型选择组件
                model_checkbox = gr.CheckboxGroup(
                    choices=workflow.get_available_models(),
                    label="选择评测模型",
                    value=['deepseek', 'gpt', 'claude'],  # 默认选择3个模型
                    info="可以选择多个模型进行对比评测"
                )

                # 执行按钮
                run_button = gr.Button(
                    "🚀 开始测评",
                    variant="primary",
                    size="lg",
                    elem_classes=["run-button"]
                )

            with gr.Column(scale=2):
                gr.Markdown("## 📊 测评结果")

                # 进度显示
                progress_output = gr.HTML(
                    value="<div class='progress-container'>等待开始测评...</div>"
                )

                # 结果表格
                result_table = gr.Dataframe(
                    label="测评得分统计表",
                    interactive=False,
                    elem_classes=["result-table"]
                )

                # 状态消息
                status_message = gr.HTML(
                    value="<div class='progress-container'>系统就绪，请上传文件并选择模型开始测评</div>"
                )

                # 下载按钮
                download_button = gr.DownloadButton(
                    label="📥 下载详细评测结果",
                    variant="secondary",
                    visible=False,
                    elem_id="download_button"
                )

        # 定义执行函数
        def run_evaluation_with_progress(file_obj, selected_models):
            if not selected_models:
                return pd.DataFrame(), "<div class='error-message'>❌ 请至少选择一个模型进行测评</div>", "<div class='progress-container'>等待开始测评...</div>", gr.DownloadButton(visible=False, label="📥 下载详细评测结果")

            if len(selected_models) > 5:
                return pd.DataFrame(), "<div class='error-message'>⚠️ 为避免系统过载，请选择不超过5个模型</div>", "<div class='progress-container'>等待开始测评...</div>", gr.DownloadButton(visible=False, label="📥 下载详细评测结果")

            # 开始执行测评
            result_df, status_msg, download_path = workflow.run_evaluation(file_obj, selected_models)

            # 格式化状态消息
            if "✅" in status_msg and download_path:
                formatted_msg = f"<div class='success-message'>{status_msg}</div>"
                progress_msg = "<div class='progress-container'>✅ 测评完成！结果已显示在下方表格中</div>"
                # 显示下载按钮
                download_button = gr.DownloadButton(
                    label="📥 下载详细评测结果",
                    value=download_path,
                    visible=True,
                    variant="secondary"
                )
            elif "❌" in status_msg:
                formatted_msg = f"<div class='error-message'>{status_msg}</div>"
                progress_msg = "<div class='progress-container'>❌ 测评失败，请检查输入并重试</div>"
                download_button = gr.DownloadButton(visible=False, label="📥 下载详细评测结果")
            else:
                formatted_msg = f"<div class='progress-container'>{status_msg}</div>"
                progress_msg = f"<div class='progress-container'>{status_msg}</div>"
                download_button = gr.DownloadButton(visible=False, label="📥 下载详细评测结果")

            return result_df, formatted_msg, progress_msg, download_button

        # 绑定事件
        run_button.click(
            fn=run_evaluation_with_progress,
            inputs=[file_input, model_checkbox],
            outputs=[result_table, status_message, progress_output, download_button],
            show_progress=True
        )

        # 添加示例说明
        gr.Markdown("---")
        gr.Markdown("## 🔍 使用说明")
        gr.Markdown("""
        ### 工作流程说明：
        1. **文件上传**: 上传包含题目信息的Excel文件
        2. **模型选择**: 选择需要对比评测的AI模型（建议选择2-5个）
        3. **执行测评**: 点击"开始测评"按钮，系统将自动执行：
           - 验证文件格式和必填列
           - 并行处理多个模型的题目回答
           - 自动评分和统计分析
           - 生成对比结果表格
        4. **结果查看**: 查看各模型在不同维度的得分对比
        5. **结果下载**: 测评完成后可下载详细的Excel结果文件

        ### 系统特性：
        - ✅ **自动化流程**: 从输入到输出的全自动化处理
        - ✅ **并行处理**: 多模型同时评测，提高效率
        - ✅ **实时进度**: 显示当前处理步骤和状态
        - ✅ **错误处理**: 完善的错误检测和提示机制
        - ✅ **结果排序**: 按总分自动排序，便于对比
        - ✅ **结果下载**: 支持下载详细评测结果的Excel文件
        """)

    return demo


if __name__ == "__main__":
    # 创建并启动演示系统
    demo = create_demo_interface()

    print("🚀 启动AI模型测评演示系统...")
    print("📍 访问地址: http://localhost:7860")
    print("📝 使用说明: 请上传Excel文件并选择模型进行测评")

    demo.launch(
        server_name="0.0.0.0",
        root_path="/demo",
        server_port=7003,
        share=False,
        show_error=True,
        debug=True
    )