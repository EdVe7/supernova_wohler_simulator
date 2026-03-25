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
import pandas as pd
import json # NUOVO: Necessario per gestire lo Snapshot

# COLORI BRAND SUPERNOVA E ACCENTI
GOLD_SN = "#D4AF37" 
BG_DARK = "#0B1D22"
COLOR_RED_ACC = "#D90429"  # Rosso più vivo e accattivante
COLOR_GOLD_ACC = "#FFC300" # Oro più saturo e vibrante

st.set_page_config(page_title="Supernova Fatigue Lab", page_icon="🚀", layout="wide")

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
        st.markdown("<h2 style='text-align:center; font-weight: 900; font-size: 2.5em; letter-spacing: 2px;'>DATA OVER TALENT</h2>", unsafe_allow_html=True)
    time.sleep(3) 
    placeholder.empty()
    st.session_state['splash_done'] = True

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<h3 style='text-align:center;'>🔒 Accesso Riservato Lab</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#A0B0C0; margin-bottom: 20px;'>Benvenuto nel centro di calibrazione avanzata. Inserisci le tue credenziali per iniziare l'ottimizzazione del setup.</p>", unsafe_allow_html=True)
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
    # NUOVO: Gestione Snapshot (Import configurazioni salvate)
    st.header("💾 Snapshot Configurazione")
    uploaded_json = st.file_uploader("Carica Snapshot (JSON)", type=["json"], help="Carica un setup salvato per applicarlo immediatamente.")
    config_override = None
    if uploaded_json is not None:
        try:
            config_override = json.load(uploaded_json)
            st.success("Snapshot applicato con successo ai calcoli!")
        except Exception as e:
            st.error("Errore lettura file JSON.")
            
    st.header("🏃 Profilazione Atleta Avanzata") 
    atleta_nome = st.text_input("Nome Atleta", "Atleta Paralimpico", help="Nome dell'atleta per la generazione del report.")
    atleta_peso = st.number_input("Peso Atleta (kg)", value=75, help="Massa corporea (utile come riferimento per stimare gli stress se non noti).")
    sport_target = st.text_input("Sport / Obiettivo", "Olimpiadi di Golf 2040")
    classe_mobilita = st.selectbox("Classe / Handicap", ["Open / Nessuna", "Amputazione Monolaterale", "Amputazione Bilaterale", "Mobilità Ridotta"], help="Metadato utile per contestualizzare l'analisi nel report.")

    st.header("🎯 Profili Sportivi Rapidi")
    presets = {
        "Manuale (Nessun Preset)": None,
        "Maratona (Basso Impatto, Alta Freq.)": {"load": "Flessione (Impatto Corsa)", "s_max": 150, "cycles": 1500000},
        "Sprint 100m (Alto Impatto, Bassa Freq.)": {"load": "Flessione (Impatto Corsa)", "s_max": 450, "cycles": 5000},
        "Salto in Lungo (Impatto Estremo, Bassa Freq.)": {"load": "Flessione (Impatto Corsa)", "s_max": 650, "cycles": 1500},
        "Ciclismo su Pista (Alta Freq., Carico Costante)": {"load": "Assiale (Carico Statico)", "s_max": 180, "cycles": 3000000},
        "Snowboard / Sci (Torsione Continua)": {"load": "Torsione (Cambio Direzione)", "s_max": 300, "cycles": 50000},
        "Sollevamento Pesi (Carico Statico Max)": {"load": "Assiale (Carico Statico)", "s_max": 750, "cycles": 500},
        "Golf Swing (Multi-assiale)": {"load": "Golf Swing (Multi-assiale)", "s_max": 250, "cycles": 15000, "sigma_ass": 180, "tau_tors": 120},
        "Golf - Preparazione Olimpica (Volume Estremo)": {"load": "Golf Swing (Multi-assiale)", "s_max": 280, "cycles": 45000, "sigma_ass": 200, "tau_tors": 150}
    }
    preset_choice = st.selectbox("Carica Configurazione", list(presets.keys()), help="Seleziona uno scenario per precompilare i campi di carico in automatico.")
    p_data = presets[preset_choice]

    st.header("⚙️ Parametri Ambientali")
    mat_name = st.selectbox("Seleziona Materiale Principale", list(materials_db.keys()), help="La lega o il composito che costituisce la sezione critica in analisi.")
    
    mat = materials_db[mat_name] 

    temp_esercizio = st.slider("Temperatura Operativa (°C)", -20, 50, 25, help="Temperature estreme declassano le performance dei polimeri e dei compositi (Fattore Kd).")
    umidita_relativa = st.slider("Umidità Relativa (%)", 0, 100, 0, help="L'umidità accelera il degrado della matrice nei compositi (Fattore Kw).")
    
    st.header("🌡️ Microclima Socket")
    usa_microclima = st.checkbox("Accumulo Calore (Cicli Continui)", help="Attiva se l'atleta svolge sessioni lunghe senza togliere la protesi.")
    ore_continue = st.slider("Ore Sessione Continuous", 1, 10, 4) if usa_microclima else 0

    st.header("📉 Fattori Marin")
    surf = st.selectbox("Finitura Superficiale", ["Lucidato", "Lavorato", "Grezzo", "Forgiato"], help="Maggiore è la rugosità, maggiore è la probabilità di innesco cricche (Fattore Ka).")
    
    load_options = ["Flessione (Impatto Corsa)", "Assiale (Carico Statico)", "Torsione (Cambio Direzione)", "Golf Swing (Multi-assiale)"]
    def_load_idx = load_options.index(p_data["load"]) if p_data else 0
    load = st.selectbox("Tipo Carico", load_options, index=def_load_idx, help="Un carico flessionale puro è meno gravoso di uno assiale o torsionale puro (Fattore Kc).")
    
    rel = st.selectbox("Affidabilità Richiesta", ["50%", "90%", "99%", "99.99%"], index=2, help="L'affidabilità statistica richiesta al componente. 99% è lo standard biomedicale (Fattore Ke).")
    
    st.header("📐 Geometria (Intaglio)")
    forma_intaglio = st.selectbox("Geometria Sezione Critica", ["Superficie Liscia (Kf=1.0)", "Raccordo Ampio (Kf=1.2)", "Foro Passante (Kf=1.8)", "Spigolo Vivo (Kf=2.5)"], help="Concenztrazioni di stress geometriche che amplificano il carico locale (Kf).")
    kf_dict = {"Superficie Liscia (Kf=1.0)": 1.0, "Raccordo Ampio (Kf=1.2)": 1.2, "Foro Passante (Kf=1.8)": 1.8, "Spigolo Vivo (Kf=2.5)": 2.5}
    kf = kf_dict[forma_intaglio]

    st.header("⚖️ Spettro di Carico Primario")
    
    # NUOVO: Convertitore Biomeccanico
    usa_biomec = st.checkbox("🧮 Calcolatore Biomeccanico", help="Calcola lo stress massimo a partire dalle dinamiche corporee.")
    
    if usa_biomec:
        vel_impatto = st.number_input("Velocità Gesto/Impatto (m/s)", value=45.0)
        grf_multi = st.number_input("Ground Reaction Force (Moltiplicatore x BW)", value=1.5)
        # Formula empirica per stimare lo stress in base a peso, accelerazione e forza reazione
        s_max_biomec = (vel_impatto * 1.5) + (grf_multi * atleta_peso * 0.8)
        st.info(f"Stress Equivalente Calcolato: {s_max_biomec:.1f} MPa")
        s_max = float(s_max_biomec)
        s_min = 1.0
        
    elif load == "Golf Swing (Multi-assiale)":
        def_sigma_ass = p_data.get("sigma_ass", 200) if p_data else 200
        def_tau_tors = p_data.get("tau_tors", 150) if p_data else 150
        sigma_ass = st.number_input("Stress Assiale (MPa)", value=def_sigma_ass)
        tau_tors = st.number_input("Stress Taglio/Torsione (MPa)", value=def_tau_tors)
        s_max_eq = math.sqrt(sigma_ass**2 + 3 * (tau_tors**2))
        st.info(f"Equivalente Von Mises: {s_max_eq:.1f} MPa")
        s_max = st.number_input("Stress Max Eq. (MPa)", value=float(s_max_eq))
        s_min = st.number_input("Stress Min (MPa)", value=1, min_value=1)
    else:
        def_smax = p_data["s_max"] if p_data else 400
        s_max = st.number_input("Stress Max (MPa)", value=def_smax, help="Picco massimo di stress durante il ciclo.")
        s_min = st.number_input("Stress Min (MPa)", value=1, min_value=1, help="Stress minimo.")
        
    def_cycles = p_data["cycles"] if p_data else 100000
    cycles_yr = st.number_input("Cicli Previsti / Anno", value=def_cycles, step=10000)

    st.markdown("---")
    usa_multiassiale_custom = st.checkbox("⚙️ Attiva Multi-Assiale Custom", help="Usa Von Mises per combinare flessione e torsione anche su sport non-golf.")
    if usa_multiassiale_custom and load != "Golf Swing (Multi-assiale)" and not usa_biomec:
        sigma_ass_c = st.number_input("Stress Assiale/Flessionale (MPa)", value=200.0)
        tau_tors_c = st.number_input("Stress Taglio/Torsionale (MPa)", value=100.0)
        s_max_eq_c = math.sqrt(sigma_ass_c**2 + 3 * (tau_tors_c**2))
        st.info(f"Von Mises Calcolato: {s_max_eq_c:.1f} MPa")
        s_max = s_max_eq_c 

    st.header("📊 Digital Twin & Spettro Telemetrico")
    st.write("Inserisci i dati sensore manualmente o via CSV.")
    telemetria_manuale = st.text_area("Input Rapido (Stress, Cicli)", placeholder="Es:\n250, 5000\n300, 1000", help="Inserisci i valori separati da virgola. Una riga per ogni set di carico.")
    uploaded_csv = st.file_uploader("Carica File (CSV)", type=["csv"], help="Il file deve avere due colonne: Stress in MPa e Cicli Annuali. Si somma ai danni calcolati.")

    st.header("💥 Carico Secondario (Miner)")
    usa_miner = st.checkbox("Aggiungi Impatti Rari / Picchi", help="Applica la regola di Miner per combinare il danno del carico primario con un secondo carico occasionale più severo.")
    if usa_miner:
        s_max_2 = st.number_input("Stress Max Sec. (MPa)", value=600)
        s_min_2 = st.number_input("Stress Min Sec. (MPa)", value=1, min_value=1)
        cycles_yr_2 = st.number_input("Cicli Sec. / Anno", value=1000, step=100)
    else:
        s_max_2, s_min_2, cycles_yr_2 = 0, 0, 0

    st.header("🔄 Confronto (A/B Test)")
    mat_comp_name = st.selectbox("Seleziona Materiale B (Opzionale)", ["Nessuno"] + list(materials_db.keys()), help="Traccia una seconda curva S-N per confrontare direttamente le prestazioni.")

    # NUOVO: Export Snapshot
    current_config = {
        "mat_name": mat_name, "temp_esercizio": temp_esercizio, "umidita_relativa": umidita_relativa,
        "usa_microclima": usa_microclima, "ore_continue": ore_continue, "surf": surf, "load": load,
        "rel": rel, "forma_intaglio": forma_intaglio, "s_max": s_max, "s_min": s_min, "cycles_yr": cycles_yr,
        "usa_miner": usa_miner, "s_max_2": s_max_2, "s_min_2": s_min_2, "cycles_yr_2": cycles_yr_2
    }
    json_str = json.dumps(current_config, indent=4)
    st.download_button(label="💾 Scarica Configurazione", data=json_str, file_name=f"Setup_{atleta_nome.replace(' ','_')}.json", mime="application/json")


