#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实体提取器
从章节内容中提取结构化的实体信息
"""

import os
import time
from typing import List, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

from ..models import ChapterChunk, Entity, ChapterEntity, EntityListResponse
from ..prompts.fanren_entity_extract_structured_template import FANREN_ENTITY_EXTRACT_STRUCTURED_TEMPLATE


class EntityExtractor:
    """实体提取器 - 使用 LangChain Structured Output"""

    def __init__(self):
        """
        初始化实体提取器
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

        # 创建支持结构化输出的模型
        self.structured_llm = self.llm.with_structured_output(EntityListResponse)
        self.template = FANREN_ENTITY_EXTRACT_STRUCTURED_TEMPLATE

    def extract_entities_from_chunk(self, chunk: ChapterChunk) -> ChapterEntity:
        """
        使用 LangChain structured output 从章节块中提取实体

        Args:
            chunk: 章节块数据

        Returns:
            ChapterEntity: 章节实体提取结果
        """
        start_time = time.time()

        try:
            # 1. 准备简化的提示词
            system_prompt = self.template.render()

            user_prompt = f"""现在请从以下文本中提取所有符合上述定义的核心实体：

文本：
{chunk.content}

请仔细分析文本，提取所有对理解剧情发展有重要价值的实体。"""

            # 2. 调用 structured LLM
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            # 3. 直接获得结构化输出
            structured_result = self.structured_llm.invoke(messages)
            if not isinstance(structured_result, EntityListResponse):
                raise ValueError(f"Expected EntityListResponse, got {type(structured_result)}")

            # 4. 转换为 Entity 对象
            entities = []
            for extraction in structured_result.entities:
                entity = Entity.create_entity(
                    entity_type=extraction.entity_type,
                    entity_name=extraction.entity_name,
                    entity_description=extraction.entity_description,
                    source_text=extraction.source_text,
                    chapter_id=chunk.chapter_id,
                    novel_name=chunk.novel_name,
                    chunk_id=chunk.chunk_id
                )
                entities.append(entity)

            # 5. 创建ChapterEntity对象
            processing_time = time.time() - start_time
            chapter_entity = ChapterEntity.create_chapter_entity(
                chapter_id=chunk.chapter_id,
                chapter_title=chunk.chapter_title,
                novel_name=chunk.novel_name,
                entities=entities,
                chunk_id=chunk.chunk_id,
                processing_time_seconds=processing_time
            )

            return chapter_entity

        except Exception as e:
            # 处理错误情况
            processing_time = time.time() - start_time
            return ChapterEntity.create_chapter_entity(
                chapter_id=chunk.chapter_id,
                chapter_title=chunk.chapter_title,
                novel_name=chunk.novel_name,
                entities=[],
                chunk_id=chunk.chunk_id,
                extraction_error=f"Structured output 提取失败: {str(e)}",
                processing_time_seconds=processing_time
            )

    def extract_entities_from_chunks(self, chunks: List[ChapterChunk]) -> List[ChapterEntity]:
        """
        批量提取多个章节块的实体

        Args:
            chunks: 章节块列表

        Returns:
            List[ChapterEntity]: 章节实体提取结果列表
        """
        results = []

        for i, chunk in enumerate(chunks, 1):
            print(f"正在处理第{i}/{len(chunks)}个章节块: 第{chunk.chapter_id}章 {chunk.chapter_title}")

            chapter_entity = self.extract_entities_from_chunk(chunk)
            results.append(chapter_entity)

            if chapter_entity.extraction_success:
                print(f"  ✓ 成功提取 {chapter_entity.total_entities} 个实体")
            else:
                print(f"  ✗ 提取失败: {chapter_entity.extraction_error}")

        return results


def extract_entities_from_chunk(chunk: ChapterChunk) -> ChapterEntity:
    """
    便捷函数：从单个章节块提取实体（使用 structured output）

    Args:
        chunk: 章节块数据

    Returns:
        ChapterEntity: 章节实体提取结果
    """
    extractor = EntityExtractor()
    return extractor.extract_entities_from_chunk(chunk)
