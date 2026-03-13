# --- CONFIGURAZIONE PAGINA E LIBRERIE ---
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

# COLORI BRAND SUPERNOVA
GOLD_SN = "#D4AF37" 
BG_DARK = "#0B1D22"

st.set_page_config(page_title="Supernova Fatigue Lab", page_icon="🚀", layout="wide")

st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .stDeployButton {{display:none;}}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# SPLASH SCREEN E LOGIN (Codice Originale Intatto)
# ==========================================
if 'splash_done' not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        try:
            st.image("logo.png", use_container_width=True)
        except:
            st.markdown(f"<h1 style='text-align:center; color:{GOLD_SN};'>SUPERNOVA</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;'>Advanced Paralympic Prosthetics Lab</p>", unsafe_allow_html=True)
    time.sleep(3) 
    placeholder.empty()
    st.session_state['splash_done'] = True

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<h3 style='text-align:center;'>🔒 Accesso Riservato Lab</h3>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1,2,1])
    with col_b:
        pwd = st.text_input("Inserisci la Password", type="password")
        if st.button("ENTRA NEL LAB", use_container_width=True):
            if pwd == "supernova26":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Password errata.")
    st.stop()

# ==========================================
# 1. DATABASE MATERIALI (Codice Originale Intatto)
# ==========================================
materials_db = {
    "Titanio Ti-6Al-4V (Piloni/Giunti)": {"uts": 950, "yield": 880, "se_base": 510, "cat": "Metalli"},
    "Titanio Grado 5 ELI (Impianti)": {"uts": 860, "yield": 795, "se_base": 440, "cat": "Metalli"},
    "Fibra Carbonio UD (Lame Corsa)": {"uts": 1500, "yield": 1500, "se_base": 900, "cat": "Compositi"},
    "Kevlar/Epoxy (Socket Strutturale)": {"uts": 1300, "yield": 1200, "se_base": 750, "cat": "Compositi"},
    "Alluminio 7075-T6 (Ergal - Raccordi)": {"uts": 572, "yield": 503, "se_base": 159, "cat": "Metalli"},
    "PEEK (Componenti Flessibili/Socket)": {"uts": 100, "yield": 100, "se_base": 45, "cat": "Polimeri"},
    "Acciaio Inox 316L (Viteria/Giunti)": {"uts": 485, "yield": 170, "se_base": 290, "cat": "Metalli"}
}

# ==========================================
# 2. INPUT USER (SIDEBAR) - Aggiunti Temp e Umidità
# ==========================================
with st.sidebar:
    st.header("🏃 Dati Atleta e Setup")
    atleta_nome = st.text_input("Nome Atleta", "Atleta Paralimpico")
    atleta_peso = st.number_input("Peso Atleta (kg)", value=75)
    sport_target = st.text_input("Sport / Obiettivo", "Golf - Olimpiadi 2040")

    st.header("⚙️ Parametri Ambientali")
    temp_esercizio = st.slider("Temperatura Operativa (°C)", -20, 100, 25)
    umidita_relativa = st.slider("Umidità Relativa (%)", 0, 100, 0)
    
    st.header("📉 Fattori Marin")
    surf = st.selectbox("Finitura Superficiale", ["Lucidato", "Lavorato", "Grezzo", "Forgiato"])
    load = st.selectbox("Tipo Carico", ["Flessione (Impatto Corsa)", "Assiale (Carico Statico)", "Torsione (Cambio Direzione)"])
    rel = st.selectbox("Affidabilità Richiesta", ["50%", "90%", "99%", "99.99%"])
    
    st.header("⚖️ Spettro di Carico")
    s_max = st.number_input("Stress Max (MPa)", value=400)
    s_min = st.number_input("Stress Min (MPa)", value=0)
    cycles_yr = st.number_input("Cicli Previsti / Anno", value=100000, step=10000)

# ==========================================
# 3. MOTORE FISICO (CALCOLI) - Integrazione k_d e k_w
# ==========================================
def get_k_factors(uts, surf_type, load_type, rel_type, mat_cat, temp, hum):
    # ka, kc, ke (Invariati)
    surfs = {"Lucidato": (1.58, -0.085), "Lavorato": (4.51, -0.265), "Grezzo": (57.7, -0.718), "Forgiato": (272.0, -0.995)}
    ka = 0.9 if mat_cat in ["Compositi", "Polimeri"] else min(surfs[surf_type][0] * (uts ** surfs[surf_type][1]), 1.0)
    
    loads = {"Flessione (Impatto Corsa)": 1.0, "Assiale (Carico Statico)": 0.85, "Torsione (Cambio Direzione)": 0.59}
    kc = loads.get(load_type, 1.0)
    
    rels = {"50%": 1.0, "90%": 0.897, "99%": 0.814, "99.99%": 0.702}
    ke = rels.get(rel_type, 1.0)
    
    # Fattore Temperatura (kd)
    if mat_cat == "Polimeri": kd = 1.0 if temp <= 25 else max(0.2, 1.0 - 0.015 * (temp - 25))
    elif mat_cat == "Compositi": kd = 1.0 if temp <= 30 else max(0.5, 1.0 - 0.008 * (temp - 30))
    else: kd = 1.0 if temp <= 450 else 1.0 - 0.0008 * (temp - 450)

    # Fattore Umidità (kw) - Critico per Kevlar e Nylon
    if mat_cat in ["Compositi", "Polimeri"] and hum > 0:
        kw = 1.0 - (0.002 * hum) # Degradazione max 20% in condizioni di saturazione
    else: kw = 1.0
        
    return ka, kc, ke, kd, kw

