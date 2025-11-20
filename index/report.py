from collections import defaultdict

from docx import Document
from dotenv import load_dotenv
from fastapi import APIRouter
from peewee import fn
from pyecharts.charts import Bar
from pyecharts import options as opts
from docx import Document
from docx.shared import Inches
from common.function import fail, success
from eva_report import EvaReport
from models.big_models import BigModels
from models.question import Question
from models.question_answer import QuestionAnswer
from models.question_bank import QuestionBank
from docx.oxml.ns import qn
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Inches, RGBColor, Pt, Cm
from docx.oxml import parse_xml, shared
from docx.oxml.ns import nsdecls
from pyecharts.render import make_snapshot
from snapshot_selenium import snapshot
from utils.logger import logger

load_dotenv()

router = APIRouter()


# 生成报告
@router.get("/GenerateReport", summary="生成报告", name="生成报告")
def GenerateReport(evaluation_id: int):
    try:
        evaluation = Question.get_question_id(evaluation_id)
        if not evaluation:
            return fail("测评不存在")
        eva = EvaReport()
        # 获取关键字（报告标题关键字）
        keywords = eva.extract_keywords(evaluation.question)
        logger.info(f"提取的关键词：{keywords}")
        # 报告标题
        report_title = f"中文大模型{keywords}能力测评报告"
        # 生成报告前言
        # 获取dimension 维度
        dimens = []
        QuestionBank_list = QuestionBank.select(QuestionBank.dimension).where(
            QuestionBank.question_id == evaluation.id).where(QuestionBank.is_del == 0).group_by(
            QuestionBank.dimension).objects()
        for qb in QuestionBank_list:
            dimens.append(qb.dimension)
        dimension_str = ",".join(dimens)
        logger.info(f"维度字符串：{dimension_str}")
        report_intro = eva.generate_report_intro(dimension_str, keywords)
        logger.info(f"生成的报告前言：{report_intro}")
        # 生成整体分析
        report_analysis = eva.generate_overall_analysis(dimension_str)
        logger.info(f"生成的整体分析：{report_analysis}")
        answer_list = []

        # 兼容models_id存储为字符串或列表
        if isinstance(evaluation.models_id, list):
            models_ids = evaluation.models_id
        else:
            try:
                models_ids = eval(evaluation.models_id) if evaluation.models_id else []
            except Exception:
                models_ids = []

        domestic_model_count = 0
        foreign_model_count = 0
        dimension_total_scores = defaultdict(lambda: {'domestic': 0.0, 'foreign': 0.0})

        for model_id in models_ids:
            model_info = BigModels.get_big_models_id(model_id)
            if model_info.types == 0:
                domestic_model_count += 1
            else:
                foreign_model_count += 1

            # 使用Peewee的group_by和fn.SUM进行分组求和
            dimension_scores = (QuestionAnswer
                                .select(QuestionAnswer.dimension,
                                        fn.SUM(QuestionAnswer.score).alias('total_score'),
                                        fn.SUM(QuestionAnswer.full_mark).alias('total_full_mark'))
                                .where(
                QuestionAnswer.question_id == evaluation.id,
                QuestionAnswer.models_id == model_id,
                QuestionAnswer.is_del == 0
            )
                                .group_by(QuestionAnswer.dimension)
                                .dicts())

            total_score = 0
            total_full_mark = 0
            summary_data = []
            for item in dimension_scores:

                dim = item['dimension'] or '未知'
                score = float(item['total_score'] or 0)
                full_mark = float(item['total_full_mark'] or 0)
                summary_data.append({"dimension": dim, "score": score, "full_mark": full_mark,
                                     "total_score_rate": f"{(score / full_mark * 100) if full_mark > 0 else 0:.2f}%"})
                total_score += score
                total_full_mark += full_mark
                percentage = 0
                if full_mark > 0:
                    percentage = round((score / full_mark * 100), 2)

                if model_info.types == 0:
                    dimension_total_scores[dim]['domestic'] += percentage
                else:
                    dimension_total_scores[dim]['foreign'] += percentage

            answer_list.append({
                "model_name": model_info.name if model_info else None,
                "model_type": model_info.types if model_info else None,
                "total_score_rate": f"{(total_score / total_full_mark * 100) if total_full_mark > 0 else 0:.2f}%",
                "model_evaluation_details": summary_data

            })

        answer_list.sort(key=lambda x: float(x['total_score_rate'].rstrip('%')), reverse=True)

        proportion_list = []
        # 国内总分
        domestic_total_score = 0
        # 国外总分
        total_score_abroad = 0

        for dim, scores in dimension_total_scores.items():
            domestic_avg = scores['domestic'] / domestic_model_count if domestic_model_count > 0 else 0
            foreign_avg = scores['foreign'] / domestic_model_count if domestic_model_count > 0 else 0
            domestic_total_score += round(domestic_avg, 2)
            total_score_abroad += round(foreign_avg, 2)
            proportion_list.append({
                "dimension": dim,
                "domestic_model_total_score": round(domestic_avg, 2),
                "foreign_models_total_score": round(foreign_avg, 2)
            })

        # 图1 模型DeepResearch能力总得分
        report_charts_1 = f"图1 模型{keywords}能力总得分"
        # 从测评的四大维度来看
        evaluation_dimension_title = f"从测评的{len(dimens)}大维度来看"

        # 生成测评维度分析
        analysis_data = ''
        t1_models=[]
        t1_scores=[]
        t1_orange_models=[]
        for answer in answer_list:
            analysis_data += f"{answer['model_name']} "
            t1_models.append(answer['model_name'])
            if answer['model_type'] == 1:
                t1_orange_models.append(answer['model_name'])
            t1_scores.append(float(answer['total_score_rate'].replace('%', '')))
            for model_evaluation in answer['model_evaluation_details']:
                analysis_data + f"{model_evaluation['dimension']}得分{model_evaluation['total_score_rate'].replace('%', '分')} "
            analysis_data += ';'

        report_dimension_analysis = eva.generate_dimension_analysis(analysis_data)

        # 国内外模型对比分析
        # 总分 国内87，国外98；维度一 国内89分，国外88分；维度二 国内88分，国外87分；维度三 国内87分，国外86分；维度四 国内86分，国外85分
        domestic_total_score_avg = domestic_total_score / domestic_model_count if domestic_model_count > 0 else 0
        total_score_abroad_avg = total_score_abroad / foreign_model_count if foreign_model_count > 0 else 0
        comparison_data = f"总分 国内{domestic_total_score_avg:.2f}，国外{total_score_abroad_avg:.2f}；"
        for proportion in proportion_list:
            comparison_data += f"维度{proportion['dimension']} 国内{proportion['domestic_model_total_score']:.2f}分，国外{proportion['foreign_models_total_score']:.2f}分；"
        report_comparison_analysis = eva.generate_comparison_analysis(comparison_data)

        doc = Document()
        addLevel(doc,report_title)
        addLevel2(doc,"01 前沿")
        addText(doc,report_intro)
        addLevel2(doc, "02 测评结果从模型差别到维度差异")
        addLevel3(doc, "从整体来看")
        addText(doc, report_analysis)
        draw_chart_1(t1_models, t1_scores, t1_orange_models)
        add_center_picture(doc, "superclue_fact_ranking.png", width=Inches(6))
        #图1 模型DeepResearch能力总得分
        addLevel3(doc, report_charts_1)
        #从测评的四大维度来看
        addLevel3(doc, evaluation_dimension_title)
        addText(doc, report_dimension_analysis)

        # 伪代码：根据evaluation_id生成报告
        report = {
            "evaluation_id": evaluation_id,
            "summary": "This is a generated report summary.",
            "details": "Detailed analysis goes here."
        }
        return success(report)
    except Exception as e:
        logger.error(f"生成报告异常：{e}")
        return fail(str(e))


