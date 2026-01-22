# 访问统计配置说明

## 概述

应用已集成 Google Analytics 4 (GA4)，可以统计以下数据：

- **用户数量**：访问应用的用户总数
- **地区分布**：用户来自哪些国家/地区（GA 自动获取）
- **使用量统计**：
  - 页面访问量（练习、考试、设置等）
  - 用户行为（开始练习、提交答案、开始考试等）
  - 功能使用频率

## 配置步骤

### 1. 创建 Google Analytics 账户

1. 访问 [Google Analytics](https://analytics.google.com/)
2. 使用 Google 账户登录
3. 创建新的 GA4 属性（如果还没有）

### 2. 获取 Measurement ID

1. 在 GA 管理界面，进入"管理" -> "数据流"
2. 选择或创建网站数据流
3. 复制 **Measurement ID**（格式：`G-XXXXXXXXXX`）

### 3. 配置环境变量

在 `web` 目录下创建 `.env` 文件：

```bash
# .env
VITE_GA_MEASUREMENT_ID=G-XXXXXXXXXX
```

**注意：**
- `.env` 文件已添加到 `.gitignore`，不会被提交到 Git
- 不要将 Measurement ID 提交到代码仓库

### 4. 重新构建应用

```bash
cd web
npm run build
```

## 统计的事件类型

### 页面访问
- `/practice` - 练习页面
- `/exam` - 考试页面
- `/settings` - 设置页面
- `/wrong-questions` - 错题集页面

### 用户行为事件

#### 练习相关
- `practice_start` - 开始练习
- `practice_next` - 下一题
- `practice_previous` - 上一题
- `practice_submit` - 提交答案
- `practice_add_to_wrong_set` - 加入错题集
- `practice_toggle_translation` - 切换翻译显示

#### 考试相关
- `exam_start` - 开始考试
- `exam_pause` - 暂停考试
- `exam_resume` - 恢复考试
- `exam_submit` - 提交考试
- `exam_time_up` - 时间到
- `exam_exit` - 退出考试

#### 错题集相关
- `wrong_questions_view` - 查看错题集
- `wrong_questions_clear_all` - 清空全部
- `wrong_questions_remove` - 移除单个错题
- `wrong_questions_start_practice` - 开始练习错题

#### 设置相关
- `settings_change_language` - 切换语言
- `settings_toggle_translation` - 切换翻译设置
- `settings_change_exam_question_count` - 修改考试题目数量
- `settings_change_passing_score` - 修改及格分数
- `settings_change_exam_duration` - 修改考试时长

## 查看统计数据

1. 登录 [Google Analytics](https://analytics.google.com/)
2. 选择对应的 GA4 属性
3. 在"报告"中查看：
   - **实时**：当前在线用户
   - **获取**：用户来源和地区
   - **参与度**：页面访问和事件统计
   - **用户**：用户数量和特征

## 隐私保护

- ✅ 已启用 IP 匿名化（`anonymize_ip: true`）
- ✅ 不收集个人身份信息
- ✅ 仅用于了解应用使用情况
- ✅ 符合 GDPR 和隐私保护要求

## 故障排除

### 统计不工作？

1. **检查环境变量**
   - 确认 `.env` 文件存在且格式正确
   - 确认 `VITE_GA_MEASUREMENT_ID` 已设置

2. **检查浏览器控制台**
   - 打开开发者工具（F12）
   - 查看 Console 是否有错误信息
   - 应该看到 `[Analytics] Google Analytics initialized` 消息

3. **检查网络请求**
   - 在 Network 标签中查找 `gtag/js` 请求
   - 确认请求成功（状态码 200）

4. **验证 GA 配置**
   - 在 GA 中查看"实时"报告
   - 访问应用后应该能看到实时访问数据

### 开发环境测试

在开发模式下，统计功能也会工作。可以在浏览器控制台看到统计日志。

## 禁用统计

如果不想使用统计功能，只需：
1. 不设置 `VITE_GA_MEASUREMENT_ID` 环境变量
2. 或设置为空字符串

应用会正常运行，只是不会发送统计数据。
