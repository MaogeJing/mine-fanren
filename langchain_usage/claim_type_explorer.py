#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修仙小说事实提取评估器
基于6个核心原则评估文本片段的事实提取效果
"""

import os
import sys
import random
import argparse
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


# 添加项目根目录到 Python 路径，以便导入依赖的模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.chapter_chunk_extractor_fanren_impl import ChapterChunkExtractor
from src.models import ChapterChunk

@dataclass
class TextFragment:
    """文本片段"""
    fragment_id: str
    chapter_id: int
    chapter_title: str
    content: str
    start_pos: int
    end_pos: int
    entities_mentioned: List[str]


@dataclass
class FactExtractionResult:
    """事实提取结果"""
    fragment_id: str
    original_content: str

    # 6个核心原则的提取结果
    strength_system_facts: List[str]  # 实力体系
    resource_flow_facts: List[str]    # 资源流转
    relationship_facts: List[str]     # 关系网络
    identity_facts: List[str]         # 身份认知
    combat_process_facts: List[str]   # 战斗过程
    narrative_function_facts: List[str] # 叙事功能

    # 评估指标
    coverage_score: float  # 覆盖度得分 (0-100)
    completeness_score: float  # 完整性得分 (0-100)
    quality_score: float  # 质量得分 (0-100)

    # 问题识别
    missing_aspects: List[str]  # 缺失的方面
    extraction_issues: List[str]  # 提取问题
    suggestions: List[str]  # 改进建议


class FactExtractionEvaluator:
    """事实提取评估器"""

  # 事实提取评估提示词模板
    FACT_EXTRACTION_EVALUATION_PROMPT = """
-Goal-
基于修仙小说事实提取的6个核心原则，分析给定文本片段，评估当前事实提取的覆盖度和完整性。

-6个核心原则-
修仙小说的事实提取应关注以下6个方面：

1. 实力体系：展现角色强弱对比、能力边界、成长轨迹
2. 资源流转：法宝、灵药、材料的获得与损失
3. 关系网络：结盟、结仇、师徒、情感关系
4. 身份认知：角色地位、声望、特殊身份、马甲系统
5. 战斗过程：完整战斗的关键节点与策略
6. 叙事功能：该事实在推动情节、制造冲突、揭示信息方面的作用

-Analysis Steps-
1. 识别文本中的关键实体（角色、物品、地点、势力等）
2. 逐一分析文本内容对应6个核心原则中的哪些方面
3. 提取每个方面的事实信息
4. 识别可能被遗漏的重要事实
5. 评估当前提取的覆盖度和质量

-Output Format-
请按以下格式输出：

=== 实力体系事实 ===
- [事实1]: 具体内容描述
- [事实2]: 具体内容描述
...

=== 资源流转事实 ===
- [事实1]: 具体内容描述
- [事实2]: 具体内容描述
...

=== 关系网络事实 ===
- [事实1]: 具体内容描述
- [事实2]: 具体内容描述
...

=== 身份认知事实 ===
- [事实1]: 具体内容描述
- [事实2]: 具体内容描述
...

=== 战斗过程事实 ===
- [事实1]: 具体内容描述
- [事实2]: 具体内容描述
...

=== 叙事功能事实 ===
- [事实1]: 具体内容描述
- [事实2]: 具体内容描述
...

=== 遗漏识别 ===
- [遗漏事实1]: 应该提取但遗漏的内容
- [遗漏事实2]: 应该提取但遗漏的内容
...

=== 质量评估 ===
覆盖度得分: [0-100分]
完整性得分: [0-100分]
主要问题: [问题描述]
改进建议: [具体建议]

-Real Data-
文本片段: {fragment_content}
章节: 第{chapter_id}章 {chapter_title}
提及的实体: {entities_mentioned}

Output:"""

    # 片段总结提示词
    FRAGMENT_SUMMARY_PROMPT = """
-Goal-
基于多个片段的分析结果，总结陈述类型定义的改进方案。

-Analysis Task-
分析以下探索结果，找出陈述类型定义的系统性问题和改进机会：

{exploration_results}

