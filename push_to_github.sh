#!/bin/bash
# Script to push MBTI-Regulator-Experiment to GitHub

REPO_NAME="MBTI-Regulator-Experiment"
GITHUB_USER="Shawn-a11"  # 从git config获取

echo "准备上传 $REPO_NAME 到 GitHub..."
echo ""

# 检查是否已有remote
if git remote get-url origin 2>/dev/null; then
    echo "⚠️  已存在 remote 'origin'"
    echo "当前 remote URL: $(git remote get-url origin)"
    read -p "是否要更新? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "取消操作"
        exit 1
    fi
fi

# 提示用户输入GitHub仓库URL或名称
echo ""
echo "请选择以下方式之一："
echo "1. 如果GitHub仓库已创建，请输入完整URL（如: https://github.com/$GITHUB_USER/$REPO_NAME.git）"
echo "2. 如果还未创建，请先在GitHub上创建仓库，然后输入URL"
echo ""
read -p "请输入GitHub仓库URL（或按Enter使用默认名称）: " REPO_URL

if [ -z "$REPO_URL" ]; then
    REPO_URL="https://github.com/$GITHUB_USER/$REPO_NAME.git"
    echo "使用默认URL: $REPO_URL"
fi

# 添加remote
echo ""
echo "添加 remote 'origin'..."
git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"

# 检查连接
echo "检查GitHub连接..."
if git ls-remote --heads origin 2>/dev/null; then
    echo "✅ 成功连接到GitHub仓库"
else
    echo "⚠️  无法连接到GitHub仓库，请确认："
    echo "   1. 仓库URL正确"
    echo "   2. 仓库已创建"
    echo "   3. 有访问权限"
    read -p "是否继续推送? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 推送代码
echo ""
echo "推送代码到GitHub..."
git branch -M main
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 成功上传到GitHub!"
    echo "仓库地址: $REPO_URL"
else
    echo ""
    echo "❌ 推送失败，请检查："
    echo "   1. GitHub认证（SSH key或token）"
    echo "   2. 仓库权限"
    echo "   3. 网络连接"
fi
