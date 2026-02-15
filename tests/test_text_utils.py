from pyreader.text_utils import html_to_text


def test_html_to_text_basic() -> None:
    html = "<h1>Title</h1><p>Hello <b>world</b>.</p><p>Second para.</p>"
    text = html_to_text(html)
    assert "Title" in text
    assert "Hello world." in text
    assert "Second para." in text
