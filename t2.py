from pyecharts.charts import Bar
from pyecharts import options as opts

# ======================
# 模拟数据
# ======================
x_data = [
    "最优大小", "适合上身", "舒适 4", "Onepiece RX", "星灵平衡 Plus",
    "雅虎 120Hz", "Kony V1", "DL4.4", "Mindbar M1", "光子一号 X1"
]

y_data = {
    "标准核心体验度": [100, 85, 80, 78, 60, 95, 80, 65, 60, 70],
    "视频通话表现": [88, 82, 65, 75, 70, 50, 60, 58, 66, 60],
    "摄像镜头效果": [85, 79, 60, 45, 72, 78, 65, 55, 70, 62],
    "处理器负载表现": [90, 81, 78, 72, 68, 76, 64, 60, 68, 65],
}

# ======================
# 创建 ECharts 柱状图
# ======================
bar = (
    Bar()
    .add_xaxis(x_data)
    .add_yaxis("标准核心体验度", y_data["标准核心体验度"], category_gap="30%", gap="0%")
    .add_yaxis("视频通话表现", y_data["视频通话表现"])
    .add_yaxis("摄像镜头效果", y_data["摄像镜头效果"])
    .add_yaxis("处理器负载表现", y_data["处理器负载表现"])
    .set_global_opts(
        title_opts=opts.TitleOpts(title="产品性能对比"),
        xaxis_opts=opts.AxisOpts(axislabel_opts={"rotate": 20}),
        yaxis_opts=opts.AxisOpts(name="平均得分 (%)"),
        legend_opts=opts.LegendOpts(pos_top="5%"),
        tooltip_opts=opts.TooltipOpts(trigger="axis"),
    )
    .set_series_opts(
        label_opts=opts.LabelOpts(is_show=False)
    )
)

# 渲染到 HTML（可直接打开看效果）
bar.render("multi_bar_chart.html")

# 如果需要生成图片：
#   pip install snapshot-selenium
#   并配置好 ChromeDriver（参考上一步）
# 然后执行：
# from pyecharts.render import make_snapshot
# from snapshot_selenium import snapshot
# make_snapshot(snapshot, bar.render(), "multi_bar_chart.png")
from pyecharts.render import make_snapshot
from snapshot_phantomjs import snapshot
make_snapshot(snapshot, bar.render(), "multi_bar_chart.png")