def addText(doc, text):
    paragrapha = doc.add_paragraph(text)
    paragrapha.style.font.size = Pt(12)
    # paragrapha.paragraph_format.first_line_indent = Cm(0.74)  # 左缩进0.74厘米即缩进2字符
    # paragrapha.paragraph_format.space_before = Pt(0.5)  # 设置段前 0.5 磅
    # paragrapha.paragraph_format.space_after = Pt(0.5)  # 设置段后 0.5 磅
    paragrapha.paragraph_format.line_spacing = 1.5  # 设置行间距为 1.5


def addLevel(doc, text):
    heading = doc.add_heading("", level=0)
    heading.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    run = heading.add_run(text)
    run.bold = True
    run.font.color.rgb = RGBColor(0, 0, 0)
    # 设置西文字体
    run.font.name = u'宋体'
    # 设置中文字体
    run._element.rPr.rFonts.set(qn('w:eastAsia'), u'宋体')
def addLevel2(doc, text):
    heading2 = doc.add_heading("", level=3)
    heading2.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
    heading2.paragraph_format.space_before = Pt(0.5)  # 设置段前 0.5磅
    heading2.paragraph_format.space_after = Pt(0.5)  # 设置段后 0.5 磅
    heading2.paragraph_format.line_spacing = 1.5  # 设置行间距为 1.5
    level3 = heading2.add_run(text)
    # level3.bold = True
    level3.font.color.rgb = RGBColor(0, 0, 0)
    level3.font.size = Pt(16)
    # 设置西文字体
    level3.font.name = u'宋体'
    # 设置中文字体
    level3._element.rPr.rFonts.set(qn('w:eastAsia'), u'宋体')

