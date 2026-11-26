"""Utilitários de texto: normalização para busca e extração de entidades da pergunta."""
import re
import unicodedata
from datetime import datetime

from rag import config


def normalizar(txt: str) -> str:
    """Minúsculas e sem acentos — melhora a busca lexical em português."""
    txt = unicodedata.normalize("NFKD", txt.lower())
    return "".join(c for c in txt if not unicodedata.combining(c))


def extrair_ativo(pergunta: str):
    """Retorna (ativo, ambigua). Reconhece MTR-07, 'motor 7', FZ-ATV-01, 'ativo da Forzy'."""
    p = normalizar(pergunta)
    encontrados = set()
    for m in re.finditer(r"\bmtr[-\s]?0?(\d{1,2})\b", p):
        encontrados.add(f"MTR-{int(m.group(1)):02d}")
    for m in re.finditer(r"\bmotor(?:es)?\s*(?:n[ºo.]?\s*)?0?(\d{1,2})\b", p):
        encontrados.add(f"MTR-{int(m.group(1)):02d}")
    if re.search(r"fz[-\s]?atv|forzy|io-?link|porta ?[12]|ciclo \d", p):
        encontrados.add(config.ID_FORZY)
    encontrados = {a for a in encontrados if a == config.ID_FORZY or a in config.IDS_MOTORES}
    if len(encontrados) == 1:
        return encontrados.pop(), False
    if len(encontrados) > 1:
        return sorted(encontrados), False
    return None, False


def extrair_ciclo(pergunta: str):
    m = re.search(r"ciclo\s*(\d)", normalizar(pergunta))
    return int(m.group(1)) if m else None


def extrair_periodo(pergunta: str):
    """Datas dd/mm/aaaa ou aaaa-mm-dd (com hora opcional). Retorna (inicio, fim) ISO ou (None, None)."""
    datas = []
    for m in re.finditer(r"(\d{2})/(\d{2})/(\d{4})(?:\s*(?:as|às|a)?\s*(\d{1,2})[:h](\d{2}))?", pergunta):
        d, mo, a, h, mi = m.groups()
        datas.append(datetime(int(a), int(mo), int(d), int(h or 0), int(mi or 0)))
    for m in re.finditer(r"(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2}))?", pergunta):
        a, mo, d, h, mi = m.groups()
        datas.append(datetime(int(a), int(mo), int(d), int(h or 0), int(mi or 0)))
    if not datas:
        return None, None
    if len(datas) == 1:
        ini = datas[0]
        fim = ini.replace(hour=23, minute=59, second=59) if ini.hour == 0 and ini.minute == 0 else ini
        return ini.isoformat(), fim.isoformat()
    return min(datas).isoformat(), max(datas).isoformat()


def extrair_numeros(pergunta: str):
    """Números com unidade opcional (aceita vírgula decimal)."""
    p = pergunta.replace(",", ".")
    p = re.sub(r"\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}[:h]\d{2}", " ", p)
    p = re.sub(r"(?i)\bfz[-\s]?atv[-\s]?\d+|\biso\s*\d+(?:-\d+)?|\bnr[-\s]?\d+", " ", p)
    p = re.sub(r"(?i)\b(mtr|motor|ciclo|porta|p|doc|os|rolamento)[-\s]?\d+", " ", p)
    return [float(n) for n in re.findall(r"(?<![\w.])[-+]?\d+(?:\.\d+)?", p)]
