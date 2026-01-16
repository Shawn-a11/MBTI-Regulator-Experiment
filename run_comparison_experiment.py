#!/usr/bin/env python3
"""
对比实验脚本：使用相同的人格组合，分别用gpt-4o-mini和gpt-4o作为监管者
"""

import argparse
import subprocess
import sys
from datetime import datetime


def run_experiment(regulator_model, player_model_1, player_model_2, 
                   personality_1, personality_2, game_name, variant_type, rounds):
    """运行单个实验"""
    cmd = [
        sys.executable, "main.py",
        "--regulator_model", regulator_model,
        "--player_model_1", player_model_1,
        "--player_model_2", player_model_2,
        "--personality_1", personality_1,
        "--personality_2", personality_2,
        "--game_name", game_name,
        "--variant_type", variant_type,
        "--rounds", str(rounds)
    ]
    
    print(f"\n{'='*80}")
    print(f"Running experiment with regulator: {regulator_model}")
    print(f"{'='*80}\n")
    
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="Run comparison experiments: gpt-4o-mini vs gpt-4o as regulator"
    )
    
    # 玩家设置（固定）
    parser.add_argument("--player_model_1", type=str, default="gpt-4o-mini",
                       help="Model for player 1")
    parser.add_argument("--player_model_2", type=str, default="gpt-4o-mini",
                       help="Model for player 2")
    
    # 人格设置（固定）
    parser.add_argument("--personality_1", type=str, default="INTJ",
                       help="MBTI personality for player 1")
    parser.add_argument("--personality_2", type=str, default="ENFP",
                       help="MBTI personality for player 2")
    
    # 游戏设置（固定）
    parser.add_argument("--game_name", type=str, default="prisoners_dilemma",
                       choices=["prisoners_dilemma", "stag_hunt", "generic", "chicken", 
                               "coordination", "hawk_dove", "deadlock", "battle_of_sexes"],
                       help="Base game to play")
    parser.add_argument("--variant_type", type=str, default="complex",
                       choices=["complex", "contextual", "multi_stage"],
                       help="Type of variant to generate")
    parser.add_argument("--rounds", type=int, default=7,
                       help="Number of rounds to play")
    
    # 实验控制
    parser.add_argument("--skip_mini", action="store_true",
                       help="Skip gpt-4o-mini experiment")
    parser.add_argument("--skip_4o", action="store_true",
                       help="Skip gpt-4o experiment")
    
    args = parser.parse_args()
    
    print("="*80)
    print("Comparison Experiment: gpt-4o-mini vs gpt-4o as Regulator")
    print("="*80)
    print(f"Personality Pair: {args.personality_1} vs {args.personality_2}")
    print(f"Game: {args.game_name}")
    print(f"Variant Type: {args.variant_type}")
    print(f"Rounds: {args.rounds}")
    print(f"Player Models: {args.player_model_1} / {args.player_model_2}")
    print("="*80)
    
    results = {}
    
    # 实验1：使用gpt-4o-mini作为监管者
    if not args.skip_mini:
        print("\n[Experiment 1/2] Using gpt-4o-mini as regulator...")
        success = run_experiment(
            regulator_model="gpt-4o-mini",
            player_model_1=args.player_model_1,
            player_model_2=args.player_model_2,
            personality_1=args.personality_1,
            personality_2=args.personality_2,
            game_name=args.game_name,
            variant_type=args.variant_type,
            rounds=args.rounds
        )
        results["gpt-4o-mini"] = success
        if success:
            print("\n✓ Experiment 1 completed successfully!")
        else:
            print("\n✗ Experiment 1 failed!")
    else:
        print("\n[Skipping] gpt-4o-mini experiment")
        results["gpt-4o-mini"] = None
    
    # 等待一下，避免API速率限制
    if not args.skip_mini and not args.skip_4o:
        print("\nWaiting 60 seconds before next experiment to avoid rate limits...")
        import time
        time.sleep(60)  # Longer delay for 3 RPM limit
    
    # 实验2：使用gpt-4o作为监管者
    if not args.skip_4o:
        print("\n[Experiment 2/2] Using gpt-4o as regulator...")
        success = run_experiment(
            regulator_model="gpt-4o",
            player_model_1=args.player_model_1,
            player_model_2=args.player_model_2,
            personality_1=args.personality_1,
            personality_2=args.personality_2,
            game_name=args.game_name,
            variant_type=args.variant_type,
            rounds=args.rounds
        )
        results["gpt-4o"] = success
        if success:
            print("\n✓ Experiment 2 completed successfully!")
        else:
            print("\n✗ Experiment 2 failed!")
    else:
        print("\n[Skipping] gpt-4o experiment")
        results["gpt-4o"] = None
    
    # 总结
    print("\n" + "="*80)
    print("Comparison Experiment Summary")
    print("="*80)
    print(f"Personality Pair: {args.personality_1} vs {args.personality_2}")
    print(f"Game: {args.game_name}")
    print(f"Variant Type: {args.variant_type}")
    print(f"Rounds: {args.rounds}")
    print("-"*80)
    
    if results.get("gpt-4o-mini") is not None:
        status = "✓ Success" if results["gpt-4o-mini"] else "✗ Failed"
        print(f"gpt-4o-mini as regulator: {status}")
    
    if results.get("gpt-4o") is not None:
        status = "✓ Success" if results["gpt-4o"] else "✗ Failed"
        print(f"gpt-4o as regulator: {status}")
    
    print("="*80)
    print("\nResults saved in: data/outputs/")
    print("You can compare the variants and game outcomes between the two experiments.")
    print("="*80)


if __name__ == "__main__":
    main()
