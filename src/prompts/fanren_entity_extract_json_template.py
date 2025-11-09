#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
凡人小说实体提取逻辑提示词模板 (基于fast_graphrag设计模式)
用于提取小说文本中的各类实体 - 严格JSON格式输出
"""

from ..models import PromptTemplate

# 凡人实体提取 SystemMessage
FANREN_ENTITY_EXTRACTION_SYSTEM_TEMPLATE = PromptTemplate.create_template(
    template_key="FANREN_ENTITY_EXTRACTION_SYSTEM_TEMPLATE",
    version="1.0.0",
    description="凡人小说实体提取系统提示词 - 基于fast_graphrag设计模式",
    template_content="""# DOMAIN
修仙小说知识图谱构建 - 从《凡人修仙传》等修仙小说文本中提取核心实体及其关系，构建完整的修仙世界观知识图谱。

# GOAL
你的目标是从给定的修仙小说文本中，提取所有对理解故事发展、人物关系和世界观构建有价值的核心实体，并识别它们之间的关系。重点关注实体在剧情中的持久性和关联性。

# 可能的查询示例:
- "韩立在七玄门时遇到了谁？"
- "韩立修炼的第一个功法是什么？"
- "掌天瓶有什么特殊功能？"
- "韩立在黄枫谷的地位如何？"
- "墨大夫和韩立的关系是什么？"

# INSTRUCTIONS
1. **实体识别**: 精确识别并提取所有属于规定实体类型的重要实体。为每个实体提供简洁的描述，捕捉其在修仙世界观中的关键特征和剧情重要性。使用标准化的实体名称，确保一致性。

2. **关系发现**: 识别并描述所有已提取实体之间的关系。解决代词指代问题，确保关系描述清晰说明实体间的连接。关系应反映修仙小说特有的逻辑（如师徒、敌对、宗门归属、法宝归属等）。

3. **实体覆盖检查**: 验证每个识别的实体都至少参与一个关系。如果存在孤立实体，推断并添加关系将其连接到图谱中，即使关系是隐含的。

4. **输出格式: 严格有效的JSON**: 输出必须是严格有效的JSON格式。遵循所有标准JSON规则。JSON必须包含三个顶级列表："entities", "relationships", 和 "other_relationships"。每个列表项必须是具有必需字段的JSON对象（实体需要"name", "type", "desc"字段；关系需要"source", "target", "desc"字段），所有字段都必须是用双引号包围的JSON字符串。**绝对不允许使用单引号、方括号包围字符串、尾随逗号或markdown格式（如三个反引号）。** 无效的JSON输出是不可接受的。

# 7类核心实体类型说明
- **character**: 角色实体（主角、配角、反派、导师等有名字的角色）
- **state**: 状态实体（境界状态、位置状态、身份状态、健康状态等）
- **ability**: 能力实体（功法秘籍、法术神通、战斗技能、辅助技能等）
- **item**: 物品实体（法宝武器、丹药灵药、材料资源、符篆阵图等）
- **creature**: 生物实体（灵兽、妖兽、灵植、奇异生物、魔物等）
- **organization**: 组织实体（宗门势力、家族势力、商会组织、邪道势力等）
- **location**: 地点实体（城镇区域、修仙福地、危险区域、宗门驻地等）

# 示例输入数据
允许的实体类型: [character, state, ability, item, creature, organization, location]
文档: "韩立在七玄门中遇到了自己的第一个师傅墨大夫，墨大夫传授了他长春功，帮助他踏上了修仙之路。后来韩立加入了黄枫谷，在那里他修炼了青元剑诀，并获得了掌天瓶这个神秘的法宝。"

# 示例输出数据 (有效JSON - 不得偏离)
{{
  "entities": [
    {{"name": "韩立", "type": "character", "desc": "修仙小说的主角，资质平凡但意志坚定"}},
    {{"name": "墨大夫", "type": "character", "desc": "韩立的第一个师傅，传授长春功的引路人"}},
    {{"name": "七玄门", "type": "organization", "desc": "韩立最初接触的世俗武学门派"}},
    {{"name": "长春功", "type": "ability", "desc": "韩立修炼的第一部功法，基础修仙法门"}},
    {{"name": "黄枫谷", "type": "organization", "desc": "韩立加入的修仙宗门，正道门派之一"}},
    {{"name": "青元剑诀", "type": "ability", "desc": "韩立在黄枫谷修炼的主要剑法功法"}},
    {{"name": "掌天瓶", "type": "item", "desc": "韩立获得的神秘法宝，具有特殊时空能力"}},
    {{"name": "修仙之路", "type": "state", "desc": "韩立踏上修仙道路的状态转变"}}
  ],
  "relationships": [
    {{"source": "韩立", "target": "墨大夫", "desc": "墨大夫是韩立的第一个修仙师傅"}},
    {{"source": "韩立", "target": "七玄门", "desc": "韩立曾是七玄门的弟子"}},
    {{"source": "墨大夫", "target": "长春功", "desc": "墨大夫将长春功传授给韩立"}},
    {{"source": "韩立", "target": "长春功", "desc": "韩立通过长春功踏上修仙之路"}},
    {{"source": "韩立", "target": "黄枫谷", "desc": "韩立加入黄枫谷成为修仙弟子"}},
    {{"source": "韩立", "target": "青元剑诀", "desc": "韩立在黄枫谷修炼青元剑诀"}},
    {{"source": "韩立", "target": "掌天瓶", "desc": "韩立获得了掌天瓶这个神秘法宝"}}
  ],
  "other_relationships": [
    {{"source": "长春功", "target": "修仙之路", "desc": "长春功是韩立踏上修仙之路的基础功法"}},
    {{"source": "黄枫谷", "target": "青元剑诀", "desc": "青元剑诀是黄枫谷的重要功法之一"}}
  ]
}}""",
    required_params=[],  # 系统模板没有变量，只需要实体类型和输入文本
    language="zh",
    notes="基于fast_graphrag设计模式的实体提取系统提示词，支持JSON格式输出"
)

# 凡人实体提取 UserMessage 
FANREN_ENTITY_EXTRACTION_PROMPT_TEMPLATE = PromptTemplate.create_template(
    template_key="FANREN_ENTITY_EXTRACTION_PROMPT_TEMPLATE",
    version="1.0.0",
    description="凡人小说实体提取用户提示词",
    template_content="""**重要的JSON格式规则:**
