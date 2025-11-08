#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试 Structured Output 问题
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import EntityListResponse
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_simple_structured_output():
    """测试简单的结构化输出"""
    print("=== 调试 Structured Output ===")

    # 初始化模型
    model_name = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    print(f"使用模型: {model_name}")

    if model_name.startswith("kimi"):
        llm = init_chat_model(model_name, model_provider="openai")
    else:
        llm = init_chat_model(model_name)

    # 创建结构化输出模型
    structured_llm = llm.with_structured_output(EntityListResponse)

    # 简单的测试提示
    system_prompt = """你是一个实体提取助手。请从文本中提取实体，并按照指定的JSON格式返回。"""

    user_prompt = """请从以下文本中提取实体：

韩立是一个少年，住在青州的小山村。他加入了七玄门学习修仙。"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    print("发送请求...")

    try:
        result = structured_llm.invoke(messages)
        print(f"成功获得结果:")
        print(f"类型: {type(result)}")
        print(f"内容: {result}")

        if hasattr(result, 'entities'):
            print(f"entities 属性: {result.entities}")
            print(f"entities 类型: {type(result.entities)}")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_structured_output()