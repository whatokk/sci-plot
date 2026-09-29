# -*- coding: utf-8 -*-
"""
sci-plot 统一作图风格模块
=========================
固定规范(与用户「专业绘图 Skill」海报一致):
- 字体: 中文宋体(SimSun); 英文/数字 Times New Roman
- 风格: 白底、保留图框(四边 spine)、无网格、加粗字体
- 标注: 显著性优先使用 A/B/C 字母;P 值规范显示 (P < 0.001)
- 输出: PNG / PDF / SVG,600 dpi
- 组合图: 子图左上角加粗 A/B/C/D 标签,统一字体/配色/图例位置

用法:
    from style import apply_style, PALETTE, save_figure, panel_label, format_pvalue
    apply_style()
"""
from __future__ import annotations

import os
import logging
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

# 宋体/黑体没有独立的 bold 字重, matplotlib 每次解析都会打一条 "Failed to find
# font weight bold" 警告。这是预期行为(中文以 regular 字重呈现), 噪音过滤掉。
class _FontWeightNoiseFilter(logging.Filter):
    def filter(self, record) -> bool:
        return "Failed to find font weight" not in record.getMessage()

# ---------------------------------------------------------------- 配色
# 主色板(柔和学术风,循环取用)
PALETTE = [
    "#E8665D",  # 珊瑚红
    "#5FB4A5",  # 青绿
    "#8F7BB8",  # 紫
    "#9BB35C",  # 橄榄绿
    "#5B8DB8",  # 蓝
    "#E8A25D",  # 橙
    "#B85B8D",  # 品红
    "#6BAED6",  # 浅蓝
]

# 发散色(热图/相关性矩阵,蓝-白-红)
DIVERGING_CMAP = "RdBu_r"
# 连续色(热图)
SEQ_CMAP = "YlGnBu"

# ---------------------------------------------------------------- 字体栈
# 逐字回退顺序: 英文/数字命中 Times New Roman, 中文命中 SimSun;
# 后续为中文兜底字体,保证任一 Windows 环境中文都不会变方块。
FONT_STACK = [
    "Times New Roman",   # 英文 / 数字
    "SimSun",            # 中文 宋体
    "NSimSun",           # 中文 新宋体
    "Microsoft YaHei",   # 中文兜底 微软雅黑
    "SimHei",            # 中文兜底 黑体
    "DejaVu Serif",      # 最后兜底(无中文,仅保证不报错)
]

# 中文字形测试串(用于 check_fonts 验证真实渲染能力)
_CJK_PROBE = "中文宋体测试"

# 栈中的中文字体候选(用于报告实际生效的中文字体)
CJK_FONTS = ["SimSun", "NSimSun", "Microsoft YaHei", "SimHei"]


def color(i: int) -> str:
    """按序号取主色板颜色(循环)。"""
    return PALETTE[i % len(PALETTE)]


# ---------------------------------------------------------------- 全局风格
def apply_style(base_size: int = 10) -> None:
    """应用统一作图规范。每次绘图前调用一次。"""
    # 静音宋体 bold 字重缺失警告(幂等)
    _fm_log = logging.getLogger("matplotlib.font_manager")
    if not any(isinstance(f, _FontWeightNoiseFilter) for f in _fm_log.filters):
        _fm_log.addFilter(_FontWeightNoiseFilter())

    plt.rcParams.update({
        # 字体: 英文/数字 Times New Roman, 中文宋体
        # 注意: 必须用「字体名列表」而非 family='serif' + font.serif。
        # 后者只在列表里选第一个命中的字体,不做逐字回退 ——
        # 结果就是 Times New Roman 命中后,中文字符全部渲染成方块(tofu)。
        # 写成显式列表后 matplotlib 才会按字符逐个回退到宋体。
        "font.family": FONT_STACK,
        "font.serif": FONT_STACK,
        "mathtext.fontset": "stix",
        "axes.unicode_minus": False,
        # 加粗
        "font.weight": "bold",
        "axes.labelweight": "bold",
        "axes.titleweight": "bold",
        # 字号
        "font.size": base_size,
        "axes.titlesize": base_size + 1,
        "axes.labelsize": base_size,
        "xtick.labelsize": base_size - 1,
        "ytick.labelsize": base_size - 1,
        "legend.fontsize": base_size - 1,
        # 图框: 保留四边, 无网格, 白底
        "axes.grid": False,
        "axes.facecolor": "white",
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "axes.spines.top": True,
        "axes.spines.right": True,
        "axes.linewidth": 1.0,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.width": 1.0,
        "ytick.major.width": 1.0,
        # 线条
        "lines.linewidth": 1.8,
        "lines.markersize": 5,
        # 输出
        "savefig.dpi": 600,
        "savefig.bbox": "tight",
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "legend.frameon": False,
    })


