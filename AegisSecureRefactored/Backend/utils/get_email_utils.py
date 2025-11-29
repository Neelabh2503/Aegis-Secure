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

def extract_body(payload):
    if not payload:
        return ""

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
                text = ""

            if text:
                return text

        except Exception:
            pass

    for part in payload.get("parts", []):
        text = extract_body(part)
        if text:
            return text

    return ""
