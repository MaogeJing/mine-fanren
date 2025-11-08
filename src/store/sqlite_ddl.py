#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite DDL (Data Definition Language) 定义
包含表结构、索引等的创建语句
"""

import sqlite3
from typing import List
from sqlite3 import Connection
from .sqlite_types import SQLiteStorageError


# 章节块表创建语句
CREATE_CHAPTER_CHUNKS_TABLE = """
CREATE TABLE IF NOT EXISTS chapter_chunks (
    chunk_id TEXT PRIMARY KEY,
    novel_name TEXT NOT NULL,
    chapter_id INTEGER NOT NULL,
    chapter_title TEXT NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    pos_start INTEGER,
    pos_end INTEGER,
    char_count INTEGER,
    token_count INTEGER,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(novel_name, chapter_id)
);
"""

# 提示词模板表创建语句
CREATE_PROMPT_TEMPLATES_TABLE = """
CREATE TABLE IF NOT EXISTS prompt_templates (
    template_key TEXT NOT NULL,
    version TEXT NOT NULL,
    description TEXT NOT NULL,
    template_content TEXT NOT NULL,
    required_params TEXT NOT NULL DEFAULT '[]',
    language TEXT NOT NULL DEFAULT 'zh',
    notes TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (template_key, version)
);
"""

# 索引创建语句
INDEX_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS idx_novel_name ON chapter_chunks(novel_name);",
    "CREATE INDEX IF NOT EXISTS idx_chapter_id ON chapter_chunks(chapter_id);",
    "CREATE INDEX IF NOT EXISTS idx_prompt_template_key ON prompt_templates(template_key);",
]


def init_database(conn: Connection) -> None:
    """
    初始化数据库（创建表和索引）

    Args:
        conn: 数据库连接对象

    Raises:
        SQLiteStorageError: 数据库初始化失败
    """
    try:
        # 创建章节块表
        conn.execute(CREATE_CHAPTER_CHUNKS_TABLE)

        # 创建提示词模板表
        conn.execute(CREATE_PROMPT_TEMPLATES_TABLE)

        # 创建索引
        for index_sql in INDEX_STATEMENTS:
            conn.execute(index_sql)

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise SQLiteStorageError(f"数据库初始化失败: {e}")


def drop_chapter_chunks_table(conn: Connection) -> None:
    """
    删除章节块表（用于测试或重建）

    Args:
        conn: 数据库连接对象

    Raises:
        SQLiteStorageError: 表删除失败
    """
    try:
        conn.execute("DROP TABLE IF EXISTS chapter_chunks;")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise SQLiteStorageError(f"删除章节块表失败: {e}")


def drop_prompt_templates_table(conn: Connection) -> None:
    """
    删除提示词模板表（用于测试或重建）

    Args:
        conn: 数据库连接对象

    Raises:
        SQLiteStorageError: 表删除失败
    """
    try:
        conn.execute("DROP TABLE IF EXISTS prompt_templates;")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise SQLiteStorageError(f"删除提示词模板表失败: {e}")


def get_table_info(conn: Connection, table_name: str) -> List[sqlite3.Row]:
    """
    获取表结构信息

    Args:
        conn: 数据库连接对象
        table_name: 表名

    Returns:
        List[sqlite3.Row]: 表结构信息列表
    """
    cursor = conn.execute(f"PRAGMA table_info({table_name});")
    return cursor.fetchall()