-Output Requirements-
1. 总结现有定义的主要不足
2. 识别缺失的陈述类型类别
3. 提出完整的类型定义修订方案
4. 给出新定义的示例和边界说明

输出格式：
=== 发现的问题 ===
1. [问题描述]
2. [问题描述]
...

=== 缺失的类型 ===
1. [新类型名称]: [定义和示例]
2. [新类型名称]: [定义和示例]
...

=== 修订后的完整类型定义 ===
[提供完整的修订版类型定义]
"""

    def __init__(self):
        """初始化评估器"""
        load_dotenv()
        self.llm = ChatOpenAI(
            model="kimi-k2-0905-preview",
            temperature=0.2,  # 稍微提高温度以获得更有创意的分析
        )
        self.evaluation_results: List[FactExtractionResult] = []

    def sample_random_fragments(self, novel_name: str, raw_text: str,
                               count: int = 10, min_length: int = 100,
                               max_length: int = 500) -> List[TextFragment]:
        """
        随机采样文本片段

        Args:
            novel_name: 小说名称
            raw_text: 原始文本
            count: 采样数量
            min_length: 片段最小长度
            max_length: 片段最大长度

        Returns:
            List[TextFragment]: 采样到的文本片段列表
        """
        print("正在提取章节...")
        chunks = ChapterChunkExtractor.extract_chapter_chunks(novel_name, raw_text)

        # 过滤出有内容的章节
        valid_chunks = [chunk for chunk in chunks if chunk.token_count > 0]
        print(f"找到 {len(valid_chunks)} 个有效章节")

        fragments = []
        fragment_id = 0

        # 从每个章节中随机采样片段
        sampled_chunks = random.sample(valid_chunks, min(count, len(valid_chunks)))

        for chunk in sampled_chunks:
            content = chunk.content
            if len(content) < min_length:
                continue

            # 随机选择一个起始位置
            max_start = max(0, len(content) - max_length)
            start_pos = random.randint(0, max_start) if max_start > 0 else 0

            # 确定结束位置
            end_pos = min(start_pos + max_length, len(content))
            fragment_content = content[start_pos:end_pos]

            # 确保片段长度满足最小要求
            if len(fragment_content) < min_length:
                # 尝试扩展到最小长度
                end_pos = min(start_pos + min_length, len(content))
                fragment_content = content[start_pos:end_pos]

            # 简单提取实体（这里可以根据需要改进）
            entities = self._extract_simple_entities(fragment_content)

            fragment = TextFragment(
                fragment_id=f"FRAG_{fragment_id:03d}",
                chapter_id=chunk.chapter_id,
                chapter_title=chunk.chapter_title,
                content=fragment_content,
                start_pos=start_pos,
                end_pos=end_pos,
                entities_mentioned=entities
            )

            fragments.append(fragment)
            fragment_id += 1
            print(f"采样片段 {fragment.fragment_id}: 第{chunk.chapter_id}章 ({len(fragment_content)} 字符)")

        print(f"成功采样 {len(fragments)} 个文本片段")
        return fragments

    def _extract_simple_entities(self, text: str) -> List[str]:
        """
        简单的实体提取（可以后续优化）

        Args:
            text: 文本内容

        Returns:
            List[str]: 提取到的实体列表
        """
        # 这里使用简单的规则，实际应用中可以使用更复杂的NLP方法
        entities = []

        # 常见的修仙小说词汇
        common_terms = [
            "韩立", "南宫婉", "紫灵", "元瑶",  # 人名
            "涅槃圣体", "化血神刀", "青元剑诀",  # 功法神通
            "元婴期", "化神期", "炼虚期",  # 境界
            "天南", "乱星海", "大晋",  # 地点
        ]

        for term in common_terms:
            if term in text:
                entities.append(term)

        return list(set(entities))  # 去重

    def evaluate_fragment(self, fragment: TextFragment) -> FactExtractionResult:
        """
        评估单个文本片段的事实提取效果

        Args:
            fragment: 文本片段

        Returns:
            FactExtractionResult: 评估结果
        """
        print(f"正在评估片段 {fragment.fragment_id}...")

        system_prompt = self.FACT_EXTRACTION_EVALUATION_PROMPT.format(
            fragment_content=fragment.content,
            chapter_id=fragment.chapter_id,
            chapter_title=fragment.chapter_title,
            entities_mentioned=', '.join(fragment.entities_mentioned)
        )

        user_prompt = f"""请基于6个核心原则评估这个文本片段的事实提取效果。

