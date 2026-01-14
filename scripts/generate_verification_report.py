#!/usr/bin/env python3
"""
生成详细的题目数据验证报告
包括图片重复使用、缺失文件、题目选项一致性等问题
"""
import json
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

# 配置
FINAL_QUESTIONS_FILE = Path(__file__).parent.parent / "web" / "src" / "data" / "questions.json"
PUBLIC_DIR = Path(__file__).parent.parent / "web" / "public"
REPORT_FILE = Path(__file__).parent.parent / "verification_report.txt"

def generate_report():
    """生成验证报告"""
    print("=" * 60)
    print("📋 生成题目数据验证报告")
    print("=" * 60)
    
    if not FINAL_QUESTIONS_FILE.exists():
        print(f"❌ 题目文件不存在: {FINAL_QUESTIONS_FILE}")
        return
    
    with open(FINAL_QUESTIONS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    questions = data.get("questions", [])
    print(f"📊 总题目数: {len(questions)}")
    
    # 统计信息
    image_usage = defaultdict(list)  # 图片路径 -> 使用该图片的题目列表
    missing_images = []  # 缺失的图片
    duplicate_image_issues = []  # 图片重复使用的问题
    
    # 检查每个题目
    for question in questions:
        question_id = question.get("id", "")
        
        # 检查题目图片
        question_images = question.get("questionImages", [])
        for img_path in question_images:
            if not img_path:
                continue
            
            # 记录使用情况
            image_usage[img_path].append({
                "id": question_id,
                "question": question.get("question", "")[:50] + "..." if len(question.get("question", "")) > 50 else question.get("question", "")
            })
            
            # 检查文件是否存在
            clean_path = img_path.lstrip("/")
            if not clean_path.startswith("images/"):
                clean_path = f"images/{clean_path}"
            full_path = PUBLIC_DIR / clean_path
            
            if not full_path.exists():
                missing_images.append({
                    "question_id": question_id,
                    "image_path": img_path,
                    "full_path": str(full_path)
                })
        
        # 检查选项图片
        for option in question.get("options", []):
            img_path = option.get("imagePath")
            if img_path:
                image_usage[img_path].append({
                    "id": question_id,
                    "question": f"选项 {option.get('label', '')}: {option.get('content', '')[:30]}"
                })
                
                clean_path = img_path.lstrip("/")
                if not clean_path.startswith("images/"):
                    clean_path = f"images/{clean_path}"
                full_path = PUBLIC_DIR / clean_path
                
                if not full_path.exists():
                    missing_images.append({
                        "question_id": question_id,
                        "image_path": img_path,
                        "full_path": str(full_path),
                        "option": option.get("label", "")
                    })
    
    # 找出重复使用的图片
    for img_path, usages in image_usage.items():
        if len(usages) > 1:
            # 检查这些使用是否合理（相同题目文本可能合理）
            unique_questions = set()
            for usage in usages:
                unique_questions.add(usage["question"])
            
            # 如果不同题目使用相同图片，可能有问题
            if len(unique_questions) > 1:
                duplicate_image_issues.append({
                    "image_path": img_path,
                    "usage_count": len(usages),
                    "unique_questions": len(unique_questions),
                    "usages": usages[:5]  # 只保存前5个示例
                })
    
    # 生成报告
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("题目数据验证报告")
    report_lines.append("=" * 80)
    report_lines.append(f"\n总题目数: {len(questions)}")
    report_lines.append(f"总图片引用数: {sum(len(usages) for usages in image_usage.values())}")
    report_lines.append(f"唯一图片数: {len(image_usage)}")
    
    # 缺失图片报告
    report_lines.append("\n" + "=" * 80)
    report_lines.append("1. 缺失图片检查")
    report_lines.append("=" * 80)
    if missing_images:
        report_lines.append(f"\n❌ 发现 {len(missing_images)} 个缺失的图片文件:")
        for missing in missing_images[:20]:
            report_lines.append(f"  题目ID: {missing['question_id']}")
            report_lines.append(f"  图片路径: {missing['image_path']}")
            if 'option' in missing:
                report_lines.append(f"  选项: {missing['option']}")
            report_lines.append("")
        if len(missing_images) > 20:
            report_lines.append(f"  ... 还有 {len(missing_images) - 20} 个缺失图片")
    else:
        report_lines.append("\n✅ 所有图片文件都存在")
    
    # 图片重复使用报告
    report_lines.append("\n" + "=" * 80)
    report_lines.append("2. 图片重复使用检查")
    report_lines.append("=" * 80)
    if duplicate_image_issues:
        report_lines.append(f"\n⚠️  发现 {len(duplicate_image_issues)} 个图片被多个不同题目使用:")
        report_lines.append("  (这可能是正常的，如果多个题目确实使用相同的图片)")
        report_lines.append("  (但也可能是抓取时的bug，导致多个题目使用了错误的图片)\n")
        
        for issue in duplicate_image_issues[:20]:
            report_lines.append(f"图片: {issue['image_path']}")
            report_lines.append(f"  被 {issue['usage_count']} 个引用使用，涉及 {issue['unique_questions']} 个不同题目")
            report_lines.append("  使用示例:")
            for usage in issue['usages']:
                report_lines.append(f"    - {usage['id']}: {usage['question']}")
            report_lines.append("")
        
        if len(duplicate_image_issues) > 20:
            report_lines.append(f"  ... 还有 {len(duplicate_image_issues) - 20} 个重复图片问题")
        
        # 特别关注那些被大量题目使用的图片
        high_usage = [issue for issue in duplicate_image_issues if issue['usage_count'] > 10]
        if high_usage:
            report_lines.append(f"\n⚠️  特别关注: {len(high_usage)} 个图片被超过10个题目使用:")
            for issue in high_usage[:10]:
                report_lines.append(f"  - {issue['image_path']}: {issue['usage_count']} 个题目")
    else:
        report_lines.append("\n✅ 没有发现异常的图片重复使用")
    
    # 题目完整性检查
    report_lines.append("\n" + "=" * 80)
    report_lines.append("3. 题目完整性检查")
    report_lines.append("=" * 80)
    
    incomplete_questions = []
    for question in questions:
        issues = []
        question_id = question.get("id", "")
        
        if not question.get("question"):
            issues.append("缺少题目文本")
        if not question.get("options") or len(question["options"]) < 2:
            issues.append(f"选项数量不足: {len(question.get('options', []))}")
        if not question.get("correctAnswer"):
            issues.append("缺少正确答案")
        
        # 检查正确答案是否在选项中
        correct_answer = question.get("correctAnswer", "").strip().upper()
        option_labels = {opt.get("label", "").strip().upper() for opt in question.get("options", [])}
        if correct_answer and correct_answer not in option_labels:
            issues.append(f"正确答案 '{correct_answer}' 不在选项中")
        
        if issues:
            incomplete_questions.append({
                "id": question_id,
                "issues": issues
            })
    
    if incomplete_questions:
        report_lines.append(f"\n❌ 发现 {len(incomplete_questions)} 个题目存在问题:")
        for q in incomplete_questions[:20]:
            report_lines.append(f"  题目ID: {q['id']}")
            for issue in q['issues']:
                report_lines.append(f"    - {issue}")
            report_lines.append("")
        if len(incomplete_questions) > 20:
            report_lines.append(f"  ... 还有 {len(incomplete_questions) - 20} 个题目存在问题")
    else:
        report_lines.append("\n✅ 所有题目数据完整")
    
    # 统计摘要
    report_lines.append("\n" + "=" * 80)
    report_lines.append("统计摘要")
    report_lines.append("=" * 80)
    report_lines.append(f"总题目数: {len(questions)}")
    report_lines.append(f"缺失图片: {len(missing_images)}")
    report_lines.append(f"图片重复使用问题: {len(duplicate_image_issues)}")
    report_lines.append(f"不完整题目: {len(incomplete_questions)}")
    report_lines.append("=" * 80)
    
    # 保存报告
    report_content = "\n".join(report_lines)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print(f"\n✅ 报告已保存到: {REPORT_FILE}")
    print("\n报告摘要:")
    print(f"  总题目数: {len(questions)}")
    print(f"  缺失图片: {len(missing_images)}")
    print(f"  图片重复使用问题: {len(duplicate_image_issues)}")
    print(f"  不完整题目: {len(incomplete_questions)}")
    
    # 输出关键问题
    if duplicate_image_issues:
        print("\n⚠️  关键问题: 发现图片重复使用，可能表示抓取时图片命名有bug")
        high_usage = [issue for issue in duplicate_image_issues if issue['usage_count'] > 10]
        if high_usage:
            print(f"  其中 {len(high_usage)} 个图片被超过10个题目使用，这很可能是不正常的")

if __name__ == "__main__":
    generate_report()
