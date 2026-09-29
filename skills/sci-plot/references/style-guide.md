# sci-plot 作图规范详解

## 1. 色板(固定,按组序循环)

| 序号 | 色值 | 描述 |
|---|---|---|
| 0 | #E8665D | 珊瑚红 |
| 1 | #5FB4A5 | 青绿 |
| 2 | #8F7BB8 | 紫 |
| 3 | #9BB35C | 橄榄绿 |
| 4 | #5B8DB8 | 蓝 |
| 5 | #E8A25D | 橙 |
| 6 | #B85B8D | 品红 |
| 7 | #6BAED6 | 浅蓝 |

- 热图(连续量): `YlGnBu`;相关性/有正负含义的数值: `RdBu_r` 发散色
- 置信椭圆 / 误差带: 与主色同色,alpha 0.12–0.15

## 2. 字体与字号

- 中文: 宋体 (SimSun);英文/数字: Times New Roman;全部 `bold`
- 基准字号 10;轴标题 10、刻度 9、图例 9、面板标签 14(加粗)
- **字体回退机制(重要)**: `apply_style()` 把字体写成一个显式列表
  `["Times New Roman", "SimSun", "NSimSun", "Microsoft YaHei", "SimHei", "DejaVu Serif"]`,
  matplotlib 会**逐字符**回退 —— 英文数字用 Times New Roman,中文用宋体。
  不可改回 `font.family='serif'` + `font.serif=[...]` 的写法:那种写法只挑第一个命中的字体,
  Times New Roman 命中后中文字符全部变方块。
- 自检: `check_fonts()` 返回 `cjk_renderable`(实测渲染无缺字)与 `resolved_cjk`;
  关键出图前可调 `assert_cjk_ok()` 直接拦截,避免静默产出方块图
- **中文字重**: 宋体(SimSun/NSimSun)没有独立 bold 字重,`font.weight='bold'` 对中文
  实际回退为常规字重;英文数字仍是真加粗。这是预期行为,相关警告已在 `apply_style()`
  中静音。若必须中文也加粗,把 `FONT_STACK` 里的中文首选换成 `SimHei` 或
  `Microsoft YaHei`(两者有 bold 变体),但会改变整体字形风格

## 3. 显著性标注规则

1. 多组比较: 先做整体检验(ANOVA/Kruskal),显著后做两两检验,用 CLD 紧凑字母(A/B/C)标注在柱子/箱体顶部
2. 两组比较: 括号 + 星号(`* <0.05, ** <0.01, *** <0.001, ns`)
3. P 值文本: `P < 0.001` 或 `P = 0.032`(三位小数)
4. 同一图中只用一种标注体系,不混用字母和星号
5. `cld_letters()` 用极大团算法,跨簇的组会带多个字母(如 `"AB"`),
   正确表达「A~B 不显著、B~C 不显著、A~C 显著」这类场景;需要小写传 `uppercase=False`

## 4. 组合图排版

- 单图基准尺寸 3.4 x 3.0 英寸;2x2 用 6.8 x 6.0,2x3 用 10.2 x 6.0
- 面板标签 A/B/C/D 置于子图左上角 (-0.12, 1.05),14 号加粗
- 图例统一放子图内部空位或右侧,禁止压数据
- `tight_layout()` 之后直接 `save_figure`,三种格式同版式

## 5. 输出物清单(每次任务)

1. PNG(预览用)+ PDF / SVG(投稿/排版用),全部 600 dpi
2. `stats_results.xlsx`: 各检验统计量、P 值、CLD 字母、重要性表
3. `README.md`: 一句话结论 + 统计结果 + 图清单

## 6. 常见问题

- **中文乱码(方块)**: 九成是字体写法问题,不是字体没装。`apply_style()` 已改为显式字体列表逐字回退;若仍出方块,先 `check_fonts()` 看 `cjk_renderable` / `resolved_cjk`,关键出图前用 `assert_cjk_ok()` 直接拦截。**禁止**改回 `font.family='serif'` + `font.serif=[...]`
- **英文数字正常、只有中文变方块**: 正是上面这条的典型症状(或漏调 `apply_style()`)。rcParams 是全局的,每个绘图脚本开头必须调一次
- **负号显示为方块**: `axes.unicode_minus` 已在 style 中设为 False,勿覆盖
- **PDF 字体嵌入问题**: `pdf.fonttype=42` 已设置;SVG 用文字而非路径(`svg.fonttype='none'`)
- **箱线图离群点重影**: 库内默认关掉 flier marker 并叠加 jitter 散点,勿重复开启
- **SHAP 图**: 接受任意 (n, m) 矩阵,不强制安装 shap 库;若有 shap 库可用 `shap_values.values` 直接传入
