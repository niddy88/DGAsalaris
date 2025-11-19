# app.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="DGA Salaris & Dividend 2026", layout="centered")
st.title("💰 DGA Salaris + Dividend Calculator 2026")
st.markdown("##### Nu met échte maandelijkse uitkering, vakantiegeld & 13e maand (expert-modus)")

# ===================================================================
# === Belastingtarieven 2026 (stand november 2025) ===
# ===================================================================
IB_SCHIJVEN_2026 = [(0, 38_041, 0.3695), (38_041, 76_934, 0.3695), (76_934, None, 0.495)]
AOW_FRANCHISE = 18_760
AOW_PREMIECENTAGE = 0.178
WLZ_ALLEEN = 0.0622

ARBEIDSKORTING = [
    (0, 12_570, lambda x: 0.06336 * x),
    (12_570, 24_338, lambda x: 795 + 0.29803 * (x - 12_570)),
    (24_338, 40_527, lambda x: 4_333),
    (40_527, 130_997, lambda x: 4_333 - 0.0665 * (x - 40_527)),
    (130_997, None, lambda x: 0)
]

AHK_MAX = 3_070
AHK_AFBOW_START = 24_338
AHK_AFBOW_EINDE = 76_934

BOX2_SCHIJVEN_2026 = [(0, 66_700, 0.245), (66_700, None, 0.318)]
VPB_SCHIJVEN_2026 = [(0, 200_000, 0.19), (200_000, None, 0.258)]
MKB_VRIJSTELLING = 0.127
EXCESSIEF_GRENS = 500_000

# ===================================================================
# === Hulpfunctions (blijven grotendeels hetzelfde) ===
# ===================================================================
def arbeidskorting(inkomen):
    for min_val, max_val, formule in ARBEIDSKORTING:
        if max_val is None or inkomen <= max_val:
            return formule(inkomen)
    return 0

def algemene_heffingskorting(dga_inkomen, partner_inkomen=0, fiscaal_partner=False):
    if not fiscaal_partner or partner_inkomen == 0:
        if dga_inkomen <= AHK_AFBOW_START:
            return AHK_MAX
        elif dga_inkomen <= AHK_AFBOW_EINDE:
            return AHK_MAX * (AHK_AFBOW_EINDE - dga_inkomen) / (AHK_AFBOW_EINDE - AHK_AFBOW_START)
        else:
            return 0
    else:
        laagste = min(dga_inkomen, partner_inkomen)
        return max(0, AHK_MAX - (laagste * 0.04))

def vpb_berekenen(winst):
    belasting = 0
    rest = winst
    for onder, boven, tarief in VPB_SCHIJVEN_2026:
        schijf = rest if boven is None else min(rest, boven - onder)
        belasting += schijf * tarief
        rest -= schijf
        if rest <= 0: break
    return round(belasting)

def box2(dividend):
    belasting = 0
    rest = dividend
    for onder, boven, tarief in BOX2_SCHIJVEN_2026:
        schijf = rest if boven is None else min(rest, boven - onder)
        belasting += schijf * tarief
        rest -= schijf
        if rest <= 0: break
    return round(belasting)

def excessief_lenen(rc_schuld_2025):
    bovenmatig = max(0, rc_schuld_2025 - EXCESSIEF_GRENS)
    if bovenmatig == 0:
        return 0, 0
    return bovenmatig, box2(bovenmatig)

# ===================================================================
# === Sidebar ===
# ===================================================================
st.sidebar.header("📊 Basis")
totaal_uitkeren = st.sidebar.number_input("Totaal uitkeren in 2026 (salaris + dividend)", min_value=50_000, value=250_000, step=10_000)
min_dga_loon_jaar = st.sidebar.number_input("Minimum gebruikelijk loon 2026", value=56_000, step=1_000)

st.sidebar.header("💸 Maanduitkering & extra's")
vakantiegeld = st.sidebar.checkbox("Vakantiegeld (8%) netto ontvangen in mei/juni", value=True)
dertiende_maand = st.sidebar.checkbox("13e maand netto ontvangen in december", value=False)

