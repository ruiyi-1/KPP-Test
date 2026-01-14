#!/usr/bin/env python3
"""
KPP题目截图采集脚本
功能：通过adb自动化控制手机App，采集题目截图
支持：断点续传、广告处理、页面更新检测
"""

import os
import sys
import json
import time
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import hashlib
from PIL import Image

# 配置
DATA_DIR = Path(__file__).parent.parent / "data"
QUESTIONS_DIR = DATA_DIR / "questions"  # 存储题目JSON数据
IMAGES_DIR = Path(__file__).parent.parent / "images"
OPTIONS_IMAGES_DIR = IMAGES_DIR / "options"
PROGRESS_FILE = Path(__file__).parent / "progress.json"
WAIT_TIME_AFTER_CLICK = 2  # 点击选项后等待颜色反馈的时间（秒）
WAIT_TIME_PAGE_UPDATE = 3  # 等待页面更新的时间（秒）
AD_WAIT_TIMEOUT = 10  # 广告等待超时时间（秒）

# Part顺序
PARTS_ORDER = ["A", "B", "C"]

class ADBController:
    """ADB控制器"""
    
    def __init__(self, device_id: Optional[str] = None):
        self.device_id = device_id
        self.check_adb_connection()
    
    def _adb_cmd(self, *args) -> List[str]:
        """构建adb命令"""
        cmd = ["adb"]
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        cmd.extend(args)
        return cmd
    
    def check_adb_connection(self):
        """检查adb连接"""
        try:
            result = subprocess.run(
                self._adb_cmd("devices"),
                capture_output=True,
                text=True,
                timeout=5
            )
            devices = [line for line in result.stdout.split("\n") if "device" in line and "List" not in line]
            if not devices:
                raise Exception("未检测到adb设备连接")
            if self.device_id:
                print(f"✓ ADB连接正常 (设备: {self.device_id})")
            else:
                if len(devices) > 1:
                    print(f"⚠️  检测到多个设备，建议使用 -d 参数指定设备ID")
                    print(f"   可用设备: {[d.split()[0] for d in devices]}")
                print("✓ ADB连接正常")
        except FileNotFoundError:
            raise Exception("未找到adb命令，请确保已安装Android SDK Platform Tools")
        except Exception as e:
            raise Exception(f"ADB连接失败: {e}")
    
    def get_ui_tree(self) -> str:
        """获取UI元素树（XML格式）"""
        # 将UI树dump到设备
        subprocess.run(
            self._adb_cmd("shell", "uiautomator", "dump", "/sdcard/ui_dump.xml"),
            check=True,
            timeout=5
        )
        # 拉取到本地
        subprocess.run(
            self._adb_cmd("pull", "/sdcard/ui_dump.xml", "/tmp/ui_dump.xml"),
            check=True,
            timeout=5
        )
        # 读取内容
        with open("/tmp/ui_dump.xml", "r", encoding="utf-8") as f:
            return f.read()
    
    def take_screenshot(self, output_path: Path):
        """截图并保存到指定路径"""
        # 截图到设备
        subprocess.run(
            self._adb_cmd("shell", "screencap", "-p", "/sdcard/screenshot.png"),
            check=True,
            timeout=5
        )
        # 拉取到本地
        subprocess.run(
            self._adb_cmd("pull", "/sdcard/screenshot.png", str(output_path)),
            check=True,
            timeout=5
        )
        print(f"  ✓ 截图已保存: {output_path}")
    
    def tap(self, x: int, y: int):
        """点击指定坐标"""
        print(f"  📍 ADB点击坐标: ({x}, {y})")
        # 确保坐标是整数
        x, y = int(x), int(y)
        result = subprocess.run(
            self._adb_cmd("shell", "input", "tap", str(x), str(y)),
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode != 0:
            print(f"  ⚠️  ADB点击失败: {result.stderr}")
        else:
            print(f"  ✓ ADB点击命令执行成功")
        time.sleep(0.5)  # 点击后短暂等待
    
    def get_element_bounds(self, element) -> Optional[Tuple[int, int, int, int]]:
        """从UI元素获取边界坐标"""
        bounds = element.get("bounds")
        if not bounds:
            return None
        # 格式: "[x1,y1][x2,y2]"
        try:
            # 先按"]["分割，得到两个坐标字符串
            parts = bounds.split("][")
            if len(parts) != 2:
                return None
            # 去掉第一个的"["和第二个的"]"
            coord1 = parts[0].replace("[", "")
            coord2 = parts[1].replace("]", "")
            x1, y1 = map(int, coord1.split(","))
            x2, y2 = map(int, coord2.split(","))
            return (x1, y1, x2, y2)
        except Exception as e:
            return None
    
    def get_center(self, bounds: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """获取边界中心点坐标"""
        x1, y1, x2, y2 = bounds
        return ((x1 + x2) // 2, (y1 + y2) // 2)

class QuestionCapture:
    """题目采集器"""
    
    def __init__(self, device_id: Optional[str] = None):
        self.adb = ADBController(device_id)
        self.current_part = None  # 当前Part: "A", "B", "C"
        self.part_question_id = {}  # 每个Part的题目编号: {"A": 0, "B": 0, "C": 0}
        self.total_question_id = 0  # 总题目编号（跨Part）
        self.load_progress()
    
    def load_progress(self):
        """加载进度"""
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                progress = json.load(f)
                # 兼容旧格式
                if "last_question_id" in progress:
                    # 旧格式，重置
                    self.current_part = None
                    self.part_question_id = {"A": 0, "B": 0, "C": 0}
                    self.total_question_id = progress.get("last_question_id", 0)
                    print(f"📂 检测到旧格式进度文件，已重置")
                else:
                    self.current_part = progress.get("current_part")
                    self.part_question_id = progress.get("part_question_id", {})
                    self.total_question_id = progress.get("total_question_id", 0)
                    if self.current_part:
                        print(f"📂 加载进度: 当前Part = {self.current_part}, Part题目ID = {self.part_question_id.get(self.current_part, 0)}, 总题目ID = {self.total_question_id}")
                    else:
                        print(f"📂 加载进度: 总题目ID = {self.total_question_id}")
        else:
            self.current_part = None
            self.part_question_id = {"A": 0, "B": 0, "C": 0}
            self.total_question_id = 0
            print("📂 开始新的采集任务")
    
    def save_progress(self):
        """保存进度"""
        progress = {
            "current_part": self.current_part,
            "part_question_id": self.part_question_id,
            "total_question_id": self.total_question_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)
    
    def get_current_question_id(self) -> int:
        """获取当前Part的题目编号"""
        if self.current_part:
            return self.part_question_id.get(self.current_part, 0)
        return 0
    
    def increment_question_id(self):
        """增加题目编号"""
        if self.current_part:
            self.part_question_id[self.current_part] = self.part_question_id.get(self.current_part, 0) + 1
        self.total_question_id += 1
    
    def find_elements_by_text(self, root, text: str, partial: bool = False) -> List:
        """根据文本查找元素"""
        results = []
        for elem in root.iter():
            text_attr = elem.get("text", "").strip()
            content_desc = elem.get("content-desc", "").strip()
            
            if partial:
                if text.lower() in text_attr.lower() or text.lower() in content_desc.lower():
                    results.append(elem)
            else:
                if text_attr == text or content_desc == text:
                    results.append(elem)
        return results
    
    def find_next_button(self, root) -> Optional[ET.Element]:
        """查找"下一页"按钮"""
        print("  📝 [find_next_button] 开始查找Next按钮...")
        next_count = 0
        # 方法1: 直接遍历所有元素查找Next按钮（更可靠）
        for elem in root.iter():
            content_desc = elem.get("content-desc", "").strip()
            text = elem.get("text", "").strip()
            combined = (content_desc + " " + text).lower()
            
            # 检查是否包含next关键词（精确匹配"next"）
            if "next" in combined or "下一" in combined:
                next_count += 1
                clickable = elem.get("clickable", "false") == "true"
                bounds = self.adb.get_element_bounds(elem)
                # 调试信息
                print(f"  📝 [find_next_button] 找到Next元素 #{next_count}: clickable={clickable}, bounds={bounds}, content-desc='{content_desc}'")
                if clickable and bounds:
                    print(f"  ✓ [find_next_button] Next按钮匹配成功，准备返回元素")
                    print(f"  📝 [find_next_button] 返回元素类型: {type(elem)}, tag: {elem.tag}")
                    return elem
                else:
                    print(f"  ⚠️  [find_next_button] Next元素 #{next_count} 不符合条件: clickable={clickable}, bounds={bounds}")
        
        print(f"  📝 [find_next_button] 方法1遍历完成，找到 {next_count} 个Next相关元素，但都不符合条件")
        
        # 方法2: 通过文本匹配（备用方法）
        print("  📝 [find_next_button] 尝试方法2: 文本匹配...")
        next_texts = ["Next", "next", "下一页", "NEXT", ">", "→"]
        for text in next_texts:
            elements = self.find_elements_by_text(root, text, partial=True)
            if elements:
                print(f"  📝 [find_next_button] 方法2找到 {len(elements)} 个匹配 '{text}' 的元素")
                # 优先选择可点击的元素
                for elem in elements:
                    if elem.get("clickable", "false") == "true":
                        bounds = self.adb.get_element_bounds(elem)
                        if bounds:
                            print(f"  ✓ [find_next_button] 方法2找到可点击的Next按钮")
                            return elem
                # 如果没有可点击的，返回第一个有bounds的
                for elem in elements:
                    bounds = self.adb.get_element_bounds(elem)
                    if bounds:
                        print(f"  ✓ [find_next_button] 方法2找到有bounds的Next按钮")
                        return elem
        
        # 方法3: 通过位置查找（底部右侧的按钮通常是Next）
        print("  📝 [find_next_button] 尝试方法3: 位置查找（底部右侧）...")
        clickable_elements = []
        for elem in root.iter():
            if elem.get("clickable", "false") == "true":
                bounds = self.adb.get_element_bounds(elem)
                if bounds:
                    x1, y1, x2, y2 = bounds
                    # 检查是否在屏幕底部（Y坐标大于屏幕高度的70%）
                    # 并且靠右（X坐标大于屏幕宽度的50%）
                    screen_height = 2848  # 根据设备调整
                    screen_width = 1276
                    if y1 > screen_height * 0.7 and x1 > screen_width * 0.5:
                        content = (elem.get("content-desc", "") + " " + elem.get("text", "")).strip()
                        clickable_elements.append((y1, x1, elem, content))
        
        if clickable_elements:
            # 按Y坐标和X坐标排序，找到最右下角的按钮
            clickable_elements.sort(key=lambda x: (x[0], -x[1]), reverse=True)
            print(f"  📝 [find_next_button] 方法3找到 {len(clickable_elements)} 个底部右侧按钮")
            print(f"  📝 [find_next_button] 最右下角按钮: Y={clickable_elements[0][0]}, X={clickable_elements[0][1]}, content='{clickable_elements[0][3]}'")
            return clickable_elements[0][2]  # 返回最右下角的元素
        
        print("  ❌ [find_next_button] 所有方法都未找到Next按钮，返回None")
        return None
    
    def is_in_home_page(self, root) -> bool:
        """检查是否在首页"""
        # 查找首页标识：Exercise、Theory Test、KPP Test等
        home_indicators = ["Exercise", "Theory Test", "KPP Test", "KEJARA System", "Colour Blind Test"]
        for indicator in home_indicators:
            elements = self.find_elements_by_text(root, indicator, partial=True)
            if elements:
                return True
        return False
    
    def is_in_language_selection_page(self, root) -> bool:
        """检查是否在语言选择页面"""
        # 查找语言选择页面的特征：同时存在多个语言选项
        language_keywords = ["Bahasa Melayu", "English", "中文"]
        found_count = 0
        for keyword in language_keywords:
            elements = self.find_elements_by_text(root, keyword, partial=True)
            if elements:
                found_count += 1
        # 如果找到至少2个语言选项，说明在语言选择页面
        return found_count >= 2
    
    def select_language(self, language: str = "English") -> bool:
        """选择语言"""
        print(f"  🌐 检测到语言选择页面，选择语言: {language}")
        root = ET.fromstring(self.adb.get_ui_tree())
        
        # 方法1: 通过文本查找
        elements = self.find_elements_by_text(root, language, partial=True)
        for elem in elements:
            # 检查元素本身是否可点击
            if elem.get("clickable", "false") == "true":
                bounds = self.adb.get_element_bounds(elem)
                if bounds:
                    x, y = self.adb.get_center(bounds)
                    content = elem.get("content-desc", "") or elem.get("text", "")
                    print(f"  🎯 点击语言选项: ({x}, {y}) - '{content}'")
                    self.adb.tap(x, y)
                    time.sleep(2)  # 等待页面加载
                    return True
            
            # 方法2: 如果元素本身不可点击，查找可点击的父元素
            parent = elem
            for _ in range(5):  # 向上查找5层
                parent = parent.getparent()
                if parent is None:
                    break
                if parent.get("clickable", "false") == "true":
                    bounds = self.adb.get_element_bounds(parent)
                    if bounds:
                        x, y = self.adb.get_center(bounds)
                        print(f"  🎯 点击语言选项（父元素）: ({x}, {y})")
                        self.adb.tap(x, y)
                        time.sleep(2)
                        return True
        
        # 方法3: 通过位置查找（English通常在中间位置）
        if language.lower() == "english":
            # 查找所有可点击元素，找到Y坐标在1300-1700之间的（语言选择通常在屏幕中部）
            clickable_elements = []
            for elem in root.iter():
                if elem.get("clickable", "false") == "true":
                    bounds = self.adb.get_element_bounds(elem)
                    if bounds:
                        x1, y1, x2, y2 = bounds
                        if 1300 < y1 < 1700:  # 语言选择区域
                            content = (elem.get("content-desc", "") + " " + elem.get("text", "")).lower()
                            if "english" in content or len(content.strip()) < 3:  # English或空内容
                                clickable_elements.append((y1, elem))
            
            if clickable_elements:
                # 按Y坐标排序，English通常在中间
                clickable_elements.sort(key=lambda x: x[0])
                if len(clickable_elements) >= 2:
                    # 选择中间的（通常是English）
                    middle_idx = len(clickable_elements) // 2
                    _, elem = clickable_elements[middle_idx]
                    bounds = self.adb.get_element_bounds(elem)
                    if bounds:
                        x, y = self.adb.get_center(bounds)
                        print(f"  🎯 点击语言选项（位置定位）: ({x}, {y})")
                        self.adb.tap(x, y)
                        time.sleep(2)
                        return True
        
        return False
    
    def is_in_question_page(self, root) -> bool:
        """检查是否在题目页面"""
        # 方法1: 查找"下一页"或"Previous"按钮
        next_button = self.find_next_button(root)
        if next_button:
            print("  ✓ 检测到Next按钮，确认在题目页面")
            return True
        
        # 方法2: 检查是否有选项（选项通常在题目页面）
        options = self._find_options_in_page(root)
        if len(options) >= 2:  # 至少2个选项
            print(f"  ✓ 检测到{len(options)}个选项，确认在题目页面")
            return True
        
        # 方法3: 检查是否有题目编号（如"1/150"）
        for elem in root.iter():
            content_desc = elem.get("content-desc", "").strip()
            text = elem.get("text", "").strip()
            combined = content_desc + " " + text
            # 题目编号通常包含"/"和数字，如"1/150"、"3/250"
            if "/" in combined and any(c.isdigit() for c in combined):
                # 检查格式是否像题目编号
                parts = combined.split("/")
                if len(parts) == 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
                    print(f"  ✓ 检测到题目编号: {combined.strip()}")
                    return True
        
        print("  ⚠️  未检测到题目页面特征（Next按钮、选项或题目编号）")
        return False
    
    def find_exercise_button(self, root) -> Optional[ET.Element]:
        """查找Exercise按钮"""
        exercise_keywords = ["Exercise", "练习", "A 部分", "B 部分", "C 部分"]
        for keyword in exercise_keywords:
            elements = self.find_elements_by_text(root, keyword, partial=True)
            for elem in elements:
                if elem.get("clickable", "false") == "true":
                    content_desc = elem.get("content-desc", "").strip()
                    text = elem.get("text", "").strip()
                    # 优先匹配"Exercise"
                    if "Exercise" in content_desc or "Exercise" in text:
                        return elem
        return None
    
    def expand_exercise(self, root) -> bool:
        """展开Exercise部分"""
        print("  🔍 查找Exercise按钮...")
        exercise_btn = self.find_exercise_button(root)
        if exercise_btn:
            bounds = self.adb.get_element_bounds(exercise_btn)
            if bounds:
                x, y = self.adb.get_center(bounds)
                print(f"  🎯 点击Exercise展开: ({x}, {y})")
                self.adb.tap(x, y)
                time.sleep(2)  # 等待展开
                return True
        return False
    
    def find_part_buttons(self, root) -> List[ET.Element]:
        """查找Part A/B/C按钮"""
        parts = []
        for elem in root.iter():
            content_desc = elem.get("content-desc", "").strip()
            text = elem.get("text", "").strip()
            
            # 合并所有文本，转为小写进行匹配（大小写忽略）
            combined_text = (content_desc + " " + text).lower()
            
            # 排除明显的非Part按钮
            exclude_keywords = ["exercise", "theory", "colour", "blind", "kejara", "tukar", "bahasa", "change", "language", "中文", "english"]
            if any(keyword in combined_text for keyword in exclude_keywords):
                continue
            
            # 检查是否包含 "part a"、"part b"、"part c" 等关键词
            part_keywords = ["part a", "part b", "part c", "a 部分", "b 部分", "c 部分"]
            matched_keyword = None
            for keyword in part_keywords:
                if keyword in combined_text:
                    matched_keyword = keyword
                    break
            
            # 如果匹配到Part关键词
            if matched_keyword:
                # 检查是否有bounds属性且可点击
                bounds = self.adb.get_element_bounds(elem)
                clickable = elem.get("clickable", "false") == "true"
                focusable = elem.get("focusable", "false") == "true"
                if bounds and (clickable or focusable):
                    parts.append(elem)
                else:
                    # 调试信息
                    if not bounds:
                        print(f"  ⚠️  Part按钮无bounds: {content_desc}")
                    elif not clickable and not focusable:
                        print(f"  ⚠️  Part按钮不可点击: {content_desc} clickable={clickable} focusable={focusable}")
        
        return parts
    
    def enter_part(self, part_name: str = "A") -> bool:
        """进入指定的Part（A/B/C）"""
        print(f"  🔍 查找并进入 Part {part_name}...")
        root = ET.fromstring(self.adb.get_ui_tree())
        
        # 先检查是否在首页，如果是则先展开Exercise
        if self.is_in_home_page(root):
            print("  📱 检测到在首页，先展开Exercise...")
            if not self.expand_exercise(root):
                print("  ⚠️  无法展开Exercise，尝试直接查找Part...")
            else:
                # 重新获取UI树（Exercise已展开）
                time.sleep(1)
                root = ET.fromstring(self.adb.get_ui_tree())
        
        parts = self.find_part_buttons(root)
        print(f"  📋 找到 {len(parts)} 个可能的Part按钮")
        
        # 调试：打印所有找到的按钮信息
        for idx, part in enumerate(parts):
            content_desc = part.get("content-desc", "").strip()
            text = part.get("text", "").strip()
            bounds = self.adb.get_element_bounds(part)
            if bounds:
                x, y = self.adb.get_center(bounds)
                print(f"  [{idx}] content-desc='{content_desc}' text='{text}' 中心=({x}, {y})")
        
        for part in parts:
            content_desc = part.get("content-desc", "").strip()
            text = part.get("text", "").strip()
            combined_text = (content_desc + " " + text).lower()  # 转为小写进行匹配
            
            # 调试：打印所有找到的Part按钮信息
            print(f"  🔍 检查按钮: content-desc='{content_desc}', text='{text}'")
            
            # 大小写忽略的匹配：检查是否包含 "part a"、"part b"、"part c" 等
            part_patterns = [
                f"part {part_name.lower()}",
                f"{part_name.lower()} 部分",
                f"part{part_name.lower()}",
                f"{part_name.lower()}部分",
            ]
            
            matched = False
            for pattern in part_patterns:
                if pattern in combined_text:
                    matched = True
                    print(f"  ✓ 匹配成功: 模式 '{pattern}' 匹配到 '{content_desc or text}'")
                    break
            
            if matched:
                bounds = self.adb.get_element_bounds(part)
                if bounds:
                    x, y = self.adb.get_center(bounds)
                    print(f"  🎯 准备点击 Part {part_name}: ({x}, {y}) - '{content_desc or text}'")
                    print(f"  📐 按钮边界: {bounds}")
                    print(f"  ⚠️  验证: Part A应该在Y=1820左右，切换语言在Y=970左右")
                    if y < 1000:
                        print(f"  ❌ 警告: Y坐标{y}太小，可能是切换语言按钮！跳过此按钮")
                        continue
                    self.adb.tap(x, y)
                    time.sleep(3)  # 等待页面加载
                    return True
                else:
                    print(f"  ⚠️  匹配成功但无法获取bounds: '{content_desc or text}'")
        
        print(f"  ⚠️  未找到 Part {part_name} 按钮")
        if parts:
            print(f"  找到的按钮: {[p.get('content-desc', p.get('text', '')) for p in parts[:3]]}")
        return False
    
    def _find_options_in_page(self, root) -> List[ET.Element]:
        """在页面中查找选项按钮（内部方法）"""
        options = []
        # 查找所有可点击的元素，可能是选项
        for elem in root.iter():
            if elem.get("clickable", "false") == "true":
                text = elem.get("text", "").strip()
                content_desc = elem.get("content-desc", "").strip()
                # 选项通常包含字母或数字标签，或者有较长的文本
                if text and (len(text) > 5 or any(c.isalpha() for c in text[:2])):
                    bounds = self.adb.get_element_bounds(elem)
                    if bounds:
                        # 检查是否在屏幕中下部（选项通常在题目下方）
                        _, y1, _, y2 = bounds
                        if y1 > 200:  # 假设题目区域在上方
                            options.append(elem)
                elif content_desc and len(content_desc) > 10:  # content-desc也可能包含选项文本
                    bounds = self.adb.get_element_bounds(elem)
                    if bounds:
                        _, y1, _, y2 = bounds
                        if y1 > 200:
                            options.append(elem)
        
        # 按Y坐标排序（从上到下）
        options.sort(key=lambda e: self.adb.get_element_bounds(e)[1] if self.adb.get_element_bounds(e) else 0)
        return options[:4]  # 最多4个选项
    
    def find_options(self, root) -> List[ET.Element]:
        """查找选项按钮"""
        options = []
        # 使用uiautomator更准确地查找选项
        for elem in root.iter():
            # 选项通常是可点击的，有bounds，在屏幕中下部
            if elem.get("clickable", "false") == "true":
                bounds = self.adb.get_element_bounds(elem)
                if bounds:
                    x1, y1, x2, y2 = bounds
                    content_desc = elem.get("content-desc", "").strip()
                    text = elem.get("text", "").strip()
                    combined_text = (content_desc + " " + text).lower()
                    
                    # 排除明显的非选项元素
                    exclude_keywords = [
                        "next", "previous", "上一", "下一", "back", "返回",
                        "tukar", "bahasa", "change", "language", "切换", "语言",
                        "exercise", "part", "theory", "colour", "blind", "kejara"
                    ]
                    if any(keyword in combined_text for keyword in exclude_keywords):
                        continue
                    
                    # 选项通常在题目下方，Y坐标在800-2500之间（排除顶部和底部导航）
                    # 宽度通常较大（选项按钮比较宽，通常占屏幕宽度的60%以上）
                    screen_width = 1276  # 根据设备调整
                    if 800 < y1 < 2500 and (x2 - x1) > screen_width * 0.5:
                        options.append(elem)
        
        # 按Y坐标排序（从上到下）
        options.sort(key=lambda e: self.adb.get_element_bounds(e)[1] if self.adb.get_element_bounds(e) else 0)
        # 通常有2-4个选项
        return options[:4]
    
    def find_image_elements(self, root) -> List[ET.Element]:
        """查找页面中的ImageView元素（图标/图片）"""
        images = []
        for elem in root.iter():
            # 查找ImageView类型的元素
            if elem.get("class", "").endswith("ImageView"):
                bounds = self.adb.get_element_bounds(elem)
                if bounds:
                    x1, y1, x2, y2 = bounds
                    # 过滤掉太小的元素（可能是装饰性图标）
                    width = x2 - x1
                    height = y2 - y1
                    if width > 50 and height > 50:  # 至少50x50像素
                        images.append(elem)
        
        # 按Y坐标排序（从上到下）
        images.sort(key=lambda e: self.adb.get_element_bounds(e)[1] if self.adb.get_element_bounds(e) else 0)
        return images
    
    def categorize_images(self, root, image_elements: List[ET.Element], options: List[ET.Element]) -> Dict[str, List[ET.Element]]:
        """将图片分类为题目图片和选项图片
        
        题目图片：出现在题目区域的图片（如交通标志），用于帮助理解题目
        选项图片：出现在选项区域的图片，是选项的一部分
        """
        question_images = []
        option_images = []
        
        # 获取选项的Y坐标范围
        option_y_ranges = []
        for option in options:
            bounds = self.adb.get_element_bounds(option)
            if bounds:
                _, y1, _, y2 = bounds
                option_y_ranges.append((y1, y2))
        
        # 获取题目文本的Y坐标范围（通常在屏幕上方）
        question_y_max = 1500  # 题目通常在Y < 1500的区域
        
        for img_elem in image_elements:
            bounds = self.adb.get_element_bounds(img_elem)
            if not bounds:
                continue
            
            _, y1, _, y2 = bounds
            img_center_y = (y1 + y2) // 2
            
            # 判断图片是否在选项区域内
            is_in_option_area = False
            for opt_y1, opt_y2 in option_y_ranges:
                # 检查图片是否与选项区域重叠（允许一些容差）
                if (y1 <= opt_y2 and y2 >= opt_y1):
                    is_in_option_area = True
                    break
            
            if is_in_option_area:
                # 图片在选项区域内，归类为选项图片
                option_images.append(img_elem)
            elif y1 < question_y_max:
                # 图片在题目区域内，归类为题目图片
                question_images.append(img_elem)
            else:
                # 其他位置的图片，默认归类为题目图片（可能是题目的一部分）
                question_images.append(img_elem)
        
        return {
            "question_images": question_images,
            "option_images": option_images
        }
    
    def has_ad(self, root) -> bool:
        """检测是否有广告"""
        ad_keywords = ["关闭", "跳过", "Skip", "Close", "X", "×", "广告", "Ad"]
        for keyword in ad_keywords:
            elements = self.find_elements_by_text(root, keyword, partial=True)
            if elements:
                # 检查是否在屏幕上方或中央（广告通常在顶部）
                for elem in elements:
                    bounds = self.adb.get_element_bounds(elem)
                    if bounds:
                        _, y1, _, _ = bounds
                        content_desc = elem.get("content-desc", "").strip()
                        text = elem.get("text", "").strip()
                        combined = (content_desc + " " + text).lower()
                        # 排除Next按钮（Next可能在底部，但不应被识别为广告）
                        if "next" in combined or "下一" in combined:
                            continue
                        # 广告通常在屏幕上半部分（Y < 500）
                        if y1 < 500:
                            return True
        return False
    
    def close_ad(self, root) -> bool:
        """关闭广告"""
        close_keywords = ["关闭", "跳过", "Skip", "Close", "X", "×"]
        for keyword in close_keywords:
            elements = self.find_elements_by_text(root, keyword, partial=True)
            for elem in elements:
                bounds = self.adb.get_element_bounds(elem)
                if bounds:
                    x, y = self.adb.get_center(bounds)
                    content_desc = elem.get("content-desc", "").strip()
                    text = elem.get("text", "").strip()
                    combined = (content_desc + " " + text).lower()
                    # 排除Next按钮
                    if "next" in combined or "下一" in combined:
                        continue
                    # 广告关闭按钮通常在屏幕上半部分
                    _, y1, _, _ = bounds
                    if y1 < 500:
                        print(f"  🎯 尝试关闭广告: 点击 ({x}, {y}) - '{content_desc or text}'")
                        self.adb.tap(x, y)
                        time.sleep(2)
                        return True
        return False
    
    def wait_for_ad_close(self, timeout: int = AD_WAIT_TIMEOUT) -> bool:
        """等待广告关闭"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            root = ET.fromstring(self.adb.get_ui_tree())
            if not self.has_ad(root):
                return True
            time.sleep(1)
        return False
    
    def compare_screenshots(self, img1_path: Path, img2_path: Path) -> bool:
        """对比两张截图是否相同（简单哈希对比）"""
        if not img1_path.exists() or not img2_path.exists():
            return False
        with open(img1_path, "rb") as f1, open(img2_path, "rb") as f2:
            hash1 = hashlib.md5(f1.read()).hexdigest()
            hash2 = hashlib.md5(f2.read()).hexdigest()
            return hash1 != hash2
    
    def verify_page_update(self) -> bool:
        """验证页面是否更新"""
        try:
            # 获取当前UI树
            current_tree = self.adb.get_ui_tree()
            root = ET.fromstring(current_tree)
            
            # 检查是否有"下一页"按钮（如果页面更新，应该能看到新页面的元素）
            next_button = self.find_next_button(root)
            return next_button is not None
        except Exception as e:
            print(f"  ⚠️  验证页面更新时出错: {e}")
            # 如果验证失败，假设页面已更新（避免阻塞）
            return True
    
    def extract_question_number_from_page(self, root) -> Optional[int]:
        """从UI dump中提取题目页面左上角的题目编号
        
        识别规则（参考ui_element_reference.md）：
        - content-desc包含 "/"（如 "19/150"）
        - 位置：bounds=[252,196][487,276]，Y坐标 < 300
        - 返回当前题目编号（如 19）
        """
        for elem in root.iter():
            bounds = self.adb.get_element_bounds(elem)
            if not bounds:
                continue
            
            x1, y1, x2, y2 = bounds
            
            # 题目编号通常在左上角，Y坐标 < 300
            if y1 >= 300:
                continue
            
            content_desc = elem.get("content-desc", "").strip()
            text = elem.get("text", "").strip()
            combined = (content_desc + " " + text).strip()
            
            # 检查是否包含 "/" 和数字（如 "19/150"）
            if "/" in combined and any(c.isdigit() for c in combined):
                # 尝试解析题目编号
                parts = combined.split("/")
                if len(parts) == 2:
                    try:
                        current_num = int(parts[0].strip())
                        total_num = int(parts[1].strip())
                        print(f"  ✓ 提取到题目编号: {current_num}/{total_num}")
                        return current_num
                    except ValueError:
                        continue
        
        print("  ⚠️  未找到题目编号")
        return None
    
    def check_question_exists(self, part: str, question_number: int) -> bool:
        """检查指定Part和题目编号的题目文件是否已存在"""
        part_lower = part.lower()
        question_id = f"part-{part_lower}-question-{question_number:03d}"
        question_file = QUESTIONS_DIR / f"{question_id}.json"
        return question_file.exists()
    
    def extract_question_text(self, root) -> str:
        """从UI dump中提取题目文本
        
        识别规则（参考ui_element_reference.md）：
        - Y坐标：300-1500
        - 宽度 > 800px
        - content-desc或text属性包含长文本（>50字符）
        """
        question_candidates = []
        
        for elem in root.iter():
            bounds = self.adb.get_element_bounds(elem)
            if not bounds:
                continue
            
            x1, y1, x2, y2 = bounds
            width = x2 - x1
            height = y2 - y1
            
            # 检查是否符合题目文本的特征
            if not (300 < y1 < 1500 and width > 800):
                continue
            
            # 获取文本内容
            content_desc = elem.get("content-desc", "").strip()
            text = elem.get("text", "").strip()
            
            # 优先使用content-desc，如果没有则使用text
            question_text = content_desc if content_desc else text
            
            # 检查文本长度（题目文本通常较长）
            if len(question_text) > 50:
                question_candidates.append({
                    "elem": elem,
                    "text": question_text,
                    "y": y1,
                    "width": width
                })
        
        if not question_candidates:
            # 如果没找到，尝试更宽松的条件
            for elem in root.iter():
                bounds = self.adb.get_element_bounds(elem)
                if not bounds:
                    continue
                
                x1, y1, x2, y2 = bounds
                width = x2 - x1
                
                if not (200 < y1 < 1800 and width > 600):
                    continue
                
                content_desc = elem.get("content-desc", "").strip()
                text = elem.get("text", "").strip()
                question_text = content_desc if content_desc else text
                
                if len(question_text) > 30:
                    question_candidates.append({
                        "elem": elem,
                        "text": question_text,
                        "y": y1,
                        "width": width
                    })
        
        if question_candidates:
            # 按Y坐标排序，选择最上方的（通常是题目文本）
            question_candidates.sort(key=lambda x: x["y"])
            question_text = question_candidates[0]["text"]
            
            # 清理文本：去除多余的空格和换行
            question_text = " ".join(question_text.split())
            
            print(f"  ✓ 提取到题目文本: {question_text[:50]}..." if len(question_text) > 50 else f"  ✓ 提取到题目文本: {question_text}")
            return question_text
        
        print("  ⚠️  未找到题目文本")
        return ""
    
    def extract_options_text(self, root) -> List[Dict[str, str]]:
        """从UI dump中提取选项文本
        
        识别规则：
        - 查找选项按钮（content-desc="A/B/C"或包含选项标签，Y坐标 1800-2500）
        - 从选项元素中提取文本（content-desc或text属性）
        """
        options = []
        option_elements = []
        
        # 方法1: 查找明确标记为A/B/C/D的选项按钮
        for elem in root.iter():
            if elem.get("clickable", "false") != "true":
                continue
            
            bounds = self.adb.get_element_bounds(elem)
            if not bounds:
                continue
            
            x1, y1, x2, y2 = bounds
            
            # 检查是否在选项区域（Y坐标 1800-2500）
            if not (1800 < y1 < 2500):
                continue
            
            content_desc = elem.get("content-desc", "").strip()
            text = elem.get("text", "").strip()
            combined = (content_desc + " " + text).strip()
            
            # 检查是否是选项标签（A/B/C/D）
            option_label = None
            if content_desc in ["A", "B", "C", "D"]:
                option_label = content_desc
            elif text in ["A", "B", "C", "D"]:
                option_label = text
            else:
                # 检查是否包含选项标签（如 "A. Stop" 或 "A Stop"）
                for label in ["A", "B", "C", "D"]:
                    if (combined.startswith(f"{label}.") or 
                        combined.startswith(f"{label} ") or
                        f" {label} " in f" {combined} "):
                        option_label = label
                        break
            
            if option_label:
                option_elements.append({
                    "elem": elem,
                    "label": option_label,
                    "y": y1,
                    "content_desc": content_desc,
                    "text": text
                })
        
        # 方法2: 如果没找到明确标记的选项，使用find_options方法查找可能的选项
        if not option_elements:
            found_options = self.find_options(root)
            # 为找到的选项分配标签（按Y坐标从上到下分配A/B/C/D）
            option_labels = ["A", "B", "C", "D"]
            for idx, elem in enumerate(found_options):
                if idx < len(option_labels):
                    bounds = self.adb.get_element_bounds(elem)
                    if bounds:
                        _, y1, _, _ = bounds
                        content_desc = elem.get("content-desc", "").strip()
                        text = elem.get("text", "").strip()
                        option_elements.append({
                            "elem": elem,
                            "label": option_labels[idx],
                            "y": y1,
                            "content_desc": content_desc,
                            "text": text
                        })
        
        # 按Y坐标排序（从上到下）
        option_elements.sort(key=lambda x: x["y"])
        
        # 提取每个选项的文本
        for opt_info in option_elements:
            elem = opt_info["elem"]
            label = opt_info["label"]
            content_desc = opt_info["content_desc"]
            text = opt_info["text"]
            
            # 尝试从选项元素中提取完整文本
            option_text = ""
            
            # 方法1: 使用content-desc（如果包含选项文本）
            if content_desc and len(content_desc) > 1 and content_desc != label:
                # 如果content-desc包含选项文本（如 "A. Stop"），提取文本部分
                if content_desc.startswith(f"{label}.") or content_desc.startswith(f"{label} "):
                    option_text = content_desc[len(label):].lstrip(". ").strip()
                elif content_desc == label:
                    # 如果content-desc就是标签，跳过
                    pass
                else:
                    option_text = content_desc
            
            # 方法2: 使用text属性
            if not option_text and text and text != label:
                if text.startswith(f"{label}.") or text.startswith(f"{label} "):
                    option_text = text[len(label):].lstrip(". ").strip()
                else:
                    option_text = text
            
            # 方法3: 查找选项元素内的子元素获取文本
            if not option_text:
                for child in elem.iter():
                    if child == elem:
                        continue
                    child_text = child.get("text", "").strip()
                    child_content_desc = child.get("content-desc", "").strip()
                    # 排除标签本身和太短的文本
                    if child_text and child_text != label and len(child_text) > 1:
                        # 如果子元素文本包含标签，提取文本部分
                        if child_text.startswith(f"{label}.") or child_text.startswith(f"{label} "):
                            option_text = child_text[len(label):].lstrip(". ").strip()
                        else:
                            option_text = child_text
                        if option_text:
                            break
                    elif child_content_desc and child_content_desc != label and len(child_content_desc) > 1:
                        if child_content_desc.startswith(f"{label}.") or child_content_desc.startswith(f"{label} "):
                            option_text = child_content_desc[len(label):].lstrip(". ").strip()
                        else:
                            option_text = child_content_desc
                        if option_text:
                            break
            
            # 方法4: 如果还是没找到，尝试从父元素或兄弟元素中查找
            if not option_text:
                parent = elem.getparent()
                if parent is not None:
                    for sibling in parent.iter():
                        if sibling == elem:
                            continue
                        sibling_text = sibling.get("text", "").strip()
                        sibling_content_desc = sibling.get("content-desc", "").strip()
                        if sibling_text and len(sibling_text) > 1 and sibling_text != label:
                            option_text = sibling_text
                            break
                        elif sibling_content_desc and len(sibling_content_desc) > 1 and sibling_content_desc != label:
                            option_text = sibling_content_desc
                            break
            
            # 清理文本：去除多余的空格和换行
            option_text = " ".join(option_text.split()) if option_text else ""
            
            options.append({
                "label": label,
                "text": option_text
            })
            
            if option_text:
                print(f"  ✓ 提取选项 {label}: {option_text[:30]}..." if len(option_text) > 30 else f"  ✓ 提取选项 {label}: {option_text}")
            else:
                print(f"  ⚠️  选项 {label} 文本为空")
        
        if not options:
            print("  ⚠️  未找到选项文本")
        
        return options
    
    def check_option_background_color(self, option, screenshot_path: Path) -> Tuple[bool, bool, Tuple[int, int, int]]:
        """检查选项的背景颜色
        
        Returns:
            (is_green, is_red, rgb): 是否为绿色、是否为红色、RGB值
        """
        try:
            bounds = self.adb.get_element_bounds(option)
            if not bounds:
                return False, False, (0, 0, 0)
            
            img = Image.open(screenshot_path)
            x1, y1, x2, y2 = bounds
            
            # 确保坐标在图片范围内
            img_width, img_height = img.size
            x1 = max(0, min(x1, img_width - 1))
            y1 = max(0, min(y1, img_height - 1))
            x2 = max(x1 + 1, min(x2, img_width))
            y2 = max(y1 + 1, min(y2, img_height))
            
            # 提取选项区域中心点的颜色（取中心区域的平均颜色）
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            # 取中心区域的小块（20x20像素）来计算平均颜色
            sample_size = 20
            x_start = max(0, center_x - sample_size // 2)
            y_start = max(0, center_y - sample_size // 2)
            x_end = min(img_width, center_x + sample_size // 2)
            y_end = min(img_height, center_y + sample_size // 2)
            
            # 计算平均RGB值
            total_r, total_g, total_b = 0, 0, 0
            pixel_count = 0
            
            for x in range(x_start, x_end):
                for y in range(y_start, y_end):
                    pixel = img.getpixel((x, y))
                    if len(pixel) >= 3:  # RGB或RGBA
                        total_r += pixel[0]
                        total_g += pixel[1]
                        total_b += pixel[2]
                        pixel_count += 1
            
            if pixel_count > 0:
                avg_r = total_r // pixel_count
                avg_g = total_g // pixel_count
                avg_b = total_b // pixel_count
                
                # 判断颜色：绿色（正确答案）或红色（错误答案）
                is_green = (avg_g > avg_r + 20 and avg_g > avg_b + 20 and avg_g > 80) or \
                          (avg_g > 150 and avg_g > avg_r and avg_g > avg_b)
                is_red = (avg_r > avg_g + 20 and avg_r > avg_b + 20 and avg_r > 80) or \
                        (avg_r > 150 and avg_r > avg_g and avg_r > avg_b)
                
                return is_green, is_red, (avg_r, avg_g, avg_b)
            
            return False, False, (0, 0, 0)
        except Exception as e:
            print(f"  ⚠️  检查选项背景颜色失败: {e}")
            return False, False, (0, 0, 0)
    
    def get_option_label(self, option, options_list) -> Optional[str]:
        """获取选项的标签（A/B/C/D）"""
        content_desc = option.get("content-desc", "").strip()
        text = option.get("text", "").strip()
        
        # 提取选项标签（A/B/C/D）
        if content_desc in ["A", "B", "C", "D"]:
            return content_desc
        elif text in ["A", "B", "C", "D"]:
            return text
        else:
            # 尝试从文本中提取标签
            combined = (content_desc + " " + text).strip()
            for label in ["A", "B", "C", "D"]:
                if combined.startswith(f"{label}.") or combined.startswith(f"{label} "):
                    return label
            
            # 如果还是没找到，通过选项在列表中的位置来确定标签
            try:
                option_idx = options_list.index(option)
                if option_idx < 4:
                    return ["A", "B", "C", "D"][option_idx]
            except ValueError:
                pass
        
        return None
    
    def detect_correct_answer(self, root, options=None) -> Optional[str]:
        """检测正确答案
        
        通过检查选项背景颜色：
        - 绿色背景 = 正确答案
        - 如果没有绿色，返回None（需要触发选项点击）
        """
        if options is None:
            options = self.find_options(root)
        
        if not options:
            return None
        
        try:
            # 临时截图用于颜色检测
            temp_screenshot_path = Path("/tmp/temp_answer_detect.png")
            self.adb.take_screenshot(temp_screenshot_path)
            
            if not temp_screenshot_path.exists():
                return None
            
            # 检查每个选项的背景颜色
            for option in options:
                is_green, is_red, rgb = self.check_option_background_color(option, temp_screenshot_path)
                
                if is_green:
                    # 找到正确答案
                    answer = self.get_option_label(option, options)
                    if answer:
                        # 删除临时截图
                        if temp_screenshot_path.exists():
                            temp_screenshot_path.unlink()
                        print(f"  ✓ 通过颜色识别找到正确答案: {answer} (绿色背景, RGB={rgb})")
                        return answer
            
            # 删除临时截图
            if temp_screenshot_path.exists():
                temp_screenshot_path.unlink()
            
            # 没有找到绿色背景
            print("  ⚠️  未检测到绿色背景，需要触发选项点击")
            return None
            
        except Exception as e:
            print(f"  ⚠️  颜色识别失败: {e}")
            return None
    
    def detect_correct_answer_by_clicking_options(self, root) -> Optional[str]:
        """通过依次点击选项来检测正确答案
        
        依次点击每个选项，检查哪个选项变成绿色背景
        """
        options = self.find_options(root)
        if not options:
            return None
        
        print(f"  🔍 开始依次点击选项查找正确答案（共{len(options)}个选项）...")
        
        # 依次点击每个选项
        for idx, option in enumerate(options):
            bounds = self.adb.get_element_bounds(option)
            if not bounds:
                continue
            
            x, y = self.adb.get_center(bounds)
            option_label = self.get_option_label(option, options)
            print(f"  🎯 点击选项 {option_label}: ({x}, {y})")
            self.adb.tap(x, y)
            
            # 等待颜色反馈显示
            time.sleep(WAIT_TIME_AFTER_CLICK)
            
            # 重新获取UI树和截图
            root_after_click = ET.fromstring(self.adb.get_ui_tree())
            options_after_click = self.find_options(root_after_click)
            
            # 检查是否有绿色背景
            temp_screenshot_path = Path("/tmp/temp_answer_detect_click.png")
            self.adb.take_screenshot(temp_screenshot_path)
            
            if temp_screenshot_path.exists():
                # 检查所有选项的背景颜色
                for opt in options_after_click:
                    is_green, is_red, rgb = self.check_option_background_color(opt, temp_screenshot_path)
                    
                    if is_green:
                        # 找到正确答案
                        answer = self.get_option_label(opt, options_after_click)
                        if answer:
                            # 删除临时截图
                            if temp_screenshot_path.exists():
                                temp_screenshot_path.unlink()
                            print(f"  ✓ 通过点击选项找到正确答案: {answer} (绿色背景, RGB={rgb})")
                            return answer
                
                # 删除临时截图
                if temp_screenshot_path.exists():
                    temp_screenshot_path.unlink()
        
        print("  ⚠️  点击所有选项后仍未找到绿色背景")
        return None
    
    def extract_icon_from_screenshot(self, screenshot_path: Path, img_elem, output_path: Path) -> bool:
        """从截图中裁剪图片元素并保存
        
        Args:
            screenshot_path: 临时截图路径
            img_elem: 图片元素（XML Element）
            output_path: 输出图片路径
        
        Returns:
            是否成功保存
        """
        try:
            if not screenshot_path.exists():
                print(f"  ⚠️  截图文件不存在: {screenshot_path}")
                return False
            
            # 获取图片元素的bounds坐标
            bounds = self.adb.get_element_bounds(img_elem)
            if not bounds:
                print(f"  ⚠️  无法获取图片元素bounds")
                return False
            
            x1, y1, x2, y2 = bounds
            
            # 打开截图
            img = Image.open(screenshot_path)
            img_width, img_height = img.size
            
            # 确保坐标在图片范围内
            x1 = max(0, min(x1, img_width - 1))
            y1 = max(0, min(y1, img_height - 1))
            x2 = max(x1 + 1, min(x2, img_width))
            y2 = max(y1 + 1, min(y2, img_height))
            
            # 裁剪图片区域
            cropped = img.crop((x1, y1, x2, y2))
            
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存裁剪后的图片
            cropped.save(output_path, "PNG")
            
            return True
        except Exception as e:
            print(f"  ⚠️  裁剪图片失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def capture_question(self) -> bool:
        """采集一道题目"""
        try:
            part_question_num = self.get_current_question_id() + 1
            part_info = f"Part {self.current_part}" if self.current_part else "未知Part"
            print(f"\n📸 开始采集 {part_info} 题目 #{part_question_num} (总题目 #{self.total_question_id + 1})")
            
            # 1. 获取当前页面元素
            ui_tree = self.adb.get_ui_tree()
            root = ET.fromstring(ui_tree)
            
            # 1.5. 检查是否在题目页面，如果不在则尝试进入当前Part
            if not self.is_in_question_page(root):
                if self.current_part:
                    print(f"  ⚠️  当前不在题目页面，尝试重新进入 Part {self.current_part}...")
                    if self.enter_part(self.current_part):
                        time.sleep(3)
                        ui_tree = self.adb.get_ui_tree()
                        root = ET.fromstring(ui_tree)
                        if not self.is_in_question_page(root):
                            print("  ⚠️  进入Part后仍未检测到题目页面")
                            return False
                    else:
                        print("  ❌ 无法进入题目页面")
                        return False
                else:
                    print("  ⚠️  未设置current_part，无法进入题目页面")
                    return False
            
            # 2. 检测并处理广告
            if self.has_ad(root):
                print("  ⚠️  检测到广告，尝试关闭...")
                if self.close_ad(root):
                    if not self.wait_for_ad_close():
                        print("  ❌ 广告关闭超时，保存进度并退出")
                        self.save_progress()
                        return False
                    print("  ✓ 广告已关闭")
                    # 重新获取UI树
                    ui_tree = self.adb.get_ui_tree()
                    root = ET.fromstring(ui_tree)
            
            # 2.5. 提取题目编号并检查是否已存在
            if self.current_part:
                page_question_num = self.extract_question_number_from_page(root)
                if page_question_num is not None:
                    if self.check_question_exists(self.current_part, page_question_num):
                        print(f"  ⏭️  题目 #{page_question_num} 已存在，跳过...")
                        # 需要先点击选项才能点击Next按钮
                        options = self.find_options(root)
                        if options:
                            # 点击第一个选项
                            first_option = options[0]
                            bounds = self.adb.get_element_bounds(first_option)
                            if bounds:
                                x, y = self.adb.get_center(bounds)
                                print(f"  🎯 点击选项以启用Next按钮: ({x}, {y})")
                                self.adb.tap(x, y)
                                time.sleep(1)  # 短暂等待
                                # 重新获取UI树
                                root = ET.fromstring(self.adb.get_ui_tree())
                        
                        # 点击Next按钮进入下一题
                        next_button = self.find_next_button(root)
                        if next_button:
                            bounds = self.adb.get_element_bounds(next_button)
                            if bounds:
                                x, y = self.adb.get_center(bounds)
                                print(f"  🎯 点击'下一页'跳过: ({x}, {y})")
                                self.adb.tap(x, y)
                                time.sleep(WAIT_TIME_PAGE_UPDATE)
                                # 更新进度（使用页面上的题目编号）
                                if page_question_num > self.part_question_id.get(self.current_part, 0):
                                    self.part_question_id[self.current_part] = page_question_num
                                    self.total_question_id = max(self.total_question_id, sum(self.part_question_id.values()))
                                self.save_progress()
                                return True
                        else:
                            print("  ⚠️  未找到Next按钮，可能已到最后一题")
                            # 更新进度
                            if page_question_num > self.part_question_id.get(self.current_part, 0):
                                self.part_question_id[self.current_part] = page_question_num
                                self.total_question_id = max(self.total_question_id, sum(self.part_question_id.values()))
                            self.save_progress()
                            return False
                    else:
                        print(f"  ✓ 题目 #{page_question_num} 不存在，开始采集...")
                        # 更新进度以匹配页面上的题目编号
                        if page_question_num > self.part_question_id.get(self.current_part, 0):
                            self.part_question_id[self.current_part] = page_question_num - 1
                            self.total_question_id = sum(self.part_question_id.values())
            
            # 3. 查找选项
            options = self.find_options(root)
            if not options:
                print("  ⚠️  未找到选项，跳过...")
                return False
            
            print(f"  ✓ 找到 {len(options)} 个选项")
            
            # 4. 先检查是否有绿色背景（可能已经显示了正确答案）
            print("  🔍 检查是否有绿色背景（正确答案）...")
            correct_answer = self.detect_correct_answer(root, options)
            
            # 5. 如果没有绿色背景，依次点击选项查找正确答案
            if correct_answer is None:
                print("  ⚠️  未检测到绿色背景，开始依次点击选项查找正确答案...")
                correct_answer = self.detect_correct_answer_by_clicking_options(root)
                
                # 重新获取UI树（点击选项后页面可能更新）
                root = ET.fromstring(self.adb.get_ui_tree())
                options = self.find_options(root)
            
            # 6. 如果还是没有找到，点击第一个选项继续（必须点击选项才能继续）
            if correct_answer is None:
                print("  ⚠️  仍未找到正确答案，点击第一个选项继续...")
                first_option = options[0]
                bounds = self.adb.get_element_bounds(first_option)
                if bounds:
                    x, y = self.adb.get_center(bounds)
                    print(f"  🎯 点击第一个选项: ({x}, {y})")
                    self.adb.tap(x, y)
                    time.sleep(WAIT_TIME_AFTER_CLICK)
                    # 重新获取UI树
                    root = ET.fromstring(self.adb.get_ui_tree())
                    options = self.find_options(root)
            
            # 7. 重新获取UI树（确保是最新状态）
            print("  🔍 获取最新的UI树...")
            ui_tree_after_click = self.adb.get_ui_tree()
            root_after_click = ET.fromstring(ui_tree_after_click)
            
            if not self.current_part:
                print("  ⚠️  未设置current_part，无法保存题目数据")
                return False
            
            part_lower = self.current_part.lower()
            
            # 从页面提取题目编号（如果之前没有提取，现在重新提取）
            page_question_num = self.extract_question_number_from_page(root_after_click)
            if page_question_num is not None:
                part_question_num = page_question_num
            else:
                # 如果无法提取，使用自动递增的编号
                part_question_num = self.get_current_question_id() + 1
                print(f"  ⚠️  无法从页面提取题目编号，使用自动编号: {part_question_num}")
            
            # 7.1. 提取题目文本
            print("  📝 提取题目文本...")
            question_text = self.extract_question_text(root_after_click)
            if not question_text:
                print("  ⚠️  未能提取题目文本")
                question_text = ""
            
            # 7.2. 提取选项信息
            print("  📝 提取选项信息...")
            options_data = self.extract_options_text(root_after_click)
            
            # 7.3. 如果之前没有找到答案，再次尝试检测
            if correct_answer is None:
                print("  🔍 再次尝试检测正确答案...")
                correct_answer = self.detect_correct_answer(root_after_click)
            
            # 6.4. 查找并提取图片元素（只对图片元素进行截图）
            print("  🖼️  查找页面中的图片元素...")
            image_elements = self.find_image_elements(root_after_click)
            
            # 重新获取选项列表（用于分类图片）
            options_after_click = self.find_options(root_after_click)
            
            # 分类图片：题目图片 vs 选项图片
            categorized_images = self.categorize_images(root_after_click, image_elements, options_after_click)
            question_images = categorized_images["question_images"]
            option_images = categorized_images["option_images"]
            
            print(f"  📸 找到 {len(image_elements)} 个图片元素:")
            print(f"    - 题目图片: {len(question_images)} 个")
            print(f"    - 选项图片: {len(option_images)} 个")
            
            # 临时截图用于提取图片元素（提取后删除）
            temp_screenshot_path = Path("/tmp/temp_screenshot.png")
            question_image_paths = []
            option_image_paths = []
            
            if image_elements:
                print(f"  📸 开始提取图片...")
                # 临时截图
                self.adb.take_screenshot(temp_screenshot_path)
                
                # 确保输出目录存在
                OPTIONS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
                
                # 提取题目图片
                for idx, img_elem in enumerate(question_images):
                    bounds = self.adb.get_element_bounds(img_elem)
                    if bounds:
                        x1, y1, x2, y2 = bounds
                        width = x2 - x1
                        height = y2 - y1
                        # 生成图片文件名（题目图片）
                        image_filename = f"part-{part_lower}-question-{part_question_num:03d}-q-image-{idx+1:02d}.png"
                        image_path = OPTIONS_IMAGES_DIR / image_filename
                        
                        if self.extract_icon_from_screenshot(temp_screenshot_path, img_elem, image_path):
                            relative_path = f"images/options/{image_filename}"
                            question_image_paths.append(relative_path)
                            print(f"  ✓ 题目图片已保存: {image_filename} (位置: [{x1},{y1}][{x2},{y2}], 尺寸: {width}x{height})")
                
                # 提取选项图片
                for idx, img_elem in enumerate(option_images):
                    bounds = self.adb.get_element_bounds(img_elem)
                    if bounds:
                        x1, y1, x2, y2 = bounds
                        width = x2 - x1
                        height = y2 - y1
                        # 生成图片文件名（选项图片）
                        image_filename = f"part-{part_lower}-question-{part_question_num:03d}-opt-image-{idx+1:02d}.png"
                        image_path = OPTIONS_IMAGES_DIR / image_filename
                        
                        if self.extract_icon_from_screenshot(temp_screenshot_path, img_elem, image_path):
                            relative_path = f"images/options/{image_filename}"
                            option_image_paths.append(relative_path)
                            print(f"  ✓ 选项图片已保存: {image_filename} (位置: [{x1},{y1}][{x2},{y2}], 尺寸: {width}x{height})")
                
                # 删除临时截图
                if temp_screenshot_path.exists():
                    temp_screenshot_path.unlink()
            else:
                print("  ℹ️  未找到图片元素")
            
            # 6.5. 保存题目数据到JSON文件
            question_id = f"part-{part_lower}-question-{part_question_num:03d}"
            
            # 确保数据目录存在
            QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)
            question_file = QUESTIONS_DIR / f"{question_id}.json"
            
            # 为选项分配图片（如果有选项图片）
            options_with_images = []
            for idx, opt in enumerate(options_data):
                option_data = {
                    "label": opt["label"],
                    "text": opt["text"],
                    "has_image": False,
                    "image": None
                }
                # 如果选项图片数量与选项数量匹配，尝试分配
                # 注意：这里假设图片顺序与选项顺序对应，实际可能需要更智能的匹配
                if idx < len(option_image_paths):
                    option_data["has_image"] = True
                    option_data["image"] = option_image_paths[idx]
                options_with_images.append(option_data)
            
            question_data = {
                "id": question_id,
                "part": self.current_part,
                "question_number": part_question_num,
                "question_text": question_text,
                "question_images": question_image_paths,  # 题目中的图片（如交通标志）
                "options": options_with_images,
                "correct_answer": correct_answer,
                "has_image_options": len(option_image_paths) > 0,
                "has_question_images": len(question_image_paths) > 0,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(question_file, "w", encoding="utf-8") as f:
                json.dump(question_data, f, indent=2, ensure_ascii=False)
            
            print(f"  ✓ 题目数据已保存: {question_file}")
            
            # 7. 查找并点击"下一页"按钮
            time.sleep(0.5)  # 短暂等待，确保页面更新
            print("  🔍 查找Next按钮...")
            next_button = self.find_next_button(root_after_click)
            print(f"  📊 find_next_button返回值类型: {type(next_button)}")
            print(f"  📊 find_next_button返回值是否为None: {next_button is None}")
            print(f"  📊 not next_button的值: {not next_button}")
            print(f"  📊 bool(next_button)的值: {bool(next_button)}")
            if next_button is not None:
                content_desc = next_button.get("content-desc", "")
                clickable = next_button.get("clickable", "")
                print(f"  📊 next_button元素: content-desc='{content_desc}' clickable={clickable}")
            # 使用 is None 而不是 not，因为Element对象即使存在也可能被判断为False
            if next_button is None:
                print("  ⚠️  未找到'下一页'按钮，可能已到最后一题")
                # 调试：检查是否有Next按钮但没找到
                for elem in root_after_click.iter():
                    content = (elem.get('content-desc', '') + ' ' + elem.get('text', '')).lower()
                    if 'next' in content:
                        content_desc = elem.get('content-desc', '')
                        clickable = elem.get('clickable', 'false')
                        print(f"  🔍 调试: 发现Next元素但未匹配 - content-desc='{content_desc}' clickable={clickable}")
                # 即使找不到Next按钮，也保存进度（可能Part已完成）
                # 使用从页面提取的题目编号
                if 'page_question_num' in locals() and page_question_num is not None:
                    self.part_question_id[self.current_part] = page_question_num
                    self.total_question_id = max(self.total_question_id, sum(self.part_question_id.values()))
                else:
                    self.increment_question_id()
                self.save_progress()
                return False
            
            print(f"  📝 [capture_question] next_button不为None，准备获取bounds...")
            bounds = self.adb.get_element_bounds(next_button)
            print(f"  📝 [capture_question] bounds获取结果: {bounds}")
            if not bounds:
                print("  ❌ 无法获取'下一页'按钮坐标")
                return False
            
            x, y = self.adb.get_center(bounds)
            print(f"  📝 [capture_question] Next按钮中心坐标: ({x}, {y})")
            print(f"  🎯 点击'下一页': ({x}, {y})")
            self.adb.tap(x, y)
            
            # 8. 等待并验证页面更新
            print(f"  ⏳ 等待页面更新 ({WAIT_TIME_PAGE_UPDATE}秒)...")
            time.sleep(WAIT_TIME_PAGE_UPDATE)
            
            if not self.verify_page_update():
                print("  ⚠️  页面可能未更新，继续尝试...")
            
            # 9. 更新进度（使用从页面提取的题目编号）
            if page_question_num is not None:
                # 使用页面上的题目编号
                self.part_question_id[self.current_part] = page_question_num
                # 更新总题目编号（取所有Part的最大值）
                self.total_question_id = max(self.total_question_id, sum(self.part_question_id.values()))
            else:
                # 如果无法提取，使用自动递增
                self.increment_question_id()
            
            self.save_progress()
            
            final_question_num = self.part_question_id.get(self.current_part, 0)
            print(f"  ✓ Part {self.current_part} 题目 #{final_question_num} 采集完成 (总题目 #{self.total_question_id})")
            return True
            
        except KeyboardInterrupt:
            print("\n\n⚠️  用户中断，保存进度...")
            self.save_progress()
            return False
        except Exception as e:
            print(f"  ❌ 采集失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def is_part_completed(self, root) -> bool:
        """检查当前Part是否已完成（通过检测是否回到首页、出现完成提示，或找不到题目页面元素）"""
        # 检查是否回到首页
        if self.is_in_home_page(root):
            print("  ✓ 检测到已回到首页，Part已完成")
            return True
        
        # 检查是否有"完成"、"Finish"等提示
        finish_keywords = ["完成", "Finish", "finish", "Done", "done", "Selesai", "selesai"]
        for keyword in finish_keywords:
            elements = self.find_elements_by_text(root, keyword, partial=True)
            if elements:
                print(f"  ✓ 检测到完成提示 '{keyword}'，Part已完成")
                return True
        
        # 检查是否还在题目页面（如果不在题目页面且不在首页，可能是完成页面）
        if not self.is_in_question_page(root):
            # 检查是否有"返回"、"Back"等按钮（完成页面通常有返回按钮）
            back_keywords = ["返回", "Back", "back", "Kembali", "kembali"]
            for keyword in back_keywords:
                elements = self.find_elements_by_text(root, keyword, partial=True)
                if elements:
                    print(f"  ✓ 检测到返回按钮 '{keyword}'，Part可能已完成")
                    return True
        
        return False
    
    def switch_to_next_part(self) -> bool:
        """切换到下一个Part"""
        if not self.current_part:
            # 如果当前没有Part，从Part A开始
            next_part = "A"
        else:
            # 找到当前Part在列表中的位置
            try:
                current_idx = PARTS_ORDER.index(self.current_part)
                if current_idx < len(PARTS_ORDER) - 1:
                    next_part = PARTS_ORDER[current_idx + 1]
                else:
                    print("  ✓ 所有Part已采集完成")
                    return False
            except ValueError:
                # 如果当前Part不在列表中，从Part A开始
                next_part = "A"
        
        print(f"\n🔄 切换到 Part {next_part}...")
        if self.enter_part(next_part):
            self.current_part = next_part
            # 如果这个Part还没有开始，初始化题目编号
            if next_part not in self.part_question_id:
                self.part_question_id[next_part] = 0
            self.save_progress()
            time.sleep(3)  # 等待页面加载
            return True
        return False
    
    def run(self, max_questions: Optional[int] = None, start_from_part: Optional[str] = None):
        """运行采集任务"""
        print("=" * 60)
        print("🚀 KPP题目截图采集工具")
        print("=" * 60)
        
        # 确保数据目录存在
        QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)
        OPTIONS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        
        # 确定起始Part
        if start_from_part:
            start_part = start_from_part.upper()
        elif self.current_part:
            start_part = self.current_part
        else:
            start_part = "A"  # 默认从Part A开始
        
        # 如果当前不在指定Part，先进入
        if not self.current_part or self.current_part != start_part:
            print(f"📱 进入 Part {start_part}...")
            if self.enter_part(start_part):
                self.current_part = start_part
                if start_part not in self.part_question_id:
                    self.part_question_id[start_part] = 0
                self.save_progress()
                time.sleep(3)
            else:
                print(f"❌ 无法进入 Part {start_part}")
                return
        
        count = 0
        consecutive_failures = 0  # 连续失败次数
        
        while True:
            if max_questions and count >= max_questions:
                print(f"\n✓ 已完成 {count} 道题目的采集")
                break
            
            # 检查当前Part是否完成
            ui_tree = self.adb.get_ui_tree()
            root = ET.fromstring(ui_tree)
            if self.is_part_completed(root):
                print(f"\n✓ Part {self.current_part} 采集完成")
                # 切换到下一个Part
                if not self.switch_to_next_part():
                    print("\n✓ 所有Part采集完成")
                    break
                continue
            
            # 采集题目
            if not self.capture_question():
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    print("\n⚠️  连续3次采集失败，可能Part已完成或遇到问题")
                    # 尝试切换到下一个Part
                    if not self.switch_to_next_part():
                        print("\n⚠️  采集中断")
                        break
                    consecutive_failures = 0
                else:
                    print(f"  ⚠️  采集失败 (连续失败 {consecutive_failures} 次)")
                    time.sleep(2)
            else:
                consecutive_failures = 0
                count += 1
                time.sleep(1)  # 题目之间的间隔
        
        print("\n" + "=" * 60)
        print(f"📊 采集统计:")
        for part in PARTS_ORDER:
            part_count = self.part_question_id.get(part, 0)
            if part_count > 0:
                print(f"  Part {part}: {part_count} 道题目")
        print(f"  总计: {self.total_question_id} 道题目")
        print(f"📁 题目数据保存位置: {QUESTIONS_DIR}")
        print(f"📁 图片保存位置: {OPTIONS_IMAGES_DIR}")
        print("=" * 60)

def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description="KPP题目截图采集工具")
    parser.add_argument(
        "-n", "--max-questions",
        type=int,
        help="最大采集题目数量（不指定则持续采集）"
    )
    parser.add_argument(
        "-d", "--device",
        type=str,
        help="指定设备ID（当有多个设备连接时使用）"
    )
    parser.add_argument(
        "-p", "--part",
        type=str,
        choices=["A", "B", "C"],
        help="从指定的Part开始采集（A/B/C），默认从Part A开始，会自动按A->B->C顺序采集"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="重置进度，从头开始采集"
    )
    args = parser.parse_args()
    
    # 如果指定了reset，删除进度文件
    if args.reset:
        if PROGRESS_FILE.exists():
            PROGRESS_FILE.unlink()
            print("🔄 已重置进度文件")
    
    try:
        capture = QuestionCapture(device_id=args.device)
        capture.run(max_questions=args.max_questions, start_from_part=args.part)
    except Exception as e:
        print(f"❌ 程序错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
