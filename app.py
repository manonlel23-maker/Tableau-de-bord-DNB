import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import json
from urllib.request import urlopen

st.set_page_config(page_title="Dashboard Brevet", page_icon="🎓", layout="wide")

st.markdown("""
<style>
    .main { background-color: #f5f7fa; }
    h1, h2, h3 { color: #1f2c56; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CHARGEMENT
# ============================================================
@st.cache_data
def load_data():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, "DNB_Dashboard_1.xlsx")
    df = pd.read_excel(path, sheet_name="Données_Source")
    df.columns = [c.strip() for c in df.columns]
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": np.nan, "NaN": np.nan, "": np.nan, "None": np.nan})
    df["Année"] = pd.to_numeric(df["Année"], errors="coerce")
    return df

@st.cache_data
def load_geojson():
    url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions.geojson"
    try:
        with urlopen(url) as r:
            return json.load(r)
    except:
        return None

@st.cache_data
def load_geojson_dom():
    url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-avec-outre-mer.geojson"
    try:
        with urlopen(url) as r:
            return json.load(r)
    except:
        return None

try:
    df = load_data()
except Exception as e:
    st.error(f"Erreur de chargement : {e}")
    st.stop()

geojson     = load_geojson()
geojson_dom = load_geojson_dom()


# TABLE DE CORRESPONDANCE CODE REGION -> INSEE

ORDER_TO_INSEE = {
    "1":  "84",  
    "2":  "27",  
    "3":  "53",  
    "4":  "24",  
    "5":  "94",  
    "6":  "44",  
    "7":  "01",  
    "8":  "03",  
    "9":  "32",  
    "10": "11",  
    "11": "04",  
    "12": "02",  
    "13": "06",  
    "14": "28",  
    "15": "75", 
    "16": "76",  
    "17": "52",  
    "18": "93",  
}

REG_NAMES = {
    "84": "Auvergne-Rhône-Alpes",
    "27": "Bourgogne-Franche-Comté",
    "53": "Bretagne",
    "24": "Centre-Val de Loire",
    "94": "Corse",
    "44": "Grand Est",
    "01": "Guadeloupe",
    "03": "Guyane",
    "32": "Hauts-de-France",
    "11": "Île-de-France",
    "04": "La Réunion",
    "02": "Martinique",
    "06": "Mayotte",
    "28": "Normandie",
    "75": "Nouvelle-Aquitaine",
    "76": "Occitanie",
    "52": "Pays de la Loire",
    "93": "Provence-Alpes-Côte d'Azur",
}

METRO = [
    "Auvergne-Rhône-Alpes", "Bourgogne-Franche-Comté", "Bretagne",
    "Centre-Val de Loire", "Corse", "Grand Est", "Hauts-de-France",
    "Île-de-France", "Normandie", "Nouvelle-Aquitaine", "Occitanie",
    "Pays de la Loire", "Provence-Alpes-Côte d'Azur",
]

DOM = ["Guadeloupe", "Guyane", "La Réunion", "Martinique", "Mayotte"]

DOM_DEP_CODES = {
    "Guadeloupe": "971",
    "Martinique":  "972",
    "Guyane":      "973",
    "La Réunion":  "974",
    "Mayotte":     "976",
}


# DETECTION DES COLONNES
def find_col(df, keywords):
    for kw in keywords:
        for col in df.columns:
            if kw.lower() in col.lower():
                return col
    return None

COL_ANNEE      = find_col(df, ["Année", "Annee"])
COL_REGION     = find_col(df, ["Libellé région", "Libelle region", "région"])
COL_CODE_REG   = find_col(df, ["Code région", "Code reg"])
COL_SERIE      = find_col(df, ["Série", "Serie"])
COL_INSCRITS   = find_col(df, ["Inscrits"])
COL_PRESENTS   = find_col(df, ["Présents", "Presents"])
COL_ADMIS      = find_col(df, ["Admis"])
COL_MENTION_SB = find_col(df, ["sans mention"])
COL_MENTION_AB = find_col(df, ["assez bien"])
COL_MENTION_B  = find_col(df, ["mention bien"])
COL_MENTION_TB = find_col(df, ["très bien", "tres bien"])
COL_ADMIS_F    = find_col(df, ["Admis fille"])
COL_ADMIS_G    = find_col(df, ["Admis Gar", "Garcons", "Garçons"])

# Conversion numérique
num_cols = [c for c in [COL_INSCRITS, COL_PRESENTS, COL_ADMIS,
                        COL_MENTION_SB, COL_MENTION_AB, COL_MENTION_B,
                        COL_MENTION_TB, COL_ADMIS_F, COL_ADMIS_G] if c]

if COL_CODE_REG:
    df[COL_CODE_REG] = (
        df[COL_CODE_REG]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )
    df["Code_Region"]    = df[COL_CODE_REG].map(ORDER_TO_INSEE)
    df["Libelle_Region"] = df["Code_Region"].map(REG_NAMES)

for col in num_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# SIDEBAR
st.sidebar.header("Filtres")

annees = sorted(df[COL_ANNEE].dropna().unique().astype(int).tolist())
annee_sel = st.sidebar.slider("Période", min(annees), max(annees), (min(annees), max(annees)))

reg_list = sorted(REG_NAMES.values())
region_sel = st.sidebar.multiselect("Région", reg_list, default=None)

if COL_SERIE:
    serie_list = sorted(df[COL_SERIE].dropna().unique().tolist())
    serie_sel  = st.sidebar.multiselect("Série", serie_list, default=None)
else:
    serie_sel = []

# Filtrage
mask = (df[COL_ANNEE] >= annee_sel[0]) & (df[COL_ANNEE] <= annee_sel[1])
if region_sel:
    mask &= df["Libelle_Region"].isin(region_sel)
if serie_sel and COL_SERIE:
    mask &= df[COL_SERIE].isin(serie_sel)

dff = df[mask].copy()
st.sidebar.metric("Lignes filtrées", f"{len(dff):,}".replace(",", " "))

# EN-TETE ET KPIs
st.title("Tableau de Bord — Résultats du Brevet")
st.markdown("Analyse interactive par **région, série, sexe et mention**.")
st.markdown("---")

total_inscrits = int(dff[COL_INSCRITS].sum()) if COL_INSCRITS else 0
total_presents = int(dff[COL_PRESENTS].sum()) if COL_PRESENTS else 0
total_admis    = int(dff[COL_ADMIS].sum())    if COL_ADMIS    else 0
taux_global    = round(total_admis / total_inscrits * 100, 1) if total_inscrits else 0

mention_cols_valid = [c for c in [COL_MENTION_AB, COL_MENTION_B, COL_MENTION_TB] if c]
total_mentions = int(dff[mention_cols_valid].sum().sum()) if mention_cols_valid else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Inscrits",        f"{total_inscrits:,}".replace(",", " "))
c2.metric("Présents",        f"{total_presents:,}".replace(",", " "))
c3.metric("Admis",           f"{total_admis:,}".replace(",", " "))
c4.metric("Taux / Inscrits", f"{taux_global} %")
c5.metric("Mentions",        f"{total_mentions:,}".replace(",", " "))

st.markdown("---")

# ONGLETS
tab1, tab2, tab3, tab4 = st.tabs(["Carte", "Evolutions", "Mentions et Sexe", "Données"])

# TAB 1 — CARTE
with tab1:
    st.subheader("Carte choroplète par région")

    choix   = st.selectbox("Indicateur", ["Taux de réussite (%)", "Admis", "Inscrits"])
    col_map = {"Taux de réussite (%)": "Taux", "Admis": "Admis", "Inscrits": "Inscrits"}
    couleur = {"Taux de réussite (%)": "Blues", "Admis": "Greens", "Inscrits": "Purples"}

    #METROPOLE
    geo_df = (
        dff[dff["Libelle_Region"].isin(METRO)]
        .groupby(["Code_Region", "Libelle_Region"])
        .agg(
            Inscrits=(COL_INSCRITS, "sum"),
            Presents=(COL_PRESENTS, "sum"),
            Admis=(COL_ADMIS,    "sum"),
        )
        .reset_index()
    )
    geo_df["Taux"] = (geo_df["Admis"] / geo_df["Inscrits"] * 100).round(1)

    st.markdown("#### France Métropolitaine")
    if geojson:
        fig = px.choropleth(
            geo_df,
            geojson=geojson,
            locations="Code_Region",
            featureidkey="properties.code",
            color=col_map[choix],
            color_continuous_scale=couleur[choix],
            hover_name="Libelle_Region",
            hover_data={"Code_Region": False, "Inscrits": True, "Admis": True, "Taux": True},
            labels={col_map[choix]: choix}
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0}, height=530)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("GeoJSON métropole indisponible.")
        fig = px.bar(
            geo_df.sort_values(col_map[choix]),
            x=col_map[choix], y="Libelle_Region",
            orientation="h", color=col_map[choix],
            color_continuous_scale=couleur[choix]
        )
        st.plotly_chart(fig, use_container_width=True)

    # CARTE DOM-TOM
    dom_df = (
        dff[dff["Libelle_Region"].isin(DOM)]
        .groupby("Libelle_Region")
        .agg(
            Inscrits=(COL_INSCRITS, "sum"),
            Presents=(COL_PRESENTS, "sum"),
            Admis=(COL_ADMIS,    "sum"),
        )
        .reset_index()
    )
    dom_df["Taux"]     = (dom_df["Admis"] / dom_df["Inscrits"] * 100).round(1)
    dom_df["Code_Dep"] = dom_df["Libelle_Region"].map(DOM_DEP_CODES)

    st.markdown("#### Départements et Régions d'Outre-Mer (DROM)")

    if not dom_df.empty and geojson_dom:
        dom_codes = list(DOM_DEP_CODES.values())
        geojson_dom_filtered = {
            "type": "FeatureCollection",
            "features": [
                f for f in geojson_dom["features"]
                if f["properties"].get("code") in dom_codes
            ]
        }
        fig_dom = px.choropleth(
            dom_df,
            geojson=geojson_dom_filtered,
            locations="Code_Dep",
            featureidkey="properties.code",
            color=col_map[choix],
            color_continuous_scale=couleur[choix],
            hover_name="Libelle_Region",
            hover_data={"Code_Dep": False, "Inscrits": True, "Admis": True, "Taux": True},
            labels={col_map[choix]: choix}
        )
        fig_dom.update_geos(fitbounds="locations", visible=False)
        fig_dom.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0}, height=400)
        st.plotly_chart(fig_dom, use_container_width=True)
    elif dom_df.empty:
        st.info("Aucune donnée DOM-TOM dans la sélection actuelle.")
    else:
        st.warning("GeoJSON DOM indisponible.")
        if not dom_df.empty:
            fig_dom_bar = px.bar(
                dom_df.sort_values(col_map[choix]),
                x=col_map[choix], y="Libelle_Region",
                orientation="h", color=col_map[choix],
                color_continuous_scale=couleur[choix]
            )
            st.plotly_chart(fig_dom_bar, use_container_width=True)

    # TABLEAUX CLASSEMENT
    st.markdown("##### Classement global des régions")

    classement_global = pd.concat([
        geo_df[["Libelle_Region", "Inscrits", "Admis", "Taux"]],
        dom_df[["Libelle_Region", "Inscrits", "Admis", "Taux"]] if not dom_df.empty else pd.DataFrame()
    ], ignore_index=True)

    classement_global = classement_global.sort_values("Taux", ascending=False).reset_index(drop=True)
    classement_global.index += 1
    classement_global.columns = ["Région", "Inscrits", "Admis", "Taux (%)"]

    st.dataframe(classement_global, use_container_width=True)

# TAB 2 — EVOLUTIONS
with tab2:
    st.subheader("Evolutions temporelles")

    colA, colB = st.columns(2)

    evo = dff.groupby(COL_ANNEE).agg(
        Inscrits=(COL_INSCRITS, "sum"),
        Admis=(COL_ADMIS, "sum")
    ).reset_index()
    evo["Taux"] = (evo["Admis"] / evo["Inscrits"] * 100).round(1)

    fig1 = px.line(evo, x=COL_ANNEE, y="Taux", markers=True,
                   title="Taux de réussite global (sur inscrits)")
    fig1.update_traces(line=dict(width=3, color="#667eea"))
    fig1.update_layout(yaxis_title="Taux (%)")
    colA.plotly_chart(fig1, use_container_width=True)

    if COL_SERIE:
        evo_s = dff.groupby([COL_ANNEE, COL_SERIE]).agg(
            Inscrits=(COL_INSCRITS, "sum"),
            Admis=(COL_ADMIS, "sum")
        ).reset_index()
        evo_s["Taux"] = (evo_s["Admis"] / evo_s["Inscrits"] * 100).round(1)

        fig2 = px.line(evo_s, x=COL_ANNEE, y="Taux", color=COL_SERIE,
                       markers=True, title="Taux par série (sur inscrits)")
        colB.plotly_chart(fig2, use_container_width=True)

        fig3 = px.area(evo_s, x=COL_ANNEE, y="Admis", color=COL_SERIE,
                       title="Volume d'admis par série")
        st.plotly_chart(fig3, use_container_width=True)

# TAB 3 — MENTIONS ET SEXE
with tab3:
    st.subheader("Mentions et répartition par sexe")
    colC, colD = st.columns(2)

    if all([COL_MENTION_SB, COL_MENTION_AB, COL_MENTION_B, COL_MENTION_TB]):
        mentions = {
            "Sans mention": dff[COL_MENTION_SB].sum(),
            "Assez bien":   dff[COL_MENTION_AB].sum(),
            "Bien":         dff[COL_MENTION_B].sum(),
            "Très bien":    dff[COL_MENTION_TB].sum(),
        }
        df_m = pd.DataFrame(mentions.items(), columns=["Mention", "Nombre"])
        fig_m = px.pie(df_m, names="Mention", values="Nombre", hole=0.45,
                       title="Répartition des mentions",
                       color_discrete_sequence=px.colors.sequential.Tealgrn)
        colC.plotly_chart(fig_m, use_container_width=True)
    else:
        colC.warning("Colonnes mentions non détectées.")

    if COL_ADMIS_F and COL_ADMIS_G:
        df_sexe = pd.DataFrame({
            "Sexe":  ["Filles", "Garçons"],
            "Admis": [int(dff[COL_ADMIS_F].sum()), int(dff[COL_ADMIS_G].sum())]
        })
        fig_s = px.bar(df_sexe, x="Sexe", y="Admis", color="Sexe", text="Admis",
                       title="Admis par sexe",
                       color_discrete_map={"Filles": "#e84393", "Garçons": "#0984e3"})
        fig_s.update_traces(textposition="outside")
        colD.plotly_chart(fig_s, use_container_width=True)
    else:
        colD.warning("Colonnes admis filles/garçons non détectées.")

    if COL_SERIE and all([COL_MENTION_SB, COL_MENTION_AB, COL_MENTION_B, COL_MENTION_TB]):
        m_serie = dff.groupby(COL_SERIE)[
            [COL_MENTION_SB, COL_MENTION_AB, COL_MENTION_B, COL_MENTION_TB]
        ].sum().reset_index()
        m_melt = m_serie.melt(id_vars=COL_SERIE, var_name="Mention", value_name="Nombre")
        m_melt["Mention"] = m_melt["Mention"].replace({
            COL_MENTION_SB: "Sans mention",
            COL_MENTION_AB: "Assez bien",
            COL_MENTION_B:  "Bien",
            COL_MENTION_TB: "Très bien"
        })
        fig_ms = px.bar(m_melt, x=COL_SERIE, y="Nombre", color="Mention",
                        barmode="stack", title="Mentions par série")
        st.plotly_chart(fig_ms, use_container_width=True)

# TAB 4 — DONNEES
with tab4:
    st.subheader("Données détaillées")
    st.dataframe(dff, use_container_width=True, height=500)
    csv = dff.to_csv(index=False, sep=";").encode("utf-8")
    
st.markdown("---")
st.caption("Dashboard Brevet — Streamlit & Plotly")
