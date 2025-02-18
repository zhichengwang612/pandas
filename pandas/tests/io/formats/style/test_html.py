from textwrap import dedent

import numpy as np
import pytest

from pandas import (
    DataFrame,
    MultiIndex,
    option_context,
)

jinja2 = pytest.importorskip("jinja2")
from pandas.io.formats.style import Styler

loader = jinja2.PackageLoader("pandas", "io/formats/templates")
env = jinja2.Environment(loader=loader, trim_blocks=True)


@pytest.fixture
def styler():
    return Styler(DataFrame([[2.61], [2.69]], index=["a", "b"], columns=["A"]))


@pytest.fixture
def styler_mi():
    midx = MultiIndex.from_product([["a", "b"], ["c", "d"]])
    return Styler(DataFrame(np.arange(16).reshape(4, 4), index=midx, columns=midx))


@pytest.fixture
def tpl_style():
    return env.get_template("html_style.tpl")


@pytest.fixture
def tpl_table():
    return env.get_template("html_table.tpl")


def test_html_template_extends_options():
    # make sure if templates are edited tests are updated as are setup fixtures
    # to understand the dependency
    with open("pandas/io/formats/templates/html.tpl") as file:
        result = file.read()
    assert "{% include html_style_tpl %}" in result
    assert "{% include html_table_tpl %}" in result


def test_exclude_styles(styler):
    result = styler.to_html(exclude_styles=True, doctype_html=True)
    expected = dedent(
        """\
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        </head>
        <body>
        <table>
          <thead>
            <tr>
              <th >&nbsp;</th>
              <th >A</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th >a</th>
              <td >2.610000</td>
            </tr>
            <tr>
              <th >b</th>
              <td >2.690000</td>
            </tr>
          </tbody>
        </table>
        </body>
        </html>
        """
    )
    assert result == expected


def test_w3_html_format(styler):
    styler.set_uuid("").set_table_styles(
        [{"selector": "th", "props": "att2:v2;"}]
    ).applymap(lambda x: "att1:v1;").set_table_attributes(
        'class="my-cls1" style="attr3:v3;"'
    ).set_td_classes(
        DataFrame(["my-cls2"], index=["a"], columns=["A"])
    ).format(
        "{:.1f}"
    ).set_caption(
        "A comprehensive test"
    )
    expected = dedent(
        """\
        <style type="text/css">
        #T_ th {
          att2: v2;
        }
        #T__row0_col0, #T__row1_col0 {
          att1: v1;
        }
        </style>
        <table id="T_" class="my-cls1" style="attr3:v3;">
          <caption>A comprehensive test</caption>
          <thead>
            <tr>
              <th class="blank level0" >&nbsp;</th>
              <th id="T__level0_col0" class="col_heading level0 col0" >A</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th id="T__level0_row0" class="row_heading level0 row0" >a</th>
              <td id="T__row0_col0" class="data row0 col0 my-cls2" >2.6</td>
            </tr>
            <tr>
              <th id="T__level0_row1" class="row_heading level0 row1" >b</th>
              <td id="T__row1_col0" class="data row1 col0" >2.7</td>
            </tr>
          </tbody>
        </table>
        """
    )
    assert expected == styler.to_html()


def test_colspan_w3():
    # GH 36223
    df = DataFrame(data=[[1, 2]], columns=[["l0", "l0"], ["l1a", "l1b"]])
    styler = Styler(df, uuid="_", cell_ids=False)
    assert '<th class="col_heading level0 col0" colspan="2">l0</th>' in styler.to_html()


def test_rowspan_w3():
    # GH 38533
    df = DataFrame(data=[[1, 2]], index=[["l0", "l0"], ["l1a", "l1b"]])
    styler = Styler(df, uuid="_", cell_ids=False)
    assert '<th class="row_heading level0 row0" rowspan="2">l0</th>' in styler.to_html()


def test_styles(styler):
    styler.set_uuid("abc")
    styler.set_table_styles([{"selector": "td", "props": "color: red;"}])
    result = styler.to_html(doctype_html=True)
    expected = dedent(
        """\
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style type="text/css">
        #T_abc td {
          color: red;
        }
        </style>
        </head>
        <body>
        <table id="T_abc">
          <thead>
            <tr>
              <th class="blank level0" >&nbsp;</th>
              <th id="T_abc_level0_col0" class="col_heading level0 col0" >A</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th id="T_abc_level0_row0" class="row_heading level0 row0" >a</th>
              <td id="T_abc_row0_col0" class="data row0 col0" >2.610000</td>
            </tr>
            <tr>
              <th id="T_abc_level0_row1" class="row_heading level0 row1" >b</th>
              <td id="T_abc_row1_col0" class="data row1 col0" >2.690000</td>
            </tr>
          </tbody>
        </table>
        </body>
        </html>
        """
    )
    assert result == expected


