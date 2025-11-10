import os
from dotenv import load_dotenv
load_dotenv()

from Crypto.PublicKey import RSA
from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.request.AlipayTradePagePayRequest import AlipayTradePagePayRequest


class AliPay:
    def __init__(self):
        # 初始化配置
        alipay_client_config = AlipayClientConfig()
        alipay_client_config.server_url = "https://openapi.alipay.com/gateway.do"
        alipay_client_config.app_id = os.getenv('ALIPAY_APPID')
        alipay_client_config.app_private_key = self.pkcs8_to_pkcs1(os.getenv('ALIPAY_PRIVATE_KEY'))
        alipay_client_config.alipay_public_key = os.getenv('ALIPAY_PUBLIC_KEY')
        alipay_client_config.sign_type = "RSA2"
        alipay_client_config.charset = "utf-8"
        alipay_client_config.debug = True
        self.client = DefaultAlipayClient(alipay_client_config)

    # 支付请求
    def pay(self, out_trade_no:str, total_amount:str, subject:str, product_code:str):
        """
        创建支付请求
        :param out_trade_no:    商户订单号
        :param total_amount:    订单金额
        :param subject:         订单标题
        :param product_code:    产品码
        :return:
        """
        host = os.getenv("HOST")
        notify_url = f'{host}/Index/AliNotify'
        request = AlipayTradePagePayRequest(biz_model=None)
        request.notify_url = notify_url
        request.biz_content = {
            "out_trade_no": out_trade_no,  # 商户订单号
            "total_amount": total_amount,  # 订单金额
            "subject": subject,  # 订单标题
            "product_code": product_code, # 产品码
            "qr_pay_mode": 4,  # 二维码支付模式
            "qrcode_width": 120, # 二维码宽度
        }

        # 发起支付请求
        response = self.client.page_execute(request, http_method="GET")
        return response

# curl -vk https://yuanjingtest.zeelin.cn/Index/AliNotify
    def pkcs8_to_pkcs1(self, pkcs8_key: str) -> str:
        """将 PKCS8 的密钥转换为 PKCS1"""
        if not pkcs8_key.startswith("-----BEGIN RSA PRIVATE KEY-----"):
            pkcs8_key = f'-----BEGIN RSA PRIVATE KEY-----\n{pkcs8_key}\n-----END RSA PRIVATE KEY-----'
        return RSA.importKey(pkcs8_key).exportKey().decode()


if __name__ == '__main__':
    out_trade_no = "20230212161023"
    total_amount = "0.01"
    subject = "测试1"
    product_code = "FAST_INSTANT_TRADE_PAY"
    response = AliPay().pay(out_trade_no, total_amount, subject, product_code)
    print(response)