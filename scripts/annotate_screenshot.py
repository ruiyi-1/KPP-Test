#!/usr/bin/env python3
"""
在截图上标注预期点击位置
"""
from PIL import Image, ImageDraw, ImageFont
import sys

# 坐标信息
part_a_center = (638, 1820)
part_a_bounds = [14, 1722, 1262, 1918]

language_button_center = (638, 970)
language_button_bounds = [162, 879, 1114, 1061]

# 读取截图
screenshot_path = "/Users/sh01617ml/workspace/KPP/screenshots/current_screen.png"
output_path = "/Users/sh01617ml/workspace/KPP/screenshots/annotated_screen.png"

try:
    img = Image.open(screenshot_path)
    draw = ImageDraw.Draw(img)
    
    # 标注Part A按钮（绿色）
    # 绘制边界框
    draw.rectangle(
        [part_a_bounds[0], part_a_bounds[1], part_a_bounds[2], part_a_bounds[3]],
        outline="green",
        width=5
    )
    # 绘制中心点
    draw.ellipse(
        [part_a_center[0]-10, part_a_center[1]-10, part_a_center[0]+10, part_a_center[1]+10],
        fill="green",
        outline="darkgreen",
        width=2
    )
    # 添加标签
    draw.text(
        (part_a_bounds[0], part_a_bounds[1] - 30),
        "Part A (正确位置)",
        fill="green",
        stroke_width=2,
        stroke_fill="white"
    )
    
    # 标注切换语言按钮（红色 - 错误点击的位置）
    # 绘制边界框
    draw.rectangle(
        [language_button_bounds[0], language_button_bounds[1], 
         language_button_bounds[2], language_button_bounds[3]],
        outline="red",
        width=5
    )
    # 绘制中心点
    draw.ellipse(
        [language_button_center[0]-10, language_button_center[1]-10, 
         language_button_center[0]+10, language_button_center[1]+10],
        fill="red",
        outline="darkred",
        width=2
    )
    # 添加标签
    draw.text(
        (language_button_bounds[0], language_button_bounds[1] - 30),
        "切换语言 (错误点击)",
        fill="red",
        stroke_width=2,
        stroke_fill="white"
    )
    
    # 保存标注后的图片
    img.save(output_path)
    print(f"✓ 标注完成，保存到: {output_path}")
    print(f"\n坐标信息:")
    print(f"  Part A按钮中心: {part_a_center}")
    print(f"  切换语言按钮中心: {language_button_center}")
    print(f"  问题: 如果点击了 {language_button_center}，说明点击了切换语言按钮而不是Part A")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
