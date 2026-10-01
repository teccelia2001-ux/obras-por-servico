"""Dashboard Frota TECCEL — visão geral de combustível e manutenção numa tela só.

Rodar:  streamlit run app.py
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import dados as D

st.set_page_config(page_title="Dashboard Frota TECCEL", page_icon="🚚", layout="wide")

# cores (validadas para daltonismo): combustível, manutenção, terceira série
ROXO, LARANJA, VERDE = "#7b2fd0", "#eb6834", "#1baf7a"
CINZA = "#8a8794"
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

st.markdown(
    """
<style>
.block-container{padding-top:3rem}
.topo{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;margin-bottom:.2rem}
.topo .marca{font-weight:900;font-size:1.7rem;color:#7b2fd0;letter-spacing:.5px}
.topo .tit{font-weight:800;font-size:1.25rem}
.topo .sub{color:#6b6878;font-size:.85rem;letter-spacing:2px;text-transform:uppercase}
.kpi{background:#fff;border:1px solid #e6e1f2;border-left:5px solid var(--c,#7b2fd0);border-radius:12px;padding:12px 16px;height:100%}
.kpi .l{font-size:.72rem;font-weight:800;letter-spacing:1.6px;text-transform:uppercase;color:#7b2fd0}
.kpi .v{font-size:1.75rem;font-weight:800;color:#1d1b24;line-height:1.25;margin-top:2px}
.kpi .d{font-size:.82rem;margin-top:2px}
.kpi .d.sobe{color:#c0392b}.kpi .d.desce{color:#1a7f4b}
.kpi .s{font-size:.8rem;color:#6b6878;margin-top:4px}
.kpi .p{font-size:.85rem;color:#c0392b;font-weight:700;margin-top:4px}
.mini{background:#f6f3fc;border-radius:10px;padding:8px 12px}
.mini .l{font-size:.7rem;color:#6b6878;text-transform:uppercase;letter-spacing:1px}
.mini .v{font-size:1.15rem;font-weight:700;color:#1d1b24}
h3{margin-top:.6rem!important}
</style>""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- formatação pt-BR
def num(v: float, casas: int = 2) -> str:
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def brl(v: float) -> str:
    return "R$ " + num(v)


def compacto(v: float) -> str:
    a = abs(v)
    if a >= 1e6:
        return num(v / 1e6, 2) + " mi"
    if a >= 1e3:
        return num(v / 1e3, 1) + " mil"
    return num(v, 0)


# ---------------------------------------------------------------- dados
@st.cache_data(show_spinner="Lendo planilhas…")
def carregar(arq_comb, arq_manut):
    avisos = []
    comb = manut = None
    try:
        comb = D.ler_planilha(arq_comb, D.COLUNAS_COMB) if arq_comb else D.ler_da_pasta("combustivel", D.COLUNAS_COMB)
    except Exception as e:  # planilha com formato inesperado: avisa e segue com o exemplo
        avisos.append(f"Combustível: {e}")
    try:
        manut = D.ler_planilha(arq_manut, D.COLUNAS_MANUT) if arq_manut else D.ler_da_pasta("manutencao", D.COLUNAS_MANUT)
    except Exception as e:
        avisos.append(f"Manutenção: {e}")
    exemplo = comb is None or manut is None
    if exemplo:
        c_ex, m_ex = D.dados_exemplo()
        comb = comb if comb is not None else c_ex
        manut = manut if manut is not None else m_ex
    return comb, manut, exemplo, avisos


with st.sidebar:
    st.markdown("### 📂 Dados")
    up_c = st.file_uploader("Planilha de combustível", type=["xlsx", "xls", "csv"], key="upc")
    up_m = st.file_uploader("Planilha de manutenção", type=["xlsx", "xls", "csv"], key="upm")

comb_all, manut_all, exemplo, avisos = carregar(up_c, up_m)

# ---------------------------------------------------------------- filtros
with st.sidebar:
    st.markdown("### 🔎 Filtros")
    anos = sorted(set(comb_all["ano"]) | set(manut_all["ano"]), reverse=True)
    ano = st.selectbox("Ano", anos)
    meses_sel = st.multiselect("Mês", list(range(1, 13)), format_func=lambda m: MESES[m - 1],
                               placeholder="Todos os meses")

    def opcoes(col):
        return sorted(set(comb_all[col]) | set(manut_all[col]))

    f_reg = st.multiselect("Regional", opcoes("regional"), placeholder="Todas")
    f_tipo = st.multiselect("Tipo de veículo", opcoes("tipo_veiculo"), placeholder="Todos")
    f_eq = st.multiselect("Serviço / equipe", opcoes("equipe"), placeholder="Todos")
    f_con = st.multiselect("Concessionária", opcoes("concessionaria"), placeholder="Todas")
    f_tomb = st.multiselect("Tombamento", opcoes("tombamento"), placeholder="Todos")


def filtrar(df: pd.DataFrame, anos_: list[int], meses_: list[int] | None) -> pd.DataFrame:
    m = df["ano"].isin(anos_)
    if meses_:
        m &= df["mes"].isin(meses_)
    for col, sel in (("regional", f_reg), ("tipo_veiculo", f_tipo), ("equipe", f_eq),
                     ("concessionaria", f_con), ("tombamento", f_tomb)):
        if sel:
            m &= df[col].isin(sel)
    return df[m]


c = filtrar(comb_all, [ano], meses_sel)
mt = filtrar(manut_all, [ano], meses_sel)
# meses com lançamento no ano escolhido: o ano anterior é comparado no MESMO período
meses_periodo = sorted(set(c["mes"]) | set(mt["mes"]))
c_ant = filtrar(comb_all, [ano - 1], meses_periodo)
mt_ant = filtrar(manut_all, [ano - 1], meses_periodo)

# ---------------------------------------------------------------- topo
st.markdown(
    f'<div class="topo"><span class="marca">TECCEL FROTA</span><span class="tit">Visão geral {ano}</span>'
    f'<span class="sub">combustível + manutenção</span></div>',
    unsafe_allow_html=True,
)
periodo = (f"{MESES[meses_periodo[0] - 1]} a {MESES[meses_periodo[-1] - 1]}/{ano}" if meses_periodo else "sem lançamentos")
st.caption(f"Período com lançamentos: **{periodo}** · comparação com o mesmo período de {ano - 1}")
if exemplo:
    st.info("Mostrando **dados de exemplo** (fictícios). Envie as planilhas na barra lateral "
            "ou coloque-as na pasta `dados/` (arquivos começando com `combustivel` e `manutencao`).", icon="ℹ️")
for a in avisos:
    st.warning(a)

if c.empty and mt.empty:
    st.warning("Nenhum lançamento com os filtros escolhidos.")
    st.stop()

# ---------------------------------------------------------------- KPIs
n_meses = max(len(meses_periodo), 1)
ultimo_ano = max(anos)
mostra_prev = not meses_sel and ano == ultimo_ano and n_meses < 12


def card(rotulo, atual, anterior, cor):
    media = atual / n_meses
    if anterior:
        var = (atual - anterior) / anterior * 100
        seta = "▲" if var >= 0 else "▼"
        delta = (f'<div class="d {"sobe" if var >= 0 else "desce"}">{seta} {num(abs(var), 1)}% '
                 f'vs {ano - 1} ({compacto(anterior)})</div>')
    else:
        delta = f'<div class="d" style="color:#6b6878">sem dados de {ano - 1}</div>'
    prev = (f'<div class="p">Previsão {ano}: {brl(atual + media * (12 - n_meses))}</div>' if mostra_prev else "")
    return (f'<div class="kpi" style="--c:{cor}"><div class="l">{rotulo}</div>'
            f'<div class="v">{brl(atual)}</div>{delta}'
            f'<div class="s">Média mensal: <b>{brl(media)}</b></div>{prev}</div>')


tc, tm = c["valor"].sum(), mt["valor"].sum()
ta_c, ta_m = c_ant["valor"].sum(), mt_ant["valor"].sum()
k1, k2, k3 = st.columns(3)
k1.markdown(card("Custo total frota", tc + tm, ta_c + ta_m, "#1d1b24"), unsafe_allow_html=True)
k2.markdown(card("Combustível", tc, ta_c, ROXO), unsafe_allow_html=True)
k3.markdown(card("Manutenção", tm, ta_m, LARANJA), unsafe_allow_html=True)
if mostra_prev:
    st.caption("Previsão = realizado + média mensal × meses que faltam no ano.")

litros, km = c["litros"].sum(), c["km"].sum()
veic = len(set(c["tombamento"]) | set(mt["tombamento"]))
minis = [
    ("Veículos com lançamento", num(veic, 0)),
    ("Litros", num(litros, 0)),
    ("KM rodados", num(km, 0)),
    ("Consumo médio", f"{num(km / litros, 2)} km/l" if litros else "—"),
    ("Preço médio do litro", brl(tc / litros) if litros else "—"),
    ("Combustível / km", brl(tc / km) if km else "—"),
    ("Manutenção / km", brl(tm / km) if km else "—"),
    ("Custo total / km", brl((tc + tm) / km) if km else "—"),
]
st.write("")
for col, (l, v) in zip(st.columns(len(minis)), minis):
    col.markdown(f'<div class="mini"><div class="l">{l}</div><div class="v">{v}</div></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- gráficos
def layout(fig: go.Figure, altura=340, legenda=True):
    fig.update_layout(
        height=altura, margin=dict(l=8, r=8, t=8, b=8), separators=",.",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="system-ui, Segoe UI, sans-serif", size=12, color="#33303d"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None) if legenda else None,
        showlegend=legenda, hoverlabel=dict(bgcolor="white", font_size=12),
        bargap=.25, legend_traceorder="normal",
    )
    fig.update_xaxes(showgrid=False, linecolor="#d9d4e6", ticks="")
    fig.update_yaxes(gridcolor="#eeebf5", zeroline=False, tickformat="~s")
    return fig


def por_mes(df, col="valor"):
    return df.groupby("mes")[col].sum().reindex(range(1, 13), fill_value=0)


meses_x = [MESES[m - 1] for m in range(1, 13)]
ate = meses_periodo[-1] if meses_periodo else 12

st.write("")
g1, g2 = st.columns([3, 2])
with g1:
    st.markdown("### Custo mensal")
    sc, sm = por_mes(c)[:ate], por_mes(mt)[:ate]
    tot_ant = (por_mes(c_ant) + por_mes(mt_ant))[:ate]
    fig = go.Figure()
    fig.add_bar(x=meses_x[:ate], y=sc, name="Combustível", marker=dict(color=ROXO, line=dict(color="white", width=2)),
                hovertemplate="Combustível: R$ %{y:,.2f}<extra></extra>")
    fig.add_bar(x=meses_x[:ate], y=sm, name="Manutenção", marker=dict(color=LARANJA, line=dict(color="white", width=2)),
                hovertemplate="Manutenção: R$ %{y:,.2f}<extra></extra>")
    if tot_ant.sum():
        fig.add_scatter(x=meses_x[:ate], y=tot_ant, name=f"Total {ano - 1}", mode="lines+markers",
                        line=dict(color=CINZA, width=2, dash="dot"), marker=dict(size=8),
                        hovertemplate=f"Total {ano - 1}: R$ %{{y:,.2f}}<extra></extra>")
    tot = sc + sm
    fig.add_scatter(x=meses_x[:ate], y=tot, mode="text", text=[compacto(v) for v in tot], textposition="top center",
                    showlegend=False, hoverinfo="skip", textfont=dict(size=11, color="#33303d"))
    fig.update_layout(barmode="stack", hovermode="x unified")
    st.plotly_chart(layout(fig), width="stretch")
with g2:
    st.markdown("### Custo por km rodado")
    kmm = por_mes(c, "km")[:ate].replace(0, pd.NA)
    fig = go.Figure()
    for nome, serie, cor in (("Combustível/km", por_mes(c)[:ate] / kmm, ROXO),
                             ("Manutenção/km", por_mes(mt)[:ate] / kmm, LARANJA),
                             ("Total/km", (por_mes(c) + por_mes(mt))[:ate] / kmm, "#1d1b24")):
        fig.add_scatter(x=meses_x[:ate], y=serie, name=nome, mode="lines+markers", line=dict(color=cor, width=2),
                        marker=dict(size=8), hovertemplate=nome + ": R$ %{y:,.2f}<extra></extra>")
    fig.update_layout(hovermode="x unified")
    fig.update_yaxes(tickformat=",.2f", tickprefix="R$ ")
    st.plotly_chart(layout(fig), width="stretch")

# comparativo ano a ano (até 3 anos)
st.markdown(f"### Comparativo {ano - 2} · {ano - 1} · {ano}")
cores_ano = {ano: ROXO, ano - 1: LARANJA, ano - 2: VERDE}
g1, g2 = st.columns(2)
for col, titulo, base in ((g1, "Combustível", comb_all), (g2, "Manutenção", manut_all)):
    with col:
        st.markdown(f"**{titulo} por mês**")
        fig = go.Figure()
        for a in (ano - 2, ano - 1, ano):
            df = filtrar(base, [a], meses_sel)
            if df.empty:
                continue
            s = por_mes(df)
            n = ate if a == ano else 12
            fig.add_scatter(x=meses_x[:n], y=s[:n], name=str(a), mode="lines+markers",
                            line=dict(color=cores_ano[a], width=3 if a == ano else 2),
                            marker=dict(size=8), hovertemplate=f"{a}: R$ %{{y:,.2f}}<extra></extra>")
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(layout(fig, 300), width="stretch")


def barras_empilhadas(chave: str, top: int, altura: int):
    a = c.groupby(chave)["valor"].sum().rename("Combustível")
    b = mt.groupby(chave)["valor"].sum().rename("Manutenção")
    t = pd.concat([a, b], axis=1).fillna(0)
    t["Total"] = t.sum(axis=1)
    t = t.sort_values("Total", ascending=False).head(top).iloc[::-1]
    fig = go.Figure()
    for nome, cor in (("Combustível", ROXO), ("Manutenção", LARANJA)):
        fig.add_bar(y=t.index.astype(str), x=t[nome], name=nome, orientation="h",
                    marker=dict(color=cor, line=dict(color="white", width=2)),
                    hovertemplate="%{y} · " + nome + ": R$ %{x:,.2f}<extra></extra>")
    fig.add_scatter(y=t.index.astype(str), x=t["Total"], mode="text", text=[" " + compacto(v) for v in t["Total"]],
                    textposition="middle right", showlegend=False, hoverinfo="skip",
                    textfont=dict(size=11, color="#33303d"))
    fig.update_layout(barmode="stack")
    fig.update_xaxes(range=[0, t["Total"].max() * 1.18] if len(t) else None)
    fig.update_yaxes(type="category", gridcolor="rgba(0,0,0,0)")
    return layout(fig, altura)


g1, g2 = st.columns(2)
with g1:
    st.markdown("### Maiores custos por tombamento")
    st.plotly_chart(barras_empilhadas("tombamento", 15, 460), width="stretch")
with g2:
    st.markdown("### Custo por serviço / equipe")
    st.plotly_chart(barras_empilhadas("equipe", 15, 460), width="stretch")

g1, g2, g3 = st.columns(3)
with g1:
    st.markdown("### Manutenção por categoria")
    t = mt.groupby("categoria")["valor"].sum().sort_values()
    pct = t / t.sum() * 100 if t.sum() else t
    fig = go.Figure(go.Bar(y=t.index, x=t, orientation="h", marker=dict(color=LARANJA),
                           text=[f" {compacto(v)} ({num(p, 1)}%)" for v, p in zip(t, pct)], textposition="outside",
                           cliponaxis=False, hovertemplate="%{y}: R$ %{x:,.2f}<extra></extra>"))
    fig.update_xaxes(range=[0, t.max() * 2.2] if len(t) else None)
    st.plotly_chart(layout(fig, 320, legenda=False).update_layout(margin=dict(r=40)), width="stretch")
with g2:
    st.markdown("### Preço médio do litro")
    fig = go.Figure()
    for prod, cor in zip(sorted(c["combustivel"].unique()), (ROXO, VERDE, LARANJA)):
        d = c[c["combustivel"] == prod]
        s = (por_mes(d) / por_mes(d, "litros").replace(0, pd.NA))[:ate]
        fig.add_scatter(x=meses_x[:ate], y=s, name=prod.title(), mode="lines+markers", line=dict(color=cor, width=2),
                        marker=dict(size=8), hovertemplate=prod.title() + ": R$ %{y:,.2f}/l<extra></extra>")
    fig.update_layout(hovermode="x unified")
    fig.update_yaxes(tickformat=",.2f", tickprefix="R$ ")
    st.plotly_chart(layout(fig, 320), width="stretch")
with g3:
    st.markdown("### Custo por concessionária")
    t = pd.concat([c.groupby("concessionaria")["valor"].sum().rename("Combustível"),
                   mt.groupby("concessionaria")["valor"].sum().rename("Manutenção")], axis=1).fillna(0)
    fig = go.Figure()
    for nome, cor in (("Combustível", ROXO), ("Manutenção", LARANJA)):
        fig.add_bar(x=t.index, y=t[nome], name=nome, marker=dict(color=cor, line=dict(color="white", width=2)),
                    hovertemplate="%{x} · " + nome + ": R$ %{y:,.2f}<extra></extra>")
    fig.add_scatter(x=t.index, y=t.sum(axis=1), mode="text", text=[compacto(v) for v in t.sum(axis=1)],
                    textposition="top center", showlegend=False, hoverinfo="skip")
    fig.update_layout(barmode="stack")
    st.plotly_chart(layout(fig, 320), width="stretch")

# ---------------------------------------------------------------- tabela por veículo
st.markdown("### Resumo por veículo")
info = (pd.concat([c, mt])[["tombamento", "tipo_veiculo", "equipe"]]
        .drop_duplicates("tombamento", keep="last").set_index("tombamento"))
r = pd.concat([
    c.groupby("tombamento").agg(combustivel=("valor", "sum"), litros=("litros", "sum"), km=("km", "sum")),
    mt.groupby("tombamento").agg(manutencao=("valor", "sum")),
], axis=1).fillna(0)
r["total"] = r["combustivel"] + r["manutencao"]
r["km_l"] = (r["km"] / r["litros"]).where(r["litros"] > 0)
r["custo_km"] = (r["total"] / r["km"]).where(r["km"] > 0)
r = info.join(r, how="right").sort_values("total", ascending=False).reset_index()
r = r.round({"combustivel": 2, "manutencao": 2, "total": 2, "litros": 0, "km": 0, "km_l": 2, "custo_km": 2})
r.columns = ["Tombamento", "Tipo", "Serviço/equipe", "Combustível (R$)", "Litros", "KM", "Manutenção (R$)",
             "Total (R$)", "km/l", "R$/km"]
st.dataframe(
    r, hide_index=True, width="stretch", height=380,
    column_config={
        "Combustível (R$)": st.column_config.NumberColumn(format="localized"),
        "Manutenção (R$)": st.column_config.NumberColumn(format="localized"),
        "Total (R$)": st.column_config.ProgressColumn(format="localized", min_value=0,
                                                       max_value=float(r["Total (R$)"].max() or 1)),
        "Litros": st.column_config.NumberColumn(format="localized"),
        "KM": st.column_config.NumberColumn(format="localized"),
        "km/l": st.column_config.NumberColumn(format="localized"),
        "R$/km": st.column_config.NumberColumn(format="localized"),
    },
)
st.download_button("⬇️ Baixar resumo (CSV)", r.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                   file_name=f"resumo-frota-{ano}.csv", mime="text/csv")
