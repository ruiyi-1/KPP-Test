#!/usr/bin/env python3
"""
测试脚本：只抓取Section A的题目（不检测答案）
"""

import sys
from pathlib import Path
import json
from urllib.parse import urlparse

# 添加scripts目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from web_scraper import WebScraper

def main():
    print("开始抓取Section A的所有题目...")
    print("=" * 60)
    
    scraper = WebScraper(use_selenium=True)  # 启用Selenium检测答案
    
    BASE_URL = "https://kpptestmy.com"
    section_path = "section-a"
    section_url = f"{BASE_URL}/{section_path}/"
    
    # 获取所有Question Set链接
    print(f"\n正在查找Question Set链接...")
    all_links = scraper.find_question_set_links(section_url)
    
    # 只保留Section A的链接
    set_links = [link for link in all_links if '/section-a/' in link]
    
    if not set_links:
        print("未找到Question Set链接，尝试直接访问...")
        # 如果找不到链接，尝试直接访问常见的Set页面
        for set_num in range(1, 7):
            set_url = f"{BASE_URL}/{section_path}/{section_path}-question-set-{set_num}/"
            set_links.append(set_url)
        set_links.append(f"{BASE_URL}/{section_path}/road-signs-in-malaysia/")
    
    print(f"\n找到 {len(set_links)} 个Question Set:")
    for i, link in enumerate(set_links, 1):
        print(f"  {i}. {link}")
    
    all_questions = []
    questions_by_url = {}  # 按URL分组题目，便于后续统一检测答案
    
    for idx, set_url in enumerate(set_links, 1):
        print(f"\n{'='*60}")
        print(f"[{idx}/{len(set_links)}] 处理: {set_url}")
        
        try:
            # 提取set名称
            path_parts = [p for p in urlparse(set_url).path.split('/') if p]
            if path_parts:
                set_name = path_parts[-1] if path_parts[-1] else (path_parts[-2] if len(path_parts) > 1 else "set-unknown")
            else:
                set_name = "set-unknown"
            
            # 解析题目（不点击，只收集）
            questions = scraper.parse_question_set_page(set_url, "A", set_name)
            if questions:
                questions_by_url[set_url] = questions
                all_questions.extend(questions)
                print(f"✓ 收集完成，共 {len(questions)} 道题目")
            else:
                print(f"⚠ 未找到题目")
        except Exception as e:
            print(f"✗ 处理失败: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # 步骤2: 统一通过点击选项检测答案
    if scraper.use_selenium and questions_by_url:
        print(f"\n{'='*60}")
        print("步骤2: 通过点击选项检测正确答案...")
        
        for set_url, questions in questions_by_url.items():
            print(f"\n处理 {set_url}...")
            updated_questions = scraper.detect_answers_for_questions(questions, set_url)
            # 更新all_questions中的答案
            for i, q in enumerate(all_questions):
                for uq in updated_questions:
                    if q['id'] == uq['id']:
                        q['correctAnswer'] = uq.get('correctAnswer')
                        break
            detected_count = sum(1 for q in updated_questions if q.get('correctAnswer'))
            print(f"完成，检测到答案的题目: {detected_count}/{len(updated_questions)}")
    
    # 关闭Selenium driver
    if scraper.driver:
        try:
            scraper.driver.quit()
        except:
            pass
    
    # 清理临时数据
    for q in all_questions:
        if "_temp_data" in q:
            del q["_temp_data"]
    
    # 保存结果
    output_file = Path(__file__).parent.parent / "web" / "src" / "data" / "questions_section_a.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if all_questions:
        output_data = {
            "total": len(all_questions),
            "questions": all_questions
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"完成！共抓取 {len(all_questions)} 道题目")
        print(f"数据已保存到: {output_file}")
        
        # 统计信息
        with_answer = sum(1 for q in all_questions if q.get('correctAnswer'))
        without_answer = len(all_questions) - with_answer
        print(f"  有答案: {with_answer} 道")
        print(f"  无答案: {without_answer} 道")
        
        # 显示前几道题目作为示例
        print(f"\n前5道题目示例:")
        for i, q in enumerate(all_questions[:5], 1):
            answer = q.get('correctAnswer', '未找到')
            print(f"  {i}. {q['id']}")
            print(f"     题目: {q['question'][:70]}...")
            print(f"     选项数: {len(q['options'])}, 答案: {answer}")
            print()
    else:
        print("\n未找到任何题目")

if __name__ == "__main__":
    main()
