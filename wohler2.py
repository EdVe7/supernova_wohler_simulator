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

# --- MODIFICA: Nascosta la barra degli strumenti (GitHub) in alto a dx ---
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .stDeployButton {{display:none;}}
    [data-testid="stToolbar"] {{visibility: hidden !important;}}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# SPLASH SCREEN E LOGIN 
# ==========================================
if 'splash_done' not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        try:
            st.image("logo.png", use_container_width=True)
        except:
            st.markdown(f"<h1 style='text-align:center; color:{GOLD_SN};'>SUPERNOVA</h1>", unsafe_allow_html=True)
        # --- MODIFICA: Scritta modificata in "DATA OVER TALENT" in maiuscolo e più grande ---
        st.markdown("<h2 style='text-align:center; font-weight: 900; font-size: 2.5em; letter-spacing: 2px;'>DATA OVER TALENT</h2>", unsafe_allow_html=True)
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
# 1. DATABASE MATERIALI 
# ==========================================
# --- MODIFICA: Database espanso a 12 materiali ---
materials_db = {
    "Titanio Ti-6Al-4V (Piloni/Giunti)": {"uts": 950, "yield": 880, "se_base": 510, "cat": "Metalli"},
    "Titanio Grado 5 ELI (Impianti)": {"uts": 860, "yield": 795, "se_base": 440, "cat": "Metalli"},
    "Titanio Trabecolare DMLS (Retico)": {"uts": 750, "yield": 680, "se_base": 300, "cat": "Metalli"},
    "Nitinol (Lega Memoria di Forma)": {"uts": 1000, "yield": 400, "se_base": 350, "cat": "Metalli"},
    "Fibra Carbonio UD (Lame Corsa)": {"uts": 1500, "yield": 1500, "se_base": 900, "cat": "Compositi"},
    "Matrice Epossidica al Grafene": {"uts": 1700, "yield": 1650, "se_base": 1100, "cat": "Compositi"},
    "Fibra di Vetro S-Glass/Epoxy": {"uts": 1100, "yield": 1000, "se_base": 400, "cat": "Compositi"},
    "Kevlar/Epoxy (Socket Strutturale)": {"uts": 1300, "yield": 1200, "se_base": 750, "cat": "Compositi"},
    "Alluminio 7075-T6 (Ergal - Raccordi)": {"uts": 572, "yield": 503, "se_base": 159, "cat": "Metalli"},
    "PEEK (Componenti Flessibili/Socket)": {"uts": 100, "yield": 100, "se_base": 45, "cat": "Polimeri"},
    "UHMWPE (Polietilene Alta Densità)": {"uts": 40, "yield": 25, "se_base": 15, "cat": "Polimeri"},
    "Acciaio Inox 316L (Viteria/Giunti)": {"uts": 485, "yield": 170, "se_base": 290, "cat": "Metalli"}
}

