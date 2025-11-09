#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Native Entity Extractor using OpenAI SDK
Extract entities and relationships using direct OpenAI SDK calls
"""

import os
import json
import time
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from openai import OpenAI
from ..models import ChapterChunk
from ..prompts.fanren_entity_extract_json_template import (
    FANREN_ENTITY_EXTRACTION_SYSTEM_TEMPLATE,
    FANREN_ENTITY_EXTRACTION_PROMPT_TEMPLATE
)
from .types import JEntity, JRelation, ExtractionResult


class OpenAINativeEntityExtractor:
    """Native entity extractor using OpenAI SDK"""

    def __init__(self):
        """Initialize entity extractor with environment variables"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL")
        self.model_name = os.getenv("OPENAI_MODEL")

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=30
        )

    def extract_entities_and_relations(self, chunk: ChapterChunk) -> ExtractionResult:
        """
        Extract entities and relationships from chapter chunk

        Args:
            chunk: Chapter chunk data

        Returns:
            ExtractionResult: Extraction result containing entities and relationships
        """
        start_time = time.time()

        try:
            # Build prompts using templates
            system_prompt = FANREN_ENTITY_EXTRACTION_SYSTEM_TEMPLATE.render()

            user_prompt = FANREN_ENTITY_EXTRACTION_PROMPT_TEMPLATE.render(
                entity_types="[character, state, ability, item, creature, organization, location]",
                input_text=chunk.content
            )

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model_name, # type: ignore
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                extra_body={"reasoning_split": True},
                stream=False,
                response_format={"type": "json_object"}
            )

            # Parse response
            result_text = response.choices[0].message.content
            print(result_text)
            if result_text is None:
                raise ValueError("OpenAI returned empty response")

            extraction_data = json.loads(result_text)

            # Build structured result
            entities = []
            for entity_data in extraction_data.get("entities", []):
                entity = JEntity(
                    name=entity_data.get("name", ""),
                    type=entity_data.get("type", ""),
                    description=entity_data.get("desc", "")
                )
                entities.append(entity)

            relationships = []
            for rel_data in extraction_data.get("relationships", []):
                relation = JRelation(
                    source=rel_data.get("source", ""),
                    target=rel_data.get("target", ""),
                    description=rel_data.get("desc", "")
                )
                relationships.append(relation)

            other_relationships = []
            for rel_data in extraction_data.get("other_relationships", []):
                relation = JRelation(
                    source=rel_data.get("source", ""),
                    target=rel_data.get("target", ""),
                    description=rel_data.get("desc", "")
                )
                other_relationships.append(relation)

            result = ExtractionResult(
                entities=entities,
                relationships=relationships,
                other_relationships=other_relationships
            )

            processing_time = time.time() - start_time
            print(f"✅ Entity extraction completed, time: {processing_time:.2f}s")
            print(f"   - Entity count: {len(entities)}")
            print(f"   - Relationship count: {len(relationships)}")
            print(f"   - Other relationships: {len(other_relationships)}")

            return result

        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"   Original response: {result_text if 'result_text' in locals() else 'N/A'}")
            return ExtractionResult(entities=[], relationships=[], other_relationships=[])

        except Exception as e:
            processing_time = time.time() - start_time
            print(f"❌ Entity extraction failed, time: {processing_time:.2f}s")
            print(f"   Error message: {e}")
            return ExtractionResult(entities=[], relationships=[], other_relationships=[])


def create_extractor() -> OpenAINativeEntityExtractor:
    """
    Create entity extractor

    Returns:
        OpenAINativeEntityExtractor: Extractor instance
    """
    return OpenAINativeEntityExtractor()


def extract_from_chunk(chunk: ChapterChunk) -> ExtractionResult:
    """
    Convenience function: extract entities and relationships from a single chapter chunk

    Args:
        chunk: Chapter chunk data

    Returns:
        ExtractionResult: Extraction result
    """
    extractor = create_extractor()
    return extractor.extract_entities_and_relations(chunk)