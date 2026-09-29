# 科研绘图统一规范与函数库

告别反复调图——所有图型共享一套固定规范，从单图到组合图风格完全一致。

## 技能清单

| 技能 | 说明 |
|---|---|
| **sci-plot** · 科研绘图库 | 17+ 图型 + 组合图排版 + 统一字体配色 + 600dpi 高清出图。 |

## 安装

把 `skills/` 下的技能目录拷贝到 WorkBuddy 的技能目录：

```bash
cp -r skills/* ~/.workbuddy/skills/
```

Windows PowerShell：

```powershell
Copy-Item .\skills\* "$env:USERPROFILE\.workbuddy\skills\" -Recurse -Force
```

重启 WorkBuddy 后，技能列表即可看到。

## 使用要点

- **支持图型**：折线图、箱线图、柱状图、散点拟合图、热图、PCA、RDA/双序图、相关性矩阵、随机森林重要性图、SHAP 摘要图、GAM 拟合图、分段回归阈值图、ROC 曲线、DCA 曲线、校准曲线、桑基图、小提琴图、混淆矩阵。
- **固定规范**：统一字体（中文宋体 / 英文 Times New Roman）、统一配色、白底保留图框无网格加粗字体、600 dpi、2×2 / 2×3 组合图排版、显著性 A/B/C 字母标注、P 值规范显示。附带统计结果 Excel 与 Markdown 说明。
- 核心文件：`scripts/style.py`（规范）、`scripts/plots.py`（图型函数）、`scripts/demo.py`（示例）、`references/style-guide.md`。

## 环境依赖

- Python 3.13
- matplotlib / seaborn / scipy / scikit-learn

## 目录规范

```
sci-plot/
└── skills/
    ├── sci-plot/
```

每个技能遵循统一结构：`SKILL.md`（必需，含 name/description frontmatter）+ `scripts/`（可选）+ `references/`（可选）。

---

## License

MIT — 随意取用、修改、二次分发。
