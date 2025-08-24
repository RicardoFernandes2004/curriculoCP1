import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="Dashboard Profissional",
    page_icon="👋",
    layout="wide"
)

# ====== Estilos (CSS leve) ======
st.markdown("""
<style>
.main blockquote, .stMarkdown p { line-height: 1.5; }
section[data-testid="stSidebar"] { background: linear-gradient(180deg,#0ea5e910,#22c55e10); }

/* HERO */
.hero { padding: 28px 28px 18px; border-radius: 18px;
        background: linear-gradient(135deg, #0ea5e93a, #22c55e24);
        border: 1px solid rgba(16,185,129,.25); }
.hero h1 { margin: 0 0 6px 0; font-size: 2rem; }
.gradient { background: linear-gradient(90deg,#0ea5e9,#22c55e,#a855f7);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

/* cartões */
.card { padding: 16px 18px; border-radius: 14px; border: 1px solid rgba(148,163,184,.25);
        background: rgba(255,255,255,.55); backdrop-filter: blur(6px); }
[data-theme="dark"] .card { background: rgba(17,17,17,.55); }

/* chips */
.chips { display: flex; flex-wrap: wrap; gap: 8px; }
.chip { font-size: .90rem; padding: 6px 10px; border-radius: 999px;
        border: 1px solid rgba(148,163,184,.35); background: rgba(148,163,184,.15); white-space: nowrap; }

/* botões link */
a.btn { display: inline-block; padding: 10px 14px; border-radius: 10px;
        border: 1px solid rgba(148,163,184,.35); text-decoration: none; font-weight: 600;
        transition: transform .05s ease-in; }
a.btn:hover { transform: translateY(-1px); }
a.primary { background:#0ea5e91a; border-color:#0ea5e950; }
a.success { background:#22c55e1a; border-color:#22c55e50; }
a.ghost   { background:transparent; }
</style>
""", unsafe_allow_html=True)

# ====== HERO ======
st.title("👋 Olá! Bem-vindo(a) ao meu Dashboard Profissional")
st.markdown("""
<div class="hero">
  <h1><span class="gradient">Ricardo Fernandes de Aquino</span></h1>
  <h3 style="margin-top:0">Desenvolvedor Back-end · Java / Spring Boot</h3>
  <p style="margin:6px 0 0 0">Estudante de Engenharia de Software (FIAP) focado em back-end com Java/Spring.</p>
</div>
""", unsafe_allow_html=True)
st.write("")

# ====== Contatos ======
col1, col2, col3, col4 = st.columns([1.2,1,1,1])
with col1:
    st.markdown('<div class="card"><b>E-mail</b><br><a href="mailto:ricardo.fernandes02082004@gmail.com">ricardo.fernandes02082004@gmail.com</a></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="card"><b>WhatsApp</b><br><a href="https://wa.me/5511972210332" target="_blank">+55 (11) 97221-0332</a></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="card"><b>GitHub</b><br><a href="https://github.com/RicardoFernandes2004" target="_blank">github.com/RicardoFernandes2004</a></div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="card"><b>LinkedIn</b><br><a href="https://www.linkedin.com/in/ricardo-fernandes-8017b5261" target="_blank">linkedin.com/in/ricardo-fernandes-8017b5261</a></div>', unsafe_allow_html=True)

st.write("")

# ====== Resumo (texto original, inalterado) ======
st.subheader("Resumo")
st.markdown("""
<div class="card">
Estudante de Engenharia de Software (FIAP) focado em back-end com Java/Spring. Experiência sólida em APIs REST, SQL (PostgreSQL, MySQL, Oracle), NoSQL (MongoDB, DynamoDB), segurança (JWT, Spring Security), migrações (Flyway) e Docker. Já entreguei projetos acadêmicos e pessoais com integração a IA/ML, tempo real (WebSockets) e dispositivos (Arduino). Perfil Hands-on, documentação objetiva e código limpo. Busco estágio/posição júnior em back-end para acelerar entregas e aprender com time sênior.
</div>
""", unsafe_allow_html=True)

# ====== Skills (chips) ======
st.subheader("Stack • Ferramentas • Conceitos")
skills = [
    "Java 17+", "Spring Boot", "Spring Security (JWT)",
    "APIs REST", "JPA/Hibernate", "JUnit",
    "SQL: PostgreSQL · MySQL · Oracle", "NoSQL: MongoDB · DynamoDB",
    "Flyway (migrações)", "Docker", "WebSockets",
    "Integração com IA/ML (Python)", "Arduino"
]
st.markdown('<div class="card"><div class="chips">' + ''.join([f'<span class="chip">{s}</span>' for s in skills]) + '</div></div>', unsafe_allow_html=True)

# ====== Acessos rápidos (integra com tua ESTRUTURA REAL) ======
st.subheader("Acessos rápidos")
# Usa a API nativa de multipage do Streamlit (1.48 tem isso)
if hasattr(st, "page_link"):
    st.page_link("pages/1_Formacao_e_Experiencia.py", label="🎓 Formação & Experiência", icon=":material/school:")
    st.page_link("pages/2_Skills.py",                  label="🧰 Skills",                icon=":material/handyman:")
    st.page_link("pages/3_Projetos_Selecionados.py",   label="📦 Projetos Selecionados", icon=":material/rocket_launch:")
    st.page_link("pages/4_Analise_de_Dados.py",        label="🔎 Análise de Dados (GitHub)", icon=":material/insights:")
else:
    # fallback: links “simples”
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<a class="btn primary" href="pages/1_Formacao_e_Experiencia.py">🎓 Formação & Experiência</a>', unsafe_allow_html=True)
    with c2:
        st.markdown('<a class="btn success" href="pages/2_Skills.py">🧰 Skills</a>', unsafe_allow_html=True)
    with c3:
        st.markdown('<a class="btn ghost" href="pages/3_Projetos_Selecionados.py">📦 Projetos Selecionados</a>', unsafe_allow_html=True)
    st.markdown('<a class="btn primary" href="pages/4_Analise_de_Dados.py">🔎 Análise de Dados (GitHub)</a>', unsafe_allow_html=True)

# ====== Rodapé ======
st.sidebar.success("Selecione uma página acima para explorar!")
st.caption(f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')} • Tema adaptável claro/escuro • Feito com Streamlit")
