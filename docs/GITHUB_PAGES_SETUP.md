# GitHub Pages 部署配置指南

## 概述

本项目已配置 GitHub Actions 自动部署到 GitHub Pages。每次推送到 `main` 分支时，会自动构建并部署应用。

## 部署步骤

### 1. 启用 GitHub Pages

1. 进入 GitHub 仓库
2. 点击 **Settings**（设置）
3. 在左侧菜单找到 **Pages**（页面）
4. 在 **Source**（源）部分：
   - 选择 **GitHub Actions**
5. 保存设置

### 2. 配置 Google Analytics（可选）

如果你需要启用访问统计功能：

1. 在仓库 **Settings** -> **Secrets and variables** -> **Actions**
2. 点击 **New repository secret**（新建仓库密钥）
3. 填写信息：
   - **Name（名称）**: `VITE_GA_MEASUREMENT_ID`
   - **Value（值）**: 你的 Google Analytics Measurement ID（格式：`G-XXXXXXXXXX`）
4. 点击 **Add secret**（添加密钥）

**如何获取 Measurement ID：**
- 访问 https://analytics.google.com/
- 创建 GA4 属性
- 在"管理" -> "数据流" -> "网站"中找到 Measurement ID

### 3. 触发部署

部署会在以下情况自动触发：

- **自动触发**：推送到 `main` 分支
- **手动触发**：在 **Actions** 标签页中点击 **Deploy to GitHub Pages** workflow，然后点击 **Run workflow**

### 4. 查看部署状态

1. 进入仓库的 **Actions** 标签页
2. 查看最新的 workflow 运行状态
3. 部署成功后，访问你的 GitHub Pages 地址：
   ```
   https://<你的用户名>.github.io/KPP-Test/
   ```

## 工作流程说明

GitHub Actions workflow 会执行以下步骤：

1. **Checkout**：检出代码
2. **Setup Node.js**：设置 Node.js 环境（版本 20）
3. **Install dependencies**：安装 npm 依赖
4. **Build**：构建应用（使用 GitHub Secret 中的环境变量）
5. **Setup Pages**：配置 Pages
6. **Upload artifact**：上传构建产物
7. **Deploy**：部署到 GitHub Pages

## 环境变量配置

### 本地开发

在 `web` 目录下创建 `.env` 文件：

```bash
VITE_GA_MEASUREMENT_ID=G-XXXXXXXXXX
```

### GitHub Pages

使用 GitHub Secrets 配置：

1. 进入 **Settings** -> **Secrets and variables** -> **Actions**
2. 添加 Secret：`VITE_GA_MEASUREMENT_ID`
3. 值：你的 Measurement ID

**注意：**
- GitHub Secrets 是加密存储的，只有仓库管理员可以查看
- Secret 的值在构建时会被注入到环境变量中
- 如果不需要统计功能，可以不配置此 Secret

## 故障排除

### 部署失败？

1. **检查 Actions 日志**
   - 进入 **Actions** 标签页
   - 查看失败的 workflow 运行
   - 点击查看详细错误信息

2. **常见问题**
   - **构建失败**：检查代码是否有语法错误
   - **权限问题**：确保 GitHub Actions 有 Pages 写入权限
   - **环境变量**：检查 Secret 名称是否正确（`VITE_GA_MEASUREMENT_ID`）

3. **重新部署**
   - 修复问题后，推送代码或手动触发 workflow

### 统计不工作？

1. **检查 Secret 配置**
   - 确认 `VITE_GA_MEASUREMENT_ID` Secret 已正确配置
   - 确认值格式正确（`G-XXXXXXXXXX`）

2. **检查构建日志**
   - 在 Actions 中查看构建步骤
   - 确认环境变量已正确注入

3. **验证部署**
   - 访问部署后的网站
   - 打开浏览器开发者工具（F12）
   - 查看 Console 是否有 `[Analytics] Google Analytics initialized` 消息
   - 查看 Network 标签，确认 `gtag/js` 请求成功

### 页面 404？

1. **检查 base 路径**
   - 确认 `vite.config.ts` 中的 `base` 配置正确
   - 默认应该是 `/KPP-Test/`

2. **检查仓库名称**
   - 如果仓库名称不是 `KPP-Test`，需要修改 `vite.config.ts` 中的 `base` 配置

## 自定义配置

### 修改部署路径

如果仓库名称不是 `KPP-Test`，需要修改：

1. 编辑 `web/vite.config.ts`：
   ```typescript
   base: '/你的仓库名/',
   ```

2. 重新部署

### 添加其他环境变量

如果需要添加其他环境变量：

1. 在 GitHub Secrets 中添加
2. 在 `.github/workflows/deploy.yml` 的 Build 步骤中添加：
   ```yaml
   env:
     VITE_GA_MEASUREMENT_ID: ${{ secrets.VITE_GA_MEASUREMENT_ID }}
     你的其他变量: ${{ secrets.你的其他变量 }}
   ```

## 相关文件

- **部署配置**: `.github/workflows/deploy.yml`
- **构建配置**: `web/vite.config.ts`
- **统计配置**: `web/src/utils/analytics.ts`
- **统计文档**: `web/ANALYTICS.md`
