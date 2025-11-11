from typing import Optional, Any, List
from dotenv import load_dotenv
from fastapi import  APIRouter, Request,Depends,BackgroundTasks
from pydantic import BaseModel
from common.function import fail, success
from common import deps
from models.big_models import BigModels
from models.files import Files
from models.question_answer import QuestionAnswer
from models.users import Users
from task.start_evaluation import start_evaluation
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
                "model_name": model_info.name if model_info else None,
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