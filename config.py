# Copyright (c) 2025 ETH Zurich.
#                    All rights reserved.
#
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# Configuration management for regulated game experiments

from dataclasses import dataclass
from typing import Optional, Literal


@dataclass
class ExperimentConfig:
    """
    Configuration for regulated game experiments.
    """
    # Regulator settings
    regulator_model: str = "gpt-4o"
    regulator_provider: Optional[str] = None
    
    # Player settings
    player_model_1: str = "gpt-4o-mini"
    player_provider_1: Optional[str] = None
    player_model_2: str = "gpt-4o-mini"
    player_provider_2: Optional[str] = None
    
    # Game settings
    base_game_name: str = "prisoners_dilemma"
    variant_type: Literal["complex", "contextual", "multi_stage"] = "complex"
    rounds: int = 7
    
    # Personality settings
    personality_1: str = "INTJ"
    personality_2: str = "ENFP"
    
    # Output settings
    output_dir: str = "data/outputs"
    save_results: bool = True
    
    # Experimental settings
    validate_variants: bool = True
    fallback_to_base: bool = True  # Fall back to base game if variant validation fails


# Default configurations for common experiment setups
DEFAULT_CONFIGS = {
    "baseline": ExperimentConfig(
        regulator_model="gpt-4o",
        player_model_1="gpt-4o-mini",
        player_model_2="gpt-4o-mini",
        base_game_name="prisoners_dilemma",
        variant_type="complex"
    ),
    
    "high_complexity": ExperimentConfig(
        regulator_model="gpt-4o",
        player_model_1="gpt-4o-mini",
        player_model_2="gpt-4o-mini",
        base_game_name="prisoners_dilemma",
        variant_type="multi_stage"
    ),
    
    "contextual": ExperimentConfig(
        regulator_model="gpt-4o",
        player_model_1="gpt-4o-mini",
        player_model_2="gpt-4o-mini",
        base_game_name="prisoners_dilemma",
        variant_type="contextual"
    )
}


def get_config(config_name: str = "baseline") -> ExperimentConfig:
    """
    Get a predefined configuration.
    
    Args:
        config_name (str): Name of the configuration
    
    Returns:
        ExperimentConfig: The configuration object
    """
    if config_name in DEFAULT_CONFIGS:
        return DEFAULT_CONFIGS[config_name]
    else:
        raise ValueError(f"Unknown configuration: {config_name}")