# ==========================================
# 2. INPUT USER (SIDEBAR)
# ==========================================
with st.sidebar:
    st.header("🏃 Dati Atleta e Setup")
    atleta_nome = st.text_input("Nome Atleta", "Atleta Paralimpico")
    atleta_peso = st.number_input("Peso Atleta (kg)", value=75)
    sport_target = st.text_input("Sport / Obiettivo", "Golf - Olimpiadi 2040")

    st.header("⚙️ Parametri Ambientali")
    mat_name = st.selectbox("Seleziona Materiale Principale", list(materials_db.keys()))
    
    mat = materials_db[mat_name] 

    temp_esercizio = st.slider("Temperatura Operativa (°C)", -20, 50, 25)
    umidita_relativa = st.slider("Umidità Relativa (%)", 0, 100, 0)
    
    # --- NUOVO INSERIMENTO: Microclima Socket (Implementazione 4) ---
    st.header("🌡️ Microclima Socket")
    usa_microclima = st.checkbox("Accumulo Calore (Cicli Continui)")
    ore_continue = st.slider("Ore Sessione Continuous", 1, 10, 4) if usa_microclima else 0

    st.header("📉 Fattori Marin")
    surf = st.selectbox("Finitura Superficiale", ["Lucidato", "Lavorato", "Grezzo", "Forgiato"])
    
    # --- NUOVO INSERIMENTO: Golf Swing Multi-assiale (Implementazione 1) ---
    load = st.selectbox("Tipo Carico", ["Flessione (Impatto Corsa)", "Assiale (Carico Statico)", "Torsione (Cambio Direzione)", "Golf Swing (Multi-assiale)"])
    rel = st.selectbox("Affidabilità Richiesta", ["50%", "90%", "99%", "99.99%"])
    
    st.header("📐 Geometria (Intaglio)")
    forma_intaglio = st.selectbox("Geometria Sezione Critica", ["Superficie Liscia (Kf=1.0)", "Raccordo Ampio (Kf=1.2)", "Foro Passante (Kf=1.8)", "Spigolo Vivo (Kf=2.5)"])
    kf_dict = {"Superficie Liscia (Kf=1.0)": 1.0, "Raccordo Ampio (Kf=1.2)": 1.2, "Foro Passante (Kf=1.8)": 1.8, "Spigolo Vivo (Kf=2.5)": 2.5}
    kf = kf_dict[forma_intaglio]

    st.header("⚖️ Spettro di Carico Primario")
    
    # --- NUOVO INSERIMENTO: Logica Von Mises per Golf Swing ---
    if load == "Golf Swing (Multi-assiale)":
        sigma_ass = st.number_input("Stress Assiale (MPa)", value=200)
        tau_tors = st.number_input("Stress Taglio/Torsione (MPa)", value=150)
        s_max_eq = math.sqrt(sigma_ass**2 + 3 * (tau_tors**2))
        st.info(f"Equivalente Von Mises: {s_max_eq:.1f} MPa")
        s_max = st.number_input("Stress Max Eq. (MPa)", value=float(s_max_eq))
    else:
        s_max = st.number_input("Stress Max (MPa)", value=400)
        
    s_min = st.number_input("Stress Min (MPa)", value=1, min_value=1)
    cycles_yr = st.number_input("Cicli Previsti / Anno", value=100000, step=10000)

    st.header("💥 Carico Secondario (Miner)")
    usa_miner = st.checkbox("Aggiungi Impatti Rari / Picchi")
    if usa_miner:
        s_max_2 = st.number_input("Stress Max Sec. (MPa)", value=600)
        s_min_2 = st.number_input("Stress Min Sec. (MPa)", value=1, min_value=1)
        cycles_yr_2 = st.number_input("Cicli Sec. / Anno", value=1000, step=100)
    else:
        s_max_2, s_min_2, cycles_yr_2 = 0, 0, 0

    st.header("🔄 Confronto (A/B Test)")
    mat_comp_name = st.selectbox("Seleziona Materiale B (Opzionale)", ["Nessuno"] + list(materials_db.keys()))


# ==========================================
# 3. MOTORE FISICO (CALCOLI) 
# ==========================================
def get_k_factors(uts, surf_type, load_type, rel_type, mat_cat, temp, hum):
    surfs = {"Lucidato": (1.58, -0.085), "Lavorato": (4.51, -0.265), "Grezzo": (57.7, -0.718), "Forgiato": (272.0, -0.995)}
    ka = 0.9 if mat_cat in ["Compositi", "Polimeri"] else min(surfs[surf_type][0] * (uts ** surfs[surf_type][1]), 1.0)
    
    # --- MODIFICA: Aggiunto Golf Swing nei K factors ---
    loads = {"Flessione (Impatto Corsa)": 1.0, "Assiale (Carico Statico)": 0.85, "Torsione (Cambio Direzione)": 0.59, "Golf Swing (Multi-assiale)": 0.70}
    kc = loads.get(load_type, 1.0)
    
    rels = {"50%": 1.0, "90%": 0.897, "99%": 0.814, "99.99%": 0.702}
    ke = rels.get(rel_type, 1.0)
    
    if mat_cat == "Polimeri": kd = 1.0 if temp <= 25 else max(0.2, 1.0 - 0.015 * (temp - 25))
    elif mat_cat == "Compositi": kd = 1.0 if temp <= 30 else max(0.5, 1.0 - 0.008 * (temp - 30))
    else: kd = 1.0 if temp <= 450 else 1.0 - 0.0008 * (temp - 450)

    if mat_cat in ["Compositi", "Polimeri"] and hum > 0:
        kw = 1.0 - (0.002 * hum) 
    else: kw = 1.0
        
    return ka, kc, ke, kd, kw

ka, kc, ke, kd, kw = get_k_factors(mat['uts'], surf, load, rel, mat['cat'], temp_esercizio, umidita_relativa)

# --- NUOVO INSERIMENTO: Applicazione Microclima ---
if usa_microclima and mat['cat'] in ["Polimeri", "Compositi"]:
    kd = kd * (1.0 - (0.02 * ore_continue))

se_corr = mat['se_base'] * ka * kc * ke * kd * kw

