#!/usr/bin/env python3
"""
KPP网页题库抓取脚本
功能：从kpptestmy.com网站抓取所有题目数据
"""

import json
import re
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from PIL import Image
import io

# Selenium相关导入
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("警告: Selenium未安装，将无法通过点击选项获取正确答案")

# 配置
BASE_URL = "https://kpptestmy.com"
SECTIONS = {
    "A": "section-a",
    "B": "section-b",
    "C": "section-c"
}

DATA_DIR = Path(__file__).parent.parent / "data"
WEB_DATA_DIR = Path(__file__).parent.parent / "web" / "src" / "data"
# 图片需要被 Vite dev server / GitHub Pages 提供访问，因此必须放到 web/public 下
WEB_PUBLIC_DIR = Path(__file__).parent.parent / "web" / "public"
IMAGES_DIR = WEB_PUBLIC_DIR / "images"
QUESTIONS_IMAGES_DIR = IMAGES_DIR / "questions"
OPTIONS_IMAGES_DIR = IMAGES_DIR / "options"
PROGRESS_FILE = DATA_DIR / "scraper_progress.json"
OUTPUT_FILE = WEB_DATA_DIR / "questions.json"

# 创建目录
QUESTIONS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
OPTIONS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)
WEB_PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

# 请求头（无图模式）
# 注意：不设置Accept-Encoding，让requests自动处理压缩
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

