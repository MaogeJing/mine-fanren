#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
陈述类型探索器
通过启发式方法探索和完善陈述类型定义
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
class AnalysisResult:
    """分析结果"""
    fragment_id: str
    original_content: str
    extracted_claims: List[Dict[str, Any]]
    uncovered_statements: List[str]  # 现有定义无法覆盖的陈述
    suggestions: List[str]  # 对类型定义的建议
    confidence_score: int  # 分析置信度


class ClaimTypeExplorer:
    """陈述类型探索器"""

    # 陈述类型分析提示词模板
    CLAIM_TYPE_ANALYSIS_PROMPT = """
-Goal-
分析给定文本片段中的陈述性事实，评估现有陈述类型定义的覆盖度，并提出改进建议。

-Current Claim Types-
当前陈述类型定义：
1. 实力对比陈述：展现角色之间的强弱关系、战斗结果
2. 能力边界陈述：说明角色能做什么、不能做什么、掌握程度如何
3. 代价成本陈述：展现行动需要付出的代价、副作用、风险
4. 身份地位陈述：说明角色的身份、称号、在世界观中的位置
5. 认知震惊陈述：角色对某事的惊讶、怀疑、误判，揭示信息差
6. 因果链条陈述：完整的因果关系：原因→行动→结果
7. 状态转变陈述：角色形态、境界、处境的变化过程

-Analysis Steps-
1. 识别文本中的所有陈述性事实
2. 尝试用现有7种类型分类每个陈述
3. 识别无法归类到现有类型的陈述
4. 分析这些未覆盖陈述的共同特征
5. 提出新的类型定义建议

-Output Format-
请按以下格式输出：

=== 成功归类的陈述 ===
[陈述1]: 类型名称 - 陈述内容
[陈述2]: 类型名称 - 陈述内容
...

=== 未覆盖的陈述 ===
[陈述1]: 陈述内容 - 无法归类的原因
[陈述2]: 陈述内容 - 无法归类的原因
...

=== 新类型建议 ===
[建议1]: 新类型名称 - 定义 - 包含的陈述
[建议2]: 新类型名称 - 定义 - 包含的陈述
...

=== 类型定义评估 ===
覆盖度: [1-10分]
问题分析: [现有定义的主要问题]
改进方向: [具体的改进建议]

-Real Data-
文本片段: {fragment_content}
章节: 第{chapter_id}章 {chapter_title}

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
        """初始化探索器"""
        load_dotenv()
        self.llm = ChatOpenAI(
            model="kimi-k2-0905-preview",
            temperature=0.2,  # 稍微提高温度以获得更有创意的分析
        )
        self.exploration_results: List[AnalysisResult] = []

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

    def analyze_fragment(self, fragment: TextFragment) -> AnalysisResult:
        """
        分析单个文本片段

        Args:
            fragment: 文本片段

        Returns:
            AnalysisResult: 分析结果
        """
        print(f"正在分析片段 {fragment.fragment_id}...")

        system_prompt = self.CLAIM_TYPE_ANALYSIS_PROMPT.format(
            fragment_content=fragment.content,
            chapter_id=fragment.chapter_id,
            chapter_title=fragment.chapter_title
        )

        user_prompt = f"""请分析这个文本片段中的陈述性事实，特别关注现有类型定义无法很好覆盖的陈述。

片段ID: {fragment.fragment_id}
章节: 第{fragment.chapter_id}章 {fragment.chapter_title}
提及的实体: {', '.join(fragment.entities_mentioned)}

