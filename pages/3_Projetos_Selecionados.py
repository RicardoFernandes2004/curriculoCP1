import streamlit as st

st.set_page_config(page_title="Projetos Selecionados", layout="wide")
st.title("🚀 Projetos Selecionados")
st.caption("Alguns projetos que desenvolvi — foco em aplicação prática e back-end.")

# ====== Estilos (CSS leve, mesmo padrão das outras páginas) ======
st.markdown("""
<style>
section[data-testid="stSidebar"] { background: linear-gradient(180deg,#0ea5e910,#22c55e10); }

.card { padding: 16px 18px; border-radius: 14px; border: 1px solid rgba(148,163,184,.25);
        background: rgba(255,255,255,.55); backdrop-filter: blur(6px); margin-bottom: 12px; }
[data-theme="dark"] .card { background: rgba(17,17,17,.55); }

.card h3 { margin: 0 0 6px 0; font-size: 1.1rem; }
.meta { font-size: .90rem; color: #64748b; margin-bottom: 8px; }

.chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 6px 0 8px 0; }
.chip  { font-size: .86rem; padding: 5px 9px; border-radius: 999px;
         border: 1px solid rgba(148,163,184,.35); background: rgba(148,163,184,.15); white-space: nowrap; }

ul.bullets { margin: 8px 0 0 18px; }
ul.bullets li { margin: 2px 0; }

a.btn {
  display:inline-block; padding:8px 12px; border-radius:10px; border:1px solid rgba(148,163,184,.35);
  text-decoration:none; font-weight:600; margin-top:6px;
}
a.btn:hover { transform: translateY(-1px); }
a.ghost { background: transparent; }
</style>
""", unsafe_allow_html=True)

# ====== Dados (conteúdo fiel ao seu texto) ======
projects = [
    {
        "title": "Plataforma de Denúncias Anônimas",
        "year": "2025",
        "subtitle": "Back-end Spring Boot + PostgreSQL",
        "bullets": [
            "API REST com autenticação JWT, autorização com Spring Security e perfis de acesso.",
            "Migrações Flyway, uso de ENUMs nativos no Postgres, documentação de endpoints e paginação.",
            "Tratamento global de erros (ControllerAdvice) e validações robustas.",
            "Resultado: Base para denúncias anônimas com hash apenas para admins, priorizando privacidade e segurança.",
        ],
        "tags": ["Java", "Spring Boot", "Spring Security", "JWT", "PostgreSQL", "Flyway", "API REST"],
        "repo": None,  # coloque a URL do repositório se quiser
    },
    {
        "title": "TechRac-E (FIAP)",
        "year": "2024",
        "subtitle": "Plataforma interativa Fórmula E",
        "bullets": [
            "Site com previsão de resultados usando modelo XGBoost com 93,33% de acurácia (Python).",
            "Back-end web tempo real com Socket.IO, integração com Arduino para controles e telemetria.",
            "Autenticação e perfis; páginas com conteúdo exclusivo e missões (MVP acadêmico).",
        ],
        "tags": ["Python", "XGBoost", "Tempo real", "Socket.IO", "Arduino", "Autenticação"],
        "repo": None,
    },
    {
        "title": "LumePath (FIAP)",
        "year": "2025",
        "subtitle": "API Java para dispositivo de medição em patologia",
        "bullets": [
            "API Java/Spring para receber e persistir medições de LiDAR + câmera.",
            "Foco em consistência de dados, endpoints REST e integração futura com painel web.",
        ],
        "tags": ["Java", "Spring Boot", "API REST", "LiDAR", "Dados de sensor"],
        "repo": None,
    },
    {
        "title": "URL Shortener",
        "year": "2025",
        "subtitle": "Spring Boot + PostgreSQL",
        "bullets": [
            "Encurtador de URLs com geração de tokens/UUID, redirecionamento e métricas básicas.",
            "Ênfase em boas práticas de API, camadas, testes e containerização.",
        ],
        "tags": ["Java", "Spring Boot", "PostgreSQL", "Docker", "API REST", "UUID"],
        "repo": None,
    },
]

# ====== Filtros (busca + tags) ======
all_tags = sorted({t for p in projects for t in p["tags"]})
colf1, colf2 = st.columns([2, 2])
with colf1:
    q = st.text_input("🔎 Buscar por texto (título, subtítulo, bullets)", "")
with colf2:
    chosen = st.multiselect("🏷️ Filtrar por tags (opcional)", all_tags, [])

def match(p):
    text = " ".join([p["title"], p["subtitle"], *p["bullets"]]).lower()
    ok_text = q.lower() in text if q else True
    ok_tags = all(t in p["tags"] for t in chosen) if chosen else True
    return ok_text and ok_tags

filtered = [p for p in projects if match(p)]
st.write("")

# ====== Renderização (cards em grid) ======
cols = st.columns(2)  # 2 cards por linha
for i, proj in enumerate(filtered):
    with cols[i % 2]:
        st.markdown(f"""
<div class="card">
  <h3>{proj['title']} <span class="meta">({proj['year']})</span></h3>
  <div class="meta">{proj['subtitle']}</div>
  <div class="chips">{''.join([f'<span class="chip">{t}</span>' for t in proj['tags']])}</div>
  <ul class="bullets">
    {''.join([f"<li>{b}</li>" for b in proj['bullets']])}
  </ul>
  {'<a class="btn ghost" href="'+proj["repo"]+'" target="_blank">Ver repositório</a>' if proj['repo'] else ''}
</div>
""", unsafe_allow_html=True)

if not filtered:
    st.info("Nenhum projeto encontrado com os filtros selecionados.")

st.divider()
st.info("📁 **Mais projetos:** https://github.com/RicardoFernandes2004", icon="ℹ️")

# ====== Navegação (opcional) ======
if hasattr(st, "page_link"):
    st.page_link("0_Home.py", label="🏠 Voltar à Home", icon=":material/home:")
    st.page_link("pages/2_Skills.py", label="🧰 Ir para Skills", icon=":material/handyman:")
    st.page_link("pages/4_Analise_de_Dados.py", label="🔎 Ir para Análise de Dados", icon=":material/insights:")
