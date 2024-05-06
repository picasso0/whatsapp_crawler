from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService

from webdriver_manager.chrome import ChromeDriverManager
from utils import extract_zip, download_file, is_zip_file, remove_directory, send_data_to_c2
from json import dumps
from time import sleep


class Worker:
    def __init__(self):
        response = send_data_to_c2("POST", "initialize/", {})
        # user_data_file = download_file(response.get("user_data_path"))
        # if user_data_file == False:
        #     return False
        #     # raise HTTPException(status_code=400, detail="Cannot Download User Data File")
        # else:
        #     if is_zip_file(user_data_file) == False:
        #         return False
        #         # raise HTTPException(status_code=400, detail="Invalid zip file provided")
        # extracted_files = extract_zip(user_data_file)
        # remove_directory(user_data_file)
        # self.id = response.get("worker_id")
        self.user_data_path = "user_data_extracted"

    def _get_driver(self):
        print("Setup WebDriver...")
        # Create a UserAgent object
        ua = UserAgent(platforms='pc', os='linux',
                       min_version=120.0, browsers=["chrome"])

        # Get the user agent string for the latest version of Chrome
        chrome_user_agent = ua.random

        browser_option = ChromeOptions()

        browser_option.add_argument('--headless')
        browser_option.add_argument('--disable-dev-shm-usage')
        browser_option.add_argument('--lang=en')
        browser_option.add_experimental_option(
            'prefs', {'intl.accept_languages': 'en,en_US'})

        browser_option.add_argument(
            f"user-data-dir={self.user_data_path}")
        browser_option.add_argument(
            "--user-agent={}".format(chrome_user_agent))
        # For Hiding Browser

        try:
            print("Initializing ChromeDriver...")
            driver = webdriver.Chrome(
                options=browser_option,
            )

            print("WebDriver Setup Complete")
            return driver
        except WebDriverException:
            try:
                print("Downloading ChromeDriver...")
                chromedriver_path = ChromeDriverManager().install()
                chrome_service = ChromeService(
                    executable_path=chromedriver_path)

                print("Initializing ChromeDriver...")
                driver = webdriver.Chrome(
                    service=chrome_service,
                    options=browser_option,
                )

                print("WebDriver Setup Complete")
                return driver
            except Exception as e:
                print(f"Error setting up WebDriver: {e}")

        pass

    async def check_whatsapp_phones(self, phones, report):
        find_count = 0
        start_datetime = datetime.now()
        results = []
        driver = self._get_driver()
        driver.get('https://web.whatsapp.com')
        sleep(4)
        for phone in phones:
            print(f"start {phone.mobile}")
            phone_result = {'mobile': phone.mobile,
                            'find': False, 'whatsapp': {}}
            url = 'https://web.whatsapp.com/send?phone={}'.format(
                phone.mobile)
            sent = False
            driver.get(url)
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@class="x12lqup9 x1o1kx08" and contains(., "Phone number shared via url is invalid")]')))
            except:
                try:
                    element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "header._amid")))
                    try:
                        profile_image_element=""
                        profile_image_element = element.find_element(
                            By.CSS_SELECTOR, 'img')
                        profile_image_element = profile_image_element.get_attribute(
                            "src")
                    except:
                        pass

                    profile_name = element.find_element(
                        By.CSS_SELECTOR, 'div._amie')
                    profile_name = profile_name.find_element(
                        By.CSS_SELECTOR, 'div._amig')
                    profile_name = profile_name.get_attribute("textContent")

                    phone_result['find'] = True
                    phone_result['whatsapp'] = {
                        'name': profile_name,
                        'image': profile_image_element
                    }
                    find_count = find_count+1
                except:
                    pass

            print(f"end {phone.mobile}")
            results.append(phone_result)
        driver.quit()
        end_datetime = datetime.now()
        report = {
            'id': report['id'],
            'start_id': report['start_id'],
            'total_count': report['total_count'],
            'start_datetime': str(start_datetime),
            'end_datetime': str(end_datetime),
            'find_count': find_count
        }
        results = dumps({"results": results, "report": report})
        response = send_data_to_c2("POST", "results/", results)
        return response
