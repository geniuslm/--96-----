import os
import re

def chinese_to_arabic(chinese_num):
    num_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
    unit_map = {'十': 10, '百': 100, '千': 1000, '万': 10000}
    result = 0
    temp = 0
    for char in chinese_num:
        if char in num_map:
            temp = num_map[char]
        elif char in unit_map:
            if temp == 0:
                temp = 1
            result += temp * unit_map[char]
            temp = 0
        else:
            return chinese_num
    result += temp
    return str(result)

def rename_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith('.txt'):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                first_line = file.readline().strip()
            
            match = re.match(r'第(.*?)章　(.*)', first_line)
            if match:
                chapter_num = match.group(1)
                chapter_title = match.group(2)
                
                # 将中文数字转换为阿拉伯数字
                chapter_num = chinese_to_arabic(chapter_num)
                
                # 将数字填充到3位
                chapter_num = chapter_num.zfill(3)
                
                new_filename = f'第{chapter_num}章 {chapter_title}.txt'
                os.rename(file_path, os.path.join(directory, new_filename))
                print(f'已重命名: {filename} -> {new_filename}')

# 使用脚本
directory = r'E:\python项目\Cursor\新版96小说网爬虫\txt\这个明星只想放假'
rename_files(directory)