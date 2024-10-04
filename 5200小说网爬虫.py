import os
import time
import random
import requests
from lxml import html
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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
def download_novel(url, save_dir=None):
    session = create_session()
    try:
        html_content = get_html(url, session)
        if not html_content:
            return

        tree = html.fromstring(html_content)
        novel_name_element = tree.xpath('//h1/text()')
        if not novel_name_element:
            print("无法找到小说名称")
            return
        novel_name = novel_name_element[0].strip()

        chapter_links = tree.xpath('/html/body/section/article/ul/li/a')
        if not chapter_links:
            print("无法找到章节链接")
            return

        save_path = os.path.join(save_dir, "txt", novel_name)
        os.makedirs(save_path, exist_ok=True)

        for link in chapter_links:
            chapter_title = link.text.strip()
            chapter_url = link.get('href')
            if not chapter_url.startswith('http'):
                chapter_url = f"https://www.5200xiaoshuo.com{chapter_url}"

            chapter_content = download_chapter_content(chapter_url, session)
            if chapter_content:
                chapter_file_path = os.path.join(save_path, f"{chapter_title}.txt")
                with open(chapter_file_path, 'w', encoding='utf-8') as file:
                    file.write(chapter_content)
                print(f"已下载: {chapter_title}")
            
            time.sleep(random.uniform(1, 3))

    except Exception as e:
        print(f"下载小说时发生错误: {e}")
        import traceback
        print(traceback.format_exc())

# 获取单个章节内容
def download_chapter_content(chapter_url, session):
    try:
        html_content = get_html(chapter_url, session)
        if not html_content:
            return None

        tree = html.fromstring(html_content)
        
        # 获取章节标题
        chapter_title = tree.xpath('/html/body/article/header/h1/text()')
        chapter_title = chapter_title[0].strip() if chapter_title else "未知标题"
        
        # 获取章节内容
        content_paragraphs = tree.xpath('/html/body/article/div[3]/p/text()')
        if not content_paragraphs:
            print(f"无法在 {chapter_url} 找到章节内容")
            return None
        
        # 组合标题和内容
        full_content = f"{chapter_title}\n\n" + "\n".join(p.strip() for p in content_paragraphs if p.strip())
        return full_content
    except Exception as e:
        print(f"获取章节内容错误: {e}")
        return None

# 主函数
def main():
    url = 'https://www.5200xiaoshuo.com/71_71424/all.html'  # 替换为实际的小说目录页面地址
    
    # 默认使用脚本所在目录，您也可以指定其他目录
    default_save_dir = get_script_directory()
    # 如果想使用自定义目录，可以取消下面这行的注释并修改路径
    # custom_save_dir = r"E:\python项目\FastAPI\资产文件\文件存储"
    
    download_novel(url, save_dir=default_save_dir)
    # 如果想使用自定义目录，使用下面这行
    # download_novel(url, save_dir=custom_save_dir)

if __name__ == '__main__':
    main()