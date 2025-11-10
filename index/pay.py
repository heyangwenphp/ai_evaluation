import datetime

from fastapi import  APIRouter, Request,Depends
from dotenv import load_dotenv
from pydantic import BaseModel
from common import deps
from common.function import success, fail, generate_order_id, is_expire
from models.users import Users
from utils.AliPay import AliPay
from utils.logger import logger

router = APIRouter()
load_dotenv()

class Item(BaseModel):
    purchase_type: int # 购买类型 1会员 2点数
    product_id: int #产品id








@router.post("/CreateOrder")
async def CreateOrder(item: Item,user: Users = Depends(deps.get_current_user)):
    try:



        out_trade_no = generate_order_id()
        total_amount = 1
        payment_type = 1
        user_id = user.id
        status = 0

        product_code = "FAST_INSTANT_TRADE_PAY"
        total_amount = str(1)
        #response = AliPayTest().pay(out_trade_no, total_amount, subject, product_code)
        response = AliPay().pay(out_trade_no, total_amount, "subject", product_code)
        return success({"rq":response,"out_trade_no":out_trade_no})
    except Exception as e:
        return fail(str(e))

#支付回调
@router.post("/AliNotify")
async def AliNotify(request: Request):
    try:
        body = await request.form()
        logger.debug(f"支付回调：{body}")
        out_trade_no = body['out_trade_no']
        #total_amount = body['total_amount']
        trade_status = body['trade_status']
        trade_no = body['trade_no']
        buyer_pay_amount = float(body['buyer_pay_amount'])
        invoice_amount = float(body['invoice_amount'])
        paymentTime = body['gmt_payment']
        if trade_status != 'TRADE_SUCCESS':
            status = 2
        else:
            status =1

        return "success"
        #return success("支付成功")
    except Exception as e:
        logger.debug(f"重新支付回调：{str(e)}")
        return "fail"
        #return fail(str(e))




