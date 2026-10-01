"""Leitura das planilhas de combustível e manutenção.

As colunas são reconhecidas pelo nome (sem acento, sem maiúscula), então a
planilha pode vir com "Tombamento", "TOMB.", "Prefixo"... Sem planilha, o app
usa dados de exemplo para dar para ver o layout.
"""
from __future__ import annotations

import io
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

PASTA_DADOS = Path(__file__).parent / "dados"

# nome padrão -> nomes aceitos na planilha (já normalizados)
COLUNAS_COMB = {
    "data": ["data", "dt", "data abastecimento", "emissao", "data emissao"],
    "tombamento": ["tombamento", "tomb", "prefixo", "veiculo", "placa"],
    "tipo_veiculo": ["tipo de veiculo", "tipo veiculo", "tipo"],
    "equipe": ["servicos", "servico", "equipe", "centro de custo"],
    "concessionaria": ["concessionaria", "cliente", "contrato"],
    "regional": ["regional", "estado", "uf", "base"],
    "estabelecimento": ["estabelecimento", "posto"],
    "combustivel": ["combustivel", "produto", "tipo combustivel"],
    "litros": ["litros", "qtd litros", "quantidade", "qtd"],
    "km": ["km rodados", "km rodado", "km"],
    "valor": ["valor", "valor total", "total", "custo", "custo total"],
}
COLUNAS_MANUT = {
    "data": ["data", "dt", "data saida", "emissao", "data emissao"],
    "tombamento": ["tombamento", "tomb", "prefixo", "veiculo", "placa"],
    "tipo_veiculo": ["tipo de veiculo", "tipo veiculo", "tipo"],
    "equipe": ["servicos", "servico", "equipe", "centro de custo"],
    "concessionaria": ["concessionaria", "cliente", "contrato"],
    "regional": ["regional", "estado", "uf", "base"],
    "categoria": ["descricao", "categoria", "grupo", "classe"],
    "material": ["material", "item", "produto"],
    "fornecedor": ["fornecedor", "oficina"],
    "qtd": ["qtd", "qtd.", "quantidade"],
    "valor": ["valor", "valor total", "total", "custo", "custo total"],
}
OBRIGATORIAS = ["data", "valor"]


def _norm(txt: str) -> str:
    t = unicodedata.normalize("NFKD", str(txt)).encode("ascii", "ignore").decode()
    return " ".join(t.lower().replace("_", " ").replace(".", " ").split())


def _mapear(df: pd.DataFrame, mapa: dict[str, list[str]]) -> pd.DataFrame:
    """Renomeia as colunas da planilha para os nomes padrão."""
    cols = {_norm(c): c for c in df.columns}
    ren = {}
    for padrao, aceitos in mapa.items():
        for a in [padrao.replace("_", " ")] + aceitos:
            a = _norm(a)
            if a in cols and cols[a] not in ren:
                ren[cols[a]] = padrao
                break
    out = df.rename(columns=ren)[list(ren.values())].copy()
    faltam = [c for c in OBRIGATORIAS if c not in out.columns]
    if faltam:
        raise ValueError(
            "não achei as colunas " + ", ".join(faltam)
            + ". Colunas da planilha: " + ", ".join(map(str, df.columns))
        )
    return out


