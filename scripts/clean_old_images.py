#!/usr/bin/env python3
"""
清理旧的图片文件（可选，重新抓取前使用）
"""
from pathlib import Path

PUBLIC_DIR = Path(__file__).parent.parent / "web" / "public"
QUESTIONS_IMAGES_DIR = PUBLIC_DIR / "images" / "questions"
OPTIONS_IMAGES_DIR = PUBLIC_DIR / "images" / "options"

def clean_old_images():
    """清理旧图片"""
    print("=" * 60)
    print("🧹 清理旧图片文件")
    print("=" * 60)
    
    questions_count = 0
    options_count = 0
    
    if QUESTIONS_IMAGES_DIR.exists():
        for img_file in QUESTIONS_IMAGES_DIR.glob("*.png"):
            img_file.unlink()
            questions_count += 1
        print(f"✓ 清理了 {questions_count} 个题目图片")
    else:
        print("⚠️  题目图片目录不存在")
    
    if OPTIONS_IMAGES_DIR.exists():
        for img_file in OPTIONS_IMAGES_DIR.glob("*.png"):
            img_file.unlink()
            options_count += 1
        print(f"✓ 清理了 {options_count} 个选项图片")
    else:
        print("⚠️  选项图片目录不存在")
    
    print(f"\n✅ 共清理了 {questions_count + options_count} 个图片文件")
    print("=" * 60)

if __name__ == "__main__":
    clean_old_images()
