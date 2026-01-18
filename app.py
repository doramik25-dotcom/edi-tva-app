import streamlit as st
import pandas as pd
import pytesseract
from PIL import Image
import pdfplumber
import re
import io

st.set_page_config(page_title="Application EDI TVA - Maroc", layout="wide")

st.title("📊 Application EDI TVA - Maroc")
st.subheader("📥 Importer des factures (PDF ou Image)")

uploaded_file = st.file_uploader(
    "اختَر فاتورة (PDF / JPG / PNG)",
    type=["pdf", "jpg", "jpeg", "png"]
)

def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_text_from_image(file):
    image = Image.open(file)
    return pytesseract.image_to_string(image, lang="fra")

def extract_invoice_data(text):
    def find(pattern):
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    return {
        "RAISON_SOCIALE": find(r"Raison sociale[:\s]*([A-Za-z0-9\s]+)"),
        "ID_FISCAL": find(r"(IF|Identifiant fiscal)[:\s]*([0-9]+)"),
        "NUM_FACTURE": find(r"(Facture|N°)[:\s]*([A-Za-z0-9/-]+)"),
        "DATE_FACTURE": find(r"(\d{2}/\d{2}/\d{4})"),
        "MONTANT_HT": find(r"(HT|H\.T)[:\s]*([\d\.,]+)"),
        "TVA": find(r"(TVA)[:\s]*([\d\.,]+)"),
        "MONTANT_TTC": find(r"(TTC)[:\s]*([\d\.,]+)")
    }

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        text = extract_text_from_pdf(uploaded_file)
    else:
        text = extract_text_from_image(uploaded_file)

    st.subheader("📝 Texte extrait")
    st.text_area("", text, height=200)

    data = extract_invoice_data(text)
    df = pd.DataFrame([data])

    st.subheader("📑 Données extraites")
    st.dataframe(df)

    output = io.BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)

    st.download_button(
        "⬇️ Télécharger EDI TVA (Excel)",
        data=output,
        file_name="EDI_TVA.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
