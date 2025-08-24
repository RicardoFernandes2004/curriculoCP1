import streamlit as st

st.set_page_config(page_title="Formação e Experiência", layout="wide")

st.title("🎓 Formação e Experiência")

# ====== CSS ANTIGO (gradiente + cards glass) ======
st.markdown("""
<style>
section[data-testid="stSidebar"] { background: linear-gradient(180deg,#0ea5e910,#22c55e10); }

/* HERO */
.hero { padding: 18px 20px; border-radius: 16px;
        background: linear-gradient(135deg, #0ea5e93a, #22c55e24);
        border: 1px solid rgba(16,185,129,.25); }
.gradient { background: linear-gradient(90deg,#0ea5e9,#22c55e,#a855f7);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

/* cards (glass) */
.card { padding: 16px 18px; border-radius: 14px;
        border: 1px solid rgba(148,163,184,.25);
        background: rgba(255,255,255,.55); backdrop-filter: blur(6px); margin-bottom: 12px; }
[data-theme="dark"] .card { background: rgba(17,17,17,.55); }
.card h3 { margin: 0 0 4px 0; }
.meta { color: #64748b; font-size: .95rem; }

/* chips reutilizáveis */
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 6px; }
.chip  { font-size: .88rem; padding: 6px 10px; border-radius: 999px;
         border: 1px solid rgba(148,163,184,.35); background: rgba(148,163,184,.15); }
ul.bullets { margin: 8px 0 0 18px; } ul.bullets li { margin: 3px 0; }
</style>
""", unsafe_allow_html=True)

# ====== HERO MINI ======
st.markdown("""
<div class="hero">
  <h3 style="margin:0"><span class="gradient">Trajetória</span></h3>
  <p style="margin:6px 0 0 0">Formação acadêmica e experiência profissional</p>
</div>
""", unsafe_allow_html=True)
st.write("")

# ====== EDUCAÇÃO (conteúdo igual ao seu) ======
st.subheader("Educação")
st.markdown("""
<div class="card">
  <h3>FIAP - Faculdade de Informática e Administração Paulista</h3>
  <div class="meta">Bacharelado em Engenharia de Software – <b>2024-atual</b></div>
</div>
""", unsafe_allow_html=True)

# ====== EXPERIÊNCIA (conteúdo igual ao seu) ======
st.subheader("Experiência Profissional")
st.markdown("""
<div class="card">
  <h3>Assistente Administrativo <span class="meta">(Informal - Loja Familiar)</span></h3>
  <div class="meta"><b>Período:</b> 06/2022 - Atual</div>
  <ul class="bullets">
    <li>Atendimento ao cliente, incluindo suporte a estrangeiros em diferentes idiomas.</li>
    <li>Uso do Pacote Office para controle de estoque, emissão de relatórios e organização administrativa.</li>
    <li>Auxílio no gerenciamento financeiro e organização de documentos da loja.</li>
    <li><b>Tecnologias:</b> Microsoft Excel, Word, PowerPoint.</li>
  </ul>
  <div class="chips">
    <span class="chip">Atendimento</span>
    <span class="chip">Organização</span>
    <span class="chip">Pacote Office</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ====== Navegação (opcional) ======
if hasattr(st, "page_link"):
    st.page_link("0_Home.py", label="🏠 Voltar à Home", icon=":material/home:")
    st.page_link("pages/2_Skills.py", label="🧰 Ir para Skills", icon=":material/handyman:")
    st.page_link("pages/3_Projetos_Selecionados.py", label="📦 Ir para Projetos", icon=":material/rocket_launch:")
    st.page_link("pages/4_Analise_de_Dados.py", label="🔎 Ir para Análise de Dados", icon=":material/insights:")
