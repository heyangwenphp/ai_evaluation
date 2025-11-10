#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : justin.郑
# @mail     : 3907721@qq.com
# @Time     : 2025/11/6 10:53
# @File     : eva_report.py
# @Desc     : 测评报告


from utils.logger import logger
from utils.ChatModel import ChatModel


class EvaReport:
    def __init__(self, model_name='deepseek_c') -> None:
        agent_factory = ChatModel().get_agent_factory(model_name=model_name)
        self.agent = agent_factory.create_agent()


    # 01 需求内容提取关键词
    def extract_keywords(self, requirement: str) -> str:
        """
        从测评报告中提取关键词

        :param requirement: 需求内容
        :return: 包含关键词
        """
        system_prompt = f"""
        从以下需求内容中提取一个关键词：
        <需求内容>
        {{requirement}}
        </需求内容>
        关键词：
        """
        try:
            res = (
                self.agent
                .general(system_prompt)
                .input({
                    "requirement": requirement
                })
                .output("提取一个关键词,不要超过6个字")
                .start()
            )
            logger.debug(f"从需求内容中提取关键词：{res}")
            return res
        except Exception as e:
            logger.error(f"从需求内容中提取关键词失败：{e}")
            return ""


    # 02 生成报告前言
    def generate_report_intro(self, dimens: str, keyword: str) -> str:
        """
        生成报告前言

        :param dimens: 测评维度
        :param keyword: 报告关键词
        :return: 报告前言
        """
        system_prompt = f"""
        根据用户在输入大模型{{测评维度}}测评维度，分析{{keyword}}测评维度的必要性。
        
        ## 参考如下：
        随着大语言模型的快速发展，AI不仅能够理解和生成自然语言，其推理、整合信息的能力也显著增强。DeepResearch正是这种能力在信息获取和知识生产领域的一个重要应用。它代表了AI从简单的信息检索向更高级的自主研究代理迈进的趋势，越来越多的DeepResearch产品出现在我们的视野中。为了全面客观地衡量各个DeepResearch产品的能力，推出测评报告。”注意只是参考我的语言风格，不要照搬结论。注意，且输出的语言不要过于复杂，也不要字数过多，一两句话即可
语言精炼且结论准确，且文字稳妥点，不要有太多评价，尤其是负面评价且要注意用语去AI化，不要有思考过程，输出格式严格参考我的样例格式，不要分段或分点，就是一段话，每句话之间自然衔接。
        """
        try:
            res = (
                self.agent
                .general(system_prompt)
                .input({
                    "测评维度": dimens,
                    "keyword": keyword
                })
                .output("生成一段测评维度的必要性内容,300字左右")
                .start()
            )
            logger.debug(f"生成报告前言：{res}")
            return res
        except Exception as e:
            logger.error(f"生成报告前言失败：{e}")
            return ""


    # 03 生成整体分析
    def generate_overall_analysis(self, models_score: str) -> str:
        """
        生成整体分析
        :param models_score: 大模型总得分
        :return: 整体分析
        """
        system_prompt = f"""
        分析大模型总得分的测试结果，分析高中低领域各自大模型，参考下面的格式进行输出，注意只是参考，不要照搬我的结论和分析。
        要注意输出内容，不要太多零散的点，要是完整的段落和平滑的过渡，只突出核心结论。
        
        参考如下:
        基线测评结果显示，所有受测模型的AI鲁棒性均不超过15%，表明当前大语言模型在事实准确性控制方面仍存在显著提升空间。其中GPT-5思考模式和自动模式以9.6%和10.2%的鲁棒性包揽冠亚军，说明OpenAI在幻觉控制维度的领先优势；Claude 4 Opus、deepseek、通义千问系列紧随其后，鲁棒性集中在5.3%-8.6%区间，位列第三至第八名；相比之下，豆包系列模型的鲁棒性相对较低，仅有1.3%，需进一步优化。
        
        注意:
        - 输出的语言不要过于复杂，也不要字数过多，一两句话即可
        - 语言精炼且结论准确，且文字稳妥点，不要有太多评价，尤其是负面评价
        - 且要注意用语去AI化
        - 注意不要瞎编数据，必须依据我提供的数据进行分析
        - 且要注意用语去AI化，不要有思考过程，输出格式严格参考我的样例格式，不要分段或分点，就是一段话，每句话之间自然衔接。
        """
        try:
            res = (
                self.agent
                .general(system_prompt)
                .input({
                    "大模型总得分": models_score
                })
                .output("生成一段分析大模型总得分的测试结果,400-500字")
                .start()
            )
            logger.debug(f"分析大模型总得分的测试结果：{res}")
            return res
        except Exception as e:
            logger.error(f"分析大模型总得分的测试结果失败：{e}")
            return ""


    # 04 生成测评维度分析
    def generate_dimension_analysis(self, data: str) -> str:
        """
        生成测评维度分析
        :param data: 平均得分对比表格数据    deepseek 维度1得分89分，维度2得分88分，维度3得分87分，维度4得分86分；
        :return: 测评维度分析
        """
        system_prompt = f"""
        请你结合各模型维度的平均得分对比表格数据，分析一下各大维度的大模型数据测评效果。
        
        ## 输出样例参考如下：
        四大任务的平均得分存在明显差异，硬性法规约束强于软性价值约束。本次测评的10个模型在规避违法犯罪、规避信息失责的平均分均达到了83分以上，其中规避违法犯罪为88.08分，规避信息失责为83.91分，而在规避伦理失范、传播中国特色社会主义核心价值观中平均分不到75分，仍有一定提升空间。”输出的分析模板如下“在哪些维度表现得好+在哪些维度有提升空间+分析总体得分高的维度和得分低的维度呈现的特点
        
        ## 注意
        - 且输出的语言不要过于复杂，也不要字数过多，一两句话即可
        - 语言精炼且结论准确，且文字稳妥点，不要有太多评价，尤其是负面评价
        - 且要注意用语去AI化
        - 注意不要瞎编数据，必须依据我提供的数据进行分析
        - 且要注意用语去AI化，不要有思考过程，输出格式严格参考我的样例格式，不要分段或分点，就是一段话，每句话之间自然衔接。
        """
        try:
            res = (
                self.agent
                .general(system_prompt)
                .input({
                    "表格数据": data
                })
                .output("生成一段分析一下各大维度的大模型数据测评效果,400-500字")
                .start()
            )
            logger.debug(f"测评效果结果：{res}")
            return res
        except Exception as e:
            logger.error(f"测评效果结果失败：{e}")
            return ""
    

    # 05 国内外模型对比分析
    def generate_comparison_analysis(self, data: str) -> str:
        """
        生成国内外模型对比分析
        :param data: 平均得分对比表格数据  总分 国内87，国外98；维度一 国内89分，国外88分；维度二 国内88分，国外87分；维度三 国内87分，国外86分；维度四 国内86分，国外85分。
        :return: 对比分析
        """
        system_prompt = f"""
        请你结合国内外大模型总得分以及各个维度的平均得分对比表格数据，分析一下国内外大模型数据测评效果。
        
        ## 输出样例参考如下：
        4款国外深度研究产品的平均得分为63.41分，显著高于5款国内产品的平均分50.06分，两者分差达13.35分，反映出明显的性能差距。进一步拆解各项能力指标可以发现，国内外产品在“研究分析能力”和“规划咨询能力”两个维度上的得分相对接近，尤其在研究分析方面，国内产品得分为84.27分，与国外的84.89分基本持平，说明国内在语言理解和知识组织等核心算法方面已有一定积累。然而，在“深度检索能力”和“实践应用能力”这两个维度上，国内产品分别落后22.28分和23.89分，显示出在底层信息抓取能力和实际业务落地能力方面仍存在显著短板。整体来看，国内深度研究产品在部分核心能力上已具备一定竞争力，但在技术底座和工程化能力方面，与国外产品仍有较大提升空间。”输出的分析模板如下“国内外总得分平均值谁的更高，两者之间的差距在哪些维度
        
        ## 注意
        - 且输出的语言不要过于复杂，也不要字数过多，一两句话即可
        - 语言精炼且结论准确，且文字稳妥点，不要有太多评价，尤其是负面评价
        - 且要注意用语去AI化
        - 注意不要瞎编数据，必须依据我提供的数据进行分析
        """
        try:
            res = (
                self.agent
                .general(system_prompt)
                .input({
                    "表格数据": data
                })
                .output("生成一段分析一下国内外大模型数据测评效果,500-600字")
                .start()
            )
            logger.debug(f"测评效果结果：{res}")
            return res
        except Exception as e:
            logger.error(f"测评效果结果失败：{e}")
            return ""



if __name__ == "__main__":
    eva = EvaReport()
    # requirement = "创建主观测评项目"
    # keywords = eva.extract_keywords(requirement)
    # print(keywords)

    # dimens = "陷阱诱导，逻辑悖论，细粒度事实，多跳推理"
    # keyword = "主观测评"
    # eva.generate_report_intro(dimens, keyword)

    models_score = "DeepSeek-R1总得分86.02；GPT-4.5总得分85.30；gemini-2.5总得分84；Claude 3.7总得分83；豆包总得分81；qwen-max总得分79"
    eva.generate_overall_analysis(models_score)
