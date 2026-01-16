# Copyright (c) 2025 ETH Zurich.
#                    All rights reserved.
#
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# Node helpers for regulated games (reused from MultiAgent-GameTheory)

import sys
import os
import json
from langchain_core.messages import SystemMessage

# Independent project - use local dependencies
current_dir = os.path.dirname(os.path.abspath(__file__))
dependencies_dir = os.path.join(current_dir, 'dependencies')
sys.path.insert(0, dependencies_dir)

from node_helpers import (
    load_game_structure_from_registry,
    get_answer_format,
    get_question_prompt,
    get_agent_annotated_prompt,
    AnnotatedPrompt
)

# Override get_personality_from_key_prompt to use local dependencies path
import node_helpers as nh_module

def get_personality_from_key_prompt_fixed(personality_key: str) -> SystemMessage:
    """Get personality prompt with correct path resolution."""
    priming_path = os.path.join(current_dir, 'dependencies', 'priming', 'priming_without_mention_of_mbti_different_none_with_altruistic_selfish.json')
    if not os.path.exists(priming_path):
        raise FileNotFoundError(f"Personality file not found at: {priming_path}")
    personalities = json.load(open(priming_path))
    return SystemMessage(personalities[personality_key])

# Monkey patch the original function in node_helpers module
nh_module.get_personality_from_key_prompt = get_personality_from_key_prompt_fixed
nh_module.get_personality_from_key_prompt = get_personality_from_key_prompt_fixed

# Re-export for convenience
__all__ = [
    'load_game_structure_from_registry',
    'get_answer_format',
    'get_question_prompt',
    'get_agent_annotated_prompt',
    'AnnotatedPrompt',
    'get_personality_from_key_prompt_fixed'
]
