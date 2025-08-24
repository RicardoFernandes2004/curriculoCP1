# pages/4_Analise_de_Dados.py
# Analise GitHub (BigQuery) – PROD: SA via secrets, cache, status, location=US

import math
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
from datetime import datetime
from google.cloud import bigquery
from google.cloud.bigquery import QueryJobConfig
from google.oauth2 import service_account

# ===============================
# CONFIG GLOBAL
# ===============================
PAGE_TITLE = "🔎 Análise de Dados (GitHub - BigQuery)"
BQ_LOCATION = "US"  # datasets públicos costumam ficar em US
DEFAULT_TOP_N = 20
DEFAULT_SAMPLE_PCT = 10

st.set_page_config(page_title="Análise de Dados", layout="wide")
st.title(PAGE_TITLE)
st.caption("Foco de engenharia: modelagem por repositório, custo/escala, métricas, inferência e explicabilidade.")

# ===============================
# HELPERS GERAIS
# ===============================
def fmt_num(x, fmt="{:.3f}", fallback="—"):
    try:
        if x is None:
            return fallback
        if isinstance(x, (float, int, np.floating)) and (math.isnan(x) or math.isinf(x)):
            return fallback
        return fmt.format(x)
    except Exception:
        return fallback

def fmt_pct(x, fallback="—"):
    try:
        if x is None or math.isnan(x):
            return fallback
        return f"{x:.1f}%"
    except Exception:
        return fallback

def human_bytes(n: int) -> str:
    if n is None or n < 0:
        return "?"
    units = ["B", "KB", "MB", "GB", "TB"]
    i, x = 0, float(n)
    while x >= 1024 and i < len(units) - 1:
        x /= 1024
        i += 1
    return f"{x:,.2f} {units[i]}"

# ===============================
# AUTENTICAÇÃO / CLIENTE BQ
# ===============================
@st.cache_resource(show_spinner=False)
def get_bq_client():
    if "gcp_service_account" in st.secrets:  # deploy
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return bigquery.Client(credentials=creds, project=creds.project_id)
    return bigquery.Client()  # local (ADC via gcloud)

@st.cache_data(show_spinner=False)
def bq_estimate_bytes(sql: str) -> int:
    client = get_bq_client()
    qcfg = QueryJobConfig(dry_run=True, use_query_cache=False)
    job = client.query(sql, location=BQ_LOCATION, job_config=qcfg)
    return int(job.total_bytes_processed)

@st.cache_data(show_spinner=False)
def bq_query(sql: str) -> tuple[pd.DataFrame, int]:
    """Retorna (DataFrame, bytes processados)."""
    client = get_bq_client()
    job = client.query(sql, location=BQ_LOCATION)
    df = job.result().to_dataframe()
    bytes_processed = getattr(job, "total_bytes_processed", None)
    return df, (int(bytes_processed) if bytes_processed is not None else -1)

def sanity_check():
    try:
        client = get_bq_client()
        df = client.query("SELECT 1 AS ok", location=BQ_LOCATION).result().to_dataframe()
        st.success(f"Conexão BigQuery OK (projeto: **{client.project}**). Retorno: {df.iloc[0]['ok']}")
        return True
    except Exception as e:
        st.error("Falha ao conectar no BigQuery. Verifique Service Account, roles e billing.")
        st.exception(e)
        return False

# ===============================
# SIDEBAR (CONTROLES)
# ===============================
with st.sidebar:
    st.header("Configurações")
    sample_pct = st.select_slider("Amostragem por repositório",
                                  options=[1, 2, 5, 10, 20, 50, 100],
                                  value=DEFAULT_SAMPLE_PCT,
                                  help="Amostra estável por hash do repo_name: reduz custo mantendo representatividade.")
    top_n = st.slider("Top-N linguagens por bytes (global)", 5, 30, DEFAULT_TOP_N, 1)
    scale = st.radio("Escala para tamanhos de repositório", ["log10", "linear"], index=0)
    calc_correlation = st.checkbox("Calcular correlação (r, p, IC)", value=True)
    calc_test = st.checkbox("Teste de hipótese (Welch: multilíngues > monolíngues)", value=True)

    st.divider()
    if st.button("🔄 Atualizar dados (limpar cache)"):
        st.cache_data.clear()
        st.success("Cache limpo. Rode novamente as consultas.")