class WebScraper:
    def __init__(self, use_selenium: bool = True):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.questions = []
        self.progress = self.load_progress()
        self.use_selenium = use_selenium and SELENIUM_AVAILABLE
        self.driver = None
        
    def load_progress(self) -> Dict:
        """加载进度"""
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "completed_sets": [],
            "last_question_id": None
        }
    
    def save_progress(self):
        """保存进度"""
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, indent=2, ensure_ascii=False)
    
    def fetch_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """获取页面内容"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # 确保正确解码
                response.encoding = response.apparent_encoding or 'utf-8'
                
                # 添加延迟避免被封
                time.sleep(1)
                
                # 使用html.parser（更兼容）
                soup = BeautifulSoup(response.text, 'html.parser')
                return soup
            except Exception as e:
                print(f"  错误: {e}, 重试 {attempt + 1}/{retries}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
        return None
    
    def find_question_set_links(self, section_url: str) -> List[str]:
        """从section页面找到所有Question Set链接"""
        print(f"正在解析 {section_url}...")
        soup = self.fetch_page(section_url)
        if not soup:
            return []
        
        links = []
        # 查找所有链接，筛选出Question Set链接
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # 匹配Question Set链接模式
            href_lower = href.lower()
            if any(keyword in href_lower for keyword in ['question-set', 'road-signs', 'kejara']):
                full_url = urljoin(BASE_URL, href)
                if full_url not in links:
                    links.append(full_url)
                    print(f"  找到: {text} -> {full_url}")
        
        # 如果没找到链接，尝试根据section生成常见的链接
        if not links:
            section_path = section_url.rstrip('/').split('/')[-1]
            # Section A: Set 1-6 + Road Signs
            if 'section-a' in section_path:
                for i in range(1, 7):
                    links.append(f"{BASE_URL}/section-a/section-a-question-set-{i}/")
                links.append(f"{BASE_URL}/section-a/road-signs/")
            # Section B: Set 1-9 (可能还有10)
            elif 'section-b' in section_path:
                for i in range(1, 11):
                    links.append(f"{BASE_URL}/section-b/section-b-question-set-{i}/")
            # Section C: Set 1-4 + KEJARA
            elif 'section-c' in section_path:
                for i in range(1, 5):
                    links.append(f"{BASE_URL}/section-c/section-c-question-set-{i}/")
                links.append(f"{BASE_URL}/section-c/kejara-system/")
        
        return links
    
    def download_image(self, img_url: str, save_dir: Path, filename: str) -> Optional[str]:
        """下载图片到本地"""
        try:
            # 如果是相对路径，转换为绝对路径
            if not img_url.startswith('http'):
                img_url = urljoin(BASE_URL, img_url)
            
            # 单独为图片请求设置 Accept/Referer，避免拿到 HTML 占位页导致 PIL 解析失败
            img_headers = {
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Referer": f"{BASE_URL}/",
            }
            response = self.session.get(img_url, timeout=30, headers=img_headers)
            response.raise_for_status()
            
            # 验证是否为图片
            img = Image.open(io.BytesIO(response.content))
            img_format = img.format.lower() if img.format else 'png'
            
            # 确保文件名有正确的扩展名
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                filename = f"{filename}.{img_format}"
            
            save_path = save_dir / filename
            img.save(save_path, format=img_format)
            
            # 返回相对路径（从 web/public 作为静态根目录）
            # 运行时会以 Vite base（例如 /KPP/）作为前缀
            relative_path = f"images/{save_dir.name}/{filename}"
            return relative_path
        except Exception as e:
            print(f"    下载图片失败 {img_url}: {e}")
            return None
    
    def extract_question_text(self, question_element) -> str:
        """提取题目文本"""
        # 查找wpvq-question-label
        question_label = question_element.find('div', class_='wpvq-question-label')
        if question_label:
            text = question_label.get_text(strip=True)
        else:
            # 如果没有找到，尝试从整个元素中提取（排除选项部分）
            full_text = question_element.get_text(separator=' ', strip=True)
            # 移除选项和答案反馈
            lines = full_text.split('\n')
            question_lines = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # 如果遇到选项内容（通常在wpvq-answer中），停止
                if any(keyword in line.lower() for keyword in ['correct!', 'wrong!', 'years respectively']):
                    break
                question_lines.append(line)
            text = ' '.join(question_lines)
        
        # 清理文本
        text = re.sub(r'\s+', ' ', text).strip()
        # 移除可能的编号（如 "1. "）
        text = re.sub(r'^\d+[\.\)]\s*', '', text).strip()
        return text
    
    def extract_options(self, question_element, question_id: str = None) -> List[Dict]:
        """提取选项"""
        options = []
        
        # 使用更精确的时间戳（包含微秒）或题目ID
        if question_id:
            # 使用题目ID生成唯一文件名
            base_name = question_id.replace('/', '_').replace('\\', '_')
        else:
            # 使用微秒级时间戳
            import time
            base_name = f"option_{int(time.time() * 1000000)}"
        
        # 查找所有wpvq-answer div
        answer_divs = question_element.find_all('div', class_='wpvq-answer')
        
        # 按顺序提取选项（A, B, C, D...）
        for idx, answer_div in enumerate(answer_divs):
            label = chr(65 + idx)  # A, B, C, D
            
            # 查找label元素
            label_elem = answer_div.find('label', class_='vq-css-label')
            if label_elem:
                text = label_elem.get_text(strip=True)
            else:
                # 如果没有label，获取整个div的文本
                text = answer_div.get_text(strip=True)
            
            # 检查是否有图片
            img = answer_div.find('img')
            image_path = None
            if img:
                img_url = img.get('src') or img.get('data-src')
                if img_url:
                    filename = f"{base_name}_opt_{label.lower()}_{idx}.png"
                    image_path = self.download_image(img_url, OPTIONS_IMAGES_DIR, filename)
            
            option = {
                "type": "image" if image_path else "text",
                "label": label,
                "content": text if text else label
            }
            if image_path:
                option["imagePath"] = image_path
            
            options.append(option)
        
        return options
    
    def init_selenium_driver(self):
        """初始化Selenium WebDriver"""
        if not self.use_selenium:
            return False
        
        if self.driver:
            return True
        
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无头模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument(f'user-agent={HEADERS["User-Agent"]}')
            
            # 尝试使用系统Chrome
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
            except:
                # 如果失败，尝试使用webdriver-manager
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                except:
                    print("  警告: 无法初始化Chrome WebDriver，将跳过点击检测答案功能")
                    self.use_selenium = False
                    return False
            
            return True
        except Exception as e:
            print(f"  警告: 初始化Selenium失败: {e}")
            self.use_selenium = False
            return False
    
    def find_correct_answer_by_clicking(self, url: str, question_id: str, option_labels: List[str]) -> Optional[str]:
        """通过点击选项来查找正确答案"""
        if not self.use_selenium:
            return None
        
        if not self.init_selenium_driver():
            return None
        
        try:
            # 打开页面
            self.driver.get(url)
            time.sleep(2)  # 等待页面加载
            
            # 等待题目元素加载
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "wpvq-question"))
                )
            except TimeoutException:
                print(f"    超时: 无法加载题目元素")
                return None
            
            # 找到对应的题目（通过question_id或题目位置）
            question_divs = self.driver.find_elements(By.CLASS_NAME, "wpvq-question")
            target_question = None
            
            # 尝试通过data-questionid找到题目
            for q_div in question_divs:
                q_id = q_div.get_attribute("data-questionid")
                if q_id == question_id:
                    target_question = q_div
                    break
            
            # 如果没找到，使用第一个题目（假设按顺序）
            if not target_question and question_divs:
                # 这里需要根据实际情况调整，可能需要通过题目文本匹配
                target_question = question_divs[0]
            
            if not target_question:
                return None
            
            # 找到所有选项
            answer_divs = target_question.find_elements(By.CLASS_NAME, "wpvq-answer")
            
            # 依次点击每个选项，检查哪个变成绿色
            for idx, answer_div in enumerate(answer_divs):
                if idx >= len(option_labels):
                    break
                
                try:
                    # 点击选项（点击label或input）
                    label_elem = answer_div.find_element(By.CLASS_NAME, "vq-css-label")
                    if label_elem:
                        label_elem.click()
                    else:
                        # 如果没有label，点击input
                        input_elem = answer_div.find_element(By.CSS_SELECTOR, "input[type='radio']")
                        if input_elem:
                            input_elem.click()
                    
                    # 等待答案反馈显示
                    time.sleep(0.5)
                    
                    # 检查所有选项的背景颜色或CSS类
                    for check_idx, check_div in enumerate(answer_divs):
                        # 检查是否有绿色背景的类或样式
                        classes = check_div.get_attribute("class") or ""
                        style = check_div.get_attribute("style") or ""
                        
                        # 检查绿色背景（可能通过CSS类或内联样式）
                        if "correct" in classes.lower() or "true" in classes.lower():
                            # 找到正确答案
                            if check_idx < len(option_labels):
                                return option_labels[check_idx]
                        
                        # 检查内联样式中的绿色背景
                        if "background" in style.lower() and ("green" in style.lower() or "rgb(82, 196, 26)" in style.lower() or "#52c41a" in style.lower()):
                            if check_idx < len(option_labels):
                                return option_labels[check_idx]
                        
                        # 检查label的样式
                        try:
                            check_label = check_div.find_element(By.CLASS_NAME, "vq-css-label")
                            check_label_classes = check_label.get_attribute("class") or ""
                            check_label_style = check_label.get_attribute("style") or ""
                            
                            if "correct" in check_label_classes.lower() or "true" in check_label_classes.lower():
                                if check_idx < len(option_labels):
                                    return option_labels[check_idx]
                            
                            if "background" in check_label_style.lower() and ("green" in check_label_style.lower() or "#52c41a" in check_label_style.lower() or "rgb(82, 196, 26)" in check_label_style.lower()):
                                if check_idx < len(option_labels):
                                    return option_labels[check_idx]
                        except:
                            pass
                
                except Exception as e:
                    continue
            
            return None
            
        except Exception as e:
            print(f"    错误: 点击检测答案时出错: {e}")
            return None
    
    def find_correct_answer(self, question_element, url: str = None, question_id: str = None) -> Optional[str]:
        """查找正确答案"""
        # 如果提供了URL和question_id，尝试通过点击选项来检测
        if url and question_id and self.use_selenium:
            # 先提取选项标签
            answer_divs = question_element.find_all('div', class_='wpvq-answer')
            option_labels = []
            for idx, answer_div in enumerate(answer_divs):
                option_labels.append(chr(65 + idx))  # A, B, C, D...
            
            if option_labels:
                correct_answer = self.find_correct_answer_by_clicking(url, question_id, option_labels)
                if correct_answer:
                    return correct_answer
        
        # 回退到原来的方法（如果点击检测失败）
        explaination = question_element.find('div', class_='wpvq-explaination')
        if not explaination:
            return None
        
        answer_divs = question_element.find_all('div', class_='wpvq-answer')
        if not answer_divs:
            return None
        
        # 由于HTML中没有直接标识正确答案，返回None
        return None
    
    def extract_question_images(self, question_element, question_id: str = None) -> List[str]:
        """提取题目图片"""
        images = []
        img_elements = question_element.find_all('img')
        
        # 使用更精确的时间戳（包含微秒）或题目ID
        if question_id:
            # 使用题目ID生成唯一文件名
            base_name = question_id.replace('/', '_').replace('\\', '_')
        else:
            # 使用微秒级时间戳
            import time
            base_name = f"question_{int(time.time() * 1000000)}"
        
        for idx, img in enumerate(img_elements):
            img_url = img.get('src') or img.get('data-src')
            if img_url:
                # 检查是否在选项区域（如果是选项图片，跳过）
                parent = img.find_parent()
                is_option_image = False
                while parent:
                    if parent.name in ['li', 'ul', 'ol'] or 'option' in str(parent.get('class', [])).lower():
                        is_option_image = True
                        break
                    parent = parent.find_parent()
                
                if not is_option_image:
                    filename = f"{base_name}_img_{idx}.png"
                    image_path = self.download_image(img_url, QUESTIONS_IMAGES_DIR, filename)
                    if image_path:
                        images.append(image_path)
        
        return images
    
    def is_ad_element(self, element) -> bool:
        """判断元素是否是广告元素"""
        if not element:
            return False
        
        # 检查元素本身及其父元素的ID和类名
        element_ids = []
        element_classes = []
        parent = element
        
        # 检查元素本身和向上3层父元素
        for _ in range(4):
            if not parent:
                break
            
            elem_id = parent.get('id', '') if hasattr(parent, 'get') else ''
            elem_class = ' '.join(parent.get('class', [])) if hasattr(parent, 'get') and parent.get('class') else ''
            
            if elem_id:
                element_ids.append(elem_id.lower())
            if elem_class:
                element_classes.append(elem_class.lower())
            
            parent = parent.find_parent() if hasattr(parent, 'find_parent') else None
        
        # 广告相关的ID关键词
        ad_id_keywords = [
            'privacy_icon', 'close_button', 'survey_page', 'cto_banner', 
            'bnr', 'beacon_', 'ad_', 'banner', 'criteo', 'duplo'
        ]
        
        # 广告相关的类名关键词
        ad_class_keywords = [
            'privacy', 'ad_', 'banner', 'criteo', 'survey', 'cto_',
            'duplo', 'adchoices', 'advertisement'
        ]
        
        # 检查ID
        for ad_id in ad_id_keywords:
            if any(ad_id in elem_id for elem_id in element_ids):
                return True
        
        # 检查类名
        for ad_class in ad_class_keywords:
            if any(ad_class in elem_class for elem_class in element_classes):
                return True
        
        # 检查是否包含广告相关的链接
        if hasattr(element, 'find_all'):
            ad_links = element.find_all('a', href=lambda x: x and any(
                keyword in x.lower() for keyword in ['criteo', 'adchoices', 'doubleclick', 'adclick']
            ))
            if ad_links:
                return True
        
        return False
    
    def parse_question_set_page(self, url: str, section: str, set_name: str) -> List[Dict]:
        """解析Question Set页面，提取所有题目"""
        print(f"  正在解析 {url}...")
        soup = self.fetch_page(url)
        if not soup:
            print(f"  无法访问 {url}")
            return []
        
        questions = []
        
        # 先移除所有广告元素
        ad_elements = soup.find_all(id=lambda x: x and any(
            keyword in x.lower() for keyword in ['privacy_icon', 'close_button', 'survey_page', 'cto_banner', 'bnr', 'beacon_']
        ))
        for ad_elem in ad_elements:
            ad_elem.decompose()  # 完全移除元素
        
        # 移除包含广告相关类名的元素
        ad_elements_by_class = soup.find_all(class_=lambda x: x and any(
            keyword in ' '.join(x).lower() for keyword in ['privacy', 'ad_', 'banner', 'criteo', 'survey', 'cto_']
        ))
        for ad_elem in ad_elements_by_class:
            # 只移除明显的广告容器，保留可能包含题目的元素
            elem_id = ad_elem.get('id', '') if hasattr(ad_elem, 'get') else ''
            if any(keyword in elem_id.lower() for keyword in ['privacy', 'ad', 'banner', 'survey', 'cto']):
                ad_elem.decompose()
        
        # 查找所有题目元素 - 使用wpvq-question class
        # 直接查找class包含'wpvq-question'的div
        all_question_divs = soup.find_all('div', class_=lambda x: x and 'wpvq-question' in x if x else False)
        
        # 去重：通过data-questionid或题目文本内容去重，同时过滤广告元素
        seen_questions = set()
        unique_question_divs = []
        for div in all_question_divs:
            # 过滤广告元素
            if self.is_ad_element(div):
                continue
            
            # 使用data-questionid作为唯一标识
            question_id = div.get('data-questionid')
            if question_id:
                if question_id not in seen_questions:
                    seen_questions.add(question_id)
                    unique_question_divs.append(div)
            else:
                # 如果没有questionid，使用题目文本的前50个字符作为标识
                question_label = div.find('div', class_='wpvq-question-label')
                if question_label:
                    text_hash = question_label.get_text(strip=True)[:50]
                    if text_hash not in seen_questions:
                        seen_questions.add(text_hash)
                        unique_question_divs.append(div)
                else:
                    # 如果都没有，检查是否是广告后再添加
                    if not self.is_ad_element(div):
                        unique_question_divs.append(div)
        
        question_divs = unique_question_divs
        
        # 如果还是没找到，尝试查找包含选项的元素
        if not question_divs:
            # 查找包含A/B/C/D选项的元素
            for label in ['A', 'B', 'C', 'D']:
                label_nodes = soup.find_all(string=re.compile(rf'^{label}[\.\)]', re.I))
                for node in label_nodes:
                    parent = node.find_parent()
                    # 向上查找包含题目的容器
                    while parent:
                        if parent.name == 'div' and 'wpvq' in str(parent.get('class', [])):
                            if parent not in question_divs:
                                question_divs.append(parent)
                            break
                        parent = parent.find_parent()
        
        print(f"    找到 {len(question_divs)} 个题目元素（去重后）")
        
        # 过滤有效的题目（必须有题目文本和至少2个选项）
        valid_questions = []
        for question_elem in question_divs:
            # 提取题目文本
            question_text = self.extract_question_text(question_elem)
            if not question_text or len(question_text) < 10:  # 太短的文本可能不是题目
                continue
            
            # 提取选项（先不传question_id，因为还没生成）
            options = self.extract_options(question_elem)
            if len(options) < 2:  # 至少需要2个选项
                continue
            
            valid_questions.append((question_elem, question_text, options))
        
        # 处理有效题目
        for idx, (question_elem, question_text, options) in enumerate(valid_questions):
            # 先生成题目ID（用于图片命名）
            set_slug = set_name.lower().replace(' ', '-').replace('_', '-').replace('section-', '')
            question_id = f"section-{section.lower()}-{set_slug}-q{idx + 1}"
            
            # 提取题目图片（传入question_id用于生成唯一文件名）
            question_images = self.extract_question_images(question_elem, question_id=question_id)
            
            # 重新提取选项（传入question_id用于生成唯一文件名）
            options = self.extract_options(question_elem, question_id=question_id)
            
            # 判断题目类型
            has_image_options = any(opt.get('type') == 'image' for opt in options)
            question_type = 'image-options' if has_image_options else 'text'
            
            # 获取data-questionid（用于Selenium定位）
            data_question_id = question_elem.get('data-questionid') if hasattr(question_elem, 'get') else None
            
            # 提取正确答案（先不点击，后续统一处理）
            correct_answer = None
            
            question = {
                "id": question_id,
                "question": question_text,
                "questionType": question_type,
                "options": options,
                "correctAnswer": correct_answer,
                "questionImages": question_images,
                "_temp_data": {  # 临时数据，用于后续点击检测
                    "url": url,
                    "data_question_id": data_question_id,
                    "question_element_index": idx
                }
            }
            
            questions.append(question)
            print(f"    题目 {idx + 1}: {question_text[:50]}... (答案: 待检测)")
        
        return questions
    
    def detect_answers_for_questions(self, questions: List[Dict], set_url: str) -> List[Dict]:
        """为题目检测正确答案（通过点击选项）"""
        if not self.use_selenium or not questions:
            return questions
        
        print(f"  开始通过点击选项检测答案（共 {len(questions)} 道题目）...")
        
        if not self.init_selenium_driver():
            print("  无法初始化Selenium，跳过答案检测")
            return questions
        
        try:
            # 打开页面
            self.driver.get(set_url)
            time.sleep(3)  # 等待页面完全加载
            
            # 等待题目元素加载
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "wpvq-question"))
                )
            except TimeoutException:
                print("  超时: 无法加载题目元素")
                return questions
            
            # 获取所有题目元素
            question_divs = self.driver.find_elements(By.CLASS_NAME, "wpvq-question")
            
            # 为每道题目检测答案
            for q_idx, question in enumerate(questions):
                if q_idx >= len(question_divs):
                    break
                
                temp_data = question.get("_temp_data", {})
                data_question_id = temp_data.get("data_question_id")
                
                # 找到对应的题目div
                target_question_div = None
                if data_question_id:
                    for q_div in question_divs:
                        if q_div.get_attribute("data-questionid") == str(data_question_id):
                            target_question_div = q_div
                            break
                
                # 如果没找到，使用索引
                if not target_question_div and q_idx < len(question_divs):
                    target_question_div = question_divs[q_idx]
                
                if not target_question_div:
                    continue
                
                # 获取选项标签
                option_labels = [opt["label"] for opt in question["options"]]
                
                # 找到所有选项
                answer_divs = target_question_div.find_elements(By.CLASS_NAME, "wpvq-answer")
                
                # 依次点击每个选项，检查哪个变成绿色
                correct_answer = None
                for opt_idx, answer_div in enumerate(answer_divs):
                    if opt_idx >= len(option_labels):
                        break
                    
                    try:
                        # 点击选项（先点击input，再点击label确保触发）
                        try:
                            input_elem = answer_div.find_element(By.CSS_SELECTOR, "input[type='radio']")
                            # 使用JavaScript点击，更可靠
                            self.driver.execute_script("arguments[0].click();", input_elem)
                        except:
                            try:
                                label_elem = answer_div.find_element(By.CLASS_NAME, "vq-css-label")
                                self.driver.execute_script("arguments[0].click();", label_elem)
                            except:
                                answer_div.click()
                        
                        # 等待答案反馈显示（等待JavaScript执行）
                        time.sleep(1.5)  # 增加等待时间
                        
                        # 等待可能的动画完成
                        try:
                            WebDriverWait(self.driver, 2).until(
                                lambda d: d.execute_script("return document.readyState") == "complete"
                            )
                        except:
                            pass
                        
                        # 检查所有选项，看哪个是绿色（正确答案）
                        for check_idx, check_div in enumerate(answer_divs):
                            if check_idx >= len(option_labels):
                                break
                            
                            try:
                                # 检查div的类名和样式
                                classes = check_div.get_attribute("class") or ""
                                style = check_div.get_attribute("style") or ""
                                
                                # 检查label的类名和样式
                                check_label = check_div.find_element(By.CLASS_NAME, "vq-css-label")
                                label_classes = check_label.get_attribute("class") or ""
                                label_style = check_label.get_attribute("style") or ""
                                
                                # 检查是否有绿色背景（通过CSS类或内联样式）
                                is_green = False
                                
                                # 方法1: 检查CSS类
                                if any(keyword in classes.lower() or keyword in label_classes.lower() 
                                       for keyword in ["correct", "true", "success", "green", "wpvq-true"]):
                                    is_green = True
                                
                                # 方法2: 检查内联样式中的绿色
                                all_style = (style + " " + label_style).lower()
                                if any(color in all_style for color in [
                                    "rgb(82, 196, 26)", "#52c41a", "green", 
                                    "rgb(76, 175, 80)", "#4caf50", "background-color: green",
                                    "rgb(183, 223, 170)", "rgb(246, 255, 237)"  # 浅绿色背景
                                ]):
                                    is_green = True
                                
                                # 方法3: 检查计算样式（使用JavaScript）
                                try:
                                    # 检查背景色
                                    bg_color = self.driver.execute_script(
                                        "return window.getComputedStyle(arguments[0]).backgroundColor;",
                                        check_label
                                    )
                                    # 检查父元素的背景色
                                    parent_bg = self.driver.execute_script(
                                        "return window.getComputedStyle(arguments[0].parentElement).backgroundColor;",
                                        check_label
                                    )
                                    
                                    # 检查是否是绿色系
                                    green_colors = [
                                        "rgb(82, 196, 26)", "rgb(76, 175, 80)", "rgb(183, 223, 170)",
                                        "rgb(246, 255, 237)", "rgb(129, 199, 132)", "rgb(102, 187, 106)"
                                    ]
                                    if bg_color and any(green in bg_color.lower() for green in green_colors):
                                        is_green = True
                                    if parent_bg and any(green in parent_bg.lower() for green in green_colors):
                                        is_green = True
                                    
                                    # 检查边框颜色（绿色边框也可能表示正确答案）
                                    border_color = self.driver.execute_script(
                                        "return window.getComputedStyle(arguments[0]).borderColor;",
                                        check_label
                                    )
                                    if border_color and any(green in border_color.lower() for green in [
                                        "rgb(82, 196, 26)", "rgb(76, 175, 80)", "#52c41a"
                                    ]):
                                        is_green = True
                                    
                                except Exception as e:
                                    pass
                                
                                # 方法4: 检查input的checked状态和对应的反馈
                                try:
                                    check_input = check_div.find_element(By.CSS_SELECTOR, "input[type='radio']")
                                    is_checked = check_input.is_selected()
                                    
                                    # 如果选项被选中，检查是否有对应的正确反馈
                                    if is_checked:
                                        # 查找explaination区域
                                        explaination = target_question_div.find_element(By.CLASS_NAME, "wpvq-explaination")
                                        true_div = explaination.find_element(By.CLASS_NAME, "wpvq-true")
                                        
                                        # 检查wpvq-true是否可见
                                        if true_div and true_div.is_displayed():
                                            # 获取wpvq-true的样式
                                            true_style = self.driver.execute_script(
                                                "return window.getComputedStyle(arguments[0]).display;",
                                                true_div
                                            )
                                            if true_style and true_style != "none":
                                                # 如果wpvq-true显示，且当前选项被选中，可能是正确答案
                                                # 但需要确认是当前选项触发的
                                                answer_id = check_input.get_attribute("data-wpvq-answer")
                                                # 检查explaination中是否有对应的答案ID
                                                explaination_html = explaination.get_attribute("innerHTML")
                                                if answer_id and answer_id in explaination_html:
                                                    is_green = True
                                except:
                                    pass
                                
                                if is_green:
                                    correct_answer = option_labels[check_idx]
                                    break
                            
                            except Exception as e:
                                continue
                        
                        if correct_answer:
                            break
                    
                    except Exception as e:
                        continue
                
                # 更新正确答案
                if correct_answer:
                    question["correctAnswer"] = correct_answer
                    print(f"    题目 {q_idx + 1}: 答案 = {correct_answer}")
                else:
                    print(f"    题目 {q_idx + 1}: 未找到答案")
                
                # 移除临时数据
                if "_temp_data" in question:
                    del question["_temp_data"]
        
        except Exception as e:
            print(f"  错误: 检测答案时出错: {e}")
        
        return questions
    
    def scrape_all(self):
        """抓取所有题目"""
        print("开始抓取KPP题库...")
        print("步骤1: 收集所有题目（不点击）...")
        
        all_questions = []
        questions_by_url = {}  # 按URL分组题目，便于后续统一检测答案
        
        for section, section_path in SECTIONS.items():
            print(f"\n处理 Section {section}...")
            section_url = f"{BASE_URL}/{section_path}/"
            
            # 获取所有Question Set链接
            set_links = self.find_question_set_links(section_url)
            
            if not set_links:
                print(f"  未找到Question Set链接，尝试直接访问...")
                # 如果找不到链接，尝试直接访问常见的Set页面
                for set_num in range(1, 10):
                    set_url = f"{BASE_URL}/{section_path}/{section_path}-question-set-{set_num}/"
                    set_links.append(set_url)
            
            for set_url in set_links:
                # 检查是否已完成
                if set_url in self.progress.get("completed_sets", []):
                    print(f"  跳过已完成的: {set_url}")
                    continue
                
                try:
                    # 提取set名称
                    path_parts = [p for p in urlparse(set_url).path.split('/') if p]
                    if path_parts:
                        set_name = path_parts[-1] if path_parts[-1] else (path_parts[-2] if len(path_parts) > 1 else f"set-{len(set_links)}")
                    else:
                        set_name = f"set-{len(set_links)}"
                    
                    # 解析题目（不点击，只收集）
                    questions = self.parse_question_set_page(set_url, section, set_name)
                    if questions:
                        # 保存到分组中
                        questions_by_url[set_url] = questions
                        all_questions.extend(questions)
                        print(f"  ✓ 收集完成 {set_url}, 共 {len(questions)} 道题目")
                    else:
                        print(f"  ⚠ 未找到题目: {set_url}")
                except Exception as e:
                    print(f"  ✗ 处理失败 {set_url}: {e}")
                    continue
        
        # 步骤2: 统一通过点击选项检测答案
        if self.use_selenium and questions_by_url:
            print(f"\n步骤2: 通过点击选项检测正确答案...")
            for set_url, questions in questions_by_url.items():
                print(f"\n  处理 {set_url}...")
                questions = self.detect_answers_for_questions(questions, set_url)
                # 更新进度
                if set_url not in self.progress.get("completed_sets", []):
                    self.progress["completed_sets"].append(set_url)
                self.save_progress()
        
        # 关闭Selenium driver
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        # 保存所有题目
        if all_questions:
            # 清理临时数据
            for q in all_questions:
                if "_temp_data" in q:
                    del q["_temp_data"]
            
            output_data = {
                "total": len(all_questions),
                "questions": all_questions
            }
            
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n完成！共抓取 {len(all_questions)} 道题目")
            print(f"数据已保存到: {OUTPUT_FILE}")
            
            # 统计信息
            with_answer = sum(1 for q in all_questions if q.get('correctAnswer'))
            without_answer = len(all_questions) - with_answer
            print(f"  有答案: {with_answer} 道")
            print(f"  无答案: {without_answer} 道")
        else:
            print("\n未找到任何题目，请检查网络连接和页面结构")
        
        return all_questions

def main():
    scraper = WebScraper()
    scraper.scrape_all()

if __name__ == "__main__":
    main()
