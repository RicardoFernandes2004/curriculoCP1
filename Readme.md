## 1) Contexto e ideia

Projeto no estilo entrevista de **engenharia de dados / back-end**: dados públicos em larga escala → **evidências quantitativas**
e **insights acionáveis** com custo controlado. Foco em **raciocínio de produção**: modelagem por repositório,
queries transparentes, amostragem estável e inferência com IC/teste.

## 2) Base de dados

- **Fonte:** `bigquery-public-data.github_repos.languages`
- **Unidade após UNNEST:** (repositório, linguagem, bytes)
- **Visão por repositório:** linguagem dominante · total de bytes · número de linguagens

## 3) Perguntas

- Quais linguagens acumulam mais **volume de código** (Top-20)?
- Repositórios **multilíngues** (≥2 linguagens) tendem a ser **maiores** do que monolíngues?
- Qual a **relação** entre **nº de linguagens** e **tamanho** do repositório?

## 4) Resultados descritivos

**Top-20 por volume**
- **Linguagem líder:** **C** · **Participação:** 60.4%
- **Top 3 linguagens (soma):** 78.2%

**Distribuições e medidas**
- `total_bytes` tem **assimetria à direita** (cauda pesada); análise em **log10** melhora a robustez.
- Medianas/boxplots por **linguagem dominante** mostram diferenças com variabilidade intra-grupo.

## 5) Correlação (nº linguagens × tamanho em log10)

- **Correlação (r):** 0.611 (forte)
- **IC 95% de r:** [0.608; 0.613]
- **p-valor:** 0
- **Leitura:** mais linguagens → tendência a repositórios maiores (em log10).

## 6) Teste de hipótese (Welch — multilíngues > monolíngues)

- **Δ média (log10):** 1.028  |  **t:** 305.14  |  **df≈** 292704
- **IC 95% (Δ):** [1.022; 1.035]  |  **p (one-sided):** 0
- **Fator multiplicativo (bytes):** ×10.67 (IC95% ×10.51–×10.83 )
- **Conclusão:** repositórios **multilíngues** tendem a ser **maiores** que **monolíngues**.

## 7) Conclusões

- **Concentração:** poucas linguagens carregam a maior parte do volume de código.
- **Cauda pesada:** trabalhar em **log10** é apropriado.
- **Relação positiva:** mais linguagens costuma vir com repositórios **maiores** (efeito fraco–moderado).
- **Inferência:** evidência de **multilíngues > monolíngues** em média (com leitura em **razões de tamanho**).

## 8) Limitações e próximos passos

- **Bytes ≠ qualidade/popularidade**; possíveis vieses (monorepos, mirrors).
- **Sem causalidade:** análise é descritiva/inferencial, não causal.
- **Extensões:** segmentar por ecossistema, adicionar séries temporais (GitHub Archive), expor métricas via API.