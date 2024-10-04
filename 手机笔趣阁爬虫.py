import os
import time
import random
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 定义请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
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
        response.encoding = 'gb2312'
        return response.text
    except requests.RequestException as e:
        print(f"请求错误: {e}")
        return None

# 获取当前脚本所在目录
def get_script_directory():
    return os.path.dirname(os.path.abspath(__file__))

# 下载并保存章节内容
def download_novel(url, save_dir=None, progress_callback=None, start_chapter=1, end_chapter=-1):
    session = create_session()
    try:
        all_chapters = get_all_chapter_links(url, session)
        if not all_chapters:
            print("无法获取章节列表")
            return

        # 获取小说名
        novel_name = get_novel_name(url, session)
        if not novel_name:
            print("无法获取小说名")
            return

        # 确保 save_dir 存在
        if save_dir is None:
            save_dir = get_script_directory()
        txt_dir = os.path.join(save_dir, "txt", novel_name)
        os.makedirs(txt_dir, exist_ok=True)

        # 处理章节范围
        start_index = max(start_chapter - 1, 0)
        end_index = len(all_chapters) if end_chapter < 0 else min(end_chapter, len(all_chapters))
        chapters_to_download = all_chapters[start_index:end_index]

        # 下载并保存章节内容
        for index, item in enumerate(chapters_to_download, start=start_index + 1):
            chapter_url = 'https://m.boquge.com' + item['href']
            chapter_title = item.get_text().strip()
            print(f"正在处理章节 {index}/{end_index}: {chapter_title}")
            chapter_content = download_chapter_content(chapter_url, session)
            if chapter_content:
                formatted_title = format_chapter_title(chapter_title, index)
                chapter_file_path = os.path.join(txt_dir, f"{formatted_title}.txt")
                with open(chapter_file_path, 'w', encoding='utf-8') as file:
                    file.write(f"{formatted_title}\n\n{chapter_content}")
                if progress_callback:
                    progress_callback(f"已下载: {formatted_title}")
            else:
                print(f"无法获取章节内容: {chapter_title}")
            
            time.sleep(random.uniform(2, 5))

        print("指定范围的章节下载完成")

    except Exception as e:
        print(f"下载小说时发生错误: {e}")
        import traceback
        traceback.print_exc()

# 获取单个章节内容
def download_chapter_content(chapter_url, session):
    try:
        html = get_html(chapter_url, session)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')
        content = soup.select_one('#cContent')
        if content:
            # 找到所有的<p>标签
            paragraphs = content.find_all('p')
            # 提取每个<p>标签的文本,并用两个换行符连接
            formatted_content = '\n\n'.join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
            return formatted_content
        else:
            print("无法找到章节内容")
            return None
    except Exception as e:
        print(f"获取章节内容错误: {e}")
        return None

# 格式化章节标题
def format_chapter_title(title, index):
    return f'{index:03d} {title}'

# 获取所有章节链接
def get_all_chapter_links(url, session):
    html = get_html(url, session)
    if not html:
        print("无法获取目录页面内容")
        return []

    soup = BeautifulSoup(html, 'html.parser')
    
    # 获取尾页链接
    last_page_link = soup.select_one('div.novel-desc div#pager a[href*="-22.html"]')
    if not last_page_link:
        print("无法找到尾页链接")
        return []

    last_page_num = int(last_page_link['href'].split('-')[-1].split('.')[0])
    print(f"共有 {last_page_num} 页目录")

    all_chapters = []
    for page_num in range(1, last_page_num + 1):
        page_url = f"https://m.boquge.com/wapbook/179180-{page_num}.html"
        print(f"正在提取第 {page_num}/{last_page_num} 页的章节链接")
        page_html = get_html(page_url, session)
        if page_html:
            page_soup = BeautifulSoup(page_html, 'html.parser')
            chapters = page_soup.select('ul.book_textList li a')
            all_chapters.extend(chapters)
        else:
            print(f"无法获取第 {page_num} 页的内容")
        time.sleep(random.uniform(1, 3))  # 添加延迟,避免请求过于频繁

    print(f"总共找到 {len(all_chapters)} 个章节")
    return all_chapters

# 新增函数：获取小说名
def get_novel_name(url, session):
    html = get_html(url, session)
    if not html:
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    novel_title = soup.select_one('div.novel-update-box h1 a')
    if novel_title:
        return novel_title.get_text().strip()
    return None

# 主函数
def main():
    catalog_url = r"https://m.boquge.com/wapbook/179180-1.html"
    download_novel(catalog_url, start_chapter=103, end_chapter=-1)

if __name__ == '__main__':
    main()