# ===============================
# INTRO (contexto + ideia do trabalho)
# ===============================
def render_intro():
    st.header("Contexto e ideia do trabalho")
    st.write(
        """
        Projeto no estilo entrevista técnica de **engenharia de dados / back-end**:
        a partir de dados públicos em larga escala, transformamos eventos de código em **evidências quantitativas**
        e **insights acionáveis**, com **custo controlado** e **inferência estatística**. O foco é **raciocínio de produção**:
        modelagem por repositório, transparência das queries, amostragem estável e leitura executiva dos resultados.
        """
    )
    st.subheader("Base de dados (o que é e como será usada)")
    st.write(
        """
        Conjunto público **GitHub on BigQuery** (`bigquery-public-data.github_repos.languages`).
        Após `UNNEST(language)`, cada registro representa **(repositório, linguagem, bytes)**.
        A visão por repositório inclui: (i) **linguagem dominante**, (ii) **tamanho total** (bytes) e (iii) **número de linguagens**.
        """
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info(f"**Amostragem estável**\n\n~**{sample_pct}%** via `FARM_FINGERPRINT(repo_name)` para reduzir custo.")
    with c2:
        st.info(f"**Top linguagens**\n\nExibo **Top-{top_n}** por bytes para evidenciar concentração.")
    with c3:
        st.info("**Tratamento estatístico**\n\nUso `log10(total_bytes+1)` para lidar com **cauda pesada**.")
    st.subheader("Perguntas norteadoras")
    st.markdown(
        f"""
        - Quais linguagens acumulam maior **volume de código** (Top-{top_n})?  
        - Repositórios **multilíngues** (≥2 linguagens) tendem a ser **maiores** do que **monolíngues**?  
        - Qual a **relação** entre **número de linguagens** e **tamanho** do repositório?
        """
    )
    st.divider()

render_intro()

# ===============================
# TIPOS DE VARIÁVEIS
# ===============================
st.subheader("Tipos de variáveis (nomenclatura formal)")
tipos_df = pd.DataFrame([
    ["repo_name", "Qualitativa (Nominal)", "Nominal", "Identificador do repositório (rótulo, sem ordenação)."],
    ["language_name", "Qualitativa (Nominal)", "Nominal", "Nome da linguagem (categoria sem ordem)."],
    ["bytes", "Quantitativa (Contínua/contagem)", "Razão", "Bytes por linguagem no repo; zero é significativo; proporções fazem sentido."],
    ["total_bytes", "Quantitativa (Contínua)", "Razão", "Soma de bytes do repo; zero possível; dobrar/triplicar tem interpretação."],
    ["num_languages", "Quantitativa (Discreta)", "Razão", "Contagem de linguagens distintas no repo."],
    ["dominant_language", "Qualitativa (Nominal)", "Nominal", "Linguagem com mais bytes no repo."],
    ["log10_total_bytes", "Quantitativa (Contínua)", "Intervalar*", "Transformação para cauda pesada (*diferenças em log viram razões na escala original*)."],
], columns=["Variável", "Tipo estatístico", "Escala de medida", "Observações"])
st.dataframe(tipos_df, use_container_width=True)
st.caption("Obs.: **Razão** tem zero absoluto e permite interpretações multiplicativas; **log10** estabiliza variância.")

# ===============================
# SANITY CHECK (BigQuery)
# ===============================
st.subheader("Conexão BigQuery")
if not sanity_check():
    st.stop()

# ===============================
# QUERIES
# ===============================
sql_top_langs = f"""
SELECT
  lang.name AS language_name,
  SUM(lang.bytes) AS total_bytes
FROM `bigquery-public-data.github_repos.languages`,
UNNEST(language) AS lang
GROUP BY language_name
ORDER BY total_bytes DESC
LIMIT {top_n}
"""

sql_per_repo = f"""
WITH lang_bytes AS (
  SELECT
    repo_name,
    lang.name AS language_name,
    lang.bytes AS bytes
  FROM `bigquery-public-data.github_repos.languages`,
  UNNEST(language) AS lang
),
per_repo AS (
  SELECT
    repo_name,
    language_name,
    bytes,
    SUM(bytes) OVER (PARTITION BY repo_name) AS total_bytes,
    COUNT(*) OVER (PARTITION BY repo_name) AS num_languages,
    ROW_NUMBER() OVER (PARTITION BY repo_name ORDER BY bytes DESC) AS rn
  FROM lang_bytes
  WHERE MOD(ABS(FARM_FINGERPRINT(repo_name)), 100) < {sample_pct}
)
SELECT
  repo_name,
  language_name AS dominant_language,
  bytes AS dominant_bytes,
  total_bytes,
  num_languages
FROM per_repo
WHERE rn = 1
"""

# ===============================
# ESTIMATIVA DE CUSTO + EXECUÇÃO
# ===============================
st.subheader("Execução das consultas")
col_est1, col_est2 = st.columns(2)
with col_est1:
    try:
        est_top = bq_estimate_bytes(sql_top_langs)
        st.info(f"Estimativa Top Linguagens: {human_bytes(est_top)}")
    except Exception:
        st.info("Estimativa Top Linguagens indisponível (ok).")
with col_est2:
    try:
        est_repo = bq_estimate_bytes(sql_per_repo)
        st.info(f"Estimativa Visão por Repo (amostra {sample_pct}%): {human_bytes(est_repo)}")
    except Exception:
        st.info("Estimativa por Repo indisponível (ok).")

with st.status("Consultando BigQuery…", expanded=False) as s:
    df_top, bytes_top = bq_query(sql_top_langs)
    df_repo, bytes_repo = bq_query(sql_per_repo)
    s.update(label="Consultas concluídas ✅", state="complete")

colb1, colb2 = st.columns(2)
with colb1:
    st.success(f"Top Linguagens — bytes processados: {human_bytes(bytes_top)}")
with colb2:
    st.success(f"Visão por Repo — bytes processados: {human_bytes(bytes_repo)} (amostra {sample_pct}%)")

# ===============================
# EXPLORAÇÃO
# ===============================
st.header("Exploração: medidas, distribuições e correlação")

# 2.1 Top linguagens
st.subheader("Top linguagens por bytes (global)")
st.dataframe(df_top, use_container_width=True)
bar = (
    alt.Chart(df_top)
    .mark_bar()
    .encode(
        x=alt.X("total_bytes:Q", title="Total de bytes"),
        y=alt.Y("language_name:N", sort="-x", title="Linguagem"),
        tooltip=["language_name", alt.Tooltip("total_bytes:Q", format=",.0f")],
    )
    .properties(height=26 * len(df_top), width=700)
)
st.altair_chart(bar, use_container_width=True)

# métricas para relatório
if len(df_top) >= 1:
    top_total = df_top["total_bytes"].sum()
    top1_name = df_top.iloc[0]["language_name"]
    top1_share = (df_top.iloc[0]["total_bytes"] / top_total) * 100 if top_total else np.nan
    top3_share = (df_top.iloc[:3]["total_bytes"].sum() / top_total) * 100 if len(df_top) >= 3 and top_total else np.nan
else:
    top_total = np.nan
    top1_name = None
    top1_share = np.nan
    top3_share = np.nan

st.markdown(
    f"**Comentário:** No **Top-{top_n}**, **{top1_name or '—'}** concentra **{fmt_pct(top1_share)}**; as **3 primeiras** somam **{fmt_pct(top3_share)}** — indício de **concentração**."
)

# 2.2 Medidas por linguagem dominante
df_repo = df_repo.copy()
df_repo["log10_total_bytes"] = np.log10(df_repo["total_bytes"] + 1)
metric_scale = "log10_total_bytes" if scale == "log10" else "total_bytes"

st.subheader("Medidas descritivas (por linguagem dominante)")
st.caption(f"Métricas calculadas sobre: **{metric_scale}**")
desc = (
    df_repo.groupby("dominant_language")[metric_scale]
    .agg(["count", "mean", "median", "std"])
    .reset_index()
    .sort_values("count", ascending=False)
    .head(20)
)
st.dataframe(desc, use_container_width=True)
st.markdown(
    "**Comentário:** usamos **média/mediana** e **desvio-padrão**. Em **log10**, outliers pesam menos e comparações por grupo ficam mais robustas."
)

# 2.3 Distribuições
st.subheader("Distribuição de tamanhos de repositório")
left, right = st.columns(2)
with left:
    st.write("Histograma (geral)")
    hist = (
        alt.Chart(df_repo)
        .mark_bar()
        .encode(
            x=alt.X(f"{metric_scale}:Q", bin=alt.Bin(maxbins=50), title=metric_scale),
            y=alt.Y("count()", title="Contagem"),
            tooltip=[alt.Tooltip(metric_scale, format=".3f"), alt.Tooltip("count()", format=",")]
        )
        .properties(height=300)
    )
    st.altair_chart(hist, use_container_width=True)

with right:
    st.write("Boxplot por linguagem dominante (Top-10 por contagem)")
    top_langs = df_repo["dominant_language"].value_counts().head(10).index.tolist()
    box = (
        alt.Chart(df_repo[df_repo["dominant_language"].isin(top_langs)])
        .mark_boxplot()
        .encode(
            y=alt.Y("dominant_language:N", title="Linguagem"),
            x=alt.X(f"{metric_scale}:Q", title=metric_scale),
            tooltip=["dominant_language", alt.Tooltip(metric_scale, format=".3f")]
        )
        .properties(height=26 * len(top_langs))
    )
    st.altair_chart(box, use_container_width=True)

st.markdown(
    "**Comentário:** histograma com **assimetria à direita** (muitos repos pequenos, poucos gigantes). No boxplot, observe **dispersão intra-grupo** e **outliers**."
)

# 2.4 Correlação
st.subheader("Correlação entre número de linguagens e tamanho")
corr_success = False
r = p = r_low = r_high = np.nan
mag = "—"
if calc_correlation:
    from scipy import stats
    corr_df = df_repo[["num_languages", "log10_total_bytes"]].dropna()
    n = len(corr_df)
    if n >= 4:
        r, p = stats.pearsonr(corr_df["num_languages"], corr_df["log10_total_bytes"])
        z = np.arctanh(r); se = 1 / math.sqrt(n - 3)
        zcrit = stats.norm.ppf(0.975)
        r_low, r_high = np.tanh([z - zcrit*se, z + zcrit*se])
        abs_r = abs(r)
        if abs_r < 0.1: mag = "muito fraca"
        elif abs_r < 0.3: mag = "fraca"
        elif abs_r < 0.5: mag = "moderada"
        else: mag = "forte"
        corr_success = True

        c1, c2, c3 = st.columns(3)
        c1.metric("Correlação (r)", fmt_num(r))
        c2.metric("p-valor", fmt_num(p, "{:.3g}"))
        c3.metric("IC 95% de r", f"[{fmt_num(r_low)}, {fmt_num(r_high)}]")

        s = corr_df.sample(min(10000, n), random_state=42)
        scatter = (
            alt.Chart(s)
            .mark_point(opacity=0.25)
            .encode(
                x=alt.X("num_languages:Q", title="Número de linguagens"),
                y=alt.Y("log10_total_bytes:Q", title="log10(total_bytes+1)"),
                tooltip=[alt.Tooltip("num_languages:Q"), alt.Tooltip("log10_total_bytes:Q", format=".3f")]
            )
            .properties(height=350)
        )
        st.altair_chart(scatter, use_container_width=True)
    else:
        st.info("Amostra insuficiente para correlação (n < 4).")
else:
    st.info("Marque a opção na barra lateral para calcular correlação.")

if corr_success:
    st.markdown(
        f"**Comentário:** r = **{fmt_num(r)}** ({mag}), IC95% **[{fmt_num(r_low)}; {fmt_num(r_high)}]**, p **{fmt_num(p, '{:.3g}')}**. "
        "Em média, repos com **mais linguagens** tendem a ser **maiores** (em log10). *Correlação ≠ causalidade*."
    )

# ===============================
# INFERÊNCIA (Welch)
# ===============================
st.header("Inferência: IC 95% e Teste de hipótese (Welch)")
def welch_t_ci(a: np.ndarray, b: np.ndarray, alpha=0.05):
    from scipy import stats
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    ma, mb = a.mean(), b.mean()
    va, vb = a.var(ddof=1), b.var(ddof=1)
    na, nb = len(a), len(b)
    diff = ma - mb
    se = math.sqrt(max(va/na + vb/nb, 0))
    if na <= 1 or nb <= 1 or se == 0:
        return diff, np.nan, np.nan, np.nan, np.nan, np.nan
    df = (va/na + vb/nb)**2 / ((va**2)/((na**2)*(na-1)) + (vb**2)/((nb**2)*(nb-1)))
    t = diff / se
    p_two = 2 * (1 - stats.t.cdf(abs(t), df))
    tcrit = stats.t.ppf(1 - alpha/2, df)
    ci_low, ci_high = diff - tcrit * se, diff + tcrit * se
    return diff, t, p_two, df, ci_low, ci_high

st.subheader("Hipótese: multilíngues são maiores que monolíngues")
st.caption("Métrica: **log10(total_bytes+1)** | Teste: **Welch (variâncias possivelmente diferentes)**")

test_success = False
diff = tval = p_two = dfw = lci = uci = np.nan
p_one = fator = fator_l = fator_u = np.nan

if calc_test:
    mono = df_repo.loc[df_repo["num_languages"] == 1, "log10_total_bytes"].dropna().to_numpy()
    multi = df_repo.loc[df_repo["num_languages"] >= 2, "log10_total_bytes"].dropna().to_numpy()
    if len(mono) > 5 and len(multi) > 5:
        diff, tval, p_two, dfw, lci, uci = welch_t_ci(multi, mono, alpha=0.05)
        p_one = (p_two / 2) if diff > 0 else 1 - (p_two / 2)
        fator   = 10 ** diff if not math.isnan(diff) else np.nan
        fator_l = 10 ** lci  if not math.isnan(lci)  else np.nan
        fator_u = 10 ** uci  if not math.isnan(uci)  else np.nan
        test_success = True

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Δ média (log10)", fmt_num(diff))
        c2.metric("t (Welch)", fmt_num(tval, "{:.2f}"))
        c3.metric("p (one-sided)", fmt_num(p_one, "{:.3g}"))
        c4.metric("IC 95% (Δ)", f"[{fmt_num(lci)}, {fmt_num(uci)}]")

        df_mm = pd.DataFrame({
            "grupo": (["Monolíngue"] * len(mono)) + (["Multilíngue"] * len(multi)),
            "valor": np.concatenate([mono, multi])
        })
        vplot = (
            alt.Chart(df_mm)
            .transform_density("valor", as_=["valor", "density"], groupby=["grupo"])
            .mark_area(opacity=0.4)
            .encode(
                x=alt.X("valor:Q", title="log10(total_bytes+1)"),
                y=alt.Y("density:Q", title="Densidade"),
                color="grupo:N"
            )
            .properties(height=300)
        )
        st.altair_chart(vplot, use_container_width=True)
    else:
        st.warning("Amostra insuficiente para o teste (precisa de >5 observações por grupo).")
else:
    st.info("Marque a opção na barra lateral para executar o teste de hipótese.")

if test_success:
    st.markdown(
        f"**Leitura executiva:** a média log10 dos **multilíngues** excede a dos **monolíngues** em **{fmt_num(diff)}** "
        f"(t={fmt_num(tval, '{:.2f}')}, df≈{fmt_num(dfw, '{:.0f}')}, p(one-sided)={fmt_num(p_one, '{:.3g}')}). "
        f"Isto equivale a um fator multiplicativo de **×{fmt_num(fator, '{:.2f}')}** na escala original "
        f"(IC95% do fator: **×{fmt_num(fator_l, '{:.2f}')}** a **×{fmt_num(fator_u, '{:.2f}')}**). "
        "Em termos simples: repositórios com 2+ linguagens tendem a ser **maiores**."
    )
    st.markdown("_Nota:_ o **Welch** evita assumir variâncias iguais; trabalhar em **log10** dá leitura em **razões de tamanho**.")

# ===============================
# RELATÓRIO TEXTUAL (Markdown caprichado)
# ===============================
st.header("Relatório textual")

def build_report_md(ctx: dict, *, calc_corr: bool, calc_test: bool) -> str:
    # Top linguagens (sempre aparece)
    top_lang_txt = (
        f"- **Linguagem líder:** **{ctx.get('top1_name') or '—'}** · **Participação:** {fmt_pct(ctx.get('top1_share'))}\n"
        f"- **Top 3 linguagens (soma):** {fmt_pct(ctx.get('top3_share'))}"
    )

    # Correlação
    if calc_corr and ctx.get("corr_success"):
        corr_txt = (
            f"- **Correlação (r):** {fmt_num(ctx.get('r'))} ({ctx.get('mag', '—')})\n"
            f"- **IC 95% de r:** [{fmt_num(ctx.get('r_low'))}; {fmt_num(ctx.get('r_high'))}]\n"
            f"- **p-valor:** {fmt_num(ctx.get('p'), '{:.3g}')}\n"
            f"- **Leitura:** mais linguagens → tendência a repositórios maiores (em log10)."
        )
    else:
        corr_txt = "- **Correlação:** não calculada neste run (opção desmarcada ou amostra insuficiente)."

    # Teste de hipótese
    if calc_test and ctx.get("test_success"):
        test_txt = (
            f"- **Δ média (log10):** {fmt_num(ctx.get('diff'))}  |  **t:** {fmt_num(ctx.get('tval'), '{:.2f}')}  |  **df≈** {fmt_num(ctx.get('dfw'), '{:.0f}')}\n"
            f"- **IC 95% (Δ):** [{fmt_num(ctx.get('lci'))}; {fmt_num(ctx.get('uci'))}]  |  **p (one-sided):** {fmt_num(ctx.get('p_one'), '{:.3g}')}\n"
            f"- **Fator multiplicativo (bytes):** ×{fmt_num(ctx.get('fator'), '{:.2f}')} "
            f"(IC95% ×{fmt_num(ctx.get('fator_l'), '{:.2f}')}–×{fmt_num(ctx.get('fator_u'), '{:.2f}')} )\n"
            f"- **Conclusão:** repositórios **multilíngues** tendem a ser **maiores** que **monolíngues**."
        )
    else:
        test_txt = "- **Teste (Welch):** não executado neste run (opção desmarcada ou amostra insuficiente)."

    md_sections = [
f"""## 1) Contexto e ideia

Projeto no estilo entrevista de **engenharia de dados / back-end**: dados públicos em larga escala → **evidências quantitativas**
e **insights acionáveis** com custo controlado. Foco em **raciocínio de produção**: modelagem por repositório,
queries transparentes, amostragem estável e inferência com IC/teste.""",

"""## 2) Base de dados

- **Fonte:** `bigquery-public-data.github_repos.languages`
- **Unidade após UNNEST:** (repositório, linguagem, bytes)
- **Visão por repositório:** linguagem dominante · total de bytes · número de linguagens""",

f"""## 3) Perguntas

- Quais linguagens acumulam mais **volume de código** (Top-{ctx.get('top_n')})?
- Repositórios **multilíngues** (≥2 linguagens) tendem a ser **maiores** do que monolíngues?
- Qual a **relação** entre **nº de linguagens** e **tamanho** do repositório?""",

f"""## 4) Resultados descritivos

**Top-{ctx.get('top_n')} por volume**
{top_lang_txt}

**Distribuições e medidas**
- `total_bytes` tem **assimetria à direita** (cauda pesada); análise em **log10** melhora a robustez.
- Medianas/boxplots por **linguagem dominante** mostram diferenças com variabilidade intra-grupo.""",

f"""## 5) Correlação (nº linguagens × tamanho em log10)

{corr_txt}""",

f"""## 6) Teste de hipótese (Welch — multilíngues > monolíngues)

{test_txt}""",

"""## 7) Conclusões

- **Concentração:** poucas linguagens carregam a maior parte do volume de código.
- **Cauda pesada:** trabalhar em **log10** é apropriado.
- **Relação positiva:** mais linguagens costuma vir com repositórios **maiores** (efeito fraco–moderado).
- **Inferência:** evidência de **multilíngues > monolíngues** em média (com leitura em **razões de tamanho**).""",

"""## 8) Limitações e próximos passos

- **Bytes ≠ qualidade/popularidade**; possíveis vieses (monorepos, mirrors).
- **Sem causalidade:** análise é descritiva/inferencial, não causal.
- **Extensões:** segmentar por ecossistema, adicionar séries temporais (GitHub Archive), expor métricas via API."""
    ]

    return "\n\n".join(md_sections).strip()

# montar o contexto com TUDO que o relatório precisa
ctx = {
    "top_n": top_n,
    "top1_name": top1_name,
    "top1_share": top1_share,
    "top3_share": top3_share,
    "corr_success": corr_success,
    "r": r, "p": p, "r_low": r_low, "r_high": r_high, "mag": mag,
    "test_success": test_success,
    "diff": diff, "tval": tval, "dfw": dfw, "lci": lci, "uci": uci, "p_one": p_one,
    "fator": fator, "fator_l": fator_l, "fator_u": fator_u,
}

report_md = build_report_md(ctx, calc_corr=calc_correlation, calc_test=calc_test)

with st.expander("📄 Visualizar relatório (Markdown)", expanded=True):
    st.markdown(report_md)
    st.caption("Copiar texto puro / colar no Docs:")
    st.code(report_md, language="markdown")

# Downloads (MD e TXT)
st.download_button(
    "⬇️ Baixar relatório (.md)",
    data=report_md.encode("utf-8"),
    file_name="relatorio_github_bigquery.md",
    mime="text/markdown",
)
st.download_button(
    "⬇️ Baixar relatório (.txt)",
    data=report_md.replace("#", "").encode("utf-8"),
    file_name="relatorio_github_bigquery.txt",
    mime="text/plain",
)

# ===============================
# RODAPÉ
# ===============================
st.caption(
    f"Última execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • "
    f"Amostra: {sample_pct}% • Top-N: {top_n} • Escala: {scale} • Região BQ: {BQ_LOCATION}"
)