def addLevel3(doc, text):
    heading3 = doc.add_heading("", level=3)
    heading3.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
    heading3.paragraph_format.space_before = Pt(0.5)  # 设置段前 0.5磅
    heading3.paragraph_format.space_after = Pt(0.5)  # 设置段后 0.5 磅
    heading3.paragraph_format.line_spacing = 1.5  # 设置行间距为 1.5
    level3 = heading3.add_run(text)
    # level3.bold = True
    level3.font.color.rgb = RGBColor(0, 0, 0)
    level3.font.size = Pt(12)
    # 设置西文字体
    level3.font.name = u'宋体'
    # 设置中文字体
    level3._element.rPr.rFonts.set(qn('w:eastAsia'), u'宋体')


def add_center_picture(doc, image_path_or_stream, width=None, height=None):
    imghead = doc.add_heading("", level=1)
    imghead.paragraph_format.line_spacing = 3  # 设置行间距为 1.5
    tab = doc.add_table(rows=1, cols=3)  # 添加一个1行3列的空表
    cell = tab.cell(0, 1)  # 获取某单元格对象（从0开始索引）
    ph = cell.paragraphs[0]
    run = ph.add_run()
    run.add_picture(image_path_or_stream, width=width, height=height)

#绘制图1
def draw_chart_1(models, scores, orange_models):
    # 按颜色分两组
    blue_data = [s if m not in orange_models else None for m, s in zip(models, scores)]
    orange_data = [s if m in orange_models else None for m, s in zip(models, scores)]

    # ================================
    # 绘制图表
    # ================================
    bar = (
        Bar(init_opts=opts.InitOpts(width="800px", height="600px", bg_color="#ffffff"))
        .add_xaxis(models[::-1])  # 倒序排列（从上到下）
        .add_yaxis("蓝色组", blue_data[::-1], color="#5B8FF9",
                   label_opts=opts.LabelOpts(position="right", color="#000"))
        .add_yaxis("橙色组", orange_data[::-1], color="#FF9F40",
                   label_opts=opts.LabelOpts(position="right", color="#000"))
        .reversal_axis()  # 横向
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="SuperCLUE-Fact中文事实性幻觉测评总榜",
                pos_left="center",
                title_textstyle_opts=opts.TextStyleOpts(font_size=20)
            ),
            xaxis_opts=opts.AxisOpts(
                name="",
                axislabel_opts=opts.LabelOpts(formatter="{value}"),
                splitline_opts=opts.SplitLineOpts(is_show=True),
            ),
            yaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(font_size=12),
            ),
            # 显示全部图例
            legend_opts=opts.LegendOpts(is_show=False),
            tooltip_opts=opts.TooltipOpts(is_show=False),
        )
        .set_series_opts(
            bar_width="30%",
            label_opts=opts.LabelOpts(is_show=True, position="right", formatter="{c}")
        )
    )

    # ================================
    # 导出 HTML
    # ================================
    bar.render("superclue_fact_ranking.html")
    make_snapshot(snapshot, bar.render(), "superclue_fact_ranking.png")


#绘制图2
def draw_chart_2(models, y_data, foreign_scores):
    x_data = models

    y_data = {
        "标准核心体验度": [100, 85, 80, 78, 60, 95, 80, 65, 60, 70],
        "视频通话表现": [88, 82, 65, 75, 70, 50, 60, 58, 66, 60],
        "摄像镜头效果": [85, 79, 60, 45, 72, 78, 65, 55, 70, 62],
        "处理器负载表现": [90, 81, 78, 72, 68, 76, 64, 60, 68, 65],
    }

    # ======================
    # 创建 ECharts 柱状图
    # ======================
    bar = (
        Bar(init_opts=opts.InitOpts(width="800px", height="600px", bg_color="#ffffff"))
        .add_xaxis(x_data)
        .add_yaxis("标准核心体验度", y_data["标准核心体验度"], category_gap="30%", gap="0%")
        .add_yaxis("视频通话表现", y_data["视频通话表现"])
        .add_yaxis("摄像镜头效果", y_data["摄像镜头效果"])
        .add_yaxis("处理器负载表现", y_data["处理器负载表现"])
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(axislabel_opts={"rotate": 20}),
            yaxis_opts=opts.AxisOpts(name="平均得分 (%)"),
            legend_opts=opts.LegendOpts(pos_top="5%"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
        )
        .set_series_opts(
            label_opts=opts.LabelOpts(is_show=False)
        )
    )

    # 渲染到 HTML（可直接打开看效果）
    bar.render("multi_bar_chart.html")

    # 如果需要生成图片：
    #   pip install snapshot-selenium
    #   并配置好 ChromeDriver（参考上一步）
    # 然后执行：
    # from pyecharts.render import make_snapshot
    # from snapshot_selenium import snapshot
    # make_snapshot(snapshot, bar.render(), "multi_bar_chart.png")
    from pyecharts.render import make_snapshot
    from snapshot_phantomjs import snapshot
    make_snapshot(snapshot, bar.render(), "multi_bar_chart.png")
