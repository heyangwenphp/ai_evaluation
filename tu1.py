from pyecharts import options as opts
from pyecharts.charts import Bar

# ================================
# 数据准备
# ================================
models = [
    "DeepSeek-R1",
    "GPT-4.5-Preview",
    "gemini-2.5-pro-exp-03-25",
    "Claude 3.7 Sonnet(Extended)",
    "ChatGPT-4o-latest",
    "DeepSeek-V3-0324",
    "doubao-1.5-pro-32k",
    "qwen-max-latest",
    "QwQ-32B",
    "o3-mini(high)",
    "gemini-2.0-flash",
    "ernie-4.5-8k-preview",
]

scores = [86.02, 85.30, 84.95, 84.23, 83.15, 82.80, 81.72, 79.93, 78.85, 78.78, 78.49, 77.78]

# 橙色模型（仅为了配色区分）
orange_models = {
    "GPT-4.5-Preview",
    "ChatGPT-4o-latest",
    "o3-mini(high)",
    "gemini-2.0-flash"
}

# 按颜色分两组
blue_data = [s if m not in orange_models else None for m, s in zip(models, scores)]
orange_data = [s if m in orange_models else None for m, s in zip(models, scores)]

# ================================
# 绘制图表
# ================================
bar = (
    Bar(init_opts=opts.InitOpts(width="800px", height="600px", bg_color="#ffffff"))
    .add_xaxis(models[::-1])  # 倒序排列（从上到下）
    .add_yaxis("蓝色组", blue_data[::-1], color="#5B8FF9", label_opts=opts.LabelOpts(position="right", color="#000"))
    .add_yaxis("橙色组", orange_data[::-1], color="#FF9F40", label_opts=opts.LabelOpts(position="right", color="#000"))
    .reversal_axis()  # 横向
    .set_global_opts(
        title_opts=opts.TitleOpts(
            title="SuperCLUE-Fact中文事实性幻觉测评总榜",
            subtitle="数据来源：SuperCLUE, 2025年4月14日",
            pos_left="center",
            title_textstyle_opts=opts.TextStyleOpts(font_size=20)
        ),
        xaxis_opts=opts.AxisOpts(
            name="",
            axislabel_opts=opts.LabelOpts(formatter="{value}"),
            splitline_opts=opts.SplitLineOpts(is_show=True),
        ),
        yaxis_opts=opts.AxisOpts(
            axislabel_opts=opts.LabelOpts(font_size=12),
        ),
        #显示全部图例
        legend_opts=opts.LegendOpts(is_show=False),
        tooltip_opts=opts.TooltipOpts(is_show=False),
    )
    .set_series_opts(
        bar_width="30%",
        label_opts=opts.LabelOpts(is_show=True, position="right", formatter="{c}")
    )
)

# ================================
# 导出 HTML
# ================================
bar.render("superclue_fact_ranking.html")

# ================================
# 如需导出图片（可选）
# ================================
# pip install snapshot-selenium
from pyecharts.render import make_snapshot
from snapshot_selenium import snapshot
make_snapshot(snapshot, bar.render(), "superclue_fact_ranking.png")
