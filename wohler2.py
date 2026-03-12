import streamlit as st
import numpy as np
import plotly.graph_objects as go
import math
from fpdf import FPDF
import datetime
import time
import seaborn as sns
import matplotlib.pyplot as plt
import tempfile
import os

# --- 1. CONFIGURAZIONE ESTETICA (ORO, NERO, BIANCO) ---
st.set_page_config(page_title="Supernova Lab", page_icon="🚀", layout="wide")

GOLD = "#D4AF37"
BLACK = "#000000"
WHITE = "#FFFFFF"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {BLACK}; color: {WHITE}; }}
    h1, h2, h3 {{ color: {GOLD} !important; text-transform: uppercase; }}
    .stButton>button {{ border: 2px solid {GOLD}; color: {GOLD}; background: transparent; border-radius: 0; width: 100%; font-weight: bold; }}
    .stButton>button:hover {{ background: {GOLD}; color: {BLACK}; }}
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {{
        background-color: #1A1A1A !important; color: {WHITE} !important; border: 1px solid {GOLD} !important;
    }}
    [data-testid="stMetricValue"] {{ color: {GOLD} !important; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 20px; }}
    .stTabs [aria-selected="true"] {{ border-bottom: 2px solid {GOLD} !important; color: {GOLD} !important; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. SISTEMA DI LOGIN PERSONALIZZATO ---
if "auth" not in st.session_state:
    st.session_state["auth"] = False
    st.session_state["atleta"] = ""

if not st.session_state["auth"]:
    st.markdown("<h1 style='text-align:center;'>SUPERNOVA LAB</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:{GOLD};'>DATA OVER TALENT.</p>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1,1.5,1])
    with col_b:
        user = st.text_input("Username (Nome Atleta)")
        pwd = st.text_input("Password", type="password")
        if st.button("ACCEDI"):
            if pwd == "supernova26" and user != "":
                st.session_state["auth"] = True
                st.session_state["atleta"] = user
                st.rerun()
            else: st.error("Credenziali non valide.")
    st.stop()

# --- 3. DATABASE MATERIALI E CARICHI ---
materials_db = {
    "Carbonio UD (Lame Corsa)": {"uts": 1800, "yield": 1800, "se_base": 1050, "cat": "Compositi"},
    "Titanio Ti-6Al-4V ELI": {"uts": 860, "yield": 795, "se_base": 440, "cat": "Metalli"},
    "Acciaio Maraging 250": {"uts": 1750, "yield": 1700, "se_base": 850, "cat": "Metalli"},
    "Alluminio 7075-T6": {"uts": 572, "yield": 503, "se_base": 159, "cat": "Metalli"},
    "PEEK (Socket Alta Resistenza)": {"uts": 100, "yield": 100, "se_base": 45, "cat": "Polimeri"}
}

# --- 4. SIDEBAR INTEGRATA ---
with st.sidebar:
    st.markdown(f"<h2 style='color:{GOLD};'>CONFIGURAZIONE</h2>", unsafe_allow_html=True)
    st.write(f"Atleta: **{st.session_state['atleta']}**")
    sport = st.selectbox("Sport", ["Golf", "Sprint", "Salto in Lungo", "Ciclismo"])
    
    st.markdown("---")
    mat_name = st.selectbox("Materiale Protesi", list(materials_db.keys()))
    mat = materials_db[mat_name]
    
    surf = st.selectbox("Finitura Superficiale", ["Lucidato", "Lavorato", "Grezzo", "Forgiato"])
    
    load_type = st.selectbox("Tipo di Carico", ["Flessione", "Assiale", "Torsione"])
    
    st.info("Affidabilità impostata al 99.9% (Standard Supernova)")
    ke = 0.753 # 99.9% costante

# --- 5. MOTORE DI CALCOLO (IL CUORE FUNZIONANTE) ---
def get_ka(uts, surf_type, mat_cat):
    if mat_cat == "Compositi": return 0.9
    surfs = {"Lucidato": (1.58, -0.085), "Lavorato": (4.51, -0.265), "Grezzo": (57.7, -0.718), "Forgiato": (272.0, -0.995)}
    a, b = surfs[surf_type]
    return min(a * (uts ** b), 1.0)

ka = get_ka(mat['uts'], surf, mat['cat'])
kc = {"Flessione": 1.0, "Assiale": 0.85, "Torsione": 0.59}[load_type]
se_corr = mat['se_base'] * ka * kc * ke

def solve_fatigue(s_max, s_min, mat_data, se_corr_val):
    sigma_a = (s_max - s_min) / 2
    sigma_m = (s_max + s_min) / 2
    if sigma_m >= mat_data['uts']: return 9999, 0, 0, 0 # Rottura
    s_eq = sigma_a / (1 - (sigma_m / mat_data['uts']))
    
    if s_eq <= se_corr_val: return s_eq, float('inf'), 0, 0
    
    f = 0.9
    S1000 = f * mat_data['uts']
    N_end = 1e6 if mat_data['cat'] != "Alluminio" else 5e8
    b_exp = -(math.log10(S1000/se_corr_val)) / (math.log10(N_end)-3)
    log_a = math.log10(S1000) - 3*b_exp
    nf = 10 ** ((math.log10(s_eq) - log_a)/b_exp)
    return s_eq, nf, log_a, b_exp

# --- 6. INTERFACCIA A DUE SETTORI ---
tab1, tab2 = st.tabs(["[ FATIGUE SIMULATOR ]", "[ RACE DAMAGE SIM ]"])

# --- SETTORE 1: FATICA ---
with tab1:
    col1, col2 = st.columns(2)
    s_max = col1.number_input("Stress Max (MPa)", value=400, key="sm1")
    s_min = col2.number_input("Stress Min (MPa)", value=0, key="sn1")
    c_anno = st.number_input("Cicli/Anno", value=100000)
    
    s_eq, nf, log_a, b_exp = solve_fatigue(s_max, s_min, mat, se_corr)
    anni = round(nf/c_anno, 2) if nf != float('inf') else "Infinito"

    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Stress Eq. (Goodman)", f"{int(s_eq)} MPa")
    m2.metric("Limite Fatica (Se)", f"{int(se_corr)} MPa")
    m3.metric("Vita Stimata", f"{anni} anni")

    # Grafico Plotly
    n_plot = np.logspace(3, 7, 100)
    if nf != float('inf') and b_exp != 0:
        s_plot = (10**log_a) * (n_plot**b_exp)
        s_plot = np.maximum(s_plot, se_corr)
    else: s_plot = np.full_like(n_plot, se_corr)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=n_plot, y=s_plot, name="Wöhler Curve", line=dict(color=GOLD)))
    fig.update_layout(xaxis_type="log", template="plotly_dark", title="ANALISI S-N")
    st.plotly_chart(fig, use_container_width=True)

# --- SETTORE 2: GARA ---
with tab2:
    st.subheader("Simulatore Performance in Gara")
    c_r1, c_r2 = st.columns(2)
    durata_gara = c_r1.number_input("Durata Gara (minuti)", value=60)
    freq_passi = c_r2.number_input("Frequenza (passi/min)", value=90)
    s_max_race = st.number_input("Stress Picco in Gara (MPa)", value=500)
    
    cicli_gara = durata_gara * freq_passi
    s_eq_r, nf_r, _, _ = solve_fatigue(s_max_race, 0, mat, se_corr)
    
    danno = (cicli_gara / nf_r) * 100 if nf_r != float('inf') else 0
    rendimento = max(0, 100 - (danno * 1.5)) # Formula Supernova: il danno degrada il ritorno elastico
    
    st.divider()
    r1, r2, r3 = st.columns(3)
    r1.metric("Cicli Totali Gara", int(cicli_gara))
    r2.metric("Danno Strutturale", f"{danno:.4f} %")
    r3.metric("Rendimento Residuo", f"{rendimento:.1f} %")
    
    if danno > 100: st.error("PERICOLO: Cedimento previsto durante la gara!")
    elif danno > 50: st.warning("ATTENZIONE: Alto degrado strutturale.")
    else: st.success("Gara sicura: Integrità strutturale ottimale.")

# --- 7. PDF ENGINE (ORO E NERO) ---
def generate_pdf(mode="Fatigue"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(0, 0, 0)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(212, 175, 55) # ORO
    pdf.cell(0, 20, "SUPERNOVA - DATA OVER TALENT", 0, 1, 'C')
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 12)
    pdf.ln(10)
    pdf.cell(0, 10, f"REPORT: {mode.upper()}", 0, 1)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 7, f"Atleta: {st.session_state['atleta']}", 0, 1)
    pdf.cell(0, 7, f"Sport: {sport}", 0, 1)
    pdf.cell(0, 7, f"Materiale: {mat_name} | Finitura: {surf}", 0, 1)
    pdf.ln(5)
    
    # Dati tecnici
    pdf.set_fill_color(212, 175, 55)
    pdf.cell(0, 8, "RISULTATI TECNICI", 1, 1, 'L', True)
    if mode == "Fatigue":
        pdf.cell(0, 7, f"Stress Eq: {int(s_eq)} MPa", 1, 1)
        pdf.cell(0, 7, f"Vita Utile: {anni} anni", 1, 1)
    else:
        pdf.cell(0, 7, f"Danno in Gara: {danno:.4f} %", 1, 1)
        pdf.cell(0, 7, f"Rendimento Finale: {rendimento:.1f} %", 1, 1)
    
    return pdf.output(dest='S').encode('latin-1')

st.sidebar.divider()
if st.sidebar.button("SCARICA REPORT PDF"):
    pdf_bytes = generate_pdf("Lifecycle" if tab1 else "Race")
    st.sidebar.download_button("Download .pdf", pdf_bytes, "Supernova_Report.pdf")
