import pandas as pd

import gtviz
from gtviz import io


def test_save_formats(tmp_path):
    fig, ax = gtviz.dot_plot([10, 20], ["a", "b"])
    paths = io.save(fig, "demo", formats=("png", "svg", "pdf"), directory=tmp_path)
    assert [p.suffix for p in paths] == [".png", ".svg", ".pdf"]
    assert all(p.exists() and p.stat().st_size > 0 for p in paths)


def test_figure_to_html_svg_and_png():
    fig, ax = gtviz.dot_plot([10, 20], ["a", "b"])
    frag_svg = io.figure_to_html(fig, embed="svg")
    assert frag_svg.startswith('<div class="gtviz-figure"><svg')
    frag_png = io.figure_to_html(fig, embed="png")
    assert "data:image/png;base64," in frag_png


def test_report_builder_html_and_pdf(tmp_path, survey, output_dir):
    fig, _ = gtviz.dot_plot([62, 48], ["Gave money", "Volunteered"], title="Behaviours")
    table = gtviz.HtmlTable(pd.DataFrame({"Q1": [50], "Q2": [55]}, index=["Gave money"]),
                            title="Table 1")
    report = (
        io.ReportBuilder(title="Q2 Generosity Report")
        .add_heading("Key trends")
        .add_text("Giving held steady this quarter.")
        .add_figure(fig, caption="Figure 1. Generosity behaviours")
        .add_table(table, caption="Table 1. Quarterly comparison")
    )
    html_path = tmp_path / "report.html"
    doc = report.to_html(html_path)
    assert html_path.exists()
    assert "<svg" in doc and "pub-table" in doc and "Q2 Generosity Report" in doc

    pdf_path = report.to_pdf(tmp_path / "report.pdf")
    assert pdf_path.exists() and pdf_path.stat().st_size > 1000

    # keep a copy as a CI artifact for human review
    report.to_html(output_dir / "sample_report.html")


def test_set_options(tmp_path):
    old = gtviz.options.output_dir
    gtviz.set_options(output_dir=tmp_path)
    assert gtviz.options.output_dir == tmp_path
    gtviz.set_options(output_dir=old)