def test_doctype(styler):
    result = styler.to_html(doctype_html=False)
    assert "<html>" not in result
    assert "<body>" not in result
    assert "<!DOCTYPE html>" not in result
    assert "<head>" not in result


def test_doctype_encoding(styler):
    with option_context("styler.render.encoding", "ASCII"):
        result = styler.to_html(doctype_html=True)
        assert '<meta charset="ASCII">' in result
        result = styler.to_html(doctype_html=True, encoding="ANSI")
        assert '<meta charset="ANSI">' in result


def test_bold_headers_arg(styler):
    result = styler.to_html(bold_headers=True)
    assert "th {\n  font-weight: bold;\n}" in result
    result = styler.to_html()
    assert "th {\n  font-weight: bold;\n}" not in result


def test_caption_arg(styler):
    result = styler.to_html(caption="foo bar")
    assert "<caption>foo bar</caption>" in result
    result = styler.to_html()
    assert "<caption>foo bar</caption>" not in result


def test_block_names(tpl_style, tpl_table):
    # catch accidental removal of a block
    expected_style = {
        "before_style",
        "style",
        "table_styles",
        "before_cellstyle",
        "cellstyle",
    }
    expected_table = {
        "before_table",
        "table",
        "caption",
        "thead",
        "tbody",
        "after_table",
        "before_head_rows",
        "head_tr",
        "after_head_rows",
        "before_rows",
        "tr",
        "after_rows",
    }
    result1 = set(tpl_style.blocks)
    assert result1 == expected_style

    result2 = set(tpl_table.blocks)
    assert result2 == expected_table


def test_from_custom_template_table(tmpdir):
    p = tmpdir.mkdir("tpl").join("myhtml_table.tpl")
    p.write(
        dedent(
            """\
            {% extends "html_table.tpl" %}
            {% block table %}
            <h1>{{custom_title}}</h1>
            {{ super() }}
            {% endblock table %}"""
        )
    )
    result = Styler.from_custom_template(str(tmpdir.join("tpl")), "myhtml_table.tpl")
    assert issubclass(result, Styler)
    assert result.env is not Styler.env
    assert result.template_html_table is not Styler.template_html_table
    styler = result(DataFrame({"A": [1, 2]}))
    assert "<h1>My Title</h1>\n\n\n<table" in styler.to_html(custom_title="My Title")


def test_from_custom_template_style(tmpdir):
    p = tmpdir.mkdir("tpl").join("myhtml_style.tpl")
    p.write(
        dedent(
            """\
            {% extends "html_style.tpl" %}
            {% block style %}
            <link rel="stylesheet" href="mystyle.css">
            {{ super() }}
            {% endblock style %}"""
        )
    )
    result = Styler.from_custom_template(
        str(tmpdir.join("tpl")), html_style="myhtml_style.tpl"
    )
    assert issubclass(result, Styler)
    assert result.env is not Styler.env
    assert result.template_html_style is not Styler.template_html_style
    styler = result(DataFrame({"A": [1, 2]}))
    assert '<link rel="stylesheet" href="mystyle.css">\n\n<style' in styler.to_html()


def test_caption_as_sequence(styler):
    styler.set_caption(("full cap", "short cap"))
    assert "<caption>full cap</caption>" in styler.to_html()


@pytest.mark.parametrize("index", [False, True])
@pytest.mark.parametrize("columns", [False, True])
@pytest.mark.parametrize("index_name", [True, False])
def test_sticky_basic(styler, index, columns, index_name):
    if index_name:
        styler.index.name = "some text"
    if index:
        styler.set_sticky(axis=0)
    if columns:
        styler.set_sticky(axis=1)

    left_css = (
        "#T_ {0} {{\n  position: sticky;\n  background-color: white;\n"
        "  left: 0px;\n  z-index: {1};\n}}"
    )
    top_css = (
        "#T_ {0} {{\n  position: sticky;\n  background-color: white;\n"
        "  top: {1}px;\n  z-index: {2};\n{3}}}"
    )

    res = styler.set_uuid("").to_html()

    # test index stickys over thead and tbody
    assert (left_css.format("thead tr th:nth-child(1)", "3 !important") in res) is index
    assert (left_css.format("tbody tr th:nth-child(1)", "1") in res) is index

    # test column stickys including if name row
    assert (
        top_css.format("thead tr:nth-child(1) th", "0", "2", "  height: 25px;\n") in res
    ) is (columns and index_name)
    assert (
        top_css.format("thead tr:nth-child(2) th", "25", "2", "  height: 25px;\n")
        in res
    ) is (columns and index_name)
    assert (top_css.format("thead tr:nth-child(1) th", "0", "2", "") in res) is (
        columns and not index_name
    )


