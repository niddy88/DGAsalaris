import streamlit as st

st.set_page_config(page_title="DGA Salaris Calculator 2025", layout="centered")
st.title("🇳🇱 DGA Salaris & Dividend Calculator 2025")

# === Tarieven 2025 ===
JAAR = 2025
MINIMUM_DGA_SALARIS = 56000

# Box 1
SCHIJF1_GRENZ = 38703
SCHIJF1_TARIEF = 0.3693   # incl. premie volksverzekeringen
SCHIJF2_TARIEF = 0.3995
SCHIJF3_TARIEF = 0.495   # (niet gebruikt, want salaris meestal onder schijf 2)

PREMIE_VOLKS = 0.276

# Korting (indicatief)
MAX_ARBEIDSKORTING = 5350
MAX_HEFFINGSKORTING = 3070

# Box 2
BOX2_DREM = 1300000
BOX2_LAAG = 0.246
BOX2_HOOG = 0.314

# === Bruto salaris uit netto salaris berekenen ===
def bruto_voor_netto_salaris(netto_gewenst):
    if netto_gewenst <= 0:
        return 0
    
    bruto = netto_gewenst * 1.5
    for _ in range(25):
        inkomen = bruto
        
        premie = min(inkomen, SCHIJF1_GRENZ) * PREMIE_VOLKS
        
        if inkomen <= SCHIJF1_GRENZ:
            ib = inkomen * SCHIJF1_TARIEF
        else:
            ib = SCHIJF1_GRENZ * SCHIJF1_TARIEF + (inkomen - SCHIJF1_GRENZ) * SCHIJF2_TARIEF
        
        korting = min(MAX_ARBEIDSKORTING + MAX_HEFFINGSKORTING, ib * 0.7)
        
        netto_calc = bruto - ib - premie + korting
        
        if abs(netto_calc - netto_gewenst) < 50:
            break
        elif netto_calc < netto_gewenst:
            bruto += (netto_gewenst - netto_calc) * 1.45
        else:
            bruto -= (netto_calc - netto_gewenst) * 1.2
            
    return max(round(bruto), MINIMUM_DGA_SALARIS)

# === Sidebar ===
with st.sidebar:
    st.header("Algemene instellingen")
    gewenst_totaal_netto = st.number_input("Totaal netto per jaar (salaris + dividend)", 
                                            min_value=50000, value=120000, step=5000)
    dividend_percentage = st.slider("Percentage netto uit dividend", 0, 100, 40)

# Berekeningen
netto_dividend = gewenst_totaal_netto * (dividend_percentage / 100)
netto_salaris = gewenst_totaal_netto - netto_dividend

bruto_salaris = bruto_voor_netto_salaris(netto_salaris)

# Bruto dividend voor netto dividend (Box 2)
bruto_dividend = netto_dividend / (1 - BOX2_LAAG)
if bruto_dividend > BOX2_DREM:
    extra = (bruto_dividend - BOX2_DREM) * (BOX2_HOOG - BOX2_LAAG)
    bruto_dividend += extra / (1 - BOX2_HOOG)
bruto_dividend = round(bruto_dividend)

# Tabs
tab1, tab2 = st.tabs(["🏠 Normaal (bruto → netto)", "⚙️ Expert (exact netto totaal)"])

with tab1:
    st.metric("Totaal gewenst netto per jaar", f"€{gewenst_totaal_netto:,}")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Salaris")
        st.metric("Bruto salaris (min €56k)", f"€{bruto_salaris:,}")
        st.metric("Netto salaris", f"€{netto_salaris:,.0f}")
        st.caption(f"Maand netto ≈ €{round(netto_salaris/12):,}")

    with col2:
        st.subheader("Dividend")
        st.metric("Bruto dividend", f"€{bruto_dividend:,}")
        st.metric("Netto dividend", f"€{netto_dividend:,.0f}")
        st.caption(f"Maand netto ≈ €{round(netto_dividend/12):,}")

    st.divider()
    st.success(f"**Totaal bruto uitkering uit BV: €{bruto_salaris + bruto_dividend:,}**")

with tab2:
    st.subheader("Ik wil exact X netto uitkeren (salaris + dividend samen)")
    totaal_exact = st.number_input("Totaal netto uitkeren", min_value=0, value=170000, step=5000)
    
    maand = totaal_exact / 12
    st.success(f"Maandelijks netto op je rekening: **€{maand:,.0f}**")
    st.info(f"Jaarlijks netto: €{totaal_exact:,} → gewoon delen door 12, geen extra belasting aftrek.")

st.caption(f"Berekend voor {JAAR} – indicatief op basis van tarieven november 2025.")
