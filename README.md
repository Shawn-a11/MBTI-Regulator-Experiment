# MBTI Regulator Experiment

## 项目独立性

**本项目是完全独立的**，不依赖 `MBTI-in-Thoughts` 项目。所有必要的依赖文件都已复制到 `dependencies/` 目录中。

## 项目位置

本项目位于 `/Users/shawn/LLM_Based_Agent/MBTI-Regulator-Experiment/`，与 `MBTI-in-Thoughts` 和 `mbti-dating-app` 同级。

## 实验概述

本实验设计了一个**监管者Agent（Regulator Agent）**作为出题者，用于动态生成博弈问题的变体，以更好地突出不同MBTI人格在博弈中的行为差异。

### 核心创新点

1. **监管者Agent（出题者）**：使用高级API（如gpt-4o）生成博弈问题的变体
2. **动态问题生成**：基于原始博弈问题prompt，生成更复杂、更具挑战性的变体
3. **API层级控制**：确保出题agent的API等级 ≥ 做题agent的API等级
4. **人格差异放大**：通过更复杂的问题变体，放大不同MBTI人格的行为差异

### 研究问题

1. **问题复杂度对MBTI人格表现的影响**：更复杂的问题是否能更好地突出人格差异？
2. **高级模型生成的问题质量**：高级模型生成的问题变体是否更有效？
3. **动态vs静态问题**：动态生成的问题是否比静态问题更能揭示人格特征？
4. **API层级效应**：不同API层级组合对实验结果的影响

## 实验设计

### 实验设置

- **监管者Agent**：使用高级API（gpt-4o）
- **做题Agent**：使用低级别API（gpt-4o-mini），保持原有数量（2个）
- **博弈游戏**：囚徒困境、猎鹿博弈等
- **MBTI人格**：16种MBTI类型组合

### 实验流程

1. **问题生成阶段**：监管者Agent基于原始博弈问题prompt生成变体
2. **游戏执行阶段**：两个做题Agent使用生成的变体进行博弈
3. **结果分析阶段**：分析不同MBTI人格在变体问题中的表现差异

## 文件结构

```
MultiAgent-GameTheory-Regulator/
├── README.md                    # 本文件
├── regulator_agent.py           # 监管者Agent实现
├── game_variant_generator.py    # 问题变体生成器
├── run_regulated_game.py        # 带监管者的游戏运行逻辑
├── main.py                      # 主入口
├── config.py                    # 配置管理
├── run_experiments.sh           # 批量实验脚本
└── EXPERIMENT_DESIGN.md         # 详细实验设计文档
```

## 使用方法

### 基本使用

```bash
python main.py \
    --regulator_model gpt-4o \
    --player_model_1 gpt-4o-mini \
    --player_model_2 gpt-4o-mini \
    --personality_1 INTJ \
    --personality_2 ENFP \
    --game_name prisoners_dilemma \
    --rounds 7
```

### 批量实验

```bash
./run_experiments.sh
```

## 预期结果

1. **人格差异放大**：在监管者生成的问题变体中，不同MBTI人格的行为差异更加明显
2. **问题质量提升**：高级模型生成的问题变体质量更高，更能揭示人格特征
3. **研究价值**：为顶级CS会议（如NeurIPS, ICML, AAAI）提供高质量研究结果

## 引用

如果使用本实验代码，请引用原始MBTI-in-Thoughts项目。
