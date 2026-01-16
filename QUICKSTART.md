# 快速开始指南

## 概述

本实验框架实现了**监管者Agent驱动的博弈实验**，通过动态生成博弈问题变体来放大不同MBTI人格的行为差异。

## 安装与配置

### 1. 环境要求

- Python 3.11.5+
- 已安装MBTI-in-Thoughts项目依赖
- OpenRouter API密钥（配置在`.env`文件中的`OPENROUTER_API_KEY`）

### 2. 目录结构

```
MultiAgent-GameTheory-Regulator/
├── README.md                    # 项目说明
├── EXPERIMENT_DESIGN.md        # 详细实验设计
├── QUICKSTART.md               # 本文件
├── regulator_agent.py          # 监管者Agent实现
├── game_variant_generator.py   # 问题变体生成器
├── run_regulated_game.py       # 游戏运行逻辑
├── main.py                     # 主入口
├── config.py                   # 配置管理
├── models.py                   # 模型加载工具
├── node_helpers.py             # 节点辅助函数
├── test_quick.py              # 快速测试脚本
├── run_experiments.sh          # 批量实验脚本
└── data/outputs/               # 结果输出目录
```

## 快速测试

### 1. 测试监管者Agent

首先测试监管者Agent是否能正常工作：

```bash
cd /Users/shawn/LLM_Based_Agent/MBTI-Regulator-Experiment
python test_quick.py
```

这将：
- 加载基础博弈（囚徒困境）
- 初始化监管者Agent
- 生成一个游戏变体
- 验证变体的有效性

### 2. 运行单个实验

运行一个完整的实验：

```bash
python main.py \
    --regulator_model gpt-4o \
    --player_model_1 gpt-4o-mini \
    --player_model_2 gpt-4o-mini \
    --personality_1 INTJ \
    --personality_2 ENFP \
    --game_name prisoners_dilemma \
    --variant_type complex \
    --rounds 7
```

### 3. 批量实验

运行多个实验：

```bash
# 设置环境变量（可选）
export REGULATOR_MODEL="gpt-4o"
export PLAYER_MODEL="gpt-4o-mini"
export GAME_NAME="prisoners_dilemma"
export VARIANT_TYPE="complex"
export ROUNDS=7

# 运行批量实验
./run_experiments.sh
```

## 参数说明

### 监管者设置

- `--regulator_model`: 监管者使用的模型（推荐：gpt-4o）
- `--regulator_provider`: 模型提供商（可选）

### 玩家设置

- `--player_model_1`: 玩家1的模型（推荐：gpt-4o-mini）
- `--player_provider_1`: 玩家1的模型提供商（可选）
- `--player_model_2`: 玩家2的模型（推荐：gpt-4o-mini）
- `--player_provider_2`: 玩家2的模型提供商（可选）

### 游戏设置

- `--game_name`: 基础博弈类型
  - `prisoners_dilemma`: 囚徒困境
  - `stag_hunt`: 猎鹿博弈
  - `chicken`: 胆小鬼博弈
  - `hawk_dove`: 鹰鸽博弈
  - 等等...

- `--variant_type`: 变体类型
  - `complex`: 增加复杂度
  - `contextual`: 增加情境因素
  - `multi_stage`: 多阶段变体

- `--rounds`: 游戏轮数（默认：7）

### 人格设置

- `--personality_1`: 玩家1的MBTI人格（如：INTJ, ENFP等）
- `--personality_2`: 玩家2的MBTI人格

## 输出结果

实验结果保存在 `data/outputs/` 目录下，CSV格式包含：

- 游戏基本信息（游戏名称、变体类型等）
- 模型配置（监管者模型、玩家模型等）
- 人格信息（两个玩家的MBTI类型）
- 游戏过程数据（消息、行动、得分等）
- 意图分析（诚实性、策略分析等）
- 成本信息（token使用、费用等）

## 实验设计建议

### 1. 小规模预实验

先运行小规模测试验证框架：

```bash
# 测试1：验证监管者能生成变体
python test_quick.py

# 测试2：运行单个实验
python main.py \
    --regulator_model gpt-4o-mini \
    --player_model_1 gpt-4o-mini \
    --player_model_2 gpt-4o-mini \
    --personality_1 INTJ \
    --personality_2 ENFP \
    --game_name prisoners_dilemma \
    --variant_type complex \
    --rounds 3
```

### 2. 对比实验

运行对比实验以验证监管者的效果：

**实验组（使用监管者）：**
```bash
python main.py \
    --regulator_model gpt-4o \
    --player_model_1 gpt-4o-mini \
    --player_model_2 gpt-4o-mini \
    --personality_1 INTJ \
    --personality_2 ENFP \
    --game_name prisoners_dilemma \
    --variant_type complex \
    --rounds 7
```

**对照组（不使用监管者，使用原始问题）：**
```bash
# 使用原始MultiAgent-GameTheory框架
cd ../MultiAgent-GameTheory
python main.py \
    --model_id_1 gpt-4o-mini \
    --model_id_2 gpt-4o-mini \
    --agent_1_persona INTJ \
    --agent_2_persona ENFP \
    --game_name prisoners_dilemma \
    --rounds 7
```

### 3. 大规模实验

运行大规模实验收集数据：

```bash
# 修改 run_experiments.sh 添加更多人格组合
# 然后运行
./run_experiments.sh
```

## 常见问题

### Q1: 导入错误

**错误**: `ModuleNotFoundError: No module named 'games_structures'`

**解决**: 确保在项目根目录运行，或检查路径设置。

### Q2: API密钥错误

**错误**: `AuthenticationError`

**解决**: 检查`.env`文件中的`OPENROUTER_API_KEY`是否正确配置。代码会自动使用OpenRouter API（如果配置了OPENROUTER_API_KEY）。

### Q3: 变体生成失败

**错误**: 监管者无法生成有效变体

**解决**: 
- 检查监管者模型是否有足够权限
- 尝试使用不同的变体类型
- 检查网络连接

### Q4: 成本过高

**解决**:
- 使用`gpt-4o-mini`作为监管者进行测试
- 减少实验轮数
- 使用采样策略减少实验数量

## 下一步

1. ✅ 完成框架搭建
2. ⏳ 运行小规模预实验
3. ⏳ 分析初步结果
4. ⏳ 调整实验设计
5. ⏳ 运行大规模实验
6. ⏳ 数据分析和论文撰写

## 联系与支持

如有问题，请参考：
- `EXPERIMENT_DESIGN.md`: 详细实验设计
- `README.md`: 项目说明
- 原始MBTI-in-Thoughts项目文档
