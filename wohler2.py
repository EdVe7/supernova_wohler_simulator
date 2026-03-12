# =====================================================================
# SUPERNOVA PROSTHETICS LAB - ADVANCED FATIGUE & RACE SIMULATOR
# Motto: Data over talent.
# =====================================================================

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

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Supernova Lab", page_icon="⚙️", layout="wide")

# --- STILE CSS (NERO, ORO, BIANCO) ---
GOLD = "#D4AF37"
BLACK = "#000000"
DARK_GREY = "#1A1A1A"
WHITE = "#FFFFFF"

st.markdown(f"""
    <style>
    /* Sfondo e Testi principali */
    .stApp {{
        background-color: {BLACK};
        color: {WHITE};
    }}
    /* Nascondi menu Streamlit */
    #MainMenu {{visibility: hidden;}} 
    footer {{visibility: hidden;}} 
    header {{visibility: hidden;}}
    .stDeployButton {{display:none;}}
    
    /* Titoli e Testi */
    h1, h2, h3, h4, h5, h6, p, span, div {{
        color: {WHITE} !important;
    }}
    h1 {{
        color: {GOLD} !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }}
    
    /* Bottoni */
    .stButton>button {{
        background-color: transparent !important;
        color: {GOLD} !important;
        border: 2px solid {GOLD} !important;
        border-radius: 0px;
        transition: 0.3s;
        font-weight: bold;
        text-transform: uppercase;
    }}
    .stButton>button:hover {{
        background-color: {GOLD} !important;
        color: {BLACK} !important;
    }}
    
    /* Input testuali e numerici */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {{
        background-color: {DARK_GREY} !important;
        color: {WHITE} !important;
        border: 1px solid {GOLD} !important;
    }}
    
    /* Dropdown/Selectbox */
    .stSelectbox>div>div>div {{
        background-color: {DARK_GREY} !important;
        color: {WHITE} !important;
        border: 1px solid {GOLD} !important;
    }}
    
    /* Metriche */
    [data-testid="stMetricValue"] {{
        color: {GOLD} !important;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 20px;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 0px;
        color: {WHITE};
        border-bottom: 2px solid transparent;
    }}
    .stTabs [aria-selected="true"] {{
        border-bottom: 2px solid {GOLD} !important;
        color: {GOLD} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# =====================================================================
# SISTEMA DI LOGIN (USER & PASS)
# =====================================================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""

if not st.session_state["authenticated"]:
    st.markdown("<h1 style='text-align:center;'>SUPERNOVA LAB</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:{GOLD} !important; letter-spacing: 3px;'>DATA OVER TALENT.</p>", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1,2,1])
    with col_b:
        user_input = st.text_input("Username")
        pwd_input = st.text_input("Password", type="password")
        if st.button("ACCESSO AL LABORATORIO", use_container_width=True):
            # Database utenti simulato (per indipendenza e sicurezza)
            valid_users = {"atleta_pro": "supernova26", "admin": "dataovertalent"}
            
            if user_input in valid_users and valid_users[user_input] == pwd_input:
                st.session_state["authenticated"] = True
                st.session_state["username"] = user_input
                st.rerun()
            else:
                st.error("Credenziali errate. Accesso negato.")
    st.stop()

# =====================================================================
# 1. DATABASE MATERIALI INGEGNERISTICI (EXPANDED)
# =====================================================================
# Struttura: UTS (MPa), Yield (MPa), Limite Fatica Base (MPa), Categoria
materials_db = {
    # COMPOSITI AVANZATI
    "Fibra Carbonio UD (Alta Modulo)": {"uts": 1800, "yield": 1800, "se_base": 1050, "cat": "Compositi"},
    "Fibra Carbonio Woven 3K (Tessuto)": {"uts": 900, "yield": 850, "se_base": 550, "cat": "Compositi"},
    "Kevlar 49 / Epossidica": {"uts": 1400, "yield": 1300, "se_base": 800, "cat": "Compositi"},
    "Vetroresina S-Glass UD": {"uts": 1200, "yield": 1150, "se_base": 600, "cat": "Compositi"},
    
    # TITANIO (Pilastri protesici)
    "Titanio Ti-6Al-4V (Grado 5)": {"uts": 950, "yield": 880, "se_base": 510, "cat": "Metalli"},
    "Titanio Grado 2 (Puro Commerciale)": {"uts": 345, "yield": 275, "se_base": 170, "cat": "Metalli"},
    "Titanio Ti-6Al-4V ELI (Grado 23)": {"uts": 860, "yield": 795, "se_base": 440, "cat": "Metalli"},
    
    # ACCIAI (Giunti e viteria)
    "Acciaio 4340 (Bonificato)": {"uts": 1100, "yield": 950, "se_base": 550, "cat": "Metalli"},
    "Acciaio Maraging 250": {"uts": 1750, "yield": 1700, "se_base": 850, "cat": "Metalli"},
    "Acciaio Inox 316L (Biomedicale)": {"uts": 485, "yield": 170, "se_base": 290, "cat": "Metalli"},
    "Acciaio Inox 17-4 PH": {"uts": 1070, "yield": 1000, "se_base": 535, "cat": "Metalli"},
    
    # ALLUMINI (Connettori leggeri)
    "Alluminio 7075-T6 (Ergal)": {"uts": 572, "yield": 503, "se_base": 159, "cat": "Metalli"},
    "Alluminio 2024-T3 (Avio)": {"uts": 483, "yield": 345, "se_base": 138, "cat": "Metalli"},
    "Alluminio 6061-T6": {"uts": 310, "yield": 276, "se_base": 96, "cat": "Metalli"},
    
    # POLIMERI TECNICI (Socket / Cuscinetti)
    "PEEK (Polietereterchetone)": {"uts": 100, "yield": 100, "se_base": 45, "cat": "Polimeri"},
    "POM (Delrin / Acetalica)": {"uts": 70, "yield": 65, "se_base": 30, "cat": "Polimeri"},
    "Nylon 6/6 (Caricato Vetro 30%)": {"uts": 130, "yield": 120, "se_base": 50, "cat": "Polimeri"}
}

# =====================================================================
# SIDEBAR COMUNE (SETUP ATLETA E MATERIALE)
# =====================================================================
with st.sidebar:
    st.markdown(f"<h2 style='color:{GOLD} !important;'>SETUP ATLETA</h2>", unsafe_allow_html=True)
    sport = st.text_input("Sport Praticato", "Es. Sprint 100m, Salto in Lungo")
    peso_atleta = st.number_input("Peso Atleta (kg)", value=75.0, step=0.5)
    
    st.markdown(f"<h2 style='color:{GOLD} !important;'>CONFIG. COMPONENTE</h2>", unsafe_allow_html=True)
    mat_name = st.selectbox("Lega / Composito", list(materials_db.keys()))
    mat = materials_db[mat_name]
    
    surf = st.selectbox("Finitura Superficiale", ["Lucidato (Specchio)", "Lavorato a Macchina", "Grezzo da Fusione/Stampo", "Forgiato / Laminato Grezzo"])
    
    load = st.selectbox("Condizione di Carico Multiassiale", [
        "Flessione Pura (es. Lama in corsa)", 
        "Assiale (Trazione/Compressione pura)", 
        "Torsione Pura (Rotazione ginocchio)", 
        "Carico Combinato Flesso-Torsionale"
    ])
    
    # Affidabilità fissa al 99.9% come richiesto.
    rel_type = "99.9%"
    ke_fixed = 0.753 

# =====================================================================
# MOTORE FISICO BASE (WÖHLER & MARIN)
# =====================================================================
def calculate_fatigue_base(s_max, s_min, mat_data, surf_type, load_type):
    uts = mat_data['uts']
    mat_cat = mat_data['cat']
    se_base = mat_data['se_base']
    
    # Superficie (ka)
    if mat_cat in ["Compositi", "Polimeri"]: 
        ka = 0.95 # Compositi meno sensibili alla finitura esterna rispetto ai metalli
    else:
        surfs = {"Lucidato (Specchio)": (1.58, -0.085), "Lavorato a Macchina": (4.51, -0.265), 
                 "Grezzo da Fusione/Stampo": (57.7, -0.718), "Forgiato / Laminato Grezzo": (272.0, -0.995)}
        a, b = surfs[surf_type]
        ka = min(a * (uts ** b), 1.0)
    
    # Carico (kc)
    loads = {"Flessione Pura (es. Lama in corsa)": 1.0, 
             "Assiale (Trazione/Compressione pura)": 0.85, 
             "Torsione Pura (Rotazione ginocchio)": 0.59, 
             "Carico Combinato Flesso-Torsionale": 0.75}
    kc = loads[load_type]
    
    # Limite di fatica corretto
    se_corr = se_base * ka * kc * ke_fixed
    
    # Stress di Goodman
    sigma_a = (s_max - s_min) / 2
    sigma_m = (s_max + s_min) / 2
    
    if sigma_m >= uts:
        s_eq = 999999 # Cedimento statico istantaneo
    else:
        s_eq = sigma_a / (1 - (sigma_m / uts))
        
    # Calcolo Cicli (Basquin)
    if s_eq <= se_corr:
        Nf_val = float('inf')
        N_end_plot = 1e8
        log_a, b = 0, 0
    elif s_max >= uts:
        Nf_val = 1
        N_end_plot = 10
        log_a, b = 0, 0
    else:
        f = 0.9
        S1000 = f * uts
        N_end_plot = 1e6 if mat_cat not in ["Alluminio", "Polimeri"] else 5e8
        b = -(math.log10(S1000/se_corr)) / (math.log10(N_end_plot)-3)
        log_a = math.log10(S1000) - 3*b
        Nf_val = 10 ** ((math.log10(s_eq) - log_a)/b)
        
    return s_eq, se_corr, Nf_val, log_a, b, N_end_plot

# =====================================================================
# PDF ENGINE (BASE CLASS CLONE)
# =====================================================================
class SupernovaPDF(FPDF):
    def header(self):
        self.set_fill_color(0, 0, 0) # Sfondo nero testata
        self.rect(0, 0, 210, 30, 'F')
        self.set_font('Arial', 'B', 16)
        # Colore Oro (D4AF37 = 212, 175, 55)
        self.set_text_color(212, 175, 55) 
        self.cell(0, 15, 'SUPERNOVA LAB', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.set_text_color(255, 255, 255)
        self.cell(0, 5, 'DATA OVER TALENT.', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, f'User: {st.session_state["username"]} | Proprietary & Confidential', 0, 0, 'L')
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'R')
        
    def section_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(212, 175, 55) # Oro
        self.set_text_color(0, 0, 0) # Nero
        self.cell(0, 8, f"  {title.upper()}", 0, 1, 'L', 1)
        self.ln(2)

    def data_row(self, col1, col2, col3, is_header=False):
        if is_header:
            self.set_font('Arial', 'B', 10)
            self.set_fill_color(230, 230, 230)
            fill = True
        else:
            self.set_font('Arial', '', 10)
            fill = False
        self.set_text_color(0, 0, 0)
        
        w = [90, 60, 40] 
        self.cell(w[0], 7, str(col1), 1, 0, 'L', fill)
        self.cell(w[1], 7, str(col2), 1, 0, 'L', fill)
        self.cell(w[2], 7, str(col3), 1, 0, 'C', fill)
        self.ln()

# =====================================================================
# MOTORE GRAFICO SEABORN (PER PDF - TEMA SCURO/ORO)
# =====================================================================
def create_sns_wohler_chart(n_x, s_y, se_corr, Nf_val, s_eq, mat_name):
    # Stile coerente con UI
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 5))
    
    ax.plot(n_x, s_y, color=GOLD, linewidth=2.5, label="Curva Materiale (S-N)")
    ax.set_xscale("log")
    
    # Linea limite fatica
    ax.axhline(se_corr, color='white', linestyle='--', linewidth=1.2, label=f"Limite Affidabilità 99.9% ({int(se_corr)} MPa)")
    
    # Punto operativo
    if Nf_val != float('inf') and Nf_val > 0:
        ax.scatter([Nf_val], [s_eq], color='red', zorder=5, s=150, label="Punto di Rottura")
        
    ax.set_xlabel("Cicli a Rottura (N)", fontsize=11, fontweight='bold', color='white')
    ax.set_ylabel("Stress Eq. Goodman (MPa)", fontsize=11, fontweight='bold', color='white')
    ax.set_title(f"Mappa Strutturale: {mat_name}", fontsize=14, fontweight='bold', color=GOLD)
    
    ax.legend(facecolor=DARK_GREY, edgecolor=GOLD, labelcolor='white')
    ax.grid(color='#333333', linestyle='-', linewidth=0.5)
    
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(tmp_file.name, format="png", bbox_inches="tight", dpi=300)
    plt.close()
    return tmp_file.name

# =====================================================================
# UI LAYOUT: TABS
# =====================================================================
st.title("SUPERNOVA DATA LAB")
tab1, tab2 = st.tabs(["[ 1 ] FATIGUE SIMULATOR (LIFECYCLE)", "[ 2 ] RACE DAMAGE SIMULATOR (PERFORMANCE)"])

# ---------------------------------------------------------------------
# TAB 1: FATIGUE SIMULATOR (Original Logic + Upgrades)
# ---------------------------------------------------------------------
with tab1:
    st.markdown(f"<h3 style='color:{GOLD} !important;'>PARAMETRI DI CARICO MACROSCopico</h3>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    s_max_f = c1.number_input("Stress Massimo (MPa) - Tab 1", value=450, key="smax1")
    s_min_f = c2.number_input("Stress Minimo (MPa) - Tab 1", value=50, key="smin1")
    cycles_yr = c3.number_input("Cicli Previsti / Anno", value=150000, step=10000)
    
    # Calcolo
    s_eq_f, se_corr_f, Nf_f, log_a_f, b_f, N_end_f = calculate_fatigue_base(s_max_f, s_min_f, mat, surf, load)
    
    if Nf_f == float('inf'):
        anni_f = "Vita Infinita"
        nf_display = "∞"
    else:
        anni_f = round(Nf_f / cycles_yr, 2)
        nf_display = f"{int(Nf_f):,}"
        
    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Stress Equivalente", f"{int(s_eq_f)} MPa")
    m2.metric("Limite Fatica (99.9%)", f"{int(se_corr_f)} MPa")
    m3.metric("Stima Vita Componente", f"{anni_f} Anni" if isinstance(anni_f, float) else anni_f)
    
    # Plotly Chart Tab 1
    n_x_f = np.logspace(3, math.log10(N_end_f), 100)
    if Nf_f != float('inf') and b_f != 0:
        s_y_f = (10**log_a_f) * (n_x_f**b_f)
    else:
        s_y_f = np.full_like(n_x_f, se_corr_f)
    s_y_f = np.maximum(s_y_f, se_corr_f)
    
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=n_x_f, y=s_y_f, mode='lines', line=dict(color=GOLD, width=3), name="S-N Curve"))
    if Nf_f != float('inf'):
        fig1.add_trace(go.Scatter(x=[Nf_f], y=[s_eq_f], mode='markers', marker=dict(color='white', size=12, line=dict(color='red', width=2)), name="Punto Rottura"))
    
    fig1.update_layout(
        plot_bgcolor=BLACK, paper_bgcolor=BLACK,
        font=dict(color=WHITE),
        xaxis=dict(type="log", title="Cicli N", gridcolor=DARK_GREY),
        yaxis=dict(title="Stress MPa", gridcolor=DARK_GREY),
        title=dict(text="LIFECYCLE WÖHLER CURVE", font=dict(color=GOLD))
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    # Generazione PDF TAB 1
    if st.button("GENERA REPORT LIFECYCLE (PDF)", key="btn_pdf1"):
        pdf1 = SupernovaPDF()
        pdf1.add_page()
        pdf1.section_title("1. Specifica Componente e Atleta")
        pdf1.data_row("Parametro", "Valore", "Unità", True)
        pdf1.data_row("Atleta / Sport", f"{st.session_state['username']} / {sport}", "-")
        pdf1.data_row("Materiale Base", mat_name, "-")
        pdf1.data_row("Carico Rottura (UTS) / Snervamento", f"{mat['uts']} / {mat['yield']}", "MPa")
        pdf1.ln(5)
        
        pdf1.section_title("2. Analisi Dinamica e Vita Utile")
        pdf1.data_row("Parametro", "Valore", "Unità", True)
        pdf1.data_row("Stress Applicato (Max/Min)", f"{s_max_f} / {s_min_f}", "MPa")
        pdf1.data_row("Stress Equivalente (Goodman)", f"{int(s_eq_f)}", "MPa")
        pdf1.data_row("Limite Fatica Operativo (R=99.9%)", f"{int(se_corr_f)}", "MPa")
        pdf1.data_row("Cicli a Rottura Stimati", nf_display, "Cicli")
        pdf1.data_row("Vita Utile", str(anni_f), "Anni")
        pdf1.ln(5)
        
        pdf1.section_title("3. Mappa di Decadimento Strutturale")
        img_path = create_sns_wohler_chart(n_x_f, s_y_f, se_corr_f, Nf_f, s_eq_f, mat_name)
        pdf1.image(img_path, x=10, w=190)
        os.remove(img_path)
        
        pdf_bytes1 = pdf1.output(dest='S').encode('latin-1')
        st.download_button("SCARICA PDF LIFECYCLE", data=pdf_bytes1, file_name="Supernova_Lifecycle_Report.pdf", mime="application/pdf")

# ---------------------------------------------------------------------
# TAB 2: RACE DAMAGE SIMULATOR (Miner's Rule)
# ---------------------------------------------------------------------
with tab2:
    st.markdown(f"<h3 style='color:{GOLD} !important;'>PARAMETRI DI GARA / SFORZO</h3>", unsafe_allow_html=True)
    st.info("Simula lo sforzo di una specifica gara per determinare il danno cumulativo alla protesi e il degrado prestazionale.")
    
    col_r1, col_r2, col_r3 = st.columns(3)
    gara_min = col_r1.number_input("Durata Sforzo (Minuti)", value=120, min_value=1)
    freq_bpm = col_r2.number_input("Frequenza Impatti (Cicli/Minuto)", value=85, help="Es. Passi al minuto, pedalate, etc.")
    s_max_r = col_r3.number_input("Stress Picco Gara (MPa)", value=600, key="smax2")
    
    s_min_r = st.number_input("Stress Minimo Gara (MPa)", value=0, key="smin2")
    
    # Calcolo Gara
    cicli_gara = gara_min * freq_bpm
    s_eq_r, se_corr_r, Nf_r, _, _, _ = calculate_fatigue_base(s_max_r, s_min_r, mat, surf, load)
    
    # Miner's Rule per il danno
    if Nf_r == float('inf'):
        damage_pct = 0.0
    else:
        damage_pct = (cicli_gara / Nf_r) * 100
        
    # Logica rendimento (Heuristic: il danno microstrutturale riduce la rigidità/restituzione elastica)
    if damage_pct >= 100:
        status_gara = "FALLIMENTO STRUTTURALE DURANTE LA GARA"
        color_status = "red"
        perf_drop = 100.0
    else:
        status_gara = "PROTESI INTATTA"
        color_status = GOLD
        # Calcolo calo performance (esponenziale leggero sul danno)
        perf_drop = min((damage_pct ** 1.1), 100.0)
        
    st.markdown("---")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Cicli Totali Gara", f"{int(cicli_gara):,}")
    r2.metric("Max Tolleranza (Cicli)", f"{int(Nf_r):,}" if Nf_r != float('inf') else "∞")
    r3.metric("Danno Strutturale", f"{damage_pct:.4f} %")
    r4.metric("Calo Performance (Rigidità)", f"-{perf_drop:.2f} %")
    
    st.markdown(f"<h2 style='text-align:center; color:{color_status} !important;'>{status_gara}</h2>", unsafe_allow_html=True)
    
    # Plotly Chart Tab 2 (Damage Accumulation)
    time_arr = np.linspace(0, gara_min, 100)
    damage_arr = ( (time_arr * freq_bpm) / Nf_r ) * 100 if Nf_r != float('inf') else np.zeros_like(time_arr)
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=time_arr, y=damage_arr, fill='tozeroy', mode='lines', line=dict(color=color_status, width=3), name="Accumulo Danno"))
    fig2.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Soglia Rottura (100%)")
    
    fig2.update_layout(
        plot_bgcolor=BLACK, paper_bgcolor=BLACK,
        font=dict(color=WHITE),
        xaxis=dict(title="Tempo Gara (Minuti)", gridcolor=DARK_GREY),
        yaxis=dict(title="Danno Cumulativo (%)", gridcolor=DARK_GREY, range=[0, max(110, max(damage_arr)*1.1)]),
        title=dict(text="RACE DAMAGE ACCUMULATION (MINER'S RULE)", font=dict(color=GOLD))
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    # Generazione PDF TAB 2
    if st.button("GENERA REPORT GARA (PDF)", key="btn_pdf2"):
        pdf2 = SupernovaPDF()
        pdf2.add_page()
        pdf2.section_title("1. Specifica Gara e Setup Atleta")
        pdf2.data_row("Parametro", "Valore", "Unità", True)
        pdf2.data_row("Atleta / Sport", f"{st.session_state['username']} / {sport}", "-")
        pdf2.data_row("Materiale Setup", mat_name, "-")
        pdf2.data_row("Durata Sforzo", str(gara_min), "Minuti")
        pdf2.data_row("Frequenza Ciclica", str(freq_bpm), "Cicli/Min")
        pdf2.ln(5)
        
        pdf2.section_title("2. Analisi Danno Cumulativo (Regola di Miner)")
        pdf2.data_row("Parametro", "Valore", "Unità", True)
        pdf2.data_row("Stress Massimo Registrato", str(s_max_r), "MPa")
        pdf2.data_row("Cicli Totali in Gara", str(cicli_gara), "Cicli")
        pdf2.data_row("Limite Cicli a Rottura", str(int(Nf_r)) if Nf_r != float('inf') else "Infinito", "Cicli")
        pdf2.data_row("Danno Strutturale Subito", f"{damage_pct:.4f}", "%")
        pdf2.data_row("Degrado Prestazionale Stimato", f"{perf_drop:.2f}", "%")
        pdf2.ln(10)
        
        # Conclusione testuale stampata grande sul PDF
        pdf2.set_font('Arial', 'B', 14)
        if damage_pct >= 100:
            pdf2.set_text_color(200, 0, 0) # Rosso per rottura
            pdf2.cell(0, 10, "ATTENZIONE: FALLIMENTO STRUTTURALE PREVISTO DURANTE LO SFORZO.", 0, 1, 'C')
        else:
            pdf2.set_text_color(212, 175, 55) # Oro per successo
            pdf2.cell(0, 10, "ESITO: COMPONENTE SICURO PER L'INTERA DURATA DELLA GARA.", 0, 1, 'C')
            
        pdf_bytes2 = pdf2.output(dest='S').encode('latin-1')
        st.download_button("SCARICA PDF RACE SIMULATION", data=pdf_bytes2, file_name="Supernova_Race_Report.pdf", mime="application/pdf")

