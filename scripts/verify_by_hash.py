#!/usr/bin/env python3
"""
通过题目hash验证图片一致性
即使没有原始数据，也能检查最终数据中相同hash的题目是否使用相同图片
"""
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict

# 配置
FINAL_QUESTIONS_FILE = Path(__file__).parent.parent / "web" / "src" / "data" / "questions.json"
PUBLIC_DIR = Path(__file__).parent.parent / "web" / "public"
QUESTIONS_DIR = Path(__file__).parent.parent / "data" / "questions"

def normalize_text(text: str) -> str:
    """标准化文本用于比较"""
    if not text:
        return ""
    text = text.strip().lower()
    # 移除常见的标点符号差异
    text = text.replace("?", "").replace("!", "").replace(".", "").replace(",", "")
    # 统一空格
    text = " ".join(text.split())
    return text

def calculate_question_hash(question_data: Dict, use_original_format: bool = False) -> str:
    """计算题目的哈希值"""
    if use_original_format:
        question_text = normalize_text(question_data.get("question_text", ""))
        option_texts = []
        for option in sorted(question_data.get("options", []), key=lambda x: x.get("label", "")):
            option_texts.append(normalize_text(option.get("text", "")))
    else:
        question_text = normalize_text(question_data.get("question", ""))
        option_texts = []
        for option in sorted(question_data.get("options", []), key=lambda x: x.get("label", "")):
            option_texts.append(normalize_text(option.get("content", "")))
    
    key_parts = [question_text] + option_texts
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode("utf-8")).hexdigest()

def normalize_image_path(path: str) -> str:
    """标准化图片路径"""
    if not path:
        return ""
    path = str(path).lstrip("/")
    if path.startswith("images/"):
        path = path[7:]
    return path.lower()