st.sidebar.header("🔧 Overige")
bijtelling = st.sidebar.number_input("Bijtelling leaseauto (bruto/jaar)", 0, 60_000, 0, 1_000)
aow_leeftijd = st.sidebar.checkbox("AOW-leeftijd in 2026")
fiscaal_partner = st.sidebar.checkbox("Fiscale partner", value=True)
partner_inkomen = 0
if fiscaal_partner:
    partner_inkomen = st.sidebar.number_input("Box 1-inkomen partner", 0, 200_000, 40_000, 5_000)

rc_schuld_2025 = st.sidebar.number_input("Rekening-courant schuld 31-12-2025", 0, 2_000_000, 0, 10_000)

# ===================================================================
# === NIEUWE: Berekening maandbedrag + vakantiegeld + 13e maand ===
# ===================================================================
def bereken_maandelijks(totaal_salaris_bruto_jaar, vakantiegeld_wel=True, dertiende_wel=False):
    basis_maand = totaal_salaris_bruto_jaar / 12

    if vakantiegeld_wel and dertiende_wel:
        # 12 + 1 (vak) + 1 (13e) = 14 betalingen
        maand_bruto = totaal_salaris_bruto_jaar / 14
        vak_bruto = maand_bruto
        dec_bruto = maand_bruto * 2  # december = normaal + 13e
        schema = {f"Jan-Nov": round(maand_bruto), "December": round(dec_bruto), "Mei/Juni": round(vak_bruto)}
        return schema, maand_bruto

    elif vakantiegeld_wel:
        # 13 betalingen (12 + vakantiegeld)
        maand_bruto = totaal_salaris_bruto_jaar / 13
        vak_bruto = maand_bruto
        schema = {f"Jan-Apr + Jul-Nov": round(maand_bruto), "Mei/Juni": round(vak_bruto), "December": round(maand_bruto)}
        return schema, maand_bruto

    else:
        # Gewoon 12x
        maand_bruto = round(totaal_salaris_bruto_jaar / 12)
        schema = {f"Elke maand": maand_bruto}
        return schema, maand_bruto

# ===================================================================
# === Hoofdberekening (jaar) ===
# ===================================================================
def bereken_jaar(salaris_jaar, dividend_jaar):
    arbeid_inkomen = salaris_jaar + bijtelling

    # VPB + MKB
    totaal_bv = salaris_jaar + dividend_jaar
    vpb = vpb_berekenen(totaal_bv)
    mkb_vrij = round((totaal_bv - vpb) * MKB_VRIJSTELLING / (1 + MKB_VRIJSTELLING))

    # Box 1
    ib = 0
    rest = arbeid_inkomen
    for onder, boven, tarief in IB_SCHIJVEN_2026:
        schijf = rest if boven is None else min(rest, boven - onder)
        ib += schijf * tarief
        rest -= schijf
        if rest <= 0: break

    premie = max(0, arbeid_inkomen - AOW_FRANCHISE) * (WLZ_ALLEEN if aow_leeftijd else AOW_PREMIECENTAGE)
    ak = arbeidskorting(arbeid_inkomen)
    ahk = algemene_heffingskorting(arbeid_inkomen, partner_inkomen if fiscaal_partner else 0, fiscaal_partner)
    ib_premie = max(0, ib + premie - ak - ahk)
    netto_salaris_jaar = salaris_jaar - ib_premie + bijtelling

    # Dividend + excessief
    box2_div = box2(dividend_jaar)
    bovenmatig, box2_exc = excessief_lenen(rc_schuld_2025)

    totaal_belasting = vpb + ib_premie + box2_div + box2_exc
    totaal_netto = netto_salaris_jaar + (dividend_jaar - box2_div) - box2_exc

    return {
        "bruto_salaris": salaris_jaar,
        "netto_salaris_jaar": round(netto_salaris_jaar),
        "dividend": dividend_jaar,
        "netto_dividend": dividend_jaar - box2_div,
        "vpb": vpb,
        "ib_premie": round(ib_premie),
        "box2": box2_div + box2_exc,
        "bovenmatig": bovenmatig,
        "totaal_belasting": round(totaal_belasting),
        "totaal_netto": round(totaal_netto),
        "percentage": round(totaal_belasting / totaal_bv * 100, 1)
    }

