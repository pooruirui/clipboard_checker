# split_storage.py

class SplitStorage:
    def __init__(self, text):
        self.text = text
        self.variables = {}
        self.exception_state = False  # 初始化异常状态
        self.exception_messages = []  # 初始化异常信息列表
        self.parse_clipboard_text()

    def parse_clipboard_text(self):
        import re
        # 初始化存储变量的字典
        self.variables = {
            'userId': '', # 存储各平台用户号，若存在
            '特殊标志': '',  # 用于存储 互动量超时、互动量上涨x次预警、历史数据回溯、新增发帖/布
            '特殊情况': '',  # 用于存储 单号
            '来源': '',
            '时间': '',
            '作者': '',
            '标题': '',
            '链接': '',
            '评转赞': '',
            'IP属地': '',
            '内容': '',
            '多条报送': [],  # 多条报送与舆论分析使用列表存储
            '舆论分析': []
        }

        # 以下为提取复切板主要逻辑
        # 读取剪切板内容，提取识别文本换行，按list存储并规范化存储入字典
        # 将文本按行分割
        lines = self.text.strip().split('\n')
        total_lines = len(lines)
        i = 0

        # 处理第一行和第二行的特殊情况
        nums = ['二', '三', '四', '五', '六', '七', '八']
        if i < total_lines and lines[i].strip() == '互动量超时':
            self.variables['特殊标志'] = '互动量超时'
            i += 1
        elif i < total_lines and lines[i].strip() == '历史数据回溯':
            self.variables['特殊标志'] = '历史数据回溯'
            i += 1
        elif i < total_lines and lines[i].strip() == '新增发布' or total_lines and lines[i].strip() == '新增发帖':
            self.variables['特殊标志'] = '新增发帖'
            i += 1
        # 快速调用定义nums处理多次预警信息
        elif i < total_lines and any(lines[i].strip() == f'互动量上涨{num}次预警' for num in nums):
            self.variables['特殊标志'] = next(f'互动量上涨{num}次预警' for num in nums if lines[i].strip() == f'互动量上涨{num}次预警')
            i += 1

        if i < total_lines:
            line = lines[i].strip()
            if line.startswith('单号：'):
                self.variables['特殊情况'] = line
                i += 1

        # 继续解析剩余的行
        while i < total_lines:
            line = lines[i].strip()
            if line.startswith('来源：'):
                self.variables['来源'] = line[len('来源：'):].strip()
                i += 1
            elif line.startswith('时间：'):
                self.variables['时间'] = line[len('时间：'):].strip()
                i += 1
            elif line.startswith('作者：'):
                self.variables['作者'] = line[len('作者：'):].strip()
                i += 1
            elif line.startswith('标题：'):
                # 标题可能是多行的，直到下一个键名或结束
                title = line[len('标题：'):].strip()
                i += 1
                while i < total_lines and not lines[i].strip().startswith(('链接：', '评论', '转发', '点赞', 'IP属地：', '内容：')):
                    title += '\n' + lines[i].strip()
                    i += 1
                self.variables['标题'] = title
            elif line.startswith('链接：'):
                self.variables['链接'] = line[len('链接：'):].strip()
                i += 1
            elif '评论' in line and '转发' in line and '点赞' in line:
                self.variables['评转赞'] = line.strip()
                i += 1
            elif line.startswith('IP属地：'):
                self.variables['IP属地'] = line[len('IP属地：'):].strip()
                i += 1
            elif line.startswith('内容：'):
                # 内容可能是多行的，直到 '链接：'、'舆论分析：' 或结束
                content = line[len('内容：'):].strip()
                i += 1
                while i < total_lines and not lines[i].strip().startswith(('链接：', '舆论分析：', '舆情分析：', '情感分析：')):
                    content += '\n' + lines[i].strip()
                    i += 1
                self.variables['内容'] = content

                # 检查是否有 '链接：'（多条报送）
                if i < total_lines and lines[i].strip().startswith('链接：'):
                    i += 1  # 跳过 '链接：' 行
                    # 提取多条报送链接
                    reports = []
                    current_report = ''
                    while i < total_lines and not lines[i].strip().startswith(('舆论分析：', '舆情分析：', '情感分析：')):
                        line = lines[i].strip()
                        if not line:
                            i += 1
                            continue
                        # 检测是否是新的报送开始，例如“微博：”开头
                        if any(line.startswith(platform + '：') for platform in ['微博', '微信', '抖音', '今日头条', '百家号', '百度新闻', '搜狐', '知乎', '哔哩哔哩'
                                                                                , '小红书', '抖音app', '虎扑体育论坛', '花粉论坛', '酷安', '网易手机端', '趣头条'
                                                                                ,]):
                            if current_report:
                                reports.append(current_report.strip())
                            current_report = line  # 开始新的报送
                        else:
                            current_report += '\n' + line
                        i += 1
                    # 将最后一个报送添加到列表中
                    if current_report:
                        reports.append(current_report.strip())
                    self.variables['多条报送'] = reports


                # 检查是否有 '舆论分析：' 或 '舆情分析：' 或 '情感分析：'
                if i < total_lines and lines[i].strip().startswith(('舆论分析：', '舆情分析：', '情感分析：')):
                    analysis_header = lines[i].strip()
                    # 检查冒号后是否跟随换行符
                    if analysis_header.endswith('：'):
                        i += 1  # 跳过 '舆论分析：' 行
                    else:
                        # 冒号后有内容，抛出异常
                        self.exception_state = True
                        self.exception_messages.append('情感分析无换行')
                        i += 1  # 仍然需要跳过当前行

                    # 提取舆论分析数据
                    while i < total_lines and lines[i].strip():
                        self.variables['舆论分析'].append(lines[i].strip())
                        i += 1
                
            else:
                i += 1  # 确保索引递增
        
        # 调试输出
        print(self.variables)
        print('***************************************************************************')
        print('***************************************************************************')
        
        return self.variables

        

    def get_variables(self):
        return self.variables
