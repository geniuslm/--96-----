import requests
import os

# 设置保存目录
save_dir = "目录分析"

# 创建保存目录
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# 下载并保存网页
def download_page(url, prefix):
    response = requests.get(url)
    if response.status_code == 200:
        filename = f"{prefix}_{url.split('/')[-1]}.html"
        with open(os.path.join(save_dir, filename), "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"{prefix}页面已下载：{filename}")
    else:
        print(f"下载{prefix}页面失败")

# 主函数
def main():
    # 目录页面URL
    directory_url = r"https://m.boquge.com/wapbook/187863-1.html"
    
    # 内容页面URL
    content_url = r"https://m.boquge.com/wapbook/187863_189394157.html"
    
    # 下载目录页面
    download_page(directory_url, "目录")
    
    # 下载内容页面
    download_page(content_url, "内容")

if __name__ == "__main__":
    main()
