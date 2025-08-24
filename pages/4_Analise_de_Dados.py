import math
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
from datetime import datetime
from google.cloud import bigquery
from google.cloud.bigquery import QueryJobConfig

# ===============================
# Config e título
# ===============================
st.set_page_config(page_title="Análise de Dados: GitHub (BigQuery)", layout="wide")
st.title("Análise de Dados: GitHub (BigQuery Public Datasets)")
st.caption("Foco de engenharia: modelagem por repositório, custo/escala, métricas, inferência e explicabilidade.")

# ===============================
# Helpers (formatação e BigQuery)
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
    i = 0
    x = float(n)
    while x >= 1024 and i < len(units) - 1:
        x /= 1024
        i += 1
    return f"{x:,.2f} {units[i]}"

@st.cache_resource(show_spinner=False)
def get_bq_client():
    return bigquery.Client()

def run_query(sql: str, job_config: QueryJobConfig | None = None) -> tuple[pd.DataFrame, int]:
    job = client.query(sql, job_config=job_config)
    df = job.result().to_dataframe()
    bytes_processed = getattr(job, "total_bytes_processed", None)
    return df, (int(bytes_processed) if bytes_processed is not None else -1)

def estimate_bytes(sql: str) -> int:
    qcfg = QueryJobConfig(dry_run=True, use_query_cache=False)
    job = client.query(sql, job_config=qcfg)
    return int(job.total_bytes_processed)

# ===============================
# Sidebar (controles)
# ===============================
st.sidebar.header("Configurações")
sample_pct = st.sidebar.select_slider(
    "Amostragem por repositório (estável via FARM_FINGERPRINT)",
    options=[1, 2, 5, 10, 20, 50, 100],
    value=10,
    key="sample_pct",
    help="Amostra estável por hash de repo_name: reduz custo mantendo representatividade."
)

top_n = st.sidebar.slider(
    "Top-N linguagens por bytes (global)",
    min_value=5, max_value=30, value=20, step=1, key="top_n"
)

scale = st.sidebar.radio(
    "Escala para tamanhos de repositório",
    options=["log10", "linear"],
    index=0,
    help="Distribuição é de cauda pesada; log10 facilita a leitura."
)

calc_correlation = st.sidebar.checkbox("Calcular correlação (r, p, IC)", value=True)
calc_test = st.sidebar.checkbox("Teste de hipótese (Welch: multilíngues > monolíngues)", value=True)

st.sidebar.divider()
st.sidebar.caption("Se necessário: `gcloud auth application-default login` e habilitar BigQuery API no seu projeto.")

# ===============================
# Intro
# ===============================
def render_intro():
    st.header("Contexto e ideia do trabalho")
    st.write(
        """
        Este projeto simula um cenário real de **engenharia de dados / back-end** para entrevista técnica:
        partir de dados públicos em larga escala, transformar eventos de código em **evidências quantitativas**
        e produzir **insights acionáveis** com **custo controlado**. O foco é **raciocínio de produção**:
        modelagem por repositório, transparência das consultas, controle de custos e **inferência estatística**.
        """
    )

    st.subheader("Base de dados (o que é e como será usada)")
    st.write(
        """
        Utilizo o conjunto público **GitHub on BigQuery** (`bigquery-public-data.github_repos.languages`).
        Após expandir o campo `language` com `UNNEST`, cada registro representa **(repositório, linguagem, bytes)**.
        Para responder às perguntas, construo uma visão **por repositório** com:
        1) **Linguagem dominante** (a que mais acumula bytes no repo),  
        2) **Tamanho total** do repositório em bytes (soma de todas as linguagens),  
        3) **Número de linguagens** distintas por repositório.
        """
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.info(f"**Amostragem estável**\n\n~**{st.session_state.get('sample_pct', sample_pct)}%** via `FARM_FINGERPRINT(repo_name)` para reduzir custo.")
    with c2:
        st.info(f"**Top linguagens**\n\nExibo **Top-{st.session_state.get('top_n', top_n)}** por bytes para evidenciar concentração.")
    with c3:
        st.info("**Tratamento estatístico**\n\nUso `log10(total_bytes+1)` para lidar com **cauda pesada**.")

    st.subheader("Perguntas norteadoras")
    st.markdown(
        f"""
        - Quais linguagens acumulam maior **volume de código** (Top-{st.session_state.get('top_n', top_n)})?
        - Repositórios **multilíngues** (≥2 linguagens) tendem a ser **maiores** do que **monolíngues**?
        - Qual a **relação** entre **número de linguagens** e **tamanho** do repositório?
        """
    )

    st.subheader("Metodologia (resumo prático)")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            """
            **Modelagem e custo**
            - Agrego por repositório → `dominant_language`, `total_bytes`, `num_languages`.
            - **Amostragem estável** por hash (barata e reprodutível).
            - **Cache** das consultas e **queries transparentes** no app.
            """
        )
    with col_b:
        st.markdown(
            """
            **Estatística e inferência**
            - Exploração: Top-N, histogramas/boxplots e medidas centrais por linguagem dominante.
            - Correlação: **Pearson** entre `num_languages` e `log10(total_bytes)` com **IC 95%**.
            - Hipótese: **Welch’s t-test** (variâncias possivelmente diferentes) comparando
              **multilíngues vs monolíngues**, com **Δ em log10**, **IC 95%** e **fator multiplicativo** na escala original.
            """
        )

    st.divider()

