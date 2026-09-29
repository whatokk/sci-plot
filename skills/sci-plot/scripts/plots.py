# -*- coding: utf-8 -*-
"""
sci-plot 图型函数库
===================
所有函数遵循统一规范: 白底、保留图框、无网格、加粗字体、600 dpi。
每个函数返回 (fig, ax) 或 fig,便于继续加工或放入组合图。
依赖: matplotlib / numpy / pandas / scipy / scikit-learn
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, PathPatch
from matplotlib.path import Path

from style import (apply_style, color, PALETTE, DIVERGING_CMAP, SEQ_CMAP,
                   save_figure, format_pvalue, p_to_stars)


def _prep():
    apply_style()


# ================================================================ 基础统计图
def line_plot(df, x, y, group=None, ax=None, error=None, markers=True):
    """折线图(分组可选, 误差带可选)。df 为长表。"""
    _prep()
    if ax is None:
        fig, ax = plt.subplots(figsize=(3.4, 3.0))
    else:
        fig = ax.figure
    groups = df[group].unique() if group else [None]
    for i, g in enumerate(groups):
        d = df if g is None else df[df[group] == g]
        d = d.sort_values(x)
        label = str(g) if g is not None else None
        ax.plot(d[x], d[y], color=color(i), marker="o" if markers else None,
                label=label)
        if error and error in d:
            ax.fill_between(d[x], d[y] - d[error], d[y] + d[error],
                            color=color(i), alpha=0.15, linewidth=0)
    if group:
        ax.legend()
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    return fig, ax


def box_plot(df, x, y, ax=None, hue_colors=None, show_points=True, letters=None):
    """分组箱线图。letters: {组: 字母} 显著性标注。"""
    _prep()
    if ax is None:
        fig, ax = plt.subplots(figsize=(3.4, 3.0))
    else:
        fig = ax.figure
    cats = list(df[x].unique())
    data = [df[df[x] == c][y].dropna() for c in cats]
    bp = ax.boxplot(data, tick_labels=cats, patch_artist=True, widths=0.55,
                    medianprops=dict(color="black", linewidth=1.4),
                    whiskerprops=dict(linewidth=1.1), capprops=dict(linewidth=1.1),
                    flierprops=dict(marker="", markersize=0))
    for i, patch in enumerate(bp["boxes"]):
        patch.set_facecolor(color(i))
        patch.set_alpha(0.85)
        patch.set_edgecolor("black")
    if show_points:
        rng = np.random.default_rng(0)
        for i, vals in enumerate(data):
            jitter = rng.normal(0, 0.05, len(vals))
            ax.scatter(np.full(len(vals), i + 1) + jitter, vals,
                       s=10, color="black", alpha=0.6, zorder=3)
    if letters:
        tops = [v.max() if len(v) else 0 for v in data]
        from style import add_sig_letters
        add_sig_letters(ax, np.arange(1, len(cats) + 1), tops,
                        [letters.get(c, "") for c in cats])
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    return fig, ax


def bar_plot(df, x, y, error=None, ax=None, letters=None):
    """柱状图(误差线 + 显著性字母)。df 需为每组一行的汇总表。"""
    _prep()
    if ax is None:
        fig, ax = plt.subplots(figsize=(3.4, 3.0))
    else:
        fig = ax.figure
    cats = list(df[x])
    vals = df[y].values
    errs = df[error].values if error and error in df else None
    bars = ax.bar(cats, vals, color=[color(i) for i in range(len(cats))],
                  edgecolor="black", linewidth=1.0, width=0.6,
                  yerr=errs, capsize=3, error_kw=dict(linewidth=1.1))
    if letters:
        from style import add_sig_letters
        tops = vals + (errs if errs is not None else 0)
        add_sig_letters(ax, np.arange(len(cats)), tops,
                        [letters.get(c, "") for c in cats])
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    return fig, ax


def scatter_fit(df, x, y, ax=None, show_stats=True):
    """散点拟合图(线性拟合 + R 与 P 值标注)。"""
    _prep()
    from scipy import stats
    if ax is None:
        fig, ax = plt.subplots(figsize=(3.4, 3.0))
    else:
        fig = ax.figure
    ax.scatter(df[x], df[y], s=16, color=color(4), alpha=0.75,
               edgecolors="white", linewidths=0.4)
    r, p = stats.pearsonr(df[x], df[y])
    xs = np.linspace(df[x].min(), df[x].max(), 100)
    slope, intercept, *_ = stats.linregress(df[x], df[y])
    ax.plot(xs, slope * xs + intercept, color=color(0), linewidth=1.8)
    if show_stats:
        ax.text(0.05, 0.95, f"R = {r:.2f}\n{format_pvalue(p)}",
                transform=ax.transAxes, va="top", fontsize=9, fontweight="bold")
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    return fig, ax


def heatmap(mat, ax=None, cmap=SEQ_CMAP, cluster=True, annot=False, cbar_label="Value"):
    """聚类热图。mat 为 DataFrame。cluster=True 时用 scipy 层次聚类重排并画树。"""
    _prep()
    from scipy.cluster import hierarchy
    from scipy.spatial.distance import pdist
    data = np.asarray(mat)
    if ax is not None:
        cluster = False  # 传入外部 ax(组合图)时禁用聚类树
    if cluster and mat.shape[0] > 2 and mat.shape[1] > 2:
        fig = plt.figure(figsize=(4.2, 3.6))
        gs = fig.add_gridspec(2, 2, width_ratios=[0.22, 1], height_ratios=[0.22, 1],
                              wspace=0.02, hspace=0.02)
        ax_top = fig.add_subplot(gs[0, 1])
        ax_left = fig.add_subplot(gs[1, 0])
        ax = fig.add_subplot(gs[1, 1])
        col_link = hierarchy.linkage(pdist(data.T), method="average")
        row_link = hierarchy.linkage(pdist(data), method="average")
        hierarchy.dendrogram(col_link, ax=ax_top, no_labels=True, color_threshold=0,
                             above_threshold_color="gray")
        hierarchy.dendrogram(row_link, ax=ax_left, no_labels=True, orientation="left",
                             color_threshold=0, above_threshold_color="gray")
        col_ord = hierarchy.leaves_list(col_link)
        row_ord = hierarchy.leaves_list(row_link)
        data = data[np.ix_(row_ord, col_ord)]
        row_labels = list(np.asarray(mat.index)[row_ord])
        col_labels = list(np.asarray(mat.columns)[col_ord])
        ax_top.axis("off")
        ax_left.axis("off")
    else:
        if ax is None:
            fig, ax = plt.subplots(figsize=(3.8, 3.2))
        else:
            fig = ax.figure
        row_labels, col_labels = list(mat.index), list(mat.columns)
    vmax = np.nanmax(np.abs(data))
    im = ax.imshow(data, cmap=cmap, aspect="auto",
                   vmin=-vmax if cmap == DIVERGING_CMAP else None,
                   vmax=vmax if cmap == DIVERGING_CMAP else None)
    ax.set_xticks(range(len(col_labels)), col_labels, rotation=45, ha="right")
    ax.set_yticks(range(len(row_labels)), row_labels)
    if annot:
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                ax.text(j, i, f"{data[i, j]:.1f}", ha="center", va="center", fontsize=7)
    fig.colorbar(im, ax=ax, label=cbar_label, fraction=0.046)
    return fig, ax


def pca_plot(df, features, group, ax=None, show_ellipse=True):
    """PCA 散点图(95% 置信椭圆 + 方差解释率)。"""
    _prep()
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    if ax is None:
        fig, ax = plt.subplots(figsize=(3.4, 3.0))
    else:
        fig = ax.figure
    X = StandardScaler().fit_transform(df[features])
    pca = PCA(n_components=2)
    scores = pca.fit_transform(X)
    var = pca.explained_variance_ratio_ * 100
    for i, g in enumerate(df[group].unique()):
        m = df[group] == g
        ax.scatter(scores[m, 0], scores[m, 1], s=18, color=color(i), label=str(g),
                   alpha=0.8, edgecolors="white", linewidths=0.4)
        if show_ellipse and m.sum() > 3:
            _confidence_ellipse(ax, scores[m, 0], scores[m, 1], color(i))
    ax.set_xlabel(f"PC1 ({var[0]:.1f}%)")
    ax.set_ylabel(f"PC2 ({var[1]:.1f}%)")
    ax.legend()
    return fig, ax


def _confidence_ellipse(ax, x, y, c, n_std=1.96):
    from matplotlib.patches import Ellipse
    cov = np.cov(x, y)
    vals, vecs = np.linalg.eigh(cov)
    order = vals.argsort()[::-1]
    vals, vecs = vals[order], vecs[:, order]
    theta = np.degrees(np.arctan2(*vecs[:, 0][::-1]))
    w, h = 2 * n_std * np.sqrt(np.maximum(vals, 1e-12))
    e = Ellipse((np.mean(x), np.mean(y)), w, h, angle=theta,
                facecolor=c, alpha=0.12, edgecolor=c, linewidth=1.0)
    ax.add_patch(e)


def biplot(df, features, group, ax=None, top_n=None):
    """RDA/PCA 双序图: 样方点 + 环境因子箭头(以 PCA 近似展示)。"""
    _prep()
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    if ax is None:
        fig, ax = plt.subplots(figsize=(3.6, 3.2))
    else:
        fig = ax.figure
    X = StandardScaler().fit_transform(df[features])
    pca = PCA(n_components=2)
    scores = pca.fit_transform(X)
    loadings = pca.components_.T
    var = pca.explained_variance_ratio_ * 100
    for i, g in enumerate(df[group].unique()):
        m = df[group] == g
        ax.scatter(scores[m, 0], scores[m, 1], s=16, color=color(i),
                   label=str(g), alpha=0.8)
    scale = np.abs(scores[:, :2]).max() * 0.9
    idx = np.argsort(np.linalg.norm(loadings, axis=1))[::-1]
    if top_n:
        idx = idx[:top_n]
    for j in idx:
        ax.annotate("", xy=loadings[j] * scale, xytext=(0, 0),
                    arrowprops=dict(arrowstyle="-|>", color="black", lw=1.2))
        ax.text(*(loadings[j] * scale * 1.12), features[j],
                fontsize=8, ha="center", fontweight="bold")
    ax.set_xlabel(f"Axis1 ({var[0]:.1f}%)")
    ax.set_ylabel(f"Axis2 ({var[1]:.1f}%)")
    ax.legend()
    return fig, ax


def correlation_matrix(corr, ax=None, pmat=None):
    """相关性矩阵气泡图。corr 为相关系数 DataFrame, pmat 可选 P 值矩阵(显著打 *)。"""
    _prep()
    if ax is None:
        fig, ax = plt.subplots(figsize=(3.8, 3.4))
    else:
        fig = ax.figure
    labels = list(corr.columns)
    n = len(labels)
    for i in range(n):
        for j in range(n):
            r = corr.iloc[i, j]
            size = abs(r) * 380
            c = plt.get_cmap(DIVERGING_CMAP)((r + 1) / 2)
            ax.scatter(j, i, s=size, color=c, edgecolors="white", linewidths=0.5)
            if pmat is not None and pmat.iloc[i, j] < 0.05 and i != j:
                ax.text(j, i, "*", ha="center", va="center", fontsize=10,
                        fontweight="bold", color="black")
    ax.set_xticks(range(n), labels, rotation=45, ha="right")
    ax.set_yticks(range(n), labels)
    ax.set_xlim(-0.6, n - 0.4)
    ax.set_ylim(n - 0.4, -0.6)
    sm = plt.cm.ScalarMappable(cmap=DIVERGING_CMAP,
                               norm=plt.Normalize(-1, 1))
    ax.figure.colorbar(sm, ax=ax, label="r", fraction=0.046)
    return fig, ax


# ================================================================ 机器学习图
def rf_importance(importances: pd.Series, ax=None, top_n=10):
    """随机森林重要性横向条形图。importances: index=特征名。"""
    _prep()
    if ax is None:
        fig, ax = plt.subplots(figsize=(3.6, 3.0))
    else:
        fig = ax.figure
    imp = importances.sort_values(ascending=True).tail(top_n)
    ax.barh(imp.index, imp.values * (100 if imp.max() <= 1 else 1),
            color=color(1), edgecolor="black", linewidth=0.8, height=0.62)
    ax.set_xlabel("Importance (%)" if imp.max() <= 1 else "Importance")
    return fig, ax


def shap_summary(shap_values: np.ndarray, X: pd.DataFrame, ax=None, max_display=8):
    """
    SHAP 蜂群摘要图(不依赖 shap 库,直接吃数值)。
    shap_values: (n_samples, n_features); X: 特征值 DataFrame(用于着色)。
    """
    _prep()
    if ax is None:
        fig, ax = plt.subplots(figsize=(3.8, 3.2))
    else:
        fig = ax.figure
    names = list(X.columns)
    order = np.argsort(np.abs(shap_values).mean(0))[::-1][:max_display]
    rng = np.random.default_rng(0)
    Xn = (X - X.min()) / (X.max() - X.min() + 1e-12)
    for row, j in enumerate(order[::-1]):
        sv = shap_values[:, j]
        y = row + rng.normal(0, 0.08, len(sv))
        sc = ax.scatter(sv, y, c=Xn.iloc[:, j], cmap=DIVERGING_CMAP,
                        s=8, alpha=0.8, linewidths=0)
    ax.set_yticks(range(len(order)), [names[j] for j in order[::-1]])
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("SHAP value")
    ax.figure.colorbar(sc, ax=ax, label="Feature value", fraction=0.046)
    return fig, ax


def gam_fit(df, x, y, ax=None, n_knots=6, show_ci=True):
    """GAM 风格平滑拟合图(样条平滑 + 95% CI + 部分残差点)。"""
    _prep()
    from scipy.interpolate import UnivariateSpline
    if ax is None:
        fig, ax = plt.subplots(figsize=(3.4, 3.0))
    else:
        fig = ax.figure
    d = df.sort_values(x)
    xs, ys = d[x].values, d[y].values
    ax.scatter(xs, ys, s=12, color=color(4), alpha=0.5)
    spl = UnivariateSpline(xs, ys, s=len(xs) * np.var(ys) * 0.1, k=3)
    grid = np.linspace(xs.min(), xs.max(), 200)
    yhat = spl(grid)
    ax.plot(grid, yhat, color=color(0), linewidth=2.0)
    if show_ci:
        resid = ys - spl(xs)
        se = 1.96 * np.std(resid)
        ax.fill_between(grid, yhat - se, yhat + se, color=color(0), alpha=0.15,
                        linewidth=0)
    ax.set_xlabel(x)
    ax.set_ylabel(f"f({x})")
    return fig, ax


def segmented_regression(df, x, y, ax=None):
    """分段回归阈值图(两段线性,自动搜索拐点)。"""
    _prep()
    if ax is None:
        fig, ax = plt.subplots(figsize=(3.4, 3.0))
    else:
        fig = ax.figure
    xs, ys = df[x].values, df[y].values
    grid = np.quantile(xs, np.linspace(0.15, 0.85, 30))

    def sse(bp):
        m1, m2 = xs <= bp, xs > bp
        if m1.sum() < 3 or m2.sum() < 3:
            return np.inf
        c1 = np.polyfit(xs[m1], ys[m1], 1)
        c2 = np.polyfit(xs[m2], ys[m2], 1)
        r = np.concatenate([ys[m1] - np.polyval(c1, xs[m1]),
                            ys[m2] - np.polyval(c2, xs[m2])])
        return np.sum(r ** 2)

    bp = min(grid, key=sse)
    m1, m2 = xs <= bp, xs > bp
    c1, c2 = np.polyfit(xs[m1], ys[m1], 1), np.polyfit(xs[m2], ys[m2], 1)
    ax.scatter(xs, ys, s=14, color=color(4), alpha=0.7)
    x1 = np.linspace(xs.min(), bp, 50)
    x2 = np.linspace(bp, xs.max(), 50)
    ax.plot(x1, np.polyval(c1, x1), color=color(0), linewidth=2.0)
    ax.plot(x2, np.polyval(c2, x2), color=color(0), linewidth=2.0)
    ax.axvline(bp, color="gray", linestyle="--", linewidth=1.0)
    ax.text(0.95, 0.95, f"Breakpoint: {bp:.1f}", transform=ax.transAxes,
            ha="right", va="top", fontsize=9, fontweight="bold")
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    return fig, ax


# ================================================================ 模型评估图
def roc_curve(y_true, scores_dict: dict, ax=None):
    """ROC 曲线。scores_dict: {模型名: 预测概率}。"""
    _prep()
    from sklearn.metrics import roc_curve as sk_roc, auc
    if ax is None:
        fig, ax = plt.subplots(figsize=(3.4, 3.0))
    else:
        fig = ax.figure
    for i, (name, s) in enumerate(scores_dict.items()):
        fpr, tpr, _ = sk_roc(y_true, s)
        ax.plot(fpr, tpr, color=color(i), linewidth=1.8,
                label=f"{name} (AUC = {auc(fpr, tpr):.2f})")
    ax.plot([0, 1], [0, 1], color="gray", linestyle="--", linewidth=1.0)
    ax.set_xlabel("1 - Specificity")
    ax.set_ylabel("Sensitivity")
    ax.legend(loc="lower right")
    return fig, ax


def dca_curve(y_true, scores_dict: dict, ax=None):
    """决策曲线分析 (DCA)。scores_dict: {模型名: 预测概率}。"""
    _prep()
    if ax is None:
        fig, ax = plt.subplots(figsize=(3.6, 3.0))
    else:
        fig = ax.figure
    thresholds = np.linspace(0.01, 0.99, 99)
    y_true = np.asarray(y_true)
    prevalence = y_true.mean()
    for i, (name, s) in enumerate(scores_dict.items()):
        nb = []
        for pt in thresholds:
            pred = np.asarray(s) >= pt
            tp = np.sum(pred & (y_true == 1))
            fp = np.sum(pred & (y_true == 0))
            nb.append(tp / len(y_true) - fp / len(y_true) * pt / (1 - pt))
        ax.plot(thresholds, nb, color=color(i), linewidth=1.8, label=name)
    nb_all = prevalence - (1 - prevalence) * thresholds / (1 - thresholds)
    ax.plot(thresholds, nb_all, color="gray", linestyle="--", linewidth=1.2,
            label="All")
    ax.axhline(0, color="black", linewidth=1.0, linestyle=":", label="None")
    ax.set_xlabel("Threshold probability")
    ax.set_ylabel("Net benefit")
    ax.set_ylim(-0.05, max(prevalence * 1.4, 0.15))
    ax.legend()
    return fig, ax


def calibration_curve(y_true, scores_dict: dict, ax=None, n_bins=8):
    """校准曲线。"""
    _prep()
    from sklearn.calibration import calibration_curve as sk_cal
    if ax is None:
        fig, ax = plt.subplots(figsize=(3.4, 3.0))
    else:
        fig = ax.figure
    ax.plot([0, 1], [0, 1], color="gray", linestyle="--", linewidth=1.0,
            label="Ideal")
    for i, (name, s) in enumerate(scores_dict.items()):
        frac, mean_pred = sk_cal(y_true, s, n_bins=n_bins)
        ax.plot(mean_pred, frac, color=color(i), marker="o", linewidth=1.8,
                label=name)
    ax.set_xlabel("Predicted probability")
    ax.set_ylabel("Observed frequency")
    ax.legend()
    return fig, ax


def confusion_matrix_plot(cm: np.ndarray, labels=("0", "1"), ax=None):
    """混淆矩阵热图。"""
    _prep()
    if ax is None:
        fig, ax = plt.subplots(figsize=(3.0, 2.8))
    else:
        fig = ax.figure
    im = ax.imshow(cm, cmap=SEQ_CMAP)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    fontsize=12, fontweight="bold",
                    color="white" if cm[i, j] > cm.max() * 0.6 else "black")
    ax.set_xticks(range(len(labels)), labels)
    ax.set_yticks(range(len(labels)), labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix", fontsize=10)
    return fig, ax


# ================================================================ 分布与其他
def violin_plot(df, x, y, ax=None, show_box=True):
    """小提琴图(内嵌迷你箱线)。"""
    _prep()
    if ax is None:
        fig, ax = plt.subplots(figsize=(3.4, 3.0))
    else:
        fig = ax.figure
    cats = list(df[x].unique())
    data = [df[df[x] == c][y].dropna() for c in cats]
    parts = ax.violinplot(data, showextrema=False, widths=0.7)
    for i, pc in enumerate(parts["bodies"]):
        pc.set_facecolor(color(i))
        pc.set_alpha(0.7)
        pc.set_edgecolor("black")
        pc.set_linewidth(1.0)
    if show_box:
        ax.boxplot(data, positions=np.arange(1, len(cats) + 1), widths=0.12,
                   patch_artist=True, showfliers=False,
                   boxprops=dict(facecolor="white", linewidth=1.0),
                   medianprops=dict(color="black", linewidth=1.2),
                   whiskerprops=dict(linewidth=1.0), capprops=dict(linewidth=1.0))
    ax.set_xticks(np.arange(1, len(cats) + 1), cats)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    return fig, ax


def sankey_plot(flows: pd.DataFrame, ax=None, source_col="source",
                target_col="target", value_col="value"):
    """
    简洁桑基图。flows: source/target/value 三列流表。
    """
    _prep()
    if ax is None:
        fig, ax = plt.subplots(figsize=(4.6, 3.4))
    else:
        fig = ax.figure
    sources = list(dict.fromkeys(flows[source_col]))
    targets = list(dict.fromkeys(flows[target_col]))
    s_tot = flows.groupby(source_col)[value_col].sum()
    t_tot = flows.groupby(target_col)[value_col].sum()
    total = s_tot.sum()

    def layout(names, totals, x):
        y = 0.0
        pos = {}
        gap = total * 0.06
        for n in names:
            h = totals[n]
            pos[n] = (x, y, y + h)
            y += h + gap
        return pos, y - gap

    s_pos, _ = layout(sources, s_tot, 0.0)
    t_pos, _ = layout(targets, t_tot, 1.0)
    s_off = {n: s_pos[n][1] for n in sources}
    t_off = {n: t_pos[n][1] for n in targets}
    norm = 1.0

    for k, (_, row) in enumerate(flows.iterrows()):
        s, t, v = row[source_col], row[target_col], row[value_col]
        y0, y1 = s_off[s], s_off[s] + v
        y2, y3 = t_off[t], t_off[t] + v
        verts = [(0.08, y0), (0.5, y0), (0.5, y2), (0.92, y2),
                 (0.92, y3), (0.5, y3), (0.5, y1), (0.08, y1), (0.08, y0)]
        codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
                 Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), facecolor=color(k),
                               alpha=0.45, edgecolor="none"))
        s_off[s] += v
        t_off[t] += v
    for i, n in enumerate(sources):
        x, y0, y1 = s_pos[n]
        ax.add_patch(plt.Rectangle((0.0, y0), 0.08, y1 - y0,
                                   facecolor=color(i), edgecolor="black"))
        ax.text(-0.02, (y0 + y1) / 2, str(n), ha="right", va="center",
                fontsize=10, fontweight="bold")
    for i, n in enumerate(targets):
        x, y0, y1 = t_pos[n]
        ax.add_patch(plt.Rectangle((0.92, y0), 0.08, y1 - y0,
                                   facecolor=color(i + len(sources)),
                                   edgecolor="black"))
        ax.text(1.02, (y0 + y1) / 2, str(n), ha="left", va="center",
                fontsize=10, fontweight="bold")
    ax.set_xlim(-0.15, 1.15)
    ax.set_ylim(-total * 0.05, total * 1.3)
    ax.axis("off")
    return fig, ax


# ================================================================ 组合图
def combined_figure(panels, nrows, ncols, path_base, figsize=None,
                    labels="ABCDEFGH"):
    """
    组合图: 依次调用绘图函数并加 A/B/C/D 面板标签,统一保存。
    panels: [lambda ax: box_plot(df, 'Group', 'Value', ax=ax), ...]
    """
    from style import make_panels, panel_label
    fig, axes = make_panels(nrows, ncols, figsize)
    for i, fn in enumerate(panels):
        fn(axes[i])
        panel_label(axes[i], labels[i])
    for j in range(len(panels), len(axes)):
        axes[j].axis("off")
    fig.tight_layout()
    return save_figure(fig, path_base)
