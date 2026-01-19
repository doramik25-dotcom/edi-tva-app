import streamlit as st
import pandas as pd
import re
import io
import requests

# ================= CONFIG =================
st.set_page_config(page_title="EDI TVA Maroc", layout="wide")
st.title("🧾 برنامج تعمير EDI TVA – المغرب")

MINDEE_API_KEY = "PUT_YOUR_MINDEE_API_KEY_HERE"

# ================= OCR =================
def run_ocr(file):
    response = requests.post(
        "https://api.mindee.net/v1/products/mindee/invoices/v4/predict",
        files={"document": file},
        headers={"Authorization": f"Token {MINDEE_API_KEY}"}
    )
    data = response.json()
    try:
        pred = data["document"]["inference"]["prediction"]
        parts = []

        if pred.get("invoice_number"):
            parts.append(f"FACTURE {pred['invoice_number']['value']}")
        if pred.get("date"):
            parts.append(pred["date"]["value"])
        if pred.get("total_excl"):
            parts.append(f"HT {pred['total_excl']['value']}")
        if pred.get("total_tax"):
            parts.append(f"TVA {pred['total_tax']['value']}")
        if pred.get("total_incl"):
            parts.append(f"TTC {pred['total_incl']['value']}")
        if pred.get("supplier_registration"):
            parts.append(pred["supplier_registration"]["value"])

        return " ".join(parts)
    except:
        return ""

# ================= ANALYSE FACTURE =================
def analyze_invoice_text(text):
    text = " ".join(text.split()).upper()

    def f(pattern):
        m = re.search(pattern, text)
        return m.group(1) if m else ""

    def nf(x):
        try:
            return float(x.replace(" ", "").replace(",", "."))
        except:
            return 0.0

    ice = f(r"\b(\d{15})\b")
    num = f(r"(FACTURE|N°)\s*[:]*\s*([A-Z0-9\-]+)")
    date = f(r"(\d{2}/\d{2}/\d{4})")

    ht = nf(f(r"(HT)\s*([\d\s,.]+)"))
    tva = nf(f(r"(TVA)\s*([\d\s,.]+)"))
    ttc = nf(f(r"(TTC)\s*([\d\s,.]+)"))

    taux = 0
    if ht and tva:
        taux = round((tva / ht) * 100)

    if not tva and ht and taux:
        tva = round(ht * taux / 100, 2)

    if not ttc and ht and tva:
        ttc = round(ht + tva, 2)

    # ID_PAIE
    if ttc > 5000:
        id_paie = 2
    else:
        id_paie = 1

    return {
        "ICE": ice,
        "NUM_FACT": num,
        "DATE_FAC": date,
        "M_HT": ht,
        "TVA": tva,
        "TAUX": taux,
        "M_TTC": ttc,
        "ID_PAIE": id_paie,
        "DESIGNATION": "Marchandises"
    }

# ================= UI =================
st.subheader("1️⃣ معلومات الشركة (مرة وحدة)")

col1, col2, col3, col4 = st.columns(4)

with col1:
    raison = st.text_input("اسم الشركة")
with col2:
    ice_company = st.text_input("ICE / IF")
with col3:
    annee = st.text_input("السنة", value="2025")
with col4:
    regime = st.selectbox("نوع التصريح", ["شهري", "ثلاثي"])

regime_code = "01" if regime == "شهري" else "02"
period_max = 12 if regime == "شهري" else 4

st.markdown("---")

st.subheader("2️⃣ ملف EDI الخاوي")
template = st.file_uploader("حط ملف EDI الخاوي (Excel)", type=["xlsx", "xlsm"])

st.markdown("---")

st.subheader("3️⃣ الفواتير")
invoices = st.file_uploader(
    "حط مجموعة الفواتير (PDF / صور)",
    accept_multiple_files=True
)

if template and invoices:
    if st.button("🚀 بدء المعالجة"):
        df_edi = pd.read_excel(template)
        rows = []

        for inv in invoices:
            ocr_text = run_ocr(inv)
            data = analyze_invoice_text(ocr_text)

            data["RAISON_SOCIALE"] = raison
            data["ICE_SOCIETE"] = ice_company
            data["ANNEE"] = annee
            data["REGIME"] = regime_code

            rows.append(data)

        df_new = pd.DataFrame(rows)
        df_final = pd.concat([df_edi, df_new], ignore_index=True)

        st.success("✅ تم تعمير ملف EDI بنجاح")
        st.dataframe(df_final)

        output = io.BytesIO()
        df_final.to_excel(output, index=False)
        st.download_button(
            "📥 تحميل ملف EDI عامر",
            output.getvalue(),
            "EDI_FINAL.xlsx"
        )
