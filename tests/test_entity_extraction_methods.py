#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实体提取方法对比测试
比较传统文本解析方法和 LangChain structured output 方法的效果
"""

import sys
import os
import time

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from index.extract_entity import extract_entities_from_chunk
from models import ChapterChunk


def create_test_chunk():
    """创建测试章节块"""
    test_content = """
    山边小村

    在青州的一个偏僻小山村里，住着一个名叫韩立的少年。他今年十六岁，家境普通，
    父母都是普通的村民。韩立的二愣子是他的外号，因为他平时看起来有些木讷。

    这一天，村里来了一个修仙者，是七玄门的墨大夫。墨大夫看中了韩立的资质，
    决定收他为记名弟子，教授他修仙之道。韩立从此踏上了修仙之路。

    墨大夫给了韩立一本《青元剑诀》，这是七玄门的基础功法。同时，他还得到了
    一个神秘的小瓶，这个瓶子可以催熟灵药，是韩立最大的秘密。
    """

    chunk = ChapterChunk.create_chunk(
        novel_name="凡人修仙传",
        chapter_id=1,
        chapter_title="山边小村",
        content=test_content.strip(),
        line_start=1,
        line_end=20,
        pos_start=0,
        pos_end=len(test_content.strip()),
        token_count=200
    )

    return chunk


def test_structured_method(chunk):
    """测试 structured output 方法"""
    print("=" * 60)
    print("测试 LangChain Structured Output 实体提取")
    print("=" * 60)

    start_time = time.time()
    result = extract_entities_from_chunk(chunk)
    end_time = time.time()

    print(f"提取耗时: {end_time - start_time:.2f} 秒")
    print(f"提取成功: {result.extraction_success}")
    print(f"提取实体数量: {result.total_entities}")

    if result.extraction_error:
        print(f"错误信息: {result.extraction_error}")

    if result.entities:
        print("\n提取的实体:")
        for i, entity in enumerate(result.entities, 1):
            print(f"{i}. [{entity.entity_type}] {entity.entity_name}")
            print(f"   描述: {entity.entity_description}")
            print(f"   原文: {entity.source_text}")
            print()

        # 分析实体类型分布
        entity_types = {}
        for entity in result.entities:
            main_type = entity.entity_type.split('-')[0]
            entity_types[main_type] = entity_types.get(main_type, 0) + 1

        print("实体类型分布:")
        for entity_type, count in entity_types.items():
            print(f"  {entity_type}: {count}")

    return result, end_time - start_time


def main():
    """主函数"""
    print("LangChain Structured Output 实体提取测试")
    print("测试文本: 凡人修仙传第一章片段")

    # 创建测试数据
    chunk = create_test_chunk()
    print(f"测试文本长度: {len(chunk.content)} 字符")
    print(f"预估token数: {chunk.token_count}")
    print()

    # 测试 structured output 方法
    result, processing_time = test_structured_method(chunk)

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    if result.extraction_success:
        print("✅ Structured Output 实体提取成功!")
        print(f"📊 提取到 {result.total_entities} 个实体")
        print(f"⏱️ 处理时间: {processing_time:.2f} 秒")
        print(f"🎯 平均每个实体耗时: {processing_time/max(1, result.total_entities):.2f} 秒")
    else:
        print("❌ Structured Output 实体提取失败")
        print(f"🚫 错误信息: {result.extraction_error}")


if __name__ == "__main__":
    main()