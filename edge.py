import asyncio
import os
import edge_tts


# 修改函数定义，添加保存文件路径为参数
async def Edge合成音频(文字内容: str, 保存文件路径: str, 播报员: str = "zh-CN-YunxiNeural") -> str:
    communicate = edge_tts.Communicate(文字内容, 播报员)
    await communicate.save(保存文件路径)
    return 保存文件路径


def 读取小说文件(文件路径):
    # 规范化路径
    文件路径 = os.path.normpath(文件路径)
    
    # 检查文件是否存在
    if not os.path.exists(文件路径):
        print(f"文件不存在：{文件路径}")
        return None
    
    try:
        with open(文件路径, 'r', encoding='utf-8') as 文件:
            return 文件.read()
    except Exception as e:
        print(f"读取文件时出错：{e}")
        return None



# 如果是直接运行这个脚本 YunjianNeural YunyangNeural
if __name__ == "__main__":
    小说章节 = "186.第185章 李大人托我传句话.txt"
    文本内容 = 读取小说文件(小说章节)

    目标文件夹 = os.path.join(os.getcwd(), "大明")
    os.makedirs(目标文件夹, exist_ok=True)

    保存文件的路径 = os.path.join(目标文件夹, f"{小说章节}.mp3")

    print(保存文件的路径)
    生成的音频文件路径 = asyncio.run(Edge合成音频(文本内容, 保存文件的路径,播报员="zh-CN-YunjianNeural"))
    print(f"音频文件已生成，路径为：{生成的音频文件路径}")
