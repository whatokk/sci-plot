---
name: sci-plot
description: 专业科研绘图统一规范与函数库。当用户需要绘制折线图、箱线图、柱状图、散点拟合图、热图、PCA、RDA/双序图、相关性矩阵、随机森林重要性图、SHAP 摘要图、GAM 拟合图、分段回归阈值图、ROC 曲线、DCA 曲线、校准曲线、桑基图、小提琴图、混淆矩阵,或需要 2x2/2x3 组合图排版、显著性 A/B/C 字母标注、P 值规范显示、600 dpi 高清出图时使用。统一字体(中文宋体/英文 Times New Roman)、统一配色、白底保留图框无网格加粗字体,并附带统计结果 Excel 与 Markdown 说明。
agent_created: true
---

# sci-plot — 专业绘图统一规范

告别反复调图:所有图型共享一套固定规范,从单图到组合图风格完全一致。

## 固定作图规范(不可随意更改)

- **字体**: 中文宋体(SimSun);英文/数字 Times New Roman;全部加粗
- **风格**: 白底、保留四边图框、无网格
- **配色**: 使用 `style.PALETTE` 固定色板,按组序循环取色;热图/相关矩阵用发散色 `RdBu_r`
- **标注**: 组间显著性优先用 A/B/C 紧凑字母(CLD);两两比较用括号 + 星号;P 值规范显示(`P < 0.001` 或 `P = 0.032`)
- **输出**: PNG + PDF + SVG,600 dpi;附带统计结果 Excel(`stats_results.xlsx`)与 Markdown 说明
- **组合图**: 2x2 / 2x3 排版,子图左上角加粗 A/B/C/D 面板标签

## 使用方式

1. 运行环境: 使用托管 Python 虚拟环境
   `C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe`

   依赖: matplotlib / numpy / pandas / scipy / scikit-learn / openpyxl（statsmodels 可选）。
   若缺失先装到该 venv，禁止全局安装：
   ```
   <venv>/Scripts/python.exe -m pip install matplotlib pandas scipy scikit-learn openpyxl
   ```
   **注意**: 本机代理会拦截清华等镜像源（报 "Could not find a version that satisfies
   the requirement"，版本列表为空），此时改用默认 PyPI 源即可。

2. 绘图代码模板:

```python
import sys
sys.path.insert(0, r"C:\Users\Administrator\.workbuddy\skills\sci-plot\scripts")
from style import (apply_style, save_figure, cld_letters, format_pvalue,
                   check_fonts, assert_cjk_ok, PALETTE)
import plots

apply_style()                      # 每次绘图前必须调用
assert_cjk_ok()                    # 字体自检: 中文无法渲染时直接报错
fig, ax = plots.box_plot(df, "Group", "Value", letters=letters)
save_figure(fig, "output/boxplot") # 自动写出 PNG+PDF+SVG @600dpi
```

   **字体（最容易踩的坑）**: 中英文混排靠 `apply_style()` 里的显式字体列表
   `FONT_STACK` 逐字符回退 —— 英文走 Times New Roman、中文走宋体。
   **禁止**改回 `font.family='serif'` + `font.serif=[...]`：那种写法只挑第一个命中的字体，
   会导致「英文正常、中文全变方块」。改动字体相关代码后务必重跑 `assert_cjk_ok()`。
   注意宋体无 bold 字重，中文实际以常规字重呈现（英文仍加粗），相关警告已静音。

3. 图型速查(均在 `scripts/plots.py`):

| 需求 | 函数 |
|---|---|
| 折线图(分组/误差带) | `line_plot(df, x, y, group=)` |
| 箱线图(散点+字母) | `box_plot(df, x, y, letters=)` |
| 柱状图(误差+字母) | `bar_plot(df, x, y, error=, letters=)` |
| 散点拟合(R 与 P) | `scatter_fit(df, x, y)` |
| 聚类热图 | `heatmap(df, cluster=True)` |
| PCA | `pca_plot(df, features, group)` |
| RDA/双序图 | `biplot(df, features, group)` |
| 相关性矩阵气泡图 | `correlation_matrix(corr, pmat=)` |
| 随机森林重要性 | `rf_importance(series)` |
| SHAP 蜂群图 | `shap_summary(shap_values, X)` |
| GAM 平滑拟合 | `gam_fit(df, x, y)` |
| 分段回归(拐点) | `segmented_regression(df, x, y)` |
| ROC | `roc_curve(y_true, {"模型": scores})` |
| DCA 决策曲线 | `dca_curve(y_true, {"模型": scores})` |
| 校准曲线 | `calibration_curve(y_true, {"模型": scores})` |
| 桑基图 | `sankey_plot(flows_df)` |
| 小提琴图 | `violin_plot(df, x, y)` |
| 混淆矩阵 | `confusion_matrix_plot(cm)` |
| 组合图 2x2/2x3 | `combined_figure([lambda ax: ..., ...], nrows, ncols, path)` |

4. 显著性字母: 先做两两检验(t 检验 / Tukey),再用 `cld_letters(groups, pairs_p)` 生成字母,传给 `letters=` 参数。
   默认输出大写 A/B/C;跨字母簇的组会自动带多字母(如 `"AB"`),用于表达
   「A~B 不显著、B~C 不显著、但 A~C 显著」这类传递性场景。需要小写传 `uppercase=False`。

5. 统计结果落盘: 检验统计量、P 值、字母分组、重要性等写入 `stats_results.xlsx`,并附 Markdown 说明(参考 `scripts/demo.py` 末尾写法)。

## 详细规范

更多细节(色板色值、组合图排版规则、常见问题)见 `references/style-guide.md`。
完整可运行示例见 `scripts/demo.py`(生成全部 18 种图 + 2x2 组合图)。
