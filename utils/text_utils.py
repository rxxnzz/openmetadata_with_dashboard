
import re
import html as html_lib


def clean_html(text: str | None) -> str:
    if not text:
        return text
    text = re.sub(r"<[^>]+>", "", text)
    text = html_lib.unescape(text)
    return text.strip()
