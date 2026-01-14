#!/usr/bin/env python3
"""
生成所有题目的翻译数据脚本
功能：从questions.json读取所有题目，生成翻译文件结构
"""

import json
from pathlib import Path
from typing import Dict, List

# 配置
WEB_DIR = Path(__file__).parent.parent / "web"
QUESTIONS_FILE = WEB_DIR / "src" / "data" / "questions.json"
OUTPUT_ZH_FILE = WEB_DIR / "public" / "translations" / "zh.json"
OUTPUT_EN_FILE = WEB_DIR / "public" / "translations" / "en.json"

def generate_translation_structure(questions: List[Dict]) -> Dict[str, Dict]:
    """为所有题目生成翻译数据结构"""
    translations = {}
    
    for question in questions:
        question_id = question.get("id")
        if not question_id:
            continue
        
        # 使用题目ID作为translationKey
        translation_key = question_id
        
        # 生成翻译结构
        translation_data = {
            "question": "",  # 题目的中文翻译（待填充）
            "options": {}
        }
        
        # 为每个选项生成翻译结构
        for option in question.get("options", []):
            option_label = option.get("label", "")
            if option_label:
                translation_data["options"][option_label] = ""  # 选项的中文翻译（待填充）
        
        translations[translation_key] = translation_data
    
    return translations

def main():
    """主函数"""
    print("=" * 60)
    print("🌐 生成题目翻译数据")
    print("=" * 60)
    
    # 读取题目数据
    if not QUESTIONS_FILE.exists():
        print(f"❌ 题目文件不存在: {QUESTIONS_FILE}")
        return
    
    print(f"\n📖 读取题目数据: {QUESTIONS_FILE}")
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        questions_data = json.load(f)
    
    questions = questions_data.get("questions", [])
    total = len(questions)
    print(f"✓ 找到 {total} 道题目")
    
    if total == 0:
        print("⚠️  没有题目数据")
        return
    
    # 生成翻译结构
    print("\n🔨 生成翻译数据结构...")
    translations = generate_translation_structure(questions)
    print(f"✓ 生成了 {len(translations)} 个题目的翻译结构")
    
    # 确保输出目录存在
    OUTPUT_ZH_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 生成中文翻译文件
    print(f"\n💾 保存中文翻译文件: {OUTPUT_ZH_FILE}")
    zh_output = {
        "questions": translations
    }
    with open(OUTPUT_ZH_FILE, "w", encoding="utf-8") as f:
        json.dump(zh_output, f, indent=2, ensure_ascii=False)
    print("✓ 中文翻译文件已保存")
    
    # 生成英文翻译文件（英文题目本身就是英文，所以直接使用原文本）
    print(f"\n💾 生成英文翻译文件: {OUTPUT_EN_FILE}")
    en_translations = {}
    for question in questions:
        question_id = question.get("id")
        if not question_id:
            continue
        
        en_translation = {
            "question": question.get("question", ""),
            "options": {}
        }
        
        for option in question.get("options", []):
            option_label = option.get("label", "")
            if option_label:
                en_translation["options"][option_label] = option.get("content", "")
        
        en_translations[question_id] = en_translation
    
    en_output = {
        "questions": en_translations
    }
    with open(OUTPUT_EN_FILE, "w", encoding="utf-8") as f:
        json.dump(en_output, f, indent=2, ensure_ascii=False)
    print("✓ 英文翻译文件已保存")
    
    # 统计信息
    print("\n" + "=" * 60)
    print("📊 生成统计:")
    print(f"  总题目数: {total}")
    print(f"  翻译结构: {len(translations)} 个")
    print(f"  中文翻译文件: {OUTPUT_ZH_FILE}")
    print(f"  英文翻译文件: {OUTPUT_EN_FILE}")
    print("\n⚠️  注意: 中文翻译文件中的翻译内容需要手动填充或使用翻译API填充")
    print("=" * 60)

if __name__ == "__main__":
    main()
