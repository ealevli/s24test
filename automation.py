import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time

# --- Streamlit Arayüzü Ayarları ---
st.set_page_config(page_title="Siebel Veri Çekme Botu", layout="wide")
st.title("📊 Siebel CRM - Otomatik Veri Çekme Botu")
st.markdown("""
Bu araç, Siebel paneline verdiğiniz kullanıcı bilgileriyle otomatik olarak giriş yapar, 
Case Numaralarını sorgular ve sonuçları size bir tablo olarak sunar.

**Kullanım:**
1.  Siebel giriş bilgilerinizi ve Case Numaralarını girin.
2.  'Verileri Çekmeye Başla' butonuna tıklayın ve işlemin bitmesini bekleyin.
""")

# --- Session State (Oturum Durumu) Yönetimi ---
if 'results' not in st.session_state:
    st.session_state.results = []

# --- Arayüz Elemanları ---
st.sidebar.header("Giriş Bilgileri")
username = st.sidebar.text_input("Kullanıcı Adı (örn: tbdir\\kullanici)")
password = st.sidebar.text_input("Şifre", type="password")

st.header("Case Numaraları")
case_numbers_text = st.text_area(
    "Her satıra bir Case Numarası gelecek şekilde aşağıya yapıştırın:", 
    height=200, 
    key="case_numbers_input"
)

# Tek bir butonla tüm işlemi başlat
if st.button("🚀 Verileri Çekmeye Başla"):
    # Gerekli bilgilerin girilip girilmediğini kontrol et
    if not username or not password or not case_numbers_text.strip():
        st.warning("Lütfen kullanıcı adı, şifre ve en az bir case numarası giriniz.")
    else:
        case_numbers = [line.strip() for line in case_numbers_text.split('\n') if line.strip()]
        st.session_state.results = []  # Her çalıştırmada sonuçları temizle
        driver = None  # Driver'ı başta None olarak ayarla

        try:
            # --- Tarayıcıyı Başlatma ---
            with st.spinner("Tarayıcı başlatılıyor ve ayarlar yapılıyor..."):
                options = Options()
                # Streamlit Cloud'da headless modda (arayüz olmadan) çalışması için gerekli ayarlar
                options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--window-size=1920,1080")
                
                # Streamlit Cloud'da Selenium'u çalıştırmak için standart yapılandırma
                driver = webdriver.Chrome(options=options)

            # --- Giriş İşlemi ---
            with st.spinner("Giriş sayfasına gidiliyor ve login yapılıyor..."):
                url = "https://dtag.tcas.cloud.tbintra.net/siebel/app/callcenter/enu/"
                driver.get(url)

                # DİKKAT: 's_swepi_1', 's_swepi_2' ve 's_swepi_22' ID'leri
                # sizin panelinizin giriş ekranındaki gerçek ID'ler ile değiştirilmelidir.
                user_field = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "s_swepi_1")))
                pass_field = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "s_swepi_2")))
                login_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "s_swepi_22")))

                user_field.send_keys(username)
                pass_field.send_keys(password)
                login_button.click()
            
            st.success("✅ Giriş başarılı!")

            # --- Veri Çekme İşlemi ---
            st.header("İşlem Durumu")
            progress_bar = st.progress(0)
            status_text = st.empty()
            total_cases = len(case_numbers)

            for i, case in enumerate(case_numbers):
                status_text.info(f"🔄 Sorgulanıyor: {case} ({i+1}/{total_cases})")
                try:
                    search_box = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "dashsearchinp")))
                    search_box.clear()
                    search_box.send_keys(case)
                    search_box.send_keys(Keys.RETURN)
                    time.sleep(3)

                    driver_name = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "s_1_1_80_0"))).get_attribute("value")
                    driver_phone = driver.find_element(By.NAME, "s_1_1_82_0").get_attribute("value")

                    st.session_state.results.append({
                        "Case Number": case, "Müşteri Adı": driver_name, "Telefon Numarası": driver_phone, "Durum": "Başarılı"
                    })
                except Exception as e:
                    st.session_state.results.append({
                        "Case Number": case, "Müşteri Adı": "HATA", "Telefon Numarası": "HATA", "Durum": f"Veri çekilemedi"
                    })
                progress_bar.progress((i + 1) / total_cases)
            
            status_text.success("✅ Tüm işlemler tamamlandı!")

        except Exception as e:
            st.error(f"❌ Bir hata oluştu: {e}")
            st.error("Giriş bilgilerinizi veya koddaki element ID'lerini kontrol edin. Eğer siteniz bir VPN gerektiriyorsa, bu uygulama Streamlit Cloud üzerinden çalışmayabilir.")
        
        finally:
            # İşlem bitince veya hata olunca tarayıcıyı güvenli bir şekilde kapat
            if driver:
                driver.quit()

# --- Sonuçları Gösterme ---
if st.session_state.results:
    st.header("Sonuçlar")
    df = pd.DataFrame(st.session_state.results)
    st.dataframe(df)

    @st.cache_data
    def convert_df_to_csv(df_to_convert):
        return df_to_convert.to_csv(index=False).encode('utf-8-sig')

    csv = convert_df_to_csv(df)
    st.download_button(
        label="📥 Sonuçları Excel (CSV) Olarak İndir",
        data=csv,
        file_name='siebel_case_sonuclari.csv',
        mime='text/csv',
    )
