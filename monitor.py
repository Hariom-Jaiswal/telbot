from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time
import os
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

CASE_NO = "HCBM020255172024"
STATE_FILE = "last_date.txt"


def send_message(msg):
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )

    print("Telegram response:", response.text)


def get_latest_date():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # comment this while testing if you want to see browser
    # options.add_argument("--headless")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        driver.get("https://bombayhighcourt.gov.in/bhc/casestatus/casenumber")
        time.sleep(3)

                # Click CNR / CIN No tab first
        tabs = driver.find_elements(By.XPATH, "//*[contains(text(),'CNR / CIN No')]")

        clicked = False
        for tab in tabs:
            if tab.is_displayed():
                tab.click()
                clicked = True
                break

        if not clicked:
            raise Exception("Could not click CNR tab")

        time.sleep(2)
        # Enter CNR
        inputs = driver.find_elements(By.NAME, "cnrinp")

        cnr_box = None
        for inp in inputs:
            if inp.is_displayed() and inp.is_enabled():
                cnr_box = inp
                break

        if cnr_box is None:
            raise Exception("Visible CNR input not found")

        cnr_box.send_keys(CASE_NO)

        # Click search button
        buttons = driver.find_elements(By.TAG_NAME, "button")

        for btn in buttons:
            text = btn.text.strip().lower()
            if btn.is_displayed() and ("fetch" in text or "search" in text):
                btn.click()
                break

        time.sleep(4)

        # Click Orders/Judgments tab
        elements = driver.find_elements(By.XPATH, "//*[contains(text(),'Orders/Judgments')]")
        for el in elements:
            if el.is_displayed():
                el.click()
                break

        time.sleep(3)

        # Grab all page text
        rows = driver.find_elements(By.TAG_NAME, "tr")

        dates = []

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")

            if len(cells) >= 4:
                text = cells[2].text.strip()   # Order Date column

                if "/" in text and len(text) == 10:
                    dates.append(text)

        print("Table dates:", dates)

        if dates:
            return dates[0]   # first row only
        return None

    finally:
        driver.quit()


def read_last_date():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    return None


def save_date(date):
    with open(STATE_FILE, "w") as f:
        f.write(date)


latest_date = get_latest_date()
print("Latest:", latest_date)

if latest_date is None:
    print("No date found.")
    exit()

old_date = read_last_date()

if old_date is None:
    save_date(latest_date)

    send_message(
        f"✅ Court bot started successfully\n"
        f"Case: {CASE_NO}\n"
        f"Current latest date: {latest_date}"
    )

    print("Initial saved and notification sent.")
    exit()

if old_date != latest_date:
    alert = (
        f"🚨 Bombay High Court update detected!\n"
        f"Case: {CASE_NO}\n"
        f"Old Date: {old_date}\n"
        f"New Date: {latest_date}"
    )

    for i in range(15):   # send 5 times
        send_message(alert)
        time.sleep(5)    # wait 5 sec between messages

    save_date(latest_date)
    print("Update detected and alerts sent.")

    print("Update sent.")
else:
    print("No change.")