# xhs/xhs_crawler.py

import requests
import json

# 维护session
global web_session
with open('websession.txt', 'r', encoding='utf-8') as file:
    web_session = file.read()

def fetch_xhs_data(url):
    cookies = {
        "web_session": f"{web_session}",
    }
    try:
        # 网页进入
        post_response = requests.get(url, cookies=cookies)
        post_response = post_response.text
        # print("0")
        into = post_response.find('__INITIAL_STATE__=')
        ending = post_response.find('</script></body></html>')
        post_json = json.loads(post_response[into + len('__INITIAL_STATE__=') : ending].replace("undefined", "null"))

        # 登录失效
        logged = post_json["user"]["loggedIn"]
        
        print(post_json["user"]["loggedIn"])
        # 帖子ID
        noteid = post_json["note"]["firstNoteId"]
        # 用户ID
        userId = post_json["note"]["noteDetailMap"][f"{noteid}"]["note"]["user"]["userId"]
        # 赞评转
        likecnt = post_json["note"]["noteDetailMap"][f"{noteid}"]["note"]["interactInfo"]["likedCount"]
        commentcnt = post_json["note"]["noteDetailMap"][f"{noteid}"]["note"]["interactInfo"]["commentCount"]
        sharecnt = post_json["note"]["noteDetailMap"][f"{noteid}"]["note"]["interactInfo"]["shareCount"]
        # print('1')
        # IP属地
        ip = post_json["note"]["noteDetailMap"][f"{noteid}"]["note"]["ipLocation"]
        # xs校验
        xs = post_json["note"]["noteDetailMap"][f"{noteid}"]["note"]["xsecToken"]
        new_post_link = f'https://www.xiaohongshu.com/explore/{noteid}?xsec_token={xs}&xsec_source=pc_user'
        # 网址替换
        homepage = requests.get(f'https://www.xiaohongshu.com/user/profile/{userId}?xsec_token=&xsec_source=pc_note',cookies=cookies)
        homepage_text = homepage.text
 
        into = homepage_text.find('__INITIAL_STATE__=')
        ending = homepage_text.find('</script></body></html>')
        # print("2")
        homepage_json = json.loads(homepage_text[into + len('__INITIAL_STATE__=') : ending].replace("undefined", "null"))
        fans = homepage_json["user"]["userPageData"]["interactions"][1]["count"]
        nickname = homepage_json["user"]["userPageData"]["basicInfo"]["nickname"]
        redId = homepage_json["user"]["userPageData"]["basicInfo"]["redId"]
        print(redId)
        # print("3")
        # print(web_session)
        
        return new_post_link, redId, ip, nickname, fans, likecnt, sharecnt, commentcnt, logged, False 

    except:

        return None, None, None, None, None, None, None, None, None, True





# 已删除
# http://120.31.140.133:8194/api/v0.5/third/xhs/url_convert?url=https://www.xiaohongshu.com/discovery/item/673295d60000000019016452&uid=5a02f9f511be1014aa8719bf&sign=3EB6843BD8FD9DC49DF5B2C7C2BDBE62

# 登录失效
# ["user"]["loggedIn"] == False