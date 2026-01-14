#!/usr/bin/env python3
"""
验证题目数据的完整性和正确性
检查图片、题目文本、选项是否匹配
"""
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict

# 配置
DATA_DIR = Path(__file__).parent.parent / "data"
QUESTIONS_DIR = DATA_DIR / "questions"
FINAL_QUESTIONS_FILE = Path(__file__).parent.parent / "web" / "src" / "data" / "questions.json"
PUBLIC_DIR = Path(__file__).parent.parent / "web" / "public"

def verify_final_questions() -> Tuple[bool, List[Dict]]:
    """验证最终题目数据"""
    if not FINAL_QUESTIONS_FILE.exists():
        print(f"❌ 最终题目文件不存在: {FINAL_QUESTIONS_FILE}")
        return False, []
    
    with open(FINAL_QUESTIONS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    questions = data.get("questions", [])
    print(f"📊 总题目数: {len(questions)}")
    
    issues = []
    image_usage = defaultdict(list)  # 图片路径 -> 使用该图片的题目ID列表
    
    # 检查每个题目
    for idx, question in enumerate(questions):
        question_id = question.get("id", f"question-{idx}")
        question_issues = []
        
        # 检查基本字段
        if not question.get("question"):
            question_issues.append("缺少题目文本")
        if not question.get("options") or len(question["options"]) < 2:
            question_issues.append(f"选项数量不足: {len(question.get('options', []))}")
        if not question.get("correctAnswer"):
            question_issues.append("缺少正确答案")
        
        # 检查题目图片
        question_images = question.get("questionImages", [])
        if not isinstance(question_images, list):
            question_images = []
        
        for img_path in question_images:
            if not img_path:
                continue
            
            # 记录图片使用情况
            image_usage[img_path].append(question_id)
            
            # 检查图片文件是否存在
            clean_path = img_path.lstrip("/")
            if not clean_path.startswith("images/"):
                clean_path = f"images/{clean_path}"
            full_path = PUBLIC_DIR / clean_path
            
            if not full_path.exists():
                question_issues.append(f"题目图片文件不存在: {img_path}")
        
        # 检查选项
        options = question.get("options", [])
        option_labels = set()
        
        for opt_idx, option in enumerate(options):
            label = option.get("label", "").strip().upper()
            
            if not label:
                question_issues.append(f"选项 {opt_idx} 缺少标签")
            elif label in option_labels:
                question_issues.append(f"选项标签重复: {label}")
            else:
                option_labels.add(label)
            
            # 检查选项内容
            if option.get("type") == "text" and not option.get("content"):
                question_issues.append(f"选项 {label} 缺少文本内容")
            
            # 检查选项图片
            if option.get("type") == "image":
                img_path = option.get("imagePath")
                if not img_path:
                    question_issues.append(f"选项 {label} 类型为图片但缺少图片路径")
                else:
                    clean_path = img_path.lstrip("/")
                    if not clean_path.startswith("images/"):
                        clean_path = f"images/{clean_path}"
                    full_path = PUBLIC_DIR / clean_path
                    
                    if not full_path.exists():
                        question_issues.append(f"选项 {label} 图片文件不存在: {img_path}")
        
        # 检查正确答案是否在选项中
        correct_answer = question.get("correctAnswer", "").strip().upper()
        if correct_answer and correct_answer not in option_labels:
            question_issues.append(f"正确答案 '{correct_answer}' 不在选项中")
        
        if question_issues:
            issues.append({
                "question_id": question_id,
                "index": idx,
                "issues": question_issues
            })
    
    # 检查图片重复使用（可能的问题）
    duplicate_images = {img: qids for img, qids in image_usage.items() if len(qids) > 1}
    if duplicate_images:
        print(f"\n⚠️  发现 {len(duplicate_images)} 个图片被多个题目使用:")
        for img, qids in list(duplicate_images.items())[:10]:
            print(f"  {img}: 被 {len(qids)} 个题目使用")
            print(f"    示例: {', '.join(qids[:3])}")
            if len(qids) > 3:
                print(f"    ... 还有 {len(qids) - 3} 个")
        if len(duplicate_images) > 10:
            print(f"  ... 还有 {len(duplicate_images) - 10} 个重复图片")
    
    return len(issues) == 0, issues

def verify_original_questions() -> Dict[str, Dict]:
    """加载并验证原始题目数据"""
    original_questions = {}
    
    if not QUESTIONS_DIR.exists():
        print(f"⚠️  原始题目目录不存在: {QUESTIONS_DIR}")
        return original_questions
    
    question_files = sorted(QUESTIONS_DIR.glob("part-*-question-*.json"))
    print(f"📂 找到 {len(question_files)} 个原始题目文件")
    
    for question_file in question_files:
        try:
            with open(question_file, "r", encoding="utf-8") as f:
                question_data = json.load(f)
            
            question_id = question_data.get("id", "")
            if question_id:
                original_questions[question_id] = question_data
        except Exception as e:
            print(f"  ⚠️  读取失败 {question_file.name}: {e}")
    
    return original_questions

def normalize_text(text: str) -> str:
    """标准化文本用于比较"""
    if not text:
        return ""
    # 移除多余空格、标点符号，统一大小写
    text = text.strip().lower()
    # 移除常见的标点符号差异
    text = text.replace("?", "").replace("!", "").replace(".", "").replace(",", "")
    # 统一空格
    text = " ".join(text.split())
    return text

def calculate_question_hash(question_data: Dict, use_original_format: bool = False) -> str:
    """计算题目的哈希值，用于匹配"""
    if use_original_format:
        # 原始格式
        question_text = normalize_text(question_data.get("question_text", ""))
        option_texts = []
        for option in sorted(question_data.get("options", []), key=lambda x: x.get("label", "")):
            option_texts.append(normalize_text(option.get("text", "")))
    else:
        # 最终格式
        question_text = normalize_text(question_data.get("question", ""))
        option_texts = []
        for option in sorted(question_data.get("options", []), key=lambda x: x.get("label", "")):
            option_texts.append(normalize_text(option.get("content", "")))
    
    # 组合题目文本和所有选项文本
    key_parts = [question_text] + option_texts
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode("utf-8")).hexdigest()