# ==========================================
# GESTIONE OVERRIDE DA SNAPSHOT JSON
# ==========================================
if config_override:
    mat_name = config_override.get("mat_name", mat_name)
    mat = materials_db.get(mat_name, mat)
    temp_esercizio = config_override.get("temp_esercizio", temp_esercizio)
    umidita_relativa = config_override.get("umidita_relativa", umidita_relativa)
    usa_microclima = config_override.get("usa_microclima", usa_microclima)
    ore_continue = config_override.get("ore_continue", ore_continue)
    surf = config_override.get("surf", surf)
    load = config_override.get("load", load)
    rel = config_override.get("rel", rel)
    forma_intaglio = config_override.get("forma_intaglio", forma_intaglio)
    kf = kf_dict.get(forma_intaglio, kf)
    s_max = config_override.get("s_max", s_max)
    s_min = config_override.get("s_min", s_min)
    cycles_yr = config_override.get("cycles_yr", cycles_yr)
    usa_miner = config_override.get("usa_miner", usa_miner)
    s_max_2 = config_override.get("s_max_2", s_max_2)
    s_min_2 = config_override.get("s_min_2", s_min_2)
    cycles_yr_2 = config_override.get("cycles_yr_2", cycles_yr_2)

# ==========================================
# 3. MOTORE FISICO (CALCOLI CON FIX ERRORI MATEMATICI) 
# ==========================================
def get_k_factors(uts, surf_type, load_type, rel_type, mat_cat, temp, hum):
    surfs = {"Lucidato": (1.58, -0.085), "Lavorato": (4.51, -0.265), "Grezzo": (57.7, -0.718), "Forgiato": (272.0, -0.995)}
    ka = 0.9 if mat_cat in ["Compositi", "Polimeri"] else min(surfs[surf_type][0] * (uts ** surfs[surf_type][1]), 1.0)
    
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

