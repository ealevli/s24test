import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

_driver = None  # Global driver nesnesi

def launch_driver():
    global _driver
    if _driver:
        return _driver

    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    _driver = uc.Chrome(options=options)
    return _driver

def extract_case_data(driver, case_number):
    wait = WebDriverWait(driver, 20)

    search_box = wait.until(EC.presence_of_element_located((By.ID, "dashsearchinp")))
    search_box.clear()
    search_box.send_keys(case_number)

    search_button = driver.find_element(By.ID, "dashsearchbut")
    search_button.click()

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label='Driver Name']")))

    name = driver.find_element(By.CSS_SELECTOR, "input[aria-label='Driver Name']").get_attribute("value")
    phone = driver.find_element(By.CSS_SELECTOR, "input[aria-label='Driver Phone']").get_attribute("value")

    return {
        "Vaka Numarası": case_number,
        "Müşteri Adı": name,
        "Telefon Numarası": phone,
        "Durum": "Başarılı"
    }
