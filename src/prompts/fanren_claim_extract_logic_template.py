#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
凡人小说claim提取逻辑提示词模板
用于提取小说文本中的论点、观点、主张
"""

from ..models import PromptTemplate
from .constants import TUPLE_DELIMITER, RECORD_DELIMITER, COMPLETION_DELIMITER

# 凡人claim提取逻辑提示词模板
FANREN_CLAIM_EXTRACT_LOGIC_TEMPLATE = PromptTemplate.create_template(
    template_key="FANREN_CLAIM_EXTRACT_LOGIC_TEMPLATE",
    version="0.0.0",
    description="凡人小说中的claim（论点、观点、主张）提取逻辑模板",
    template_content=f"""你是一个专门分析修仙小说的智能助手,帮助从修仙小说文本中提取具有叙事价值的陈述性事实。

========================================
目标
========================================
给定一段修仙小说文本和实体列表,提取所有与这些实体相关的、对理解故事发展有价值的陈述性事实。

========================================
核心原则
========================================
修仙小说的陈述提取应关注:
1. 实力体系: 展现角色强弱对比、能力边界
2. 因果逻辑: 行动→代价→结果的完整链条
3. 身份认知: 角色地位、声望、特殊身份
4. 叙事功能: 该陈述在推动情节、制造冲突、揭示信息方面的作用

========================================
陈述类型定义
========================================

类型1: 实力对比陈述
展现角色之间的强弱关系、战斗结果
示例: "韩立一击击伤号称魔族第一魔尊的大汉"

类型2: 能力边界陈述
说明角色能做什么、不能做什么、掌握程度如何
示例: "韩立掌握涅槃圣体但未完全修成"

类型3: 代价成本陈述
展现行动需要付出的代价、副作用、风险
示例: "强行催动神通导致韩立遭受反噬吐血"

类型4: 身份地位陈述
说明角色的身份、称号、在世界观中的位置
示例: "魔族大汉号称魔族第一魔尊"

类型5: 认知震惊陈述
角色对某事的惊讶、怀疑、误判,揭示信息差
示例: "魔族大汉震惊于人族能修成圣界神通"

类型6: 因果链条陈述
完整的因果关系: 原因→行动→结果
示例: "因未完全修成→强行催动→遭受反噬"

类型7: 状态转变陈述
角色形态、境界、处境的变化过程
示例: "韩立从金色人影变为双头四臂形态"

========================================
提取步骤
========================================

步骤1: 识别关键实体
从文本中识别所有符合以下类别的实体:
- 角色: 修士、魔族、妖兽等有名字或称号的存在
- 神通/功法: 涅槃圣体、化血神刀等特殊能力
- 法宝/物品: 宝物、灵药、法器等
- 势力/组织: 宗门、种族、联盟等
- 境界/等级: 元婴期、化神期等修炼阶段

步骤2: 提取陈述事实
对每个关键实体,提取与其相关的陈述,包含以下信息:

- 陈述主体: 陈述的核心实体,大写
- 陈述类型: 从上述7种类型中选择最匹配的
- 陈述内容: 用一句话概括陈述的核心事实
- 证据强度: 
  * 明确描写 - 叙述者直接描写的事实
  * 角色陈述 - 角色说出的话(可能有主观性)
  * 暗示推断 - 从情节中推断出的事实
- 原文引用: 支持该陈述的所有原文片段
- 叙事功能: 该陈述的作用(展示实力/制造悬念/推动情节/揭示信息/建立对比/埋下伏笔)
- 关联实体: 陈述中涉及的其他实体,用逗号分隔

步骤3: 识别因果链条
如果多个陈述之间存在因果关系,标注出完整的因果链:
- 因果链ID: 用数字标识(如 CHAIN_1)
- 链条步骤: 按顺序列出因→果的陈述

步骤4: 输出格式
每个陈述使用以下格式:

(<陈述主体>{TUPLE_DELIMITER}<陈述类型>{TUPLE_DELIMITER}<陈述内容>{TUPLE_DELIMITER}<证据强度>{TUPLE_DELIMITER}<原文引用>{TUPLE_DELIMITER}<叙事功能>{TUPLE_DELIMITER}<关联实体>{TUPLE_DELIMITER}<因果链ID>)

多个陈述之间用 {RECORD_DELIMITER} 分隔

完成后输出 {COMPLETION_DELIMITER}

========================================
示例
========================================

示例1:

实体列表: 韩立, 魔族大汉, 涅槃圣体
文本: 韩立施展涅槃圣体神通,以万元之力攻击魔族大汉。金色巨掌落下,一击就将号称魔族第一魔尊的大汉击伤,使其口吐精血。大汉惊呼道:"涅槃圣体,万元之力!不可能,区区一名人族怎可能修成我们圣界的无上神通。"

输出:

