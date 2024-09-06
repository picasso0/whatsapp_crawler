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
    TimeoutException
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService

from webdriver_manager.chrome import ChromeDriverManager
from utils import extract_zip, download_file, is_zip_file, remove_directory, send_data_to_c2
from json import dumps
from time import sleep
import logging
import sys

# SET LOGGING
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

logger.info("start")

class Worker:
    
    def initialize(self):
            logger.info("start initialize")
            try:
                extracted_folder = "user_data_extracted"
                download_directory="downloads";
                remove_directory(download_directory)
                remove_directory(extracted_folder)
                
                response = send_data_to_c2("POST", "initialize/", {})
                if response.status_code==500:
                    logger.error("error in c2 initialize ( check c2 logs )")
                    return False
                if response.status_code==401:
                    logger.error("unauth please check token")
                    return False
                response=response.json()
                user_data_file = download_file(response.get("user_data_path"),download_directory)
                
                if user_data_file == False:
                    logger.error("c2 dont sended any user data")
                    return False
                else:
                    if is_zip_file(user_data_file) == False:
                        logger.error("c2 dont sended any user data")
                        return False
                    
                extracted_files = extract_zip(user_data_file, extracted_folder)
                remove_directory(download_directory)
                self.id = response.get("worker_id")
                self.user_data_path = extracted_folder
            except Exception as e:
                logger.error("faild  to connection with c2")
                return False
            logger.info("end initialize")

    def im_ready(self):
         send_data_to_c2("GET", "send_status/", "status=0")
         logger.info("im ready")
         
    def _get_driver(self):
        logger.info("Setup WebDriver...")
        # Create a UserAgent object
        ua = UserAgent(platforms='pc', os='linux',
                       min_version=128.0, browsers=["chrome"])

        # Get the user agent string for the latest version of Chrome
        chrome_user_agent = ua.random

        browser_option = ChromeOptions()
        browser_option.add_argument("--no-sandbox")
        browser_option.add_argument("--ignore-certificate-errors")
        browser_option.add_argument("--disable-gpu")
        browser_option.add_argument("--log-level=3")
        browser_option.add_argument("--disable-notifications")
        browser_option.add_argument("--disable-popup-blocking")
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
            logger.info("Initializing ChromeDriver...")
            driver = webdriver.Chrome(
                options=browser_option,
            )

            logger.info("WebDriver Setup Complete")
            return driver
        except :
            try:
                logger.info("Downloading ChromeDriver...")
                chromedriver_path = ChromeDriverManager().install()
                chrome_service = ChromeService(
                    executable_path=chromedriver_path)

                logger.info("Initializing ChromeDriver...")
                driver = webdriver.Chrome(
                    service=chrome_service,
                    options=browser_option,
                )

                logger.info("WebDriver Setup Complete")
                return driver
            except Exception as e:
                logger.info(f"Error setting up WebDriver: {e}")

        pass
    
    async def check_whatsapp_phone(self, driver, phone):
        phone_result = {'mobile': phone.mobile,
                        'find': False, 'whatsapp': {}}
        url = 'https://web.whatsapp.com/send?phone={}'.format(
            phone.mobile)
        try:
            driver.get(url)
        except TimeoutException:
            logger.error(f"driver.get(url) to {url} failed")
            return 0
        try:
            element = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.XPATH, '//div[@class="x12lqup9 x1o1kx08" and contains(., "Phone number shared via url is invalid")]')))
        except:
            sleep(7)
            try:
                last_seen = driver.find_element(By.CSS_SELECTOR, 'div.x78zum5.x1cy8zhl.xisnujt.x1nxh6w3.xcgms0a.x16cd2qt').text
            except:
                last_seen=""
            try:
                element = WebDriverWait(driver, 12).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "header._amid._aqbz")))
                try:
                    element.click()
                except:
                    element = WebDriverWait(driver, 12).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.x1c4vz4f.x2lah0s.xdl72j9.x1i4ejaq.x1y332i5"))).click()
                sleep(1)
                element = WebDriverWait(driver, 12).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div._aigv._aig-._aohg")))
                
                try:
                    profile_image = element.find_element(By.CSS_SELECTOR, 'img').get_attribute("src")
                except:
                    profile_image=""
                
                try:
                    profile_name = element.find_element(By.CSS_SELECTOR, 'div._aou8._aj_h').text
                except:
                    profile_name=""
                
                try:
                    category = element.find_element(By.CSS_SELECTOR, 'div.x1f6kntn.x1anpt5t.x37zpob.xyorhqc').text
                except:
                    category=""
                    
                try:
                    business = element.find_element(By.CSS_SELECTOR, 'div.x13mwh8y.x1q3qbx4.x1wg5k15.xajqne3.x1n2onr6.x1c4vz4f.x2lah0s.xdl72j9.xyorhqc.x13x2ugz.x178xt8z.x13fuv20.x1sdoubt.x1f6kntn').text
                    business=True
                except:
                    business=""
                
                try:
                    bio_text=[]
                    bio_contents = element.find_elements(By.CSS_SELECTOR, 'div.xqui205')
                    for bio_content in bio_contents : bio_text.append(bio_content.text)
                    bio_text = '\n'.join(bio_text)
                except:
                    bio_text=""                
                
                phone_result['has_whatsapp'] = True
                phone_result['whatsapp'] = {
                    'profile_name': profile_name,
                    'image': profile_image,
                    'category': category,
                    'business': business,
                    'bio': bio_text,
                    'last_seen': last_seen,
                }
                find_count = find_count+1
                logger.info(f"_________________FINDED {phone.mobile}________________________")
            except:
                pass
        return phone_result
    
    async def check_whatsapp_phones(self, phones, report):
        failed_numbers = []
        find_count = 0
        start_datetime = datetime.now()
        results = []
        driver = self._get_driver()
        driver.get('https://web.whatsapp.com')
        try:
            element = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label='Chats']")))
        except:
            return send_data_to_c2("GET", "send_status/", "status=2")
        logger.info(f"logged in to whatsapp")
        for index_number, phone in enumerate(phones):
            logger.info(f"start {phone.mobile}")
            phone_result = await self.check_whatsapp_phone(driver=driver,phone=phone)
            if phone_result == 0:
                for failed_phone in phones[index_number:]:
                    failed_numbers.append(failed_phone.dict())
                break
            if phone_result['find']==True:
                find_count=find_count+1
            logger.info(f"end {phone.mobile}")
            
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
        if len(failed_numbers) :
            logger.info({"results": results, "report": report, "failed_numbers": failed_numbers})
        results = dumps({"results": results, "report": report, "failed_numbers": failed_numbers})
        response = send_data_to_c2("POST", "results/", results)
        return response