def check_fonts(verbose: bool = False) -> dict:
    """
    检查字体可用性,并实测中文能否真正渲染。

    返回值:
        {
          "Times New Roman": bool,      # 英文/数字字体是否安装
          "SimSun (宋体)": bool,        # 中文宋体是否安装
          "cjk_renderable": bool,       # 中文是否可真实渲染(不会变方块)
          "resolved_cjk": str | None,   # 实际负责中文的字体名
        }

    注意: 光看字体是否安装是不够的 —— 字体装了但没进 font.family 列表,
    中文照样渲染成方块。所以这里用一次真实渲染 + 捕获缺字警告来判定。
    """
    import warnings

    installed = {f.name for f in font_manager.fontManager.ttflist}
    result = {
        "Times New Roman": "Times New Roman" in installed,
        "SimSun (宋体)": "SimSun" in installed,
    }

    # 实测渲染
    fig = plt.figure(figsize=(1, 1))
    fig.text(0.1, 0.5, _CJK_PROBE)
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            fig.canvas.draw()
            missing = [str(x.message) for x in w
                       if "missing from font" in str(x.message).lower()]
        result["cjk_renderable"] = not missing
        if verbose and missing:
            print("[sci-plot] 中文缺字警告:", missing[:3])
    finally:
        plt.close(fig)

    # 找出字体栈里实际承担中文的字体(按栈序第一个已安装的中文字体)
    result["resolved_cjk"] = next((n for n in FONT_STACK if n in CJK_FONTS and n in installed), None)
    if result["resolved_cjk"] is None:
        result["cjk_renderable"] = False
    return result


def assert_cjk_ok() -> None:
    """自检: 中文无法渲染时直接抛错,避免静默产出方块图。"""
    info = check_fonts()
    if not info["cjk_renderable"]:
        raise RuntimeError(
            "sci-plot 字体自检失败: 中文无法渲染(会变成方块)。"
            "请确认已调用 apply_style(),且系统安装了 SimSun / Microsoft YaHei。"
        )


# ---------------------------------------------------------------- 输出
def save_figure(fig, path_base: str, formats=("png", "pdf", "svg"), dpi: int = 600) -> list:
    """
    按统一规范保存图片。
    path_base: 不带扩展名的路径, 如 'output/boxplot'
    返回实际写出的文件路径列表。
    """
    os.makedirs(os.path.dirname(os.path.abspath(path_base)), exist_ok=True)
    written = []
    for fmt in formats:
        p = f"{path_base}.{fmt}"
        fig.savefig(p, format=fmt, dpi=dpi)
        written.append(p)
    plt.close(fig)
    return written


# ---------------------------------------------------------------- 组合图
def panel_label(ax, label: str, x: float = -0.12, y: float = 1.05, size: int = 14) -> None:
    """在子图左上角添加加粗面板标签 (A/B/C/D)。"""
    ax.text(x, y, label, transform=ax.transAxes,
            fontsize=size, fontweight="bold", va="bottom", ha="left")


def make_panels(nrows: int, ncols: int, figsize=None):
    """创建组合图画布,返回 (fig, axes_flat)。"""
    if figsize is None:
        figsize = (3.4 * ncols, 3.0 * nrows)
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    axes_flat = np.atleast_1d(axes).ravel()
    return fig, axes_flat


# ---------------------------------------------------------------- P 值与显著性
def format_pvalue(p: float) -> str:
    """规范显示 P 值: P < 0.001 / P = 0.032。"""
    if p < 0.001:
        return "P < 0.001"
    return f"P = {p:.3f}"