(韩立{TUPLE_DELIMITER}实力对比陈述{TUPLE_DELIMITER}韩立一击击伤号称魔族第一魔尊的魔族大汉{TUPLE_DELIMITER}明确描写{TUPLE_DELIMITER}金色巨掌落下,一击就将号称魔族第一魔尊的大汉击伤,使其口吐精血{TUPLE_DELIMITER}展示实力,建立对比{TUPLE_DELIMITER}魔族大汉,涅槃圣体{TUPLE_DELIMITER}无)
{RECORD_DELIMITER}
(魔族大汉{TUPLE_DELIMITER}身份地位陈述{TUPLE_DELIMITER}魔族大汉号称魔族第一魔尊{TUPLE_DELIMITER}明确描写{TUPLE_DELIMITER}号称魔族第一魔尊的大汉{TUPLE_DELIMITER}建立对比,强化韩立战绩的含金量{TUPLE_DELIMITER}无{TUPLE_DELIMITER}无)
{RECORD_DELIMITER}
(涅槃圣体{TUPLE_DELIMITER}身份地位陈述{TUPLE_DELIMITER}涅槃圣体是圣界的无上神通{TUPLE_DELIMITER}角色陈述{TUPLE_DELIMITER}区区一名人族怎可能修成我们圣界的无上神通{TUPLE_DELIMITER}揭示信息,说明神通的珍贵性{TUPLE_DELIMITER}韩立{TUPLE_DELIMITER}无)
{RECORD_DELIMITER}
(魔族大汉{TUPLE_DELIMITER}认知震惊陈述{TUPLE_DELIMITER}魔族大汉震惊于人族韩立能修成圣界无上神通{TUPLE_DELIMITER}角色陈述{TUPLE_DELIMITER}大汉惊呼道:"涅槃圣体,万元之力!不可能,区区一名人族怎可能修成我们圣界的无上神通。"{TUPLE_DELIMITER}制造悬念,揭示信息差{TUPLE_DELIMITER}韩立,涅槃圣体{TUPLE_DELIMITER}无)
{COMPLETION_DELIMITER}

示例2:

实体列表: 韩立, 魔族大汉, 涅槃圣体
文本: 韩立施展涅槃圣体神通,以万元之力攻击魔族大汉。金色巨掌落下,一击就将号称魔族第一魔尊的大汉击伤。韩立虽然击伤了对手,但也口吐金色精血,显然遭受了反噬之力。魔族大汉惊呼:"你并没有修成这无上神通,只是强行催动而已!"

输出:

(韩立{TUPLE_DELIMITER}实力对比陈述{TUPLE_DELIMITER}韩立一击击伤号称魔族第一魔尊的魔族大汉{TUPLE_DELIMITER}明确描写{TUPLE_DELIMITER}金色巨掌落下,一击就将号称魔族第一魔尊的大汉击伤{TUPLE_DELIMITER}展示实力{TUPLE_DELIMITER}魔族大汉,涅槃圣体{TUPLE_DELIMITER}CHAIN_1)
{RECORD_DELIMITER}
(韩立{TUPLE_DELIMITER}能力边界陈述{TUPLE_DELIMITER}韩立并未完全修成涅槃圣体,只是强行催动{TUPLE_DELIMITER}角色陈述{TUPLE_DELIMITER}你并没有修成这无上神通,只是强行催动而已{TUPLE_DELIMITER}揭示信息,说明能力限制{TUPLE_DELIMITER}涅槃圣体{TUPLE_DELIMITER}CHAIN_1)
{RECORD_DELIMITER}
(韩立{TUPLE_DELIMITER}代价成本陈述{TUPLE_DELIMITER}韩立强行催动神通遭受反噬吐出金色精血{TUPLE_DELIMITER}明确描写{TUPLE_DELIMITER}韩立虽然击伤了对手,但也口吐金色精血,显然遭受了反噬之力{TUPLE_DELIMITER}展示代价,埋下隐患{TUPLE_DELIMITER}涅槃圣体{TUPLE_DELIMITER}CHAIN_1)
{RECORD_DELIMITER}
(韩立{TUPLE_DELIMITER}因果链条陈述{TUPLE_DELIMITER}因未完全修成涅槃圣体而强行催动导致遭受反噬{TUPLE_DELIMITER}明确描写+角色陈述{TUPLE_DELIMITER}韩立虽然击伤了对手,但也口吐金色精血,显然遭受了反噬之力。魔族大汉惊呼:"你并没有修成这无上神通,只是强行催动而已!"{TUPLE_DELIMITER}揭示因果逻辑,展现修仙世界规则{TUPLE_DELIMITER}涅槃圣体{TUPLE_DELIMITER}CHAIN_1)
{COMPLETION_DELIMITER}

========================================
实际数据
========================================

实体列表: {{entity_specs}}
文本: {{input_text}}

输出:""",
    required_params=["entity_specs", "claim_description", "input_text"],
    language="zh",
    notes="初始版本，用于修仙小说陈述性事实提取，关注实力体系、因果逻辑、身份认知和叙事功能"
)