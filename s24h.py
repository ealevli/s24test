# app.py
import streamlit as st
import pandas as pd
import time
import io
import base64

from automation import launch_driver, extract_case_data

@st.cache_data
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_bg_from_local(image_file):
    file_extension = image_file.split('.')[-1].lower()
    image_type = 'image/jpeg' if file_extension in ['jpg', 'jpeg'] else 'image/png'
    image_as_base64 = get_base64_of_bin_file(image_file)
    bg_image_style = f"""
    <style>
    .stApp {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), url("data:{image_type};base64,{image_as_base64}");
        background-size: cover;
    }}
    label, h1, h2, h3, p, span, div {{
        color: white !important;
    }}
    </style>
    """
    st.markdown(bg_image_style, unsafe_allow_html=True)

st.set_page_config(page_title="S24H Veri Çekme Aracı", layout="wide")
set_bg_from_local("assets/background.jpg")

st.markdown("<h1 style='text-align: center;'>S24H Veri Çekme Otomasyon Aracı</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Bu aracı kullanmadan önce VPN bağlantısınızı aktif hale getirip manuel olarak siteye giriş yapın.</p>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Vaka numaralarını içeren Excel dosyasını yükleyin (.xlsx)", type=["xlsx"])
case_list = []

driver = launch_driver()

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("✅ Dosya yüklendi. ")
        st.dataframe(df.head())

        selected_column = st.selectbox("Vaka numaralarını içeren sütunu seçin:", df.columns)
        case_list = df[selected_column].dropna().astype(str).tolist()

        if st.button("🔓 Login Sayfasını Aç"):
            driver.get("https://dtag.tcas.cloud.tbintra.net/siebel/app/callcenter/enu/?SWECmd=GotoView&SWEView=CAC+S24+Phone+Fix+View")
            st.info("Lütfen giriş işlemini tamamlayın, sonra 'Devam Et' butonuna basın.")

        if case_list and st.button("✅ Devam Et ve Verileri Çek"):
            status = st.empty()
            results = []

            for i, case in enumerate(case_list):
                status.info(f"🔍 {i+1}/{len(case_list)}: {case}")
                try:
                    data = extract_case_data(driver, case)
                    results.append(data)
                except Exception as e:
                    results.append({"Vaka Numarası": case, "Müşteri Adı": "Hata", "Telefon Numarası": "Hata", "Durum": str(e)})

            df_result = pd.DataFrame(results)
            st.dataframe(df_result)

            buffer = io.BytesIO()
            df_result.to_excel(buffer, index=False)
            st.download_button("📥 Excel olarak indir", data=buffer.getvalue(), file_name="sonuclar.xlsx")

    except Exception as e:
        st.error(f"Excel dosyası okunurken hata oluştu: {e}")
