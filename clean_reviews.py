"""
数据清洗脚本
输入: reviews_raw.csv
输出: clean_reviews.csv
"""
import pandas as pd

# ========== 1. 读取 ==========
df = pd.read_csv("reviews_raw.csv")
print(f"原始数据: {len(df)} 条")

# ========== 2. 去重（同一作者 + 同一内容 = 重复） ==========
before = len(df)
df = df.drop_duplicates(subset=["author", "content"])
print(f"去重: {before} → {len(df)} 条 (删除 {before - len(df)} 条)")

# ========== 3. 日期格式化 ==========
df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
print(f"日期范围: {df['date'].min()} ~ {df['date'].max()}")

# ========== 4. 评分分组 ==========
def label_rating(r):
    if r >= 4:
        return "好评"
    elif r == 3:
        return "中评"
    else:
        return "差评"

df["rating_label"] = df["rating"].apply(label_rating)
print(f"评分分布:\n{df['rating_label'].value_counts()}")

# ========== 5. 评论长度（中文有效内容） ==========
df["review_len"] = df["content"].str.len()
# 过滤纯空或太短的评论（可能是灌水）
before = len(df)
df = df[df["review_len"] >= 2]
print(f"移除过短评论: {before} → {len(df)} 条 (删除 {before - len(df)} 条)")

# ========== 6. 版本号清洗 ==========
# 去掉可能的换行符和空格
df["version"] = df["version"].str.strip()

# ========== 7. 导出 ==========
df.to_csv("clean_reviews.csv", index=False, encoding="utf-8-sig")
print(f"\n最终数据: {len(df)} 条")
print(f"列: {list(df.columns)}")
print(f"文件大小: {df.memory_usage(deep=True).sum() / 1024:.1f} KB")
print("\n✓ 清洗完成 → clean_reviews.csv")
