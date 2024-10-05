import os
import re
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QComboBox, QListWidget, QTextEdit, QLabel, QPushButton, QSlider, QScrollBar, QSplitter)
from PySide6.QtCore import Qt, QSettings, QEvent
from PySide6.QtGui import QFont, QMouseEvent, QColor, QPalette

class CustomTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.is_dragging = False
        self.last_y = 0

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.last_y = event.position().y()
            self.setCursor(Qt.ClosedHandCursor)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_dragging:
            delta_y = self.last_y - event.position().y()
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + delta_y)
            self.last_y = event.position().y()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.setCursor(Qt.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)

class ReaderGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("小说阅读器")
        self.setGeometry(100, 100, 800, 600)
        
        # 设置应用程序全局字体
        app_font = QFont("MiSans")
        app_font.setWeight(QFont.Medium)
        QApplication.setFont(app_font)
        
        # 创建中央部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # 左侧布局
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 小说选择下拉框
        self.novel_combo = QComboBox()
        left_layout.addWidget(self.novel_combo)
        
        # 章节列表
        self.chapter_list = QListWidget()
        left_layout.addWidget(self.chapter_list)
        
        # 设置章节列表的样式表
        self.chapter_list.setStyleSheet("""
            QListWidget {
                font-size: 14px;
                font-weight: normal;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #70C070;
                color: #004000;
                font-weight: bold;
                border-radius: 5px;
            }
        """)

        # 控制区
        control_layout = QVBoxLayout()
        
        # 字体选择
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("字体:"))
        self.font_combo = QComboBox()
        self.font_combo.addItems(["MiSans", "宋体", "黑体", "楷体", "微软雅黑"])
        self.font_combo.setCurrentText("MiSans")  # 设置默认字体为 MiSans
        self.font_combo.currentTextChanged.connect(self.change_font)
        font_layout.addWidget(self.font_combo)
        control_layout.addLayout(font_layout)
        
        # 字重选择
        weight_layout = QHBoxLayout()
        weight_layout.addWidget(QLabel("字重:"))
        self.weight_combo = QComboBox()
        self.weight_combo.addItems(["正常", "半粗体", "粗体", "特粗"])
        self.weight_combo.setCurrentText("半粗体")  # 设置默认字重为半粗体
        self.weight_combo.currentTextChanged.connect(self.change_font_weight)
        weight_layout.addWidget(self.weight_combo)
        control_layout.addLayout(weight_layout)
        
        # 字号选择
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("字号:"))
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(12, 24)
        self.size_slider.setValue(16)  # 设置默认字号
        self.size_slider.setTickPosition(QSlider.TicksBelow)
        self.size_slider.setTickInterval(1)
        self.size_slider.valueChanged.connect(self.change_font_size)
        size_layout.addWidget(self.size_slider)
        self.size_label = QLabel("16")
        size_layout.addWidget(self.size_label)
        control_layout.addLayout(size_layout)
        
        left_layout.addLayout(control_layout)
        
        self.splitter.addWidget(left_widget)
        
        # 右侧文本编辑器
        self.content_edit = CustomTextEdit()
        self.content_edit.setReadOnly(True)
        self.content_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.content_edit.verticalScrollBar().setFixedWidth(15)
        self.content_edit.mouseDoubleClickEvent = self.toggle_left_panel
        self.splitter.addWidget(self.content_edit)
        
        # 设置初始分割比例
        self.splitter.setSizes([200, 600])
        
        # 加载小说列表
        self.load_novels()
        
        # 连接信号和槽
        self.novel_combo.currentIndexChanged.connect(self.load_chapters)
        self.chapter_list.itemClicked.connect(self.load_content)
        self.content_edit.textChanged.connect(self.save_scroll_position)

        # 添加设置对象
        self.settings = QSettings("MyCompany", "NovelReader")
        
        # 加载上次的阅读状态
        self.load_last_state()

    def load_novels(self):
        # 获取txt目录下的所有文件夹（小说）
        novel_dirs = [d for d in os.listdir('txt') if os.path.isdir(os.path.join('txt', d))]
        self.novel_combo.addItems(novel_dirs)

    def load_chapters(self):
        self.chapter_list.clear()
        current_novel = self.novel_combo.currentText()
        chapter_files = os.listdir(os.path.join('txt', current_novel))
        
        def chapter_sort_key(filename):
            # 使用正则表达式提取文件名中的数字
            match = re.search(r'^(\d+)', filename)
            if match:
                return int(match.group(1))
            return float('inf')  # 如果没有数字，将其排在最后
        
        chapter_files.sort(key=chapter_sort_key)
        self.chapter_list.addItems(chapter_files)

    def load_content(self, item):
        current_novel = self.novel_combo.currentText()
        chapter_file = item.text()
        with open(os.path.join('txt', current_novel, chapter_file), 'r', encoding='utf-8') as f:
            content = f.read()
        self.content_edit.setText(content)

    def change_font_size(self, size):
        font = self.content_edit.font()
        font.setPointSize(size)
        self.content_edit.setFont(font)
        self.size_label.setText(str(size))
        self.save_last_state()

    def change_font_weight(self, weight):
        font = self.content_edit.font()
        weight_map = {"正常": QFont.Normal, "半粗体": QFont.Medium, "粗体": QFont.Bold, "特粗": QFont.Black}
        font.setWeight(weight_map.get(weight, QFont.Medium))  # 默认使用半粗体
        self.content_edit.setFont(font)
        self.save_last_state()

    def change_font(self, font_name):
        font = self.content_edit.font()
        font.setFamily(font_name)
        self.content_edit.setFont(font)
        self.save_last_state()

    def save_last_state(self):
        current_novel = self.novel_combo.currentText()
        current_chapter = self.chapter_list.currentItem().text() if self.chapter_list.currentItem() else ""
        scroll_position = self.content_edit.verticalScrollBar().value()
        
        state = {
            "novel": current_novel,
            "chapter": current_chapter,
            "scroll_position": scroll_position,
            "font_family": self.font_combo.currentText(),
            "font_size": self.size_slider.value(),
            "font_weight": self.weight_combo.currentText()
        }
        
        self.settings.setValue("last_state", json.dumps(state))

    def load_last_state(self):
        state_json = self.settings.value("last_state", "{}")
        state = json.loads(state_json)
        
        if state.get("novel"):
            index = self.novel_combo.findText(state["novel"])
            if index >= 0:
                self.novel_combo.setCurrentIndex(index)
                self.load_chapters()
                
                if state.get("chapter"):
                    items = self.chapter_list.findItems(state["chapter"], Qt.MatchExactly)
                    if items:
                        self.chapter_list.setCurrentItem(items[0])
                        self.load_content(items[0])
                        
                        # 恢复滚动位置
                        QApplication.processEvents()
                        self.content_edit.verticalScrollBar().setValue(state.get("scroll_position", 0))

        if state.get("font_family"):
            index = self.font_combo.findText(state["font_family"])
            if index >= 0:
                self.font_combo.setCurrentIndex(index)
        
        if state.get("font_size"):
            self.size_slider.setValue(state["font_size"])
        
        if state.get("font_weight"):
            index = self.weight_combo.findText(state["font_weight"])
            if index >= 0:
                self.weight_combo.setCurrentIndex(index)
        
        self.change_font(self.font_combo.currentText())
        self.change_font_size(self.size_slider.value())
        self.change_font_weight(self.weight_combo.currentText())

    def save_scroll_position(self):
        self.save_last_state()

    def closeEvent(self, event):
        self.save_last_state()
        super().closeEvent(event)

    def toggle_left_panel(self, event):
        left_widget = self.splitter.widget(0)
        if left_widget.isVisible():
            left_widget.hide()
        else:
            left_widget.show()

if __name__ == "__main__":
    app = QApplication([])
    window = ReaderGUI()
    window.show()
    app.exec()