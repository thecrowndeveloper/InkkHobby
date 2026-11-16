import re


def split_paragraphs(text):
    """Split plain chapter text into paragraphs on blank lines."""
    return [p.strip() for p in re.split(r"\n\s*\n", (text or "").strip()) if p.strip()]


def preview(text, words=80):
    """Whole paragraphs up to roughly `words` words; the last one is trimmed with an ellipsis."""
    out, used = [], 0
    for para in split_paragraphs(text):
        count = len(para.split())
        if used + count <= words:
            out.append(para)
            used += count
            continue
        remaining = words - used
        if remaining > 8 or not out:
            out.append(" ".join(para.split()[: max(remaining, 20)]).rstrip(",.;:") + "…")
        break
    return out
