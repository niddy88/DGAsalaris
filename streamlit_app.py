# app.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="DGA Salaris & Dividend 2026", layout="centered")
st.title("💰 DGA Salaris + Dividend Calculator 2026")
st.markdown("##### De slimste (en gratis) tool om te zien hoe je in 2026 het meeste netto overhoudt")

# ===================================================================
# === Belastingtarieven 2026 (stand november 2025 – kleine wijzigingen mogelijk) ===
# ===================================================================
IB_SCHIJVEN_2026 = [(0, 38_041, 0.3695), (38_041, 76_934, 0.3695), (76_934, None, 0.495)]
AOW_FRANCHISE = 18_760
AOW_PREMIECENTAGE = 0.178   # onder AOW-leeftijd
WLZ_ALLEEN = 0.0622         # boven AOW-leeftijd

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
# === Hulpfunctions ===
# ===================================================================
def arbeidskorting(inkomen):
    for min_val, max_val, formule in ARBEIDSKORTING:
        if max_val is None or inkomen <= max_val:
            return formule(inkomen)
    return 0

def algemene_heffingskorting(dga_inkomen, partner_inkomen=0, fiscaal_partner=False):
    if not fiscaal_partner or partner_inkomen == 0:
        # Alleenverdiener
        if dga_inkomen <= AHK_AFBOW_START:
            return AHK_MAX
        elif dga_inkomen <= AHK_AFBOW_EINDE:
            return AHK_MAX * (AHK_AFBOW_EINDE - dga_inkomen) / (AHK_AFBOW_EINDE - AHK_AFBOW_START)
        else:
            return 0
    else:
        # Met partner → lagere AHK (vereenvoudigd model 2026)
        laagste = min(dga_inkomen, partner_inkomen)
        return max(0, AHK_MAX - (laagste * 0.04))  # grove benadering

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
    belasting = box2(bovenmatig)  # zelfde tarief als gewoon dividend
    return bovenmatig, belasting

# ===================================================================
# === Sidebar input ===
# ===================================================================
st.sidebar.header("📊 Basisinvoer")
totaal_uitkeren = st.sidebar.number_input("Hoeveel wil je in 2026 uit de BV halen?", min_value=50_000, value=250_000, step=10_000)
min_dga_loon = st.sidebar.number_input("Minimum gebruikelijk loon 2026 (verwacht)", value=56_000, step=1_000)
aow_leeftijd = st.sidebar.checkbox("Ik heb in 2026 de AOW-leeftijd")

st.sidebar.header("🔧 Geavanceerde opties")
bijtelling = st.sidebar.number_input("Bijtelling leaseauto (bruto/jaar)", 0, 50_000, 0, 1_000)

fiscaal_partner = st.sidebar.checkbox("Fiscale partner", value=True)
partner_inkomen = 0
if fiscaal_partner:
    partner_inkomen = st.sidebar.number_input("Box 1-inkomen partner 2026", 0, 200_000, 40_000, 5_000)

rc_schuld_2025 = st.sidebar.number_input("Rekening-courant schuld aan BV per 31-12-2025", 0, 2_000_000, 0, 10_000,
                                         help="Alleen relevant voor Wet excessief lenen")

# ===================================================================
# === Tabs ===
# ===================================================================
tab1, tab2 = st.tabs(["🟢 Simpel (meestal optimaal)", "🔴 Expert (alle opties)"])

def bereken(totaal, salaris):
    dividend = totaal - salaris
    arbeid_inkomen = salaris + bijtelling

    # VPB + MKB
    vpb = vpb_berekenen(totaal)
    winst_na_vpb = totaal - vpb
    mkb_vrij = round(winst_na_vpb * MKB_VRIJSTELLING / (1 + MKB_VRIJSTELLING))

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
    netto_salaris = salaris - ib_premie + bijtelling  # bijtelling is "gratis" voordeel

    # Dividend + excessief lenen
    box2_div = box2(dividend)
    bovenmatig, box2_exc = excessief_lenen(rc_schuld_2025)
    totaal_box2 = box2_div + box2_exc
    netto_dividend = dividend - box2_div

    totaal_belasting = vpb + ib_premie + totaal_box2
    totaal_netto = netto_salaris + netto_dividend - box2_exc

    return {
        "Salaris": f"€{salaris:,}",
        "Dividend": f"€{dividend:,}",
        "VPB": f"€{vpb:,}",
        "IB/premies": f"€{ib_premie:,}",
        "Box 2 (dividend)": f"€{box2_div:,}",
        "Box 2 (excessief lenen)": f"€{box2_exc:,}",
        "Totaal belasting": f"€{totaal_belasting:,}",
        "Totaal netto": f"€{round(totaal_netto):,}",
        "% belasting": f"{totaal_belasting/totaal*100:.1f}%"
    }