f = 0.9
S1000 = f * mat['uts']
N_end = 1e6 if mat['cat'] not in ["Alluminio", "Polimeri"] else 5e8
b = -(math.log10(S1000/se_corr)) / (math.log10(N_end)-3)
log_a = math.log10(S1000) - 3*b

sigma_a = (s_max - s_min) / 2
sigma_m = (s_max + s_min) / 2
s_eq = (sigma_a / (1 - (sigma_m / mat['uts'])) if sigma_m < mat['uts'] else 9999) * kf

# Logica di calcolo Cicli (Nf_val) per il Carico 1
if s_eq <= se_corr: Nf_val = float('inf')
elif s_max >= mat['uts']: Nf_val = 1e-5
else:
    Nf_val = 10 ** ((math.log10(s_eq) - log_a)/b)

if usa_miner:
    sigma_a_2 = (s_max_2 - s_min_2) / 2
    sigma_m_2 = (s_max_2 + s_min_2) / 2
    s_eq_2 = (sigma_a_2 / (1 - (sigma_m_2 / mat['uts'])) if sigma_m_2 < mat['uts'] else 9999) * kf
    
    if s_eq_2 <= se_corr: Nf_val_2 = float('inf')
    elif s_max_2 >= mat['uts']: Nf_val_2 = 1e-5
    else:
        Nf_val_2 = 10 ** ((math.log10(s_eq_2) - log_a)/b)
else:
    Nf_val_2 = float('inf')
    s_eq_2 = 0

danno_1 = cycles_yr / Nf_val if Nf_val > 0 else float('inf')
danno_2 = cycles_yr_2 / Nf_val_2 if Nf_val_2 > 0 else float('inf')
danno_totale = danno_1 + danno_2

if danno_totale >= 1 or s_max >= mat['uts'] or (usa_miner and s_max_2 >= mat['uts']):
    years, Nf = 0, 0
elif danno_totale == 0:
    years, Nf = "Infinito", "Infinito"
else:
    years = round(1 / danno_totale, 2)
    Nf = int(Nf_val) 

if isinstance(years, (int, float)) and years != 0:
    danno_annuo = danno_totale * 100
    perf_decay = min(danno_annuo * 0.5, 100.0)
else:
    perf_decay = 0.0

n_x = np.logspace(3, 8, 50)
s_y = (10**log_a) * (n_x**b) if isinstance(Nf, int) and Nf > 0 else np.zeros_like(n_x)
s_y = np.maximum(s_y, se_corr)

if mat_comp_name != "Nessuno":
    mat2 = materials_db[mat_comp_name]
    ka2, kc2, ke2, kd2, kw2 = get_k_factors(mat2['uts'], surf, load, rel, mat2['cat'], temp_esercizio, umidita_relativa)
    if usa_microclima and mat2['cat'] in ["Polimeri", "Compositi"]:
        kd2 = kd2 * (1.0 - (0.02 * ore_continue))
    se_corr2 = mat2['se_base'] * ka2 * kc2 * ke2 * kd2 * kw2
    
    f2 = 0.9
    S1000_2 = f2 * mat2['uts']
    N_end_2 = 1e6 if mat2['cat'] not in ["Alluminio", "Polimeri"] else 5e8
    b2 = -(math.log10(S1000_2/se_corr2)) / (math.log10(N_end_2)-3)
    log_a2 = math.log10(S1000_2) - 3*b2
    
    s_y_comp = (10**log_a2) * (n_x**b2)
    s_y_comp = np.maximum(s_y_comp, se_corr2)

# ==========================================
# 4. VISUALIZZAZIONE UI (Colore OroSN)
# ==========================================
st.title("🦾 Analisi Strutturale Protesi")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Stress Eq. Principale", f"{int(s_eq)} MPa")
c2.metric("Limite Fatica Corretto", f"{int(se_corr)} MPa")
c3.metric("Fattore Amb. (kd*kw)", f"{kd*kw:.2f}")
c4.metric("Vita Utile Stimata", f"{years} anni" if isinstance(years, (int, float)) else years)

st.markdown("---")
st.metric("Degrado Performance (Perdita Rigidità Stimata a 1 Anno)", f"-{perf_decay:.2f} %" if isinstance(Nf, int) and Nf > 0 else "0.00 %")
st.markdown("---")

fig = go.Figure()
fig.add_trace(go.Scatter(x=n_x, y=s_y, name=f"Curva S-N ({mat_name})", line=dict(color=GOLD_SN, width=3)))

if isinstance(Nf, int) and Nf > 0:
    fig.add_trace(go.Scatter(x=[Nf], y=[s_eq], mode='markers', marker=dict(color='#FF4B4B', size=12), name="Carico Primario"))