@pytest.mark.parametrize("index", [False, True])
@pytest.mark.parametrize("columns", [False, True])
def test_sticky_mi(styler_mi, index, columns):
    if index:
        styler_mi.set_sticky(axis=0)
    if columns:
        styler_mi.set_sticky(axis=1)

    left_css = (
        "#T_ {0} {{\n  position: sticky;\n  background-color: white;\n"
        "  left: {1}px;\n  min-width: 75px;\n  max-width: 75px;\n  z-index: {2};\n}}"
    )
    top_css = (
        "#T_ {0} {{\n  position: sticky;\n  background-color: white;\n"
        "  top: {1}px;\n  height: 25px;\n  z-index: {2};\n}}"
    )

    res = styler_mi.set_uuid("").to_html()

    # test the index stickys for thead and tbody over both levels
    assert (
        left_css.format("thead tr th:nth-child(1)", "0", "3 !important") in res
    ) is index
    assert (left_css.format("tbody tr th.level0", "0", "1") in res) is index
    assert (
        left_css.format("thead tr th:nth-child(2)", "75", "3 !important") in res
    ) is index
    assert (left_css.format("tbody tr th.level1", "75", "1") in res) is index

    # test the column stickys for each level row
    assert (top_css.format("thead tr:nth-child(1) th", "0", "2") in res) is columns
    assert (top_css.format("thead tr:nth-child(2) th", "25", "2") in res) is columns


@pytest.mark.parametrize("index", [False, True])
@pytest.mark.parametrize("columns", [False, True])
@pytest.mark.parametrize("levels", [[1], ["one"], "one"])
def test_sticky_levels(styler_mi, index, columns, levels):
    styler_mi.index.names, styler_mi.columns.names = ["zero", "one"], ["zero", "one"]
    if index:
        styler_mi.set_sticky(axis=0, levels=levels)
    if columns:
        styler_mi.set_sticky(axis=1, levels=levels)

    left_css = (
        "#T_ {0} {{\n  position: sticky;\n  background-color: white;\n"
        "  left: {1}px;\n  min-width: 75px;\n  max-width: 75px;\n  z-index: {2};\n}}"
    )
    top_css = (
        "#T_ {0} {{\n  position: sticky;\n  background-color: white;\n"
        "  top: {1}px;\n  height: 25px;\n  z-index: {2};\n}}"
    )

    res = styler_mi.set_uuid("").to_html()

    # test no sticking of level0
    assert "#T_ thead tr th:nth-child(1)" not in res
    assert "#T_ tbody tr th.level0" not in res
    assert "#T_ thead tr:nth-child(1) th" not in res

    # test sticking level1
    assert (
        left_css.format("thead tr th:nth-child(2)", "0", "3 !important") in res
    ) is index
    assert (left_css.format("tbody tr th.level1", "0", "1") in res) is index
    assert (top_css.format("thead tr:nth-child(2) th", "0", "2") in res) is columns


def test_sticky_raises(styler):
    with pytest.raises(ValueError, match="No axis named bad for object type DataFrame"):
        styler.set_sticky(axis="bad")


@pytest.mark.parametrize(
    "sparse_index, sparse_columns",
    [(True, True), (True, False), (False, True), (False, False)],
)
def test_sparse_options(sparse_index, sparse_columns):
    cidx = MultiIndex.from_tuples([("Z", "a"), ("Z", "b"), ("Y", "c")])
    ridx = MultiIndex.from_tuples([("A", "a"), ("A", "b"), ("B", "c")])
    df = DataFrame([[1, 2, 3], [4, 5, 6], [7, 8, 9]], index=ridx, columns=cidx)
    styler = df.style

    default_html = styler.to_html()  # defaults under pd.options to (True , True)

    with option_context(
        "styler.sparse.index", sparse_index, "styler.sparse.columns", sparse_columns
    ):
        html1 = styler.to_html()
        assert (html1 == default_html) is (sparse_index and sparse_columns)
    html2 = styler.to_html(sparse_index=sparse_index, sparse_columns=sparse_columns)
    assert html1 == html2


