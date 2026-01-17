import streamlit as st
import pandas as pd

st.set_page_config(page_title="EDI TVA Maroc", layout="wide")

st.title("📊 Application EDI TVA – Maroc")

# ==== معلومات الشركة ====
st.header("🏢 معلومات الشركة")

raison_sociale = st.text_input("Raison sociale")
id_fiscal = st.text_input("Identifiant fiscal")
annee = st.number_input("Année", min_value=2000, max_value=2100, step=1)

regime = st.selectbox(
    "Régime TVA",
    options=["01 - Mensuel", "02 - Trimestriel"]
)

if regime.startswith("01"):
    periode = st.selectbox("Période (mois)", list(range(1, 13)))
else:
    periode = st.selectbox("Période (trimestre)", [1, 2, 3, 4])

st.divider()

# ==== Upload fichier factures ====
st.header("📤 Importer les factures (Excel)")

uploaded_file = st.file_uploader(
    "Choisir un fichier Excel (.xlsx)",
    type=["xlsx"]
)

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("🔍 Aperçu des factures")
    st.dataframe(df)

    # Totaux
    total_ht = df["M_HT"].sum()
    total_tva = df["TVA"].sum()
    total_ttc = df["M_TTC"].sum()

    st.subheader("📌 Totaux")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total HT", f"{total_ht:,.2f} DH")
    col2.metric("Total TVA", f"{total_tva:,.2f} DH")
    col3.metric("Total TTC", f"{total_ttc:,.2f} DH")

    # Export EDI
    st.subheader("⬇️ Générer fichier EDI")

    edi_df = df.copy()
    edi_df.insert(0, "RAISON_SOCIAL", raison_sociale)
    edi_df.insert(1, "ID_FISCAL", id_fiscal)
    edi_df.insert(2, "ANNEE", annee)
    edi_df.insert(3, "PERIODE", periode)
    edi_df.insert(4, "REGIME", 1 if regime.startswith("01") else 2)

    st.download_button(
        "📥 Télécharger EDI TVA (Excel)",
        data=edi_df.to_excel(index=False, engine="openpyxl"),
        file_name="EDI_TVA.xlsx"
    )
