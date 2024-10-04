import asyncio
import os
import re
import sys
import time  # 引入time模块
from PySide6.QtCore import QThread, Signal, QRunnable, QThreadPool, QObject, Slot
from PySide6.QtCore import QTimer
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QComboBox, QHBoxLayout, QSpinBox,
                               QListWidget, QScrollArea, QListWidgetItem, QTextEdit, QLineEdit, QGroupBox, QStyle)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize
from PySide6.QtCore import QMetaObject, Q_ARG
import threading
from 新版69爬虫 import download_novel as download_novel_69, get_script_directory
from 手机笔趣阁爬虫 import download_novel as download_novel_biquge, get_script_directory as get_script_directory_biquge


# 你之前的脚本代码应该被导入或在这里重新定义
from edge import Edge合成音频, 读取小说文件


class WorkerSignals(QObject):
    finished = Signal(str)
    log = Signal(str)


class Worker(QRunnable):
    def __init__(self, 文字内容, 保存文件路径, 播报员):
        super().__init__()
        self.文字内容 = 文字内容
        self.保存文件路径 = 保存文件路径
        self.播报员 = 播报员
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        try:
            # 发送开始合成的日志
            file_name = os.path.basename(self.保存文件路径)
            self.signals.log.emit(f"开始合成: {file_name:>60}")
            start_time = time.time()

            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 运行协程
            Edge合成音频结果 = loop.run_until_complete(Edge合成音频(self.文字内容, self.保存文件路径, self.播报员))

            # 发送完成合成的日志
            elapsed_time = time.time() - start_time
            self.signals.log.emit(f"合成完成: {elapsed_time:>6.2f}秒 {file_name}")

        except Exception as e:
            self.signals.log.emit(f"合成失败：{str(e)}")

        finally:
            loop.close()


class MainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("小说章节音频合成器")
        self.layout = QVBoxLayout()

        # 创建所有控件
        self.createWidgets()

        # 创建两个主要部分：爬虫和TTS
        crawler_group = QGroupBox("爬虫设置")
        tts_group = QGroupBox("TTS设置")

        crawler_layout = QVBoxLayout()
        tts_layout = QVBoxLayout()

        # 爬虫部分
        crawler_layout.addWidget(QLabel("选择爬虫:"))
        crawler_layout.addWidget(self.crawlerComboBox)
        crawler_layout.addWidget(QLabel("输入小说URL:"))
        crawler_layout.addWidget(self.urlInput)
        crawler_layout.addWidget(self.startChapterLabel)
        crawler_layout.addWidget(self.startChapterInput)
        crawler_layout.addWidget(self.endChapterLabel)
        crawler_layout.addWidget(self.endChapterInput)
        crawler_layout.addWidget(self.startCrawlButton)
        crawler_layout.addWidget(self.stopCrawlButton)
        crawler_group.setLayout(crawler_layout)

        # TTS部分
        tts_layout.addWidget(self.label2)
        tts_layout.addWidget(self.comboBox)
        tts_layout.addWidget(self.saveFolderPathLabel)
        tts_layout.addWidget(self.saveFolderPathLineEdit)
        tts_layout.addWidget(self.selectFolderButton)
        tts_layout.addLayout(self.rangeSelectionLayout)

        # 文件列表、确认选择按钮和选中文件列表并排
        lists_layout = QHBoxLayout()
        lists_layout.addWidget(self.scrollArea, 4)  # 左侧列表占4份宽度
        
        # 添加一个垂直布局来容纳确认选择按钮
        button_layout = QVBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.confirmSelectionButton)
        button_layout.addStretch()
        lists_layout.addLayout(button_layout, 1)  # 按钮占1份宽度
        
        lists_layout.addWidget(self.selectedFilesScrollArea, 4)  # 右侧列表占4份宽度
        tts_layout.addLayout(lists_layout)

        tts_layout.addWidget(self.batchStartButton)
        tts_layout.addWidget(self.stopSynthesisButton)
        tts_group.setLayout(tts_layout)

        # 将两个主要部分添加到主布局
        self.layout.addWidget(crawler_group)
        self.layout.addWidget(tts_group)

        # 日志部分
        self.layout.addWidget(self.logTextEdit)

        self.setLayout(self.layout)

        # 初始化其他设置
        self.initializeOtherSettings()

        # 确保这行代码存在
        self.confirmSelectionButton.clicked.connect(self.updateSelectedFilesDisplay)

        # 初始化右侧列表
        self.selectedFilesListWidget = QListWidget()
        self.selectedFilesScrollArea.setWidget(self.selectedFilesListWidget)
        
        # 设置滚动区域的最小大小
        self.selectedFilesScrollArea.setMinimumSize(200, 200)
        
        # 添加一个初始项目
        self.selectedFilesListWidget.addItem("初始测试项目")
        
        # 确保这行代码存在
        self.confirmSelectionButton.clicked.connect(self.updateSelectedFilesDisplay)

        # 修改默认播报员
        self.comboBox.setCurrentText("zh-CN-YunyangNeural")

        # 修改确认选择按钮
        self.confirmSelectionButton.setText("")
        self.confirmSelectionButton.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
        self.confirmSelectionButton.setIconSize(QSize(30, 30))  # 调整图标大小
        self.confirmSelectionButton.setFixedSize(40, 80)  # 调整按钮大小

    def createWidgets(self):
        # 创建所有控件
        self.crawlerComboBox = QComboBox()
        self.crawlerComboBox.addItems(["69爬虫", "笔趣阁爬虫"])
        self.urlInput = QLineEdit()
        self.startChapterLabel = QLabel("起始章节:")
        self.startChapterInput = QSpinBox()
        self.startChapterInput.setMinimum(1)
        self.startChapterInput.setMaximum(9999)  # 设置一个较大的最大值
        self.endChapterLabel = QLabel("结束章节:")
        self.endChapterInput = QSpinBox()
        self.endChapterInput.setMinimum(-2)
        self.endChapterInput.setMaximum(9999)  # 设置一个较大的最大值
        self.startCrawlButton = QPushButton("开始爬取")
        self.startCrawlButton.clicked.connect(self.start_crawl)
        self.stopCrawlButton = QPushButton("停止爬虫")
        self.stopCrawlButton.clicked.connect(self.stopCrawl)
        self.stopCrawlButton.setEnabled(False)  # 初始状态为禁用
        self.label2 = QLabel("选择播报员:")
        self.comboBox = QComboBox()
        self.comboBox.addItems(["zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural", "zh-CN-YunyangNeural", "zh-CN-liaoning-XiaobeiNeural", "zh-CN-shaanxi-XiaoniNeural"])
        self.saveFolderPathLabel = QLabel("保存文件夹路径:")
        self.saveFolderPathLineEdit = QLineEdit()
        self.selectFolderButton = QPushButton("选择小说文件夹")
        self.selectFolderButton.clicked.connect(self.selectAndScanDirectory)
        self.rangeSelectionLayout = QHBoxLayout()
        self.startSpinBox = QSpinBox()
        self.endSpinBox = QSpinBox()
        self.selectRangeButton = QPushButton("选择区间")
        self.rangeSelectionLayout.addWidget(QLabel("起始章节:"))
        self.rangeSelectionLayout.addWidget(self.startSpinBox)
        self.rangeSelectionLayout.addWidget(QLabel("结束章节:"))
        self.rangeSelectionLayout.addWidget(self.endSpinBox)
        self.rangeSelectionLayout.addWidget(self.selectRangeButton)
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.fileListWidget = QListWidget()
        self.scrollArea.setWidget(self.fileListWidget)
        self.selectedFilesScrollArea = QScrollArea()
        self.selectedFilesScrollArea.setWidgetResizable(True)
        self.selectedFilesListWidget = QListWidget()
        self.selectedFilesScrollArea.setWidget(self.selectedFilesListWidget)
        self.confirmSelectionButton = QPushButton("确认选择 >>")
        self.confirmSelectionButton.clicked.connect(self.updateSelectedFilesDisplay)
        self.batchStartButton = QPushButton("批量开始合成")
        self.batchStartButton.clicked.connect(self.batchStartSynthesis)
        self.stopSynthesisButton = QPushButton("停止音频转换")
        self.stopSynthesisButton.clicked.connect(self.stopSynthesis)
        self.stopSynthesisButton.setEnabled(False)  # 初始状态为禁用
        self.logTextEdit = QTextEdit()
        self.logTextEdit.setReadOnly(True)  # 设置为只读，用户不能编辑

    def initializeOtherSettings(self):
        # 初始化定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTimer)
        self.startTime = 0
        self.selectedFilesListWidget = QListWidget()

        # 初始化选中文件的数组
        self.selectedFiles = []

        # 初始化线程池，设置最大线程数为3
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(3)

        # 连接区间选择按钮的点击事件
        self.selectRangeButton.clicked.connect(self.selectFileRange)

        # 初始化小说名称变量
        self.novel_name = ""

        # 添加标志位
        self.is_synthesizing = False
        self.is_crawling = False

        # 连接startChapterInput的valueChanged信号到一个新的方法
        self.startChapterInput.valueChanged.connect(self.updateEndChapterMinimum)

    def updateSelectedFilesDisplay(self):
        self.selectedFilesListWidget.clear()
        self.selectedFiles = []
        
        for index in range(self.fileListWidget.count()):
            item = self.fileListWidget.item(index)
            if item.checkState() == Qt.Checked:
                file_name = item.text().split(". ", 1)[1]
                filePath = os.path.join(self.currentDirectory, file_name)
                self.selectedFiles.append(filePath)
                self.selectedFilesListWidget.addItem(file_name)
        
        self.updateLog(f"已选择 {len(self.selectedFiles)} 个文件")
        
        # 如果列表为空，添加一个提示项
        if self.selectedFilesListWidget.count() == 0:
            self.selectedFilesListWidget.addItem("没有选中的文件")

    def selectAndScanDirectory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择小说文件夹")
        if directory:
            self.currentDirectory = directory
            self.novel_name = os.path.basename(directory)
            
            # 更新保存路径的默认值
            default_save_path = os.path.join(os.getcwd(), "音频文件", self.novel_name)
            self.saveFolderPathLineEdit.setText(default_save_path)
            
            # 清除之前的列表
            self.fileListWidget.clear()
            self.selectedFiles.clear()
            self.selectedFilesListWidget.clear()

            # 获取目录中的所有txt文件并进行自然排序
            filenames = [f for f in os.listdir(directory) if f.endswith('.txt')]
            sorted_filenames = sorted(filenames, key=lambda x: [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', x)])

            for index, filename in enumerate(sorted_filenames, start=1):
                display_text = f"{index:03d}. {filename}"
                listItem = QListWidgetItem(display_text)
                listItem.setFlags(listItem.flags() | Qt.ItemIsUserCheckable)
                listItem.setCheckState(Qt.Unchecked)
                self.fileListWidget.addItem(listItem)

            # 更新SpinBox的范围
            max_chapter = len(sorted_filenames)
            self.startSpinBox.setRange(1, max_chapter)
            self.endSpinBox.setRange(1, max_chapter)
            self.endSpinBox.setValue(max_chapter)

            self.updateLog(f"已加载 {max_chapter} 个txt文件")

    @Slot(str)
    def updateLog(self, message):
        # 移除对消息类型的限制,记录所有消息
        self.logTextEdit.append(message)

    def batchStartSynthesis(self):
        self.is_synthesizing = True
        self.stopSynthesisButton.setEnabled(True)
        用户指定目录 = self.saveFolderPathLineEdit.text().strip()
        if not 用户指定目录:
            用户指定目录 = os.path.join(os.getcwd(), "音频文件", self.novel_name)
        
        total_files = len(self.selectedFiles)
        self.processed_files = 0
        
        for filePath in self.selectedFiles:
            if not self.is_synthesizing:
                break
            # 移除文件名前的序号
            原文件名 = os.path.basename(filePath)
            章节名 = re.sub(r'^\d+\.\s*', '', 原文件名)
            
            # 构建新的文件路径
            新文件路径 = os.path.join(os.path.dirname(filePath), 章节名)
            
            文本内容 = 读取小说文件(新文件路径)
            if 文本内容 is None:
                self.updateLog(f"文件不存在：{新文件路径}")
                continue  # 跳过无法读取的文件
            
            if not os.path.exists(用户指定目录):
                os.makedirs(用户指定目录)
            
            保存文件的路径 = os.path.join(用户指定目录, f"{章节名}.mp3")
            播报员 = self.comboBox.currentText()
            
            worker = Worker(文本内容, 保存文件的路径, 播报员)
            worker.signals.log.connect(self.updateLog)
            worker.signals.finished.connect(self.onWorkerFinished)
            
            # 使用线程池启动worker
            self.threadpool.start(worker)
        
        # 启动一个定时器来检查是否所有任务都完成了
        self.checkCompletionTimer = QTimer()
        self.checkCompletionTimer.timeout.connect(lambda: self.checkCompletion(total_files))
        self.checkCompletionTimer.start(1000)  # 每秒检查一次

    def checkCompletion(self, total_files):
        if self.processed_files == total_files or not self.is_synthesizing:
            self.checkCompletionTimer.stop()
            if self.is_synthesizing:
                self.updateLog(f"批量转换完成：共处理 {self.processed_files} 个文件")
            else:
                self.updateLog(f"批量转换被中断：已处理 {self.processed_files}/{total_files} 个文件")
            self.is_synthesizing = False
            self.stopSynthesisButton.setEnabled(False)

    def onWorkerFinished(self, file_path):
        self.processed_files += 1
        self.updateLog(f"文件 {os.path.basename(file_path)} 处理完成")

    def stopSynthesis(self):
        if self.is_synthesizing:
            self.is_synthesizing = False
            self.threadpool.clear()  # 清空线程池中的任务
            self.stopSynthesisButton.setEnabled(False)
            self.updateLog("音频转换已停止")

    def openFileDialog(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择小说章节文件")
        if file_name:
            self.selectedFile = file_name
            self.label.setText(f"已选择文件：{file_name}")

    def startSynthesis(self):
        if hasattr(self, 'selectedFile'):
            # 启动计时器
            self.startTime = 0
            self.timer.start(1000)  # 每秒更新一次
            self.timerLabel.setText("合成用时：0秒")

            文本内容 = 读取小说文件(self.selectedFile)
            保存文件的路径 = os.path.join(os.getcwd(), "大明", os.path.basename(self.selectedFile) + ".mp3")
            播报员 = self.comboBox.currentText()
            self.worker = Worker(文本内容, 保存文件的路径, 播报员)
            self.worker.start()

    def updateTimer(self):
        """更新界面上的计时器标签"""
        self.startTime += 1
        self.timerLabel.setText(f"合成用时：{self.startTime}秒")

    def selectFileRange(self):
        start = self.startSpinBox.value() - 1  # 减1是因为列表索引从0开始
        end = self.endSpinBox.value()
        
        for i in range(self.fileListWidget.count()):
            item = self.fileListWidget.item(i)
            if start <= i < end:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
        
        # 更新选中文件的显示
        self.updateSelectedFilesDisplay()

    def start_crawl(self):
        url = self.urlInput.text().strip()
        if not url:
            self.updateLog("请输入有效的URL")
            return

        self.is_crawling = True
        self.startCrawlButton.setEnabled(False)
        self.stopCrawlButton.setEnabled(True)

        # 获取选择的爬虫和章节范围
        selected_crawler = self.crawlerComboBox.currentText()
        start_chapter = self.startChapterInput.value()
        end_chapter = self.endChapterInput.value()

        # 在新线程中运行爬虫
        threading.Thread(target=self.run_crawler, args=(url, selected_crawler, start_chapter, end_chapter), daemon=True).start()

    def stopCrawl(self):
        if self.is_crawling:
            self.is_crawling = False
            self.stopCrawlButton.setEnabled(False)
            self.startCrawlButton.setEnabled(True)
            self.updateLog("爬虫已停止")

    def run_crawler(self, url, selected_crawler, start_chapter, end_chapter):
        original_stdout = sys.stdout  # 保存原始的stdout

        class CustomOutput:
            def __init__(self, callback):
                self.callback = callback

            def write(self, message):
                if message.strip():  # 忽略空白行
                    self.callback(message.strip())

            def flush(self):
                pass  # 为了完整性添加这个方法

        try:
            custom_output = CustomOutput(lambda msg: QMetaObject.invokeMethod(self, "updateLog", 
                                                                              Qt.QueuedConnection,
                                                                              Q_ARG(str, msg)))
            sys.stdout = custom_output  # 重定向stdout到custom_output对象
            
            if not self.is_crawling:
                raise Exception("爬虫已停止")

            if selected_crawler == "69爬虫":
                download_novel_69(url, start_chapter, end_chapter)
            elif selected_crawler == "笔趣阁爬虫":
                download_novel_biquge(url, start_chapter, end_chapter)
            else:
                self.updateLog("未知的爬虫类型")

        except Exception as e:
            if str(e) != "爬虫已停止":
                self.updateLog(f"爬取过程中发生错误: {str(e)}")
        finally:
            sys.stdout = original_stdout  # 恢复原始的stdout
            self.is_crawling = False
            QMetaObject.invokeMethod(self.startCrawlButton, "setEnabled", 
                                     Qt.QueuedConnection,
                                     Q_ARG(bool, True))
            QMetaObject.invokeMethod(self.stopCrawlButton, "setEnabled", 
                                     Qt.QueuedConnection,
                                     Q_ARG(bool, False))

    def updateEndChapterMinimum(self, value):
        """
        当起始章节的值改变时,更新结束章节的最小值
        """
        self.endChapterInput.setMinimum(value)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())