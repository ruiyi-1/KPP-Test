#!/usr/bin/env python3
"""
KPP题目数据汇总脚本
功能：将所有Part的题目汇总为统一题库，去除Part分类
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
import hashlib

# 配置
DATA_DIR = Path(__file__).parent.parent / "data"
QUESTIONS_DIR = DATA_DIR / "questions"
TRANSLATIONS_DIR = DATA_DIR / "translations"
OUTPUT_FILE = DATA_DIR / "questions.json"
OUTPUT_TRANSLATIONS_FILE = TRANSLATIONS_DIR / "zh.json"

def calculate_question_hash(question_data: Dict) -> str:
    """计算题目的哈希值，用于去重"""
    # 使用题目文本和选项文本计算哈希
    key_parts = [
        question_data.get("question_text", ""),
    ]
    for option in question_data.get("options", []):
        key_parts.append(option.get("text", ""))
    
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode("utf-8")).hexdigest()

def convert_to_final_format(question_data: Dict, new_id: str) -> Dict:
    """转换为最终数据库结构格式"""
    # 确定题目类型
    has_image_options = question_data.get("has_image_options", False)
    question_type = "image-options" if has_image_options else "text"
    
    # 转换选项格式
    options = []
    for option in question_data.get("options", []):
        option_type = "image" if option.get("has_image", False) else "text"
        option_dict = {
            "type": option_type,
            "label": option.get("label", ""),
            "content": option.get("text", ""),
        }
        if option.get("image"):
            option_dict["imagePath"] = option["image"]
        options.append(option_dict)
    
    # 构建最终格式
    final_data = {
        "id": new_id,
        "question": question_data.get("question_text", ""),
        "questionType": question_type,
        "options": options,
        "correctAnswer": question_data.get("correct_answer"),
        "questionImages": question_data.get("question_images", [])
    }
    
    return final_data

def merge_questions() -> Tuple[List[Dict], Dict]:
    """汇总所有Part的题目"""
    question_files = sorted(QUESTIONS_DIR.glob("part-*-question-*.json"))
    
    if not question_files:
        print("⚠️  未找到题目文件")
        return [], {}
    
    print(f"📂 找到 {len(question_files)} 个题目文件")
    
    all_questions = []
    seen_hashes: Set[str] = set()
    question_id_map = {}  # 旧ID -> 新ID映射
    
    question_counter = 1
    
    # 按Part和题目编号排序
    def get_sort_key(file_path: Path) -> tuple:
        name = file_path.stem
        # 提取 part 和 question_number
        parts = name.split("-")
        if len(parts) >= 3:
            part = parts[1].upper()
            question_num = int(parts[3]) if parts[3].isdigit() else 0
            return (part, question_num)
        return ("", 0)
    
    sorted_files = sorted(question_files, key=get_sort_key)
    
    for question_file in sorted_files:
        try:
            with open(question_file, "r", encoding="utf-8") as f:
                question_data = json.load(f)
            
            # 计算哈希值检查重复
            question_hash = calculate_question_hash(question_data)
            if question_hash in seen_hashes:
                print(f"  ⚠️  跳过重复题目: {question_file.name}")
                continue
            
            seen_hashes.add(question_hash)
            
            # 生成新ID（去除Part前缀）
            new_id = f"question-{question_counter:03d}"
            old_id = question_data.get("id", "")
            question_id_map[old_id] = new_id
            
            # 转换为最终格式
            final_question = convert_to_final_format(question_data, new_id)
            all_questions.append(final_question)
            
            question_counter += 1
            
        except Exception as e:
            print(f"  ❌ 处理失败 {question_file.name}: {e}")
            import traceback
            traceback.print_exc()
    
    return all_questions, question_id_map

def update_translations(question_id_map: Dict[str, str]) -> Dict:
    """更新翻译文件中的题目ID引用"""
    translation_file = TRANSLATIONS_DIR / "zh.json"
    
    if not translation_file.exists():
        print("⚠️  翻译文件不存在，跳过更新")
        return {}
    
    try:
        with open(translation_file, "r", encoding="utf-8") as f:
            translations = json.load(f)
        
        updated_translations = {}
        questions = translations.get("questions", {})
        
        for old_id, new_id in question_id_map.items():
            if old_id in questions:
                updated_translations[new_id] = questions[old_id]
        
        return {"questions": updated_translations}
        
    except Exception as e:
        print(f"⚠️  更新翻译文件失败: {e}")
        return {}

def validate_merged_data(questions: List[Dict]) -> Tuple[bool, List[str]]:
    """验证汇总后的数据"""
    errors = []
    
    if not questions:
        errors.append("没有题目数据")
        return False, errors
    
    # 检查ID唯一性
    ids = [q.get("id") for q in questions]
    if len(ids) != len(set(ids)):
        errors.append("存在重复的题目ID")
    
    # 检查每个题目的完整性
    for idx, question in enumerate(questions):
        if not question.get("id"):
            errors.append(f"题目 {idx} 缺少ID")
        if not question.get("question"):
            errors.append(f"题目 {idx} 缺少题目文本")
        if not question.get("options") or len(question["options"]) < 2:
            errors.append(f"题目 {idx} 选项数量不足")
    
    return len(errors) == 0, errors

def main():
    """主函数"""
    print("=" * 60)
    print("🔄 KPP题目数据汇总工具")
    print("=" * 60)
    
    # 确保目录存在
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    TRANSLATIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 汇总题目
    print("\n📦 开始汇总题目...")
    all_questions, question_id_map = merge_questions()
    
    if not all_questions:
        print("⚠️  没有题目可汇总")
        return
    
    print(f"✓ 汇总完成，共 {len(all_questions)} 道题目")
    
    # 验证数据
    print("\n🔍 验证数据...")
    is_valid, errors = validate_merged_data(all_questions)
    
    if not is_valid:
        print("⚠️  数据验证失败:")
        for error in errors:
            print(f"  - {error}")
        return
    
    print("✓ 数据验证通过")
    
    # 保存汇总后的题目数据
    print(f"\n💾 保存汇总数据到: {OUTPUT_FILE}")
    output_data = {
        "total": len(all_questions),
        "questions": all_questions
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print("✓ 题目数据已保存")
    
    # 更新翻译文件
    print(f"\n🌐 更新翻译数据...")
    updated_translations = update_translations(question_id_map)
    if updated_translations:
        with open(OUTPUT_TRANSLATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(updated_translations, f, indent=2, ensure_ascii=False)
        print(f"✓ 翻译数据已更新: {OUTPUT_TRANSLATIONS_FILE}")
        print(f"  包含 {len(updated_translations.get('questions', {}))} 个题目的翻译")
    else:
        print("⚠️  没有翻译数据需要更新")
    
    # 输出统计信息
    print("\n" + "=" * 60)
    print("📊 汇总统计:")
    print(f"  总题目数: {len(all_questions)}")
    print(f"  输出文件: {OUTPUT_FILE}")
    print(f"  翻译文件: {OUTPUT_TRANSLATIONS_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    main()