if usa_microclima and mat['cat'] in ["Polimeri", "Compositi"]:
    kd = kd * (1.0 - (0.02 * ore_continue))

se_corr = mat['se_base'] * ka * kc * ke * kd * kw

# FIX MATEMATICO: Prevenzione errori logaritmo se se_corr eccede teoricamente S1000
f = 0.9
S1000 = f * mat['uts']
se_corr = min(se_corr, S1000 * 0.99) # Impedisce che b diventi positivo (pendenza anomala)

N_end = 1e6 if mat['cat'] not in ["Alluminio", "Polimeri"] else 5e8
b = -(math.log10(S1000/se_corr)) / (math.log10(N_end)-3)
log_a = math.log10(S1000) - 3*b

sigma_a = (s_max - s_min) / 2
sigma_m = (s_max + s_min) / 2
s_eq = (sigma_a / (1 - (sigma_m / mat['uts'])) if sigma_m < mat['uts'] else 9999) * kf

# FIX MATEMATICO: Controllo domini logaritmo
if s_eq <= se_corr: Nf_val = float('inf')
elif s_max >= mat['uts'] or s_eq <= 0: Nf_val = 1e-5 
else:
    Nf_val = 10 ** ((math.log10(s_eq) - log_a)/b)

if usa_miner:
    sigma_a_2 = (s_max_2 - s_min_2) / 2
    sigma_m_2 = (s_max_2 + s_min_2) / 2
    s_eq_2 = (sigma_a_2 / (1 - (sigma_m_2 / mat['uts'])) if sigma_m_2 < mat['uts'] else 9999) * kf
    
    if s_eq_2 <= se_corr: Nf_val_2 = float('inf')
    elif s_max_2 >= mat['uts'] or s_eq_2 <= 0: Nf_val_2 = 1e-5
    else:
        Nf_val_2 = 10 ** ((math.log10(s_eq_2) - log_a)/b)
