from typing import Optional, Any, List
from dotenv import load_dotenv
from fastapi import  APIRouter, Request,Depends,BackgroundTasks
from pydantic import BaseModel
from common.function import fail, success
from common import deps
from models.big_models import BigModels
from models.files import Files
from models.question_analyze import QuestionAnalyze
from models.question_answer import QuestionAnswer
from models.question_bank import QuestionBank
from models.users import Users
from task.start_evaluation import start_evaluation
from utils.eva_report import EvaReport
from utils.logger import logger
from models.question import Question
from peewee import fn
from collections import defaultdict

load_dotenv()

router = APIRouter()


class Item(BaseModel):
    question: str
    file_id: int
    models_id: List[int] = []




#创建测评
@router.post("/CreateEvaluation", summary="创建测评", name="创建测评")
def CreateEvaluation(item:Item,background_tasks: BackgroundTasks,user: Users = Depends(deps.get_current_user)):
    try:
        if not item.question or item.question.strip() == "":
            return fail("问题不能为空")
        if not item.file_id:
            return fail("测评文件不能为空")
        if not Files.get_file_id(item.file_id):
            return fail("测评文件不存在")
        if not item.models_id or len(item.models_id) == 0:
            return fail("请选择测评模型")
        #判断模型id是否全部存在BigModels表中
        models = [model.id for model in BigModels.select(BigModels.id).where(BigModels.id.in_(item.models_id)).where(BigModels.status == 0).where(BigModels.is_del == 0).execute()]
        if len(models) != len(item.models_id):
            return fail("所选模型不存在")
        evaluation = Question.create_question(user_id=user.id, question=item.question.strip(),file_id=item.file_id,models_id=item.models_id)
        background_tasks.add_task(start_evaluation, evaluation=evaluation, models_id=item.models_id)
        return success(evaluation.id)


    except Exception as e:
        logger.error(f"创建对话异常：{e}")
        return fail(str(e))
#获取测评列表
@router.get("/GetEvaluationList", summary="获取测评列表", name="获取测评列表")
def GetEvaluationList(page: int = 1, page_size: int = 20, user: Users = Depends(deps.get_current_user)):
    try:
        evaluations, paginate = Question.fetch_user_questions(user_id=user.id, page=page, page_size=page_size)

        return success({"data": (evaluations), "total": paginate['count'], "current_page": paginate['current_page'],
                        "per_page": page_size})
    except Exception as e:
        logger.error(f"获取测评列表异常：{e}")
        return fail(str(e))


#获取测评任详情
@router.get("/GetEvaluationDetail", summary="获取测评详情", name="获取测评详情")
def GetEvaluationDetail(evaluation_id: int, user: Users = Depends(deps.get_current_user)):
    try:
        evaluation = Question.get_question_id(evaluation_id)
        if not evaluation:
            return fail("测评不存在")
        if evaluation.user_id != user.id:
            return fail("无权限查看该测评")
        data = {
            "id": evaluation.id,
            "question": evaluation.question,
            "file_id": evaluation.file_id,
            "models_id": evaluation.models_id,
            "status": evaluation.status,
            "remarks": evaluation.remarks
        }
        if evaluation.status != 2:
            return success(data)
        #查看是否已经存在分析结果
        analyze = QuestionAnalyze.get_analyze_by_question_id(evaluation.id)
        if analyze and analyze.analysis_results != '':
            analysis_results = eval(analyze.analysis_results)
            analysis_results["id"] = evaluation.id
            analysis_results["question"] = evaluation.question
            analysis_results["file_id"] = evaluation.file_id
            analysis_results["models_id"] = evaluation.models_id
            analysis_results["status"] = evaluation.status
            analysis_results["remarks"] = evaluation.remarks
            return success(analysis_results)
        return fail("测评结果生成中，请稍后查看")


    except Exception as e:
        logger.error(f"获取测评详情异常：{e}")
        return fail(str(e))

