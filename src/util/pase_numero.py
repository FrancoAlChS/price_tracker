import re

def parse_numero(texto:str):
    if not texto:
        return None
    limpio = re.sub(r"[^\d.]", "", texto.replace(",", ""))
    match = re.search(r"(\d+\.?\d*)", limpio)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None