if usa_miner and isinstance(Nf_val_2, float) and Nf_val_2 < float('inf'):
    fig.add_trace(go.Scatter(x=[int(Nf_val_2)], y=[s_eq_2], mode='markers', marker=dict(color='#FFA500', size=10, symbol='x'), name="Carico Secondario"))

if mat_comp_name != "Nessuno":
    fig.add_trace(go.Scatter(x=n_x, y=s_y_comp, name=f"Confronto: {mat_comp_name}", line=dict(color="#A0B0C0", width=2, dash='dash')))

fig.update_layout(xaxis_type="log", title="Curva di Fatica (Wöhler) - Supernova Oro", height=400)
st.plotly_chart(fig, use_container_width=True)

# --- NUOVO INSERIMENTO: Sezione Ottimizzazione e Hysteresis (Implementazioni 2 e 3) ---
st.markdown("---")
st.subheader("🛠️ Modulo Avanzato: Topologia & Decadimento Hysteresis")
c_opt1, c_opt2 = st.columns(2)

with c_opt1:
    st.markdown("**1. Ottimizzazione Topologica (Solver Peso/Vita)**")
    target_anni = st.number_input("Vita Agonistica Target (Anni)", value=4.0, min_value=0.5, step=0.5)
    target_cicli = target_anni * (cycles_yr + cycles_yr_2)
    
    if target_cicli >= N_end: s_target = se_corr
    else: s_target = 10 ** (log_a + b * math.log10(target_cicli))
    
    st.info(f"Per garantire {target_anni} anni, lo Stress Equivalente Max non deve superare: **{s_target:.1f} MPa**")
    
    if s_eq < s_target and s_eq > 0:
        st.success(f"📉 Puoi RIDURRE il peso! La sezione è sovradimensionata del {((s_target/s_eq)-1)*100:.1f}% rispetto al target scelto.")
    elif s_eq > s_target:
        st.error(f"⚠️ Rischio Rottura! Aumenta la sezione (aggiungi peso) del {(1-(s_target/s_eq))*100:.1f}% o passa a un materiale superiore.")
        
with c_opt2:
    st.markdown("**2. Hysteresis (Decadimento Rigidità Stimata)**")
    fig_stiff = go.Figure()
    
    # Calcolo di decadimento logaritmico basato su perf_decay limitato
    stiffness = 100 - (perf_decay * (np.log10(n_x) / 6)) 
    stiffness = np.clip(stiffness, 0, 100)
    
    fig_stiff.add_trace(go.Scatter(x=n_x, y=stiffness, fill='tozeroy', name="Modulo Elastico (%)", line=dict(color="#00FF00" if perf_decay < 10 else "#FF4B4B")))
    fig_stiff.update_layout(xaxis_type="log", height=250, margin=dict(l=0,r=0,t=30,b=0), title="Stiffness Retention % (Modulo Elastico)")
    st.plotly_chart(fig_stiff, use_container_width=True)

# ==========================================
# 5. GENERATORE PDF (Aggiornato con Oro e Parametri)
# ==========================================
def create_seaborn_temp_image():
    plt.figure(figsize=(10, 5))
    sns.set_theme(style="whitegrid")
    ax = sns.lineplot(x=n_x, y=s_y, color=GOLD_SN, linewidth=2.5, label=mat_name)
    ax.set_xscale("log")
    plt.axhline(se_corr, color='green', linestyle='--')
    
    if isinstance(Nf, int) and Nf > 0:
        plt.scatter([Nf], [s_eq], color="#FF4B4B", zorder=5, s=150, label="Primario")
        
    if usa_miner and isinstance(Nf_val_2, float) and Nf_val_2 < float('inf'):
        plt.scatter([int(Nf_val_2)], [s_eq_2], color="#FFA500", zorder=5, s=100, marker='X', label="Secondario")

    if mat_comp_name != "Nessuno":
        sns.lineplot(x=n_x, y=s_y_comp, color="#A0B0C0", linewidth=2.0, linestyle="--", label=mat_comp_name)

    plt.title(f"Analisi Strutturale Combinata", fontsize=14, fontweight='bold')
    plt.legend()
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(tmp_file.name, format="png", bbox_inches="tight", dpi=300)
    plt.close()
    return tmp_file.name

class TablePDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_text_color(212, 175, 55) # Colore Oro Supernova
        self.cell(0, 10, 'SUPERNOVA LAB - PROSTHETICS FATIGUE REPORT', 0, 1, 'C')
        self.line(10, 20, 200, 20)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, 'Powered by Supernova Sport Science', 0, 0, 'C')
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'R')
        
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, title, 0, 1, 'L', 1)
        self.ln(2)

    def add_table_row(self, col1, col2, col3, header=False):
        if header:
            self.set_font('Arial', 'B', 10)
        else:
            self.set_font('Arial', '', 10)
        self.cell(85, 7, str(col1), 1)
        self.cell(55, 7, str(col2), 1)
        self.cell(50, 7, str(col3), 1, 0, 'C')
        self.ln()

def generate_full_pdf():
    pdf = TablePDF()
    pdf.add_page()
    
    # --- SEZIONE 0: DATI ATLETA ---
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 6, f"Atleta: {atleta_nome} ({atleta_peso} kg)", 0, 1)
    pdf.cell(0, 6, f"Target Event: {sport_target}", 0, 1)
    pdf.cell(0, 6, f"Data Analisi: {datetime.datetime.now().strftime('%d/%m/%Y')}", 0, 1)
    pdf.ln(5)

    # --- SEZIONE 1: INPUT ---
    pdf.chapter_title("1. Parametri di Configurazione")
    pdf.add_table_row("Parametro", "Valore", "Note", header=True)
    pdf.add_table_row("Materiale Scelto", mat_name, mat['cat'])
    pdf.add_table_row("Carico Rottura Statico (UTS)", f"{mat['uts']}", "MPa")
    pdf.add_table_row("Limite Snervamento (Yield)", f"{mat['yield']}", "MPa")
    pdf.add_table_row("Cicli Annuali Previsti", f"{cycles_yr:,}", "Cicli Primari")
    pdf.ln(3)

    # --- SEZIONE 2: FATIGUE MODIFIERS ---
    pdf.chapter_title("2. Condizioni Ambientali e di Carico")
    pdf.add_table_row("Fattore Correttivo", "Coefficiente", "Condizione Applicata", header=True)
    pdf.add_table_row("Finitura Superficiale (ka)", f"{ka:.3f}", surf)
    pdf.add_table_row("Vettore di Carico (kc)", f"{kc:.2f}", load)
    pdf.add_table_row("Sicurezza/Affidabilità (ke)", f"{ke:.3f}", rel)
    pdf.add_table_row("Fattore Termico (kd)", f"{kd:.3f}", f"{temp_esercizio} C")
    pdf.add_table_row("Fattore Umidità (kw)", f"{kw:.3f}", f"{umidita_relativa} %")
    pdf.add_table_row("Fattore Intaglio (Kf)", f"{kf:.2f}", forma_intaglio) 
    # --- MODIFICA PDF: Aggiunta Microclima in tabella ---
    if usa_microclima and mat['cat'] in ["Polimeri", "Compositi"]:
        pdf.add_table_row("Fattore Microclima", "Attivo", f"{ore_continue} ore continue")
    pdf.ln(3)

    # --- SEZIONE 3: RISULTATI ---
    pdf.chapter_title("3. Output Analisi Strutturale")
    pdf.add_table_row("Grandezza", "Valore", "Unità", header=True)
    pdf.add_table_row("Limite Fatica Ideale", f"{mat['se_base']}", "MPa")
    pdf.add_table_row("Limite Fatica Reale (Se)", f"{int(se_corr)}", "MPa")
    pdf.add_table_row("Stress Teorico Primario", f"{int(s_eq)}", "MPa")
    if usa_miner:
        pdf.add_table_row("Stress Teorico Secondario", f"{int(s_eq_2)}", "MPa")
        pdf.add_table_row("Danno Accumulato", f"{danno_totale*100:.2f} % / anno", "Regola di Miner")
    pdf.add_table_row("Perdita Rigidità Stimata (1 anno)", f"-{perf_decay:.2f} %", "Decadimento")
    pdf.ln(5)
    
    # --- BOX CONCLUSIVO VITA ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, "PREVISIONE VITA UTILE COMPONENTE:", 0, 1)
    if isinstance(years, (int, float)):
        res_text = f"Stima Vita Sicura: {years} Anni"
        color = (0, 128, 0) if years > 5 else (200, 0, 0)
    else:
        res_text = f"Resistenza Strutturale: {years}"
        color = (0, 0, 200)

    pdf.set_font('Arial', 'B', 13)
    pdf.set_text_color(*color)
    pdf.cell(0, 10, res_text, 1, 1, 'C')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    # --- SEZIONE 4: GRAFICO WOHLER ---
    pdf.chapter_title("4. Mappa Decadimento Strutturale (Curva S-N)")
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