def p_to_stars(p: float) -> str:
    """P 值转星号: *** <0.001, ** <0.01, * <0.05, ns 否则。"""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


def cld_letters(labels, pairs_p: dict, uppercase: bool = True) -> dict:
    """
    紧凑字母表示法 (Compact Letter Display)。
    labels: 组名列表
    pairs_p: {(组A, 组B): p值} — p >= 0.05 视为无显著差异;未给出的对按「有差异」处理
    返回 {组名: 字母}, 无显著差异的组共享字母;跨簇的组会带多个字母(如 "AB")。

    实现: 在「无显著差异图」上用 Bron-Kerbosch 求极大团,每个极大团一个字母。
    比贪心算法更严谨 —— 能正确处理 A~B 不显著、B~C 不显著、但 A~C 显著
    这类传递性场景(贪心会给 B 单独一个字母,标准 CLD 应给 B "AB")。
    """
    import string

    labels = list(labels)
    n = len(labels)
    # 邻接表只存「非显著」邻居,不能含自身 —— 含自环会让 Bron-Kerbosch 无限递归
    adj = {l: set() for l in labels}
    for (a, b), p in pairs_p.items():
        if a in adj and b in adj and a != b and p >= 0.05:
            adj[a].add(b)
            adj[b].add(a)

    # 组数过多时极大团可能爆炸,退回贪心(实用场景下极少触发)
    if n > 15:
        assigned, letters = [], {}
        for l in labels:
            placed = False
            for grp in assigned:
                if all(l in adj[g] for g in grp):
                    grp.append(l)
                    placed = True
                    break
            if not placed:
                assigned.append([l])
        for i, grp in enumerate(assigned):
            ch = string.ascii_uppercase[i] if i < 26 else f"A{i}"
            for l in grp:
                letters[l] = ch
        return letters

    # Bron-Kerbosch 求极大团
    cliques: list = []

    def bk(R, P, X):
        if not P and not X:
            cliques.append(set(R))
            return
        for v in list(P):
            bk(R | {v}, P & adj[v], X & adj[v])
            P = P - {v}
            X = X | {v}

    bk(set(), set(labels), set())
    # 大团优先分配靠前的字母,顺序稳定
    cliques.sort(key=lambda c: (-len(c), [labels.index(x) for x in sorted(c)]))
    if not cliques:
        cliques = [{l} for l in labels]

    alphabet = string.ascii_uppercase if uppercase else string.ascii_lowercase
    letters = {l: "" for l in labels}
    for i, c in enumerate(cliques):
        ch = alphabet[i] if i < 26 else f"{alphabet[0]}{i}"
        for l in c:
            letters[l] += ch
    return letters


def add_sig_letters(ax, x_positions, y_tops, letters, y_offset=None, size=10) -> None:
    """
    在柱状图/箱线图各组顶部标注显著性字母。
    自动扩展 y 轴,保证所有字母上方有足够留白(不会被图框裁切或贴边)。
    """
    lo, hi = ax.get_ylim()
    yr = hi - lo if hi > lo else 1.0
    if y_offset is None:
        y_offset = 0.04 * yr
    top = max(y_tops) + y_offset if len(y_tops) else 0.0
    # 字母自身高度约 0.035*yr, 再留 0.065*yr 空隙, 共 0.10*yr
    need = top + 0.10 * yr
    if hi < need:
        ax.set_ylim(lo, need)
    for x, y, s in zip(x_positions, y_tops, letters):
        ax.text(x, y + y_offset, s, ha="center", va="bottom",
                fontsize=size, fontweight="bold")


def add_pvalue_bracket(ax, x1, x2, y, p, tick=0.02, size=9) -> None:
    """绘制两组间显著性括号 + P 值/星号。y 为括号高度, tick 为竖线相对长度(轴比例)。"""
    yr = np.ptp(ax.get_ylim())
    t = tick * yr
    ax.plot([x1, x1, x2, x2], [y, y + t, y + t, y], lw=1.0, c="black", clip_on=False)
    ax.text((x1 + x2) / 2, y + t, p_to_stars(p), ha="center", va="bottom",
            fontsize=size, fontweight="bold")