else:
    Nf_val_2 = float('inf')
    s_eq_2 = 0

danno_1 = cycles_yr / Nf_val if Nf_val > 0 else float('inf')
danno_2 = cycles_yr_2 / Nf_val_2 if Nf_val_2 > 0 else float('inf')

danno_csv = 0
if uploaded_csv is not None:
    try:
        df_spettro = pd.read_csv(uploaded_csv, header=None)
        for idx, row in df_spettro.iterrows():
            stress_csv = float(row.iloc[0]) * kf
            cicli_csv = float(row.iloc[1])
            if stress_csv <= se_corr:
                nf_csv = float('inf')
            elif stress_csv >= mat['uts'] or stress_csv <= 0:
                nf_csv = 1e-5
            else:
                nf_csv = 10 ** ((math.log10(stress_csv) - log_a)/b)
            danno_csv += cicli_csv / nf_csv if nf_csv > 0 else float('inf')
        st.sidebar.success("CSV caricato: Danno aggiunto.")
    except Exception as e:
        st.sidebar.error(f"Errore lettura CSV. ({e})")

danno_manuale = 0
if telemetria_manuale:
    try:
        for riga in telemetria_manuale.split('\n'):
            if riga.strip():
                valori = riga.split(',')
                if len(valori) == 2:
                    stress_man = float(valori[0].strip()) * kf
                    cicli_man = float(valori[1].strip())
                    if stress_man <= se_corr: nf_man = float('inf')
                    elif stress_man >= mat['uts'] or stress_man <= 0: nf_man = 1e-5
                    else: nf_man = 10 ** ((math.log10(stress_man) - log_a)/b)
                    danno_manuale += cicli_man / nf_man if nf_man > 0 else float('inf')
        st.sidebar.success("Input manuale elaborato.")
    except Exception as e:
        st.sidebar.error("Errore formato input manuale.")

danno_totale = danno_1 + danno_2 + danno_csv + danno_manuale

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
    se_corr2 = min(se_corr2, S1000_2 * 0.99) # Fix
    N_end_2 = 1e6 if mat2['cat'] not in ["Alluminio", "Polimeri"] else 5e8
    b2 = -(math.log10(S1000_2/se_corr2)) / (math.log10(N_end_2)-3)
    log_a2 = math.log10(S1000_2) - 3*b2
    
    s_y_comp = (10**log_a2) * (n_x**b2)
    s_y_comp = np.maximum(s_y_comp, se_corr2)

# ==========================================
# 4. VISUALIZZAZIONE UI (CON VISTA TOGGLE)
# ==========================================
c_title, c_toggle = st.columns([3, 1])
with c_title:
    st.title("🦾 Analisi Strutturale Protesi")
with c_toggle:
    st.markdown("<br>", unsafe_allow_html=True)
    # NUOVO: Toggle Vista Ingegnere / Atleta
    vista_mode = st.radio("Interfaccia:", ["Vista Ingegnere ⚙️", "Vista Atleta 🏃"], horizontal=True)