片段ID: {fragment.fragment_id}
章节: 第{fragment.chapter_id}章 {fragment.chapter_title}
提及的实体: {', '.join(fragment.entities_mentioned)}

请分析各个原则下的事实提取情况，识别遗漏，并给出质量评估。"""

        # 调用LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        evaluation_text = response.content  # type: ignore

        # 解析评估结果
        result = self._parse_evaluation_result(fragment, evaluation_text)

        print(f"片段 {fragment.fragment_id} 评估完成")
        return result

    def _parse_evaluation_result(self, fragment: TextFragment, evaluation_text: str) -> FactExtractionResult:
        """
        解析AI评估结果

        Args:
            fragment: 文本片段
            evaluation_text: AI返回的评估文本

        Returns:
            FactExtractionResult: 解析后的结果
        """
        lines = evaluation_text.split('\n')

        result = FactExtractionResult(
            fragment_id=fragment.fragment_id,
            original_content=fragment.content,
            strength_system_facts=[],
            resource_flow_facts=[],
            relationship_facts=[],
            identity_facts=[],
            combat_process_facts=[],
            narrative_function_facts=[],
            coverage_score=0.0,
            completeness_score=0.0,
            quality_score=0.0,
            missing_aspects=[],
            extraction_issues=[],
            suggestions=[]
        )

        current_section = None

        for line in lines:
            line = line.strip()

            # 识别各个事实类型部分
            if line.startswith('=== 实力体系事实 ==='):
                current_section = 'strength_system'
            elif line.startswith('=== 资源流转事实 ==='):
                current_section = 'resource_flow'
            elif line.startswith('=== 关系网络事实 ==='):
                current_section = 'relationship'
            elif line.startswith('=== 身份认知事实 ==='):
                current_section = 'identity'
            elif line.startswith('=== 战斗过程事实 ==='):
                current_section = 'combat_process'
            elif line.startswith('=== 叙事功能事实 ==='):
                current_section = 'narrative_function'
            elif line.startswith('=== 遗漏识别 ==='):
                current_section = 'missing'
            elif line.startswith('=== 质量评估 ==='):
                current_section = 'evaluation'
            # 解析各类事实
            elif line.startswith('- [事实') and current_section in ['strength_system', 'resource_flow', 'relationship', 'identity', 'combat_process', 'narrative_function']:
                fact_content = line
                if current_section == 'strength_system':
                    result.strength_system_facts.append(fact_content)
                elif current_section == 'resource_flow':
                    result.resource_flow_facts.append(fact_content)
                elif current_section == 'relationship':
                    result.relationship_facts.append(fact_content)
                elif current_section == 'identity':
                    result.identity_facts.append(fact_content)
                elif current_section == 'combat_process':
                    result.combat_process_facts.append(fact_content)
                elif current_section == 'narrative_function':
                    result.narrative_function_facts.append(fact_content)
            # 解析遗漏事项
            elif line.startswith('- [遗漏事实') and current_section == 'missing':
                result.missing_aspects.append(line)
            # 解析评估得分
            elif line.startswith('覆盖度得分:') and current_section == 'evaluation':
                try:
                    score_str = line.split(':')[1].strip()
                    result.coverage_score = float(''.join(filter(lambda x: x.isdigit() or x == '.', score_str)))
                except:
                    pass
            elif line.startswith('完整性得分:') and current_section == 'evaluation':
                try:
                    score_str = line.split(':')[1].strip()
                    result.completeness_score = float(''.join(filter(lambda x: x.isdigit() or x == '.', score_str)))
                except:
                    pass
            elif line.startswith('主要问题:') and current_section == 'evaluation':
                problem = line.replace('主要问题:', '').strip()
                if problem:
                    result.extraction_issues.append(problem)
            elif line.startswith('改进建议:') and current_section == 'evaluation':
                suggestion = line.replace('改进建议:', '').strip()
                if suggestion:
                    result.suggestions.append(suggestion)

        # 计算质量得分
        result.quality_score = (result.coverage_score + result.completeness_score) / 2

        return result

    def run_evaluation(self, novel_file: str = "resources/ignored/1.txt",
                       novel_name: str = "fanren", fragment_count: int = 10):
        """
        运行完整的事实提取评估流程

        Args:
            novel_file: 小说文件路径
            novel_name: 小说名称
            fragment_count: 片段数量
        """
        print(f"读取小说文件: {novel_file}")

        # 读取小说文本
        try:
            with open(novel_file, 'r', encoding='gb18030') as f:
                raw_text = f.read()
        except UnicodeDecodeError:
            try:
                with open(novel_file, 'r', encoding='gbk') as f:
                    raw_text = f.read()
            except UnicodeDecodeError:
                with open(novel_file, 'r', encoding='utf-8', errors='ignore') as f:
                    raw_text = f.read()

        print(f"文件读取完成，总字符数: {len(raw_text)}")
        print("=" * 60)
        print("开始事实提取评估...")
        print("=" * 60)

        # 第一步：随机采样片段
        fragments = self.sample_random_fragments(novel_name, raw_text, fragment_count)

        if not fragments:
            print("未能采样到有效的文本片段")
            return

        print("\n" + "=" * 60)
        print("开始评估片段...")
        print("=" * 60)

        # 第二步：逐个评估片段
        for i, fragment in enumerate(fragments, 1):
            print(f"\n[{i}/{len(fragments)}] 评估片段 {fragment.fragment_id}")
            print(f"内容预览: {fragment.content[:100]}...")

            result = self.evaluate_fragment(fragment)
            self.evaluation_results.append(result)

            print(f"  - 实力体系事实: {len(result.strength_system_facts)} 个")
            print(f"  - 资源流转事实: {len(result.resource_flow_facts)} 个")
            print(f"  - 关系网络事实: {len(result.relationship_facts)} 个")
            print(f"  - 身份认知事实: {len(result.identity_facts)} 个")
            print(f"  - 战斗过程事实: {len(result.combat_process_facts)} 个")
            print(f"  - 叙事功能事实: {len(result.narrative_function_facts)} 个")
            print(f"  - 覆盖度得分: {result.coverage_score:.1f}/100")
            print(f"  - 完整性得分: {result.completeness_score:.1f}/100")
            print(f"  - 质量得分: {result.quality_score:.1f}/100")

        # 第三步：总结评估结果
        self._summarize_evaluation()

        # 第四步：生成改进建议
        self._generate_improvement_suggestions()

    def _summarize_evaluation(self):
        """总结评估结果"""
        print("\n" + "=" * 60)
        print("事实提取评估结果汇总")
        print("=" * 60)

        if not self.evaluation_results:
            print("没有评估结果")
            return

        # 统计各类事实数量
        total_strength = sum(len(r.strength_system_facts) for r in self.evaluation_results)
        total_resource = sum(len(r.resource_flow_facts) for r in self.evaluation_results)
        total_relationship = sum(len(r.relationship_facts) for r in self.evaluation_results)
        total_identity = sum(len(r.identity_facts) for r in self.evaluation_results)
        total_combat = sum(len(r.combat_process_facts) for r in self.evaluation_results)
        total_narrative = sum(len(r.narrative_function_facts) for r in self.evaluation_results)

        # 计算平均得分
        avg_coverage = sum(r.coverage_score for r in self.evaluation_results) / len(self.evaluation_results)
        avg_completeness = sum(r.completeness_score for r in self.evaluation_results) / len(self.evaluation_results)
        avg_quality = sum(r.quality_score for r in self.evaluation_results) / len(self.evaluation_results)

        # 统计问题
        all_issues = []
        all_missing = []
        all_suggestions = []
        for result in self.evaluation_results:
            all_issues.extend(result.extraction_issues)
            all_missing.extend(result.missing_aspects)
            all_suggestions.extend(result.suggestions)

        print(f"评估片段数: {len(self.evaluation_results)}")
        print(f"\n=== 各类事实提取统计 ===")
        print(f"实力体系事实: {total_strength} 个")
        print(f"资源流转事实: {total_resource} 个")
        print(f"关系网络事实: {total_relationship} 个")
        print(f"身份认知事实: {total_identity} 个")
        print(f"战斗过程事实: {total_combat} 个")
        print(f"叙事功能事实: {total_narrative} 个")
        print(f"\n=== 质量评估 ===")
        print(f"平均覆盖度得分: {avg_coverage:.1f}/100")
        print(f"平均完整性得分: {avg_completeness:.1f}/100")
        print(f"平均质量得分: {avg_quality:.1f}/100")

        # 显示最常见的问题
        if all_issues:
            print(f"\n=== 主要问题统计 ===")
            issue_counts = {}
            for issue in all_issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
            sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
            for i, (issue, count) in enumerate(sorted_issues[:5], 1):
                print(f"  {i}. {issue} (出现 {count} 次)")

        # 显示最常遗漏的内容
        if all_missing:
            print(f"\n=== 常见遗漏内容 ===")
            for i, missing in enumerate(all_missing[:5], 1):
                print(f"  {i}. {missing}")

    def _generate_improvement_suggestions(self):
        """生成改进建议"""
        print("\n" + "=" * 60)
        print("生成事实提取改进建议...")
        print("=" * 60)

        # 准备评估结果文本
        evaluation_text = "=== 各片段评估结果 ===\n"
        for i, result in enumerate(self.evaluation_results, 1):
            evaluation_text += f"\n片段{i} ({result.fragment_id}):\n"
            evaluation_text += f"内容: {result.original_content[:200]}...\n"
            evaluation_text += f"质量得分: {result.quality_score:.1f}/100\n"
            evaluation_text += f"覆盖度: {result.coverage_score:.1f}/100, 完整性: {result.completeness_score:.1f}/100\n"
            evaluation_text += f"遗漏内容: {len(result.missing_aspects)} 个\n"
            for missing in result.missing_aspects:
                evaluation_text += f"  - {missing}\n"
            evaluation_text += f"改进建议: {len(result.suggestions)} 个\n"
            for suggestion in result.suggestions:
                evaluation_text += f"  - {suggestion}\n"

        system_prompt = self.FRAGMENT_SUMMARY_PROMPT.format(
            exploration_results=evaluation_text
        )

        user_prompt = """基于以上评估结果，请提供一份完整的事实提取改进方案。