def verify_by_hash():
    """通过hash验证题目数据"""
    print("=" * 60)
    print("🔍 通过题目hash验证图片一致性")
    print("=" * 60)
    
    # 加载最终题目数据
    if not FINAL_QUESTIONS_FILE.exists():
        print(f"❌ 题目文件不存在: {FINAL_QUESTIONS_FILE}")
        return
    
    with open(FINAL_QUESTIONS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    questions = data.get("questions", [])
    print(f"\n📊 总题目数: {len(questions)}")
    
    # 按hash分组题目
    questions_by_hash = defaultdict(list)
    for question in questions:
        hash_key = calculate_question_hash(question, use_original_format=False)
        questions_by_hash[hash_key].append(question)
    
    # 找出重复的题目（相同hash）
    duplicate_questions = {h: qs for h, qs in questions_by_hash.items() if len(qs) > 1}
    print(f"📋 唯一题目hash数: {len(questions_by_hash)}")
    print(f"🔄 重复题目hash数: {len(duplicate_questions)}")
    
    # 检查相同hash的题目是否使用相同图片
    print("\n🔍 检查相同hash题目的图片一致性...")
    image_inconsistencies = []
    
    for hash_key, hash_questions in duplicate_questions.items():
        # 收集所有图片
        all_question_images = []
        all_option_images = defaultdict(list)  # label -> images
        
        for q in hash_questions:
            # 题目图片
            q_images = [normalize_image_path(img) for img in q.get("questionImages", []) if img]
            all_question_images.append((q.get("id", ""), sorted(q_images)))
            
            # 选项图片
            for opt in q.get("options", []):
                label = opt.get("label", "")
                if opt.get("imagePath"):
                    img = normalize_image_path(opt.get("imagePath"))
                    all_option_images[label].append((q.get("id", ""), img))
        
        # 检查题目图片是否一致
        if len(set(tuple(imgs) for _, imgs in all_question_images)) > 1:
            image_inconsistencies.append({
                "hash": hash_key,
                "type": "题目图片不一致",
                "questions": [qid for qid, _ in all_question_images],
                "images": {qid: imgs for qid, imgs in all_question_images}
            })
        
        # 检查选项图片是否一致
        for label, opt_images in all_option_images.items():
            unique_images = set(img for _, img in opt_images)
            if len(unique_images) > 1:
                image_inconsistencies.append({
                    "hash": hash_key,
                    "type": f"选项 {label} 图片不一致",
                    "questions": list(set(qid for qid, _ in opt_images)),
                    "images": {qid: img for qid, img in opt_images if qid in [q.get("id", "") for q in hash_questions]}
                })
    
    # 加载原始题目数据（如果有）
    print("\n📂 加载原始题目数据...")
    original_questions = {}
    if QUESTIONS_DIR.exists():
        question_files = sorted(QUESTIONS_DIR.glob("part-*-question-*.json"))
        print(f"  找到 {len(question_files)} 个原始题目文件")
        
        for question_file in question_files:
            try:
                with open(question_file, "r", encoding="utf-8") as f:
                    question_data = json.load(f)
                question_id = question_data.get("id", "")
                if question_id:
                    original_questions[question_id] = question_data
            except Exception as e:
                print(f"  ⚠️  读取失败 {question_file.name}: {e}")
    
    # 匹配原始题目和最终题目
    matches = []
    comparison_issues = []
    
    if original_questions:
        print(f"\n🔗 匹配原始题目和最终题目...")
        
        # 为原始题目建立hash索引
        original_by_hash = {}
        for orig_id, orig_data in original_questions.items():
            hash_key = calculate_question_hash(orig_data, use_original_format=True)
            if hash_key not in original_by_hash:
                original_by_hash[hash_key] = []
            original_by_hash[hash_key].append((orig_id, orig_data))
        
        # 匹配最终题目
        for final_question in questions:
            final_id = final_question.get("id", "")
            hash_key = calculate_question_hash(final_question, use_original_format=False)
            
            if hash_key in original_by_hash:
                for orig_id, orig_data in original_by_hash[hash_key]:
                    matches.append({
                        "original_id": orig_id,
                        "final_id": final_id,
                        "original": orig_data,
                        "final": final_question
                    })
                    
                    # 比较图片
                    orig_q_images = sorted([normalize_image_path(img) for img in orig_data.get("question_images", []) if img])
                    final_q_images = sorted([normalize_image_path(img) for img in final_question.get("questionImages", []) if img])
                    
                    if orig_q_images != final_q_images:
                        comparison_issues.append({
                            "original_id": orig_id,
                            "final_id": final_id,
                            "type": "题目图片不一致",
                            "original_images": orig_data.get("question_images", []),
                            "final_images": final_question.get("questionImages", [])
                        })
                    
                    # 比较选项图片
                    orig_options = {opt.get("label", ""): opt for opt in orig_data.get("options", [])}
                    final_options = {opt.get("label", ""): opt for opt in final_question.get("options", [])}
                    
                    for label in set(orig_options.keys()) | set(final_options.keys()):
                        orig_opt = orig_options.get(label)
                        final_opt = final_options.get(label)
                        
                        if orig_opt and final_opt:
                            orig_img = normalize_image_path(orig_opt.get("image", "")) if orig_opt.get("image") else ""
                            final_img = normalize_image_path(final_opt.get("imagePath", "")) if final_opt.get("imagePath") else ""
                            
                            if orig_img != final_img:
                                comparison_issues.append({
                                    "original_id": orig_id,
                                    "final_id": final_id,
                                    "type": f"选项 {label} 图片不一致",
                                    "original_image": orig_opt.get("image"),
                                    "final_image": final_opt.get("imagePath")
                                })
        
        print(f"  ✓ 匹配到 {len(matches)} 对题目")
    
    # 输出结果
    print("\n" + "=" * 60)
    print("📊 验证结果")
    print("=" * 60)
    
    if image_inconsistencies:
        print(f"\n❌ 发现 {len(image_inconsistencies)} 个相同hash题目的图片不一致问题:")
        for issue in image_inconsistencies[:10]:
            print(f"\n  Hash: {issue['hash'][:16]}...")
            print(f"  问题类型: {issue['type']}")
            print(f"  涉及题目: {', '.join(issue['questions'][:5])}")
            if len(issue['questions']) > 5:
                print(f"    ... 还有 {len(issue['questions']) - 5} 个题目")
            if 'images' in issue:
                print("  图片差异:")
                for qid, imgs in list(issue['images'].items())[:3]:
                    print(f"    {qid}: {imgs}")
        if len(image_inconsistencies) > 10:
            print(f"\n  ... 还有 {len(image_inconsistencies) - 10} 个问题")
    else:
        print("\n✅ 相同hash的题目图片都一致")
    
    if comparison_issues:
        print(f"\n⚠️  原始题目和最终题目比较，发现 {len(comparison_issues)} 个图片不一致:")
        for issue in comparison_issues[:10]:
            print(f"\n  {issue['original_id']} <-> {issue['final_id']}")
            print(f"  问题: {issue['type']}")
            if 'original_images' in issue:
                print(f"  原始图片: {issue['original_images']}")
                print(f"  最终图片: {issue['final_images']}")
            elif 'original_image' in issue:
                print(f"  原始图片: {issue['original_image']}")
                print(f"  最终图片: {issue['final_image']}")
        if len(comparison_issues) > 10:
            print(f"\n  ... 还有 {len(comparison_issues) - 10} 个问题")
    elif matches:
        print("\n✅ 所有匹配题目的图片都一致")
    
    # 统计图片重复使用
    print("\n" + "=" * 60)
    print("📸 图片使用统计")
    print("=" * 60)
    
    image_usage = defaultdict(list)
    for question in questions:
        qid = question.get("id", "")
        for img in question.get("questionImages", []):
            if img:
                image_usage[img].append(qid)
        for opt in question.get("options", []):
            if opt.get("imagePath"):
                image_usage[opt["imagePath"]].append(qid)
    
    duplicate_images = {img: qids for img, qids in image_usage.items() if len(qids) > 1}
    high_usage_images = {img: qids for img, qids in duplicate_images.items() if len(qids) > 10}
    
    print(f"总图片引用数: {sum(len(qids) for qids in image_usage.values())}")
    print(f"唯一图片数: {len(image_usage)}")
    print(f"被多个题目使用的图片: {len(duplicate_images)}")
    print(f"被超过10个题目使用的图片: {len(high_usage_images)}")
    
    if high_usage_images:
        print("\n⚠️  被大量使用的图片（可能有问题）:")
        for img, qids in list(high_usage_images.items())[:5]:
            print(f"  {img}: {len(qids)} 个题目")
            # 检查这些题目是否真的应该使用相同图片
            question_texts = set()
            for q in questions:
                if q.get("id", "") in qids:
                    question_texts.add(normalize_text(q.get("question", ""))[:50])
            print(f"    涉及 {len(question_texts)} 个不同题目文本")
            if len(question_texts) > 1:
                print(f"    ⚠️  这些题目文本不同，但使用了相同图片，可能有问题！")
    
    print("=" * 60)

if __name__ == "__main__":
    verify_by_hash()
