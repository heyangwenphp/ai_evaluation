from pyecharts.charts import Bar
from pyecharts import options as opts
from docx import Document
from docx.shared import Inches
import os

#pip3 install snapshot-selenium
#pip3 snapshot-selenium
#pip3 install snapshot-phantomjs
# ========== 1. 使用 pyecharts 生成 ECharts 图表 ==========
def create_chart_image(output_path="chart.png"):
    # 构造示例数据
    bar = (
        Bar()
        .add_xaxis(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
        .add_yaxis("Sales", [120, 200, 150, 80, 70, 110, 130])
        .set_global_opts(
            title_opts=opts.TitleOpts(title="Weekly Sales", subtitle="ECharts 示例"),
            xaxis_opts=opts.AxisOpts(name="Day"),
            yaxis_opts=opts.AxisOpts(name="Sales Volume"),
        )
    )

    # 渲染为 HTML 文件
    html_path = "chart.html"
    bar.render(html_path)

    # # 使用 snapshot-selenium 将图表保存为 PNG 图片
    from pyecharts.render import make_snapshot
    from snapshot_phantomjs import snapshot
    make_snapshot(snapshot, bar.render(), output_path)
    print(output_path)
    return output_path

# ========== 2. 创建 Word 文档并插入图片 ==========
def export_to_word(image_path):
    doc = Document()
    print("doc")
    doc.add_heading("销售数据报告", level=1)
    print("销售数据报告")

    # 添加图表说明文字
    doc.add_paragraph("以下是本周销售数据的可视化图表：")
    print("以下是本周销售数据的可视化图表")

    # 插入图片（图表）
    doc.add_picture(image_path, width=Inches(5.5))
    print("插入图片")

    doc.add_paragraph("从图表可以看出，周二的销售额最高。")
    print("从图表可以看出，周二的销售额最高。")

    output_file = "销售报告.docx"
    doc.save(output_file)
    print(f"✅ Word 导出成功: {output_file}")

# ========== 主函数 ==========
if __name__ == "__main__":
    # 如果第一次运行，请确保安装 selenium + ChromeDriver
    img = create_chart_image("sales_chart.png")
    export_to_word(img)
