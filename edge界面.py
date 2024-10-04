import asyncio
import os
import re
import sys
import time  # 引入time模块
from PySide6.QtCore import QThread, Signal, QRunnable, QThreadPool, QObject, Slot
from PySide6.QtCore import QTimer
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QComboBox, QHBoxLayout, QSpinBox)
from PySide6.QtWidgets import QListWidget, QScrollArea, QListWidgetItem, QTextEdit,QLineEdit
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
            self.signals.log.emit(f"开始合成：{os.path.basename(self.保存文件路径)}")
            start_time = time.time()

            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 运行协程
            Edge合成音频结果 = loop.run_until_complete(Edge合成音频(self.文字内容, self.保存文件路径, self.播报员))

            # 发送完成合成的日志
            elapsed_time = time.time() - start_time
            self.signals.log.emit(f"{os.path.basename(self.保存文件路径)} 合成完成，用时 {elapsed_time:.2f}秒")

            # 发送完成信号
            self.signals.finished.emit(self.保存文件路径)

        except Exception as e:
            self.signals.log.emit(f"合成失败：{str(e)}")

        finally:
            loop.close()


class MainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("小说章节音频合成器")
        self.layout = QVBoxLayout()

        self.label2 = QLabel("选择播报员：")
        self.layout.addWidget(self.label2)

        self.comboBox = QComboBox()
        self.comboBox.addItems(["zh-CN-YunjianNeural", "zh-CN-YunxiNeural"])  # 添加你的播报员选项
        self.layout.addWidget(self.comboBox)
        self.setLayout(self.layout)

        # 添加一个新的输入框让用户输入目标文件夹
        self.saveFolderPathLabel = QLabel("输入保存音频的文件夹路径：")
        self.layout.addWidget(self.saveFolderPathLabel)

        self.saveFolderPathLineEdit = QLineEdit(self)
        self.saveFolderPathLineEdit.setPlaceholderText("例如：大明")
        self.layout.addWidget(self.saveFolderPathLineEdit)

        # 初始化定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTimer)
        self.startTime = 0
        self.fileListWidget = QListWidget()
        self.selectedFilesListWidget = QListWidget()

        self.scanButton = QPushButton("选择文件夹并扫描")
        self.scanButton.clicked.connect(self.scanDirectory)
        self.layout.addWidget(self.scanButton)

        # 添加区间选择功能，放在扫描按钮下面
        self.rangeSelectionLayout = QHBoxLayout()
        self.startSpinBox = QSpinBox()
        self.endSpinBox = QSpinBox()
        self.selectRangeButton = QPushButton("选择区间")
        self.rangeSelectionLayout.addWidget(QLabel("起始章节:"))
        self.rangeSelectionLayout.addWidget(self.startSpinBox)
        self.rangeSelectionLayout.addWidget(QLabel("结束章节:"))
        self.rangeSelectionLayout.addWidget(self.endSpinBox)
        self.rangeSelectionLayout.addWidget(self.selectRangeButton)
        self.layout.addLayout(self.rangeSelectionLayout)

        # 设置滑条区域展示文件列表
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidget(self.fileListWidget)
        self.scrollArea.setWidgetResizable(True)
        self.layout.addWidget(self.scrollArea)

        # 设置滑条区域展示选中的文件列表
        self.selectedFilesScrollArea = QScrollArea()
        self.selectedFilesScrollArea.setWidget(self.selectedFilesListWidget)
        self.selectedFilesScrollArea.setWidgetResizable(True)
        self.layout.addWidget(self.selectedFilesScrollArea)

        self.confirmSelectionButton = QPushButton("确认选择")
        self.confirmSelectionButton.clicked.connect(self.updateSelectedFilesDisplay)
        self.layout.addWidget(self.confirmSelectionButton)

        self.batchStartButton = QPushButton("批量开始合成")
        self.batchStartButton.clicked.connect(self.batchStartSynthesis)
        self.layout.addWidget(self.batchStartButton)

        self.logTextEdit = QTextEdit()
        self.logTextEdit.setReadOnly(True)  # 设置为只读，用户不能编辑
        self.layout.addWidget(self.logTextEdit)

        # 初始化选中文件的数组
        self.selectedFiles = []

        # 初始化线程池，设置最大线程数为3
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(3)

        # 连接区间选择按钮的点击事件
        self.selectRangeButton.clicked.connect(self.selectFileRange)

        # 初始化小说名称变量
        self.novel_name = ""

        # 添加URL输入框
        self.urlLabel = QLabel("输入小说URL:")
        self.layout.addWidget(self.urlLabel)
        self.urlInput = QLineEdit()
        self.layout.addWidget(self.urlInput)

        # 添加开始爬取按钮
        self.startCrawlButton = QPushButton("开始爬取")
        self.startCrawlButton.clicked.connect(self.start_crawl)
        self.layout.addWidget(self.startCrawlButton)

        # 添加音频转换停止按钮
        self.stopSynthesisButton = QPushButton("停止音频转换")
        self.stopSynthesisButton.clicked.connect(self.stopSynthesis)
        self.stopSynthesisButton.setEnabled(False)  # 初始状态为禁用
        self.layout.addWidget(self.stopSynthesisButton)

        # 添加爬虫停止按钮
        self.stopCrawlButton = QPushButton("停止爬虫")
        self.stopCrawlButton.clicked.connect(self.stopCrawl)
        self.stopCrawlButton.setEnabled(False)  # 初始状态为禁用
        self.layout.addWidget(self.stopCrawlButton)

        # 添加标志位
        self.is_synthesizing = False
        self.is_crawling = False

        # 添加爬虫选择下拉框
        self.crawlerLabel = QLabel("选择爬虫:")
        self.crawlerComboBox = QComboBox()
        self.crawlerComboBox.addItems(["69爬虫", "笔趣阁爬虫"])
        self.layout.addWidget(self.crawlerLabel)
        self.layout.addWidget(self.crawlerComboBox)

        # 修改章节选择输入框为QSpinBox
        self.startChapterLabel = QLabel("起始章节:")
        self.startChapterInput = QSpinBox()
        self.startChapterInput.setMinimum(1)
        self.startChapterInput.setMaximum(9999)  # 设置一个较大的最大值
        self.endChapterLabel = QLabel("结束章节:")
        self.endChapterInput = QSpinBox()
        self.endChapterInput.setMinimum(-2)
        self.endChapterInput.setMaximum(9999)  # 设置一个较大的最大值
        self.layout.addWidget(self.startChapterLabel)
        self.layout.addWidget(self.startChapterInput)
        self.layout.addWidget(self.endChapterLabel)
        self.layout.addWidget(self.endChapterInput)

        # 连接startChapterInput的valueChanged信号到一个新的方法
        self.startChapterInput.valueChanged.connect(self.updateEndChapterMinimum)

    def updateSelectedFilesDisplay(self):
        self.selectedFilesListWidget.clear()  # 清空当前选中文件的列表
        self.selectedFiles = []  # 清空选中文件的路径数组
        for index in range(self.fileListWidget.count()):
            item = self.fileListWidget.item(index)
            if item.checkState() == Qt.Checked:
                filePath = os.path.join(self.currentDirectory, item.text())  # 假设currentDirectory是你当前扫描的目录
                self.selectedFiles.append(filePath)
                self.selectedFilesListWidget.addItem(filePath)

    def scanDirectory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if directory:
            self.currentDirectory = directory
            self.novel_name = os.path.basename(directory)  # 获取文件夹名作为小说名
            
            # 更新保存路径的默认值
            default_save_path = os.path.join(os.getcwd(), "音频文件", self.novel_name)
            self.saveFolderPathLineEdit.setText(default_save_path)
            
            # 清除之前的列表
            self.fileListWidget.clear()
            self.selectedFiles.clear()
            self.selectedFilesListWidget.clear()  # 如果有必要，也清空选中文件的显示列表

            # 获取目录中的所有文件并进行自然排序
            filenames = os.listdir(directory)
            sorted_filenames = sorted(filenames, key=lambda x: [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', x)])

            for index, filename in enumerate(sorted_filenames, start=1):
                if os.path.isfile(os.path.join(directory, filename)):
                    display_text = f"{index:03d}. {filename}"  # 添加三位数的序号
                    listItem = QListWidgetItem(display_text)
                    listItem.setFlags(listItem.flags() | Qt.ItemIsUserCheckable)
                    listItem.setCheckState(Qt.Unchecked)
                    self.fileListWidget.addItem(listItem)

            # 更新SpinBox的范围
            max_chapter = len(sorted_filenames)
            self.startSpinBox.setRange(1, max_chapter)
            self.endSpinBox.setRange(1, max_chapter)
            self.endSpinBox.setValue(max_chapter)  # 默认设置为最大章节

    def fileListWidgetItemChanged(self, item):
        # 当用户勾选或取消勾选一个文件时更新选中文件的数组
        filePath = os.path.join(self.currentDirectory, item.text())
        if item.checkState() == Qt.Checked and filePath not in self.selectedFiles:
            self.selectedFiles.append(filePath)
            self.selectedFilesListWidget.addItem(filePath)
        elif item.checkState() == Qt.Unchecked and filePath in self.selectedFiles:
            self.selectedFiles.remove(filePath)
            # 这里需要找到并移除对应的QListWidgetItem
            foundItems = self.selectedFilesListWidget.findItems(filePath, Qt.MatchExactly)
            if foundItems:
                for item in foundItems:
                    row = self.selectedFilesListWidget.row(item)
                    self.selectedFilesListWidget.takeItem(row)

    def batchStartSynthesis(self):
        self.is_synthesizing = True
        self.stopSynthesisButton.setEnabled(True)
        用户指定目录 = self.saveFolderPathLineEdit.text().strip()
        if not 用户指定目录:
            用户指定目录 = os.path.join(os.getcwd(), "音频文件", self.novel_name)
        
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

    def stopSynthesis(self):
        if self.is_synthesizing:
            self.is_synthesizing = False
            self.threadpool.clear()  # 清空线程池中的任务
            self.stopSynthesisButton.setEnabled(False)
            self.updateLog("音频转换已停止")

    @Slot(str)
    def updateLog(self, message):
        self.logTextEdit.append(message)

    @Slot(str)
    def onWorkerFinished(self, file_path):
        self.updateLog(f"文件 {os.path.basename(file_path)} 处理完成")

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
        try:
            def custom_print(*args, **kwargs):
                if not self.is_crawling:
                    raise Exception("爬虫已停止")
                message = ' '.join(map(str, args))
                self.updateLog(message)

            original_stdout = sys.stdout
            class CustomStdout:
                def write(self, message):
                    if message.strip():
                        custom_print(message.strip())
                def flush(self):
                    pass

            sys.stdout = CustomStdout()

            if selected_crawler == "69爬虫":
                download_novel_69(url, save_dir=get_script_directory(), progress_callback=custom_print, start_chapter=start_chapter, end_chapter=end_chapter)
            else:  # 笔趣阁爬虫
                download_novel_biquge(url, save_dir=get_script_directory_biquge(), progress_callback=custom_print, start_chapter=start_chapter, end_chapter=end_chapter)

        except Exception as e:
            if str(e) != "爬虫已停止":
                self.updateLog(f"爬取过程中发生错误: {str(e)}")
        finally:
            sys.stdout = original_stdout
            self.is_crawling = False
            QMetaObject.invokeMethod(self.startCrawlButton, "setEnabled", 
                                     Qt.QueuedConnection,
                                     Q_ARG(bool, True))
            QMetaObject.invokeMethod(self.stopCrawlButton, "setEnabled", 
                                     Qt.QueuedConnection,
                                     Q_ARG(bool, False))

    @Slot(str)
    def updateLog(self, message):
        # 使用QMetaObject.invokeMethod确保在主线程中更新UI
        QMetaObject.invokeMethod(self.logTextEdit, "append", 
                                 Qt.QueuedConnection,
                                 Q_ARG(str, message))

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