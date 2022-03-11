from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, WebDriverException, UnexpectedAlertPresentException
import sys
import os
from rename import FilenamesToURLs, URLsToFilenames

def main():
    if len(sys.argv) != 4:
        print("This code generates the folder directories source and screenshots and populates them depending on user preference")
        print("Usage: python scrape.py FilenamesOrUrls(0:filenames, 1:urls) TakeScreenshotsBinary(0:false, 1:true) GetSourceBinary")
        print("You can also edit the Selenium Webdriver settings if you so choose")
        exit()
    
    if sys.argv[1] == "0":
        fileDirectory = input("Directory with filenames: ")
    elif sys.argv[1] == "1":
        URLs = input("URL file: ")
    else:
        print("Invalid argument")
        exit()

    if sys.argv[1] == "0":
        try:
            FilenamesToURLs(fileDirectory)
        except Exception:
            print("Invalid file directory")
            exit()

    # For Firefox
    options = FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument('--hide-scrollbars')
    options.add_argument('--disable-gpu')
    driver = webdriver.Firefox(options=options)
    driver.set_window_size(1200, 600)

    if sys.argv[1] == "0":
        with open("URLs.txt", "r") as f:
            URLsToFilenames("URLs.txt")
            lines = f.readlines()
            with open("filenames.txt", "r") as n:
                names = n.readlines()
                if sys.argv[2] == "1":
                    os.mkdir("screenshots")
                    i = 0
                    for line in lines:
                        names[i] = names[i].replace('\n', '')
                        driver.save_screenshot('screenshots/' + names[i] + '.jpg')
                        i += 1
                elif sys.argv[3] == "1":
                    os.mkdir("source")
                    i = 0
                    for line in lines:
                        names[i] = names[i].replace('\n', '')
                        driver.get(line)
                        html = driver.page_source
                        with open('source/' + names[i] + '.html', 'w') as f:
                            f.write(html)
                        i += 1
    else:
        with open(URLs, "r") as f:
            lines = f.readlines()
            URLsToFilenames(URLs)
            with open("filenames.txt", "r") as n:
                names = n.readlines()
                if sys.argv[2] == "1":
                    try:
                        os.makedir("screenshots")
                    except Exception:
                        pass
                    i = 0
                    for line in lines:
                        driver.save_screenshot('screenshots/' + names[i] + '.jpg')
                elif sys.argv[3] == "1":
                    try:
                        os.makedir("source")
                    except Exception:
                        pass
                    i = 0
                    for line in lines:
                        driver.get(line)
                        html = driver.page_source
                        with open('source/' + names[i] + '.html', 'w') as f:
                            f.write(html)


if __name__ == "__main__":
    main()