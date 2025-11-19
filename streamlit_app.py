import streamlit as st

st.set_page_config(page_title="DGA Netto Maximaliseren 2026", layout="centered")
st.title("🇳🇱 DGA Netto Maximaliseren 2026")

# === Tarieven 2026 (definitief Belastingplan 2026) ===
JAAR = 2026
MIN_DGA_SALARIS = 58000

# Box 1
SCHIJF1_GRENZ = 38986
TARIEF1 = 0.3594   # IB + premies volksverzekeringen
TARIEF2 = 0.3765
SCHIJF2_GRENZ = 76817  # schijf 3 begint hier

# Heffingskortingen 2026
MAX_AHK = 3126
MAX_AK = 5712
MAX_IACK = 3048

# Box 2
BOX2_DREMPEL = 67804
BOX2_LAAG = 0.245
BOX2_HOOG = 0.31

# BV-kosten
ZVW_WERKGEVER = 0.0651
VAKANTIEGELD = 0.08

# === Netto salaris (exact met partner & kinderen) ===
def netto_salaris(bruto_jaar, partner, partner_geen_inkomen, jonge_kinderen):
    ink = bruto_jaar

    # IB + premies
    if ink <= SCHIJF1_GRENZ:
        ib_pvv = ink * TARIEF1
    elif ink <= SCHIJF2_GRENZ:
        ib_pvv = SCHIJF1_GRENZ * TARIEF1 + (ink - SCHIJF1_GRENZ) * TARIEF2
    else:
        ib_pvv = SCHIJF1_GRENZ * TARIEF1 + (SCHIJF2_GRENZ - SCHIJF1_GRENZ) * TARIEF2 + (ink - SCHIJF2_GRENZ) * 0.495

    # Arbeidskorting (vereenvoudigd maar dichtbij)
    if ink <= 40426:
        ak = min(MAX_AK, ink * 0.1413)
    else:
        ak = MAX_AK - max(0, (ink - 40426) * 0.065)

    # Algemene heffingskorting
    ahk = max(0, MAX_AHK - max(0, (ink - 28900) * 0.0642))

    # Combinatiekorting
    iack = MAX_IACK if jonge_kinderen and ink >= 6200 else 0

    korting = ak + ahk + iack
    if partner and partner_geen_inkomen:
        korting += MAX_AHK  # partner kan AHK overnemen

    netto = bruto_jaar - ib_pvv + korting
    return round(netto), round(ib_pvv - korting)

# === Optimalisatie loop ===
def optimaliseer(winst_na_vpb, partner, partner_geen_ink, jonge_kinderen):
    best_netto = 0
    best_sal = MIN_DGA_SALARIS
    best_div = 0

    for sal in range(MIN_DGA_SALARIS, min(winst_na_vpb + 10000, 300000), 1500):
        div = winst_na_vpb - sal
        if div < 0:
            continue

        netto_sal, _ = netto_salaris(sal, partner, partner_geen_ink, jonge_kinderen)

        box2 = div * BOX2_LAAG if div <= BOX2_DREMPEL else BOX2_DREMPEL * BOX2_LAAG + (div - BOX2_DREMPEL) * BOX2_HOOG
        netto_div = div - box2

        totaal = netto_sal + netto_div
        if totaal > best_netto:
            best_netto = totaal
            best_sal = sal
            best_div = div

    return best_sal, best_div, best_netto

# === Sidebar ===
with st.sidebar:
    st.header("Jouw situatie 2026")
    winst = st.number_input("Winst na VPB om uit te keren", min_value=100000, value=250000, step=10000)
    partner = st.checkbox("Fiscale partner", value=True)
    partner_geen_ink = False
    if partner:
        partner_geen_ink = st.checkbox("Partner geen/low inkomen (extra korting)", value=True)
    kinderen = st.checkbox("Kind(eren) <12 jaar (IACK +€3.048)", value=False)

# === Bereken ===
sal, div, max_netto = optimaliseer(winst, partner, partner_geen_ink, kinderen)
netto_sal, _ = netto_salaris(sal, partner, partner_geen_ink, kinderen)
box2 = div * BOX2_LAAG if div <= BOX2_DREMPEL else BOX2_DREMPEL * BOX2_LAAG + (div - BOX2_DREMPEL) * BOX2_HOOG
netto_div = div - box2

bv_kosten_sal = sal * (1 + VAKANTIEGELD) * (1 + ZVW_WERKGEVER)
totaal_bv_kosten = round The(bv_kosten_sal + div)

tab1, tab2, tab3 = st.tabs(["Optimaal scenario", "Loonstrook", "Handmatig netto"])

with tab1:
    st.success(f"**Maximaal netto in 2026: €{max_netto:,}**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Salaris")
        st.metric("Bruto salaris", f"€{sal:,}")
        st.metric("Netto salaris", f"€{netto_sal:,}")
    with col2:
        st.subheader("Dividend")
        st.metric("Bruto dividend", f"€{div:,}")
        st.metric("Netto dividend", f"€{netto_div:,}")
    with col3:
        st.subheader("BV totaal")
        st.metric("Totale kosten BV", f"€{totaal_bv_kosten:,}")
        st.metric("Netto rendement", f"{(max_netto / winst * 100):.1f}%")

with tab2:
    st.subheader(f"Voorbeeld maandloonstrook (€{sal:,} bruto/jaar)")
    st.write(f"Maand bruto: **€{sal/12:,.0f}**")
    st.write(f"Maand netto salaris: **€{netto_sal/12:,.0f}**")
    st.write(f"Maand netto dividend (gem.): **€{netto_div/12:,.0f}**")
    st.success(f"Totaal per maand op je rekening: **€{max_netto/12:,.0f}**")

with tab3:
    hand = st.number_input("Ik wil exact dit netto totaal", value=max_netto, step=1000)
    st.success(f"Dan ≈ **€{hand/12:,.0f}** per maand")

st.caption("2026 tarieven – indicatief, altijd accountant checken bij écht grote bedragen.")
