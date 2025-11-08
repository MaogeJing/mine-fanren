#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
陈述提取器
从章节内容中提取结构化的陈述/事实信息
"""

import os
import time
from typing import List, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

from ..models import ChapterChunk, ChapterClaim, Claim
from ..prompts.fanren_claim_extract_chat_template import FANREN_CLAIM_EXTRACT_CHAT_TEMPLATE
from ..prompts.constants import TUPLE_DELIMITER, RECORD_DELIMITER, COMPLETION_DELIMITER


class ClaimExtractor:
    """陈述提取器"""

    def __init__(self):
        """
        初始化陈述提取器
        """
        # 从环境变量读取配置
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        model_name = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

        if not model_name:
            raise ValueError("缺少环境变量 OPENAI_MODEL")

        # 使用 init_chat_model 初始化模型，支持 OpenAI 兼容接口
        # 对于 kimi 模型，需要指定 model_provider="openai" 因为它使用 OpenAI 兼容接口
        if model_name.startswith("kimi"):
            self.llm = init_chat_model(model_name, model_provider="openai")
        else:
            self.llm = init_chat_model(model_name)
        self.template = FANREN_CLAIM_EXTRACT_CHAT_TEMPLATE

    def extract_claims_from_chunk(self, chunk: ChapterChunk, entities: Optional[List[str]] = None) -> ChapterClaim:
        """
        从章节块中提取陈述

        Args:
            chunk: 章节块数据
            entities: 预识别的实体列表，必须提供

        Returns:
            ChapterClaim: 章节陈述提取结果
        """
        start_time = time.time()

        try:
            # 1. 验证实体参数
            if entities is None:
                raise ValueError("entities 参数是必需的，请提供预识别的实体列表")

            entity_specs = ", ".join(entities) if entities else "无明显实体"

            # 2. 准备 Chat 格式的提示词
            system_prompt = self.template.render(
                entity_specs=entity_specs,
                claim_description="修仙小说陈述性事实提取",
                tuple_delimiter=TUPLE_DELIMITER,
                record_delimiter=RECORD_DELIMITER,
                completion_delimiter=COMPLETION_DELIMITER
            )

            user_prompt = f"""现在请从以下文本中提取所有符合上述定义的陈述性事实：

文本：
{chunk.content}

