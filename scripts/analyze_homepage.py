#!/usr/bin/env python3
"""
分析首页结构并在截图上标注
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

def analyze_homepage_ui_dump(ui_dump_path):
    """分析首页UI dump，提取关键元素"""
    with open(ui_dump_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    root = ET.fromstring(content)
    
    elements = {
        "exercise_button": None,
        "part_buttons": [],
        "language_button": None,
        "other_buttons": [],
        "text_elements": []
    }
    
    for elem in root.iter():
        class_name = elem.get("class", "")
        content_desc = elem.get("content-desc", "").strip()
        text = elem.get("text", "").strip()
        bounds = parse_bounds(elem.get("bounds", ""))
        clickable = elem.get("clickable", "false") == "true"
        
        if not bounds:
            continue
        
        x1, y1, x2, y2 = bounds
        center = ((x1 + x2) // 2, (y1 + y2) // 2)
        width = x2 - x1
        height = y2 - y1
        
        combined_text = (content_desc + " " + text).lower()
        
        elem_info = {
            "element": elem,
            "bounds": bounds,
            "center": center,
            "size": (width, height),
            "class": class_name,
            "content_desc": content_desc,
            "text": text,
            "clickable": clickable
        }
        
        # 识别Exercise按钮
        if "exercise" in combined_text and clickable:
            if not elements["exercise_button"] or y1 < elements["exercise_button"]["bounds"][1]:
                elements["exercise_button"] = elem_info
        
        # 识别Part按钮（A, B, C）
        if "part" in combined_text and clickable:
            # 检查是否是Part A/B/C
            if any(part in combined_text for part in ["part a", "part b", "part c"]):
                elements["part_buttons"].append(elem_info)
        
        # 识别语言切换按钮
        if any(keyword in combined_text for keyword in ["language", "bahasa", "tukar", "切换", "语言"]):
            if clickable:
                elements["language_button"] = elem_info
        
        # 收集其他可点击按钮
        if clickable and class_name.endswith("Button"):
            if not any([
                "exercise" in combined_text,
                "part" in combined_text,
                "language" in combined_text or "bahasa" in combined_text or "tukar" in combined_text
            ]):
                elements["other_buttons"].append(elem_info)
        
        # 收集文本元素（用于理解页面结构）
        if (content_desc or text) and len(content_desc + text) > 10:
            if y1 > 500:  # 排除顶部状态栏
                elements["text_elements"].append(elem_info)
    
    # 按Y坐标排序Part按钮
    elements["part_buttons"].sort(key=lambda x: x["bounds"][1])
    
    return elements

def annotate_homepage_screenshot(screenshot_path, ui_dump_path, output_path):
    """在首页截图上标注UI元素"""
    # 分析UI dump
    elements = analyze_homepage_ui_dump(ui_dump_path)
    
    # 打开截图
    img = Image.open(screenshot_path)
    draw = ImageDraw.Draw(img)
    
    # 尝试加载字体
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
        font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    colors = {
        "exercise": "blue",
        "part": "green",
        "language": "red",
        "other": "orange"
    }
    
    # 标注Exercise按钮
    if elements["exercise_button"]:
        info = elements["exercise_button"]
        x1, y1, x2, y2 = info["bounds"]
        draw.rectangle([x1, y1, x2, y2], outline=colors["exercise"], width=4)
        label = info["content_desc"] or info["text"] or "Exercise"
        draw.text((x1, y1 - 30), f"Exercise按钮: {label}", 
                 fill=colors["exercise"], font=font_medium,
                 stroke_width=2, stroke_fill="white")
        cx, cy = info["center"]
        draw.ellipse([cx-10, cy-10, cx+10, cy+10], fill=colors["exercise"], outline="white", width=2)
    
    # 标注Part按钮
    part_labels = ["Part A", "Part B", "Part C"]
    for idx, part in enumerate(elements["part_buttons"]):
        x1, y1, x2, y2 = part["bounds"]
        draw.rectangle([x1, y1, x2, y2], outline=colors["part"], width=4)
        label = part["content_desc"] or part["text"] or part_labels[idx] if idx < len(part_labels) else f"Part {idx+1}"
        draw.text((x1, y1 - 30), label, 
                 fill=colors["part"], font=font_medium,
                 stroke_width=2, stroke_fill="white")
        cx, cy = part["center"]
        draw.ellipse([cx-10, cy-10, cx+10, cy+10], fill=colors["part"], outline="white", width=2)
    
    # 标注语言切换按钮
    if elements["language_button"]:
        info = elements["language_button"]
        x1, y1, x2, y2 = info["bounds"]
        draw.rectangle([x1, y1, x2, y2], outline=colors["language"], width=4)
        label = info["content_desc"] or info["text"] or "Language"
        draw.text((x1, y1 - 30), f"语言切换: {label}", 
                 fill=colors["language"], font=font_medium,
                 stroke_width=2, stroke_fill="white")
        cx, cy = info["center"]
        draw.ellipse([cx-10, cy-10, cx+10, cy+10], fill=colors["language"], outline="white", width=2)
    
    # 标注其他按钮（最多显示5个）
    for idx, btn in enumerate(elements["other_buttons"][:5]):
        x1, y1, x2, y2 = btn["bounds"]
        draw.rectangle([x1, y1, x2, y2], outline=colors["other"], width=2)
        label = btn["content_desc"] or btn["text"] or f"Button {idx+1}"
        if len(label) > 20:
            label = label[:20] + "..."
        draw.text((x1, y1 - 25), label, 
                 fill=colors["other"], font=font_small,
                 stroke_width=1, stroke_fill="white")
    
    # 保存标注后的图片
    img.save(output_path)
    
    # 打印分析结果
    print("=" * 60)
    print("📊 首页结构分析")
    print("=" * 60)
    print(f"\n📍 元素位置信息:")
    
    if elements["exercise_button"]:
        info = elements["exercise_button"]
        print(f"  Exercise按钮: {info['bounds']} 中心={info['center']}")
        print(f"    内容: '{info['content_desc'] or info['text']}'")
    
    print(f"\n  Part按钮 ({len(elements['part_buttons'])} 个):")
    for idx, part in enumerate(elements["part_buttons"]):
        label = part["content_desc"] or part["text"] or f"Part {idx+1}"
        print(f"    {label}: {part['bounds']} 中心={part['center']} 尺寸={part['size']}")
    
    if elements["language_button"]:
        info = elements["language_button"]
        print(f"\n  语言切换按钮: {info['bounds']} 中心={info['center']}")
        print(f"    内容: '{info['content_desc'] or info['text']}'")
        print(f"    ⚠️  注意：这个按钮在Y={info['center'][1]}，Part按钮在Y={elements['part_buttons'][0]['center'][1] if elements['part_buttons'] else 'N/A'}")
    
    if elements["other_buttons"]:
        print(f"\n  其他按钮 ({len(elements['other_buttons'])} 个):")
        for btn in elements["other_buttons"][:5]:
            label = btn["content_desc"] or btn["text"] or "Unknown"
            print(f"    {label}: {btn['bounds']}")
    
    print(f"\n✓ 标注完成，保存到: {output_path}")
    print("=" * 60)
    
    # 输出重要提示
    if elements["language_button"] and elements["part_buttons"]:
        lang_y = elements["language_button"]["center"][1]
        part_y = elements["part_buttons"][0]["center"][1]
        if lang_y < part_y:
            print(f"\n⚠️  重要提示：")
            print(f"  语言切换按钮 (Y={lang_y}) 在 Part按钮 (Y={part_y}) 上方")
            print(f"  点击Part按钮时需要确保Y坐标 > {lang_y + 50}，避免误点击语言按钮")

if __name__ == "__main__":
    ui_dump_path = "/tmp/homepage_ui_dump.xml"
    screenshot_path = "/tmp/homepage_screenshot.png"
    output_path = "/Users/sh01617ml/workspace/KPP/screenshots/annotated_homepage.png"
    
    if not Path(ui_dump_path).exists():
        print(f"❌ UI dump文件不存在: {ui_dump_path}")
        sys.exit(1)
    
    if not Path(screenshot_path).exists():
        print(f"❌ 截图文件不存在: {screenshot_path}")
        sys.exit(1)
    
    annotate_homepage_screenshot(screenshot_path, ui_dump_path, output_path)
