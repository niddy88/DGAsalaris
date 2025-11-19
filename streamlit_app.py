import streamlit as st
from datetime import datetime

st.set_page_config(page_title="DGA Salaris Calculator", layout="centered")
st.title("🇳🇱 DGA Salaris & Dividend Calculator 2025")

# Huidige jaar
jaar = 2025

# Belastingtarieven & bedragen 2025 (bron: Belastingdienst + officiële publicaties)
# Box 1
inkomensbelasting_schijf1_grens = 38703
inkomensbelasting_schijf1_percentage = 0.3693
inkomensbelasting_schijf2_percentage = 0.3995
inkomensbelasting_schijf3_percentage = 0.495

# Box 2 (aanmerkelijk belang)
box2_drempel = 1300000
box2_laag_percentage = 0.246
box2_hoog_percentage = 0.314

# Premies volksverzekeringen (AOW, Anw, Wlz) - alleen voor inkomen tot schijf 1 grens
premie_volksverzekeringen = 0.276

# Algemene heffingskorting & arbeidskorting 2025 (vereenvoudigd, max bedragen)
max_arbeidskorting = 5350
max_heffingskorting = 3070

# DGA minimumloon 2025
minimum_dga_salaris = 56000

tab1, tab2 = st.tabs(["Normaal (bruto → netto)", "Expert (totaal netto gewenst)"])

with tab1:
    st.subheader("Hoeveel salaris + dividend wil je netto overhouden?")
    
    col1, col2 = st.columns(2)
    with col1:
        gewenst_netto_totaal = st.number_input("Totaal netto per jaar (salaris + dividend)", min_value=0, value=100000, step=5000)
    with col2:
        dividend_deel = st.slider("Percentage dat uit dividend komt (%)", 0, 100, 30)

    dividend_netto = gewenst_netto_totaal * (dividend_deel / 100)
    salaris_netto_nodig = gewenst_netto_totaal - dividend_netto

    # Bereken bruto salaris dat nodig is voor het netto salaris deel
    def bereken_bruto_uit_netto(netto):
        if netto <= 0:
            return 0
        # Simpele iteratie om bruto te vinden (nauwkeurig genoeg)
        bruto = netto
        for _ in range(20):
            belasting = 0
            belastbaar = bruto
            
            # Premie volksverzekeringen alleen over eerste schijf
            if belastbaar <= inkomensbelasting_schijf1_grens:
                premie = belastbaar * premie_volksverzekeringen
            else:
                premie = inkomensbelasting_schijf1_grens * premie_volksverzekeringen
            
            # Inkomensbelasting
            if belastbaar <= inkomensbelasting_schijf1_grens:
                belasting = belastbaar * inkomensbelasting_schijf1_percentage
            else:
                belasting = inkomensbelasting_schijf1_grens * inkomensbelasting_sch_n1_percentage + \
                            (belastbaar - inkomensbelasting_schijf1_grens) * inkomensbelasting_schijf2_percentage
            
            # Korting (ruwweg)
            korting = min(max_arbeidskorting + max_heffingskorting, belasting * 0.6)
            
            netto_berekend = bruto - belasting - premie + korting
            
            if netto_berekend < netto:
                bruto += (netto - netto_berekend) * 1.4
            else:
                bruto -= (netto_berekend - netto) * 1.2
        return round(bruto)

    bruto_salaris = max(bereken_bruto_uit_netto(salaris_netto_nodig), minimum_dga_salaris)

    # Box 2 berekening
    bruto_dividend_voor_box2 = dividend_netto / (1 - box2_laag_percentage) if dividend_netto > 0 else 0
    if bruto_dividend_voor_box2 > box2_drempel:
        extra_belasting = (bruto_dividend_voor_box2 - box2_drempel) * (box2_hoog_percentage - box2_laag_percentage)
        bruto_dividend_voor_box2 += extra_belasting / (1 - box2_hoog_percentage)

    st.divider()
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Bruto salaris (min 56k)", f"€{bruto_salaris:,.0f}")
        st.metric("Netto salaris", f"€{salaris_netto_nodig:,.0f}")
    with col_b:
        st.metric("Bruto dividend", f"€{bruto_dividend_voor_box2:,.0f}")
        st.metric("Netto dividend", f"€{dividend_netto:,.0f}")
    with col_c:
        st.metric("Totaal netto", f"€{gewenst_netto_totaal:,.0f}", "✅")
        st.metric("Totaal bruto uitkering", f"€{bruto_salaris + bruto_dividend_voor_box2:,.0f}")

with tab2:
    st.subheader("Expert: ik weet precies wat ik totaal netto wil uitkeren")
    
    totaal_netto_uitkeren = st.number_input("Totaal netto uit te keren (salaris + dividend samen)", min_value=0, value=170000, step=5000)
    
    maand_netto = totaal_netto_uitkeren / 12
    
    st.success(f"✅ Maandelijks netto op je rekening: **€{maand_netto:,.0f}**")
    st.info(f"Jaarlijks netto: €{totaal_netto_uitkeren:,.0f}")
    
    st.caption("Hier wordt geen extra belasting meer afgetrokken – het bedrag dat je invult is echt wat je houdt.")

st.caption(f"Calculatie voor {jaar} – gebaseerd op bekende tarieven per nov 2025. Geen garanties, altijd accountant checken bij grote bedragen.")
