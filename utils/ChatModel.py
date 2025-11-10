#!/usr/bin/env python
# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author  : justin.郑
# @mail    : 3907721@qq.com
# @Time    : 2024/9/18 09:51
# @File    : ChatModel
# @desc    : 聊天模型类


import os
from dotenv import load_dotenv
load_dotenv()

import Agently
from loguru import logger

class ChatModel:
    # 创建agent
    def get_agent_factory(self, model_name="deepseek"):
        models = {
            "deepseek": {
                "auth": {"api_key": os.getenv("DEEPSEEK_API_KEY")},
                "url": os.getenv("DEEPSEEK_API_BASE"),
                "options": {"model": "deepseek-reasoner"}
            },
            "deepseek_c": {
                "auth": {"api_key": os.getenv("DEEPSEEK_API_KEY")},
                "url": os.getenv("DEEPSEEK_API_BASE"),
                "options": {"model": "deepseek-chat"}
            },
            "qwen": {
                "auth": {"api_key": os.getenv("DASHSCOPE_API_KEY")},
                "url": os.getenv("DASHSCOPE_API_BASE"),
                "options": {"model": "qwen3-max"}
            },
            "kimi": {
                "auth": {"api_key": os.getenv("MOONSHOT_API_KEY")},
                "url": os.getenv("MOONSHOT_API_BASE"),
                "options": {"model": "kimi-k2-0905-preview"}
            },
            "qianfan": {
                "auth": {"api_key": os.getenv("QIANFAN_API_KEY")},
                "url": os.getenv("QIANFAN_API_BASE"),
                "options": {"model": "ernie-x1.1-preview"}
            },
            "doubao": {
                "auth": {"api_key": os.getenv("DOUBAO_API_KEY")},
                "url": os.getenv("DOUBAO_API_BASE"),
                "options": {"model": "doubao-seed-1-6-250615"}
            },
            "baichuan": {
                "auth": {"api_key": os.getenv("BAICHU_API_KEY")},
                "url": os.getenv("BAICHU_API_BASE"),
                "options": {"model": "Baichuan4-Turbo"}
            },
            "spark": {
                "auth": {"api_key": os.getenv("SPARK_API_KEY")},
                "url": os.getenv("SPARK_API_BASE"),
                "options": {"model": "x1"}
            },
            "zhipu": {
                "auth": {"api_key": os.getenv("ZHIPU_API_KEY")},
                "url": os.getenv("ZHIPU_API_BASE"),
                "options": {"model": "glm-4.6"}
            },
            "minimax": {
                "auth": {"api_key": os.getenv("MINIMAX_API_KEY")},
                "url": os.getenv("MINIMAX_API_BASE"),
                "options": {"model": "MiniMax-M1"}
            },
            "longcat": {
                "auth": {"api_key": os.getenv("LOGCAT_API_KEY")},
                "url": os.getenv("LOGCAT_API_BASE"),
                "options": {"model": "LongCat-Flash-Thinking"}
            },
            "hunyuan": {
                "auth": {"api_key": os.getenv("HUNYUAN_API_KEY")},
                "url": os.getenv("HUNYUAN_API_BASE"),
                "options": {"model": "hunyuan-turbos-20250926"}
            },
            "claude": {
                "auth": {"api_key": os.getenv("YIBU_API_KEY")},
                "url": os.getenv("YIBU_API_BASE"),
                "options": {"model": "claude-sonnet-4-5-20250929"}
            },
            "gemini": {
                "auth": {"api_key": os.getenv("YIBU_API_KEY")},
                "url": os.getenv("YIBU_API_BASE"),
                "options": {"model": "gemini-2.5-pro"}
            },
            "gpt": {
                "auth": {"api_key": os.getenv("YIBU_API_KEY")},
                "url": os.getenv("YIBU_API_BASE"),
                "options": {"model": "gpt-5"}
            }
        }
        try:
            agent_factory = Agently.AgentFactory()
            (
                agent_factory
                .set_settings("current_model", "OAIClient")
                .set_settings("model.OAIClient.auth", models[model_name]['auth'])
                .set_settings("model.OAIClient.url", models[model_name]['url'])
                .set_settings("model.OAIClient.options", models[model_name]['options'])
                .set_settings("is_debug", False)
            )
        except Exception as e:
            print(e)
            logger.error("使用大模型错误：" + str(e))

        return agent_factory


if __name__ == '__main__':
    agent_factory = ChatModel().get_agent_factory(model_name="zhipu")
    agent = agent_factory.create_agent()

    print(
        agent
        .input("慈禧是谁")
        .instruct("输出语言", "中文")
        .start()
    )

    # res = (
    #     agent
    #     .input("请画一只小象")
    #     # .files("https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg")
    #     # .instruct("输出语言", "中文")
    #     .start()
    # )
    # print(res)