import streamlit as st
import numpy as np
import plotly.graph_objects as go
import math
from fpdf import FPDF
import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Vector Lab | Fatigue Report", layout="wide", page_icon="⚙️")

st.title("Vector Lab: Fatigue Analysis (No-Kaleido Version)")
st.markdown("Calcolo a fatica con report tabellare professionale (senza dipendenze grafiche pesanti).")

# --- 1. DATABASE MATERIALI ---
materials_db = {
    "Acciaio 4340 (High Strength)": {"uts": 1100, "yield": 950, "se_base": 550, "cat": "Metalli"},
    "Titanio Ti-6Al-4V": {"uts": 950, "yield": 880, "se_base": 510, "cat": "Metalli"},
    "Alluminio 7075-T6": {"uts": 572, "yield": 503, "se_base": 159, "cat": "Metalli"},
    "Acciaio Inox 316L": {"uts": 485, "yield": 170, "se_base": 290, "cat": "Metalli"},
    "Fibra Carbonio UD (Ref)": {"uts": 1500, "yield": 1500, "se_base": 900, "cat": "Compositi"}
}

# --- 2. INPUT USER ---
with st.sidebar:
    st.header("Parametri Materiale")
    mat_name = st.selectbox("Materiale", list(materials_db.keys()))
    mat = materials_db[mat_name]
    
    st.header("Fattori Marin")
    surf = st.selectbox("Finitura", ["Lucidato", "Lavorato", "Grezzo", "Forgiato"])
    load = st.selectbox("Carico", ["Flessione", "Assiale", "Torsione"])
    rel = st.selectbox("Affidabilità", ["50%", "90%", "95%", "99%", "99.9%"])
    
    st.header("Carichi")
    s_max = st.number_input("Stress Max (MPa)", value=400)
    s_min = st.number_input("Stress Min (MPa)", value=0)
    cycles_yr = st.number_input("Cicli/Anno", value=100000)

# --- 3. CALCOLI (MOTORE FISICO) ---
# Fattori Marin
def get_k_factors(uts, surf_type, load_type, rel_type):
    # Superficie (ka)
    surfs = {"Lucidato": (1.58, -0.085), "Lavorato": (4.51, -0.265), 
             "Grezzo": (57.7, -0.718), "Forgiato": (272.0, -0.995)}
    if mat["cat"] == "Compositi": 
        ka = 0.9 
    else:
        a, b = surfs[surf_type]
        ka = min(a * (uts ** b), 1.0)
    
    # Carico (kc)
    kc = {"Flessione": 1.0, "Assiale": 0.85, "Torsione": 0.59}[load_type]
    # Affidabilità (ke)
    ke = {"50%": 1.0, "90%": 0.897, "95%": 0.868, "99%": 0.814, "99.9%": 0.753}[rel_type]
    
    return ka, kc, ke

ka, kc, ke = get_k_factors(mat['uts'], surf, load, rel)
se_corr = mat['se_base'] * ka * kc * ke

# Stress Goodman
sigma_a = (s_max - s_min) / 2
sigma_m = (s_max + s_min) / 2
if sigma_m >= mat['uts']:
    s_eq = 99999 # Rottura
else:
    s_eq = sigma_a / (1 - (sigma_m / mat['uts']))

# Vita
if s_eq <= se_corr:
    Nf = "Infinito"
    years = "Infinito"
elif s_max >= mat['uts']:
    Nf = 0
    years = 0
else:
    # Basquin: S = aN^b
    f = 0.9
    S1000 = f * mat['uts']
    N_end = 1e6 if mat['cat']!="Alluminio" else 5e8
    b = -(math.log10(S1000/se_corr)) / (math.log10(N_end)-3)
    log_a = math.log10(S1000) - 3*b
    
    Nf_val = 10 ** ((math.log10(s_eq) - log_a)/b)
    Nf = int(Nf_val)
    years = round(Nf_val / cycles_yr, 2)

# --- 4. VISUALIZZAZIONE SCREEN ---
c1, c2, c3 = st.columns(3)
c1.metric("Stress Eq. (Goodman)", f"{int(s_eq)} MPa")
c2.metric("Limite Fatica (Se)", f"{int(se_corr)} MPa")
c3.metric("Vita Stimata", f"{years} anni" if isinstance(years, (int, float)) else years)

