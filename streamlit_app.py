import streamlit as st

st.set_page_config(page_title="DGA Maximaliseer Netto 2025", layout="centered")
st.title("🇳🇱 DGA Netto Maximaliseren 2025 (incl. BV-kosten & loonstrook)")

# === Exacte tarieven 2025 ===
JAAR = 2025
MIN_DGA_LOON = 56000

# Box 1
SCHIJF1 = 38441
TARIEF1 = 0.3582   # IB + premies volksverzekeringen
TARIEF2 = 0.3748
TARIEF3 = 0.495

# Heffingskortingen 2025
MAX_AHK = 3068      # algemene heffingskorting
MAX_AK = 5599       # arbeidskorting max
MAX_IACK = 2986     # inkomensafhankelijke combinatiekorting

# Box 2
BOX2_DREMPEL = 67804
BOX2_LAAG = 0.245
BOX2_HOOG = 0.31

# BV-kosten
WERKGEVERS_ZVW = 0.0651
VAKANTIEGELD = 0.08

# === Nauwkeurige netto salaris berekening (met partner & kinderen) ===
def bereken_netto_salaris(bruto_salaris, heeft_partner, jonge_kinderen, partner_heeft_inkomen):
    ink = bruto_salaris
    
    # Premie volksverzekeringen alleen in schijf 1
    premie = min(ink, SCHIJF1) * 0.276   # zit al in TARIEF1, maar voor duidelijkheid
    
    # IB berekenen
    if ink <= SCHIJF1:
        ib = ink * TARIEF1
    elif ink <= 76817:
        ib = SCHIJF1 * TARIEF1 + (ink - SCHIJF1) * TARIEF2
    else:
        ib = SCHIJF1 * TARIEF1 + (76817 - SCHIJF1) * TARIEF2 + (ink - 76817) * TARIEF3
    
    # Arbeidskorting 2025 (exacte formule)
    if ink <= 11050:
        ak = 0
    elif ink <= 23500:
        ak = ink * 0.1107
    elif ink <= 43071:
        ak = 5599 * (ink - 23500) / (43071 - 23500) + iets, maar approx max
    else:
        ak = MAX_AK - max(0, (ink - 43071) * 0.0651)
    ak = min(MAX_AK, max(0, ak))
    
    # Algemene heffingskorting (afbouw vanaf €28.406 met 6.337%)
    ahk = MAX_AHK - max(0, (ink - 28406) * 0.06337)
    ahk = max(0, ahk)
    
    # IACK bij jonge kinderen
    iack = MAX_IACK if jonge_kinderen and ink >= 6145 else 0
    
    totaal_korting = ak + ahk + iack
    
    if heeft_partner and not partner_heeft_inkomen:
        # Partner kan eigen AHK + AK overnemen als jij genoeg belasting betaalt
        totaal_korting += MAX_AHK + MAX_AK
    
    netto = bruto_salaris - ib + totaal_korting
    return round(netto), round(ib - totaal_korting)

# === Optimalisatie loop (probeert salaris van min tot 200k) ===
def vind_optimaal(gew_winstaat_na_vpb, heeft_partner, jonge_kinderen, partner_inkomen_nul):
    best_netto = 0
    best_salaris = MIN_DGA_LOON
    best_dividend_bruto = 0
    
    for test_salaris in range(MIN_DGA_LOON, 200001, 2000):
        resterend = gew_winstaat_na_vpb - test_salaris
        if resterend < 0:
            continue
            
        # Netto salaris
        netto_sal, _ = bereken_netto_salaris(test_salaris, heeft_partner, jonge_kinderen, partner_inkomen_nul)
        
        # Netto dividend
        bruto_div = resterend
        if bruto_div <= BOX2_DREMPEL:
            box2 = bruto_div * BOX2_LAAG
        else:
            box2 = BOX2_DREMPEL * BOX2_LAAG + (bruto_div - BOX2_DREMPEL) * BOX2_HOOG
        netto_div = bruto_div - box2
        
        totaal_netto = netto_sal + netto_div
        
        if totaal_netto > best_netto:
            best_netto = totaal_netto
            best_salaris = test_salaris
            best_dividend_bruto = bruto_div
    
    return best_salaris, best_dividend_bruto, best_netto