if vista_mode == "Vista Atleta 🏃":
    st.markdown("### 🚦 Status Componente")
    if danno_totale >= 1 or s_max >= mat['uts'] or (usa_miner and s_max_2 >= mat['uts']):
        st.error("🔴 **RIGETTO:** Rischio di rottura immediato. Materiale o configurazione non adeguata.")
    elif isinstance(years, (int, float)) and years <= 2:
        st.warning("🟡 **ATTENZIONE:** Il materiale resisterà, ma perderà molta spinta elastica. Valuta sostituzioni frequenti.")
    else:
        st.success("🟢 **READY TO COMPETE:** Il setup è solido e la trasmissione di potenza rimarrà costante nel tempo.")
        
    spinta_residua = 100.0 - perf_decay
    st.metric("Efficienza / Spinta Elastica Residua Stimata (Anno 1)", f"{spinta_residua:.1f}%")
    st.progress(int(spinta_residua) if spinta_residua > 0 else 0)
    
else:
    # VISTA INGEGNERE ORIGINALE (Mantenuta Pedissequamente)
    st.markdown("### 🚥 Dashboard Rischio Operativo")
    if danno_totale >= 1 or s_max >= mat['uts'] or (usa_miner and s_max_2 >= mat['uts']):
        st.error("🔴 **ALLERTA CRITICA:** Pericolo di rottura catastrofica. Il componente non sopporta il carico. Modificare materiale o sezione.")
    elif isinstance(years, (int, float)) and years <= 2:
        st.warning(f"🟡 **ISPEZIONE CONSIGLIATA:** Il componente mostra fatica elevata. Sostituzione prevista entro {years} anni.")
    else:
        st.success("🟢 **SICURO:** Il componente è dimensionato correttamente per il volume di allenamento previsto.")
    st.markdown("---")

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
        fig.add_trace(go.Scatter(x=[Nf], y=[s_eq], mode='markers', marker=dict(color=COLOR_RED_ACC, size=12), name="Carico Primario"))

    if usa_miner and isinstance(Nf_val_2, float) and Nf_val_2 < float('inf'):
        fig.add_trace(go.Scatter(x=[int(Nf_val_2)], y=[s_eq_2], mode='markers', marker=dict(color='#FFA500', size=10, symbol='x'), name="Carico Secondario"))

    if mat_comp_name != "Nessuno":
        fig.add_trace(go.Scatter(x=n_x, y=s_y_comp, name=f"Confronto: {mat_comp_name}", line=dict(color="#A0B0C0", width=2, dash='dash')))

    fig.update_layout(xaxis_type="log", title="Curva di Fatica (Wöhler) - Supernova Oro", height=400)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🛠️ Modulo Avanzato: Ottimizzazione & Diagnostica")

    penalties_dict = {
        "Finitura Superficiale (Ka)": round((1 - ka) * 100, 1),
        "Tipo Sollecitazione (Kc)": round((1 - kc) * 100, 1),
        "Affidabilità Richiesta (Ke)": round((1 - ke) * 100, 1),
        "Temperatura/Microclima (Kd)": round((1 - kd) * 100, 1),
        "Umidità Relativa (Kw)": round((1 - kw) * 100, 1),
        "Effetto Intaglio (Kf)": round((1 - (1/kf)) * 100, 1) if kf > 1.0 else 0.0
    }
    penalties_filtered = {k: v for k, v in penalties_dict.items() if v > 0}
    penalties_sorted = dict(sorted(penalties_filtered.items(), key=lambda item: item[1]))

    c_opt1, c_opt2, c_opt3 = st.columns([1.5, 1, 1]) 

    with c_opt1:
        st.markdown("**1. Diagnostica Sensibilità (Tornado Chart)**")
        if penalties_sorted:
            fig_tornado = go.Figure(go.Bar(
                x=list(penalties_sorted.values()),
                y=list(penalties_sorted.keys()),
                orientation='h',
                marker=dict(color=COLOR_RED_ACC)
            ))
            fig_tornado.update_layout(height=250, margin=dict(l=0,r=0,t=30,b=0), title="Fattori di Riduzione Resistenza (%)", xaxis_title="Penalità %")
            st.plotly_chart(fig_tornado, use_container_width=True)
        else:
            st.info("Condizioni Ideali: Nessuna penalizzazione applicata al limite di fatica base.")

    with c_opt2:
        st.markdown("**2. Solver Topologico**")
        target_anni = st.number_input("Target Vita (Anni)", value=4.0, min_value=0.5, step=0.5)
        target_cicli = target_anni * (cycles_yr + cycles_yr_2)
        
        if target_cicli >= N_end: s_target = se_corr
        else: s_target = 10 ** (log_a + b * math.log10(target_cicli))
        
        st.info(f"Max Stress per target: **{s_target:.1f} MPa**")
        
        if s_eq < s_target and s_eq > 0:
            st.success(f"📉 Sezione sovradimensionata: -{((s_target/s_eq)-1)*100:.1f}% peso stimato.")
        elif s_eq > s_target:
            st.error(f"⚠️ Rischio: Aumenta la sezione del {(1-(s_target/s_eq))*100:.1f}%.")

    with c_opt3:
        st.markdown("**3. Hysteresis (Decadimento)**")
        fig_stiff = go.Figure()
        
        stiffness = 100 - (perf_decay * (np.log10(n_x) / 6)) 
        stiffness = np.clip(stiffness, 0, 100)
        
        fig_stiff.add_trace(go.Scatter(x=n_x, y=stiffness, fill='tozeroy', name="Modulo Elastico (%)", line=dict(color=COLOR_GOLD_ACC if perf_decay < 10 else COLOR_RED_ACC)))
        fig_stiff.update_layout(xaxis_type="log", height=200, margin=dict(l=0,r=0,t=30,b=0), title="Stiffness Retention %")
        st.plotly_chart(fig_stiff, use_container_width=True)

    # NUOVO: Proiezione Timeline Dinamica (Macro-Cicli)
    st.markdown("---")
    st.subheader("📈 Proiezione Danno su Macro-Cicli (Timeline Orizzonte Olimpico)")
    anni_proj = np.arange(1, 16)
    danno_cum_proj = np.clip(anni_proj * danno_totale * 100, 0, 100)
    fig_timeline = go.Figure()
    fig_timeline.add_trace(go.Scatter(x=anni_proj, y=danno_cum_proj, mode='lines+markers', line=dict(color=COLOR_RED_ACC, width=3), name="Danno Cumulato %"))
    fig_timeline.add_hline(y=100, line_dash="dash", line_color="black", annotation_text="Punto di Rottura")
    fig_timeline.update_layout(height=250, margin=dict(l=0,r=0,t=30,b=0), xaxis_title="Anni di Utilizzo Continuativo", yaxis_title="Danno Strutturale %")
    st.plotly_chart(fig_timeline, use_container_width=True)

