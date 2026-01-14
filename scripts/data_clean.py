#!/usr/bin/env python3
"""
KPP题目数据清洗脚本
功能：清洗和格式化已采集的题目数据，提取翻译数据
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import os

# 配置
DATA_DIR = Path(__file__).parent.parent / "data"
QUESTIONS_DIR = DATA_DIR / "questions"
TRANSLATIONS_DIR = DATA_DIR / "translations"
IMAGES_DIR = Path(__file__).parent.parent / "images"

def clean_text(text: str) -> str:
    """清洗文本：去除多余的空格和换行"""
    if not text:
        return ""
    # 去除首尾空白
    text = text.strip()
    # 将多个连续空格替换为单个空格
    text = re.sub(r'\s+', ' ', text)
    # 去除多余的换行
    text = re.sub(r'\n+', ' ', text)
    return text

def separate_bilingual_text(text: str) -> Tuple[str, Optional[str]]:
    """分离双语文本（马来文+英文）
    
    Returns:
        (english_text, translation_text): 英文原文和翻译文本
    """
    if not text:
        return "", None
    
    # 尝试识别双语文本的模式
    # 模式1: 马来文句子 + 英文句子（通常英文在马来文后面）
    # 模式2: 马来文 + 空格 + 英文（如 "2 tahun 2 years"）
    
    # 检查是否包含明显的英文单词（大写字母开头的单词通常是英文句子）
    # 或者包含数字+英文的组合（如 "2 years"）
    
    # 简单策略：如果文本包含常见英文单词模式，尝试分离
    # 更复杂的策略需要语言检测库
    
    # 当前策略：保持原样，英文部分作为主要文本
    # 翻译部分（如果有中文）会在后续处理中提取
    
    # 检查是否有中文
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
    
    if has_chinese:
        # 如果有中文，尝试分离
        # 通常格式：英文 + 中文 或 中文 + 英文
        # 这里简单处理：保留英文部分，提取中文部分
        chinese_parts = re.findall(r'[\u4e00-\u9fff]+', text)
        if chinese_parts:
            # 移除中文部分，保留英文
            english_text = re.sub(r'[\u4e00-\u9fff]+', '', text)
            english_text = clean_text(english_text)
            translation_text = ' '.join(chinese_parts)
            return english_text, translation_text
    
    # 如果没有中文，保持原样（马来文+英文混合）
    # 在实际应用中，可能需要将马来文翻译为英文
    # 这里暂时保持原样，英文部分作为主要显示文本
    cleaned = clean_text(text)
    return cleaned, None

def extract_translation_from_text(text: str) -> Optional[str]:
    """从文本中提取翻译部分（中文）"""
    if not text:
        return None
    
    # 提取中文字符
    chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text)
    if chinese_chars:
        return ' '.join(chinese_chars)
    
    return None

def validate_question_data(question_data: Dict) -> Tuple[bool, List[str]]:
    """验证题目数据的完整性"""
    errors = []
    
    # 检查必需字段
    required_fields = ["id", "part", "question_number", "question_text", "options", "correct_answer"]
    for field in required_fields:
        if field not in question_data:
            errors.append(f"缺少必需字段: {field}")
    
    # 检查题目文本
    if "question_text" in question_data:
        if not question_data["question_text"] or not question_data["question_text"].strip():
            errors.append("题目文本为空")
    
    # 检查选项
    if "options" in question_data:
        options = question_data["options"]
        if not isinstance(options, list) or len(options) < 2:
            errors.append("选项数量不足（至少需要2个选项）")
        else:
            # 检查每个选项
            for idx, option in enumerate(options):
                if not isinstance(option, dict):
                    errors.append(f"选项 {idx} 格式错误")
                    continue
                if "label" not in option:
                    errors.append(f"选项 {idx} 缺少label字段")
                if "text" not in option:
                    errors.append(f"选项 {idx} 缺少text字段")
    
    # 检查答案格式
    if "correct_answer" in question_data:
        answer = question_data["correct_answer"]
        if answer is not None:
            if answer not in ["A", "B", "C", "D"]:
                errors.append(f"答案格式错误: {answer}（应为A/B/C/D）")
            # 检查答案是否在选项范围内
            if "options" in question_data and isinstance(question_data["options"], list):
                option_labels = [opt.get("label") for opt in question_data["options"]]
                if answer not in option_labels:
                    errors.append(f"答案 {answer} 不在选项范围内: {option_labels}")
    
    # 检查图片路径
    if "question_images" in question_data:
        for img_path in question_data["question_images"]:
            if img_path:
                full_path = Path(__file__).parent.parent / img_path
                if not full_path.exists():
                    errors.append(f"题目图片不存在: {img_path}")
    
    if "options" in question_data:
        for option in question_data["options"]:
            if isinstance(option, dict) and option.get("image"):
                img_path = option["image"]
                if img_path:
                    full_path = Path(__file__).parent.parent / img_path
                    if not full_path.exists():
                        errors.append(f"选项图片不存在: {img_path}")
    
    return len(errors) == 0, errors

def clean_question_file(question_file: Path) -> Tuple[Dict, Dict]:
    """清洗单个题目文件
    
    Returns:
        (cleaned_question_data, translation_data): 清洗后的题目数据和翻译数据
    """
    with open(question_file, "r", encoding="utf-8") as f:
        question_data = json.load(f)
    
    # 清洗题目文本
    if "question_text" in question_data:
        original_text = question_data["question_text"]
        english_text, translation_text = separate_bilingual_text(original_text)
        question_data["question_text"] = english_text
        
        # 提取翻译（如果有中文）
        chinese_translation = extract_translation_from_text(original_text)
    
    # 清洗选项文本
    translation_options = {}
    if "options" in question_data:
        for option in question_data["options"]:
            if "text" in option:
                original_option_text = option["text"]
                english_option_text, _ = separate_bilingual_text(original_option_text)
                option["text"] = english_option_text
                
                # 提取选项翻译（如果有中文）
                option_label = option.get("label", "")
                chinese_option = extract_translation_from_text(original_option_text)
                if chinese_option and option_label:
                    translation_options[option_label] = chinese_option
    
    # 构建翻译数据
    translation_data = {}
    question_id = question_data.get("id", "")
    if chinese_translation or translation_options:
        translation_data = {
            "question": chinese_translation,
            "options": translation_options
        }
    
    return question_data, translation_data

def main():
    """主函数"""
    print("=" * 60)
    print("🧹 KPP题目数据清洗工具")
    print("=" * 60)
    
    # 确保目录存在
    QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)
    TRANSLATIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 查找所有题目文件
    question_files = sorted(QUESTIONS_DIR.glob("part-*-question-*.json"))
    
    if not question_files:
        print("⚠️  未找到题目文件")
        return
    
    print(f"📂 找到 {len(question_files)} 个题目文件")
    
    # 统计数据
    total_questions = 0
    cleaned_questions = 0
    errors_count = 0
    translations = {}
    
    # 处理每个题目文件
    for question_file in question_files:
        try:
            print(f"\n📝 处理: {question_file.name}")
            
            # 清洗题目数据
            cleaned_data, translation_data = clean_question_file(question_file)
            
            # 验证数据
            is_valid, errors = validate_question_data(cleaned_data)
            
            if not is_valid:
                print(f"  ⚠️  数据验证失败:")
                for error in errors:
                    print(f"    - {error}")
                errors_count += 1
                continue
            
            # 保存清洗后的数据（覆盖原文件）
            with open(question_file, "w", encoding="utf-8") as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
            
            # 收集翻译数据
            question_id = cleaned_data.get("id", "")
            if translation_data and (translation_data.get("question") or translation_data.get("options")):
                translations[question_id] = translation_data
            
            cleaned_questions += 1
            total_questions += 1
            print(f"  ✓ 清洗完成")
            
        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
            errors_count += 1
            import traceback
            traceback.print_exc()
    
    # 生成翻译数据文件
    if translations:
        translation_file = TRANSLATIONS_DIR / "zh.json"
        translation_output = {
            "questions": translations
        }
        with open(translation_file, "w", encoding="utf-8") as f:
            json.dump(translation_output, f, indent=2, ensure_ascii=False)
        print(f"\n✓ 翻译数据已保存: {translation_file}")
        print(f"  包含 {len(translations)} 个题目的翻译")
    else:
        print("\n⚠️  未找到翻译数据（可能题目中没有中文）")
    
    # 输出统计信息
    print("\n" + "=" * 60)
    print("📊 清洗统计:")
    print(f"  总题目数: {total_questions}")
    print(f"  成功清洗: {cleaned_questions}")
    print(f"  错误数量: {errors_count}")
    print(f"  翻译数据: {len(translations)} 个题目")
    print("=" * 60)

if __name__ == "__main__":
    main()
