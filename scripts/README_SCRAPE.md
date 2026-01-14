# 重新抓取题目说明

## 修复内容

已修复 `web_scraper.py` 中的图片命名问题：
- **之前**：使用 `int(time.time())` 导致同一秒内多个题目使用相同文件名
- **现在**：使用题目ID生成唯一文件名，格式为 `{question_id}_img_{idx}.png` 和 `{question_id}_opt_{label}_{idx}.png`

## 运行抓取

### 方法1：直接运行（推荐）
```bash
cd /Users/sh01617ml/workspace/KPP
python3 scripts/scrape_all_sections.py
```

### 方法2：后台运行
```bash
cd /Users/sh01617ml/workspace/KPP
nohup python3 scripts/scrape_all_sections.py > scrape.log 2>&1 &
tail -f scrape.log  # 查看日志
```

### 方法3：清理旧图片后重新抓取
```bash
cd /Users/sh01617ml/workspace/KPP
python3 scripts/clean_old_images.py  # 清理旧图片（可选）
python3 scripts/scrape_all_sections.py
```

## 注意事项

1. **抓取时间**：完整抓取所有Section可能需要较长时间（30分钟-1小时），因为需要：
   - 下载所有题目和图片
   - 使用Selenium点击选项检测答案

2. **网络要求**：需要稳定的网络连接访问 kpptestmy.com

3. **Selenium要求**：需要安装Chrome浏览器和ChromeDriver（脚本会自动处理）

4. **进度保存**：抓取进度会保存在 `data/scraper_progress.json`，可以中断后继续

## 验证结果

抓取完成后，运行验证脚本检查结果：
```bash
python3 scripts/verify_by_hash.py
python3 scripts/generate_verification_report.py
```