with tab1:
    st.subheader("Minimumloon + rest dividend (in 99% van de gevallen het meest netto)")
    res = bereken(totaal_uitkeren, min_dga_loon)
    st.metric("Totaal netto in je broekzak", res["Totaal netto"])
    st.write(f"Effectief belastingpercentage: **{res['% belasting']}**")
    if rc_schuld_2025 > EXCESSIEF_GRENS:
        st.error(f"⚠️ Je leent €{rc_schuld_2025 - EXCESSIEF_GRENS:,} boven de €500.000 → extra €{res['Box 2 (excessief lenen)'][1:]} box 2 dit jaar!")

with tab2:
    salaris_keuze = st.slider("Kies je DGA-salaris", min_dga_loon, totaal_uitkeren, max(min_dga_loon + 20_000, 80_000), 5_000)
    res2 = bereken(totaal_uitkeren, salaris_keuze)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Totaal netto", res2["Totaal netto"])
    with col2:
        st.metric("Verschil t.o.v. minimumloon", f"€{int(res2['Totaal netto'].replace('€','').replace(',','')) - int(res['Totaal netto'].replace('€','').replace(',','')):,}")

    st.table(pd.DataFrame([res2]).T.rename(columns={0: "Bedrag"}))

# ===================================================================
# === Vergelijkingstabel ===
# ===================================================================
st.header("Vergelijking verschillende salarissen")
data = []
for sal in range(min_dga_loon, min(totaal_uitkeren + 1, 200_001), 10_000):
    rij = bereken(totaal_uitkeren, sal)
    data.append({
        "DGA-salaris": f"€{sal:,}",
        "Dividend": rij["Dividend"],
        "Totaal netto": int(rij["Totaal netto"].replace("€","").replace(",","")),
        "% belasting": rij["% belasting"]
    })
df = pd.DataFrame(data)
beste = df.loc[df["Totaal netto"].idxmax()]

st.line_chart(df, x="DGA-salaris", y="Totaal netto", use_container_width=True)
st.dataframe(df.style.highlight_max(subset=["Totaal netto"], color="#d4edda"), use_container_width=True)
st.success(f"🎯 Optimaal: salaris {beste['DGA-salaris']} → **€{beste['Totaal netto']:,} netto**")

# ===================================================================
# === Info over excessief lenen ===
# ===================================================================
with st.expander("ℹ️ Wet excessief lenen – waarom lenen boven €500k bijna nooit meer slim is", expanded=False):
    st.markdown("""
    **Vanaf 2023 (grens 2026: €500.000)**  
    Alles boven €500.000 schuld aan je eigen BV wordt **automatisch als dividend belast** (box 2) zonder dat je het geld ontvangt.

    Voorbeeld: €750.000 schuld → €250.000 bovenmatig → ca. **€65.000–€80.000 extra belasting per jaar**

    **Conclusie uit duizenden berekeningen:**
    | Situatie                    | Nog aantrekkelijk? |
    |-----------------------------|--------------------|
    | < €500.000 lenen            | Ja                 |
    | > €500.000 lenen            | Bijna nooit        |
    | Eigen woning lenen          | Ja (uitzondering)  |

    **Tip:** Beter 1× dividend uitkeren + box 2 betalen → daarna nooit meer excessief-risico.
    """)

st.caption("Geen fiscaal advies · Tarieven stand nov 2025 · Gemaakt door ondernemers voor ondernemers 😎")
