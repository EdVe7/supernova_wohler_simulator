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

st.set_page_config(page_title="Supernova Fatigue Lab", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stDeployButton {display:none;}
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
            st.markdown("<h1 style='text-align:center; color:#FF9800;'>SUPERNOVA</h1>", unsafe_allow_html=True)
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
# 1. DATABASE MATERIALI PROTESICI AVANZATI
# ==========================================
materials_db = {
    "Titanio Ti-6Al-4V (Piloni/Giunti)": {"uts": 950, "yield": 880, "se_base": 510, "cat": "Metalli"},
    "Titanio Grado 5 ELI (Impianti)": {"uts": 860, "yield": 795, "se_base": 440, "cat": "Metalli"},
    "Fibra Carbonio UD (Lame Corsa)": {"uts": 1500, "yield": 1500, "se_base": 900, "cat": "Compositi"},
    "Kevlar/Epoxy (Socket Strutturale)": {"uts": 1300, "yield": 1200, "se_base": 750, "cat": "Compositi"},
    "Alluminio 7075-T6 (Ergal - Raccordi)": {"uts": 572, "yield": 503, "se_base": 159, "cat": "Metalli"},
    "Alluminio 2024-T3 (Aeronautico)": {"uts": 483, "yield": 345, "se_base": 138, "cat": "Metalli"},
    "PEEK (Componenti Flessibili/Socket)": {"uts": 100, "yield": 100, "se_base": 45, "cat": "Polimeri"},
    "Acciaio Inox 316L (Viteria/Giunti)": {"uts": 485, "yield": 170, "se_base": 290, "cat": "Metalli"},
    "Acciaio 4340 (High Strength)": {"uts": 1100, "yield": 950, "se_base": 550, "cat": "Metalli"}
}

# ==========================================
# 2. INPUT USER (SIDEBAR)
# ==========================================
with st.sidebar:
    st.header("🏃 Dati Atleta e Setup")
    atleta_nome = st.text_input("Nome Atleta", "Atleta Paralimpico")
    atleta_peso = st.number_input("Peso Atleta (kg)", value=75)
    sport_target = st.text_input("Sport / Obiettivo", "Golf - Olimpiadi 2040")

    st.header("⚙️ Parametri Materiale")
    mat_name = st.selectbox("Seleziona Materiale", list(materials_db.keys()))
    mat = materials_db[mat_name]
    
    st.header("📉 Fattori Marin")
    surf = st.selectbox("Finitura Superficiale", ["Lucidato", "Lavorato", "Grezzo", "Forgiato"])
    # Aggiunti carichi complessi tipici delle protesi
    load = st.selectbox("Tipo Carico", ["Flessione (Impatto Corsa)", "Assiale (Carico Statico)", "Torsione (Cambio Direzione)", "Flesso-Torsione Combinata"])
    rel = st.selectbox("Affidabilità Richiesta", ["50%", "90%", "95%", "99%", "99.9%", "99.99% (Aerospace)"])
    
    st.header("⚖️ Spettro di Carico")
    s_max = st.number_input("Stress Max (MPa)", value=400, help="Carico di picco durante l'impatto o lo swing")
    s_min = st.number_input("Stress Min (MPa)", value=0, help="Carico a riposo")
    cycles_yr = st.number_input("Cicli Previsti / Anno", value=100000, step=10000)

# ==========================================
# 3. MOTORE FISICO (CALCOLI)
# ==========================================
def get_k_factors(uts, surf_type, load_type, rel_type, mat_cat):
    # Superficie (ka)
    surfs = {"Lucidato": (1.58, -0.085), "Lavorato": (4.51, -0.265), "Grezzo": (57.7, -0.718), "Forgiato": (272.0, -0.995)}
    if mat_cat in ["Compositi", "Polimeri"]: 
        ka = 0.9  # I compositi e polimeri sono meno sensibili alla finitura standard
    else:
        a, b = surfs[surf_type]
        ka = min(a * (uts ** b), 1.0)
    
    # Carico (kc)
    loads = {"Flessione (Impatto Corsa)": 1.0, "Assiale (Carico Statico)": 0.85, "Torsione (Cambio Direzione)": 0.59, "Flesso-Torsione Combinata": 0.75}
    kc = loads[load_type]
    
    # Affidabilità (ke)
    rels = {"50%": 1.0, "90%": 0.897, "95%": 0.868, "99%": 0.814, "99.9%": 0.753, "99.99% (Aerospace)": 0.702}
    ke = rels[rel_type]
    
    return ka, kc, ke

ka, kc, ke = get_k_factors(mat['uts'], surf, load, rel, mat['cat'])
se_corr = mat['se_base'] * ka * kc * ke

# Stress Goodman
sigma_a = (s_max - s_min) / 2
sigma_m = (s_max + s_min) / 2
if sigma_m >= mat['uts']:
    s_eq = 99999 # Rottura statica immediata
else:
    s_eq = sigma_a / (1 - (sigma_m / mat['uts']))

# Vita a Fatica (Basquin)
if s_eq <= se_corr:
    Nf = "Infinito"
    years = "Infinito"
elif s_max >= mat['uts']:
    Nf = 0
    years = 0
else:
    f = 0.9
    S1000 = f * mat['uts']
    N_end = 1e6 if mat['cat'] not in ["Alluminio", "Polimeri"] else 5e8
    b = -(math.log10(S1000/se_corr)) / (math.log10(N_end)-3)
    log_a = math.log10(S1000) - 3*b
    
    Nf_val = 10 ** ((math.log10(s_eq) - log_a)/b)
    Nf = int(Nf_val)
    years = round(Nf_val / cycles_yr, 2)

# Calcolo dati curva
n_x = np.logspace(3, 8, 50)
s_y = (10**log_a) * (n_x**b) if isinstance(Nf, int) and Nf > 0 else np.zeros_like(n_x)
s_y = np.maximum(s_y, se_corr)

# ==========================================
# 4. VISUALIZZAZIONE UI (Plotly)
# ==========================================
st.title("🦾 Analisi Strutturale Protesi")
c1, c2, c3 = st.columns(3)
c1.metric("Stress Eq. (Goodman)", f"{int(s_eq)} MPa")
c2.metric("Limite Fatica Corretto", f"{int(se_corr)} MPa")
c3.metric("Vita Utile Stimata", f"{years} anni" if isinstance(years, (int, float)) else years)

fig = go.Figure()
fig.add_trace(go.Scatter(x=n_x, y=s_y, name="Curva Wöhler S-N", line=dict(color='#2CB8C8', width=3)))
if isinstance(Nf, int) and Nf > 0:
    fig.add_trace(go.Scatter(x=[Nf], y=[s_eq], mode='markers', marker=dict(color='#FF4B4B', size=12), name="Punto Operativo (Rottura)"))
fig.add_hline(y=se_corr, line_dash="dash", line_color="green", annotation_text="Limite di Vita Infinita")
fig.update_layout(xaxis_type="log", title="Curva di Fatica (Wöhler) Interattiva", height=400, xaxis_title="Cicli (N)", yaxis_title="Stress Alternato (MPa)")
st.plotly_chart(fig, use_container_width=True)



# ==========================================
# 5. GENERATORE GRAFICO SEABORN (PER PDF)
# ==========================================
def create_seaborn_temp_image():
    plt.figure(figsize=(10, 5))
    sns.set_theme(style="whitegrid")
    
    # Traccia la curva
    ax = sns.lineplot(x=n_x, y=s_y, color="#2CB8C8", linewidth=2.5, label="Curva Wöhler (Materiale)")
    ax.set_xscale("log")
    
    # Asintoto
    plt.axhline(se_corr, color='green', linestyle='--', linewidth=1.5, label=f"Limite Fatica ({int(se_corr)} MPa)")
    
    # Punto operativo
    if isinstance(Nf, int) and Nf > 0:
        plt.scatter([Nf], [s_eq], color="#FF4B4B", zorder=5, s=150, label="Punto di Lavoro Protesi")
    
    plt.xlabel("Numero di Cicli a Rottura (Log N)", fontsize=11, fontweight='bold')
    plt.ylabel("Stress Equivalente (MPa)", fontsize=11, fontweight='bold')
    plt.title(f"Analisi S-N: {mat_name}", fontsize=14, fontweight='bold')
    plt.legend()
    
    # Salva in temp file
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(tmp_file.name, format="png", bbox_inches="tight", dpi=300)
    plt.close()
    return tmp_file.name

# ==========================================
# 6. PDF ENGINE AVANZATO (Con Immagine)
# ==========================================
class TablePDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_text_color(44, 184, 200) # Colore Brand Turchese
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
        w = [85, 55, 50] 
        h = 7
        self.cell(w[0], h, str(col1), 1)
        self.cell(w[1], h, str(col2), 1)
        self.cell(w[2], h, str(col3), 1, 0, 'C')
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
    pdf.add_table_row("Cicli Annuali Previsti", f"{cycles_yr:,}", "Cicli/y")
    pdf.ln(3)

    # --- SEZIONE 2: FATIGUE MODIFIERS ---
    pdf.chapter_title("2. Condizioni Ambientali e di Carico (Marin)")
    pdf.add_table_row("Fattore Correttivo", "Coefficiente", "Condizione Applicata", header=True)
    pdf.add_table_row("Finitura Superficiale (ka)", f"{ka:.3f}", surf)
    pdf.add_table_row("Vettore di Carico (kc)", f"{kc:.2f}", load)
    pdf.add_table_row("Sicurezza/Affidabilità (ke)", f"{ke:.3f}", rel)
    pdf.ln(3)

    # --- SEZIONE 3: RISULTATI ---
    pdf.chapter_title("3. Output Analisi Strutturale")
    pdf.add_table_row("Grandezza", "Valore", "Unità", header=True)
    pdf.add_table_row("Limite Fatica Ideale", f"{mat['se_base']}", "MPa")
    pdf.add_table_row("Limite Fatica Reale (Se)", f"{int(se_corr)}", "MPa")
    pdf.add_table_row("Stress Massimo Applicato", f"{s_max}", "MPa")
    pdf.add_table_row("Stress Teorico (Goodman)", f"{int(s_eq)}", "MPa")
    pdf.ln(5)
    
    # BOX CONCLUSIVO VITA
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, "PREVISIONE VITA UTILE COMPONENTE:", 0, 1)
    if isinstance(years, (int, float)):
        res_text = f"{Nf:,} Cicli di Esercizio  (Stima: {years} Anni)"
        color = (0, 128, 0) if years > 5 else (200, 0, 0)
    else:
        res_text = f"Resistenza Strutturale: {Nf}"
        color = (0, 0, 200)

    pdf.set_font('Arial', 'B', 13)
    pdf.set_text_color(*color)
    pdf.cell(0, 10, res_text, 1, 1, 'C')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    # --- SEZIONE 4: GRAFICO WOHLER SEABORN ---
    pdf.chapter_title("4. Mappa Decadimento Strutturale (Curva S-N)")
    img_path = create_seaborn_temp_image()
    # Inserisce l'immagine nel PDF (x=10, width=190mm adatta all'A4)
    pdf.image(img_path, x=10, w=190)
    
    # Pulisce il file temporaneo per non intasare il server
    os.remove(img_path)
    
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 7. DOWNLOAD AREA
# ==========================================
st.markdown("---")
if st.button("📄 Genera & Scarica Report Avanzato (PDF con Grafico)"):
    try:
        pdf_bytes = generate_full_pdf()
        st.download_button(
            label="Clicca qui per scaricare il File .pdf",
            data=pdf_bytes,
            file_name=f"Report_Protesi_{atleta_nome.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
        st.success("Report generato con successo! Il grafico Seaborn è stato incluso.")
    except Exception as e:
        st.error(f"Errore durante la generazione del PDF: {e}")