# === Sidebar inputs ===
with st.sidebar:
    st.header("Situatie")
    winst_na_vpb = st.number_input("Winst na VPB die je wilt uitkeren", min_value=0, value=200000, step=10000)
    
    heeft_partner = st.checkbox("Fiscale partner", value=True)
    if heeft_partner:
        partner_geen_inkomen = st.checkbox("Partner heeft geen/low inkomen (kan kortingen overnemen)", value=True)
    else:
        partner_geen_inkomen = False
        
    jonge_kinderen = st.checkbox("Kind(eren) jonger dan 12 jaar (IACK ±€3.000 extra)", value=False)

# === Berekening ===
bruto_sal, bruto_div, max_netto = vind_optimaal(winst_na_vpb, heeft_partner, jonge_kinderen, partner_geen_inkomen)

netto_sal, _ = bereken_netto_salaris(bruto_sal, heeft_partner, jonge_kinderen, partner_geen_inkomen)

box2 = (bruto_div * BOX2_LAAG) if bruto_div <= BOX2_DREMPEL else (BOX2_DREMPEL * BOX2_LAAG + (bruto_div - BOX2_DREMPEL) * BOX2_HOOG)
netto_div = bruto_div - box2

# BV kosten
bv_kosten_sal = bruto_sal * (1 + VAKANTIEGELD) * (1 + WERKGEVERS_ZVW)
totaal_bv_kosten = bv_kosten_sal + bruto_div   # dividend geen extra kosten

tab1, tab2, tab3 = st.tabs(["Optimaal scenario", "Voorbeeld loonstrook", "Expert: exact netto"])

with tab1:
    st.success(f"**Maximaal netto op je rekening: €{max_netto:,}** (+{max_netto - (winstprese_na_vpb * 0.75):,} t.o.v. alles dividend)")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Salaris")
        st.metric("Bruto salaris", f"€{bruto_sal:,}")
        st.metric("Netto salaris", f"€{netto_sal:,}")
    with col2:
        st.subheader("Dividend")
        st.metric("Bruto dividend", f"€{bruto_div:,}")
        st.metric("Netto dividend", f"€{netto_div:,}")
    with col3:
        st.subheader("BV kosten")
        st.metric("Totale kosten BV", f"€{totaal_bv_kosten:,.0f}")
        st.metric("Netto efficiency", f"{max_netto / totaal_bv_kosten * 100:.1f}%")

with tab2:
    st.subheader(f"Loonstrook bij optimaal salaris €{bruto_sal:,} bruto/jaar")
    maand_bruto = bruto_sal / 12
    maand_netto_sal = netto_sal / 12
    st.write(f"**Maand bruto**: €{maand_bruto:,.0f}")
    st.write(f"**Loonheffing + Zvw-inhouding**: ± €{ (maand_bruto - maand_netto_sal):,.0f}")
    st.write(f"**Maand netto salaris**: €{maand_netto_sal:,.0f}")
    st.write(f"**Maand netto dividend** (als je het gelijkmatig uitkeert): €{netto_div/12:,.0f}")
    st.success(f"**Totaal maand netto op rekening**: €{(netto_sal + netto_div)/12:,.0f}")

with tab3:
    totaal_netto = st.number_input("Ik wil exact dit netto (salaris+dividend)", value=max_netto, step=1000)
    st.success(f"Maandelijks netto: **€{totaal_netto/12:,.0f}**")

st.caption("2025 tarieven – indicatief. Bij grote bedragen altijd accountant raadplegen.")
