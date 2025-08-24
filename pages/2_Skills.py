import streamlit as st

st.set_page_config(page_title="Skills", layout="wide")

# ====== Estilos (CSS leve, combina com a Home) ======
st.markdown("""
<style>
section[data-testid="stSidebar"] { background: linear-gradient(180deg,#0ea5e910,#22c55e10); }

/* título/hero mini */
.hero { padding: 18px 20px; border-radius: 16px;
        background: linear-gradient(135deg, #0ea5e93a, #22c55e24);
        border: 1px solid rgba(16,185,129,.25); }
.gradient { background: linear-gradient(90deg,#0ea5e9,#22c55e,#a855f7);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

/* cards e chips */
.card { padding: 16px 18px; border-radius: 14px; border: 1px solid rgba(148,163,184,.25);
        background: rgba(255,255,255,.55); backdrop-filter: blur(6px); }
[data-theme="dark"] .card { background: rgba(17,17,17,.55); }
.card h4 { margin: 0 0 8px 0; }

.chips { display: flex; flex-wrap: wrap; gap: 8px; }
.chip  { font-size: .92rem; padding: 6px 10px; border-radius: 999px;
         border: 1px solid rgba(148,163,184,.35); background: rgba(148,163,184,.15); white-space: nowrap; }

/* listas compactas */
.stack ul { margin: 0; padding-left: 18px; }
.stack li { margin: 2px 0; }
</style>
""", unsafe_allow_html=True)

# ====== HERO ======
st.title("🛠️ Skills")
st.markdown('<div class="hero"><h3 style="margin:0">Mapa técnico</h3><p style="margin:6px 0 0 0">Stack, ferramentas e conceitos — com foco em back-end Java/Spring.</p></div>', unsafe_allow_html=True)
st.write("")

# ====== Dados (mesmo conteúdo que você já tinha) ======
linguagens = ["Java (17+)", "Python (IA/ML, Django)", "JavaScript / TypeScript (Node.js)"]
frameworks = ["Spring Boot, Spring Security, JPA/Hibernate"]
apis_arq   = ["RESTful, validação, paginação, tratamento de erros (ControllerAdvice), testes (JUnit)"]
bancos     = ["PostgreSQL (tipos ENUM, migrações com Flyway)", "MongoDB"]
devops     = ["Git/GitHub, GitHub Actions (básico), Docker, Insomnia/Postman"]
cloud_outros = ["AWS (Cloud Quest: Cloud Practitioner badge)", "Socket.IO (tempo real), Arduino/IoT (prototipagem)"]

# ====== GRID DE CARDS ======
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="card stack"><h4>👨‍💻 Linguagens</h4><div class="chips">' +
                ''.join([f'<span class="chip">{x}</span>' for x in linguagens]) +
                '</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="card stack"><h4>🏛️ APIs & Arquitetura</h4><ul>' +
                ''.join([f'<li>{x}</li>' for x in apis_arq]) +
                '</ul></div>', unsafe_allow_html=True)

    st.markdown('<div class="card stack"><h4>⚙️ DevOps & Ferramentas</h4><ul>' +
                ''.join([f'<li>{x}</li>' for x in devops]) +
                '</ul></div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card stack"><h4>🏗️ Frameworks</h4><ul>' +
                ''.join([f'<li>{x}</li>' for x in frameworks]) +
                '</ul></div>', unsafe_allow_html=True)

    st.markdown('<div class="card stack"><h4>🗃️ Bancos de Dados</h4><ul>' +
                ''.join([f'<li>{x}</li>' for x in bancos]) +
                '</ul></div>', unsafe_allow_html=True)

    st.markdown('<div class="card stack"><h4>☁️ Cloud & Outros</h4><ul>' +
                ''.join([f'<li>{x}</li>' for x in cloud_outros]) +
                '</ul></div>', unsafe_allow_html=True)

st.write("")

# ====== Atalhos (integração multipage) ======
st.subheader("Navegar")
if hasattr(st, "page_link"):
    st.page_link("0_Home.py",                         label="🏠 Voltar à Home",         icon=":material/home:")
    st.page_link("pages/3_Projetos_Selecionados.py",  label="📦 Projetos Selecionados", icon=":material/rocket_launch:")
    st.page_link("pages/4_Analise_de_Dados.py",       label="🔎 Análise de Dados",      icon=":material/insights:")
else:
    st.write("Use o menu lateral para navegar.")

