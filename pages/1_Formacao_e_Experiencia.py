import streamlit as st

st.set_page_config(page_title="Formação e Experiência", layout="wide")

st.title("🎓 Formação e Experiência")

with st.container(border=True):
    st.header("Educação")
    st.subheader("FIAP - Faculdade de Informática e Administração Paulista")
    st.write("Bacharelado em Engenharia de Software – 2024-atual")

with st.container(border=True):
    st.header("Experiência Profissional")
    st.subheader("Assistente Administrativo (Informal - Loja Familiar)")
    st.write("**Período:** 06/2022 - Atual")
    st.write("""
    - Atendimento ao cliente, incluindo suporte a estrangeiros em diferentes idiomas.
    - Uso do Pacote Office para controle de estoque, emissão de relatórios e organização administrativa.
    - Auxílio no gerenciamento financeiro e organização de documentos da loja.
    - **Tecnologias:** Microsoft Excel, Word, PowerPoint.
    """)
