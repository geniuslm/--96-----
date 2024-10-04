import os
import time
import random
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re

# 定义请求头，模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# 创建一个具有重试机制的会话
def create_session():
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# 获取网页内容
def get_html(url, session):
    try:
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response.text
    except requests.RequestException as e:
        print(f"请求错误: {e}")
        return None

# 获取当前脚本所在目录
def get_script_directory():
    return os.path.dirname(os.path.abspath(__file__))

# 下载并保存章节内容
def download_novel(url, save_dir=None, progress_callback=None):
    session = create_session()
    try:
        html = get_html(url, session)
        if not html:
            return

        soup = BeautifulSoup(html, 'html.parser')
        novel_name = soup.select_one('body > div.container > div > h3 > div.bread > a:nth-child(3)').get_text().strip()

        if save_dir is None:
            save_dir = get_script_directory()
        
        save_path = os.path.join(save_dir, "txt", novel_name)
        os.makedirs(save_path, exist_ok=True)

        catalog_list = soup.select('#catalog > ul > li > a')
        ordered_catalog = determine_chapter_order(catalog_list)
        
        print(f"下载顺序: 从 '{ordered_catalog[0].get_text().strip()}' 到 '{ordered_catalog[-1].get_text().strip()}'")
        
        for item in ordered_catalog:
            chapter_title = item.get_text().strip()
            chapter_url = item['href']

            formatted_title = format_chapter_title(chapter_title)
            chapter_content = download_chapter_content(chapter_url, session)
            if chapter_content:
                chapter_file_path = os.path.join(save_path, f"{formatted_title}.txt")
                with open(chapter_file_path, 'w', encoding='utf-8') as file:
                    file.write(f"{formatted_title}\n\n{chapter_content}")
                if progress_callback:
                    progress_callback(f"已下载: {formatted_title}")
            
            # 添加随机延迟，避免请求过于频繁
            time.sleep(random.uniform(2, 5))

    except Exception as e:
        if progress_callback:
            progress_callback(f"下载小说时发生错误: {e}")
        else:
            print(f"下载小说时发生错误: {e}")

# 获取单个章节内容
def download_chapter_content(chapter_url, session):
    try:
        html = get_html(chapter_url, session)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')
        chapter_content = soup.select_one('body > div.container > div.mybox > div.txtnav').get_text().strip()
        return chapter_content
    except Exception as e:
        print(f"获取章节内容错误: {e}")
        return None

# 将中文数字转换为阿拉伯数字
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

# 格式化章节标题
def format_chapter_title(title):
    match = re.match(r'第(.*?)章　(.*)', title)
    if match:
        chapter_num = match.group(1)
        chapter_title = match.group(2)
        
        # 将中文数字转换为阿拉伯数字
        chapter_num = chinese_to_arabic(chapter_num)
        
        # 将数字填充到3位
        chapter_num = chapter_num.zfill(3)
        
        return f'第{chapter_num}章 {chapter_title}'
    return title

# 智能判断章节顺序
def determine_chapter_order(catalog_list):
    # 提取所有章节的编号
    chapter_numbers = [extract_chapter_number(chapter.get_text().strip()) for chapter in catalog_list]
    
    # 过滤掉None值,只保留有效的章节编号
    valid_numbers = [num for num in chapter_numbers if num is not None]
    
    if valid_numbers:
        # 如果有效的章节编号是递增的,保持原顺序;否则反转顺序
        if all(valid_numbers[i] <= valid_numbers[i+1] for i in range(len(valid_numbers)-1)):
            return catalog_list
        else:
            return list(reversed(catalog_list))
    else:
        # 如果没有有效的章节编号,使用字符串排序
        return sorted(catalog_list, key=lambda x: x.get_text().strip())

def extract_chapter_number(chapter_title):
    # 尝试匹配"第X章"的模式
    match = re.search(r'第(\d+)章', chapter_title)
    if match:
        return int(match.group(1))
    
    # 如果上面的匹配失败,尝试匹配纯数字
    match = re.search(r'\d+', chapter_title)
    if match:
        return int(match.group())
    
    # 如果都匹配失败,返回None
    return None

# 主函数
def main():
    url = 'https://69shuba.cx/book/10019447/'  # 替换为实际的小说目录页面地址
    
    # 默认使用脚本所在目录，您也可以指定其他目录
    default_save_dir = get_script_directory()
    # 如果想使用自定义目录，可以取消下面这行的注释并修改路径
    # custom_save_dir = r"E:\python项目\FastAPI\资产文件\文件存储"
    
    download_novel(url, save_dir=default_save_dir, progress_callback=print)
    # 如果想使用自定义目录，使用下面这行
    # download_novel(url, save_dir=custom_save_dir)

if __name__ == '__main__':
    main()