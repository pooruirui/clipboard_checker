# hw/huawei_crawler.py

import requests
import json

# global两个重要参数便于维护就不建类了
global post_SGW_APP_ID # post_page 1.2
global user_SGW_APP_ID # home_page 2
post_SGW_APP_ID = "5881CD5912A8D0AA39AEC96F2EC2388A" 
user_SGW_APP_ID = "EDCF82D77A5AB59706CD5F2163F67427"

def fetch_huawei_data(thread_id):
    # 发包固定格式
    headers = {
        "SGW-APP-ID": f"{post_SGW_APP_ID}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
        "X-Requested-With": "XMLHttpRequest",
        "request-source": "H5"
    }
    url = "https://sgw-cn.c.huawei.com/forward/club/content_h5/queryThreadDetail/1"

    print(f"Thread ID: {thread_id}")
    data_original_article = {
        "threadId": int(thread_id),  # 确保 thread_id 为整数
        "pageIndex": 1,
        "pageSize": 20,
        "orderBy": 1
    }

    post_data = json.dumps(data_original_article, separators=(',', ':'))

    try:
        post_response = requests.post(url, headers=headers, data=post_data)
        post_json = post_response.json()
        
        # 检查 errcode 的值，而不是仅检查其存在
        if post_json.get('errcode') != '0':
            print(f"Error fetching thread: {post_json.get('errmsg')}")
            # 帖子删除的json返回为 {"errcode":"100141000","errmsg":"Thread is not exist"}
            # 在这种情况下，返回六个 None，并返回一个帖子已删除的标志
            return None, None, None, None, None, None, None, False, True  # 多返回一个标志位

        # 用户ID
        userid = post_json["data"]["authorInfo"]["id"]
        # 赞评转
        likecnt = post_json["data"]["likeCnt"]
        commentcnt = post_json["data"]["commentCnt"]
        sharecnt = post_json["data"]["shareCnt"]

        # 帖子发布时的Ip
        post_ip = post_json["data"]["ipLocation"]
        # 评论
        comments = post_json["data"]["postList"]
        # print(comments)

        # 获取评论的二级评论（如果有的话）
        all_comments = []

        for comment in comments:
            replies_count = int(comment["replies"])
            comment_id = comment["commentId"]
            if replies_count > 0:  # 如果有二级评论，则需要获取这些评论
                sub_comments = fetch_sub_comments(thread_id, comment_id)
                all_comments.extend(sub_comments)
            
            # 将该评论本身加入到评论列表中
            all_comments.append(comment)

        # 打印所有评论的数量
        print(f"Total number of comments (including sub-comments): {len(all_comments)}")

        # 进入二级页面
        headers = {
            "SGW-APP-ID": f"{user_SGW_APP_ID}"
        }
        url = "https://sgw-cn.c.huawei.com/forward/myhuawei/bffuserservice_h5/gethome_new/2"
        data_homepage = {
            "userId": f"{userid}"
        }

        data = json.dumps(data_homepage, separators=(',', ':'))
        homepage_response = requests.post(url, headers=headers, data=data)
        homepage_json = homepage_response.json()

        # IP
        ip = homepage_json["data"].get("ipLocation", "")
        # 昵称
        nickname = homepage_json["data"].get("nickName", "")
        # 粉丝数
        fans = homepage_json["data"].get("follower", "")

        interacted = False
        if process_comments(all_comments):
            interacted = True
            print("A match was found.")
        else:
            interacted = False
            print("No match found.")

        print(f"Fetched data from Huawei forum:\nIP属地: {ip}\n昵称: {nickname}\n粉丝数: {fans}")
        return userid, ip, nickname, fans, likecnt, sharecnt, commentcnt, interacted, False  # 帖子存在，标志为 False

    except Exception as e:
        print(f"Error fetching Huawei data: {e}")
        # 如果发生异常，也返回七个个 None，并返回两个异常标志
        return None, None, None, None, None, None, None, False, True  # 标志为 True，表示出现错误
    

# 获取评论的二级评论
def fetch_sub_comments(thread_id, parent_comment_id):
    headers = {
        "Content-Type": "application/json",
        "SGW-APP-ID": "EDCF82D77A5AB59706CD5F2163F67427",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
        "X-Requested-With": "XMLHttpRequest",
        "request-source": "H5"
    }
    url = "https://sgw-cn.c.huawei.com/forward/club/comment_h5/subComment/1"
    data = {
        "topicId": thread_id,
        "parentCommentId": parent_comment_id,
        "pageIndex": 1,
        "pageSize": 20,
        "queryOrder": 1
    }
    data = json.dumps(data, separators=(',', ':'))
    
    try:
        response = requests.post(url, headers=headers, data=data)
        sub_comments_json = response.json()

        if sub_comments_json.get("errcode") == "0":
            return sub_comments_json["data"]  # 返回二级评论列表
        else:
            return []  # 如果没有二级评论，返回空列表

    except Exception as e:
        print(f"Error fetching sub-comments: {e}")
        return []  # 返回空列表，表示获取二级评论失败
    
# 去重并输出评论者的名字    
def process_comments(all_comments):
    names = set()  # 用set去重
    nicknames = set()  # 用set去重，保证唯一

    for comment in all_comments:
        author_info = comment.get("authorInfo", {})
        name = author_info.get("name", None)
        nickname = author_info.get("nickName", None)
        
        if name:
            names.add(name)  # 添加到names集合去重
        if nickname:
            nicknames.add(nickname)  # 添加到nicknames集合去重

    # 输出去重后的names和nicknames
    print("Unique Names:", names)
    print("Unique Nicknames:", nicknames)
    
    # 检查是否有包含特定字符串的昵称或名字
    keywords = ["花粉帮", "帮堂", "帮主"]
    for name in names.union(nicknames):
        if any(keyword in name for keyword in keywords):
            print(f"Match found: {name}")
            return True  # 如果匹配到，返回True
    return False  # 如果没有匹配到，返回False