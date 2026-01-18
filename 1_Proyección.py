import streamlit as st
import pandas as pd
import os
import altair as alt

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Dashboard Avance y Ranking",
    layout="wide"
)

# =========================
# CARGA DE DATA
# =========================
@st.cache_data(ttl=3600)  # se refresca cada hora
def cargar_data():
    ruta_script = os.path.dirname(os.path.abspath(__file__))
    ruta = os.path.join(ruta_script, "avance.xlsx")
    return pd.read_excel(ruta, dtype={"HC": str})

df = cargar_data()

df["Ranking"] = pd.to_numeric(df["Ranking"], errors="coerce")
df = df.sort_values("Ranking", na_position="last")

# =========================
# LIMPIEZA BÁSICA
# =========================
df["DEPARTAMENTO"] = df["DEPARTAMENTO"].astype(str).str.strip()
df["CANAL"] = df["CANAL"].astype(str).str.strip()
df["CLUSTER"] = df["CLUSTER"].astype(str).str.strip()

# =========================
# SIDEBAR – FILTROS
# =========================

st.sidebar.image("Panel.png", use_container_width=True)
st.sidebar.title("Filtros")

departamentos = ["Todos"] + sorted(df["DEPARTAMENTO"].unique().tolist())
clusters = ["Todos"] + sorted(df["CLUSTER"].unique().tolist())

dep_sel = st.sidebar.selectbox("Departamento", departamentos)
cluster_sel = st.sidebar.selectbox("Cluster", clusters)

solo_ganadores = st.sidebar.checkbox("Mostrar solo ganadores")
top_n = st.sidebar.slider("Top Ranking", 1, 50, 10)

# =========================
# APLICAR FILTROS
# =========================
df_filt = df.copy()

if dep_sel != "Todos":
    df_filt = df_filt[df_filt["DEPARTAMENTO"] == dep_sel]

if cluster_sel != "Todos":
    df_filt = df_filt[df_filt["CLUSTER"] == cluster_sel]

if solo_ganadores:
    df_filt = df_filt[df_filt["Ganadores"] == 1]

# =========================
# KPIs
# =========================
col_logo, col_title = st.columns([1, 6])

with col_logo:
    st.image("logo.png", width=120)

with col_title:
    st.title(" Proyección, Ranking y Ganadores")

st.markdown("""
<style>
.kpi {
    background-color: #1e1e1e;
    padding: 18px;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
.kpi-title {
    font-size: 14px;
    color: #AAAAAA;
}
.kpi-value {
    font-size: 28px;
    font-weight: 700;
    color: white;
}
</style>
""", unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)

def kpi(col, title, value):
    col.markdown(f"""
    <div class="kpi">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

kpi(c1, "👥 Participantes", f"{len(df_filt):,}")
kpi(c2, "🏆 Ganadores", f"{df_filt['Ganadores'].sum():,}")
kpi(c3, "📈 Proyección PP", f"{df_filt['Avance PP Total'].mean()*100:.1f}%")
kpi(c4, "📊 Proyección SS", f"{df_filt['Avance SS Total'].mean()*100:.1f}%")
kpi(c5, "⚡ Proyección Eqv", f"{df_filt['Avance Eqv Total'].mean()*100:.1f}%")

st.divider()

# =========================
# 🏆 RANKING POR PROYECCIÓN TOTAL
# =========================
st.subheader("🏆 Ranking por Proyección Total")

df_rank = (
    df_filt
    .sort_values("Ranking")
    .head(top_n)
    .copy()
)

# 🔴 LIMPIEZA REAL DEL RANKING
df_rank["Ranking"] = pd.to_numeric(df_rank["Ranking"], errors="coerce")

# Ranking visual (medallas + números limpios)
def ranking_medalla(x):
    if pd.isna(x):
        return ""
    x = int(x)
    if x == 1:
        return "🥇 1"
    elif x == 2:
        return "🥈 2"
    elif x == 3:
        return "🥉 3"
    else:
        return str(x)

df_rank["Ranking 🏅"] = df_rank["Ranking"].apply(ranking_medalla)

# Porcentajes visuales
df_rank["Proyección Eqv Total %"] = (df_rank["Avance Eqv Total"] * 100).round(1).astype(str) + "%"
df_rank["Proyección PP Total %"]  = (df_rank["Avance PP Total"]  * 100).round(1).astype(str) + "%"

# Columnas finales
cols_rank = [
    "Ranking 🏅",
    "HC",
    "NOMBRE",
    "DEPARTAMENTO",
    "CLUSTER",
    "Proyección Eqv Total %",
    "Proyección PP Total %",
    "PROY TOTAL PP",
    "PROY TOTAL SS"
]

st.dataframe(
    df_rank[cols_rank],
    use_container_width=True,
    hide_index=True
)

# =========================
# RESUMEN POR DEPARTAMENTO (FIJO)
# =========================
st.subheader("📍 Proyección por Departamento (Resumen General)")

df_dep = (
    df.groupby("DEPARTAMENTO", as_index=False)
    .agg(
        Proyección_PP_Total=("Avance PP Total", "mean"),
        Proyección_SS_Total=("Avance SS Total", "mean"),
        Proyección_Eqv_Total=("Avance Eqv Total", "mean")
    )
)

# Ordenar por Equivalente (descendente)
df_dep = df_dep.sort_values("Proyección_Eqv_Total", ascending=False)

# Formato porcentaje
for col in ["Proyección_PP_Total", "Proyección_SS_Total", "Proyección_Eqv_Total"]:
    df_dep[col] = (df_dep[col] * 100).round(1)

styled_dep = (
    df_dep
    .style
    .format({
        "Proyección_PP_Total": "{:.1f}%",
        "Proyección_SS_Total": "{:.1f}%",
        "Proyección_Eqv_Total": "{:.1f}%"
    })
    .background_gradient(
        cmap="RdYlGn",
        subset=["Proyección_Eqv_Total"]
    )
    .set_properties(**{
        "text-align": "center"
    })
    .set_table_styles([
        {"selector": "th", "props": [("text-align", "center"), ("font-weight", "bold")]},
        {"selector": "td", "props": [("font-size", "13px")]}
    ])
)

st.data_editor(
    styled_dep,
    use_container_width=True,
    hide_index=True,
    disabled=True
)
