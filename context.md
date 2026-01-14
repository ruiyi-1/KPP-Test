# KPP 驾考题库（KPP01）抓取与 Web 化项目

## 项目背景

原始题库练习依赖第三方 App，广告多、体验差。目标是把题目与答案整理成结构化数据，并在 `web/` 内提供一个无广告的移动端练习/考试页面。

## 当前题库数据源

### 数据来源页面

抓取来源为 `kpptestmy.com` 的公开练习页：

- **Section A**：`https://kpptestmy.com/section-a/` 下所有 Question Set
- **Section B**：`https://kpptestmy.com/section-b/` 下所有 Question Set
- **Section C**：`https://kpptestmy.com/section-c/` 下所有 Question Set

### 明确不产出"题目"的页面

以下页面在 HTML 结构中不包含题目组件（无 `wpvq-question`），因此不会产出可答题题目：

- `https://kpptestmy.com/section-a/road-signs-in-malaysia/`
- `https://kpptestmy.com/section-c/kejara-system/`

另外：

- `https://kpptestmy.com/simulation-test/` 页面本身不提供固定题库（页面说明为 50 题模拟，题目是随机抽取），因此不作为新增题目来源。

## 抓取实现说明

### 技术栈

- **静态解析**：`requests` + `beautifulsoup4`
- **动态交互拿答案**：`selenium`（headless Chrome）+ `webdriver-manager`
- **图片下载/校验**：`Pillow`

### 核心策略（两阶段）

#### 第一阶段：收集题目与选项

- 解析每个 set 页面，提取题干、选项（A/B/C/D）、题目/选项图片 URL
- 图片下载到 `web/public/images/...`（以题库 JSON 里的相对路径引用）
- 过滤广告/插入内容（例如中间插入的广告 DOM），避免误识别为题目节点
- 记录临时定位信息（例如 `data-questionid` / 索引），用于第二阶段定位题目

#### 第二阶段：逐题点击选项识别正确答案

- 对每个 set 页面，用 Selenium 逐题逐选项点击
- 通过页面反馈判断正确项（例如绿色背景、`wpvq-true` 等提示/样式）
- 将 `correctAnswer` 写回题目对象

## 题库输出（前端数据源）

前端统一从下面文件读取题库：

- **题库文件**：`web/src/data/questions.json`
- **读取入口**：`web/src/utils/index.ts`（`import questionsData from '../data/questions.json'`）

该 JSON 结构为：

```json
{
  "total": 450,
  "questions": [
    {
      "id": "section-a-a-question-set-1-q1",
      "question": "....",
      "questionType": "text",
      "options": [
        { "type": "text", "label": "A", "content": "..." },
        { "type": "image", "label": "B", "content": "images/options/xxx.png" }
      ],
      "correctAnswer": "C",
      "questionImages": ["images/questions/xxx.png"],
      "translationKey": "section-a-a-question-set-1-q1"
    }
  ]
}
```

### 当前题目数量（2026-01-14）

- **总题数**：450 道
- **答案覆盖率**：100%（450/450）
- **分布**：
  - Section A：149 道
  - Section B：218 道
  - Section C：83 道

> 网站文案提到 "500 questions"，但基于上述所有可定位到的题库页面（含 sitemap 与菜单入口）目前只能稳定抽取到 450 道可交互选择题；其余差异可能来自非题库内容、站点版本差异，或其他未公开入口。

## Web 应用功能

### 主要页面

1. **练习页面（Practice）**
   - 逐题浏览模式
   - 支持前进/后退导航
   - 选择答案后立即显示正确/错误
   - 支持跳转到指定题目
   - 可切换显示/隐藏中文翻译

2. **模拟考试页面（Exam）**
   - 随机抽取 50 道题目
   - 42 道通过标准（84%）
   - 支持暂停和恢复功能
   - 完成后显示详细结果和错题列表
   - 错题可跳转到复习页面查看

3. **设置页面（Settings）**
   - 语言切换（英文/中文）
   - 默认显示翻译设置
   - 所有设置持久化到 localStorage

4. **复习页面（Review）**
   - 查看所有题目
   - 显示正确答案
   - 支持切换显示/隐藏翻译

### 技术实现

- **框架**：React 18 + TypeScript
- **构建工具**：Vite
- **UI 库**：Ant Design Mobile
- **国际化**：react-i18next
- **状态管理**：React Hooks + localStorage
- **错误处理**：ErrorBoundary 组件

### 数据加载

- 题目数据：从 `web/src/data/questions.json` 静态导入
- 翻译数据：从 `web/public/translations/` 动态加载
- 图片资源：从 `web/public/images/` 加载

## 如何重新生成题库

### 全量抓取

```bash
# 运行全量抓取脚本
python scripts/scrape_all_sections.py
```

### 数据验证

```bash
# 验证题目数据完整性
python scripts/verify_question_data.py

# 验证图片文件存在性
python scripts/verify_images.py

# 验证图片 hash 一致性
python scripts/verify_by_hash.py
```

### 生成翻译

```bash
# 生成题目翻译数据
python scripts/generate_translations.py

# 检查翻译进度
python scripts/check_translation_progress.py
```

### 核心脚本说明

- **`scripts/web_scraper.py`**：核心抓取逻辑，包含两阶段抓取策略
- **`scripts/scrape_all_sections.py`**：全量抓取入口，遍历所有 Section
- **`scripts/data_clean.py`**：数据清洗和格式化
- **`scripts/data_merge.py`**：合并多个数据文件

## 图片资源管理

### 图片存储结构

```
web/public/images/
├── questions/          # 题目图片
│   └── {question_id}_img_{idx}.png
└── options/            # 选项图片
    └── {question_id}_opt_{label}_{idx}.png
```

### 图片命名规则

- **题目图片**：`{question_id}_img_{idx}.png`
- **选项图片**：`{question_id}_opt_{label}_{idx}.png`

例如：
- `section-a-a-question-set-1-q1_img_0.png`
- `section-a-a-question-set-1-q12_opt_a_0.png`

## 翻译数据管理

### 翻译文件结构

翻译数据存储在 `web/public/translations/` 目录：

```json
{
  "questions": {
    "section-a-a-question-set-1-q1": {
      "question": "中文题目",
      "options": {
        "A": "选项A的中文",
        "B": "选项B的中文",
        "C": "选项C的中文",
        "D": "选项D的中文"
      }
    }
  }
}
```

### 翻译加载机制

1. 应用启动时从 `web/src/i18n/locales/` 加载 UI 文本翻译
2. 异步从 `web/public/translations/` 加载题目翻译数据
3. 翻译数据合并到 i18next 资源中，通过 `t('questions.{translationKey}.question')` 访问

## 旧方案（已弃用）

早期方案基于 **ADB UI 自动化** 从手机 App 抽取题目（易受广告/界面变更影响、维护成本高）。目前已切换为网页抓取作为主数据源。

## 项目维护

### 代码质量

- 使用 TypeScript 严格模式
- 使用 logger 工具替代 console.log（生产环境自动禁用）
- 使用自定义 Hook 统一管理 localStorage
- 组件化设计，代码复用

### 数据更新流程

1. 运行抓取脚本获取最新题目
2. 运行验证脚本检查数据完整性
3. 生成翻译数据（如需要）
4. 更新 `web/src/data/questions.json`
5. 提交代码并部署