# ==========================================
# 5. GENERATORE PDF COMPATTO E COMPLETO
# ==========================================
def create_seaborn_temp_image():
    plt.figure(figsize=(9, 4))
    sns.set_theme(style="whitegrid")
    ax = sns.lineplot(x=n_x, y=s_y, color=GOLD_SN, linewidth=2.5, label=mat_name)
    ax.set_xscale("log")
    plt.axhline(se_corr, color=COLOR_GOLD_ACC, linestyle='--')
    
    if isinstance(Nf, int) and Nf > 0:
        plt.scatter([Nf], [s_eq], color=COLOR_RED_ACC, zorder=5, s=150, label="Primario")
        
    if usa_miner and isinstance(Nf_val_2, float) and Nf_val_2 < float('inf'):
        plt.scatter([int(Nf_val_2)], [s_eq_2], color="#FFA500", zorder=5, s=100, marker='X', label="Secondario")

    if mat_comp_name != "Nessuno":
        sns.lineplot(x=n_x, y=s_y_comp, color="#A0B0C0", linewidth=2.0, linestyle="--", label=mat_comp_name)

    plt.title(f"Analisi Strutturale Combinata", fontsize=12, fontweight='bold')
    plt.legend()
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(tmp_file.name, format="png", bbox_inches="tight", dpi=300)
    plt.close()
    return tmp_file.name

def create_tornado_temp_image():
    plt.figure(figsize=(9, 3))
    sns.set_theme(style="whitegrid")
    if penalties_sorted:
        plt.barh(list(penalties_sorted.keys()), list(penalties_sorted.values()), color=COLOR_RED_ACC)
        plt.xlabel("Penalità %", fontsize=9)
        plt.title("Diagnostica Sensibilità (Fattori di Riduzione)", fontsize=11, fontweight='bold')
        plt.tight_layout()
    else:
        plt.text(0.5, 0.5, "Condizioni Ideali: Nessuna penalizzazione", ha='center', va='center', fontsize=11)
        plt.axis('off')
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(tmp_file.name, format="png", bbox_inches="tight", dpi=300)
    plt.close()
    return tmp_file.name

def create_hysteresis_temp_image():
    plt.figure(figsize=(9, 3))
    sns.set_theme(style="whitegrid")
    stiffness_arr = 100 - (perf_decay * (np.log10(n_x) / 6))
    stiffness_arr = np.clip(stiffness_arr, 0, 100)
    
    color_fill = COLOR_GOLD_ACC if perf_decay < 10 else COLOR_RED_ACC
    plt.fill_between(n_x, stiffness_arr, color=color_fill, alpha=0.5)
    plt.plot(n_x, stiffness_arr, color=color_fill, linewidth=2.5)
    
    plt.xscale("log")
    plt.ylim(0, 105)
    plt.title("Stiffness Retention % (Modulo Elastico)", fontsize=11, fontweight='bold')
    plt.xlabel("Cicli", fontsize=9)
    plt.ylabel("Rigidità (%)", fontsize=9)
    
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(tmp_file.name, format="png", bbox_inches="tight", dpi=300)
    plt.close()
    return tmp_file.name

