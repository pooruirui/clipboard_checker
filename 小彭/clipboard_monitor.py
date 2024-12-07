# clipboard_monitor.py

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication
import time
from split_storage import SplitStorage
from variable_checker import VariableChecker

class ClipboardMonitor(QThread):
    content_changed = pyqtSignal(str, str, str, bool, dict)  # (原始文本, 处理后的内容, 异常信息, 异常状态, variables)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.clipboard = QApplication.clipboard()
        self.last_valid_text = ""  # 保存上一次有效的原始文本
        self.enable_volume_check = False  # 初始化声量检查开关

    def run(self):
        while True:
            try:
                text = self.clipboard.text()
                if text != self.last_valid_text:
                    if self.is_valid_text(text):
                        processed_text, exception_text, exception_state, variables = self.process_text(text)
                        self.last_valid_text = text
                        self.content_changed.emit(text, processed_text, exception_text, exception_state, variables)
                    else:
                        pass
                time.sleep(0.1)  # 每0.1秒检查一次剪贴板
            except Exception as e:
                print(f"ClipboardMonitor encountered an error: {e}")

    def is_valid_text(self, text):
        #检查文本是否以指定的关键词开头
        keywords = ['单号', '互动量', '来源', '历史', '新增发帖', '新增发布',]
        if any(text.startswith(keyword) for keyword in keywords) or any(text.startswith('\n' + keyword) for keyword in keywords):
            # 新增条件判断
            if text.startswith('单号'):
                if '\n' not in text and '来源' not in text:
                    return False
            return True
        else:
            return False

    def process_text(self, text):
        try:
            # 使用传入的 text 创建 SplitStorage 实例
            storage = SplitStorage(text)
            variables = storage.get_variables()
            # 使用 VariableChecker 检查变量
            checker = VariableChecker(variables)
            variables, exception_state, exception_messages = checker.check_variables(enable_volume_check=self.enable_volume_check)

            # 构建处理后的内容（不含异常信息）
            processed_text = ''
            if variables['特殊标志']:
                processed_text += f"{variables['特殊标志']}\n"
            if variables['特殊情况']:
                processed_text += f"{variables['特殊情况']}\n"

            processed_text += f"来源：{variables['来源']}\n"
            processed_text += f"时间：{variables['时间']}\n"
            processed_text += f"作者：{variables['作者']}\n"
            processed_text += f"标题：{variables['标题']}\n"
            processed_text += f"链接：{variables['链接']}\n"
            processed_text += f"{variables['评转赞']}\n"
            processed_text += f"IP属地：{variables['IP属地']}\n"
            processed_text += f"\n内容：{variables['内容']}\n"

            # 添加多条报送链接
            if variables['多条报送']:
                processed_text += "\n链接：\n"
                for report in variables['多条报送']:
                    processed_text += report + '\n'

            if variables['舆论分析']:
                processed_text += "\n舆论分析：\n"
                for report in variables['舆论分析']:
                    processed_text += report + '\n'

            # 构建异常信息字符串
            if exception_messages:
                exception_text = "\n异常信息：\n" + '\n'.join(exception_messages)
            else:
                exception_text = ""

            return processed_text, exception_text, exception_state, variables

        except Exception as e:
            print(f"process_text encountered an error: {e}")
            return "", "", True, {}  # 返回异常状态