def GetEvaluationDetail_new_old(evaluation_id: int, user: Users = Depends(deps.get_current_user)):
    try:
        evaluation = Question.get_question_id(evaluation_id)
        if not evaluation:
            return fail("测评不存在")
        if evaluation.user_id != user.id:
            return fail("无权限查看该测评")
        data = {
            "id": evaluation.id,
            "question": evaluation.question,
            "file_id": evaluation.file_id,
            "models_id": evaluation.models_id,
            "status": evaluation.status,
            "remarks": evaluation.remarks
        }
        if evaluation.status != 2:
            return success(data)
        #查看是否已经存在分析结果
        analyze = QuestionAnalyze.get_analyze_by_question_id(evaluation.id)
        if analyze and analyze.analysis_results != '':
            return success(eval(analyze.analysis_results))

        eva = EvaReport()
        # 获取关键字（报告标题关键字）
        keywords = eva.extract_keywords(evaluation.question)
        logger.info(f"提取的关键词：{keywords}")
        # 报告标题
        data["report_title"] = f"中文大模型{keywords}能力测评报告"
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
        #前沿
        data["report_intro"] = report_intro
        # 生成整体分析
        report_analysis = eva.generate_overall_analysis(dimension_str)
        logger.info(f"生成的整体分析：{report_analysis}")
        #整体分析
        data["report_analysis"] = report_analysis
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
                                     "total_score_rate": f"{(score / full_mark * 100) if full_mark > 0 else 0:.2f}"})
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
                "model_name": model_info.title if model_info else None,
                "model_type": model_info.types if model_info else None,
                "total_score_rate": f"{(total_score / total_full_mark * 100) if total_full_mark > 0 else 0:.2f}",
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
        data['report_charts_1_data']=answer_list
        data["report_charts_1_title"] = report_charts_1
        # 从测评的四大维度来看
        evaluation_dimension_title = f"从测评的{len(dimens)}大维度来看"
        data["evaluation_dimension_title"] =evaluation_dimension_title

        # 生成测评维度分析
        analysis_data = ''
        t1_models = []
        t1_scores = []
        t1_orange_models = []
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
        #维度分析
        data["report_dimension_analysis"] = report_dimension_analysis
        data["report_dimension_analysis_charts_data"] = answer_list

        # 国内外模型对比分析
        # 总分 国内87，国外98；维度一 国内89分，国外88分；维度二 国内88分，国外87分；维度三 国内87分，国外86分；维度四 国内86分，国外85分
        domestic_total_score_avg = domestic_total_score / domestic_model_count if domestic_model_count > 0 else 0
        total_score_abroad_avg = total_score_abroad / foreign_model_count if foreign_model_count > 0 else 0
        comparison_data = f"总分 国内{domestic_total_score_avg:.2f}，国外{total_score_abroad_avg:.2f}；"
        proportion_list.insert(0,{
            "dimension": "总分",
            "domestic_model_total_score": round(domestic_total_score_avg,2),
            "foreign_models_total_score": round(total_score_abroad_avg,2)
        })
        for proportion in proportion_list:
            comparison_data += f"维度{proportion['dimension']} 国内{proportion['domestic_model_total_score']:.2f}分，国外{proportion['foreign_models_total_score']:.2f}分；"
        #国内外模型对比分析
        report_comparison_analysis = eva.generate_comparison_analysis(comparison_data)
        #国内外模型对比分析
        data["report_comparison_analysis"] = report_comparison_analysis
        data["report_comparison_analysis_charts_data"] = proportion_list

        # data["answers"] = answer_list
        # data["proportion"] = proportion_list
        analyze={
            "question_id":evaluation.id,
            "analysis_results":data
        }
        QuestionAnalyze.create(**analyze)
        return success(data)

    except Exception as e:
        logger.error(f"获取测评详情异常：{e}")
        return fail(str(e))





def GetEvaluationDetail_old(evaluation_id: int, user: Users = Depends(deps.get_current_user)):
    try:
        evaluation = Question.get_question_id(evaluation_id)
        if not evaluation:
            return fail("测评不存在")
        if evaluation.user_id != user.id:
            return fail("无权限查看该测评")
        data = {
            "id": evaluation.id,
            "question": evaluation.question,
            "file_id": evaluation.file_id,
            "models_id": evaluation.models_id,
            "status": evaluation.status,
            "remarks": evaluation.remarks
        }

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
                summary_data.append({"dimension":dim,"score": score, "full_mark": full_mark,"total_score_rate": f"{(score / full_mark * 100) if full_mark > 0 else 0:.2f}%"})
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
                "models_id": model_id,
                "model_name": model_info.title if model_info else None,
                "total_score": total_score,
                "total_full_mark": total_full_mark,
                "total_score_rate": f"{(total_score / total_full_mark * 100) if total_full_mark > 0 else 0:.2f}%",
                "model_evaluation_details": summary_data
            })

        answer_list.sort(key=lambda x: float(x['total_score_rate'].rstrip('%')), reverse=True)

        proportion_list = []

        for dim, scores in dimension_total_scores.items():
            domestic_avg = scores['domestic'] / domestic_model_count if domestic_model_count > 0 else 0
            foreign_avg = scores['foreign'] / domestic_model_count if domestic_model_count > 0 else 0
            proportion_list.append({
                "dimension": dim,
                "domestic_model_total_score": round(domestic_avg,2),
                "foreign_models_total_score": round(foreign_avg,2)
            })

        data["answers"] = answer_list
        data["proportion"] = proportion_list
        return success(data)

    except Exception as e:
        logger.error(f"获取测评详情异常：{e}")
        return fail(str(e))