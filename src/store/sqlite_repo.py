#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite DQL (Data Query Language) 操作
包含章节块的增删改查操作
"""
from typing import List, Dict
import json
from sqlite3 import Connection
from ..models import ChapterChunk, PromptTemplate, PromptTemplateBundle


class ChapterChunkRepo:
    """章节块数据仓库类，专注于 chapter_chunks 表的操作"""

    @staticmethod
    def upsert_chunks(conn: Connection, chunks: List[ChapterChunk]) -> int:
        """
        批量插入或更新章节块（批量UPSERT操作）
        批量处理多个章节块，大幅提升性能

        Args:
            conn: 数据库连接对象（由上层管理生命周期）
            chunks: 章节块对象列表

        Returns:
            int: 成功处理的章节数量
        """
        if not chunks:
            return 0

        sql = """
        INSERT INTO chapter_chunks
        (chunk_id, novel_name, chapter_id, chapter_title, line_start, line_end,
         pos_start, pos_end, char_count, token_count, content)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(chunk_id) DO UPDATE SET
            novel_name = excluded.novel_name,
            chapter_id = excluded.chapter_id,
            chapter_title = excluded.chapter_title,
            line_start = excluded.line_start,
            line_end = excluded.line_end,
            pos_start = excluded.pos_start,
            pos_end = excluded.pos_end,
            char_count = excluded.char_count,
            token_count = excluded.token_count,
            content = excluded.content,
            updated_at = CURRENT_TIMESTAMP
        """

        # 构建批量参数
        params_list = []
        for chunk in chunks:
            params = (
                chunk.chunk_id,
                chunk.novel_name,
                chunk.chapter_id,
                chunk.chapter_title,
                chunk.line_start,
                chunk.line_end,
                chunk.pos_start,
                chunk.pos_end,
                chunk.char_count,
                chunk.token_count,
                chunk.content
            )
            params_list.append(params)

        # 执行批量操作
        cursor = conn.executemany(sql, params_list)
        return cursor.rowcount

    @staticmethod
    def get_chunks_by_ids(conn: Connection, chunk_ids: List[str]) -> Dict[str, ChapterChunk]:
        """
        批量根据chunk_id查询章节块

        Args:
            conn: 数据库连接对象（由上层管理生命周期）
            chunk_ids: 章节块ID列表

        Returns:
            Dict[str, ChapterChunk]: 章节块字典，key为chunk_id，value为章节块对象

        Raises:
            SQLiteStorageError: 数据库操作失败
        """
        if not chunk_ids:
            return {}

        # 构建IN查询，使用参数化查询防止SQL注入
        placeholders = ','.join(['?' for _ in chunk_ids])
        sql = f"SELECT * FROM chapter_chunks WHERE chunk_id IN ({placeholders})"

        cursor = conn.execute(sql, chunk_ids)
        rows = cursor.fetchall()

        result = {}
        for row in rows:
            chunk = ChapterChunkRepo._row_to_chunk(row)
            result[chunk.chunk_id] = chunk

        return result


    @staticmethod
    def get_chunks_by_chapter_ids(conn: Connection, novel_name: str, chapter_ids: List[int]) -> Dict[int, ChapterChunk]:
        """
        批量根据小说名称和章节ID查询章节块

        Args:
            conn: 数据库连接对象（由上层管理生命周期）
            novel_name: 小说名称
            chapter_ids: 章节ID列表

        Returns:
            Dict[int, ChapterChunk]: 章节块字典，key为chapter_id，value为章节块对象

        Raises:
            SQLiteStorageError: 数据库操作失败
        """
        if not chapter_ids:
            return {}

        # 构建IN查询，使用参数化查询防止SQL注入
        placeholders = ','.join(['?' for _ in chapter_ids])
        sql = f"SELECT * FROM chapter_chunks WHERE novel_name = ? AND chapter_id IN ({placeholders})"

        # 参数列表：第一个是novel_name，后面是chapter_ids
        params = [novel_name] + chapter_ids
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()

        result = {}
        for row in rows:
            chunk = ChapterChunkRepo._row_to_chunk(row)
            result[chunk.chapter_id] = chunk

        return result

    @staticmethod
    def delete_chunk(conn: Connection, chunk_id: str) -> bool:
        """
        删除章节块

        Args:
            conn: 数据库连接对象（由上层管理生命周期）
            chunk_id: 章节块ID

        Returns:
            bool: 删除是否成功

        Raises:
            SQLiteStorageError: 数据库操作失败
        """
        sql = "DELETE FROM chapter_chunks WHERE chunk_id = ?"

        cursor = conn.execute(sql, (chunk_id,))
        return cursor.rowcount > 0

    
    @staticmethod
    def _row_to_chunk(row) -> ChapterChunk:
        """
        将数据库行转换为ChapterChunk对象

        Args:
            row: 数据库行对象

        Returns:
            ChapterChunk: 章节块对象
        """
        return ChapterChunk.create_chunk(
            novel_name=row['novel_name'],
            chapter_id=row['chapter_id'],
            chapter_title=row['chapter_title'],
            content=row['content'] or '',
            line_start=row['line_start'] or 0,
            line_end=row['line_end'] or 0,
            pos_start=row['pos_start'] or 0,
            pos_end=row['pos_end'] or 0,
            token_count=row['token_count'] or 0
        )


class PromptTemplateRepo:
    """提示词模板数据仓库类，专注于 prompt_templates 表的操作"""

    @staticmethod
    def upsert_template(conn: Connection, template: PromptTemplate) -> int:
        """
        插入或更新提示词模板

        Args:
            conn: 数据库连接对象（由上层管理生命周期）
            template: 提示词模板对象

        Returns:
            int: 成功处理的行数

        Raises:
            SQLiteStorageError: 数据库操作失败
        """
        sql = """
        INSERT INTO prompt_templates
        (template_key, version, description, template_content, required_params, language, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(template_key, version) DO UPDATE SET
            description = excluded.description,
            template_content = excluded.template_content,
            required_params = excluded.required_params,
            language = excluded.language,
            notes = excluded.notes,
            updated_at = CURRENT_TIMESTAMP
        """

        params = (
            template.template_key,
            template.version,
            template.description,
            template.template_content,
            json.dumps(template.required_params, ensure_ascii=False),
            template.language,
            template.notes
        )

        cursor = conn.execute(sql, params)
        return cursor.rowcount

    @staticmethod
    def get_template_bundle(conn: Connection, template_key: str) -> PromptTemplateBundle:
        """
        根据模板Key获取所有版本的提示词模板（模板包）

        Args:
            conn: 数据库连接对象（由上层管理生命周期）
            template_key: 模板Key

        Returns:
            PromptTemplateBundle: 该模板Key的所有版本组成的模板包

        Raises:
            SQLiteStorageError: 数据库操作失败
            ValueError: 如果模板不存在

        Returns:
            PromptTemplateBundle: 模板包对象
        """
        sql = """
        SELECT * FROM prompt_templates
        WHERE template_key = ?
        ORDER BY version
        """

        cursor = conn.execute(sql, (template_key,))
        rows = cursor.fetchall()

        if not rows:
            raise ValueError(f"模板 {template_key} 不存在")

        templates = [PromptTemplateRepo._row_to_template(row) for row in rows]
        return PromptTemplateBundle(templates=templates)

    @staticmethod
    def get_all_template_keys(conn: Connection) -> List[str]:
        """
        获取所有模板Key

        Args:
            conn: 数据库连接对象（由上层管理生命周期）

        Returns:
            List[str]: 模板Key列表

        Raises:
            SQLiteStorageError: 数据库操作失败
        """
        sql = "SELECT DISTINCT template_key FROM prompt_templates ORDER BY template_key"

        cursor = conn.execute(sql)
        rows = cursor.fetchall()

        return [row['template_key'] for row in rows]

    
    @staticmethod
    def delete_template(conn: Connection, template_key: str, version: str) -> bool:
        """
        删除指定版本的提示词模板

        Args:
            conn: 数据库连接对象（由上层管理生命周期）
            template_key: 模板Key
            version: 版本号

        Returns:
            bool: 删除是否成功

        Raises:
            SQLiteStorageError: 数据库操作失败
        """
        sql = "DELETE FROM prompt_templates WHERE template_key = ? AND version = ?"

        cursor = conn.execute(sql, (template_key, version))
        return cursor.rowcount > 0

    @staticmethod
    def _row_to_template(row) -> PromptTemplate:
        """
        将数据库行转换为PromptTemplate对象

        Args:
            row: 数据库行对象

        Returns:
            PromptTemplate: 提示词模板对象
        """
        required_params = json.loads(row['required_params']) if row['required_params'] else []

        return PromptTemplate.create_template(
            template_key=row['template_key'],
            version=row['version'],
            description=row['description'],
            template_content=row['template_content'],
            required_params=required_params,
            language=row['language'],
            notes=row['notes'] or ''
        )