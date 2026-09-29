# -*- coding: utf-8 -*-
"""
sci-plot 演示脚本: 用合成数据生成全套示例图 + 统计结果 Excel + Markdown 说明。
用法:
    python demo.py <输出目录>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
from scipy import stats

from style import (apply_style, save_figure, format_pvalue, cld_letters,
                   check_fonts, assert_cjk_ok)
import plots

OUT = sys.argv[1] if len(sys.argv) > 1 else "sci-plot-demo"
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(42)
apply_style()
assert_cjk_ok()               # 字体自检: 中文无法渲染直接报错, 不静默产出方块图
FONT_INFO = check_fonts()

# ---------------------------------------------------------------- 合成数据
groups = ["A", "B", "C", "D"]
means = [50, 62, 45, 58]
rows = []
for g, m in zip(groups, means):
    for v in rng.normal(m, 9, 30):
        rows.append({"Group": g, "Value": v})
df_box = pd.DataFrame(rows)

# 组间显著性 (ANOVA + 两两 t 检验 -> CLD 字母)
pairs = {}
for i, a in enumerate(groups):
    for b in groups[i + 1:]:
        va = df_box[df_box.Group == a].Value
        vb = df_box[df_box.Group == b].Value
        pairs[(a, b)] = stats.ttest_ind(va, vb).pvalue
letters = cld_letters(groups, pairs)
f_stat, p_anova = stats.f_oneway(*[df_box[df_box.Group == g].Value for g in groups])

# 折线图数据
t = np.linspace(0, 10, 9)
rows = []
for i, g in enumerate(["Group 1", "Group 2", "Group 3"]):
    y = 5 + (i + 1) * 3 * t + rng.normal(0, 2, len(t))
    for ti, yi in zip(t, y):
        rows.append({"Time": ti, "Value": yi, "Treatment": g})
df_line = pd.DataFrame(rows)

# 散点
xs = rng.uniform(0, 10, 60)
ys = 3 * xs + rng.normal(0, 4, 60) + 20
df_sc = pd.DataFrame({"x": xs, "y": ys})

# 热图
mat = pd.DataFrame(rng.normal(0, 1, (8, 6)),
                   index=[f"S{i+1}" for i in range(8)],
                   columns=[f"Var{j+1}" for j in range(6)])
mat.iloc[:4, :3] += 1.5

# PCA
pca_rows = []
for i, g in enumerate(["Type A", "Type B", "Type C"]):
    center = rng.normal(0, 1, 5)
    for _ in range(25):
        pca_rows.append({"Cluster": g, **{f"f{k+1}": c + rng.normal(0, 0.8)
                                          for k, c in enumerate(center)}})
df_pca = pd.DataFrame(pca_rows)

# 相关性矩阵
corr_df = pd.DataFrame(rng.normal(0, 1, (50, 5)),
                       columns=[f"Var{i+1}" for i in range(5)])
corr_df["Var2"] += corr_df["Var1"] * 0.7
corr_df["Var4"] -= corr_df["Var3"] * 0.5
corr = corr_df.corr()
pmat = corr_df.apply(lambda a: corr_df.apply(
    lambda b: stats.pearsonr(a, b).pvalue))

# 机器学习数据
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

X = pd.DataFrame(rng.normal(0, 1, (300, 6)),
                 columns=[f"Feature {i+1}" for i in range(6)])
logit = 2 * X["Feature 1"] - 1.5 * X["Feature 3"] + X["Feature 5"] + rng.normal(0, 1, 300)
y_bin = (logit > logit.median()).astype(int)
Xtr, Xte, ytr, yte = train_test_split(X, y_bin, test_size=0.3, random_state=1)
rf = RandomForestClassifier(n_estimators=200, random_state=1).fit(Xtr, ytr)
lr = LogisticRegression(max_iter=1000).fit(Xtr, ytr)
scores = {"RF": rf.predict_proba(Xte)[:, 1], "LR": lr.predict_proba(Xte)[:, 1]}
importances = pd.Series(rf.feature_importances_, index=X.columns)
shap_like = np.column_stack([
    (Xte[c] - Xte[c].mean()) * (imp / imp.sum())
    for c, imp in zip(Xte.columns, rf.feature_importances_)
]) + rng.normal(0, 0.02, Xte.shape)

cm = np.array([[50, 10], [8, 32]])

# 桑基
flows = pd.DataFrame({
    "source": ["A", "A", "B", "B", "C", "D", "D"],
    "target": ["W", "X", "W", "Y", "X", "Y", "Z"],
    "value": [30, 20, 25, 15, 35, 20, 25],
})

# ---------------------------------------------------------------- 逐一出图
made = []

def go(name, fn):
    """单图按统一规范产出 PNG + PDF + SVG 三格式。"""
    fig = fn()
    made.extend(save_figure(fig, os.path.join(OUT, name), formats=("png", "pdf", "svg")))

go("01_line", lambda: plots.line_plot(df_line, "Time", "Value", group="Treatment")[0])
go("02_boxplot", lambda: plots.box_plot(df_box, "Group", "Value", letters=letters)[0])
summary = df_box.groupby("Group").Value.agg(["mean", "std"]).reset_index()
go("03_bar", lambda: plots.bar_plot(
    summary.rename(columns={"mean": "Value"}), "Group", "Value",
    error="std", letters=letters)[0])
go("04_scatter_fit", lambda: plots.scatter_fit(df_sc, "x", "y")[0])
go("05_heatmap", lambda: plots.heatmap(mat)[0])
go("06_pca", lambda: plots.pca_plot(df_pca, [f"f{i+1}" for i in range(5)], "Cluster")[0])
go("07_biplot", lambda: plots.biplot(df_pca, [f"f{i+1}" for i in range(5)], "Cluster")[0])
go("08_correlation", lambda: plots.correlation_matrix(corr, pmat=pmat)[0])
go("09_rf_importance", lambda: plots.rf_importance(importances)[0])
go("10_shap", lambda: plots.shap_summary(shap_like, Xte)[0])
go("11_gam", lambda: plots.gam_fit(df_sc, "x", "y")[0])
go("12_segmented", lambda: plots.segmented_regression(
    pd.DataFrame({"x": np.r_[xs, xs], "y": np.r_[ys * 0.2 + 1,
                                                 ys * 0.05 + 4 + rng.normal(0, 0.5, 60)]}),
    "x", "y")[0])
go("13_roc", lambda: plots.roc_curve(yte, scores)[0])
go("14_dca", lambda: plots.dca_curve(yte, scores)[0])
go("15_calibration", lambda: plots.calibration_curve(yte, scores)[0])
go("16_sankey", lambda: plots.sankey_plot(flows)[0])
go("17_violin", lambda: plots.violin_plot(df_box, "Group", "Value")[0])
go("18_confusion_matrix", lambda: plots.confusion_matrix_plot(cm)[0])

# ---------------------------------------------------------------- 组合图 2x2
combo = plots.combined_figure([
    lambda ax: plots.bar_plot(summary.rename(columns={"mean": "Value"}),
                              "Group", "Value", error="std", letters=letters, ax=ax),
    lambda ax: plots.scatter_fit(df_sc, "x", "y", ax=ax),
    lambda ax: plots.heatmap(mat.iloc[:5, :4], ax=ax, cluster=False),
    lambda ax: plots.violin_plot(df_box, "Group", "Value", ax=ax),
], 2, 2, os.path.join(OUT, "19_combined_2x2"))
made.extend([p for p in combo if p.endswith(".png")])

# ---------------------------------------------------------------- 统计结果 Excel
xl = os.path.join(OUT, "stats_results.xlsx")
with pd.ExcelWriter(xl) as w:
    pd.DataFrame({"Test": ["One-way ANOVA"], "Statistic": [f_stat],
                  "P": [p_anova], "P_display": [format_pvalue(p_anova)]}
                 ).to_excel(w, sheet_name="ANOVA", index=False)
    pd.DataFrame([(a, b, p) for (a, b), p in pairs.items()],
                 columns=["Group1", "Group2", "P"]
                 ).to_excel(w, sheet_name="Pairwise", index=False)
    pd.DataFrame(list(letters.items()), columns=["Group", "Letter"]
                 ).to_excel(w, sheet_name="CLD_Letters", index=False)
    importances.sort_values(ascending=False).rename("Importance").to_frame(
        ).to_excel(w, sheet_name="RF_Importance")
    corr.to_excel(w, sheet_name="Correlation")

# ---------------------------------------------------------------- Markdown 说明
md = os.path.join(OUT, "README.md")
with open(md, "w", encoding="utf-8") as f:
    f.write("# sci-plot 示例输出说明\n\n")
    f.write("统一规范: 中文宋体 / 英文 Times New Roman、白底、保留图框、"
            "无网格、加粗字体、600 dpi、显著性字母优先。\n\n")
    f.write("## 字体自检\n\n")
    for k, v in FONT_INFO.items():
        f.write(f"- {k}: {v}\n")
    f.write("\n")
    f.write(f"- ANOVA: F = {f_stat:.2f}, {format_pvalue(p_anova)}\n")
    f.write(f"- 显著性字母: {letters}\n\n")
    f.write(f"## 图清单 (共 {sum(1 for p in made if p.endswith('.png'))} 张, "
            "单图均含 PNG + PDF + SVG)\n\n")
    for p in made:
        if p.endswith(".png"):
            f.write(f"- `{os.path.basename(p)}`\n")

print("OK")
for p in made:
    print(p)
print(xl)
print(md)
