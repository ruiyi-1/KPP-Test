#!/usr/bin/env python3
"""
分析题目页面结构并在截图上标注
"""
from PIL import Image, ImageDraw, ImageFont
import xml.etree.ElementTree as ET
from pathlib import Path
import sys

def parse_bounds(bounds_str):
    """解析bounds字符串为坐标元组"""
    if not bounds_str:
        return None
    try:
        # 格式: "[x1,y1][x2,y2]"
        parts = bounds_str.split("][")
        if len(parts) != 2:
            return None
        coord1 = parts[0].replace("[", "").split(",")
        coord2 = parts[1].replace("]", "").split(",")
        x1, y1 = int(coord1[0]), int(coord1[1])
        x2, y2 = int(coord2[0]), int(coord2[1])
        return (x1, y1, x2, y2)
    except:
        return None

def analyze_ui_dump(ui_dump_path):
    """分析UI dump，提取关键元素"""
    with open(ui_dump_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    root = ET.fromstring(content)
    
    elements = {
        "back_button": None,
        "question_number": None,
        "question_text": None,
        "question_image": None,
        "options": [],
        "previous_button": None,
        "next_button": None,
        "other_buttons": []
    }
    
    for elem in root.iter():
        class_name = elem.get("class", "")
        content_desc = elem.get("content-desc", "").strip()
        text = elem.get("text", "").strip()
        bounds = parse_bounds(elem.get("bounds", ""))
        
        if not bounds:
            continue
        
        x1, y1, x2, y2 = bounds
        center = ((x1 + x2) // 2, (y1 + y2) // 2)
        width = x2 - x1
        height = y2 - y1
        
        elem_info = {
            "element": elem,
            "bounds": bounds,
            "center": center,
            "size": (width, height),
            "class": class_name,
            "content_desc": content_desc,
            "text": text
        }
        
        # 识别Back按钮
        if content_desc.lower() == "back" or (class_name.endswith("Button") and y1 < 400):
            if "back" in content_desc.lower():
                elements["back_button"] = elem_info
        
        # 识别题目编号（如 "19/150"）
        if "/" in content_desc and y1 < 300:
            elements["question_number"] = elem_info
        
        # 识别题目文本（通常在ScrollView中，Y坐标在300-1500之间，宽度较大）
        if y1 > 300 and y1 < 1500 and width > 800 and (content_desc or text):
            if len(content_desc) > 50 or len(text) > 50:
                if not elements["question_text"] or y1 < elements["question_text"]["bounds"][1]:
                    elements["question_text"] = elem_info
        
        # 识别ImageView（题目中的图片）
        if class_name.endswith("ImageView") and width > 100 and height > 100:
            if 1000 < y1 < 2000:  # 题目图片通常在题目文本下方，选项上方
                elements["question_image"] = elem_info
        
        # 识别选项按钮（A, B, C, D）
        if class_name.endswith("Button") and content_desc in ["A", "B", "C", "D"]:
            if 1800 < y1 < 2500:  # 选项通常在屏幕中下部
                elements["options"].append(elem_info)
        
        # 识别Previous按钮
        if "previous" in content_desc.lower() or "上一" in content_desc:
            if y1 > 2400:
                elements["previous_button"] = elem_info
        
        # 识别Next按钮
        if "next" in content_desc.lower() or "下一" in content_desc:
            if y1 > 2400:
                elements["next_button"] = elem_info
    
    # 按Y坐标排序选项
    elements["options"].sort(key=lambda x: x["bounds"][1])
    
    return elements

def annotate_screenshot(screenshot_path, ui_dump_path, output_path):
    """在截图上标注UI元素"""
    # 分析UI dump
    elements = analyze_ui_dump(ui_dump_path)
    
    # 打开截图
    img = Image.open(screenshot_path)
    draw = ImageDraw.Draw(img)
    
    # 尝试加载字体（如果失败则使用默认字体）
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    colors = {
        "back_button": "orange",
        "question_number": "cyan",
        "question_text": "blue",
        "question_image": "green",
        "option": "red",
        "previous_button": "purple",
        "next_button": "magenta"
    }
    
    # 标注Back按钮
    if elements["back_button"]:
        info = elements["back_button"]
        x1, y1, x2, y2 = info["bounds"]
        draw.rectangle([x1, y1, x2, y2], outline=colors["back_button"], width=3)
        draw.text((x1, y1 - 25), "Back按钮", fill=colors["back_button"], font=font_medium,
                 stroke_width=2, stroke_fill="white")
    
    # 标注题目编号
    if elements["question_number"]:
        info = elements["question_number"]
        x1, y1, x2, y2 = info["bounds"]
        draw.rectangle([x1, y1, x2, y2], outline=colors["question_number"], width=3)
        draw.text((x1, y1 - 25), f"题目编号: {info['content_desc']}", 
                 fill=colors["question_number"], font=font_medium,
                 stroke_width=2, stroke_fill="white")
    
    # 标注题目文本
    if elements["question_text"]:
        info = elements["question_text"]
        x1, y1, x2, y2 = info["bounds"]
        draw.rectangle([x1, y1, x2, y2], outline=colors["question_text"], width=3)
        text_preview = (info["content_desc"] or info["text"])[:30] + "..."
        draw.text((x1, y1 - 25), f"题目文本: {text_preview}", 
                 fill=colors["question_text"], font=font_medium,
                 stroke_width=2, stroke_fill="white")
    
    # 标注题目图片
    if elements["question_image"]:
        info = elements["question_image"]
        x1, y1, x2, y2 = info["bounds"]
        draw.rectangle([x1, y1, x2, y2], outline=colors["question_image"], width=4)
        draw.text((x1, y1 - 25), "题目图片 (ImageView)", 
                 fill=colors["question_image"], font=font_medium,
                 stroke_width=2, stroke_fill="white")
        # 在中心画一个X标记
        cx, cy = info["center"]
        draw.line([cx-20, cy-20, cx+20, cy+20], fill=colors["question_image"], width=3)
        draw.line([cx-20, cy+20, cx+20, cy-20], fill=colors["question_image"], width=3)
    
    # 标注选项
    for idx, option in enumerate(elements["options"]):
        x1, y1, x2, y2 = option["bounds"]
        label = option["content_desc"]
        draw.rectangle([x1, y1, x2, y2], outline=colors["option"], width=3)
        draw.text((x1, y1 - 25), f"选项 {label}", 
                 fill=colors["option"], font=font_medium,
                 stroke_width=2, stroke_fill="white")
        # 标注选项中心点
        cx, cy = option["center"]
        draw.ellipse([cx-8, cy-8, cx+8, cy+8], fill=colors["option"], outline="white", width=2)
    
    # 标注Previous按钮
    if elements["previous_button"]:
        info = elements["previous_button"]
        x1, y1, x2, y2 = info["bounds"]
        draw.rectangle([x1, y1, x2, y2], outline=colors["previous_button"], width=3)
        draw.text((x1, y1 - 25), "Previous按钮", 
                 fill=colors["previous_button"], font=font_medium,
                 stroke_width=2, stroke_fill="white")
    
    # 标注Next按钮
    if elements["next_button"]:
        info = elements["next_button"]
        x1, y1, x2, y2 = info["bounds"]
        draw.rectangle([x1, y1, x2, y2], outline=colors["next_button"], width=3)
        draw.text((x1, y1 - 25), "Next按钮", 
                 fill=colors["next_button"], font=font_medium,
                 stroke_width=2, stroke_fill="white")
    
    # 保存标注后的图片
    img.save(output_path)
    
    # 打印分析结果
    print("=" * 60)
    print("📊 题目页面结构分析")
    print("=" * 60)
    print(f"\n📍 元素位置信息:")
    
    if elements["back_button"]:
        info = elements["back_button"]
        print(f"  Back按钮: {info['bounds']} 中心={info['center']}")
    
    if elements["question_number"]:
        info = elements["question_number"]
        print(f"  题目编号: {info['bounds']} 内容='{info['content_desc']}'")
    
    if elements["question_text"]:
        info = elements["question_text"]
        print(f"  题目文本: {info['bounds']} 尺寸={info['size']}")
        print(f"    内容预览: {(info['content_desc'] or info['text'])[:100]}...")
    
    if elements["question_image"]:
        info = elements["question_image"]
        print(f"  题目图片: {info['bounds']} 尺寸={info['size']} 中心={info['center']}")
    
    print(f"\n  选项 ({len(elements['options'])} 个):")
    for option in elements["options"]:
        print(f"    选项 {option['content_desc']}: {option['bounds']} 中心={option['center']}")
    
    if elements["previous_button"]:
        info = elements["previous_button"]
        print(f"  Previous按钮: {info['bounds']} 中心={info['center']}")
    
    if elements["next_button"]:
        info = elements["next_button"]
        print(f"  Next按钮: {info['bounds']} 中心={info['center']}")
    
    print(f"\n✓ 标注完成，保存到: {output_path}")
    print("=" * 60)

if __name__ == "__main__":
    ui_dump_path = "/tmp/current_ui_dump.xml"
    screenshot_path = "/tmp/current_screenshot.png"
    output_path = "/Users/sh01617ml/workspace/KPP/screenshots/annotated_question_page.png"
    
    if not Path(ui_dump_path).exists():
        print(f"❌ UI dump文件不存在: {ui_dump_path}")
        sys.exit(1)
    
    if not Path(screenshot_path).exists():
        print(f"❌ 截图文件不存在: {screenshot_path}")
        sys.exit(1)
    
    annotate_screenshot(screenshot_path, ui_dump_path, output_path)
