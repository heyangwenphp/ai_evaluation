from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed, wait

from peewee import fn

from eva_questions import EvaQuestions
from models.big_models import BigModels
from models.files import Files
from models.question import Question
from models.question_analyze import QuestionAnalyze
from models.question_answer import QuestionAnswer
from models.question_bank import QuestionBank
from utils.eva_report import EvaReport
from utils.handle_execl import HandleExecl
from utils.logger import logger

def start_evaluation(evaluation,models_id):
    try:
        logger.debug("start evaluation task")
        Question.update(status=1).where(Question.id == evaluation.id).execute()
        #1. 获取测评文件内容
        #根据文件id获取文件路径
        files=Files.get_file_id(evaluation.file_id)
        sample_xls = f".{files.path}"

        #2. 问题存入数据库
        # 读取execl表格内容,获得df
        logger.info(f"start evaluation task, sample_xls: {sample_xls}")
        df = HandleExecl().read_excel(sample_xls)
        #获得问题列表
        questions_list = HandleExecl().get_questions_list(df)
        logger.debug(f"questions_list: {questions_list}")
        for question in questions_list:
            logger.debug(f"question: {question}")
            data = {
                "question_id": evaluation.id,
                "cases": question["q_type"],
                "question": question['q_title'],
                "standard_answer": question['q_standard_answer'],
                "standard": question['q_standard'],
                "dimension": question['q_dimension']
            }
            logger.debug(f"插入QuestionBank数据库: {data}")
            QuestionBank.create(**data)
        #3. 调用模型接口获取答案
        #使用线程池并行执行不同模型的评测
        model_list =BigModels.select().where(BigModels.id.in_(models_id)).where(BigModels.status == 0).where(BigModels.is_del == 0).execute()
        # 使用多线程异步执行每个镜头需要生成的图片
        all_task = []
        thread_pool = ThreadPoolExecutor(
            max_workers=len(model_list),
            thread_name_prefix="start_evaluation_thread"
        )
        for val in model_list:
            all_task.append(thread_pool.submit(start_evaluation_thread,val=val,evaluation=evaluation))

        # 等待所有任务完成后更新后面的状态值
        wait(all_task)
        results = [future.result() for future in all_task]
        thread_pool.shutdown()
        logger.debug(f"all evaluation results: {results}")
        #4. 更新测评状态
        # if all(results):
        #     # Question.update(status=2).where(Question.id == evaluation.id).execute()
        #
        #
        #
        #
        #
        # else:
        #     Question.update(status=3,remarks="").where(Question.id == evaluation.id).execute()
        report=generate_report(evaluation)
        if report:
            Question.update(status=2).where(Question.id == evaluation.id).execute()
        else:
            Question.update(status=3,remarks="报告生成失败").where(Question.id == evaluation.id).execute()
        logger.debug("end evaluation task")
    except Exception as e:
        logger.error(f"start evaluation task error: {e}")
        Question.update(status=3,remarks=str(e)).where(Question.id == evaluation.id).execute()


def start_evaluation_thread(val, evaluation):
    try:
        logger.debug(f"start_evaluation_thread models: {val.id} evaluation: {evaluation.id}")
        question_list = QuestionBank.select().where(QuestionBank.question_id == evaluation.id).where(QuestionBank.is_del == 0).execute()
        for question_item in question_list:
            logger.debug(f"模型 {val.id} 对测评 {evaluation.id} 进行评测开始")
            question = {
                "q_type": question_item.cases,
                "q_title": question_item.question,
                "q_standard_answer": question_item.standard_answer,
                "q_standard": question_item.standard,
                "q_dimension": question_item.dimension
            }
            result = EvaQuestions(model_name=val.title).eva_question(question)
            logger.debug(f"模型 {val.id} 对测评 {evaluation.id} 题目 {question_item.id} 评测结果: {result}")
            data = {
                "question_id": question_item.question_id,
                "question_bank_id": question_item.id,
                "cases": question_item.cases,
                "dimension": question_item.dimension,
                "models_id": val.id,
                "answer_content":  result.get("answer_content",""),
                "score": result.get("score",0),
                "full_mark": result.get("full_mark",0),
                "according": result.get("according",""),
            }
            logger.debug(f"模型 {val.id} 对测评 {evaluation.id} 题目 {question_item.id} 评测结果存入数据库: {data}")
            QuestionAnswer.create(**data)
            logger.debug(f"模型 {val.id} 对测评 {evaluation.id} 题目 {question_item.id} 评测完成")
        logger.debug(f"模型 {val.id} 对测评 {evaluation.id} 进行评测完成")
        return True
    except Exception as e:
        logger.error(f"start_evaluation_thread error: {e}")
        return False

#生成报告
def generate_report(evaluation):
    try:
        logger.debug(f"generate_report evaluation_id: {evaluation.id}")
        evaluation = Question.get_question_id(evaluation.id)
        data = {}
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
        # 前沿
        data["report_intro"] = report_intro
        # 生成整体分析
        report_analysis = eva.generate_overall_analysis(dimension_str)
        logger.info(f"生成的整体分析：{report_analysis}")
        # 整体分析
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
                "model_name": model_info.name if model_info else None,
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
        data['report_charts_1_data'] = answer_list
        data["report_charts_1_title"] = report_charts_1
        # 从测评的四大维度来看
        evaluation_dimension_title = f"从测评的{len(dimens)}大维度来看"
        data["evaluation_dimension_title"] = evaluation_dimension_title

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
        # 维度分析
        data["report_dimension_analysis"] = report_dimension_analysis
        data["report_dimension_analysis_charts_data"] = answer_list

        # 国内外模型对比分析
        # 总分 国内87，国外98；维度一 国内89分，国外88分；维度二 国内88分，国外87分；维度三 国内87分，国外86分；维度四 国内86分，国外85分
        data['report_comparison_analysis_show'] = 1
        if domestic_model_count == 0 or foreign_model_count == 0:
            data['report_comparison_analysis_show'] = 0
            data["report_comparison_analysis"] = ''
            data["report_comparison_analysis_charts_data"] = ''
        else:
            domestic_total_score_avg = domestic_total_score / domestic_model_count if domestic_model_count > 0 else 0
            total_score_abroad_avg = total_score_abroad / foreign_model_count if foreign_model_count > 0 else 0
            comparison_data = f"总分 国内{domestic_total_score_avg:.2f}，国外{total_score_abroad_avg:.2f}；"
            proportion_list.insert(0, {
                "dimension": "总分",
                "domestic_model_total_score": round(domestic_total_score_avg, 2),
                "foreign_models_total_score": round(total_score_abroad_avg, 2)
            })
            for proportion in proportion_list:
                comparison_data += f"维度{proportion['dimension']} 国内{proportion['domestic_model_total_score']:.2f}分，国外{proportion['foreign_models_total_score']:.2f}分；"
            # 国内外模型对比分析
            report_comparison_analysis = eva.generate_comparison_analysis(comparison_data)
            # 国内外模型对比分析
            data["report_comparison_analysis"] = report_comparison_analysis
            data["report_comparison_analysis_charts_data"] = proportion_list

        # data["answers"] = answer_list
        # data["proportion"] = proportion_list
        analyze = {
            "question_id": evaluation.id,
            "analysis_results": data
        }
        QuestionAnalyze.create(**analyze)
        logger.debug(f"generate_report completed for evaluation_id: {evaluation.id}")
        return True
    except Exception as e:
        logger.error(f"generate_report error: {e}")
        return False