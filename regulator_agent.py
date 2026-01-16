# Copyright (c) 2025 ETH Zurich.
#                    All rights reserved.
#
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# Regulator Agent for generating game variants

import sys
import os

# Independent project - use local dependencies
current_dir = os.path.dirname(os.path.abspath(__file__))
dependencies_dir = os.path.join(current_dir, 'dependencies')
sys.path.insert(0, dependencies_dir)

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from typing import Literal
from models import get_model_by_id_and_provider
from games_structures.base_game import BaseGameStructure


class GameVariantResponse(BaseModel):
    """
    Response from regulator agent containing the generated game variant.
    """
    variant_description: str
    variant_payoff_matrix: str  # Store as JSON string to avoid schema issues
    complexity_level: Literal["low", "medium", "high"]
    reasoning: str
    
    class Config:
        json_schema_extra = {
            "variant_payoff_matrix": {
                "description": "JSON string representation of the payoff matrix, e.g., '{\"cooperate,cooperate\": [3,3], \"cooperate,defect\": [0,5]}'"
            }
        }


class RegulatorAgent:
    """
    Regulator Agent that generates game variants based on original game prompts.
    Uses a higher-level API to create more complex and challenging variants.
    """
    
    def __init__(self, model_id: str, model_provider: str = None):
        """
        Initialize the Regulator Agent.
        
        Args:
            model_id (str): The model ID to use (e.g., "gpt-4o")
            model_provider (str, optional): The model provider
        """
        self.model = get_model_by_id_and_provider(model_id, provider=model_provider)
    
    def generate_game_variant(
        self, 
        base_game: BaseGameStructure,
        variant_type: Literal["complex", "contextual", "multi_stage"] = "complex"
    ) -> GameVariantResponse:
        """
        Generate a game variant based on the base game structure.
        
        Args:
            base_game (BaseGameStructure): The base game structure
            variant_type (str): Type of variant to generate
                - "complex": Add complexity to the game mechanics
                - "contextual": Add contextual information or framing
                - "multi_stage": Create a multi-stage variant
        
        Returns:
            GameVariantResponse: The generated game variant
        """
        base_prompt = base_game.GAME_PROMPT.content if hasattr(base_game.GAME_PROMPT, 'content') else str(base_game.GAME_PROMPT)
        base_payoff = base_game.payoff_matrix
        
        regulator_prompt = self._build_regulator_prompt(
            base_prompt, 
            base_payoff, 
            base_game.game_name,
            variant_type
        )
        
        # Use function_calling method to avoid schema validation issues with dict types
        import time
        from openai import RateLimitError, APIConnectionError
        try:
            from httpx import RemoteProtocolError
        except ImportError:
            RemoteProtocolError = Exception
        
        max_retries = 5
        retry_delay = 2  # 快速重试延迟
        
        # 移除初始等待，直接调用API
        import time
        import sys
        sys.stdout.flush()
        print("🚀 Regulator: 直接调用API...", flush=True)
        
        for attempt in range(max_retries):
            try:
                # Use json_schema method for OpenRouter compatibility
                response = self.model.with_structured_output(
                    GameVariantResponse, 
                    method="json_schema"
                ).invoke(regulator_prompt)
                return response
            except Exception as e:
                # Handle different types of errors
                error_str = str(e).lower()
                error_type = type(e).__name__
                
                # Check for rate limit errors
                is_rate_limit = ("rate limit" in error_str or "429" in error_str or 
                               isinstance(e, RateLimitError) or "too many requests" in error_str)
                
                # Check for connection errors (network issues, server disconnects)
                is_connection_error = (isinstance(e, (APIConnectionError, RemoteProtocolError)) or
                                     "connection" in error_str or "disconnected" in error_str or
                                     "server disconnected" in error_str or "timeout" in error_str)
                
                if (is_rate_limit or is_connection_error) and attempt < max_retries - 1:
                    error_msg = str(e)
                    
                    # For rate limits, try to extract wait time
                    if is_rate_limit and "try again in" in error_msg.lower():
                        import re
                        wait_match = re.search(r'(\d+)s', error_msg)
                        if wait_match:
                            retry_delay = int(wait_match.group(1)) + 2
                    elif is_connection_error:
                        # For connection errors, use exponential backoff
                        retry_delay = min(10 * (2 ** attempt), 60)  # Max 60 seconds
                    
                    if is_rate_limit:
                        print(f"Rate limit reached in regulator. Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}...")
                    else:
                        print(f"Connection error in regulator ({error_type}). Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}...")
                    
                    time.sleep(retry_delay)
                else:
                    print(f"Error in regulator after {attempt + 1} attempts: {error_type}: {str(e)}")
                    raise
    
    def _build_regulator_prompt(
        self, 
        base_prompt: str, 
        base_payoff: dict,
        game_name: str,
        variant_type: str
    ) -> list:
        """
        Build the prompt for the regulator agent.
        
        Args:
            base_prompt (str): The base game prompt
            base_payoff (dict): The base payoff matrix
            game_name (str): The name of the game
            variant_type (str): Type of variant to generate
        
        Returns:
            list: List of messages for the regulator agent
        """
        system_prompt = SystemMessage("""You are an expert game theorist and experimental designer. 
Your task is to create game variants that are more complex and challenging than the base game, 
while maintaining the core strategic structure. Your variants should:
1. Preserve the fundamental strategic dilemma of the original game
2. Add complexity through additional context, framing, or mechanics
3. Make it harder for agents to immediately identify the optimal solution
4. Create situations where different personality types might respond differently

Your goal is to design variants that better reveal personality differences in strategic decision-making.""")

        variant_instructions = {
            "complex": """Create a variant that adds complexity to the game mechanics. 
For example:
- Add uncertainty about payoffs
- Introduce reputation or history effects
- Add communication constraints or opportunities
- Include multiple rounds with changing conditions""",
            
            "contextual": """Create a variant that adds rich contextual framing to the game.
For example:
- Frame the game in a specific real-world scenario
- Add emotional or social context
- Include relationship dynamics
- Add moral or ethical considerations""",
            
            "multi_stage": """Create a multi-stage variant where decisions in earlier stages 
affect later stages. Add complexity through:
- Sequential decision points
- Information revelation over time
- Changing game conditions
- Cumulative effects of previous decisions"""
        }
        
        human_prompt = HumanMessage(f"""You are designing a variant of the game: {game_name}

**Base Game Description:**
{base_prompt}

**Base Payoff Matrix:**
{base_payoff}

**Variant Type:** {variant_type}
{variant_instructions.get(variant_type, variant_instructions["complex"])}

**Your Task:**
Generate a game variant that:
1. Maintains the core strategic structure
2. Adds meaningful complexity or context
3. Makes personality differences more apparent
4. Is still playable with the same action space

**Output Format:**
- variant_description: A detailed description of the game variant (similar format to base game)
- variant_payoff_matrix: The payoff matrix as a JSON string. Format example: {{"cooperate,cooperate": [3,3], "cooperate,defect": [0,5], "defect,cooperate": [5,0], "defect,defect": [1,1]}}
  Use comma-separated action pairs as keys (e.g., "cooperate,defect") and arrays of two numbers as values.
- complexity_level: "low", "medium", or "high"
- reasoning: Explain why this variant better reveals personality differences

**Important:** The variant should make it harder for agents to immediately identify the optimal solution, 
forcing them to rely more on their personality traits and decision-making style.""")

        return [system_prompt, human_prompt]
    
    def generate_multiple_variants(
        self,
        base_game: BaseGameStructure,
        n_variants: int = 3,
        variant_types: list = None
    ) -> list[GameVariantResponse]:
        """
        Generate multiple variants of a game.
        
        Args:
            base_game (BaseGameStructure): The base game structure
            n_variants (int): Number of variants to generate
            variant_types (list, optional): List of variant types to use
        
        Returns:
            list[GameVariantResponse]: List of generated variants
        """
        if variant_types is None:
            variant_types = ["complex", "contextual", "multi_stage"]
        
        variants = []
        for i in range(n_variants):
            variant_type = variant_types[i % len(variant_types)]
            variant = self.generate_game_variant(base_game, variant_type)
            variants.append(variant)
        
        return variants
