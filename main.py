# Copyright (c) 2025 ETH Zurich.
#                    All rights reserved.
#
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# Main entry point for regulated game experiments

import argparse
import json
from datetime import datetime
from run_regulated_game import run_regulated_game


def main(args):
    """
    Main function to run regulated game experiments.
    """
    import sys
    sys.stdout.flush()  # 确保输出立即刷新
    
    print("🚀 程序开始运行...", flush=True)
    
    date_string = datetime.now().strftime("%y%m%d")
    output_dir = "data/outputs/"
    base_game_state_path = f"{date_string}_regulated"
    game_state_path = output_dir + f"{base_game_state_path}.csv"
    
    # Ensure output directory exists
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 80, flush=True)
    print("Regulated Game Experiment", flush=True)
    print("=" * 80, flush=True)
    print(f"Regulator Model: {args.regulator_model}", flush=True)
    print(f"Player 1 Model: {args.player_model_1} ({args.personality_1})", flush=True)
    print(f"Player 2 Model: {args.player_model_2} ({args.personality_2})", flush=True)
    print(f"Base Game: {args.game_name}", flush=True)
    print(f"Variant Type: {args.variant_type}", flush=True)
    print(f"Rounds: {args.rounds}", flush=True)
    print("=" * 80, flush=True)
    print("⏳ 正在初始化游戏...", flush=True)
    
    game_state = run_regulated_game(
        regulator_model_id=args.regulator_model,
        regulator_provider=args.regulator_provider if args.regulator_provider else None,
        player_model_1=args.player_model_1,
        player_provider_1=args.player_provider_1 if args.player_provider_1 else None,
        player_model_2=args.player_model_2,
        player_provider_2=args.player_provider_2 if args.player_provider_2 else None,
        total_rounds=args.rounds,
        personality_key_1=args.personality_1,
        personality_key_2=args.personality_2,
        base_game_name=args.game_name,
        variant_type=args.variant_type,
        file_path=game_state_path
    )
    
    print("\n" + "=" * 80)
    print("Experiment Completed!")
    print("=" * 80)
    print(f"Results saved to: {game_state_path}")
    print(f"Final Scores - Agent 1: {sum(game_state['agent_1_scores'])}, Agent 2: {sum(game_state['agent_2_scores'])}")
    print("=" * 80)


if __name__ == "__main__":
    # Load personality choices from local dependencies
    import sys
    import os
    
    # Use local dependencies directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    priming_path = os.path.join(current_dir, 'dependencies', 'priming', 'priming_without_mention_of_mbti_different_none_with_altruistic_selfish.json')
    
    if os.path.exists(priming_path):
        personality_choices = json.load(open(priming_path)).keys()
    else:
        # Fallback to common MBTI types
        personality_choices = ["INTJ", "ENFP", "ESTJ", "ISFP", "ENTP", "ISFJ", "ESTP", "INFJ", "INTP", "ESFP", "ENTJ", "INFP", "ESFJ", "ISTP", "ENFJ", "ISTJ", "NONE", "EXPERT"]
    
    game_names = ["prisoners_dilemma", "stag_hunt", "generic", "chicken", "coordination", "hawk_dove", "deadlock", "battle_of_sexes"]
    variant_types = ["complex", "contextual", "multi_stage"]
    
    parser = argparse.ArgumentParser(
        description="Run regulated game experiments with regulator agent generating variants"
    )
    
    # Regulator settings
    parser.add_argument("--regulator_model", type=str, 
                       help="Model ID for regulator agent (e.g., gpt-4o)", 
                       default="gpt-4o", required=True)
    parser.add_argument("--regulator_provider", type=str, 
                       help="Provider for regulator model", 
                       required=False)
    
    # Player settings
    parser.add_argument("--player_model_1", type=str, 
                       help="Model ID for player 1 (e.g., gpt-4o-mini)", 
                       required=True)
    parser.add_argument("--player_provider_1", type=str, 
                       help="Provider for player 1 model", 
                       required=False)
    parser.add_argument("--player_model_2", type=str, 
                       help="Model ID for player 2", 
                       required=True)
    parser.add_argument("--player_provider_2", type=str, 
                       help="Provider for player 2 model", 
                       required=False)
    
    # Game settings
    parser.add_argument("--rounds", type=int, 
                       help="Number of rounds to play", 
                       default=7, required=True)
    parser.add_argument("--personality_1", choices=personality_choices, 
                       help="MBTI personality for player 1", 
                       required=True)
    parser.add_argument("--personality_2", choices=personality_choices, 
                       help="MBTI personality for player 2", 
                       required=True)
    parser.add_argument("--game_name", choices=game_names, 
                       help="Base game to play", 
                       required=True)
    parser.add_argument("--variant_type", choices=variant_types, 
                       help="Type of variant to generate", 
                       default="complex")
    
    args = parser.parse_args()
    main(args)
