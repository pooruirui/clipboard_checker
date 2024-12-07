# ui.py
from datetime import datetime, time
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QComboBox, QTextEdit, QHBoxLayout, QLabel, QApplication, QSpacerItem, QSizePolicy, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase, QIcon, QPixmap

from clipboard_monitor import ClipboardMonitor
from variable_checker import VariableChecker
from split_storage import SplitStorage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("小彭v1.2.0")
        self.resize(450, 500)  # 设置初始窗口大小为 450x500
        self.setWindowIcon(QIcon("640.ico"))

        # 加载字体
        font_id = QFontDatabase.addApplicationFont("微软简粗黑.ttf")
        if font_id < 0:
            print("字体加载失败")
            self.custom_font_family = "微软雅黑"  # 可以设置一个默认字体
        else:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                self.custom_font_family = font_families[0]
                print(f"加载字体：{self.custom_font_family}")
            else:
                self.custom_font_family = "微软简粗黑"

        # 初始化窗口置顶状态
        self.always_on_top = False

        # 保存窗口的大小和位置
        self.window_geometry = self.geometry()

        # 初始化报错检查状态
        self.enable_volume_check = False  # 声量超量报送监测
        self.is_interact = False  # 用于控制是否添加“，已互动”
        self.variables = None  # 用于保存变量
        self.original_text = ''  # 保存原始文本

        # 初始化界面
        self.init_ui()

        # 初始化复制监控类
        self.clipboard_monitor = ClipboardMonitor(self)
        self.clipboard_monitor.enable_volume_check = self.enable_volume_check  # 传递初始值
        self.clipboard_monitor.content_changed.connect(self.update_text_edits)
        self.clipboard_monitor.start()

    def init_ui(self):
        # 创建主部件
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        # 创建主布局
        main_layout = QVBoxLayout(self.main_widget)

        # 创建顶部布局，用于放置按钮
        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)

        # 添加图钉按钮
        self.pin_button = QPushButton('📌')
        self.pin_button.setCheckable(True)  # 使按钮可切换
        self.pin_button.setFixedSize(30, 30)  # 设置按钮的大小
        self.pin_button.clicked.connect(self.toggle_always_on_top)  # 连接按钮的点击事件
        top_layout.addWidget(self.pin_button)

        # 添加“报送”按钮
        self.error_check_button = QPushButton("报送")
        self.error_check_button.setFixedSize(30, 30)
        self.error_check_button.setCheckable(True)
        self.error_check_button.toggled.connect(self.toggle_error_check)
        top_layout.addWidget(self.error_check_button)

        # 添加字体大小选择下拉框
        self.font_size_combo = QComboBox()
        self.font_size_combo.setFixedSize(60, 30)
        self.font_size_combo.addItems([str(size) for size in range(5, 19)])
        self.font_size_combo.setCurrentText('7')  # 设置默认字体大小为7
        self.font_size_combo.currentTextChanged.connect(self.change_font_size_combo)
        top_layout.addWidget(self.font_size_combo)

        # 添加左侧弹性空间，将以下按钮推到右侧
        top_layout.addStretch()

        # 创建可折叠的按钮组容器
        self.collapsible_widget = QWidget()
        self.collapsible_layout = QHBoxLayout(self.collapsible_widget)
        self.collapsible_layout.setContentsMargins(0, 0, 0, 0)

        # 添加需要收起的按钮
        buttons = [
            ("用户号",self.copy_useId_text),
            ("单号", self.copy_special_text),
            ("作者", self.copy_author_text),
            ("链接", self.copy_lianjie_text),
            ("时间", self.copy_time_text),
            ("标题", self.copy_title_text),
            ("内容", self.copy_content_text),
            ("已互动", self.on_interact_button_clicked)
        ]
        for text, slot in buttons:
            btn = QPushButton(text)
            btn.setFixedSize(50, 30)
            btn.clicked.connect(slot)
            self.collapsible_layout.addWidget(btn)

        # 默认隐藏可折叠按钮组
        self.collapsible_widget.setVisible(False)

        # 将可折叠按钮组添加到顶部布局
        top_layout.addWidget(self.collapsible_widget)

        # 添加“更多”按钮
        self.more_button = QPushButton("更多")
        self.more_button.setFixedSize(50, 30)
        self.more_button.setCheckable(True)
        self.more_button.clicked.connect(self.toggle_collapsible_buttons)
        top_layout.addWidget(self.more_button)

        # 添加“复制”按钮
        self.copy_button = QPushButton("复制")
        self.copy_button.setFixedSize(50, 30)
        self.copy_button.clicked.connect(self.copy_right_text)
        top_layout.addWidget(self.copy_button)

        # 创建文本框区域
        text_edit_layout = QHBoxLayout()

        # 左侧文本框及其标签
        left_layout = QVBoxLayout()
        self.left_label = QLabel("剪贴板内容")
        self.text_edit_left = QTextEdit()
        self.text_edit_left.setReadOnly(True)  # 左文本框不可编辑
        left_layout.addWidget(self.left_label)
        left_layout.addWidget(self.text_edit_left)

        # 右侧文本框及其标签
        right_layout = QVBoxLayout()
        self.right_label = QLabel("处理后的内容")
        right_layout.addWidget(self.right_label)
        self.text_edit_right = QTextEdit()

        # 在此处定义 font 变量
        font = QFont(self.custom_font_family)
        font.setPointSize(int(self.font_size_combo.currentText()))

        # 设置文本框的字体
        self.text_edit_left.setFont(font)
        self.text_edit_right.setFont(font)

        # 禁止富文本输入
        self.text_edit_right.setAcceptRichText(False)
        right_layout.addWidget(self.text_edit_right)

        # 将左右布局添加到文本框布局中
        text_edit_layout.addLayout(left_layout)
        text_edit_layout.addLayout(right_layout)
        main_layout.addLayout(text_edit_layout)

        # 设置文本框的初始字体大小
        self.change_font_size_combo()

    def toggle_collapsible_buttons(self):
        # 切换可见性
        is_visible = self.collapsible_widget.isVisible()
        self.collapsible_widget.setVisible(not is_visible)
        # 更改按钮文本
        if is_visible:
            self.more_button.setText("更多")
        else:
            self.more_button.setText("收起")
        # 调整窗口大小
        self.adjustSize()

    # 互动按钮的点击事件处理方法
    def on_interact_button_clicked(self):
        self.is_interact = True  # 设置为 True
        # 重新处理剪贴板内容
        self.process_clipboard_content()

    # 处理剪贴板内容的方法
    def process_clipboard_content(self):
        text = self.original_text
        if text:
            # 使用传入的 text 创建 SplitStorage 实例
            storage = SplitStorage(text)
            variables = storage.get_variables()
            # 使用 VariableChecker 检查变量
            checker = VariableChecker(variables)
            variables, exception_state, exception_messages = checker.check_variables(
                enable_volume_check=self.enable_volume_check,
                is_interact=self.is_interact
            )

            # 构建处理后的内容（不含异常信息）
            processed_text = self.generate_processed_text(variables)

            # 构建异常信息字符串
            if exception_messages:
                exception_text = "\n异常信息：\n" + '\n'.join(exception_messages)
            else:
                exception_text = ""

            # 更新界面
            self.update_text_edits(text, processed_text, exception_text, exception_state, variables)

            # 重置 is_interact 为 False
            self.is_interact = False

    # 冗余一个CM类中的修改后文本提取，用于"，已互动"的构建
    def generate_processed_text(self, variables):
        processed_text = ''
        if variables.get('特殊标志'):
            processed_text += f"{variables['特殊标志']}\n"
        if variables.get('特殊情况'):
            processed_text += f"{variables['特殊情况']}\n"
        # 添加其他字段
        processed_text += f"来源：{variables.get('来源', '')}\n"
        processed_text += f"时间：{variables.get('时间', '')}\n"
        processed_text += f"作者：{variables.get('作者', '')}\n"
        processed_text += f"标题：{variables.get('标题', '')}\n"
        processed_text += f"链接：{variables.get('链接', '')}\n"
        processed_text += f"{variables.get('评转赞', '')}\n"
        processed_text += f"IP属地：{variables.get('IP属地', '')}\n"

        processed_text += f"\n内容：{variables.get('内容', '')}\n"

        # 如果有多条报送链接
        if variables.get('多条报送'):
            processed_text += "\n链接：\n"
            for report in variables['多条报送']:
                processed_text += report + '\n'

        if variables.get('舆论分析'):
            processed_text += "\n舆论分析：\n"
            for report in variables['舆论分析']:
                processed_text += report + '\n'

        return processed_text

    # 复制右侧文本框内容到剪贴板
    def copy_right_text(self):
        clipboard = QApplication.clipboard()
        full_text = self.text_edit_right.toPlainText()
        # 移除异常信息
        if "\n异常信息：\n" in full_text:
            processed_text_only = full_text.split("\n异常信息：\n")[0]
        else:
            processed_text_only = full_text
        clipboard.setText(processed_text_only)

    # 提取小红书号
    def copy_useId_text(self):
        if self.variables and 'userId' in self.variables:
            special = self.variables['userId']
            clipboard = QApplication.clipboard()
            clipboard.setText(special)

    # 提取单号
    def copy_special_text(self):
        if self.variables and '特殊情况' in self.variables:
            special = self.variables['特殊情况']
            # 括号不一定出现
            if '（' in special:
                special = special[(special.find('：') + 1):(special.rfind('（'))]
            else:
                special = special[(special.find('：') + 1):]
            clipboard = QApplication.clipboard()
            clipboard.setText(special)

    # 提取作者名
    def copy_author_text(self):
        if self.variables and '作者' in self.variables:
            author_name = self.variables['作者']
            if '（' in author_name:
                author_name = author_name[:author_name.find('（')]
            clipboard = QApplication.clipboard()
            clipboard.setText(author_name)

    # 提取链接
    def copy_lianjie_text(self):
        if self.variables and '链接' in self.variables:
            web = self.variables['链接']
            clipboard = QApplication.clipboard()
            clipboard.setText(web)

    # 提取时间
    def copy_time_text(self):
        if self.variables and '时间' in self.variables:
            time = self.variables['时间']
            clipboard = QApplication.clipboard()
            clipboard.setText(time)

    # 提取标题
    def copy_title_text(self):
        if self.variables and '标题' in self.variables:
            title = self.variables['标题']
            clipboard = QApplication.clipboard()
            clipboard.setText(title)

    # 提取内容
    def copy_content_text(self):
        if self.variables and '内容' in self.variables:
            content = self.variables['内容']
            # 提取“反馈”后和“，共”前的内容
            if '反馈' in content and '，共' in content:
                content = content[content.find('反馈') + 2:content.rfind('，共')]
            clipboard = QApplication.clipboard()
            clipboard.setText(content)

    # 切换置顶状态的方法
    def toggle_always_on_top(self):
        # 保存当前窗口的大小和位置
        self.window_geometry = self.geometry()

        if self.pin_button.isChecked():
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
            self.always_on_top = True
        else:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
            self.always_on_top = False

        self.show()

        # 恢复窗口的大小和位置
        self.setGeometry(self.window_geometry)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 更新窗口大小和位置
        self.window_geometry = self.geometry()

    def moveEvent(self, event):
        super().moveEvent(event)
        # 更新窗口大小和位置
        self.window_geometry = self.geometry()

    def change_font_size_combo(self):
        value = int(self.font_size_combo.currentText())
        font = QFont(self.custom_font_family)
        font.setPointSize(value)
        # 更新文本框内文字的字体
        self.text_edit_left.setFont(font)
        self.text_edit_right.setFont(font)

    def update_text_edits(self, original_text, processed_text, exception_text, exception_state, variables):
        try:
            self.original_text = original_text
            self.variables = variables  # 保存变量
            self.text_edit_left.setPlainText(original_text)
            self.text_edit_right.setPlainText(processed_text + exception_text)
            # 根据异常状态更改右侧文本框的背景颜色
            if exception_state:
                # 设置背景色为淡红色
                self.text_edit_right.setStyleSheet("QTextEdit { background-color: rgb(255, 200, 200); }")
            else:
                # 恢复默认背景色
                self.text_edit_right.setStyleSheet("")
        except Exception as e:
            print(f"update_text_edits encountered an error: {e}")

    # 切换声量报错检查的方法
    def toggle_error_check(self, checked):
        self.enable_volume_check = checked
        self.clipboard_monitor.enable_volume_check = checked

    # 时间
    

    def closeEvent(self, event):
        # 获取当前时间
        current_time = datetime.now().time()
        def is_time_in_range(start, end, current):
            """
            检查当前时间是否在[start, end]范围内。
            如果start <= end，直接比较。
            如果start > end，表示时间范围跨越午夜，需要特殊处理。
            """
            if start <= end:
                return start <= current <= end
            else:  # 跨越午夜
                return current >= start or current <= end
        # 定义时间范围
        range1_start = time(17, 25)  # 下午 5:25
        range1_end = time(17, 35)    # 下午 5:35
        range2_start = time(23, 59)  # 下午 11:59
        range2_end = time(0, 30)     # 上午 00:30

        # 检查当前时间是否在任一时间范围内
        if (is_time_in_range(range1_start, range1_end, current_time) or
            is_time_in_range(range2_start, range2_end, current_time)):
            title = '下班咯886'
        else:
            title = '还没下班，别跑！'

        # 创建消息框
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle(title)  # 动态设置标题
        msgBox.setText('确定要关闭小彭吗？')
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        
        # 加载并调整图标大小
        icon_path = '641.ico'
        msgBox.setWindowIcon(QIcon(icon_path))
        pixmap = QPixmap(icon_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        msgBox.setIconPixmap(pixmap)
        
        # 设置对话框的窗口标志，确保其在顶层显示
        msgBox.setWindowFlags(msgBox.windowFlags() | Qt.WindowStaysOnTopHint)
        
        # 显示对话框并获取用户响应
        reply = msgBox.exec_()
        
        if reply == QMessageBox.Yes:
            event.accept()  # 允许关闭
        else:
            event.ignore()  # 取消关闭