@pytest.mark.parametrize("index", [True, False])
@pytest.mark.parametrize("columns", [True, False])
def test_applymap_header_cell_ids(styler, index, columns):
    # GH 41893
    func = lambda v: "attr: val;"
    styler.uuid, styler.cell_ids = "", False
    if index:
        styler.applymap_index(func, axis="index")
    if columns:
        styler.applymap_index(func, axis="columns")

    result = styler.to_html()

    # test no data cell ids
    assert '<td class="data row0 col0" >2.610000</td>' in result
    assert '<td class="data row1 col0" >2.690000</td>' in result

    # test index header ids where needed and css styles
    assert (
        '<th id="T__level0_row0" class="row_heading level0 row0" >a</th>' in result
    ) is index
    assert (
        '<th id="T__level0_row1" class="row_heading level0 row1" >b</th>' in result
    ) is index
    assert ("#T__level0_row0, #T__level0_row1 {\n  attr: val;\n}" in result) is index

    # test column header ids where needed and css styles
    assert (
        '<th id="T__level0_col0" class="col_heading level0 col0" >A</th>' in result
    ) is columns
    assert ("#T__level0_col0 {\n  attr: val;\n}" in result) is columns


@pytest.mark.parametrize("rows", [True, False])
@pytest.mark.parametrize("cols", [True, False])
def test_maximums(styler_mi, rows, cols):
    result = styler_mi.to_html(
        max_rows=2 if rows else None,
        max_columns=2 if cols else None,
    )

    assert ">5</td>" in result  # [[0,1], [4,5]] always visible
    assert (">8</td>" in result) is not rows  # first trimmed vertical element
    assert (">2</td>" in result) is not cols  # first trimmed horizontal element


def test_replaced_css_class_names(styler_mi):
    css = {
        "row_heading": "ROWHEAD",
        # "col_heading": "COLHEAD",
        "index_name": "IDXNAME",
        # "col": "COL",
        "row": "ROW",
        # "col_trim": "COLTRIM",
        "row_trim": "ROWTRIM",
        "level": "LEVEL",
        "data": "DATA",
        "blank": "BLANK",
    }
    midx = MultiIndex.from_product([["a", "b"], ["c", "d"]])
    styler_mi = Styler(
        DataFrame(np.arange(16).reshape(4, 4), index=midx, columns=midx),
        uuid_len=0,
    ).set_table_styles(css_class_names=css)
    styler_mi.index.names = ["n1", "n2"]
    styler_mi.hide_index(styler_mi.index[1:])
    styler_mi.hide_columns(styler_mi.columns[1:])
    styler_mi.applymap_index(lambda v: "color: red;", axis=0)
    styler_mi.applymap_index(lambda v: "color: green;", axis=1)
    styler_mi.applymap(lambda v: "color: blue;")
    expected = dedent(
        """\
    <style type="text/css">
    #T__ROW0_col0 {
      color: blue;
    }
    #T__LEVEL0_ROW0, #T__LEVEL1_ROW0 {
      color: red;
    }
    #T__LEVEL0_col0, #T__LEVEL1_col0 {
      color: green;
    }
    </style>
    <table id="T_">
      <thead>
        <tr>
          <th class="BLANK" >&nbsp;</th>
          <th class="IDXNAME LEVEL0" >n1</th>
          <th id="T__LEVEL0_col0" class="col_heading LEVEL0 col0" >a</th>
        </tr>
        <tr>
          <th class="BLANK" >&nbsp;</th>
          <th class="IDXNAME LEVEL1" >n2</th>
          <th id="T__LEVEL1_col0" class="col_heading LEVEL1 col0" >c</th>
        </tr>
        <tr>
          <th class="IDXNAME LEVEL0" >n1</th>
          <th class="IDXNAME LEVEL1" >n2</th>
          <th class="BLANK col0" >&nbsp;</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th id="T__LEVEL0_ROW0" class="ROWHEAD LEVEL0 ROW0" >a</th>
          <th id="T__LEVEL1_ROW0" class="ROWHEAD LEVEL1 ROW0" >c</th>
          <td id="T__ROW0_col0" class="DATA ROW0 col0" >0</td>
        </tr>
      </tbody>
    </table>
    """
    )
    result = styler_mi.to_html()
    assert result == expected


