from collections import defaultdict

from dotenv import load_dotenv
from fastapi import APIRouter
from peewee import fn

from common.function import fail, success
from eva_report import EvaReport
from models.big_models import BigModels
from models.question import Question
from models.question_answer import QuestionAnswer
from models.question_bank import QuestionBank
from utils.logger import logger

load_dotenv()

router = APIRouter()

#生成报告
@router.get("/GenerateReport", summary="生成报告", name="生成报告")
def GenerateReport(evaluation_id: int):
    try:
        evaluation=Question.get_question_id(evaluation_id)
        if not evaluation:
            return fail("测评不存在")
        eva = EvaReport()
        #获取关键字（报告标题关键字）
        keywords = eva.extract_keywords(evaluation.question)
        logger.info(f"提取的关键词：{keywords}")
        #报告标题
        report_title = f"中文大模型{keywords}能力测评报告"
        #生成报告前言
        #获取dimension 维度
        dimens = []
        QuestionBank_list = QuestionBank.select(QuestionBank.dimension).where(QuestionBank.question_id == evaluation.id).where(QuestionBank.is_del == 0).group_by(QuestionBank.dimension).objects()
        for qb in QuestionBank_list:
            dimens.append(qb.dimension)
        dimension_str = ",".join(dimens)
        logger.info(f"维度字符串：{dimension_str}")
        report_intro = eva.generate_report_intro(dimension_str, keywords)
        logger.info(f"生成的报告前言：{report_intro}")
        #生成整体分析
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
            for item in dimension_scores:
                score = float(item['total_score'] or 0)
                full_mark = float(item['total_full_mark'] or 0)
                total_score += score
                total_full_mark += full_mark

            answer_list.append({

                "model_name": model_info.name if model_info else None,
                "model_type": model_info.types if model_info else None,
                "total_score_rate": f"{(total_score / total_full_mark * 100) if total_full_mark > 0 else 0:.2f}%",

            })

        answer_list.sort(key=lambda x: float(x['total_score_rate'].rstrip('%')), reverse=True)

        #图1 模型DeepResearch能力总得分
        report_charts_1 = f"图1 模型{keywords}能力总得分"
        #从测评的四大维度来看
        evaluation_dimension_title = f"从测评的{len(dimens)}大维度来看"
        #生成测评维度分析
        report_dimension_analysis = eva.generate_dimension_analysis(dimension_str)




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














