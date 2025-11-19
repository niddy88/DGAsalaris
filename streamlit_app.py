# app.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="BV Geld Halen 2026 Calculator", layout="centered")
st.title("💰 Hoe haal je in 2026 het meeste netto uit je BV?")
st.markdown("##### Minimale belasting door slim salaris + dividend te combineren (tarieven nov 2025)")

# === Tarieven 2026 (update deze als Prinsjesdag 2026 iets verandert) ===
IB_SCHIJVEN_2026 = [(0, 38041, 0.3695), (38041, 76934, 0.3695), (76934, None, 0.495)]
AOW_FRANCHISE = 18760
AOW_PREMIECENTAGE = 0.178  # onder AOW-leeftijd
WLZ_ALLEEN = 0.0622        # boven AOW-leeftijd

ARBEIDSKORTING = [
    (0, 12570, lambda x: 0.06336 * x),
    (12570, 24338, lambda x: 795 + 0.29803 * (x - 12570)),
    (24338, 40527, lambda x: 4333),
    (40527, 130997, lambda x: 4333 - 0.0665 * (x - 40527)),
    (130997, None, lambda x: 0)
]

AHK_MAX = 3070
AHK_AFBouw_START = 24338
AHK_AFBouw_EINDE = 76934

BOX2_SCHIJVEN_2026 = [(0, 66700, 0.245), (66700, None, 0.318)]
VPB_SCHIJVEN_2026 = [(0, 200000, 0.19), (200000, None, 0.258)]
MKB_VRIJSTELLING = 0.127

# === Functies ===
def arbeidskorting(inkomen):
    for min_val, max_val, formule in ARBEIDSKORTING:
        if max_val is None or inkomen <= max_val:
            return formule(inkomen)
    return 0

def heffingskortingen(inkomen):
    ak = arbeidskorting(inkomen)
    if inkomen <= AHK_AFBouw_START:
        ahk = AHK_MAX
    elif inkomen <= AHK_AFBouw_EINDE:
        ahk = AHK_MAX * (AHK_AFBouw_EINDE - inkomen) / (AHK_AFBouw_EINDE - AHK_AFBouw_START)
    else:
        ahk = 0
    return ak + ahk

def ib_box1(salaris, aow_leeftijd):
    premie_grondslag = max(0, salaris - AOW_FRANCHISE)
    premie = premie_grondslag * (WLZ_ALLEEN if aow_leeftijd else AOW_PREMIECENTAGE)

    ib = 0
    rest = salaris
    for onder, boven, tarief in IB_SCHIJVEN_2026:
        schijf = rest if boven is None else min(rest, boven - onder)
        ib += schijf * tarief
        rest -= schijf
        if rest <= 0:
            break

    korting = heffingskortingen(salaris)
    te_betalen = max(0, ib + premie - korting)
    return round(te_betalen), round(salaris - te_betalen)

def box2(dividend):
    belasting = 0
    rest = dividend
    for onder, boven, tarief in BOX2_SCHIJVEN_2026:
        schijf = rest if boven is None else min(rest, boven - onder)
        belasting += schijf * tarief
        rest -= schijf
        if rest <= 0:
            break
    return round(belasting), round(dividend - belasting)

def vpb_berekenen(winst):
    belasting = 0
    rest = winst
    for onder, boven, tarief in VPB_SCHIJVEN_2026:
        schijf = rest if boven is None else min(rest, boven - onder)
        belasting += schijf * tarief
        rest -= schijf
        if rest <= 0:
            break
    return round(belasting)