# NUOVO: Immagine per Timeline da inserire nel PDF
def create_timeline_temp_image():
    plt.figure(figsize=(9, 3))
    sns.set_theme(style="whitegrid")
    anni_proj = np.arange(1, 16)
    danno_cum_proj = np.clip(anni_proj * danno_totale * 100, 0, 100)
    plt.plot(anni_proj, danno_cum_proj, color=COLOR_RED_ACC, marker='o', linewidth=2.5)
    plt.axhline(100, color="black", linestyle="--")
    plt.title("Proiezione Danno su Macro-Cicli", fontsize=11, fontweight='bold')
    plt.xlabel("Anni", fontsize=9)
    plt.ylabel("Danno Cumulato %", fontsize=9)
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(tmp_file.name, format="png", bbox_inches="tight", dpi=300)
    plt.close()
    return tmp_file.name

class TablePDF(FPDF):
    def header(self):
        # ---------------------------------------------------------
        # 🟢 INIZIO CODICE LOGO PDF
        # Se genera un errore al download perché non trova "logo.png" 
        # (es. se deployato su cloud senza path corretta), 
        # cancella le 4 righe sottostanti dal "try" all'"except: pass"
        # ---------------------------------------------------------
        try:
            self.image("logo.png", 10, 8, 20)
        except:
            pass
        # ---------------------------------------------------------
        # 🔴 FINE CODICE LOGO PDF
        # ---------------------------------------------------------

        self.set_font('Arial', 'B', 14)
        self.set_text_color(212, 175, 55) 
        self.cell(0, 6, 'SUPERNOVA LAB - PROSTHETICS FATIGUE REPORT', 0, 1, 'C')
        self.line(10, 16, 200, 16)
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 5, 'Powered by Supernova Sport Science', 0, 0, 'C')
        self.cell(0, 5, f'Pagina {self.page_no()}', 0, 0, 'R')
        
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 11)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(0, 0, 0)
        self.cell(0, 6, title, 0, 1, 'L', 1)
        self.ln(1)

    def add_table_row(self, col1, col2, col3, header=False):
        if header:
            self.set_font('Arial', 'B', 9)
        else:
            self.set_font('Arial', '', 9)
        self.cell(85, 5, str(col1), 1)
        self.cell(55, 5, str(col2), 1)
        self.cell(50, 5, str(col3), 1, 0, 'C')
        self.ln()