特别关注：
1. 识别6个核心原则下的系统性提取问题
2. 确保事实提取的完整性和准确性
3. 提供针对每个原则的具体改进建议
4. 考虑修仙小说的特殊性和复杂性"""

        print("正在调用LLM生成改进建议...")

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        improvement_suggestions = response.content  # type: ignore

        print("\n" + "=" * 60)
        print("事实提取改进建议")
        print("=" * 60)
        print(improvement_suggestions)

        # 保存改进建议到文件
        self._save_improvement_suggestions(improvement_suggestions)

    def _save_improvement_suggestions(self, suggestions: str):
        """保存改进建议到文件"""
        output_file = "fact_extraction_improvement_suggestions.md"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# 修仙小说事实提取改进建议\n\n")
                f.write(f"生成时间: {self._get_current_time()}\n")
                f.write(f"评估片段数: {len(self.evaluation_results)}\n\n")
                f.write(suggestions)

            print(f"\n改进建议已保存到: {output_file}")
        except Exception as e:
            print(f"保存文件时出错: {e}")

    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='修仙小说事实提取评估器')
    parser.add_argument('--file', '-f', default="resources/ignored/1.txt",
                       help='小说文件路径 (默认: resources/ignored/1.txt)')
    parser.add_argument('--name', '-n', default="fanren",
                       help='小说名称 (默认: fanren)')
    parser.add_argument('--count', '-c', type=int, default=10,
                       help='采样片段数量 (默认: 10)')

    args = parser.parse_args()

    evaluator = FactExtractionEvaluator()
    evaluator.run_evaluation(
        novel_file=args.file,
        novel_name=args.name,
        fragment_count=args.count
    )


if __name__ == "__main__":
    main()