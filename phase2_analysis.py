"""
Phase 2: 版本/日期评分趋势 + 差评抽样（手读归类用）
"""
import pandas as pd

df = pd.read_csv("clean_reviews.csv")
df["date"] = pd.to_datetime(df["date"])
bad = df[df["rating_label"] == "差评"].copy()

# ========== 1. 按日期看评分趋势 ==========
print("=" * 60)
print("按日期评分趋势")
print("=" * 60)
daily = df.groupby("date").agg(
    评论数=("rating", "count"),
    平均分=("rating", "mean"),
    差评率=("rating", lambda x: (x <= 2).sum() / len(x) * 100),
).sort_index()
print(daily.to_string(float_format="%.1f"))

# ========== 2. 按版本统计（只显示评论 ≥5 的版本） ==========
print("\n" + "=" * 60)
print("按版本评分（评论数 ≥5）")
print("=" * 60)
ver = df.groupby("version").agg(
    评论数=("rating", "count"),
    平均分=("rating", "mean"),
    差评数=("rating", lambda x: (x <= 2).sum()),
    差评率=("rating", lambda x: f"{(x <= 2).sum() / len(x) * 100:.0f}%"),
).query("评论数 >= 5").sort_values("差评数", ascending=False)
print(ver.to_string(float_format="%.1f"))

# ========== 3. 抽 50 条差评让你手读归类 ==========
print("\n" + "=" * 60)
print("手读归类样本（50 条差评）")
print("=" * 60)
sample = bad.sample(n=min(50, len(bad)), random_state=42).reset_index(drop=True)
sample = sample[["date", "rating", "version", "content"]]
sample.to_csv("sample_bad_reviews.csv", index=False, encoding="utf-8-sig")

for i, row in sample.head(50).iterrows():
    c = str(row["content"])[:80]
    print(f"  [{i+1:2d}] {c}{'...' if len(str(row['content'])) > 80 else ''}")

print(f"\n✓ 样本已保存 → sample_bad_reviews.csv（共 {len(sample)} 条）")
print("  打开这个文件，在最后一列加上你的分类标签。")
print("  分类参考：账号封禁 | 审核误判 | 客服无响应 | 广告太多")
print("             | 内容同质化 | 算法推荐差 | 功能BUG | 其他")
