# Program to send bulk messages through WhatsApp web from an excel sheet without saving contact numbers
# Author @inforkgodara

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
import pandas

excel_data = pandas.read_excel('phones.xlsx', sheet_name='phones')

count = 0
options = webdriver.ChromeOptions()
options.add_argument(
    "user-data-dir=/Users/imanpirooz/repo/whatsapp-bulk-messages-without-saving-contacts/chrome_user_data")

breakpoint()
driver = webdriver.Chrome(options=options)

driver.get('https://web.whatsapp.com')
sleep(4)
for column in excel_data['Contact'].tolist():
    try:
        url = 'https://web.whatsapp.com/send?phone={}'.format(
            excel_data['Contact'][count])
        sent = False
        # It tries 3 times to send a message in case if there any error occurred
        driver.get(url)
        sleep(6)
        try:
            element = driver.find_element(By.CSS_SELECTOR,'header._amid')
            breakpoint()
            profile_image_element=element.find_element(By.CSS_SELECTOR,'img')
            profile_image_element = profile_image_element.get_attribute("src")
            
            profile_name=element.find_element(By.CSS_SELECTOR,'div._amie')
            profile_name=profile_name.find_element(By.CSS_SELECTOR,'div._amig')
            profile_name=profile_name.get_attribute("textContent")
            
            print(profile_name , profile_image_element)
            print("/n")
            
        except Exception as e:
            print("cannot open chat of this phonenumber has not whatsapp " +
                  str(excel_data['Contact'][count]))
        count = count + 1
    except Exception as e:
        print("Sorry this phonenumber has not whatsapp " +
              str(excel_data['Contact'][count]))
driver.quit()
print("The script executed successfully.")
