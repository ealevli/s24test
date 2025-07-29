import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Sayfa ayarları
st.set_page_config(page_title="TCAS Case Scraper", layout="wide")
st.title("🚛 Daimler TCAS Case Data Scraper")

# Tarayıcı durumu yönetimi
if 'driver' not in st.session_state:
    st.session_state.driver = None

url = "https://dtag.tcas.cloud.tbintra.net/siebel/app/callcenter/enu/?SWECmd=GotoView&SWEView=CAC+S24+Phone+Fix+View&SWERF=1&SWEHo=&SWEBU=1"

# Tarayıcıyı başlat
if st.button("1️⃣ Tarayıcıyı Aç ve Giriş Yap"):
    try:
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument('--disable-blink-features=AutomationControlled')

        driver = uc.Chrome(options=options)
        driver.get(url)

        st.session_state.driver = driver
        st.success("✅ Tarayıcı açıldı. Lütfen giriş yapın. Giriş tamamlandıktan sonra aşağıdaki 'Devam Et' butonuna tıklayın.")
    except Exception as e:
        st.error(f"❌ Tarayıcı başlatılamadı: {e}")

# Devam Et butonu: Giriş tamamlandıysa
if st.session_state.driver is not None:
    st.markdown("---")
    st.subheader("2️⃣ Case Numaralarını Girin ve Verileri Çekin")

    case_input = st.text_area("Case Numaralarını girin (her satıra bir tane):")
    case_list = [c.strip() for c in case_input.strip().splitlines() if c.strip()]

    if st.button("🔍 Devam Et ve Verileri Çek"):
        results = []
        driver = st.session_state.driver

        for case in case_list:
            try:
                # Case arama alanını bul
                search_box = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.ID, "dashsearchinp"))
                )
                search_box.clear()
                search_box.send_keys(case)
                search_box.send_keys(Keys.RETURN)
                time.sleep(3)

                # İsim ve telefon numarasını çek
                driver_name = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "s_1_1_80_0"))
                ).get_attribute("value")

                driver_phone = driver.find_element(By.NAME, "s_1_1_82_0").get_attribute("value")

                results.append({"Case Number": case, "Driver Name": driver_name, "Driver Phone": driver_phone})
            except Exception as e:
                results.append({"Case Number": case, "Driver Name": "HATA", "Driver Phone": str(e)})

        df = pd.DataFrame(results)
        st.success("Veriler çekildi!")
        st.dataframe(df)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Excel Olarak İndir", csv, "case_data.csv")
