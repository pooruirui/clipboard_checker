# variable_checker.py

from hw.huawei_crawler import fetch_huawei_data  
from xhs.xhs_crawler import fetch_xhs_data 

class VariableChecker:
    def __init__(self, variables):
        self.variables = variables
        self.exception_state = False  # 异常状态标志
        self.exception_messages = []  # 存储异常信息
        self.interacted = False

    def check_variables(self, enable_volume_check=False, is_interact=False):
        
        source = self.variables.get('来源', '').strip()
        if source in ['花粉论坛', '华为论坛']:
            self.hw_fetch_and_compare_data()
        if source in ['小红书']:
            self.xhs_fetch_and_compare_data()    
        # 这里优先调用内容检查避免内容中的阵地与来源中的阵地无法对齐
        self.check_content(is_interact=is_interact)
        self.check_links()
        self.check_source()
        # 自动调用数据获取和比较方法
        self.check_author()
        self.check_title()
        self.check_engagement()
        self.check_ip_location()
        self.check_sentiment_analysis()
        
        if enable_volume_check:
            self.check_volume()
        # 返回可能被修改的变量、异常状态和异常信息
        return self.variables, self.exception_state, self.exception_messages

    # 建类存储这些爬虫检查方法
    def xhs_fetch_and_compare_data(self):
        import re
        link = self.variables.get('链接', '').strip()
        # print(link)
        if not link:
            self.exception_state = True
            self.exception_messages.append('链接为空，无法获取数据')
            return
        # 调用xhs_crawler 获取数据
        new_post_link, redId, ip, nickname, fans, likecnt, sharecnt, commentcnt, logged, is_deleted= fetch_xhs_data(link)

        # 待加入互动判断

        # 判断帖子是否删除       
        if is_deleted:
            # 帖子已删除，设置特殊标志或提示信息
            self.variables['特殊标志'] = '链接状态未知'
            self.exception_state = True
            self.exception_messages.append('请更新cookies或核查帖子是否删除')
            # 可以根据需要清空相关字段或保留原有数据
            return
        
        # 比较并更新 作者 和 粉丝数
        author = self.variables.get('作者', '').strip()
        if '（粉丝数' in author:
            existing_author_name = author.split('（粉丝数')[0].strip()
            existing_fans = re.search(r'粉丝数([\d\.]+w?)', author)
            existing_fans = existing_fans.group(1) if existing_fans else ''
        else:
            existing_author_name = author
            existing_fans = ''

        # 检查作者名
        if not existing_author_name:
            self.variables['作者'] = f"{nickname}（粉丝数{fans}）"
            self.exception_state = True
            self.exception_messages.append('作者已填充')
        elif existing_author_name != nickname:
            self.variables['作者'] = f"{nickname}（粉丝数{fans}）"
            self.exception_state = True
            self.exception_messages.append('作者已更新')
        else:
            # 作者名相同，检查粉丝数
            if not existing_fans:
                self.variables['作者'] = f"{existing_author_name}（粉丝数{fans}）"
                self.exception_state = True
                self.exception_messages.append('粉丝数已填充')
            elif existing_fans != str(fans):
                self.variables['作者'] = f"{existing_author_name}（粉丝数{fans}）"
                self.exception_state = True
                self.exception_messages.append('粉丝数已更新')

        # 检查 IP属地
        existing_ip = self.variables.get('IP属地', '').strip()
        if not existing_ip:
            self.variables['IP属地'] = ip
            self.exception_state = True
            self.exception_messages.append('IP属地已填充')
        elif existing_ip != ip:
            self.variables['IP属地'] = ip
            self.exception_state = True
            self.exception_messages.append('IP属地已更新')

        # 检查 评转赞
        engagement = self.variables.get('评转赞', '').strip()
        pattern = r'评论(\d+)转发(\d+)点赞(\d+)'
        match = re.match(pattern, engagement)
        if not match:
            # 原数据缺失或格式错误，直接更新
            self.variables['评转赞'] = f"评论{commentcnt}转发{sharecnt}点赞{likecnt}"
            self.exception_state = True
            self.exception_messages.append('评转赞已填充')
        else:
            existing_comments, existing_shares, existing_likes = map(str, match.groups())

            updates = []
            if existing_comments != str(commentcnt):
                updates.append('评论数')
            if existing_shares != str(sharecnt):
                updates.append('转发数')
            if existing_likes != str(likecnt):
                updates.append('点赞数')
            if updates:
                self.variables['评转赞'] = f"评论{commentcnt}转发{sharecnt}点赞{likecnt}"
                self.exception_state = True
                self.exception_messages.append('、'.join(updates) + '已更新')

        # 登陆状态 # 这里新增一个检测登陆状态但无法访问帖子的账号封禁返回
        if not logged:
            self.exception_state = True
            self.exception_messages.append("当前登录状态失效，请使用小红书登录获取新的登陆状态，并重启该程序")
        else:
            pass

        # 更新单独的互动量字段
        print("VC",redId)
        self.variables['userId'] = redId
        self.variables['链接'] = new_post_link
        self.variables['评论数'] = int(commentcnt)
        self.variables['转发数'] = int(sharecnt)
        self.variables['点赞数'] = int(likecnt)

    def hw_fetch_and_compare_data(self):
        import re
        link = self.variables.get('链接', '').strip()
        if not link:
            self.exception_state = True
            self.exception_messages.append('链接为空，无法获取数据')
            return
        # 从链接中提取 threadId
        match = re.search(r'id_(\d+)', link)
        if not match:
            self.exception_state = True
            self.exception_messages.append('无法从链接中提取 threadId')
            return
        thread_id = match.group(1)
        # 调用 huawei_crawler 获取数据
        hid, ip, nickname, fans, likecnt, sharecnt, commentcnt, interacted, is_deleted = fetch_huawei_data(thread_id)
        self.interacted = interacted

        if is_deleted:
            # 帖子已删除，设置特殊标志或提示信息
            self.variables['特殊标志'] = '该帖子已删除'
            self.exception_state = True
            self.exception_messages.append('帖子已删除')
            # 可以根据需要清空相关字段或保留原有数据
            return

        # 比较并更新 作者 和 粉丝数
        author = self.variables.get('作者', '').strip()
        if '（粉丝数' in author:
            existing_author_name = author.split('（粉丝数')[0].strip()
            existing_fans = re.search(r'粉丝数([\d\.]+w?)', author)
            existing_fans = existing_fans.group(1) if existing_fans else ''
        else:
            existing_author_name = author
            existing_fans = ''

        # 检查作者名
        if not existing_author_name:
            self.variables['作者'] = f"{nickname}（粉丝数{fans}）"
            self.exception_state = True
            self.exception_messages.append('作者已填充')
        elif existing_author_name != nickname:
            self.variables['作者'] = f"{nickname}（粉丝数{fans}）"
            self.exception_state = True
            self.exception_messages.append('作者已更新')
        else:
            # 作者名相同，检查粉丝数
            if not existing_fans:
                self.variables['作者'] = f"{existing_author_name}（粉丝数{fans}）"
                self.exception_state = True
                self.exception_messages.append('粉丝数已填充')
            elif existing_fans != str(fans):
                self.variables['作者'] = f"{existing_author_name}（粉丝数{fans}）"
                self.exception_state = True
                self.exception_messages.append('粉丝数已更新')

        # 检查 IP属地
        existing_ip = self.variables.get('IP属地', '').strip()
        if not existing_ip:
            self.variables['IP属地'] = ip
            self.exception_state = True
            self.exception_messages.append('IP属地已填充')
        elif existing_ip != ip:
            self.variables['IP属地'] = ip
            self.exception_state = True
            self.exception_messages.append('IP属地已更新')

        # 检查 评转赞
        engagement = self.variables.get('评转赞', '').strip()
        pattern = r'评论(\d+)转发(\d+)点赞(\d+)'
        match = re.match(pattern, engagement)
        if not match:
            # 原数据缺失或格式错误，直接更新
            self.variables['评转赞'] = f"评论{commentcnt}转发{sharecnt}点赞{likecnt}"
            self.exception_state = True
            self.exception_messages.append('评转赞已填充')
        else:
            existing_comments, existing_shares, existing_likes = map(int, match.groups())
            updates = []
            if existing_comments != int(commentcnt):
                updates.append('评论数')
            if existing_shares != int(sharecnt):
                updates.append('转发数')
            if existing_likes != int(likecnt):
                updates.append('点赞数')
            if updates:
                self.variables['评转赞'] = f"评论{commentcnt}转发{sharecnt}点赞{likecnt}"
                self.exception_state = True
                self.exception_messages.append('、'.join(updates) + '已更新')

        # 更新单独的互动量字段
        self.variables['userId'] = hid
        self.variables['评论数'] = int(commentcnt)
        self.variables['转发数'] = int(sharecnt)
        self.variables['点赞数'] = int(likecnt)

    def check_volume(self):
        # 如果来源不为 '人民网'、'花粉论坛'，且评论数大于等于30，特殊情况为空时，抛出报错
        source = self.variables.get('来源', '').strip()
        comments = int(self.variables.get('评论数', 0))
        special_case = self.variables.get('特殊情况', '').strip()

        if source not in ['人民网', '花粉论坛'] and comments >= 30 and not special_case:
            self.exception_state = True
            self.exception_messages.append('声量大于30请建单')

    def check_source(self):
        # 来源检查，替换特殊阵地的输出表述
        source = self.variables.get('来源', '').strip()
        a = 0
        if not source:
            self.exception_state = True
            self.exception_messages.append('来源为空')
        else:
            if source == '百度百家':
                self.variables['来源'] = '百家号'
                a = 1
            elif source == '腾讯':
                self.variables['来源'] = 'QQ浏览器'
                a = 1
            elif source == '华为论坛':
                self.variables['来源'] = '花粉论坛'
                a = 1
            elif sorted == '抖音app':
                self.variables['来源'] = '抖音'
        if a == 1:
            self.exception_state = True
            self.exception_messages.append('来源已修改')
    
    def check_author(self):
        import re
        author = self.variables.get('作者', '').strip()
        # print(f"Checking author: {author}")

        if not author:
            self.exception_state = True
            self.exception_messages.append('作者为空')
            return

        if '（粉丝数' not in author:
            self.exception_state = True
            self.exception_messages.append('粉丝数缺失')

        # 检查粉丝数格式
        if '（粉丝数' in author and '）' in author:
            # 提取作者名称和粉丝信息
            author_name = author.split('（粉丝数')[0].strip()
            fans_info = author[author.find('（粉丝数'):].strip()

            # 检查作者名称是否为空
            if not author_name:
                self.exception_state = True
                self.exception_messages.append('作者名称为空')
                # 根据需求选择是否继续处理
                # return  # 如果需要在作者名称为空时停止处理，可以取消注释这行

            # 提取粉丝数，包括可能的“未识别”
            match = re.search(r'粉丝数([\d\.]+w?|未识别)', fans_info, re.IGNORECASE)
            if match:
                fans_count_str = match.group(1)

                if fans_count_str.lower() == "未识别":
                    # 粉丝数未识别，不抛出异常
                    pass
                else:
                    if 'w' in fans_count_str.lower():
                        # 处理包含“w”的粉丝数
                        num_part = fans_count_str.lower().replace('w', '')
                        if '.' not in num_part:
                            # 如果是整数，添加 .0w
                            simplified_count = f"{num_part}.0w"
                        else:
                            # 保持原有格式
                            simplified_count = fans_count_str.lower()

                        # 检查是否需要更新
                        if simplified_count != fans_count_str.lower():
                            self.variables['作者'] = f"{author_name}（粉丝数{simplified_count}）"
                            self.exception_state = True
                            self.exception_messages.append('我有强迫症')
                        else:
                            # 已经包含“w”且格式正确，不处理
                            pass
                    else:
                        try:
                            fans_count = float(fans_count_str)
                            if fans_count >= 10000:
                                # 进行简化处理
                                simplified_count = f"{fans_count / 10000:.1f}w"
                                # 如果是整数，确保有一位小数
                                if simplified_count.endswith('.0w'):
                                    simplified_count = simplified_count[:-3] + 'w'
                                # 替换粉丝数
                                self.variables['作者'] = f"{author_name}（粉丝数{simplified_count}）"
                                self.exception_state = True
                                self.exception_messages.append('粉丝数已简化')
                            else:
                                # 不处理小于10000的粉丝数
                                pass
                        except ValueError:
                            self.exception_state = True
                            self.exception_messages.append('粉丝数格式错误')
            else:
                # 未匹配到粉丝数，但如果包含“粉丝数未识别”，不抛出异常
                if '粉丝数未识别' in fans_info:
                    # 粉丝数未识别，不抛出异常
                    pass
                else:
                    # 其他情况，抛出异常
                    self.exception_state = True
                    self.exception_messages.append('粉丝数未识别')
        else:
            self.exception_state = True
            self.exception_messages.append('作者格式不正确')


    def check_title(self):
        # 处理标题中的内容
        title = self.variables.get('标题', '').strip()
        if not title:
            self.exception_state = True
            self.exception_messages.append('标题为空')
            return
        # 执行复杂的重复内容检查
        # 缺失逻辑：若文本为A(A+B),无法提取(A+B)中的A与前方A的重复文本检查
        length = len(title)
        if length >= 10:  # 确保标题足够长
            a =0.4
            while a <= 0.6:
                index_40 = int(length * 0.4)
                part_a = title[:index_40]
                part_b = title[index_40:]
                # 检查 part_a 是否在 part_b 中出现
                if part_a in part_b:
                    self.exception_state = True
                    self.exception_messages.append('标题存在重复内容')
                    break
                a+=0.01
        else:
            # 标题过短，跳过此检查
            pass

    def check_engagement(self):
        import re
        engagement = self.variables.get('评转赞', '').strip()
        # 定义严格匹配的正则表达式
        strict_pattern = r'^评论(\d+)转发(\d+)点赞(\d+)$'
        match = re.match(strict_pattern, engagement)
        if match:
            # 如果整体匹配成功，提取评论、转发、点赞数
            try:
                comments, shares, likes = map(int, match.groups())
                self.variables['评论数'] = comments  # 保存评论数
                self.variables['转发数'] = shares    # 保存转发数
                self.variables['点赞数'] = likes     # 保存点赞数
            except ValueError:
                # 这一步通常不会触发，因为正则已经确保了都是数字
                self.exception_state = True
                self.exception_messages.append('评转赞中存在非数字')
        else:
            # 整体匹配失败，进一步检查具体是哪一部分有问题
            # 定义单独匹配每个部分的正则表达式
            comment_pattern = r'^评论(\d+)(?!\d)'
            share_pattern = r'转发(\d+)(?!\d)'
            like_pattern = r'点赞(\d+)(?!\d)'

            comment_match = re.search(comment_pattern, engagement)
            share_match = re.search(share_pattern, engagement)
            like_match = re.search(like_pattern, engagement)

            # 检查每个部分是否存在并且格式正确
            errors = []
            # 检查“评论”部分
            if not comment_match or comment_match.group(1) != re.search(r'评论(\d+)', engagement).group(1):
                errors.append('评论格式错误')
            # 检查“转发”部分
            if not share_match or share_match.group(1) != re.search(r'转发(\d+)', engagement).group(1):
                errors.append('转发格式错误')
            # 检查“点赞”部分
            if not like_match or like_match.group(1) != re.search(r'点赞(\d+)', engagement).group(1):
                errors.append('点赞格式错误')

            if errors:
                # 如果有具体的部分格式错误，记录相应的错误信息
                for error in errors:
                    if error not in self.exception_messages:
                        self.exception_state = True
                        self.exception_messages.append(error)
            else:
                # 如果没有具体的部分格式错误，记录整体格式错误
                self.exception_state = True
                self.exception_messages.append('评转赞格式不正确')

    def check_ip_location(self):
        ip_location = self.variables.get('IP属地', '').strip()

        if not ip_location:
            self.exception_state = True
            self.exception_messages.append('IP属地为空')
            return  # 结束方法
        else:
            original_ip = ip_location  # 保存原始 IP 属地
            # 特殊处理自治区和特别行政区
            special_regions = {
                '内蒙古自治区': '内蒙古',
                '广西壮族自治区': '广西',
                '西藏自治区': '西藏',
                '宁夏回族自治区': '宁夏',
                '新疆维吾尔自治区': '新疆',
                '香港特别行政区': '香港',
                '澳门特别行政区': '澳门'
            }
            if ip_location in special_regions:
                self.variables['IP属地'] = special_regions[ip_location]
                if self.variables['IP属地'] != original_ip:
                    self.exception_state = True
                    self.exception_messages.append('IP属地已修改')
            else:
                # 删除“省”和“市”
                if ip_location.endswith('省') or ip_location.endswith('市'):
                    self.variables['IP属地'] = ip_location[:-1]
                    if self.variables['IP属地'] != original_ip:
                        self.exception_state = True
                        self.exception_messages.append('IP属地已修改')

            # 核查IP属地是否正确
            try:
                with open('地址.txt', 'r', encoding='utf-8') as file:
                    # 读取文件内容
                    content = file.read()
            except:
                with open('小彭/地址.txt', 'r', encoding='utf-8') as file:
                    # 读取文件内容
                    content = file.read()
            if self.variables['IP属地'] not in content:
                self.exception_state = True
                self.exception_messages.append('IP属地不合理，请订正')


    def check_content(self, is_interact=False):
        # 核心内容、BUG多发
        import re
        content = self.variables.get('内容', '').strip()
        if not content:
            self.exception_state = True
            self.exception_messages.append('内容为空')
            return  # 结束方法

        # 移除可能存在的“内容：”前缀
        if content.startswith('内容：') or content.startswith('内容:'):
            content = content[3:].strip()

        # 分离“内容”和“链接”，可能存在
        if '\n链接：' in content or '\n链接:' in content:
            content_part, links_part = re.split(r'\n链接[:：]', content, maxsplit=1)
        else:
            content_part = content

        # 提取原有的篇数
        match = re.search(r'共监测到(\d+)篇', content_part)
        if match:
            original_count = int(match.group(1))
        else:
            original_count = None  # 如果未找到，设置为 None

        # 检查是否存在篇数位置异常
        if '共监测到篇1' in content_part or '共监测1到篇' in content_part:
            self.exception_state = True
            self.exception_messages.append('篇数位置异常')

        # 计算新的篇数
        article_count = 1 + len(self.variables.get('多条报送', []))

        # 移除现有的“共监测到X篇”和“已互动”
        content_part = re.sub(r'(，)?共监测到\d*篇', '', content_part)
        content_part = content_part.strip('共监测到篇').strip('共监测到篇1').strip('共监测1到篇')
        content_part = re.sub(r'(，)?已互动', '', content_part)

        # 比较原有篇数和新的篇数
        if original_count is not None and original_count != article_count:
            self.exception_state = True
            self.exception_messages.append(f'篇数与原始篇数不一致，原始篇数为{original_count}，重新计算为{article_count}')

        # 定义 markers 和 markers_inside
        markers = ['产品问题', '服务问题', '销售问题', '用户口碑', 'GoToMarketing', '市场进入', 'GoToMarket', '网络安全', '市场营销']
        markers_inside = ['用户反馈', '用户反映', '用户表达', '用户认为', '用户询问']

        # 对 markers 和 markers_inside 进行排序
        markers.sort(key=lambda x: -len(x))

        # 创建正则表达式模式
        marker_pattern = r'({})[:：]'.format('|'.join(map(re.escape, markers)))

        # 查找 markers 的匹配项
        matches = list(re.finditer(marker_pattern, content_part))
        positions = [(match.start(), match.end(), match.group()) for match in matches]

        # 根据匹配项的位置进行处理
        if positions:
            # 按开始位置排序
            positions.sort(key=lambda x: x[0])
            latest_end = positions[-1][1]
            # 截取 latest_end 之后的内容
            specific_content = content_part[latest_end:].strip()
        else:
            specific_content = content_part.strip()

        # 媒体名替换，使用来源变量
        source = self.variables.get('来源', '').strip()

        # 应用媒体名的替换规则
        media_aliases = {
            '百度百家': '百家号',
            '腾讯': 'QQ浏览器',
            '华为论坛': '花粉论坛',
            '抖音app': '抖音',
            '今日头条app': '今日头条',
            # 可以根据需要继续添加映射关系
        }
        if source in media_aliases:
            media_name = media_aliases[source]
            if media_name not in ['抖音app', '抖音']:
                self.exception_state = True
                self.exception_messages.append(f'来源已修改为{media_name}')
        else:
            media_name = source

        # 如果媒体名发生了变化，替换内容中的旧来源名称
        if source != media_name:
            specific_content = specific_content.replace(source, media_name)
            specific_content = specific_content.strip()

        # 优先移除原始的来源名称
        if specific_content.startswith(source):
            specific_content = specific_content[len(source):].strip()
        elif specific_content.startswith(media_name):
            specific_content = specific_content[len(media_name):].strip()

        # 移除“用户反馈”前可能存在的冒号
        if specific_content.startswith('用户反馈：') or specific_content.startswith('用户反馈:'):
            specific_content = specific_content[4:].strip()
        elif specific_content.startswith('用户反馈'):
            specific_content = specific_content[4:].strip()
            
        # 调整“语言通畅”处理逻辑
        if (specific_content.startswith('用户') or specific_content.startswith('反映') or specific_content.startswith('认为')) and not specific_content.startswith('用户反馈'):
            specific_content = specific_content[2:].strip()
            self.exception_state = True
            self.exception_messages.append('修改语言通畅')

        # 移除 specific_content 末尾的逗号或其他标点符号
        specific_content = specific_content.rstrip('，。！？；：:')

        # 构建新的内容
        new_content = f'{media_name}用户反馈{specific_content}，共监测到{article_count}篇'

        # 如果原内容包含“已互动”，则保留
        # 通过评论区传递的interacted判断是否增加已互动
        if '已互动' in content or '已互动' in content_part or '已互动' in specific_content:
            new_content += '，已互动'
        elif is_interact:
            # 如果 is_interact 为 True，则添加“，已互动”
            new_content += '，已互动'
        elif self.interacted:
            new_content += '，已互动'
            self.exception_state = True
            self.exception_messages.append('更新互动状态')

        self.variables['内容'] = new_content


    def check_sentiment_analysis(self):
        import re
        analysis_list = self.variables.get('舆论分析', [])
        if analysis_list:
            total_percentage = 0
            analysis_items = []
            percentages = []
            for idx, item in enumerate(analysis_list):
                # 提取百分比值和内容
                match = re.match(r'(\d+)%(.+)', item)
                if match:
                    percentage = int(match.group(1))
                    percentages.append(percentage)
                    content = match.group(2).strip()
                    total_percentage += percentage
                    analysis_items.append({'original_order': idx, 'percentage': percentage, 'content': content})
                else:
                    # 未找到百分比，抛出异常
                    self.exception_state = True
                    self.exception_messages.append(f'舆论分析项缺少百分比：{item}')
            # 检查总和是否为100
            if total_percentage != 100:
                self.exception_state = True
                self.exception_messages.append(f'舆论分析百分比总和为{total_percentage}%，不等于100%')
            if percentages != sorted(percentages, reverse=True):
                self.exception_state = True
                self.exception_messages.append('舆论分析百分比未按降序排列')
            # 对分析项按百分比降序排列            
            analysis_items.sort(key=lambda x: x['percentage'], reverse=True)
            # 生成排序后的舆论分析列表
            sorted_analysis_list = [f"{item['percentage']}%{item['content']}" for item in analysis_items]
            self.variables['舆论分析'] = sorted_analysis_list
        else:
            # 舆论分析列表为空，根据需求决定是否处理
            pass

    def check_links(self):
        import re
        reports = self.variables.get('多条报送', [])
        for report in reports:
            # 检查是否包含括号部分
            match = re.search(r'（(.*)）$', report)
            if match:
                parentheses_content = match.group(1)
                # 检查括号内的格式是否符合要求
                # 要求格式：任意字符串 + '，' + '评论' + 数字
                if re.match(r'.+，评论\d+$', parentheses_content):
                    continue  # 格式正确，继续检查下一条
                else:
                    self.exception_state = True
                    self.exception_messages.append('多条报送格式错误')
                    break  # 发现错误，停止检查
            else:
                self.exception_state = True
                self.exception_messages.append('多条报送格式错误')
                break  # 发现错误，停止检查