def generate_full_pdf():
    pdf = TablePDF()
    pdf.add_page()
    
    # --- SEZIONE 0: DATI ATLETA ---
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 5, f"Atleta: {atleta_nome} ({atleta_peso} kg) | Target Event: {sport_target} | Data: {datetime.datetime.now().strftime('%d/%m/%Y')}", 0, 1)
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 5, f"Classe/Handicap: {classe_mobilita}", 0, 1) # Aggiunta metadato atleta
    pdf.ln(2)

    # --- SEZIONE 1: INPUT ---
    pdf.chapter_title("1. Parametri di Configurazione")
    pdf.add_table_row("Parametro", "Valore", "Note", header=True)
    pdf.add_table_row("Materiale Scelto", mat_name, mat['cat'])
    pdf.add_table_row("Carico Rottura Statico (UTS)", f"{mat['uts']}", "MPa")
    pdf.add_table_row("Limite Snervamento (Yield)", f"{mat['yield']}", "MPa")
    pdf.add_table_row("Cicli Annuali Previsti", f"{cycles_yr:,}", "Cicli Primari")
    # NUOVO: Aggiunta info biomeccanica se usata
    if usa_biomec:
        pdf.add_table_row("Metodo Calcolo Stress", "Biomeccanica Inversa", "Attivo")
    pdf.ln(2)

    # --- SEZIONE 2: FATIGUE MODIFIERS ---
    pdf.chapter_title("2. Condizioni Ambientali e di Carico")
    pdf.add_table_row("Fattore Correttivo", "Coefficiente", "Condizione Applicata", header=True)
    pdf.add_table_row("Finitura Superficiale (ka)", f"{ka:.3f}", surf)
    pdf.add_table_row("Vettore di Carico (kc)", f"{kc:.2f}", load)
    pdf.add_table_row("Sicurezza/Affidabilità (ke)", f"{ke:.3f}", rel)
    pdf.add_table_row("Fattore Termico (kd)", f"{kd:.3f}", f"{temp_esercizio} C")
    pdf.add_table_row("Fattore Umidità (kw)", f"{kw:.3f}", f"{umidita_relativa} %")
    pdf.add_table_row("Fattore Intaglio (Kf)", f"{kf:.2f}", forma_intaglio) 
    if usa_microclima and mat['cat'] in ["Polimeri", "Compositi"]:
        pdf.add_table_row("Fattore Microclima", "Attivo", f"{ore_continue} ore continue")
    pdf.ln(2)

    # --- SEZIONE 3: RISULTATI ---
    pdf.chapter_title("3. Output Analisi Strutturale")
    pdf.add_table_row("Grandezza", "Valore", "Unità", header=True)
    pdf.add_table_row("Limite Fatica Ideale", f"{mat['se_base']}", "MPa")
    pdf.add_table_row("Limite Fatica Reale (Se)", f"{int(se_corr)}", "MPa")
    pdf.add_table_row("Stress Teorico Primario", f"{int(s_eq)}", "MPa")
    if usa_miner:
        pdf.add_table_row("Stress Teorico Secondario", f"{int(s_eq_2)}", "MPa")
    if uploaded_csv is not None or telemetria_manuale: 
        pdf.add_table_row("Spettro Telemetrico", "Attivo", "Dati inseriti")
    pdf.add_table_row("Danno Accumulato", f"{danno_totale*100:.2f} % / anno", "Miner Complessivo")
    pdf.add_table_row("Perdita Rigidità Stimata (1 anno)", f"-{perf_decay:.2f} %", "Decadimento")
    pdf.ln(3)
    
    # --- BOX CONCLUSIVO VITA ---
    pdf.set_font('Arial', 'B', 11)
    if isinstance(years, (int, float)):
        res_text = f"STIMA VITA SICURA COMPONENTE: {years} ANNI"
        color = (0, 128, 0) if years > 5 else (200, 0, 0)
    else:
        res_text = f"RESISTENZA STRUTTURALE: {years}"
        color = (0, 0, 200)

    pdf.set_text_color(*color)
    pdf.cell(0, 8, res_text, 1, 1, 'C')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    # --- SEZIONE 4: GRAFICO WOHLER ---
    pdf.chapter_title("4. Mappa Decadimento Strutturale (Curva S-N)")
    img_path = create_seaborn_temp_image()
    pdf.image(img_path, x=10, w=190)
    os.remove(img_path)
    
    pdf.add_page() 
    
    # --- SEZIONE 5: GRAFICO TORNADO (DIAGNOSTICA) ---
    pdf.chapter_title("5. Diagnostica Sensibilità (Tornado Chart)")
    img_path_tornado = create_tornado_temp_image()
    pdf.image(img_path_tornado, x=10, w=190)
    os.remove(img_path_tornado)
    pdf.ln(3)
    
    # --- SEZIONE 6: OTTIMIZZAZIONE E HYSTERESIS ---
    # NUOVO: Aggiunta Timeline Grafico PDF
    pdf.chapter_title("6. Proiezione Macro-Cicli e Hysteresis")
    img_path_timeline = create_timeline_temp_image()
    pdf.image(img_path_timeline, x=10, w=190)
    os.remove(img_path_timeline)
    pdf.ln(2)

    img_path_2 = create_hysteresis_temp_image()
    pdf.image(img_path_2, x=10, w=190)
    os.remove(img_path_2)

    pdf.ln(5)
    
    if isinstance(years, (int, float)) and years >= 4:
        stato_protesi = "si trova in un range di sicurezza strutturale eccellente"
    elif isinstance(years, (int, float)) and years > 0:
        stato_protesi = "mostra segni di affaticamento che necessiteranno di monitoraggio"
    else:
        stato_protesi = "presenta criticità strutturali che richiedono un upgrade immediato"
        
    pdf.set_font('Arial', 'I', 10)
    pdf.set_text_color(60, 60, 60)
    
    messaggio_atleta = (f"Nota per {atleta_nome}: L'attuale configurazione in {mat_name} {stato_protesi}. "
                        "Ogni millimetro e ogni megapascal della tua protesi sono stati testati per assicurarti stabilità e potenza in ogni movimento. "
                        "La preparazione per i tuoi obiettivi sportivi richiede un trasferimento di forza chirurgico e senza dispersioni: "
                        "monitoreremo questo decadimento per far sì che il gesto atletico rimanga fluido e costante fino alla fine.")
    
    pdf.multi_cell(0, 5, messaggio_atleta)
    
    return pdf.output(dest='S').encode('latin-1')

st.markdown("---")
if st.button("📄 Genera Wohler Sim Report"):
    try:
        pdf_bytes = generate_full_pdf()
        st.download_button(label="Download Report PDF", data=pdf_bytes, file_name=f"Supernova_Report_{atleta_nome}.pdf", mime="application/pdf")
        st.success("Report generato!")
    except Exception as e:
        st.error(f"Errore Generazione PDF: {e}")
