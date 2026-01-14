# KPP 驾考题库 Web 应用

## 项目简介

本项目是一个马来西亚 KPP 驾考题库的 Web 应用，提供无广告的移动端练习和模拟考试功能。题目数据通过网页抓取从 `kpptestmy.com` 获取，并提供了完整的英文原文和中文翻译支持。

## 功能特性

- ✅ **题目练习**：逐题练习模式，支持查看答案和翻译
- ✅ **模拟考试**：50道题随机抽取，42道通过标准，支持暂停和恢复
- ✅ **错题复习**：查看考试中的错题及正确答案
- ✅ **国际化支持**：英文原文 + 中文翻译，可切换显示
- ✅ **移动端优化**：H5 适配的移动端界面（React + Ant Design Mobile）
- ✅ **数据完整**：450 道题目，100% 答案覆盖率
- ✅ **图片支持**：支持题目和选项中的图片显示

## 技术栈

### 前端
- **React 18** + **TypeScript**
- **Vite** - 构建工具
- **Ant Design Mobile** - UI 组件库
- **react-i18next** - 国际化支持

### 数据抓取
- **Python 3.8+**
- **Selenium** - 动态网页交互
- **BeautifulSoup4** - HTML 解析
- **requests** - HTTP 请求

## 项目结构

```
KPP/
├── data/                    # 题目数据
│   ├── questions/          # 原始题目数据
│   └── scraper_progress.json
├── docs/                   # 文档
│   └── ui_element_reference.md
├── scripts/                # 数据抓取脚本
│   ├── web_scraper.py      # 核心抓取脚本
│   ├── scrape_all_sections.py  # 全量抓取
│   ├── verify_*.py         # 数据验证脚本
│   └── translate_questions.py   # 翻译生成脚本
├── web/                    # Web 应用
│   ├── src/
│   │   ├── components/     # React 组件
│   │   │   ├── QuestionCard/    # 题目卡片
│   │   │   ├── OptionItem/      # 选项组件
│   │   │   ├── ExamResult/       # 考试结果
│   │   │   ├── LanguageToggle/  # 语言切换
│   │   │   └── ErrorBoundary/   # 错误边界
│   │   ├── pages/          # 页面组件
│   │   │   ├── Practice/        # 练习页面
│   │   │   ├── Exam/            # 考试页面
│   │   │   ├── Review/          # 复习页面
│   │   │   └── Settings/        # 设置页面
│   │   ├── hooks/          # 自定义 Hooks
│   │   │   └── useLocalStorage.ts
│   │   ├── utils/          # 工具函数
│   │   │   ├── index.ts        # 题目数据加载
│   │   │   └── logger.ts        # 日志工具
│   │   ├── i18n/          # 国际化配置
│   │   │   ├── config.ts
│   │   │   └── locales/        # 翻译文件
│   │   ├── data/          # 题目数据
│   │   │   └── questions.json  # 450 道题目
│   │   └── types/         # TypeScript 类型定义
│   ├── public/
│   │   ├── images/        # 题目和选项图片
│   │   └── translations/  # 题目翻译数据
│   └── package.json
├── README.md              # 项目说明
├── context.md            # 详细需求文档
└── requirements.txt      # Python 依赖
```

## 快速开始

### 环境要求

1. **Node.js 16+** 和 **npm**
2. **Python 3.8+**（仅用于数据抓取）

### 安装和运行

#### Web 应用

```bash
# 进入 web 目录
cd web

# 安装依赖
npm install

# 开发模式运行
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

#### 数据抓取（可选）

如果需要重新抓取题目数据：

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 运行全量抓取
python scripts/scrape_all_sections.py
```

## 题目数据

- **总题数**：450 道
- **答案覆盖率**：100%（450/450）
- **分布**：
  - Section A：149 道
  - Section B：218 道
  - Section C：83 道
- **数据文件**：`web/src/data/questions.json`
- **图片资源**：`web/public/images/`

## 主要功能说明

### 练习模式
- 逐题浏览，支持前进/后退
- 选择答案后立即显示正确/错误
- 支持跳转到指定题目
- 可切换显示/隐藏中文翻译

### 模拟考试
- 随机抽取 50 道题目
- 42 道通过标准（84%）
- 支持暂停和恢复
- 完成后显示详细结果和错题列表

### 设置
- 语言切换（英文/中文）
- 默认显示翻译设置
- 数据持久化到 localStorage

## 开发说明

### 代码规范
- 使用 TypeScript 严格模式
- 使用 logger 工具替代 console.log（生产环境自动禁用）
- 使用自定义 Hook 统一管理 localStorage
- 组件化设计，代码复用

### 数据更新流程
1. 运行 `scripts/scrape_all_sections.py` 抓取最新题目
2. 运行验证脚本检查数据完整性
3. 生成翻译数据（如需要）
4. 更新 `web/src/data/questions.json`

## 部署

项目支持部署到 GitHub Pages 或其他静态托管服务：

```bash
cd web
npm run build
# 将 dist/ 目录部署到静态服务器
```

## 注意事项

1. **数据来源**：题目数据来自 `kpptestmy.com`，仅用于学习目的
2. **图片资源**：题目和选项图片存储在 `web/public/images/` 目录
3. **翻译数据**：中文翻译存储在 `web/public/translations/` 目录
4. **浏览器兼容**：建议使用现代浏览器（Chrome、Safari、Firefox 等）

## 详细文档

请查看 [context.md](./context.md) 了解详细的项目需求和技术实现说明。

## 支持项目

如果这个项目对你有帮助，欢迎打赏支持：

[![打赏](https://img.shields.io/badge/打赏-支持项目-ff6b6b?style=flat-square)](https://qr.alipay.com/fkx10871ew38ukfqghwjx86)

<div align="center">

### 💰 支付宝打赏

[![支付宝二维码](./docs/images/alipay-qrcode.png)](https://qr.alipay.com/fkx10871ew38ukfqghwjx86)

**扫描二维码或 [点击这里](https://qr.alipay.com/fkx10871ew38ukfqghwjx86) 进行打赏**

感谢你的支持！🙏

</div>

## 许可证

本项目仅用于个人学习使用，请勿用于商业用途。
