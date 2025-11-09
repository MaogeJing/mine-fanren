#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entity and Relationship Extraction Data Types
Using Pydantic to define structured entity and relationship data
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class JEntity(BaseModel):
    """Entity data structure"""
    name: str = Field(description="Entity name")
    type: str = Field(description="Entity type")
    description: str = Field(description="Entity description")


class JRelation(BaseModel):
    """Relationship data structure"""
    source: str = Field(description="Source entity name")
    target: str = Field(description="Target entity name")
    description: str = Field(description="Relationship description")


class ExtractionResult(BaseModel):
    """Extraction result data structure"""
    entities: List[JEntity] = Field(description="Entity list")
    relationships: List[JRelation] = Field(description="Relationship list")
    other_relationships: List[JRelation] = Field(description="Other relationship list")