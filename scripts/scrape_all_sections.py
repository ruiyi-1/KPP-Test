#!/usr/bin/env python3
"""
完整抓取脚本：抓取所有Section的题目并检测答案
"""

import sys
from pathlib import Path
import json
from urllib.parse import urlparse

# 添加scripts目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from web_scraper import WebScraper

def main():
    print("=" * 60)
    print("开始抓取所有Section的题目...")
    print("=" * 60)
    
    scraper = WebScraper(use_selenium=True)  # 启用Selenium检测答案
    
    BASE_URL = "https://kpptestmy.com"
    SECTIONS = {
        "A": "section-a",
        "B": "section-b",
        "C": "section-c"
    }
    
    all_questions = []
    all_questions_by_section = {}
    
    for section, section_path in SECTIONS.items():
        print(f"\n{'='*60}")
        print(f"处理 Section {section}...")
        print(f"{'='*60}")
        
        section_url = f"{BASE_URL}/{section_path}/"
        
        # 获取所有Question Set链接
        print(f"\n正在查找Question Set链接...")
        all_links = scraper.find_question_set_links(section_url)
        
        # 只保留当前Section的链接
        set_links = [link for link in all_links if f'/{section_path}/' in link]
        
        if not set_links:
            print(f"未找到Question Set链接，尝试直接访问...")
            # 根据Section生成常见的Set页面
            if section == "A":
                for set_num in range(1, 7):
                    set_links.append(f"{BASE_URL}/{section_path}/{section_path}-question-set-{set_num}/")
                set_links.append(f"{BASE_URL}/{section_path}/road-signs-in-malaysia/")
            elif section == "B":
                for set_num in range(1, 10):
                    set_links.append(f"{BASE_URL}/{section_path}/{section_path}-question-set-{set_num}/")
            elif section == "C":
                for set_num in range(1, 5):
                    set_links.append(f"{BASE_URL}/{section_path}/{section_path}-question-set-{set_num}/")
                set_links.append(f"{BASE_URL}/{section_path}/kejara-system/")
        
        print(f"\n找到 {len(set_links)} 个Question Set:")
        for i, link in enumerate(set_links, 1):
            print(f"  {i}. {link}")
        
        section_questions = []
        questions_by_url = {}
        
        # 步骤1: 收集所有题目（不点击）
        print(f"\n步骤1: 收集Section {section}的所有题目...")
        for idx, set_url in enumerate(set_links, 1):
            print(f"\n[{idx}/{len(set_links)}] 处理: {set_url}")
            
            try:
                # 提取set名称
                path_parts = [p for p in urlparse(set_url).path.split('/') if p]
                if path_parts:
                    set_name = path_parts[-1] if path_parts[-1] else (path_parts[-2] if len(path_parts) > 1 else "set-unknown")
                else:
                    set_name = "set-unknown"
                
                # 解析题目（不点击，只收集）
                questions = scraper.parse_question_set_page(set_url, section, set_name)
                if questions:
                    questions_by_url[set_url] = questions
                    section_questions.extend(questions)
                    print(f"✓ 收集完成，共 {len(questions)} 道题目")
                else:
                    print(f"⚠ 未找到题目")
            except Exception as e:
                print(f"✗ 处理失败: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\nSection {section} 步骤1完成：共收集 {len(section_questions)} 道题目")
        
        # 步骤2: 统一通过点击选项检测答案
        if scraper.use_selenium and questions_by_url:
            print(f"\n步骤2: 通过点击选项检测Section {section}的正确答案...")
            
            for set_url, questions in questions_by_url.items():
                print(f"\n处理 {set_url}...")
                updated_questions = scraper.detect_answers_for_questions(questions, set_url)
                # 更新section_questions中的答案
                for sq in section_questions:
                    for uq in updated_questions:
                        if sq['id'] == uq['id']:
                            sq['correctAnswer'] = uq.get('correctAnswer')
                            break
                detected_count = sum(1 for q in updated_questions if q.get('correctAnswer'))
                print(f"完成，检测到答案的题目: {detected_count}/{len(updated_questions)}")
        
        all_questions.extend(section_questions)
        all_questions_by_section[section] = section_questions
        
        # 清理临时数据
        for q in section_questions:
            if "_temp_data" in q:
                del q["_temp_data"]
        
        print(f"\nSection {section} 完成！共 {len(section_questions)} 道题目")
        with_answer = sum(1 for q in section_questions if q.get('correctAnswer'))
        print(f"  有答案: {with_answer} 道")
        print(f"  无答案: {len(section_questions) - with_answer} 道")
    
    # 关闭Selenium driver
    if scraper.driver:
        try:
            scraper.driver.quit()
        except:
            pass
    
    # 保存所有题目到统一文件
    output_file = Path(__file__).parent.parent / "web" / "src" / "data" / "questions.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if all_questions:
        output_data = {
            "total": len(all_questions),
            "questions": all_questions
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"全部完成！共抓取 {len(all_questions)} 道题目")
        print(f"数据已保存到: {output_file}")
        
        # 统计信息
        with_answer = sum(1 for q in all_questions if q.get('correctAnswer'))
        without_answer = len(all_questions) - with_answer
        print(f"  有答案: {with_answer} 道 ({with_answer/len(all_questions)*100:.1f}%)")
        print(f"  无答案: {without_answer} 道")
        
        # 各Section统计
        print(f"\n各Section统计:")
        for section, questions in all_questions_by_section.items():
            section_with_answer = sum(1 for q in questions if q.get('correctAnswer'))
            print(f"  Section {section}: {len(questions)} 道 (有答案: {section_with_answer} 道)")
        
        # 显示前几道题目作为示例
        print(f"\n前3道题目示例:")
        for i, q in enumerate(all_questions[:3], 1):
            answer = q.get('correctAnswer', '未找到')
            print(f"  {i}. {q['id']}: {q['question'][:60]}... (答案: {answer})")
    else:
        print("\n未找到任何题目")

if __name__ == "__main__":
    main()
