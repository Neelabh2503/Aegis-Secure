import base64, html, re

def html_to_text(html_content):
    if not html_content:
        return ""

    text = html.unescape(html_content)
    text = re.sub(r"</p>|<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<(script|style).*?>.*?</\1>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


# def shorten_urls(text, max_length=100):
#     def _shorten(match):
#         url = match.group(0)
#         if len(url) <= max_length:
#             return url
#         return url[:max_length] + "..."
    
#     url_regex = r"(https?://[^\s]+)"
#     return re.sub(url_regex, _shorten, text)


# def format_links(text):
#     if not text:
#         return text
#     text = shorten_urls(text)
#     return text


def extract_body(payload):
    if not payload:
        return None

    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")

    if body_data:
        try:
            decoded = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")

            if "text/plain" in mime_type:
                text = decoded.strip()

            elif "text/html" in mime_type:
                text = html_to_text(decoded)

            else:
                text = None

            # if text:
            #     return format_links(text)

        except Exception:
            pass

    for part in payload.get("parts", []):
        text = extract_body(part)
        if text:
            return text

    return None
