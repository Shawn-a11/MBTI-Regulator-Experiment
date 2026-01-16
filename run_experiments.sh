#!/bin/bash

# Batch experiment script for regulated game experiments
# This script runs multiple experiments with different configurations

# Set default values
REGULATOR_MODEL=${REGULATOR_MODEL:-"gpt-4o"}
PLAYER_MODEL=${PLAYER_MODEL:-"gpt-4o-mini"}
GAME_NAME=${GAME_NAME:-"prisoners_dilemma"}
ROUNDS=${ROUNDS:-7}
VARIANT_TYPE=${VARIANT_TYPE:-"complex"}

# Create output directory
mkdir -p data/outputs

# Define personality pairs to test (can be expanded)
PERSONALITY_PAIRS=(
    "INTJ ENFP"
    "ESTJ ISFP"
    "ENTP ISFJ"
    "ESTP INFJ"
    "INTP ESFP"
    "ENTJ INFP"
    "ESFJ ISTP"
    "ENFJ ISTJ"
)

echo "=========================================="
echo "Regulated Game Experiments"
echo "=========================================="
echo "Regulator Model: $REGULATOR_MODEL"
echo "Player Model: $PLAYER_MODEL"
echo "Game: $GAME_NAME"
echo "Variant Type: $VARIANT_TYPE"
echo "Rounds: $ROUNDS"
echo "=========================================="
echo ""

# Run experiments for each personality pair
for pair in "${PERSONALITY_PAIRS[@]}"; do
    IFS=' ' read -r p1 p2 <<< "$pair"
    echo "Running experiment: $p1 vs $p2"
    
    python main.py \
        --regulator_model "$REGULATOR_MODEL" \
        --player_model_1 "$PLAYER_MODEL" \
        --player_model_2 "$PLAYER_MODEL" \
        --personality_1 "$p1" \
        --personality_2 "$p2" \
        --game_name "$GAME_NAME" \
        --variant_type "$VARIANT_TYPE" \
        --rounds "$ROUNDS"
    
    echo "Completed: $p1 vs $p2"
    echo "----------------------------------------"
    sleep 2  # Small delay between experiments
done

echo ""
echo "=========================================="
echo "All experiments completed!"
echo "=========================================="