def _num(s: pd.Series) -> pd.Series:
    if s.dtype.kind in "if":
        return s.fillna(0)
    t = s.astype(str).str.replace(r"[^\d,.\-]", "", regex=True)
    # "1.234,56" -> 1234.56 ; "1234.56" fica como está
    br = t.str.contains(",")
    t = t.where(~br, t.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    return pd.to_numeric(t, errors="coerce").fillna(0)


def _datas(s: pd.Series) -> pd.Series:
    """Data do Excel já vem pronta; texto pode ser 2026-03-01 (ISO) ou 01/03/2026 (dia primeiro)."""
    if pd.api.types.is_datetime64_any_dtype(s):
        return s
    iso = pd.to_datetime(s, format="ISO8601", errors="coerce")
    br = pd.to_datetime(s.where(iso.isna()), dayfirst=True, format="mixed", errors="coerce")
    return iso.fillna(br)


def _limpar(df: pd.DataFrame, mapa: dict[str, list[str]]) -> pd.DataFrame:
    df = _mapear(df, mapa)
    df["data"] = _datas(df["data"])
    df = df.dropna(subset=["data"])
    for c in ("valor", "litros", "km", "qtd"):
        if c in df.columns:
            df[c] = _num(df[c])
    for c in mapa:
        if c in ("data", "valor", "litros", "km", "qtd"):
            if c not in df.columns:
                df[c] = 0.0
            continue
        if c not in df.columns:
            df[c] = "NÃO INFORMADO"
        else:
            # tombamento 128 vem como número (128.0): vira texto "128"
            t = df[c].astype("string").str.strip().str.replace(r"\.0$", "", regex=True).str.upper()
            df[c] = t.mask(t.isna() | (t == ""), "NÃO INFORMADO").astype(str)
    df["ano"] = df["data"].dt.year
    df["mes"] = df["data"].dt.month
    return df.reset_index(drop=True)


def ler_planilha(arquivo, mapa) -> pd.DataFrame:
    nome = getattr(arquivo, "name", str(arquivo)).lower()
    if nome.endswith(".csv"):
        bruto = arquivo.read() if hasattr(arquivo, "read") else Path(arquivo).read_bytes()
        df = pd.read_csv(io.BytesIO(bruto), sep=None, engine="python", encoding_errors="replace")
    else:
        df = pd.read_excel(arquivo)
    return _limpar(df, mapa)


def ler_da_pasta(prefixo: str, mapa) -> pd.DataFrame | None:
    """Junta todas as planilhas da pasta dados/ que começam com o prefixo."""
    arqs = sorted(p for p in PASTA_DADOS.glob(f"{prefixo}*") if p.suffix.lower() in (".xlsx", ".xls", ".csv"))
    if not arqs:
        return None
    return pd.concat([ler_planilha(a, mapa) for a in arqs], ignore_index=True)


# ---------------------------------------------------------------- exemplo
def dados_exemplo(hoje: pd.Timestamp | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Frota fictícia com o mesmo formato das planilhas reais (2024 até o mês passado)."""
    rng = np.random.default_rng(7)
    hoje = hoje or pd.Timestamp.today()
    fim = (hoje.replace(day=1) - pd.Timedelta(days=1))
    meses = pd.period_range("2024-01", fim.to_period("M"), freq="M")

    equipes = ["CONSTRUÇÃO", "COORDENAÇÃO", "MANUTENÇÃO", "PLANTÃO", "LINHA VIVA", "TRANSPORTE", "RESERVA", "PERDAS"]
    peso_eq = np.array([30, 8, 10, 12, 9, 8, 6, 3], float)
    tipos = {"CAMINHÃO": (2.6, 8.0), "PICKUP": (8.5, 6.4), "CARRO": (11.0, 6.2), "MOTO": (30.0, 6.3)}
    veics = []
    for i, tomb in enumerate([str(n) for n in rng.choice(range(120, 310), 70, replace=False)]
                             + [f"C.A{n:03d}" for n in range(1, 21)]):
        tipo = rng.choice(list(tipos), p=[.25, .4, .25, .1])
        veics.append(dict(tombamento=tomb, tipo_veiculo=tipo,
                          equipe=rng.choice(equipes, p=peso_eq / peso_eq.sum()),
                          concessionaria="ENERGISA" if rng.random() < .62 else "EQUATORIAL",
                          regional="ALAGOAS" if rng.random() < .12 else "PARAÍBA"))

    preco = {"DIESEL": 6.2, "GASOLINA": 6.3}
    comb, manut = [], []
    cats = {"PEÇAS": (.44, ["PASTILHA DE FREIO", "FILTRO DE ÓLEO", "VÁLVULA PEDAL FREIO", "AMORTECEDOR", "CORREIA"]),
            "PNEUS": (.20, ["PNEU NOVO 275/80 R22,5", "PNEU NOVO 215/75 R17,5", "PNEU REFORMADO", "PNEU NOVO 175/70 R14"]),
            "EMPLACAMENTO/IMPOSTO": (.15, ["IPVA", "LICENCIAMENTO"]),
            "SERVIÇOS": (.12, ["ALINHAMENTO", "BALANCEAMENTO", "SERVIÇO ELÉTRICO", "TORNEARIA"]),
            "SEGUROS": (.09, ["SEGURO"])}
    fornecedores = ["CENTER PEÇAS", "TORNEARIA SOUSA", "BATERIA SOL", "ATACADÃO DAS PEÇAS", "FABIO EQUIPAMENTOS", "OFICINA PRÓPRIA"]
    for per in meses:
        sazon = 1 + .08 * np.sin(per.month / 12 * 2 * np.pi) + .05 * (per.year - 2024)
        for v in veics:
            kml, base = tipos[v["tipo_veiculo"]]
            prod = "GASOLINA" if v["tipo_veiculo"] in ("CARRO", "MOTO") else "DIESEL"
            for _ in range(rng.integers(2, 6)):
                km = float(rng.normal(380, 120) * (1.6 if v["tipo_veiculo"] == "CAMINHÃO" else 1))
                km = max(km, 40)
                litros = km / kml * rng.uniform(.9, 1.1)
                p = preco[prod] * sazon * rng.uniform(.97, 1.03)
                dia = int(rng.integers(1, 28))
                comb.append(dict(v, data=pd.Timestamp(per.year, per.month, dia), combustivel=prod,
                                 estabelecimento=rng.choice(["POSTO CENTRAL", "POSTO BR 230", "POSTO AL 101"]),
                                 litros=round(litros, 2), km=round(km), valor=round(litros * p, 2)))
            if rng.random() < .55:
                for _ in range(rng.integers(1, 4)):
                    cat = rng.choice(list(cats), p=[c[0] for c in cats.values()])
                    mat = rng.choice(cats[cat][1])
                    qtd = float(rng.integers(1, 5))
                    unit = {"PNEUS": 1800, "EMPLACAMENTO/IMPOSTO": 1400, "SEGUROS": 700}.get(cat, 260)
                    manut.append(dict(v, data=pd.Timestamp(per.year, per.month, int(rng.integers(1, 28))),
                                      categoria=cat, material=mat, fornecedor=rng.choice(fornecedores),
                                      qtd=qtd, valor=round(qtd * unit * rng.uniform(.5, 1.5) * sazon, 2)))
    c = pd.DataFrame(comb)
    m = pd.DataFrame(manut)
    for df in (c, m):
        df["ano"] = df["data"].dt.year
        df["mes"] = df["data"].dt.month
    return c, m