def test_include_css_style_rules_only_for_visible_cells(styler_mi):
    # GH 43619
    result = (
        styler_mi.set_uuid("")
        .applymap(lambda v: "color: blue;")
        .hide_columns(styler_mi.data.columns[1:])
        .hide_index(styler_mi.data.index[1:])
        .to_html()
    )
    expected_styles = dedent(
        """\
        <style type="text/css">
        #T__row0_col0 {
          color: blue;
        }
        </style>
        """
    )
    assert expected_styles in result


def test_include_css_style_rules_only_for_visible_index_labels(styler_mi):
    # GH 43619
    result = (
        styler_mi.set_uuid("")
        .applymap_index(lambda v: "color: blue;", axis="index")
        .hide_columns(styler_mi.data.columns)
        .hide_index(styler_mi.data.index[1:])
        .to_html()
    )
    expected_styles = dedent(
        """\
        <style type="text/css">
        #T__level0_row0, #T__level1_row0 {
          color: blue;
        }
        </style>
        """
    )
    assert expected_styles in result


def test_include_css_style_rules_only_for_visible_column_labels(styler_mi):
    # GH 43619
    result = (
        styler_mi.set_uuid("")
        .applymap_index(lambda v: "color: blue;", axis="columns")
        .hide_columns(styler_mi.data.columns[1:])
        .hide_index(styler_mi.data.index)
        .to_html()
    )
    expected_styles = dedent(
        """\
        <style type="text/css">
        #T__level0_col0, #T__level1_col0 {
          color: blue;
        }
        </style>
        """
    )
    assert expected_styles in result


def test_hiding_index_columns_multiindex_alignment():
    # gh 43644
    midx = MultiIndex.from_product(
        [["i0", "j0"], ["i1"], ["i2", "j2"]], names=["i-0", "i-1", "i-2"]
    )
    cidx = MultiIndex.from_product(
        [["c0"], ["c1", "d1"], ["c2", "d2"]], names=["c-0", "c-1", "c-2"]
    )
    df = DataFrame(np.arange(16).reshape(4, 4), index=midx, columns=cidx)
    styler = Styler(df, uuid_len=0)
    styler.hide_index(level=1).hide_columns(level=0)
    styler.hide_index([("j0", "i1", "j2")])
    styler.hide_columns([("c0", "d1", "d2")])
    result = styler.to_html()
    expected = dedent(
        """\
    <style type="text/css">
    </style>
    <table id="T_">
      <thead>
        <tr>
          <th class="blank" >&nbsp;</th>
          <th class="index_name level1" >c-1</th>
          <th id="T__level1_col0" class="col_heading level1 col0" colspan="2">c1</th>
          <th id="T__level1_col2" class="col_heading level1 col2" >d1</th>
        </tr>
        <tr>
          <th class="blank" >&nbsp;</th>
          <th class="index_name level2" >c-2</th>
          <th id="T__level2_col0" class="col_heading level2 col0" >c2</th>
          <th id="T__level2_col1" class="col_heading level2 col1" >d2</th>
          <th id="T__level2_col2" class="col_heading level2 col2" >c2</th>
        </tr>
        <tr>
          <th class="index_name level0" >i-0</th>
          <th class="index_name level2" >i-2</th>
          <th class="blank col0" >&nbsp;</th>
          <th class="blank col1" >&nbsp;</th>
          <th class="blank col2" >&nbsp;</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th id="T__level0_row0" class="row_heading level0 row0" rowspan="2">i0</th>
          <th id="T__level2_row0" class="row_heading level2 row0" >i2</th>
          <td id="T__row0_col0" class="data row0 col0" >0</td>
          <td id="T__row0_col1" class="data row0 col1" >1</td>
          <td id="T__row0_col2" class="data row0 col2" >2</td>
        </tr>
        <tr>
          <th id="T__level2_row1" class="row_heading level2 row1" >j2</th>
          <td id="T__row1_col0" class="data row1 col0" >4</td>
          <td id="T__row1_col1" class="data row1 col1" >5</td>
          <td id="T__row1_col2" class="data row1 col2" >6</td>
        </tr>
        <tr>
          <th id="T__level0_row2" class="row_heading level0 row2" >j0</th>
          <th id="T__level2_row2" class="row_heading level2 row2" >i2</th>
          <td id="T__row2_col0" class="data row2 col0" >8</td>
          <td id="T__row2_col1" class="data row2 col1" >9</td>
          <td id="T__row2_col2" class="data row2 col2" >10</td>
        </tr>
      </tbody>
    </table>
    """
    )
    assert result == expected