render_intro()

# ===============================
# Tipos de variáveis
# ===============================
st.subheader("Tipos de variáveis (nomenclatura formal)")
tipos_df = pd.DataFrame([
    ["repo_name", "Qualitativa (Nominal)", "Nominal", "Identificador do repositório (rótulo, sem ordenação)."],
    ["language_name", "Qualitativa (Nominal)", "Nominal", "Nome da linguagem (categoria sem ordem)."],
    ["bytes", "Quantitativa (Contínua/contagem)", "Razão", "Bytes por linguagem no repo; zero é significativo; proporções fazem sentido."],
    ["total_bytes", "Quantitativa (Contínua)", "Razão", "Soma de bytes do repo; zero possível; dobrar/triplicar tem interpretação."],
    ["num_languages", "Quantitativa (Discreta)", "Razão", "Contagem de linguagens distintas no repo."],
    ["dominant_language", "Qualitativa (Nominal)", "Nominal", "Linguagem com mais bytes no repo."],
    ["log10_total_bytes", "Quantitativa (Contínua)", "Intervalar*", "Transformação para estabilizar cauda pesada (*diferenças em log viram razões na escala original*)."],
], columns=["Variável", "Tipo estatístico", "Escala de medida", "Observações"])
st.dataframe(tipos_df, use_container_width=True)
st.caption("Obs.: **Razão** possui zero absoluto e permite interpretações multiplicativas; **log10** torna a análise robusta em cauda pesada.")

# ===============================
# Cliente BigQuery
# ===============================
try:
    client = get_bq_client()
except Exception as e:
    st.error(f"Não consegui criar o cliente do BigQuery: {e}")
    st.stop()

# ===============================
# Queries (dinâmicas)
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
# Estimativas de custo e execução
# ===============================
col_est1, col_est2 = st.columns(2)
with col_est1:
    try:
        est_top = estimate_bytes(sql_top_langs)
        st.info(f"Estimativa Top Linguagens: {human_bytes(est_top)}")
    except Exception:
        st.info("Estimativa Top Linguagens indisponível (ok).")

with col_est2:
    try:
        est_repo = estimate_bytes(sql_per_repo)
        warn = "⚠️" if est_repo > 5 * 1024**3 else ""
        st.info(f"{warn} Estimativa Visão por Repo (amostra {sample_pct}%): {human_bytes(est_repo)}")
    except Exception:
        st.info("Estimativa por Repo indisponível (ok).")

st.write("Rodando consultas…")
df_top, bytes_top = run_query(sql_top_langs)
df_repo, bytes_repo = run_query(sql_per_repo)

colb1, colb2 = st.columns(2)
with colb1:
    st.success(f"Top Linguagens — Bytes processados: {human_bytes(bytes_top)}")
with colb2:
    st.success(f"Visão por Repo — Bytes processados: {human_bytes(bytes_repo)} (amostra {sample_pct}%)")

# ===============================
# 2) Exploração: medidas, distribuições e correlação
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