def bereken_scenario(salaris, dividend, aow_leeftijd):
    totaal_uit_te_keren = salaris + dividend
    vpb = vpb_berekenen(totaal_uit_te_keren)
    winst_na_vpb = totaal_uit_te_keren - vpb
    mkb_vrij = round(winst_na_vpb * MKB_VRIJSTELLING / (1 + MKB_VRIJSTELLING))
    
    ib_premie, netto_salaris = ib_box1(salaris, aow_leeftijd)
    box2_bedrag, netto_dividend = box2(dividend)
    
    totaal_belasting = vpb + ib_premie + box2_bedrag
    totaal_netto = netto_salaris + netto_dividend
    
    return {
        "Bruto salaris": f"€{salaris:,}",
        "Bruto dividend": f"€{dividend:,}",
        "VPB": f"€{vpb:,}",
        "IB + premies": f"€{ib_premie:,}",
        "Box 2": f"€{box2_bedrag:,}",
        "Totaal belasting": f"€{totaal_belasting:,}",
        "Netto salaris": f"€{netto_salaris:,}",
        "Netto dividend": f"€{netto_dividend:,}",
        "TOTAAL NETTO": f"€{totaal_netto:,}",
        "Effectief % belasting": f"{totaal_belasting / totaal_uit_te_keren * 100:.1f}%"
    }

# === Sidebar input ===
st.sidebar.header("Jouw situatie")
totaal_bedrag = st.sidebar.number_input(
    "Hoeveel geld wil je in 2026 uit de BV halen?", min_value=50000, value=250000, step=10000
)
min_loon = st.sidebar.number_input("Minimum gebruikelijk loon 2026 (verwacht)", value=56000, step=1000)
aow_leeftijd = st.sidebar.checkbox("Ik heb in 2026 al de AOW-leeftijd")

st.sidebar.markdown("---")
st.sidebar.caption("Gemaakt door een ondernemer die geen € 997 wil betalen voor 3 Excel-tabbladen 😉")

# === Scenario's ===
st.header("Kies je strategie")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Minimumloon + rest dividend (meestal optimaal)")
    dividend1 = totaal_bedrag - min_loon
    if dividend1 < 0:
        dividend1 = 0
    res1 = bereken_scenario(min_loon, dividend1, aow_leeftijd)
    st.metric("Totaal netto", res1["TOTAAL NETTO"])
    st.caption(f"Effectief {res1['Effectief % belasting']} belasting")

with col2:
    st.subheader("2. Zelf gekozen salaris")
    salaris_keuze = st.slider(
        "DGA-salaris", min_value=min_loon, max_value=totaal_bedrag, value=max(min_loon, 75000), step=5000
    )
    dividend_keuze = totaal_bedrag - salaris_keuze
    res2 = bereken_scenario(salaris_keuze, dividend_keuze, aow_leeftijd)
    st.metric("Totaal netto", res2["TOTAAL NETTO"])
    st.caption(f"Effectief {res2['Effectief % belasting']} belasting")

# === Vergelijkingstabel ===
st.header("Vergelijking verschillende salarissen")
data = []
for sal in range(min_loon, min(totaal_bedrag + 1, 150001), 10000):
    div = totaal_bedrag - sal
    if div < 0:
        continue
    res = bereken_scenario(sal, div, aow_leeftijd)
    data.append(
        {
            "Salaris": f"€{sal:,}",
            "Dividend": f"€{div:,}",
            "Totaal netto": int(res["TOTAAL NETTO"].replace("€", "").replace(",", "")),
            "Belasting %": res["Effectief % belasting"],
        }
    )

df = pd.DataFrame(data)
beste = df.loc[df["Totaal netto"].idxmax()]

st.line_chart(df, x="Salaris", y="Totaal netto", use_container_width=True)

st.dataframe(df.style.highlight_max(subset=["Totaal netto"], color="#d4edda"), use_container_width=True)

st.success(
    f"🎯 Optimaal scenario: salaris €{beste['Salaris'].replace('€','')} + dividend €{int(totaal_bedrag) - int(beste['Salaris'].replace('€','').replace(',', '')):,} → **{beste['Totaal netto']:,} netto**"
)

st.caption("Let op: dit is een indicatie. Definitieve tarieven worden pas september 2026 bekend. Geen fiscaal advies, etc. etc.")
