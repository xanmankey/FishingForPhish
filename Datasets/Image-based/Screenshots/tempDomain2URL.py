# This is a quick file that I'll delete later on; it's for renaming the domains to urls in the file
# I've already ran it on my dataset, but if you want to use it on another dataset where you only know domains it may come in handy to get the full URLs
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


driver.close()
driver.quit()