top_total = df_top["total_bytes"].sum() if len(df_top) else np.nan
top1_name = df_top.iloc[0]["language_name"] if len(df_top) else None
top1_share = (df_top.iloc[0]["total_bytes"] / top_total) * 100 if len(df_top) else np.nan
top3_share = (df_top.iloc[:3]["total_bytes"].sum() / top_total) * 100 if len(df_top) >= 3 else np.nan
st.markdown(
    f"**Comentário:** No **Top-{top_n}**, **{top1_name or '—'}** concentra **{fmt_pct(top1_share)}**; as **3 primeiras** somam **{fmt_pct(top3_share)}**. "
    "Padrão de **concentração** típico em dados de larga escala."
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
    "**Comentário:** histograma com **assimetria à direita** (muitos repos pequenos, poucos gigantes). "
    "No boxplot, observe **dispersão intra-grupo** e **outliers**; em **log10**, as diferenças ficam mais legíveis."
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
        from scipy import stats as ststats
        zcrit = ststats.norm.ppf(0.975)
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
# 3) Inferência: IC 95% e Teste de hipótese (Welch)
# ===============================
st.header("Inferência: IC 95% e Teste de hipótese")

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
    st.markdown(
        "_Nota:_ o **Welch** é adequado quando os grupos podem ter variâncias diferentes e tamanhos desbalanceados; "
        "trabalhar em **log10** torna a comparação mais robusta e dá interpretação em **razões de tamanho**."
    )

# ===============================
# 4) Relatório textual consolidado (+ download)
# ===============================
st.header("Relatório textual")
st.caption("Parágrafos gerados automaticamente com base nos resultados acima.")

def build_report_text():
    # Bloco apresentação / ideia
    intro = f"""
**Apresentação da base.**
Uso o conjunto público GitHub on BigQuery (`bigquery-public-data.github_repos.languages`).
Após `UNNEST(language)`, cada registro representa (repositório, linguagem, bytes).
A visão por repositório inclui: (i) linguagem dominante, (ii) tamanho total (bytes) e (iii) número de linguagens distintas.

**Perguntas.**
Top-{top_n} por volume, multilíngues (≥2) são maiores que monolíngues? Qual a relação entre nº de linguagens e tamanho?
"""

    # Tipos de variáveis
    tipos = """
**Tipos de variáveis.**
Qualitativas (Nominal): repo_name, language_name, dominant_language.
Quantitativas: Discreta — num_languages; Contínua (Razão) — bytes e total_bytes.
Transformação: log10(total_bytes+1) para lidar com cauda pesada.
"""

    # Exploração com números dinâmicos
    expl = f"""
**Exploração descritiva.**
Concentração: no Top-{top_n}, {top1_name or '—'} ≈ {fmt_pct(top1_share)}; as 3 primeiras ≈ {fmt_pct(top3_share)}.
Distribuição: assimetria à direita; em log10, comparações de grupos ficam mais robustas.
Medidas por linguagem dominante: médias/medianas (log) e desvios indicam diferenças com variabilidade intra-grupo.
"""

    # Correlação
    if calc_correlation and corr_success:
        corr_txt = f"Correlação: r={fmt_num(r)}, IC95% [{fmt_num(r_low)}; {fmt_num(r_high)}], p={fmt_num(p, '{:.3g}')}. Magnitude: {mag}."
    else:
        corr_txt = "Correlação: não calculada neste run (opção desmarcada ou amostra insuficiente)."

    # Teste
    if calc_test and test_success:
        test_txt = (
            f"Teste de hipótese (Welch) em log10(total_bytes+1): Δ={fmt_num(diff)} "
            f"(IC95% [{fmt_num(lci)}; {fmt_num(uci)}], p(one-sided)={fmt_num(p_one, '{:.3g}')}). "
            f"Equivale a fator ≈ ×{fmt_num(fator, '{:.2f}')} (IC95% ×{fmt_num(fator_l, '{:.2f}')}–×{fmt_num(fator_u, '{:.2f}')}), "
            f"indicando que multilíngues tendem a ser maiores."
        )
    else:
        test_txt = "Teste de hipótese (Welch): não executado neste run (opção desmarcada ou amostra insuficiente)."

    # Conclusões e limitações
    concl = """
**Conclusões.**
(1) Padrão de concentração por linguagem; (2) cauda pesada → log10 é apropriado;
(3) relação positiva (fraca–moderada) entre nº de linguagens e tamanho; (4) efeito significativo: multilíngues > monolíngues.

**Limitações.**
Bytes ≠ qualidade/popularidade; possível viés por monorepos/espelhos; causalidade fora de escopo.

**Próximos passos.**
Segmentar por ecossistema (Python/JS/Java); analisar séries temporais (GitHub Archive);
expor resultados via endpoints para consumo por outros serviços.
"""

    return "\n".join([intro.strip(), tipos.strip(), expl.strip(), corr_txt.strip(), test_txt.strip(), concl.strip()])

report_text = build_report_text()
with st.expander("Mostrar/ocultar relatório", expanded=True):
    st.markdown(report_text)

st.download_button(
    "Baixar relatório (TXT)",
    data=report_text.encode("utf-8"),
    file_name="relatorio_github_bigquery.txt",
    mime="text/plain"
)

# ===============================
# Rodapé
# ===============================
st.caption(
    f"Última execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    f"Amostra por repo: {sample_pct}% | Top-N linguagens: {top_n} | Escala: {scale}"
)
