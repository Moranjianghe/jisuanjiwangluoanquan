import re
import os
from datetime import datetime

def parse_question_bank(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取题库基本信息
    title_match = re.search(r'(.*?)\n', content)
    title = title_match.group(1) if title_match else "题库"
    
    questions_count_match = re.search(r'题量：\s*(\d+)', content)
    questions_count = questions_count_match.group(1) if questions_count_match else "未知"
    
    total_score_match = re.search(r'满分：\s*(\d+\.\d+)', content)
    total_score = total_score_match.group(1) if total_score_match else "未知"
    
    exam_time_match = re.search(r'考试时间：(.*?)(?:\n|$)', content)
    exam_time = exam_time_match.group(1) if exam_time_match else "未知"
    
    # 將題目內容按照題號分塊
    question_blocks = re.split(r'\n\d+\.\s*\(', content)
    
    # 第一個元素是題庫信息，不是題目
    if len(question_blocks) > 0:
        question_blocks = question_blocks[1:]
    
    # 處理每個題目
    single_choice_questions = []
    multiple_choice_questions = []
    tf_questions = []
    
    for i, block in enumerate(question_blocks):
        question_number = str(i + 1)
        
        # 確定題目類型
        if '单选题' in block:
            question_type = 'single'
        elif '多选题' in block:
            question_type = 'multiple'
        elif '判断题' in block:
            question_type = 'tf'
        else:
            continue  # 跳過無法識別類型的題目
        
        # 提取題目內容
        content_match = re.search(r'.*?\)(.*?)(?:A\.|正确\n错误|$)', block, re.DOTALL)
        if content_match:
            question_content = content_match.group(1).strip()
        else:
            question_content = ""
        
        # 提取正確答案
        answer_match = re.search(r'正确答案:([A-Z]+|对|错)', block)
        if answer_match:
            correct_answer = answer_match.group(1)
        else:
            correct_answer = ""
        
        # 提取選項
        options = []
        if question_type in ['single', 'multiple']:
            # 找出所有選項
            option_matches = re.findall(r'([A-E])\.\s*(.*?)(?=\n[A-E]\.|我的答案:|$)', block, re.DOTALL)
            for opt, text in option_matches:
                options.append((opt, text.strip()))
        
        # 根據題型分類
        question = {
            'number': question_number,
            'content': question_content,
            'correct_answer': correct_answer,
            'options': options
        }
        
        if question_type == 'single':
            single_choice_questions.append(question)
        elif question_type == 'multiple':
            multiple_choice_questions.append(question)
        elif question_type == 'tf':
            tf_questions.append(question)
    
    # 將特定類型的題目按照題號排序
    # 首先，提取和轉換題號
    for questions in [single_choice_questions, multiple_choice_questions, tf_questions]:
        for q in questions:
            num_match = re.search(r'^\d+', q['number'])
            if num_match:
                q['sort_num'] = int(num_match.group(0))
            else:
                q['sort_num'] = 0
    
    # 然後排序
    single_choice_questions.sort(key=lambda q: q['sort_num'])
    multiple_choice_questions.sort(key=lambda q: q['sort_num'])
    tf_questions.sort(key=lambda q: q['sort_num'])
    
    return {
        'title': title,
        'questions_count': questions_count,
        'total_score': total_score,
        'exam_time': exam_time,
        'single_choice_questions': single_choice_questions,
        'multiple_choice_questions': multiple_choice_questions,
        'tf_questions': tf_questions
    }

def extract_question_number_from_block(block):
    """從題目塊中提取題號"""
    number_match = re.search(r'^(\d+)', block)
    return number_match.group(1) if number_match else "0"

def generate_markdown(data, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        # 写入题库基本信息
        f.write(f"# {data['title']}\n\n")
        f.write(f"- 题量：{data['questions_count']}\n")
        f.write(f"- 满分：{data['total_score']}\n")
        f.write(f"- 考试时间：{data['exam_time']}\n")
        f.write(f"- 转换时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 写入单选题
        f.write("## 一、单选题\n\n")
        for i, question in enumerate(data['single_choice_questions']):
            # 使用原始題號而不是序列號，不使用標題格式
            num = i + 1
            f.write(f"**{num}. {question['content']}**\n\n")
            
            for opt, text in question['options']:
                if opt == question['correct_answer']:
                    f.write(f"- {opt}. <font color='red'>{text}</font>\n")
                else:
                    f.write(f"- {opt}. {text}\n")
            f.write("\n")
        
        # 写入多选题
        f.write("## 二、多选题\n\n")
        for i, question in enumerate(data['multiple_choice_questions']):
            num = len(data['single_choice_questions']) + i + 1
            f.write(f"**{num}. {question['content']}**\n\n")
            
            for opt, text in question['options']:
                if opt in question['correct_answer']:
                    f.write(f"- {opt}. <font color='red'>{text}</font>\n")
                else:
                    f.write(f"- {opt}. {text}\n")
            f.write("\n")
        
        # 写入判断题
        f.write("## 三、判断题\n\n")
        for i, question in enumerate(data['tf_questions']):
            num = len(data['single_choice_questions']) + len(data['multiple_choice_questions']) + i + 1
            f.write(f"**{num}. {question['content']}**\n\n")
            
            if question['correct_answer'] == '对' or question['correct_answer'] == '對':
                f.write("- A. <font color='red'>对</font>\n")
                f.write("- B. 错\n\n")
            elif question['correct_answer'] == '错' or question['correct_answer'] == '錯':
                f.write("- A. 对\n")
                f.write("- B. <font color='red'>错</font>\n\n")
            else:
                f.write("- A. 对\n")
                f.write("- B. 错\n\n")

def main():
    input_file = "题库.txt"
    output_file = "题库.md"
    
    print(f"開始轉換 {input_file} 到 {output_file}...")
    data = parse_question_bank(input_file)
    generate_markdown(data, output_file)
    print(f"轉換完成！已生成 {output_file}")

if __name__ == "__main__":
    main()