请进行深入分析并提出改进建议。"""

        # 调用LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        analysis_text = response.content  # type: ignore

        # 解析分析结果
        result = self._parse_analysis_result(fragment, analysis_text)

        print(f"片段 {fragment.fragment_id} 分析完成")
        return result

    def _parse_analysis_result(self, fragment: TextFragment, analysis_text: str) -> AnalysisResult:
        """
        解析AI分析结果

        Args:
            fragment: 文本片段
            analysis_text: AI返回的分析文本

        Returns:
            AnalysisResult: 解析后的结果
        """
        lines = analysis_text.split('\n')

        result = AnalysisResult(
            fragment_id=fragment.fragment_id,
            original_content=fragment.content,
            extracted_claims=[],
            uncovered_statements=[],
            suggestions=[],
            confidence_score=5
        )

        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith('=== 成功归类的陈述 ==='):
                current_section = 'covered'
            elif line.startswith('=== 未覆盖的陈述 ==='):
                current_section = 'uncovered'
            elif line.startswith('=== 新类型建议 ==='):
                current_section = 'suggestions'
            elif line.startswith('=== 类型定义评估 ==='):
                current_section = 'evaluation'
            elif line.startswith('[陈述') and current_section == 'covered':
                # 解析成功归类的陈述
                result.extracted_claims.append(line)
            elif line.startswith('[陈述') and current_section == 'uncovered':
                # 解析未覆盖的陈述
                result.uncovered_statements.append(line)
            elif line.startswith('[建议') and current_section == 'suggestions':
                # 解析建议
                result.suggestions.append(line)
            elif line.startswith('覆盖度:') and current_section == 'evaluation':
                # 提取置信度
                try:
                    score_str = line.split(':')[1].strip()
                    score = int(''.join(filter(str.isdigit, score_str)))
                    result.confidence_score = min(10, max(1, score))
                except:
                    pass

        return result

    def run_exploration(self, novel_file: str = "resources/ignored/1.txt",
                       novel_name: str = "fanren", fragment_count: int = 10):
        """
        运行完整的探索流程

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
        print("开始陈述类型探索...")
        print("=" * 60)

        # 第一步：随机采样片段
        fragments = self.sample_random_fragments(novel_name, raw_text, fragment_count)

        if not fragments:
            print("未能采样到有效的文本片段")
            return

        print("\n" + "=" * 60)
        print("开始分析片段...")
        print("=" * 60)

        # 第二步：逐个分析片段
        for i, fragment in enumerate(fragments, 1):
            print(f"\n[{i}/{len(fragments)}] 分析片段 {fragment.fragment_id}")
            print(f"内容预览: {fragment.content[:100]}...")

            result = self.analyze_fragment(fragment)
            self.exploration_results.append(result)

            print(f"  - 提取陈述: {len(result.extracted_claims)} 个")
            print(f"  - 未覆盖陈述: {len(result.uncovered_statements)} 个")
            print(f"  - 改进建议: {len(result.suggestions)} 个")
            print(f"  - 分析置信度: {result.confidence_score}/10")

        # 第三步：总结探索结果
        self._summarize_exploration()

        # 第四步：生成改进建议
        self._generate_improvement_suggestions()

    def _summarize_exploration(self):
        """总结探索结果"""
        print("\n" + "=" * 60)
        print("探索结果汇总")
        print("=" * 60)

        total_claims = sum(len(r.extracted_claims) for r in self.exploration_results)
        total_uncovered = sum(len(r.uncovered_statements) for r in self.exploration_results)
        total_suggestions = sum(len(r.suggestions) for r in self.exploration_results)
        avg_confidence = sum(r.confidence_score for r in self.exploration_results) / len(self.exploration_results)

        print(f"分析片段数: {len(self.exploration_results)}")
        print(f"提取陈述总数: {total_claims}")
        print(f"未覆盖陈述总数: {total_uncovered}")
        print(f"改进建议总数: {total_suggestions}")
        print(f"平均分析置信度: {avg_confidence:.1f}/10")

        # 统计最常见的未覆盖陈述类型
        all_uncovered = []
        for result in self.exploration_results:
            all_uncovered.extend(result.uncovered_statements)

        if all_uncovered:
            print(f"\n最常见的未覆盖陈述模式:")
            for i, statement in enumerate(all_uncovered[:10], 1):
                print(f"  {i}. {statement}")

    def _generate_improvement_suggestions(self):
        """生成改进建议"""
        print("\n" + "=" * 60)
        print("生成类型定义改进建议...")
        print("=" * 60)

        # 准备探索结果文本
        exploration_text = "=== 各片段分析结果 ===\n"
        for i, result in enumerate(self.exploration_results, 1):
            exploration_text += f"\n片段{i} ({result.fragment_id}):\n"
            exploration_text += f"内容: {result.original_content[:200]}...\n"
            exploration_text += f"未覆盖陈述: {len(result.uncovered_statements)} 个\n"
            for statement in result.uncovered_statements:
                exploration_text += f"  - {statement}\n"
            exploration_text += f"改进建议: {len(result.suggestions)} 个\n"
            for suggestion in result.suggestions:
                exploration_text += f"  - {suggestion}\n"

        system_prompt = self.FRAGMENT_SUMMARY_PROMPT.format(
            exploration_results=exploration_text
        )

        user_prompt = """基于以上探索结果，请提供一份完整的陈述类型定义改进方案。

特别关注：
1. 识别系统性的类型缺失
2. 确保新类型定义的互斥性和完备性
3. 提供清晰的操作化定义和示例
4. 考虑修仙小说的特殊性"""

        print("正在调用LLM生成改进建议...")

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        improvement_suggestions = response.content  # type: ignore

        print("\n" + "=" * 60)
        print("陈述类型定义改进建议")
        print("=" * 60)
        print(improvement_suggestions)

        # 保存改进建议到文件
        self._save_improvement_suggestions(improvement_suggestions)

    def _save_improvement_suggestions(self, suggestions: str):
        """保存改进建议到文件"""
        output_file = "claim_type_improvement_suggestions.md"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# 陈述类型定义改进建议\n\n")
                f.write(f"生成时间: {self._get_current_time()}\n")
                f.write(f"分析片段数: {len(self.exploration_results)}\n\n")
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
    parser = argparse.ArgumentParser(description='陈述类型探索器')
    parser.add_argument('--file', '-f', default="resources/ignored/1.txt",
                       help='小说文件路径 (默认: resources/ignored/1.txt)')
    parser.add_argument('--name', '-n', default="fanren",
                       help='小说名称 (默认: fanren)')
    parser.add_argument('--count', '-c', type=int, default=10,
                       help='采样片段数量 (默认: 10)')

    args = parser.parse_args()

    explorer = ClaimTypeExplorer()
    explorer.run_exploration(
        novel_file=args.file,
        novel_name=args.name,
        fragment_count=args.count
    )


if __name__ == "__main__":
    main()