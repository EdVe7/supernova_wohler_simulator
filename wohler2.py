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
import json

GOLD_SN = "#D4AF37"
GOLD_SOFT = "#F2E3B3"
BG_LIGHT = "#FFFDF6"
COLOR_RED_ACC = "#D90429"
COLOR_GOLD_ACC = "#FFC300"

st.set_page_config(page_title="Supernova Fatigue Lab", page_icon="🚀", layout="wide")
st.markdown(
    f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .stDeployButton {{display:none;}}
    [data-testid="stToolbar"] {{visibility: hidden !important;}}
    .stApp {{
        background: linear-gradient(180deg, #FFFFFF 0%, {BG_LIGHT} 70%, #F9F1DA 100%);
    }}
    .sn-badge {{
        border: 1px solid {GOLD_SN};
        border-radius: 10px;
        background: #fff;
        color: #6d5312;
        padding: 8px 10px;
        margin-bottom: 6px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# SPLASH
if "splash_done" not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        try:
            st.image("logo.png", use_container_width=True)
        except Exception:
            st.markdown(
                f"<h1 style='text-align:center; color:{GOLD_SN};'>SUPERNOVA</h1>",
                unsafe_allow_html=True,
            )
        st.markdown(
            "<h2 style='text-align:center; font-weight: 900; font-size: 2.2em; letter-spacing: 2px;'>DATA OVER TALENT</h2>",
            unsafe_allow_html=True,
        )
    time.sleep(2)
    placeholder.empty()
    st.session_state["splash_done"] = True

# LOGIN (username + privacy policy)
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

if not st.session_state["authenticated"]:
    st.markdown("<h3 style='text-align:center;'>🔒 Accesso Riservato Lab</h3>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        with st.form("auth_form"):
            username = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            accepted_privacy = st.checkbox("Accetto Privacy Policy e trattamento dati simulazione.")
            submit = st.form_submit_button("ENTRA NEL LAB", use_container_width=True)
            if submit:
                if username and pwd == "supernova26" and accepted_privacy:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.rerun()
                elif not accepted_privacy:
                    st.error("Devi accettare la Privacy Policy.")
                else:
                    st.error("Credenziali non valide.")
        st.markdown(
            "<div class='sn-badge'><b>Privacy Policy:</b> i dati caricati servono esclusivamente a simulazione e report tecnici.</div>",
            unsafe_allow_html=True,
        )
    st.stop()

materials_db = {
    "Titanio Ti-6Al-4V (Piloni/Giunti)": {"uts": 950, "yield": 880, "se_base": 510, "cat": "Metalli"},
    "Titanio Grado 5 ELI (Impianti)": {"uts": 860, "yield": 795, "se_base": 440, "cat": "Metalli"},
    "Nitinol (Lega Memoria di Forma)": {"uts": 1000, "yield": 400, "se_base": 350, "cat": "Metalli"},
    "Fibra Carbonio UD (Lame Corsa)": {"uts": 1500, "yield": 1500, "se_base": 900, "cat": "Compositi"},
    "Matrice Epossidica al Grafene": {"uts": 1700, "yield": 1650, "se_base": 1100, "cat": "Compositi"},
    "Kevlar/Epoxy (Socket Strutturale)": {"uts": 1300, "yield": 1200, "se_base": 750, "cat": "Compositi"},
    "Alluminio 7075-T6 (Ergal - Raccordi)": {"uts": 572, "yield": 503, "se_base": 159, "cat": "Metalli"},
    "PEEK (Componenti Flessibili/Socket)": {"uts": 100, "yield": 100, "se_base": 45, "cat": "Polimeri"},
    "UHMWPE (Polietilene Alta Densità)": {"uts": 40, "yield": 25, "se_base": 15, "cat": "Polimeri"},
    "Acciaio Inox 316L (Viteria/Giunti)": {"uts": 485, "yield": 170, "se_base": 290, "cat": "Metalli"},
}

# Header UI con logo top-left
c_logo, c_title, c_user = st.columns([1, 3, 1.2])
with c_logo:
    try:
        st.image("logo.png", width=120)
    except Exception:
        st.markdown(f"## <span style='color:{GOLD_SN}'>SUPERNOVA</span>", unsafe_allow_html=True)
with c_title:
    st.title("🦾 Supernova Wohler Lab")
    st.markdown("Simulatore affidabile per fatica protesica, prevenzione infortuni e ottimizzazione performance.")
with c_user:
    st.markdown(f"<div class='sn-badge'>Utente: <b>{st.session_state['username']}</b></div>", unsafe_allow_html=True)

with st.sidebar:
    st.header("💾 Snapshot Configurazione")
    uploaded_json = st.file_uploader("Carica Snapshot (JSON)", type=["json"])
    config_override = None
    if uploaded_json is not None:
        try:
            config_override = json.load(uploaded_json)
            st.success("Snapshot applicato.")
        except Exception:
            st.error("Errore lettura JSON.")

    st.header("🏃 Profilazione Atleta Avanzata")
    atleta_nome = st.text_input("Nome Atleta", "Atleta Paralimpico")
    atleta_peso = st.number_input("Peso Atleta (kg)", value=75)
    sport_target = st.text_input("Sport / Obiettivo", "Olimpiadi 2040")
    classe_mobilita = st.selectbox(
        "Classe / Handicap",
        ["Open / Nessuna", "Amputazione Monolaterale", "Amputazione Bilaterale", "Mobilità Ridotta"],
    )

    st.header("🎯 Profili Sportivi Rapidi")
    presets = {
        "Manuale (Nessun Preset)": None,
        "Maratona (Basso Impatto, Alta Freq.)": {"load": "Flessione (Impatto Corsa)", "s_max": 150, "cycles": 1500000},
        "Sprint 100m (Alto Impatto, Bassa Freq.)": {"load": "Flessione (Impatto Corsa)", "s_max": 450, "cycles": 5000},
        "Golf Swing (Multi-assiale)": {"load": "Golf Swing (Multi-assiale)", "s_max": 250, "cycles": 15000, "sigma_ass": 180, "tau_tors": 120},
    }
    preset_choice = st.selectbox("Carica Configurazione", list(presets.keys()))
    p_data = presets[preset_choice]

    st.header("⚙️ Parametri Ambientali")
    mat_name = st.selectbox("Seleziona Materiale Principale", list(materials_db.keys()))
    mat = materials_db[mat_name]
    temp_esercizio = st.slider("Temperatura Operativa (°C)", -20, 60, 25)
    umidita_relativa = st.slider("Umidità Relativa (%)", 0, 100, 0)

    st.header("📉 Fattori Marin")
    surf = st.selectbox("Finitura Superficiale", ["Lucidato", "Lavorato", "Grezzo", "Forgiato"])
    load_options = ["Flessione (Impatto Corsa)", "Assiale (Carico Statico)", "Torsione (Cambio Direzione)", "Golf Swing (Multi-assiale)"]
    def_load_idx = load_options.index(p_data["load"]) if p_data else 0
    load = st.selectbox("Tipo Carico", load_options, index=def_load_idx)
    rel = st.selectbox("Affidabilità Richiesta", ["50%", "90%", "99%", "99.99%"], index=2)

    st.header("📐 Geometria (Intaglio)")
    forma_intaglio = st.selectbox(
        "Geometria Sezione Critica",
        ["Superficie Liscia (Kf=1.0)", "Raccordo Ampio (Kf=1.2)", "Foro Passante (Kf=1.8)", "Spigolo Vivo (Kf=2.5)"],
    )
    kf_dict = {"Superficie Liscia (Kf=1.0)": 1.0, "Raccordo Ampio (Kf=1.2)": 1.2, "Foro Passante (Kf=1.8)": 1.8, "Spigolo Vivo (Kf=2.5)": 2.5}
    kf = kf_dict[forma_intaglio]

    st.header("⚖️ Spettro di Carico Primario")
    usa_biomec = st.checkbox("🧮 Calcolatore Biomeccanico")
    if usa_biomec:
        vel_impatto = st.number_input("Velocità Gesto/Impatto (m/s)", value=45.0)
        grf_multi = st.number_input("Ground Reaction Force (x BW)", value=1.5)
        s_max = float((vel_impatto * 1.5) + (grf_multi * atleta_peso * 0.8))
        s_min = 1.0
        st.info(f"Stress Equivalente Calcolato: {s_max:.1f} MPa")
    elif load == "Golf Swing (Multi-assiale)":
        def_sigma_ass = p_data.get("sigma_ass", 200) if p_data else 200
        def_tau_tors = p_data.get("tau_tors", 150) if p_data else 150
        sigma_ass = st.number_input("Stress Assiale (MPa)", value=def_sigma_ass)
        tau_tors = st.number_input("Stress Taglio/Torsione (MPa)", value=def_tau_tors)
        s_max_eq = math.sqrt(sigma_ass ** 2 + 3 * (tau_tors ** 2))
        st.info(f"Equivalente Von Mises: {s_max_eq:.1f} MPa")
        s_max = st.number_input("Stress Max Eq. (MPa)", value=float(s_max_eq))
        s_min = st.number_input("Stress Min (MPa)", value=1, min_value=1)
    else:
        def_smax = p_data["s_max"] if p_data else 400
        s_max = st.number_input("Stress Max (MPa)", value=def_smax)
        s_min = st.number_input("Stress Min (MPa)", value=1, min_value=1)

    def_cycles = p_data["cycles"] if p_data else 100000
    cycles_yr = st.number_input("Cicli Previsti / Anno", value=def_cycles, step=10000)

    st.header("📊 Telemetria (CSV User-Friendly)")
    st.caption("Carica dati reali allenamento/gara: formato raccomandato `stress,cicli,tipo_sessione`.")
    template_csv = "stress,cicli,tipo_sessione\n250,5000,allenamento\n320,1200,gara\n"
    st.download_button("Scarica template CSV", data=template_csv, file_name="supernova_telemetria_template.csv", mime="text/csv")
    telemetria_manuale = st.text_area("Input Rapido (stress,cicli)", placeholder="250,5000\n300,1000")
    uploaded_csv = st.file_uploader("Carica File CSV", type=["csv"])
    auto_clean_csv = st.checkbox("Ripara automaticamente separatori/colonne", value=True)

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

    # 10 aggiunte orientate professionale/biomeccanica
    st.header("🧠 Add-on Ingegneria Clinica")
    asymmetry_idx = st.slider("Indice Asimmetria Appoggio (%)", 0, 30, 8)
    shock_events = st.number_input("Eventi Shock/mese", 0, 100, 4)
    uncertainty_pct = st.slider("Incertezza modello (%)", 0, 30, 8)
    safety_target = st.slider("Margine sicurezza target (%)", 0, 50, 20)
    compliance_target = st.slider("Compliance atleta obiettivo (%)", 0, 100, 80)
    recovery_quality = st.slider("Qualità recupero percepita (%)", 0, 100, 70)
    maintenance_interval = st.selectbox("Intervallo manutenzione", ["Settimanale", "Bisettimanale", "Mensile"])
    anomaly_guard = st.checkbox("Rilevazione anomalie telemetria", value=True)
    export_csv_report = st.checkbox("Abilita export report CSV", value=True)
    alert_mode = st.selectbox("Modalità allerta", ["Conservativa", "Bilanciata", "Performance"])

    current_config = {
        "mat_name": mat_name, "temp_esercizio": temp_esercizio, "umidita_relativa": umidita_relativa,
        "surf": surf, "load": load, "rel": rel, "forma_intaglio": forma_intaglio, "s_max": s_max, "s_min": s_min,
        "cycles_yr": cycles_yr, "usa_miner": usa_miner, "s_max_2": s_max_2, "s_min_2": s_min_2, "cycles_yr_2": cycles_yr_2
    }
    st.download_button("💾 Scarica Configurazione", data=json.dumps(current_config, indent=4), file_name=f"Setup_{atleta_nome.replace(' ','_')}.json", mime="application/json")

if config_override:
    mat_name = config_override.get("mat_name", mat_name)
    mat = materials_db.get(mat_name, mat)
    temp_esercizio = config_override.get("temp_esercizio", temp_esercizio)
    umidita_relativa = config_override.get("umidita_relativa", umidita_relativa)
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

def get_k_factors(uts, surf_type, load_type, rel_type, mat_cat, temp, hum):
    surfs = {"Lucidato": (1.58, -0.085), "Lavorato": (4.51, -0.265), "Grezzo": (57.7, -0.718), "Forgiato": (272.0, -0.995)}
    ka = 0.9 if mat_cat in ["Compositi", "Polimeri"] else min(surfs[surf_type][0] * (uts ** surfs[surf_type][1]), 1.0)
    kc = {"Flessione (Impatto Corsa)": 1.0, "Assiale (Carico Statico)": 0.85, "Torsione (Cambio Direzione)": 0.59, "Golf Swing (Multi-assiale)": 0.70}.get(load_type, 1.0)
    ke = {"50%": 1.0, "90%": 0.897, "99%": 0.814, "99.99%": 0.702}.get(rel_type, 1.0)
    if mat_cat == "Polimeri":
        kd = 1.0 if temp <= 25 else max(0.2, 1.0 - 0.015 * (temp - 25))
    elif mat_cat == "Compositi":
        kd = 1.0 if temp <= 30 else max(0.5, 1.0 - 0.008 * (temp - 30))
    else:
        kd = 1.0
    kw = (1.0 - 0.002 * hum) if mat_cat in ["Compositi", "Polimeri"] and hum > 0 else 1.0
    return ka, kc, ke, kd, kw

ka, kc, ke, kd, kw = get_k_factors(mat["uts"], surf, load, rel, mat["cat"], temp_esercizio, umidita_relativa)
se_corr = mat["se_base"] * ka * kc * ke * kd * kw
f = 0.9
S1000 = f * mat["uts"]
se_corr = min(se_corr, S1000 * 0.99)
N_end = 1e6 if mat["cat"] not in ["Alluminio", "Polimeri"] else 5e8
b = -(math.log10(S1000 / se_corr)) / (math.log10(N_end) - 3)
log_a = math.log10(S1000) - 3 * b

sigma_a = (s_max - s_min) / 2
sigma_m = (s_max + s_min) / 2
s_eq = (sigma_a / (1 - (sigma_m / mat["uts"])) if sigma_m < mat["uts"] else 9999) * kf
s_eq = s_eq * (1 + asymmetry_idx / 200)

if s_eq <= se_corr:
    Nf_val = float("inf")
elif s_max >= mat["uts"] or s_eq <= 0:
    Nf_val = 1e-5
else:
    Nf_val = 10 ** ((math.log10(s_eq) - log_a) / b)

if usa_miner:
    sigma_a_2 = (s_max_2 - s_min_2) / 2
    sigma_m_2 = (s_max_2 + s_min_2) / 2
    s_eq_2 = (sigma_a_2 / (1 - (sigma_m_2 / mat["uts"])) if sigma_m_2 < mat["uts"] else 9999) * kf
    if s_eq_2 <= se_corr:
        Nf_val_2 = float("inf")
    elif s_max_2 >= mat["uts"] or s_eq_2 <= 0:
        Nf_val_2 = 1e-5
    else:
        Nf_val_2 = 10 ** ((math.log10(s_eq_2) - log_a) / b)
else:
    Nf_val_2 = float("inf")
    s_eq_2 = 0

danno_1 = cycles_yr / Nf_val if Nf_val > 0 else float("inf")
danno_2 = cycles_yr_2 / Nf_val_2 if Nf_val_2 > 0 else float("inf")

def parse_friendly_csv(uploaded):
    if uploaded is None:
        return 0.0, None
    try:
        df = pd.read_csv(uploaded)
        if auto_clean_csv:
            df.columns = [str(c).strip().lower() for c in df.columns]
        if "stress" in df.columns and "cicli" in df.columns:
            pass
        elif df.shape[1] >= 2:
            df = df.iloc[:, :3]
            df.columns = ["stress", "cicli", "tipo_sessione"][:df.shape[1]]
        else:
            raise ValueError("Colonne insufficienti.")

        if "tipo_sessione" not in df.columns:
            df["tipo_sessione"] = "n/a"
        df = df.dropna(subset=["stress", "cicli"])
        df["stress"] = pd.to_numeric(df["stress"], errors="coerce")
        df["cicli"] = pd.to_numeric(df["cicli"], errors="coerce")
        df = df.dropna(subset=["stress", "cicli"])
        danno = 0.0
        for _, row in df.iterrows():
            stress_csv = float(row["stress"]) * kf
            cicli_csv = float(row["cicli"])
            if stress_csv <= se_corr:
                nf_csv = float("inf")
            elif stress_csv >= mat["uts"] or stress_csv <= 0:
                nf_csv = 1e-5
            else:
                nf_csv = 10 ** ((math.log10(stress_csv) - log_a) / b)
            danno += cicli_csv / nf_csv if nf_csv > 0 else float("inf")
        return danno, df
    except Exception as e:
        st.sidebar.error(f"CSV non valido: {e}")
        return 0.0, None

danno_csv, df_csv_preview = parse_friendly_csv(uploaded_csv)
danno_manuale = 0.0
if telemetria_manuale:
    try:
        for riga in telemetria_manuale.split("\n"):
            if riga.strip():
                vals = riga.split(",")
                if len(vals) >= 2:
                    stress_man = float(vals[0].strip()) * kf
                    cicli_man = float(vals[1].strip())
                    if stress_man <= se_corr:
                        nf_man = float("inf")
                    elif stress_man >= mat["uts"] or stress_man <= 0:
                        nf_man = 1e-5
                    else:
                        nf_man = 10 ** ((math.log10(stress_man) - log_a) / b)
                    danno_manuale += cicli_man / nf_man if nf_man > 0 else float("inf")
    except Exception:
        st.sidebar.error("Errore formato input manuale.")

danno_shock = shock_events * 50 / max(Nf_val, 1)
danno_totale = danno_1 + danno_2 + danno_csv + danno_manuale + danno_shock

if danno_totale >= 1 or s_max >= mat["uts"] or (usa_miner and s_max_2 >= mat["uts"]):
    years, Nf = 0, 0
elif danno_totale == 0:
    years, Nf = "Infinito", "Infinito"
else:
    years = round(1 / danno_totale, 2)
    Nf = int(Nf_val)

danno_annuo = danno_totale * 100 if isinstance(years, (int, float)) and years != 0 else 0.0
perf_decay = min(danno_annuo * 0.5, 100.0)

# 10 aggiunte: indicatori avanzati
recovery_index = max(0.0, min(100.0, recovery_quality - perf_decay * 0.2))
compliance_score = max(0.0, min(100.0, compliance_target - asymmetry_idx * 0.8))
risk_score = min(100.0, danno_annuo * 1.2 + asymmetry_idx + uncertainty_pct)
safe_margin = max(0.0, ((se_corr - s_eq) / max(se_corr, 1)) * 100)
if alert_mode == "Conservativa":
    risk_score = risk_score * 1.15
elif alert_mode == "Performance":
    risk_score = risk_score * 0.9
risk_class = "Basso" if risk_score < 30 else ("Medio" if risk_score < 65 else "Alto")
maintenance_note = {
    "Settimanale": "Ispezione socket + fissaggi ogni 7 giorni",
    "Bisettimanale": "Ispezione ogni 14 giorni",
    "Mensile": "Ispezione ogni 30 giorni",
}[maintenance_interval]

if anomaly_guard and df_csv_preview is not None and not df_csv_preview.empty:
    anom = df_csv_preview["stress"].mean() + 2.5 * df_csv_preview["stress"].std(ddof=0)
    anomaly_count = int((df_csv_preview["stress"] > anom).sum())
else:
    anomaly_count = 0

n_x = np.logspace(3, 8, 50)
s_y = (10 ** log_a) * (n_x ** b) if isinstance(Nf, int) and Nf > 0 else np.zeros_like(n_x)
s_y = np.maximum(s_y, se_corr)

st.markdown("### 🚥 Dashboard Operativa")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Stress Eq.", f"{int(s_eq)} MPa")
c2.metric("Limite Fatica", f"{int(se_corr)} MPa")
c3.metric("Vita Stimata", f"{years} anni" if isinstance(years, (int, float)) else years)
c4.metric("Rischio", risk_class)
c5.metric("Margine Sicurezza", f"{safe_margin:.1f}%")

c6, c7, c8 = st.columns(3)
c6.metric("Recovery Index", f"{recovery_index:.1f}%")
c7.metric("Compliance Score", f"{compliance_score:.1f}%")
c8.metric("Anomalie Telemetria", anomaly_count)

if df_csv_preview is not None:
    with st.expander("Anteprima CSV normalizzato"):
        st.dataframe(df_csv_preview, use_container_width=True)

fig = go.Figure()
fig.add_trace(go.Scatter(x=n_x, y=s_y, name=f"Curva S-N ({mat_name})", line=dict(color=GOLD_SN, width=3)))
if isinstance(Nf, int) and Nf > 0:
    fig.add_trace(go.Scatter(x=[Nf], y=[s_eq], mode="markers", marker=dict(color=COLOR_RED_ACC, size=12), name="Carico Primario"))
fig.update_layout(xaxis_type="log", title="Curva di Fatica (Wöhler) - Supernova", height=420)
st.plotly_chart(fig, use_container_width=True)

if risk_class == "Alto":
    st.error(f"⚠️ Rischio ALTO. {maintenance_note}")
elif risk_class == "Medio":
    st.warning(f"Monitoraggio consigliato. {maintenance_note}")
else:
    st.success("Setup stabile per il ciclo attuale.")


class TablePDF(FPDF):
    def header(self):
        try:
            self.image("logo.png", 10, 8, 20)
        except Exception:
            pass
        self.ln(8)  # spazio prima del titolo richiesto
        self.set_font("Arial", "B", 14)
        self.set_text_color(212, 175, 55)
        self.cell(0, 6, "SUPERNOVA LAB - PROSTHETICS FATIGUE REPORT", 0, 1, "C")
        self.line(10, 20, 200, 20)
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(128)
        self.cell(0, 5, "Powered by Supernova Sport Science", 0, 0, "C")
        self.cell(0, 5, f"Pagina {self.page_no()}", 0, 0, "R")

    def chapter_title(self, title):
        self.set_font("Arial", "B", 11)
        self.set_fill_color(246, 238, 209)
        self.set_text_color(0, 0, 0)
        self.cell(0, 6, title, 0, 1, "L", 1)
        self.ln(1)

    def add_table_row(self, col1, col2, col3, header=False):
        self.set_font("Arial", "B" if header else "", 9)
        self.cell(85, 5, str(col1), 1)
        self.cell(55, 5, str(col2), 1)
        self.cell(50, 5, str(col3), 1, 0, "C")
        self.ln()


def create_seaborn_temp_image():
    plt.figure(figsize=(9, 4))
    sns.set_theme(style="whitegrid")
    ax = sns.lineplot(x=n_x, y=s_y, color=GOLD_SN, linewidth=2.5, label=mat_name)
    ax.set_xscale("log")
    plt.axhline(se_corr, color=COLOR_GOLD_ACC, linestyle="--")
    if isinstance(Nf, int) and Nf > 0:
        plt.scatter([Nf], [s_eq], color=COLOR_RED_ACC, zorder=5, s=120, label="Primario")
    plt.title("Analisi Strutturale Combinata", fontsize=12, fontweight="bold")
    plt.legend()
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(tmp_file.name, format="png", bbox_inches="tight", dpi=300)
    plt.close()
    return tmp_file.name


def generate_full_pdf():
    pdf = TablePDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 5, f"Utente: {st.session_state['username']} | Atleta: {atleta_nome} ({atleta_peso} kg)", 0, 1)
    pdf.cell(0, 5, f"Target: {sport_target} | Data: {datetime.datetime.now().strftime('%d/%m/%Y')}", 0, 1)
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 5, f"Classe/Handicap: {classe_mobilita}", 0, 1)
    pdf.ln(2)

    pdf.chapter_title("1. Parametri Configurazione")
    pdf.add_table_row("Parametro", "Valore", "Note", header=True)
    pdf.add_table_row("Materiale", mat_name, mat["cat"])
    pdf.add_table_row("UTS", mat["uts"], "MPa")
    pdf.add_table_row("Yield", mat["yield"], "MPa")
    pdf.add_table_row("Cicli/Anno", f"{cycles_yr:,}", "Primario")

    pdf.chapter_title("2. Risultati Ingegneristici")
    pdf.add_table_row("Metrica", "Valore", "Unità", header=True)
    pdf.add_table_row("Se corretto", f"{int(se_corr)}", "MPa")
    pdf.add_table_row("Stress Eq.", f"{int(s_eq)}", "MPa")
    pdf.add_table_row("Danno annuo", f"{danno_annuo:.2f}", "%")
    pdf.add_table_row("Vita stimata", f"{years}", "anni")
    pdf.add_table_row("Rischio", risk_class, "classe")
    pdf.add_table_row("Recovery Index", f"{recovery_index:.1f}", "%")
    pdf.add_table_row("Compliance Score", f"{compliance_score:.1f}", "%")
    pdf.add_table_row("Maintenance", maintenance_note, "piano")
    pdf.add_table_row("Anomalie CSV", anomaly_count, "conteggio")

    pdf.chapter_title("3. Curva Wöhler")
    img_path = create_seaborn_temp_image()
    pdf.image(img_path, x=10, w=190)
    os.remove(img_path)
    return pdf.output(dest="S").encode("latin-1")


st.markdown("---")
if st.button("📄 Genera Wohler Sim Report"):
    try:
        pdf_bytes = generate_full_pdf()
        st.download_button(
            label="Download Report PDF",
            data=pdf_bytes,
            file_name=f"Supernova_Report_{atleta_nome}.pdf",
            mime="application/pdf",
        )
        st.success("Report generato!")
    except Exception as e:
        st.error(f"Errore Generazione PDF: {e}")

if export_csv_report:
    export_df = pd.DataFrame(
        [
            {"metrica": "stress_eq_mpa", "valore": round(float(s_eq), 2)},
            {"metrica": "se_corr_mpa", "valore": round(float(se_corr), 2)},
            {"metrica": "danno_annuo_percent", "valore": round(float(danno_annuo), 2)},
            {"metrica": "vita_anni", "valore": years if isinstance(years, (int, float)) else str(years)},
            {"metrica": "risk_class", "valore": risk_class},
            {"metrica": "recovery_index", "valore": round(float(recovery_index), 2)},
            {"metrica": "compliance_score", "valore": round(float(compliance_score), 2)},
        ]
    )
    st.download_button("📥 Export KPI CSV", export_df.to_csv(index=False), "supernova_kpi_export.csv", "text/csv")

st.download_button(
    "📦 Export tecnico JSON",
    data=json.dumps(
        {
            "user": st.session_state["username"],
            "athlete": atleta_nome,
            "timestamp": datetime.datetime.now().isoformat(),
            "results": {
                "s_eq": float(s_eq),
                "se_corr": float(se_corr),
                "years": years if isinstance(years, (int, float)) else str(years),
                "risk_class": risk_class,
                "maintenance_note": maintenance_note,
            },
        },
        indent=2,
        ensure_ascii=False,
    ),
    file_name="supernova_export.json",
    mime="application/json",
)




