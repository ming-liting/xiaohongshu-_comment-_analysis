"""
生成分析报告图表
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # 非交互模式，输出到文件
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
import jieba
import os

# 中文字体设置
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# 创建图表输出目录
os.makedirs("charts", exist_ok=True)

df = pd.read_csv("clean_reviews.csv")
df["date"] = pd.to_datetime(df["date"])

# ========== 图1: 每日评分趋势 ==========
fig, ax1 = plt.subplots(figsize=(10, 5))

daily = df.groupby("date").agg(
    评论数=("rating", "count"),
    平均分=("rating", "mean"),
    差评率=("rating", lambda x: (x <= 2).sum() / len(x) * 100),
).sort_index()

bars = ax1.bar(daily.index, daily["评论数"], color="#ddd", label="评论数", width=0.6)
ax1.set_ylabel("评论数", fontsize=12)
ax1.set_xlabel("日期", fontsize=12)

ax2 = ax1.twinx()
ax2.plot(daily.index, daily["平均分"], "o-", color="#e74c3c", linewidth=2, markersize=8, label="平均评分")
ax2.set_ylabel("平均评分 (1-5)", fontsize=12, color="#e74c3c")
ax2.set_ylim(1, 5)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

plt.title("小红书 App Store 每日评论数与评分趋势 (2026.07)", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig("charts/01_daily_trend.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ charts/01_daily_trend.png")

# ========== 图2: 评分分布饼图 ==========
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# 饼图
labels = ["差评 (1-2分)", "中评 (3分)", "好评 (4-5分)"]
sizes = [
    len(df[df["rating"] <= 2]),
    len(df[df["rating"] == 3]),
    len(df[df["rating"] >= 4]),
]
colors_pie = ["#e74c3c", "#f39c12", "#2ecc71"]
explode = (0.02, 0.02, 0.02)

ax1.pie(sizes, explode=explode, labels=labels, colors=colors_pie, autopct="%1.1f%%",
        shadow=False, startangle=90, textprops={"fontsize": 11})
ax1.set_title("评分分布 (485条)", fontsize=13, fontweight="bold")

# 柱状图
ratings = df["rating"].value_counts().sort_index()
ax2.bar(ratings.index, ratings.values, color=colors_pie, width=0.6)
for i, v in enumerate(ratings.values):
    ax2.text(ratings.index[i], v + 3, str(v), ha="center", fontsize=11, fontweight="bold")
ax2.set_xticks([1, 2, 3, 4, 5])
ax2.set_xlabel("评分", fontsize=12)
ax2.set_ylabel("评论数", fontsize=12)
ax2.set_title("各评分数量", fontsize=13, fontweight="bold")

plt.tight_layout()
plt.savefig("charts/02_rating_distribution.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ charts/02_rating_distribution.png")

# ========== 图3: 差评归因条形图 ==========
cat_data = {
    "账号封禁": 13,
    "审核误判": 9,
    "客服无响应": 8,
    "内容质量差\n(含社区氛围)": 8,
    "算法推荐差": 3,
    "广告太多": 2,
    "其他": 7,  # 去掉无实质吐槽的 10 条
}
# 去掉"其他"，排好序
cats = {k: v for k, v in cat_data.items() if k != "其他"}
cats = dict(sorted(cats.items(), key=lambda x: x[1], reverse=True))

fig, ax = plt.subplots(figsize=(10, 5))
colors_bar = ["#c0392b", "#e74c3c", "#e67e22", "#f39c12", "#3498db", "#95a5a6"][:len(cats)]
bars = ax.barh(list(cats.keys()), list(cats.values()), color=colors_bar, height=0.6)
for bar, v in zip(bars, cats.values()):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
            f"{v}条 ({v/50*100:.0f}%)", va="center", fontsize=11, fontweight="bold")
ax.set_xlabel("评论数 (共抽样50条)", fontsize=12)
ax.set_title("差评归因分类统计", fontsize=14, fontweight="bold")
ax.invert_yaxis()
ax.set_xlim(0, max(cats.values()) + 5)
plt.tight_layout()
plt.savefig("charts/03_bad_review_categories.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ charts/03_bad_review_categories.png")

# ========== 图4: 词云 ==========
bad = df[df["rating_label"] == "差评"]
stopwords = set([
    "的", "了", "是", "我", "就", "都", "也", "不", "在", "和", "很", "有", "这",
    "你", "他", "她", "它", "们", "那", "个", "一", "还", "没", "看", "说", "要",
    "会", "去", "上", "下", "人", "把", "着", "又", "过", "能", "让", "到", "被",
    "而", "与", "且", "或", "从", "以", "及", "可", "为", "但", "只", "太", "好",
    "吗", "呢", "吧", "啊", "呀", "哦", "嗯", "嘛", "呗", "哈",
    "app", "真的", "然后", "所以", "因为", "可以", "什么", "怎么", "这个", "那个",
    "自己", "已经", "没有", "知道", "感觉", "觉得", "现在", "还是", "就是",
    "一个", "一直", "一下", "一样", "有点", "特别", "非常", "好多", "每次", "天天",
    "以前", "以后", "东西", "今天", "昨天", "但是", "而且", "这么", "为什么",
    "不能", "不是", "你们", "别人", "任何", "直接",
    "小红书", "软件", "平台",
])

text_all = " ".join(bad["content"].astype(str).tolist())
words = jieba.lcut(text_all)
words = [w for w in words if len(w) >= 2 and w not in stopwords]
word_freq = Counter(words)

wc = WordCloud(
    font_path="C:/Windows/Fonts/simhei.ttf",  # 黑体
    width=1000, height=600,
    background_color="white",
    max_words=100,
    colormap="Reds",
    collocations=False,
).generate_from_frequencies(dict(word_freq.most_common(100)))

fig, ax = plt.subplots(figsize=(12, 7))
ax.imshow(wc, interpolation="bilinear")
ax.axis("off")
ax.set_title("差评关键词词云", fontsize=16, fontweight="bold", pad=20)
plt.tight_layout()
plt.savefig("charts/04_wordcloud.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ charts/04_wordcloud.png")

# ========== 图5: 版本对比 ==========
ver = df.groupby("version").agg(
    评论数=("rating", "count"),
    差评率=("rating", lambda x: (x <= 2).sum() / len(x) * 100),
).query("评论数 >= 5").sort_index()

fig, ax = plt.subplots(figsize=(8, 4))
colors_ver = ["#f39c12", "#e74c3c"]
bars = ax.bar(ver.index, ver["差评率"], color=colors_ver[:len(ver)], width=0.4)
for bar, v in zip(bars, ver["差评率"]):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
            f"{v:.0f}%", ha="center", fontsize=13, fontweight="bold")
ax.set_ylabel("差评率 (%)", fontsize=12)
ax.set_xlabel("版本号", fontsize=12)
ax.set_title("各版本差评率对比", fontsize=14, fontweight="bold")
ax.set_ylim(0, 100)
plt.tight_layout()
plt.savefig("charts/05_version_compare.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ charts/05_version_compare.png")

print("\n全部 5 张图表已生成 → charts/ 目录")
