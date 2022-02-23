# This is a quick file that I'll delete later on; it's for renaming the domains to urls in the file
# I haven't actually ran this yet; I'll run it when I get a chance and just end up debugging the other code (combined.py)
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time

# Working test file
options = FirefoxOptions()
options.add_argument("--headless")
driver = webdriver.Firefox(options=options)
driver.get('https://www.google.com/')

url = driver.current_url
element_present = EC.visibility_of_all_elements_located((By.TAG_NAME, "a"))
WebDriverWait(driver, 10).until(element_present)
print("worK")

# for element in aTags:
#     href = element.get_attribute("href")
#     print(href)

driver.close()
driver.quit()