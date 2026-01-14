#!/usr/bin/env python3
"""
自动翻译题目脚本
功能：使用翻译API为所有题目生成中文翻译
"""

import json
from pathlib import Path
import time
from typing import Dict, Optional

# 配置
WEB_DIR = Path(__file__).parent.parent / "web"
QUESTIONS_FILE = WEB_DIR / "src" / "data" / "questions.json"
TRANSLATIONS_FILE = WEB_DIR / "public" / "translations" / "zh.json"

def translate_text(text: str, target_lang: str = "zh", max_retries: int = 3) -> Optional[str]:
    """
    翻译文本
    这里使用简单的占位实现，实际可以使用翻译API
    """
    if not text or not text.strip():
        return None
    
    # 尝试使用deep-translator库
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source='en', target='zh-CN')
        
        # 重试机制
        for attempt in range(max_retries):
            try:
                translated = translator.translate(text)
                return translated
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1)  # 等待后重试
                    continue
                else:
                    raise e
    except ImportError:
        print("⚠️  deep-translator未安装，使用占位翻译")
        print("   安装方法: pip install deep-translator")
        return f"[待翻译] {text}"
    except Exception as e:
        print(f"⚠️  翻译失败: {e}")
        return None  # 返回None，让调用者决定如何处理

def translate_questions(questions: list, translations: Dict) -> Dict:
    """翻译所有题目"""
    total = len(questions)
    translated_count = 0
    skipped_count = 0
    
    print(f"\n🔄 开始翻译 {total} 道题目...")
    print("   注意: 翻译可能需要一些时间，请耐心等待...")
    
    for idx, question in enumerate(questions, 1):
        question_id = question.get("id")
        if not question_id:
            continue
        
        # 检查是否已有翻译
        if question_id in translations:
            existing = translations[question_id]
            # 如果题目和所有选项都有翻译，跳过
            if existing.get("question") and all(
                existing.get("options", {}).get(label)
                for label in ["A", "B", "C", "D"]
                if any(opt.get("label") == label for opt in question.get("options", []))
            ):
                skipped_count += 1
                if idx % 50 == 0:
                    print(f"   进度: {idx}/{total} (已跳过: {skipped_count})")
                continue
        
        # 翻译题目
        question_text = question.get("question", "")
        if question_text:
            # 检查是否已有翻译
            if question_id not in translations:
                translations[question_id] = {"question": "", "options": {}}
            
            if not translations[question_id].get("question"):
                translated_question = translate_text(question_text)
                if translated_question:
                    translations[question_id]["question"] = translated_question
                    time.sleep(0.2)  # 避免请求过快
                else:
                    print(f"   警告: 题目 {question_id} 翻译失败，跳过")
        
        # 翻译选项
        for option in question.get("options", []):
            option_label = option.get("label", "")
            option_content = option.get("content", "")
            
            if option_label and option_content:
                if question_id not in translations:
                    translations[question_id] = {"question": "", "options": {}}
                if "options" not in translations[question_id]:
                    translations[question_id]["options"] = {}
                
                # 检查是否已有翻译
                if not translations[question_id]["options"].get(option_label):
                    translated_option = translate_text(option_content)
                    if translated_option:
                        translations[question_id]["options"][option_label] = translated_option
                        time.sleep(0.2)  # 避免请求过快
        
        translated_count += 1
        
        # 每翻译10道题目保存一次（防止数据丢失）
        if idx % 10 == 0:
            save_translations(translations)
            print(f"   进度: {idx}/{total} (已翻译: {translated_count}, 已跳过: {skipped_count})")
    
    return translations

def save_translations(translations: Dict):
    """保存翻译数据"""
    output = {"questions": translations}
    with open(TRANSLATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

def main():
    """主函数"""
    print("=" * 60)
    print("🌐 自动翻译题目")
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
    
    # 读取现有翻译（如果有）
    translations = {}
    if TRANSLATIONS_FILE.exists():
        print(f"\n📖 读取现有翻译: {TRANSLATIONS_FILE}")
        try:
            with open(TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                translations = existing_data.get("questions", {})
            print(f"✓ 找到 {len(translations)} 个现有翻译")
        except Exception as e:
            print(f"⚠️  读取现有翻译失败: {e}")
    
    # 翻译题目
    translations = translate_questions(questions, translations)
    
    # 保存翻译
    print(f"\n💾 保存翻译数据: {TRANSLATIONS_FILE}")
    save_translations(translations)
    print("✓ 翻译数据已保存")
    
    # 统计信息
    translated_questions = sum(1 for t in translations.values() if t.get("question"))
    translated_options = sum(
        len([v for v in t.get("options", {}).values() if v])
        for t in translations.values()
    )
    
    print("\n" + "=" * 60)
    print("📊 翻译统计:")
    print(f"  总题目数: {total}")
    print(f"  已翻译题目: {translated_questions}")
    print(f"  已翻译选项: {translated_options}")
    print(f"  翻译文件: {TRANSLATIONS_FILE}")
    print("=" * 60)
    
    print("\n💡 提示:")
    print("   - 如果翻译不完整，可以再次运行此脚本继续翻译")
    print("   - 翻译使用Google翻译API，可能需要网络连接")
    print("   - 如果遇到翻译限制，请稍后再试")

if __name__ == "__main__":
    main()
