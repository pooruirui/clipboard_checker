import requests


headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9",
    "origin": "https://www.xiaohongshu.com",
    "priority": "u=1, i",
    "referer": "https://www.xiaohongshu.com/",
    "sec-ch-ua": "\"Chromium\";v=\"130\", \"Microsoft Edge\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    "x-b3-traceid": "e78d85ee3407372d",
    "x-s": "XYW_eyJzaWduU3ZuIjoiNTUiLCJzaWduVHlwZSI6IngyIiwiYXBwSWQiOiJ4aHMtcGMtd2ViIiwic2lnblZlcnNpb24iOiIxIiwicGF5bG9hZCI6ImU0NDEyNzY4OGMzM2FjMzU1ZGNkY2FiYTBhNTZlZDMwOWE3ZmQyN2U1NjYyNDI2NGMyNDBmODJlNWE2Nzc0OWQ5NzU1MmY5M2Q4MTUxZmE0ZjM4ODM5MWVmM2U1ZDVjZTZiNjJlOTc5NmY0NzllODcxZTg1Yjk1YmVmNzNjNjhlNzUzMDE5NDI3M2MyNWE4NDBlMWM3NWM2ZjRhOTRlZGE5MmY1NzFiZGVjMGE0ZjA2N2QwZTlhNWVhZmRiZWQ4NmIyZjE1YWYxMDU2MGMwMDUwMTA5ODFlODc0N2IzNGRjMzcwNGM2YmM1YmU1NmM4NDk3NjIyNmZkNGY0MTBhZmRkNTA5NjZkYjA5ZjhmNzdiNTI4ODYzMWVkYWVhNDA4ODEzYTFkYjBhNTk5OTQyYmEyM2Y3NDJhOTcwNDA0ZjExNjQ5OGM2YzU0YTc2NTcxNjRhZWVjM2U3OWE5OGE0MDVjYzFjMWM4MmU4ZDhkMDJiYmVkNjIwMTNhMDI3MmE1ZmQ0MTZkNWJiMWM3ZDYwYWE5ZDNlZWY2NjFjYThiNTY2In0=",
    "x-s-common": "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",
    "x-t": "1731682017423",
    "x-xray-traceid": "c998254ff48769162080e64836dea108"
}
cookies = {
    "a1": "18f9e255c8f7ofwfg3c4n7oarwjjiyteoktnjk71e50000338142",
    "webId": "73526038f1c79f5cf926a05c0d905a33",
    "abRequestId": "73526038f1c79f5cf926a05c0d905a33",
    "gid": "yj8KjfqJj0ldyYijdJ22STTWYiWliEikqS4I9ydWl0FEVI28V3v9dV888qqYy4J8iWJ0fqdi",
    "xsecappid": "xhs-pc-web",
    "webBuild": "4.43.0",
    "websectiga": "f3d8eaee8a8c63016320d94a1bd00562d516a5417bc43a032a80cbf70f07d5c0",
    "sec_poison_id": "9c70292a-064f-4012-af1c-252bf9e204c6",
    "acw_tc": "0a4aa96317316819572074842ef175148f593954c1121b49636ed564da4b21",
    "web_session": "040069b5ce602e01309c8b1602354beac86fea"
}
url = "https://edith.xiaohongshu.com/api/sns/web/v2/comment/page"
params = {
    "note_id": "673747250000000019016a2e",
    "cursor": "",
    "top_comment_id": "",
    "image_formats": "jpg,webp,avif",
    "xsec_token": "ABVLZlgZiJ2HElrxbHtlIGB28v86otqeSZbbiG7BOuTic="
}
response = requests.get(url, headers=headers, cookies=cookies, params=params)

print(response.text)
print(response)