# ===================================================================
# === Tabs ===
# ===================================================================
tab1, tab2 = st.tabs(["🟢 Simpel (minimumloon + dividend)", "🔴 Expert (maanduitkering + extra's)"])

with tab1:
    resultaat = bereken_jaar(min_dga_loon_jaar, totaal_uitkeren - min_dga_loon_jaar)
    st.metric("Totaal netto 2026", f"€{resultaat['totaal_netto']:,}")
    st.write(f"Effectief belasting: **{resultaat['percentage']} %**")
    if resultaat['bovenmatig'] > 0:
        st.error(f"Excessief lenen: €{resultaat['bovenmatig']:,} → extra €{resultaat['box2'] - box2(resultaat['dividend']):,} box 2")

with tab2:
    st.subheader("🎯 Stel je ideale maandschema samen")

    bruto_salaris_jaar = st.slider("Bruto jaarsalaris (inclusief eventueel vakantiegeld/13e)", 
                                   min_value=min_dga_loon_jaar, max_value=totaal_uitkeren, 
                                   value=max(min_dga_loon_jaar, 80_000), step=2_000)

    dividend_jaar = totaal_uitkeren - bruto_salaris_jaar

    res = bereken_jaar(bruto_salaris_jaar, dividend_jaar)

    col1, col2, col3 = st.columns(3)
    col1.metric("Netto salaris jaar", f"€{res['netto_salaris_jaar']:,}")
    col2.metric("Netto dividend", f"€{res['netto_dividend']:,}")
    col3.metric("TOTAAL NETTO 2026", f"€{res['totaal_netto']:,}", 
                delta=f"{res['totaal_netto'] - bereken_jaar(min_dga_loon_jaar, totaal_uitkeren - min_dga_loon_jaar)['totaal_netto']:,}")

    st.markdown("### Jouw maandelijkse uitkering")
    schema, maand_netto_bruto = bereken_maandelijks(bruto_salaris_jaar, vakantiegeld, dertiende_maand)

    # Ruwweg netto per maand schatten (lijkt erg veel op jaar, maar iets gunstiger door schijven)
    maand_netto = round(res['netto_salaris_jaar'] / (12 + vakantiegeld + dertiende_maand))

    st.success(f"**± €{maand_netto:,} netto per maand** (incl. extra's in mei/dec)")
    st.table(schema)

    if vakantiegeld or dertiende_maand:
        st.info("Doordat vakantiegeld/13e maand in één keer vallen, is het netto maandbedrag in die maand hoger door progressief tarief – vaak €500–€2.000 extra netto!")

# ===================================================================
# === Vergelijking & info ===
# ===================================================================
st.header("Vergelijking")
data = []
for salaris in range(min_dga_loon_jaar, min(totaal_uitkeren, 200_001), 10_000):
    div = totaal_uitkeren - salaris
    r = bereken_jaar(salaris, div)
    data.append({"Salaris bruto": f"€{salaris:,}", "Netto totaal": r['totaal_netto'], "% belasting": r['percentage']})
df = pd.DataFrame(data).sort_values("Netto totaal", ascending=False)
st.dataframe(df.style.highlight_max("Netto totaal", color="#d4edda"), use_container_width=True)

with st.expander("ℹ️ Vakantiegeld & 13e maand – waarom wel/niet?"):
    st.markdown("""
    - **Vakantiegeld (8%)** → meestal **gunstig** want het valt vaak in de lagere schijf  
    - **13e maand** → vaak **iets ongunstig** door progressief tarief (49,5% boven €76.934)  
    - Maar: geeft wel cashflow in december + voelt lekker  
    → In 95% van gevallen wint minimumloon + dividend nog steeds, maar met vakantiegeld kom je heel dichtbij én leef je relaxer
    """)

with st.expander("ℹ️ Excessief lenen"):
    st.markdown("Alles boven €500.000 schuld aan je BV = automatisch box 2-belasting. Beter uitkeren + herinvesteren privé.")

st.caption("Geen fiscaal advies · Tarieven nov 2025 · Door ondernemers, voor ondernemers 🚀")
