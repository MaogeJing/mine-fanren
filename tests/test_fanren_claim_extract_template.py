#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
凡人claim提取逻辑提示词模板演示
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.prompts.fanren_claim_extract_logic_template import FANREN_CLAIM_EXTRACT_LOGIC_TEMPLATE
from src.prompts.constants import TUPLE_DELIMITER, RECORD_DELIMITER, COMPLETION_DELIMITER


def demo_template():
    """演示提示词模板的使用效果"""

    print("=== 凡人claim提取逻辑提示词模板演示 ===\n")

    # 显示模板基本信息
    print(f"模板Key: {FANREN_CLAIM_EXTRACT_LOGIC_TEMPLATE.template_key}")
    print(f"版本: {FANREN_CLAIM_EXTRACT_LOGIC_TEMPLATE.version}")
    print(f"语言: {FANREN_CLAIM_EXTRACT_LOGIC_TEMPLATE.language}")
    print(f"必需参数: {FANREN_CLAIM_EXTRACT_LOGIC_TEMPLATE.required_params}")
    print(f"描述: {FANREN_CLAIM_EXTRACT_LOGIC_TEMPLATE.description}")
    print()

    # 显示常量值
    print("=== 系统常量 ===")
    print(f"TUPLE_DELIMITER = '{TUPLE_DELIMITER}'")
    print(f"RECORD_DELIMITER = '{RECORD_DELIMITER}'")
    print(f"COMPLETION_DELIMITER = '{COMPLETION_DELIMITER}'")
    print()

    # 示例1: 基本使用
    print("=== 示例1: 战斗事件提取 ===")
    params1 = {
        "entity_specs": "韩立, 魔族大汉, 涅槃圣体",
        "claim_description": "修仙小说陈述性事实提取",
        "input_text": "韩立施展涅槃圣体神通,以万元之力攻击魔族大汉。金色巨掌落下,一击就将号称魔族第一魔尊的大汉击伤,使其口吐精血。大汉惊呼道:\"涅槃圣体,万元之力!不可能,区区一名人族怎可能修成我们圣界的无上神通。\""
    }

    rendered1 = FANREN_CLAIM_EXTRACT_LOGIC_TEMPLATE.render(**params1)
    print(rendered1)
    print("\n" + "="*80 + "\n")

    # 示例2: 多实体分析
    print("=== 示例2: 修炼成就和战斗结果 ===")
    params2 = {
        "entity_specs": "韩立, 魔族大汉, 涅槃圣体",
        "claim_description": "修仙小说陈述性事实提取",
        "input_text": "韩立施展涅槃圣体神通,以万元之力攻击魔族大汉。金色巨掌落下,一击就将号称魔族第一魔尊的大汉击伤。韩立虽然击伤了对手,但也口吐金色精血,显然遭受了反噬之力。魔族大汉惊呼:\"你并没有修成这无上神通,只是强行催动而已!\""
    }

    rendered2 = FANREN_CLAIM_EXTRACT_LOGIC_TEMPLATE.render(**params2)
    print(rendered2)
    print("\n" + "="*80 + "\n")

    # 示例3: 简单文本测试
    print("=== 示例3: 简单测试 ===")
    params3 = {
        "entity_specs": "韩立",
        "claim_description": "修仙小说陈述性事实提取",
        "input_text": "经过十年苦修,韩立终于突破到筑基期,实力大增。"
    }

    rendered3 = FANREN_CLAIM_EXTRACT_LOGIC_TEMPLATE.render(**params3)
    print(rendered3)


if __name__ == "__main__":
    demo_template()