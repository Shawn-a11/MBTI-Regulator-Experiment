# GitHub上传指南

## 当前状态
✅ Git仓库已初始化
✅ 代码已提交（29个文件，3224行）
✅ Remote已配置（但仓库尚未创建）

## 上传步骤

### 步骤1: 在GitHub上创建仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - **Repository name**: `MBTI-Regulator-Experiment`
   - **Description**: `Regulator Agent for generating game variants to amplify MBTI personality differences`
   - **Visibility**: Public 或 Private（根据你的选择）
   - **不要**勾选 "Initialize this repository with a README"（因为我们已经有了）
3. 点击 "Create repository"

### 步骤2: 推送代码

创建仓库后，运行以下命令：

```bash
cd /Users/shawn/LLM_Based_Agent/MBTI-Regulator-Experiment

# 如果使用HTTPS（需要GitHub token）
git remote set-url origin https://github.com/Shawn-a11/MBTI-Regulator-Experiment.git
git branch -M main
git push -u origin main

# 或者如果使用SSH
git remote set-url origin git@github.com:Shawn-a11/MBTI-Regulator-Experiment.git
git branch -M main
git push -u origin main
```

### 步骤3: 验证

推送成功后，访问：
https://github.com/Shawn-a11/MBTI-Regulator-Experiment

## 如果遇到认证问题

### HTTPS方式
如果使用HTTPS，需要配置Personal Access Token：
1. 访问 https://github.com/settings/tokens
2. 生成新token（需要 `repo` 权限）
3. 推送时使用token作为密码

### SSH方式
如果使用SSH，确保已配置SSH key：
```bash
# 检查SSH key
ls -la ~/.ssh/id_rsa.pub

# 如果没有，生成新的
ssh-keygen -t ed25519 -C "shuwen8681@gmail.com"

# 添加到GitHub
cat ~/.ssh/id_rsa.pub
# 然后复制到 https://github.com/settings/keys
```

## 快速脚本

也可以使用提供的脚本：
```bash
./push_to_github.sh
```
