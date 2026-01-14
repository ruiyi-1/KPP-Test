#!/bin/bash
# 等待抓取任务完成并验证图片路径

echo "等待抓取任务完成..."
PID=$1

if [ -z "$PID" ]; then
    PID=$(pgrep -f "scrape_all_sections.py" | head -1)
fi

if [ -z "$PID" ]; then
    echo "未找到运行中的抓取任务"
    exit 1
fi

echo "监控任务 PID: $PID"

# 等待任务完成
while ps -p $PID > /dev/null 2>&1; do
    echo -n "."
    sleep 5
done

echo ""
echo "✅ 抓取任务已完成，开始验证图片路径..."

# 运行验证脚本
cd "$(dirname "$0")/.."
python3 scripts/verify_images.py