- **按照示例输出包含所有识别实体和关系的严格有效JSON。**
- **不要使用方括号或单引号 `(}},],')` 来包围JSON中的字符串。**
- **确保列表或对象中没有尾随逗号。**
- **输出必须是单个有效的JSON对象。不要用三个反引号或任何其他markdown格式包装JSON输出。**

# 输入数据
<<ENTITY_TYPES_START>>
**实体类型**:
{entity_types}
<<ENTITY_TYPES_END>>

<<DOCUMENT_START>>
**文档**:
{input_text}
<<DOCUMENT_END>>

输出:""",
    required_params=["entity_types", "input_text"],
    language="zh",
    notes="用户提示词模板，用于实体提取请求，强调JSON格式要求"
)

# 继续提取提示词
FANREN_ENTITY_CONTINUE_EXTRACTION_TEMPLATE = PromptTemplate.create_template(
    template_key="FANREN_ENTITY_CONTINUE_EXTRACTION_TEMPLATE",
    version="1.0.0",
    description="凡人小说实体继续提取提示词",
    template_content="上次提取中遗漏了很多重要实体。请使用相同的格式添加它们，重点关注：\n1. 有名字的角色和他们的身份\n2. 提到的具体功法、法宝、丹药\n3. 重要的地点和宗门势力\n4. 修仙相关的状态变化",
    required_params=[],
    language="zh",
    notes="继续提取提示词，用于补充遗漏的实体信息"
)

# 提取完成检查提示词
FANREN_ENTITY_GLEANING_DONE_TEMPLATE = PromptTemplate.create_template(
    template_key="FANREN_ENTITY_GLEANING_DONE_TEMPLATE",
    version="1.0.0",
    description="凡人小说实体提取完成检查提示词",
    template_content="回顾检查是否所有重要实体都已被正确识别：如果已完成请回答done，如果仍有实体需要添加请继续。检查重点：\n- 主角、重要配角、反派的完整信息\n- 重要的功法、法宝、丹药\n- 关键的修仙地点和宗门势力\n- 境界提升、重要事件等状态变化",
    required_params=[],
    language="zh",
    notes="提取完成检查提示词，用于确认所有重要实体都已识别"
)

# 实体描述总结提示词
FANREN_SUMMARIZE_ENTITY_DESCRIPTIONS_TEMPLATE = PromptTemplate.create_template(
    template_key="FANREN_SUMMARIZE_ENTITY_DESCRIPTIONS_TEMPLATE",
    version="1.0.0",
    description="凡人小说实体描述总结提示词",
    template_content="""你是一个专门分析修仙小说的助手，负责对提供的实体描述进行总结。

根据当前描述，通过移除冗余和通用信息来总结它。解决任何矛盾并提供一个单一、连贯的摘要。
使用第三人称写作，明确包含实体名称以保持完整的上下文。
重点关注实体在修仙世界观中的作用和剧情重要性。

当前描述:
{description}

更新后的描述:""",
    required_params=["description"],
    language="zh",
    notes="实体描述总结提示词，用于精炼和统一实体描述"
)

# 关系分组相似性提示词
FANREN_EDGES_GROUP_SIMILAR_TEMPLATE = PromptTemplate.create_template(
    template_key="FANREN_EDGES_GROUP_SIMILAR_TEMPLATE",
    version="1.0.0",
    description="凡人小说关系分组相似性提示词",
    template_content="""你是一个负责维护描述两个实体之间关系事实列表的助手，以确保信息不冗余。

给定ID和事实列表，识别任何应该分组在一起的事实，因为它们包含相似或重复的信息，并为该组提供新的总结描述。

# 示例
事实 (ID, 描述):
0, 韩立是墨大夫的弟子
1, 墨大夫教导韩立修仙
2, 韩立从墨大夫那里学到长春功
3, 墨大夫收韩立为徒

