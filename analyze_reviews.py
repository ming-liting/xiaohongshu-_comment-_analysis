"""
差评归因分析 - jieba 分词 + 高频词提取
"""
import pandas as pd
import jieba
from collections import Counter

# ========== 1. 读取 ==========
df = pd.read_csv("clean_reviews.csv")

# ========== 2. 分离差评 ==========
bad = df[df["rating_label"] == "差评"].copy()
good = df[df["rating_label"] == "好评"].copy()

print(f"差评 {len(bad)} 条 | 好评 {len(good)} 条 | 中评 {len(df) - len(bad) - len(good)} 条\n")

# ========== 3. 停用词表 ==========
# 中文常见停用词 + App 评论常见噪声词
stopwords = set([
    "的", "了", "是", "我", "就", "都", "也", "不", "在", "和", "很", "有", "这",
    "你", "他", "她", "它", "们", "那", "个", "一", "还", "没", "看", "说", "要",
    "会", "去", "上", "下", "人", "把", "着", "又", "过", "能", "让", "到", "被",
    "而", "与", "且", "或", "从", "以", "及", "可", "为", "但", "只", "太", "好",
    "吗", "呢", "吧", "啊", "呀", "哦", "嗯", "嘛", "呗", "哈",
    "app", "真的", "然后", "所以", "因为", "可以", "什么", "怎么", "这个",
    "那个", "自己", "已经", "没有", "知道", "感觉", "觉得", "现在", "还是",
    "就是", "一个", "一直", "一下", "一样", "有点", "特别", "非常", "好多",
    "每次", "天天", "以前", "以后", "东西", "今天", "昨天",
    "小红书", "软件", "平台",
])

# ========== 4. 分词 + 频次统计 ==========
def extract_keywords(series, stopwords, top_n=50):
    all_words = []
    for text in series:
        words = jieba.lcut(str(text))
        for w in words:
            w = w.strip()
            if len(w) >= 2 and w not in stopwords:
                all_words.append(w)
    return Counter(all_words).most_common(top_n)

print("=" * 50)
print("差评高频词 TOP 30")
print("=" * 50)
bad_keywords = extract_keywords(bad["content"], stopwords, 30)
for i, (word, count) in enumerate(bad_keywords, 1):
    bar = "█" * (count // 3)
    print(f"  {i:2d}. {word:　<6s} {count:>4d} 次  {bar}")

print(f"\n{'='*50}")
print("好评高频词 TOP 20")
print("=" * 50)
good_keywords = extract_keywords(good["content"], stopwords, 20)
for i, (word, count) in enumerate(good_keywords, 1):
    print(f"  {i:2d}. {word:　<6s} {count:>3d} 次")

# ========== 5. 保存 ==========
# 把差评关键词存成 CSV
kw_df = pd.DataFrame(bad_keywords, columns=["关键词", "频次"])
kw_df.to_csv("bad_review_keywords.csv", index=False, encoding="utf-8-sig")
print(f"\n✓ 差评关键词已保存 → bad_review_keywords.csv")

# 同时保存带分词标注的评论
print("✓ 分析完成")
