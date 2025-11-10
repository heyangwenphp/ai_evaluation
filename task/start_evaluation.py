from concurrent.futures import ThreadPoolExecutor, as_completed, wait

from eva_questions import EvaQuestions
from models.big_models import BigModels
from models.files import Files
from models.question import Question
from models.question_answer import QuestionAnswer
from models.question_bank import QuestionBank
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
        if all(results):
            Question.update(status=2).where(Question.id == evaluation.id).execute()
        else:
            Question.update(status=3,remarks="").where(Question.id == evaluation.id).execute()
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
            logger.debug("模型 {val.id} 对测评 {evaluation.id} 题目 {question_item.id} 评测完成")
        logger.debug(f"模型 {val.id} 对测评 {evaluation.id} 进行评测完成")
        return True
    except Exception as e:
        logger.error(f"start_evaluation_thread error: {e}")
        return False