输出:
{{
  grouped_facts: [
    {{
      'ids': [0, 1, 3],
      'description': '墨大夫收韩立为弟子，教导他修仙基础'
    }},
    {{
      'ids': [2],
      'description': '韩立从墨大夫那里学到长春功'
    }}
  ]
}}

# 输入:
事实:
{edge_list}

输出:""",
    required_params=["edge_list"],
    language="zh",
    notes="关系分组相似性提示词，用于合并重复或相似的关系信息"
)

# 查询实体提取提示词
FANREN_ENTITY_EXTRACTION_QUERY_TEMPLATE = PromptTemplate.create_template(
    template_key="FANREN_ENTITY_EXTRACTION_QUERY_TEMPLATE",
    version="1.0.0",
    description="凡人小说查询实体提取提示词",
    template_content="""根据下面的查询，你的任务是提取所有与执行信息检索以产生答案相关的实体。

-示例1-
查询: 韩立在七玄门时遇到了谁？
输出: {{"named": ["[角色] 韩立", "[组织] 七玄门"], "generic": ["遇到的人", "七玄门成员"]}}

-示例2-
查询: 韩立修炼的第一个功法是什么？
输出: {{"named": ["[角色] 韩立"], "generic": ["第一个功法", "修仙功法"]}}

-输入-
查询: {query}
输出:""",
    required_params=["query"],
    language="zh",
    notes="查询实体提取提示词，用于从用户查询中提取相关实体"
)

# 带引用的响应生成提示词
FANREN_GENERATE_RESPONSE_WITH_REFERENCES_TEMPLATE = PromptTemplate.create_template(
    template_key="FANREN_GENERATE_RESPONSE_WITH_REFERENCES_TEMPLATE",
    version="1.0.0",
    description="凡人小说带引用的响应生成提示词",
    template_content="""你是一个专门分析修仙小说数据的助手，为用户查询提供有用的响应。

# 输入数据
{context}

# 用户查询
{query}

# 指令
你的目标是使用输入数据中的相关信息为用户查询提供响应：
- "实体"和"关系"表包含高层次信息。使用这些表来识别回答查询最重要的实体和关系。
- "源"列表包含帮助回答查询的原始文本源。它可能包含噪声数据，所以在分析时要注意。

遵循以下步骤：
1. 阅读并理解用户查询。
2. 查看"实体"和"关系"表以获得数据的一般感觉，并理解哪些信息最相关来回答查询。
3. 仔细分析所有"源"以获得更详细的信息。信息可能分散在多个源中，使用识别的相关实体和关系来指导你对源的分析。
4. 在编写响应时，你必须在每句话末尾通过附加 `[<source_id>]` 来包含你正在使用的所有源的内联引用，其中 `source_id` 是"源"列表中对应的源ID。
5. 根据你收集的信息编写用户查询的响应 - 必须包含内联引用。非常简洁并直接回答用户查询。如果无法从输入数据推断响应，就说没有找到相关信息。不要编造任何内容或添加不相关信息。

答案:""",
    required_params=["context", "query"],
    language="zh",
    notes="带引用的响应生成提示词，生成带有源引用的答案响应"
)

# 无引用的响应生成提示词
FANREN_GENERATE_RESPONSE_NO_REFERENCES_TEMPLATE = PromptTemplate.create_template(
    template_key="FANREN_GENERATE_RESPONSE_NO_REFERENCES_TEMPLATE",
    version="1.0.0",
    description="凡人小说无引用的响应生成提示词",
    template_content="""你是一个专门分析修仙小说数据的助手，为用户查询提供有用的响应。

# 输入数据
{context}

# 用户查询
{query}

# 指令
你的目标是使用输入数据中的相关信息为用户查询提供响应：
- "实体"和"关系"表包含高层次信息。使用这些表来识别回答查询最重要的实体和关系。
- "源"列表包含帮助回答查询的原始文本源。它可能包含噪声数据，所以在分析时要注意。

遵循以下步骤：
1. 阅读并理解用户查询。
2. 查看"实体"和"关系"表以获得数据的一般感觉，并理解哪些信息最相关来回答查询。
3. 仔细分析所有"源"以获得更详细的信息。信息可能分散在多个源中，使用识别的相关实体和关系来指导你对源的分析。
4. 根据你收集的信息编写用户查询的响应。非常简洁并直接回答用户查询。如果无法从输入数据推断响应，就说没有找到相关信息。不要编造任何内容或添加不相关信息。

答案:""",
    required_params=["context", "query"],
    language="zh",
    notes="无引用的响应生成提示词，生成简洁的答案响应"
)

# 失败响应提示词
FANREN_FAIL_RESPONSE_TEMPLATE = PromptTemplate.create_template(
    template_key="FANREN_FAIL_RESPONSE_TEMPLATE",
    version="1.0.0",
    description="凡人小说失败响应提示词",
    template_content="抱歉，我无法为那个问题提供答案。",
    required_params=[],
    language="zh",
    notes="失败响应提示词，用于无法回答查询时的固定回复"
)