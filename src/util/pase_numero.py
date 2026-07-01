import re


def parse_numero(texto: str) -> float | None:
    if not texto:
        return None
    limpio: str = re.sub(r"[^\d.]", "", texto.replace(",", ""))
    match: re.Match[str] | None = re.search(r"(\d+\.?\d*)", limpio)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None