# Grafico a video (SOLO VIDEO, non nel PDF)
fig = go.Figure()
n_x = np.logspace(3, 8, 50)
s_y = (10**log_a) * (n_x**b) if isinstance(Nf, int) and Nf > 0 else np.zeros_like(n_x)
s_y = np.maximum(s_y, se_corr)
fig.add_trace(go.Scatter(x=n_x, y=s_y, name="Curva Wöhler"))
if isinstance(Nf, int) and Nf > 0:
    fig.add_trace(go.Scatter(x=[Nf], y=[s_eq], mode='markers', marker=dict(color='red', size=10), name="Punto Operativo"))
fig.update_layout(xaxis_type="log", title="Curva S-N (Solo Anteprima)", height=400)
st.plotly_chart(fig, use_container_width=True)

# --- 5. PDF ENGINE (TABELLARE SENZA KALEIDO) ---
class TablePDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'VECTOR LAB - REPORT ANALISI FATICA', 0, 1, 'C')
        self.line(10, 20, 200, 20)
        self.ln(5)

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 8, title, 0, 1, 'L', 1)
        self.ln(2)

    def add_table_row(self, col1, col2, col3, header=False):
        if header:
            self.set_font('Arial', 'B', 10)
        else:
            self.set_font('Arial', '', 10)
            
        # Larghezze colonne: Descrizione, Valore, Unità
        w = [90, 50, 50] 
        h = 7
        
        self.cell(w[0], h, str(col1), 1)
        self.cell(w[1], h, str(col2), 1)
        self.cell(w[2], h, str(col3), 1, 0, 'C') # 0 = no a capo
        self.ln()

def generate_table_pdf():
    pdf = TablePDF()
    pdf.add_page()
    
    # --- SEZIONE 1: INPUT ---
    pdf.chapter_title("1. Parametri di Input")
    pdf.add_table_row("Parametro", "Valore", "Note", header=True)
    pdf.add_table_row("Materiale", mat_name, mat['cat'])
    pdf.add_table_row("Carico Rottura (UTS)", f"{mat['uts']}", "MPa")
    pdf.add_table_row("Limite Snervamento", f"{mat['yield']}", "MPa")
    pdf.add_table_row("Cicli per Anno", f"{cycles_yr:,}", "Cicli/y")
    pdf.ln(5)

    # --- SEZIONE 2: FATTORI MARIN ---
    pdf.chapter_title("2. Fattori Correttivi (Marin)")
    pdf.add_table_row("Fattore", "Coefficiente (k)", "Condizione", header=True)
    pdf.add_table_row("Superficie (ka)", f"{ka:.3f}", surf)
    pdf.add_table_row("Tipo Carico (kc)", f"{kc:.2f}", load)
    pdf.add_table_row("Affidabilità (ke)", f"{ke:.3f}", rel)
    pdf.ln(5)

    # --- SEZIONE 3: RISULTATI ---
    pdf.chapter_title("3. Risultati Calcolo")
    pdf.add_table_row("Grandezza", "Valore Calcolato", "Unità", header=True)
    pdf.add_table_row("Limite Fatica Base", f"{mat['se_base']}", "MPa")
    pdf.add_table_row("Limite Fatica Corretto (Se)", f"{int(se_corr)}", "MPa")
    pdf.add_table_row("Stress Max Applicato", f"{s_max}", "MPa")
    pdf.add_table_row("Stress Equivalente (Goodman)", f"{int(s_eq)}", "MPa")
    
    pdf.ln(5)
    
    # BOX CONCLUSIVO
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "STIMA VITA UTILE:", 0, 1)
    
    if isinstance(years, (int, float)):
        res_text = f"{Nf:,} Cicli  (= {years} Anni)"
        color = (0, 100, 0) if years > 10 else (200, 0, 0)
    else:
        res_text = f"{Nf}" # Infinito o Rottura
        color = (0, 0, 200)

    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(*color)
    pdf.cell(0, 10, res_text, 1, 1, 'C')
    pdf.set_text_color(0, 0, 0)
    
    # Note
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 8)
    pdf.multi_cell(0, 5, "Nota: Report generato automaticamente. Analisi basata sul metodo S-N (Wöhler) con correzione dello stress medio di Goodman. I valori sono stime teoriche.")
    
    return pdf.output(dest='S').encode('latin-1')

# --- BOTTONE DOWNLOAD ---
st.markdown("---")
if st.button("📄 Scarica Report Tecnico (PDF)"):
    pdf_bytes = generate_table_pdf()
    st.download_button(
        label="Download PDF Definitivo",
        data=pdf_bytes,
        file_name="Report_Fatica_VectorLab.pdf",
        mime="application/pdf"
    )