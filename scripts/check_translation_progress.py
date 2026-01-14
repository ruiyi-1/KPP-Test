#!/usr/bin/env python3
"""
检查翻译进度脚本
"""

import json
from pathlib import Path

WEB_DIR = Path(__file__).parent.parent / "web"
TRANSLATIONS_FILE = WEB_DIR / "public" / "translations" / "zh.json"

def check_progress():
    with open(TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    questions = data.get("questions", {})
    total = len(questions)
    
    translated_questions = 0
    translated_options_total = 0
    incomplete_questions = []
    
    for q_id, q_data in questions.items():
        has_question = bool(q_data.get("question", "").strip())
        options = q_data.get("options", {})
        translated_options = sum(1 for v in options.values() if v and v.strip())
        total_options = len(options)
        
        if has_question and translated_options == total_options:
            translated_questions += 1
            translated_options_total += translated_options
        else:
            incomplete_questions.append({
                "id": q_id,
                "has_question": has_question,
                "translated_options": translated_options,
                "total_options": total_options
            })
    
    print("=" * 60)
    print("📊 翻译进度统计")
    print("=" * 60)
    print(f"总题目数: {total}")
    print(f"已完成翻译: {translated_questions} ({translated_questions/total*100:.1f}%)")
    print(f"待翻译: {total - translated_questions} ({(total-translated_questions)/total*100:.1f}%)")
    print(f"已翻译选项总数: {translated_options_total}")
    print("=" * 60)
    
    if incomplete_questions:
        print(f"\n⚠️  未完成的题目: {len(incomplete_questions)}")
        if len(incomplete_questions) <= 10:
            print("未完成的题目列表:")
            for q in incomplete_questions[:10]:
                print(f"  - {q['id']}: 题目={'✓' if q['has_question'] else '✗'}, 选项={q['translated_options']}/{q['total_options']}")
        else:
            print(f"前10个未完成的题目:")
            for q in incomplete_questions[:10]:
                print(f"  - {q['id']}: 题目={'✓' if q['has_question'] else '✗'}, 选项={q['translated_options']}/{q['total_options']}")

if __name__ == "__main__":
    check_progress()