def calculate_question_hash_flexible(question_data: Dict, use_original_format: bool = False) -> Tuple[str, str]:
    """计算题目的多个哈希值，用于灵活匹配
    返回: (完整hash, 仅题目文本hash)
    """
    if use_original_format:
        question_text = normalize_text(question_data.get("question_text", ""))
    else:
        question_text = normalize_text(question_data.get("question", ""))
    
    # 仅题目文本的hash
    question_only_hash = hashlib.md5(question_text.encode("utf-8")).hexdigest()
    
    # 完整hash（题目+选项）
    full_hash = calculate_question_hash(question_data, use_original_format)
    
    return full_hash, question_only_hash

def match_and_compare(original_questions: Dict[str, Dict], final_questions: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """匹配原始题目和最终题目，并比较差异
    返回: (匹配结果列表, 问题列表)
    """
    if not original_questions:
        return [], []
    
    # 为原始题目建立多个哈希索引
    original_by_full_hash = {}  # 完整hash -> 题目列表
    original_by_question_hash = {}  # 仅题目文本hash -> 题目列表
    
    for orig_id, orig_data in original_questions.items():
        full_hash, question_hash = calculate_question_hash_flexible(orig_data, use_original_format=True)
        
        if full_hash not in original_by_full_hash:
            original_by_full_hash[full_hash] = []
        original_by_full_hash[full_hash].append((orig_id, orig_data))
        
        if question_hash not in original_by_question_hash:
            original_by_question_hash[question_hash] = []
        original_by_question_hash[question_hash].append((orig_id, orig_data))
    
    matches = []
    comparison_issues = []
    matched_original_ids = set()
    matched_final_ids = set()
    
    # 匹配最终题目
    for final_question in final_questions:
        final_id = final_question.get("id", "")
        full_hash, question_hash = calculate_question_hash_flexible(final_question, use_original_format=False)
        
        matched = False
        
        # 首先尝试完整匹配
        if full_hash in original_by_full_hash:
            for orig_id, orig_data in original_by_full_hash[full_hash]:
                matches.append({
                    "original_id": orig_id,
                    "final_id": final_id,
                    "match_type": "完整匹配",
                    "original": orig_data,
                    "final": final_question
                })
                matched_original_ids.add(orig_id)
                matched_final_ids.add(final_id)
                matched = True
                
                # 比较图片
                issues = compare_question_pair(orig_data, final_question, orig_id, final_id)
                if issues:
                    comparison_issues.extend(issues)
        
        # 如果完整匹配失败，尝试仅题目文本匹配（可能选项有变化）
        if not matched and question_hash in original_by_question_hash:
            for orig_id, orig_data in original_by_question_hash[question_hash]:
                # 检查是否已经匹配过
                if orig_id in matched_original_ids:
                    continue
                
                matches.append({
                    "original_id": orig_id,
                    "final_id": final_id,
                    "match_type": "题目文本匹配（选项可能不同）",
                    "original": orig_data,
                    "final": final_question
                })
                matched_original_ids.add(orig_id)
                matched_final_ids.add(final_id)
                
                # 比较图片和选项
                issues = compare_question_pair(orig_data, final_question, orig_id, final_id)
                if issues:
                    comparison_issues.extend(issues)
    
    return matches, comparison_issues

def compare_question_pair(orig_data: Dict, final_data: Dict, orig_id: str, final_id: str) -> List[Dict]:
    """比较一对匹配的题目"""
    issues = []
    
    # 比较题目图片
    orig_images = orig_data.get("question_images", [])
    final_images = final_data.get("questionImages", [])
    
    def normalize_img_path(path):
        if not path:
            return ""
        path = str(path).lstrip("/")
        if path.startswith("images/"):
            path = path[7:]
        return path.lower()
    
    orig_normalized = sorted([normalize_img_path(img) for img in orig_images if img])
    final_normalized = sorted([normalize_img_path(img) for img in final_images if img])
    
    if orig_normalized != final_normalized:
        issues.append({
            "original_id": orig_id,
            "final_id": final_id,
            "type": "题目图片不一致",
            "original_images": orig_images,
            "final_images": final_images,
            "original_normalized": orig_normalized,
            "final_normalized": final_normalized
        })
    
    # 比较选项图片
    orig_options = orig_data.get("options", [])
    final_options = final_data.get("options", [])
    
    orig_by_label = {opt.get("label", ""): opt for opt in orig_options}
    final_by_label = {opt.get("label", ""): opt for opt in final_options}
    
    all_labels = set(orig_by_label.keys()) | set(final_by_label.keys())
    
    for label in sorted(all_labels):
        orig_opt = orig_by_label.get(label)
        final_opt = final_by_label.get(label)
        
        if not orig_opt or not final_opt:
            continue
        
        orig_img = normalize_img_path(orig_opt.get("image")) if orig_opt.get("image") else ""
        final_img = normalize_img_path(final_opt.get("imagePath")) if final_opt.get("imagePath") else ""
        
        if orig_img != final_img:
            issues.append({
                "original_id": orig_id,
                "final_id": final_id,
                "type": f"选项 {label} 图片不一致",
                "original_image": orig_opt.get("image"),
                "final_image": final_opt.get("imagePath")
            })
    
    return issues

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 验证题目数据完整性和正确性")
    print("=" * 60)
    
    # 验证最终题目数据
    print("\n📋 验证最终题目数据...")
    is_valid, issues = verify_final_questions()
    
    if is_valid:
        print("✅ 所有题目数据验证通过")
    else:
        print(f"❌ 发现 {len(issues)} 个题目存在问题")
        print("\n问题详情（前10个）:")
        for issue_data in issues[:10]:
            print(f"\n题目 ID: {issue_data['question_id']} (索引: {issue_data['index']})")
            for issue in issue_data['issues']:
                print(f"  - {issue}")
        if len(issues) > 10:
            print(f"\n... 还有 {len(issues) - 10} 个题目存在问题")
    
    # 加载原始题目数据
    print("\n📂 加载原始题目数据...")
    original_questions = verify_original_questions()
    
    if original_questions:
        print(f"✓ 找到 {len(original_questions)} 道原始题目")
        
        # 加载最终题目数据
        with open(FINAL_QUESTIONS_FILE, "r", encoding="utf-8") as f:
            final_data = json.load(f)
        final_questions = final_data.get("questions", [])
        
        # 匹配并比较
        print("\n🔗 通过题目hash匹配并比较原始题目和最终题目...")
        matches, comparison_issues = match_and_compare(original_questions, final_questions)
        
        print(f"✓ 匹配到 {len(matches)} 对题目")
        
        if matches:
            print("\n匹配详情:")
            for match in matches[:10]:
                print(f"  {match['original_id']} <-> {match['final_id']} ({match['match_type']})")
            if len(matches) > 10:
                print(f"  ... 还有 {len(matches) - 10} 对匹配")
        
        if comparison_issues:
            print(f"\n⚠️  发现 {len(comparison_issues)} 个匹配题目的图片不一致:")
            for comp_issue in comparison_issues[:10]:
                print(f"\n原始ID: {comp_issue['original_id']} -> 最终ID: {comp_issue['final_id']}")
                print(f"  问题类型: {comp_issue['type']}")
                if 'original_images' in comp_issue:
                    print(f"  原始图片: {comp_issue['original_images']}")
                    print(f"  最终图片: {comp_issue['final_images']}")
                elif 'original_image' in comp_issue:
                    print(f"  原始图片: {comp_issue['original_image']}")
                    print(f"  最终图片: {comp_issue['final_image']}")
            if len(comparison_issues) > 10:
                print(f"\n  ... 还有 {len(comparison_issues) - 10} 个问题")
        else:
            if matches:
                print("✅ 所有匹配题目的图片一致")
            else:
                print("⚠️  没有匹配到任何题目")
    else:
        print("⚠️  没有原始题目数据，跳过比较")
    
    # 统计信息
    print("\n" + "=" * 60)
    print("📊 验证统计")
    print("=" * 60)
    
    if FINAL_QUESTIONS_FILE.exists():
        with open(FINAL_QUESTIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        questions = data.get("questions", [])
        
        # 统计图片
        total_question_images = 0
        total_option_images = 0
        missing_question_images = 0
        missing_option_images = 0
        
        for q in questions:
            for img in q.get("questionImages", []):
                total_question_images += 1
                clean_path = img.lstrip("/")
                if not clean_path.startswith("images/"):
                    clean_path = f"images/{clean_path}"
                if not (PUBLIC_DIR / clean_path).exists():
                    missing_question_images += 1
            
            for opt in q.get("options", []):
                if opt.get("imagePath"):
                    total_option_images += 1
                    clean_path = opt["imagePath"].lstrip("/")
                    if not clean_path.startswith("images/"):
                        clean_path = f"images/{clean_path}"
                    if not (PUBLIC_DIR / clean_path).exists():
                        missing_option_images += 1
        
        print(f"总题目数: {len(questions)}")
        print(f"题目图片: {total_question_images} 个引用, {missing_question_images} 个缺失")
        print(f"选项图片: {total_option_images} 个引用, {missing_option_images} 个缺失")
    
    print("=" * 60)
    
    return is_valid and len(issues) == 0

if __name__ == "__main__":
    main()