请严格按照输出格式要求，提取所有相关事实并完成输出。"""

            # 3. 调用LLM
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = self.llm.invoke(messages)
            extraction_text = response.content  # type: ignore

            # 4. 解析结果
            claims = self._parse_extraction_result(extraction_text, chunk) # type: ignore

            # 5. 创建ChapterClaim对象
            processing_time = time.time() - start_time
            chapter_claim = ChapterClaim.create_chapter_claim(
                chapter_id=chunk.chapter_id,
                chapter_title=chunk.chapter_title,
                novel_name=chunk.novel_name,
                claims=claims,
                chunk_id=chunk.chunk_id,
                processing_time_seconds=processing_time
            )

            return chapter_claim

        except Exception as e:
            # 处理错误情况
            processing_time = time.time() - start_time
            return ChapterClaim.create_chapter_claim(
                chapter_id=chunk.chapter_id,
                chapter_title=chunk.chapter_title,
                novel_name=chunk.novel_name,
                claims=[],
                chunk_id=chunk.chunk_id,
                extraction_error=str(e),
                processing_time_seconds=processing_time
            )

  
    def _parse_extraction_result(self, extraction_text: str, chunk: ChapterChunk) -> List[Claim]:
        """
        解析LLM提取结果

        Args:
            extraction_text: LLM返回的提取文本
            chunk: 章节块信息

        Returns:
            List[Claim]: 解析后的陈述列表
        """
        claims = []

        # 检查是否完成
        if COMPLETION_DELIMITER not in extraction_text:
            # 如果没有完成标记，尝试处理部分结果
            extraction_text += f"\n{COMPLETION_DELIMITER}"

        # 分割记录
        records = extraction_text.split(RECORD_DELIMITER)

        for record in records:
            record = record.strip()

            # 跳过空记录和完成标记
            if not record or record == COMPLETION_DELIMITER:
                continue

            # 尝试解析单个记录
            claim = self._parse_single_record(record, chunk)
            if claim:
                claims.append(claim)

        return claims

    def _parse_single_record(self, record: str, chunk: ChapterChunk) -> Optional[Claim]:
        """
        解析单个陈述记录

        Args:
            record: 单个陈述记录文本
            chunk: 章节块信息

        Returns:
            Optional[Claim]: 解析后的陈述，解析失败返回None
        """
        try:
            # 移除首尾的括号
            record = record.strip()
            if record.startswith('(') and record.endswith(')'):
                record = record[1:-1]

            # 分割字段
            fields = record.split(TUPLE_DELIMITER)

            if len(fields) != 4:
                # 如果字段数不对，跳过这个记录
                print(f"警告：记录字段数不正确，期望4个，实际{len(fields)}个: {record}")
                return None

            claim_type = fields[0].strip()
            main_entity = fields[1].strip()
            claim_content = fields[2].strip()
            source_text = fields[3].strip()

            # 验证必要字段
            if not all([claim_type, main_entity, claim_content, source_text]):
                print(f"警告：记录包含空字段: {record}")
                return None

            # 创建Claim对象
            claim = Claim.create_claim(
                claim_type=claim_type,
                main_entity=main_entity,
                claim_content=claim_content,
                source_text=source_text,
                chapter_id=chunk.chapter_id,
                novel_name=chunk.novel_name,
                chunk_id=chunk.chunk_id
            )

            return claim

        except Exception as e:
            print(f"警告：解析记录时出错: {e}, 记录: {record}")
            return None

    def extract_claims_from_chunks(self, chunks: List[ChapterChunk], entities_list: List[List[str]]) -> List[ChapterClaim]:
        """
        批量提取多个章节块的陈述

        Args:
            chunks: 章节块列表
            entities_list: 每个章节对应的实体列表，必须提供

        Returns:
            List[ChapterClaim]: 章节陈述提取结果列表
        """
        if len(chunks) != len(entities_list):
            raise ValueError(f"chunks 数量 {len(chunks)} 与 entities_list 数量 {len(entities_list)} 不匹配")

        results = []

        for i, chunk in enumerate(chunks, 1):
            chunk_entities = entities_list[i-1]  # 调整索引，因为 i 从 1 开始

            # 显示实体信息
            entities_str = ", ".join(chunk_entities[:5]) + ("..." if len(chunk_entities) > 5 else "")
            print(f"正在处理第{i}/{len(chunks)}个章节块: 第{chunk.chapter_id}章 {chunk.chapter_title}")
            print(f"  实体: {entities_str}")

            chapter_claim = self.extract_claims_from_chunk(chunk, chunk_entities)
            results.append(chapter_claim)

            if chapter_claim.extraction_success:
                print(f"  ✓ 成功提取 {chapter_claim.total_claims} 个陈述")
            else:
                print(f"  ✗ 提取失败: {chapter_claim.extraction_error}")

        return results

    def get_extraction_statistics(self, results: List[ChapterClaim]) -> dict:
        """
        获取提取统计信息

        Args:
            results: 章节陈述提取结果列表

        Returns:
            dict: 统计信息
        """
        total_chapters = len(results)
        successful_chapters = sum(1 for r in results if r.extraction_success)
        total_claims = sum(r.total_claims for r in results)

        # 按类型统计
        claim_types = {}
        for result in results:
            for claim in result.claims:
                claim_type = claim.claim_type.split('.')[0]  # 取主类型
                claim_types[claim_type] = claim_types.get(claim_type, 0) + 1

        # 按实体统计
        entities = {}
        for result in results:
            for claim in result.claims:
                entity = claim.main_entity
                entities[entity] = entities.get(entity, 0) + 1

        return {
            "total_chapters": total_chapters,
            "successful_chapters": successful_chapters,
            "success_rate": successful_chapters / total_chapters if total_chapters > 0 else 0,
            "total_claims": total_claims,
            "avg_claims_per_chapter": total_claims / successful_chapters if successful_chapters > 0 else 0,
            "claim_types": claim_types,
            "top_entities": sorted(entities.items(), key=lambda x: x[1], reverse=True)[:10]
        }


def extract_claims_from_chunk(chunk: ChapterChunk, entities: List[str]) -> ChapterClaim:
    """
    便捷函数：从单个章节块提取陈述

    Args:
        chunk: 章节块数据
        entities: 预识别的实体列表，必须提供

    Returns:
        ChapterClaim: 章节陈述提取结果
    """
    extractor = ClaimExtractor()
    return extractor.extract_claims_from_chunk(chunk, entities)


def extract_claims_from_chunks(chunks: List[ChapterChunk], entities_list: List[List[str]]) -> List[ChapterClaim]:
    """
    便捷函数：批量提取多个章节块的陈述

    Args:
        chunks: 章节块列表
        entities_list: 每个章节对应的实体列表，必须提供

    Returns:
        List[ChapterClaim]: 章节陈述提取结果列表
    """
    if len(chunks) != len(entities_list):
        raise ValueError(f"chunks 数量 {len(chunks)} 与 entities_list 数量 {len(entities_list)} 不匹配")

    extractor = ClaimExtractor()

    results = []
    for i, chunk in enumerate(chunks):
        chunk_entities = entities_list[i]
        result = extractor.extract_claims_from_chunk(chunk, chunk_entities)
        results.append(result)

    return results