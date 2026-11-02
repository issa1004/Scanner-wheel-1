]

ETF_CAD = [
    "XIC.TO", "XIU.TO", "ZEB.TO",
    "VFV.TO", "ZSP.TO", "XEI.TO",
    "VDY.TO", "HYLD.TO", "HDIV.TO",
    "HMAX.TO", "ZWB.TO"
]


# ============================================================
# 4. PROFILS DE STRATEGIE
# ============================================================

st.sidebar.header("Profil de Stratégie")

profile = st.sidebar.radio(
    "Choisissez votre profil :",
    [
        "Conservatrice",
        "Modérée",
        "Agressive",
        "Personnalisée"
    ]
)

if profile == "Conservatrice":

    def_p_min, def_p_max = 15.0, 300.0
    def_f_ema, def_s_ema = 20, 50
    def_cross_d = 10
    def_min_v = 1000000
    def_min_mc = 10000.0
    def_max_pe = 25.0
    def_min_roe = 10.0
    def_max_de = 1.5
    def_dte_min, def_dte_max = 30, 45
    def_delta_min, def_delta_max = 0.10, 0.20

elif profile == "Modérée":

    def_p_min, def_p_max = 10.0, 400.0
    def_f_ema, def_s_ema = 20, 50
    def_cross_d = 10
    def_min_v = 500000
    def_min_mc = 2000.0
    def_max_pe = 40.0
    def_min_roe = 5.0
    def_max_de = 2.5
    def_dte_min, def_dte_max = 20, 45
    def_delta_min, def_delta_max = 0.15, 0.30

elif profile == "Agressive":

    def_p_min, def_p_max = 5.0, 500.0
    def_f_ema, def_s_ema = 9, 21
    def_cross_d = 15
    def_min_v = 300000
    def_min_mc = 500.0
    def_max_pe = 75.0
    def_min_roe = 0.0
    def_max_de = 4.0
    def_dte_min, def_dte_max = 14, 30
    def_delta_min, def_delta_max = 0.25, 0.40

else:

    def_p_min, def_p_max = 1.0, 1000.0
    def_f_ema, def_s_ema = 5, 20
    def_cross_d = 10
    def_min_v = 500000
    def_min_mc = 1000.0
    def_max_pe = 30.0
    def_min_roe = 5.0
    def_max_de = 2.0
    def_dte_min, def_dte_max = 7, 60
    def_delta_min, def_delta_max = 0.10, 0.40


# ============================================================
# 5. SELECTION DU MARCHE
# ============================================================

st.sidebar.header("Sélection du Marché")

market_type = st.sidebar.selectbox(
    "Choisissez le marché :",
    [
        "Secteurs US (Dynamiques en direct)",
        "Canada Global (TSX + TSX Venture)",
        "Listes personnalisées (10 listes modifiables)",
        "ETF US",
        "ETF Canada"
    ]
)

if "Secteurs US" in market_type:

    with st.spinner("Téléchargement des marchés US..."):

        us_map = charger_marche_us_dynamique()

    selected_sec = st.sidebar.selectbox(
        "Secteur US :",
        list(us_map.keys())
    )

    universe = us_map[selected_sec]

elif "Canada Global" in market_type:

    with st.spinner("Téléchargement des titres canadiens..."):

        try:

            canada_map = charger_marche_canada_global()

            selected_canada = st.sidebar.selectbox(
                "Univers canadien :",
                list(canada_map.keys())
            )

            universe = canada_map[selected_canada]

            st.sidebar.caption(
                f"TSX : {len(canada_map['TSX - Bourse de Toronto']):,} titres"
                f" | TSX Venture : {len(canada_map['TSX Venture']):,} titres"
            )

        except Exception as e:

            st.error(f"Erreur de chargement du Canada : {e}")

            universe = []

elif market_type == "ETF US":

    universe = ETF_US

elif market_type == "ETF Canada":

    universe = ETF_CAD

else:

    st.sidebar.markdown("---")
    st.sidebar.subheader("Gestion des 10 listes personnalisées")

    selected_list_name = st.sidebar.selectbox(
        "Choisir la liste à modifier :",
        list(st.session_state.custom_lists.keys())
    )

    current_val = st.session_state.custom_lists[selected_list_name]

    updated_val = st.sidebar.text_area(
        "Modifier les tickers :",
        current_val,
        height=120
    )

    st.session_state.custom_lists[selected_list_name] = updated_val

    universe = [
        s.strip().upper()
        for s in updated_val.replace("\n", ",").split(",")
        if s.strip()
    ]

st.sidebar.markdown("---")

scan_all = st.sidebar.checkbox(
    "SCANNER TOUTE LA LISTE SANS LIMITE",
    value=True
)

active_universe = universe if scan_all else universe[:50]

st.sidebar.success(
    f"Titres chargés : {len(active_universe):,}"
)


# ============================================================
# 6. FILTRES
# ============================================================

st.sidebar.header("Filtres Techniques et Fondamentaux")

min_price = st.sidebar.number_input(
    "Prix minimum ($)",
    value=def_p_min,
