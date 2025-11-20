from pyecharts.charts import Bar
from pyecharts import options as opts

# ================================
# 数据准备
# ================================
x_data = ["总分", "深度检索能力", "研究分析能力", "实践应用能力", "规划咨询能力"]
china_scores = [50.06, 16.36, 84.27, 31.51, 73.01]
oversea_scores = [63.41, 38.64, 84.89, 55.40, 78.52]

# ================================
# 绘制柱状图
# ================================
bar = (
    Bar(init_opts=opts.InitOpts(width="900px", height="600px", bg_color="#ffffff"))
    .add_xaxis(x_data)
    .add_yaxis(
        "国内平均分",
        china_scores,
        color="#5B8FF9",  # 蓝色
        label_opts=opts.LabelOpts(is_show=True, position="top", color="#000", font_size=12),
        category_gap="40%"
    )
    .add_yaxis(
        "海外平均分",
        oversea_scores,
        color="#FF9F40",  # 橙色
        label_opts=opts.LabelOpts(is_show=True, position="top", color="#000", font_size=12),
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(
            title="国内外深度研究产品平均分对比",
            pos_left="center",
            title_textstyle_opts=opts.TextStyleOpts(font_size=20)
        ),
        legend_opts=opts.LegendOpts(pos_top="5%", pos_right="center"),
        xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(font_size=12)),
        yaxis_opts=opts.AxisOpts(
            name="得分",
            max_=100,
            axislabel_opts=opts.LabelOpts(formatter="{value}.00"),
            splitline_opts=opts.SplitLineOpts(is_show=True),
        ),
        tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="shadow"),
    )
    .set_series_opts(label_opts=opts.LabelOpts(is_show=True))
)

# ================================
# 输出结果
# ================================
bar.render("china_vs_oversea_score.html")

# 如果要导出成 PNG 图片（需安装 snapshot-selenium）
# pip install snapshot-selenium
from pyecharts.render import make_snapshot
from snapshot_selenium import snapshot
make_snapshot(snapshot, bar.render(), "china_vs_oversea_score.png")
