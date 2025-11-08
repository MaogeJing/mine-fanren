#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型定义
定义章节块提取过程中使用的数据结构
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
import uuid


class ChapterChunk(BaseModel):
    """章节块数据结构"""
    novel_name: str = Field(description="小说名称")
    chunk_id: str = Field(description="章节块唯一标识符(UUID)")
    chapter_id: int = Field(description="章节编号")
    chapter_title: str = Field(description="章节标题")

    # 位置信息
    line_start: int = Field(description="开始行号")
    line_end: int = Field(description="结束行号")
    pos_start: int = Field(description="在原文中的字符开始位置")
    pos_end: int = Field(description="在原文中的字符结束位置")

    # 统计信息
    char_count: int = Field(description="字符数")
    token_count: int = Field(description="词元数")

    # 内容
    content: str = Field(description="章节内容")

    @classmethod
    def create_chunk(
        cls,
        novel_name: str,
        chapter_id: int,
        chapter_title: str,
        content: str,
        line_start: int,
        line_end: int,
        pos_start: int,
        pos_end: int,
        token_count: int
    ) -> "ChapterChunk":
        """
        创建章节块实例

        Args:
            novel_name: 小说名称
            chapter_id: 章节编号
            chapter_title: 章节标题
            content: 章节内容
            line_start: 开始行号
            line_end: 结束行号
            pos_start: 字符开始位置
            pos_end: 字符结束位置
            token_count: 词元数，如果为None则用字符数估算

        Returns:
            ChapterChunk: 章节块实例
        """
        # 生成不带横线的UUID
        chunk_id = uuid.uuid4().hex.replace('-', '')

        return cls(
            novel_name=novel_name,
            chunk_id=chunk_id,
            chapter_id=chapter_id,
            chapter_title=chapter_title,
            content=content,
            line_start=line_start,
            line_end=line_end,
            pos_start=pos_start,
            pos_end=pos_end,
            char_count=len(content),
            token_count=token_count
        )

    def __str__(self) -> str:
        """字符串表示"""
        return f"ChapterChunk(id={self.chapter_id}, title='{self.chapter_title}', novel={self.novel_name})"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"ChapterChunk(chunk_id='{self.chunk_id}', novel_name='{self.novel_name}', "
                f"chapter_id={self.chapter_id}, chapter_title='{self.chapter_title}', "
                f"lines={self.line_start}-{self.line_end}, chars={self.char_count})")


class PromptTemplate(BaseModel):
    """提示词模板数据结构"""
    template_key: str = Field(description="提示词模板唯一标识符")
    version: str = Field(description="模板版本号 (例如: '1.0.0')")
    description: str = Field(description="模板描述")

    # 模板内容
    template_content: str = Field(description="Python字符串模板内容")
    required_params: list[str] = Field(description="模板所需参数列表", default_factory=list)

    # 元数据
    language: str = Field(description="模板语言", default="zh")
    notes: str = Field(description="备注信息，使用感受、优化建议等", default="")

    @classmethod
    def create_template(
        cls,
        template_key: str,
        version: str,
        description: str,
        template_content: str,
        required_params: list[str] | None = None,
        language: str = "zh",
        notes: str = ""
    ) -> "PromptTemplate":
        """
        创建提示词模板实例

        Args:
            template_key: 模板唯一标识符
            version: 版本号
            description: 模板描述
            template_content: Python字符串模板内容
            required_params: 必需参数列表
            language: 模板语言
            notes: 备注信息

        Returns:
            PromptTemplate: 提示词模板实例
        """
        return cls(
            template_key=template_key,
            version=version,
            description=description,
            template_content=template_content,
            required_params=required_params or [],
            language=language,
            notes=notes
        )

    def render(self, **kwargs) -> str:
        """
        渲染模板

        Args:
            **kwargs: 模板参数

        Returns:
            str: 渲染后的内容

        Raises:
            ValueError: 缺少必需参数
            KeyError: 参数不存在于模板中
        """
        # 检查必需参数
        missing_params = set(self.required_params) - set(kwargs.keys())
        if missing_params:
            raise ValueError(f"缺少必需参数: {', '.join(missing_params)}")

        try:
            return self.template_content.format(**kwargs)
        except KeyError as e:
            raise KeyError(f"模板中存在未定义的参数: {e}")
        except ValueError as e:
            raise ValueError(f"模板格式错误: {e}")

    def __str__(self) -> str:
        """字符串表示"""
        return f"PromptTemplate(key={self.template_key}, version={self.version})"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"PromptTemplate(template_key='{self.template_key}', version='{self.version}', "
                f"required_params={self.required_params}, notes='{self.notes[:50]}...')" if len(self.notes) > 50 else
                f"PromptTemplate(template_key='{self.template_key}', version='{self.version}', "
                f"required_params={self.required_params}, notes='{self.notes})")


class PromptTemplateBundle(BaseModel):
    """提示词模板包，包含一个模板的所有版本"""

    templates: List[PromptTemplate] = Field(description="模板版本列表")

    @field_validator('templates')
    @classmethod
    def validate_templates(cls, v):
        """验证模板列表"""
        if not v:
            raise ValueError("模板列表不能为空")

        # 检查所有模板是否都有相同的 template_key
        template_keys = {t.template_key for t in v}
        if len(template_keys) > 1:
            raise ValueError(f"模板包中的模板必须有相同的 template_key，发现: {template_keys}")

        # 按版本号排序
        return sorted(v, key=lambda t: t.version)

    @property
    def template_key(self) -> str:
        """获取模板Key"""
        return self.templates[0].template_key

    @property
    def versions(self) -> List[str]:
        """获取所有版本号"""
        return [t.version for t in self.templates]

    def get_template(self, version: Optional[str] = None) -> PromptTemplate:
        """
        获取指定版本的模板，如果不指定版本则返回最新版本

        Args:
            version: 版本号，如果为None则返回最新版本

        Returns:
            PromptTemplate: 指定版本的模板，如果不存在则返回最新版本
        """
        if version is None:
            # 返回最新版本
            return max(self.templates, key=lambda t: t.version)

        # 返回指定版本
        for template in self.templates:
            if template.version == version:
                return template

        # 如果指定版本不存在，返回最新版本
        return max(self.templates, key=lambda t: t.version)

    def __str__(self) -> str:
        """字符串表示"""
        return f"PromptTemplateBundle(key={self.template_key}, versions={self.versions})"

    def __repr__(self) -> str:
        """详细字符串表示"""
        latest = max(self.templates, key=lambda t: t.version)
        return (f"PromptTemplateBundle(template_key='{self.template_key}', "
                f"count={len(self.templates)}, latest_version='{latest.version}', "
                f"latest_notes='{latest.notes[:50]}...')" if len(latest.notes) > 50 else
                f"PromptTemplateBundle(template_key='{self.template_key}', "
                f"count={len(self.templates)}, latest_version='{latest.version}', "
                f"latest_notes='{latest.notes}')")

    def __iter__(self):
        """支持迭代"""
        return iter(self.templates)

    def __len__(self):
        """支持len()"""
        return len(self.templates)