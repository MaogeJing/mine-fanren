#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
索引模块
提供文本索引和检索功能
"""

from .extract_claim import ClaimExtractor, extract_claims_from_chunk, extract_claims_from_chunks

__all__ = [
    'ClaimExtractor',
    'extract_claims_from_chunk',
    'extract_claims_from_chunks'
]