ka, kc, ke, kd, kw = get_k_factors(mat['uts'], surf, load, rel, mat['cat'], temp_esercizio, umidita_relativa)
se_corr = mat['se_base'] * ka * kc * ke * kd * kw

# Stress Goodman e Basquin (Invariati)
sigma_a = (s_max - s_min) / 2
sigma_m = (s_max + s_min) / 2
s_eq = sigma_a / (1 - (sigma_m / mat['uts'])) if sigma_m < mat['uts'] else 9999

if s_eq <= se_corr: Nf, years = "Infinito", "Infinito"
elif s_max >= mat['uts']: Nf, years = 0, 0
else:
    f = 0.9
    S1000 = f * mat['uts']
    N_end = 1e6 if mat['cat'] not in ["Alluminio", "Polimeri"] else 5e8
    b = -(math.log10(S1000/se_corr)) / (math.log10(N_end)-3)
    log_a = math.log10(S1000) - 3*b
    Nf_val = 10 ** ((math.log10(s_eq) - log_a)/b)
    Nf, years = int(Nf_val), round(Nf_val / cycles_yr, 2)

n_x = np.logspace(3, 8, 50)
s_y = (10**log_a) * (n_x**b) if isinstance(Nf, int) and Nf > 0 else np.zeros_like(n_x)
s_y = np.maximum(s_y, se_corr)

# ==========================================
# 4. VISUALIZZAZIONE UI (Colore OroSN)
# ==========================================
st.title("🦾 Analisi Strutturale Protesi")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Stress Eq. (Goodman)", f"{int(s_eq)} MPa")
c2.metric("Limite Fatica Corretto", f"{int(se_corr)} MPa")
c3.metric("Fattore Amb. (kd*kw)", f"{kd*kw:.2f}")
c4.metric("Vita Utile Stimata", f"{years} anni" if isinstance(years, (int, float)) else years)

fig = go.Figure()
fig.add_trace(go.Scatter(x=n_x, y=s_y, name="Curva Wöhler S-N", line=dict(color=GOLD_SN, width=3)))
if isinstance(Nf, int) and Nf > 0:
    fig.add_trace(go.Scatter(x=[Nf], y=[s_eq], mode='markers', marker=dict(color='#FF4B4B', size=12), name="Rottura"))
fig.update_layout(xaxis_type="log", title="Curva di Fatica (Wöhler) - Supernova Oro", height=400)
st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 5. GENERATORE PDF (Aggiornato con Oro e Parametri)
# ==========================================
def create_seaborn_temp_image():
    plt.figure(figsize=(10, 5))
    sns.set_theme(style="whitegrid")
    ax = sns.lineplot(x=n_x, y=s_y, color=GOLD_SN, linewidth=2.5)
    ax.set_xscale("log")
    plt.axhline(se_corr, color='green', linestyle='--')
    if isinstance(Nf, int) and Nf > 0:
        plt.scatter([Nf], [s_eq], color="#FF4B4B", zorder=5, s=150)
    plt.title(f"Analisi S-N: {mat_name}", fontsize=14, fontweight='bold')
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(tmp_file.name, format="png", bbox_inches="tight", dpi=300)
    plt.close()
    return tmp_file.name

class TablePDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_text_color(212, 175, 55) # ORO RGB
        self.cell(0, 10, 'SUPERNOVA LAB - PROSTHETICS FATIGUE REPORT', 0, 1, 'C')
        self.ln(5)

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 8, title, 0, 1, 'L', 1)
        self.ln(2)

    def add_table_row(self, col1, col2, col3):
        self.set_font('Arial', '', 10)
        self.cell(85, 7, str(col1), 1)
        self.cell(55, 7, str(col2), 1)
        self.cell(50, 7, str(col3), 1, 1, 'C')

def generate_full_pdf():
    pdf = TablePDF()
    pdf.add_page()
    pdf.chapter_title("1. Condizioni Operative")
    pdf.add_table_row("Materiale", mat_name, mat['cat'])
    pdf.add_table_row("Temperatura", f"{temp_esercizio} C", f"kd={kd:.2f}")
    pdf.add_table_row("Umidita Relativa", f"{umidita_relativa} %", f"kw={kw:.2f}")
    pdf.ln(5)
    
    pdf.chapter_title("2. Risultati Analisi")
    pdf.add_table_row("Limite Fatica Se", f"{int(se_corr)} MPa", "Corretto")
    pdf.add_table_row("Stress Massimo", f"{s_max} MPa", "Input")
    pdf.add_table_row("Vita Stimata", f"{years} Anni", "Output")
    
    img_path = create_seaborn_temp_image()
    pdf.image(img_path, x=10, w=190)
    os.remove(img_path)
    return pdf.output(dest='S').encode('latin-1')

st.markdown("---")
if st.button("📄 Genera & Scarica Report Oro"):
    try:
        pdf_bytes = generate_full_pdf()
        st.download_button(label="Download Report PDF", data=pdf_bytes, file_name=f"Supernova_Report_{atleta_nome}.pdf", mime="application/pdf")
        st.success("Report generato!")
    except Exception as e:
        st.error(f"Errore Generazione PDF: {e}")
