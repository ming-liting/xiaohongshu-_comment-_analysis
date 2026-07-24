"""
小红书 App Store 评论抓取 - 直接调 Apple API
"""

import requests
import pandas as pd
import time
import json
from datetime import datetime

APP_ID = 741292507
COUNTRY_CODE = "cn"
TARGET_COUNT = 3000

# Apple 官方的用户评论 API（不是 RSS，是 App Store 页面用的接口）
BASE_URL = f"https://itunes.apple.com/{COUNTRY_CODE}/rss/customerreviews/id={APP_ID}/sortBy=mostRecent/page=1/json"

# 另一种：直接翻页抓取
def fetch_page_rss(page_num):
    """用 RSS 接口翻页抓取"""
    url = f"https://itunes.apple.com/{COUNTRY_CODE}/rss/customerreviews/id={APP_ID}/sortBy=mostRecent/page={page_num}/json"
    headers = {
        "User-Agent": "iTunes/12.0 (Windows; Microsoft Windows 10 x64) AppleWebKit/536.30.1",
        "Accept": "application/json",
    }
    resp = requests.get(url, headers=headers, timeout=30)
    data = resp.json()
    entries = data.get("feed", {}).get("entry", [])
    # 第一条是 feed 元数据，跳过
    reviews = []
    for e in entries:
        if "im:rating" in e:
            reviews.append({
                "rating": int(e["im:rating"]["label"]),
                "title": e.get("title", {}).get("label", ""),
                "content": e.get("content", {}).get("label", ""),
                "author": e.get("author", {}).get("name", {}).get("label", ""),
                "date": e.get("updated", {}).get("label", ""),
                "version": e.get("im:version", {}).get("label", "") if "im:version" in e else "",
            })
    return reviews

# 备选：用 itunes.apple.com 的 lookup API
def fetch_via_lookup():
    """通过 lookup API 获取 app 信息 + 评论页链接"""
    url = f"https://itunes.apple.com/lookup?id={APP_ID}&country={COUNTRY_CODE}&entity=software"
    resp = requests.get(url, timeout=30)
    data = resp.json()
    print(json.dumps(data, ensure_ascii=False, indent=2)[:500])
    return data

print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始多策略抓取...\n")

all_reviews = []

# 策略 1: RSS 分页
print("=== 策略1: RSS 分页抓取 ===")
for page in range(1, 11):
    try:
        reviews = fetch_page_rss(page)
        print(f"  第 {page} 页: {len(reviews)} 条")
        if not reviews:
            break
        all_reviews.extend(reviews)
        time.sleep(1)
    except Exception as e:
        print(f"  第 {page} 页出错: {e}")
        break

print(f"\nRSS 共抓取: {len(all_reviews)} 条")

# 如果 RSS 还是空的，试试策略 2
if not all_reviews:
    print("\n=== 策略2: Lookup API ===")
    fetch_via_lookup()

    print("\n=== 策略3: 直接请求 App Store 页面 ===")
    store_url = f"https://apps.apple.com/{COUNTRY_CODE}/app/id{APP_ID}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    resp = requests.get(store_url, headers=headers, timeout=30)
    print(f"  HTTP 状态码: {resp.status_code}")
    print(f"  响应长度: {len(resp.text)}")
    # 保存一份 HTML 看看结构
    with open("page_debug.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
    print("  页面已保存到 page_debug.html")

    # 检查是否有客户评论的 JSON 数据嵌入在页面中
    # Apple 通常在页面内嵌一个包含评论数据的 script 标签
    if "customerReviews" in resp.text:
        print("  页面中包含 'customerReviews' 关键词 ✓")
    else:
        print("  页面中未找到 'customerReviews'")

# 保存结果
if all_reviews:
    df = pd.DataFrame(all_reviews)
    df.to_csv("reviews_raw.csv", index=False, encoding="utf-8-sig")
    print(f"\n✓ 已保存 reviews_raw.csv，行数: {len(df)}")
    print(f"  列名: {list(df.columns)}")
    print(f"  评分分布:\n{df['rating'].value_counts().sort_index()}")
else:
    print("\n✗ 所有策略均未获取到评论。")
    print("  原因: Apple 已停用公开评论 API，无法通过程序直接获取。")
    print("  需要更换数据源。")
