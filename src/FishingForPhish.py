# FishingForPhish.py: contains the major classes, functions, and objects
# I used throughout this research
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
import weka.core.jvm as jvm
from weka.core.dataset import Attribute, Instance, Instances
from weka.core.converters import Saver
from weka.filters import Filter
import weka.core.packages as packages
from weka.attribute_selection import ASSearch, ASEvaluation, AttributeSelection
import time
import pyshorteners
from bs4 import BeautifulSoup
import subprocess
from collections import Counter
import requests
import os
from filetype import is_image
import sqlite3 as SQL
import cssutils
import logging
from datetime import datetime
from urllib import parse
from urllib3.exceptions import InsecureRequestWarning
import validators
from PIL import Image
import imagehash


class fisher():
    '''A class for initializing Selenium, Beautiful Soup, and the project filesystem'''

    def __init__(self, dataDir="data", driver=None, BS=None, **kwargs):
        '''Defines the dataDir, driver, and BS attributes, where dataDir is the home directory
        containing a screenshots directory for screenshots, an html directory for html,
        a css directory for css, and a datasets directory for datasets, and the driver and
        BS attributes store the current state of the Selenium Webdriver and Beautiful Soup
        objects respectively'''
        super().__init__(**kwargs)
        self.dataDir = dataDir
        self.driver = driver
        self.BS = BS
        if not os.path.isdir(self.dataDir):
            if self.dataDir == "data":
                os.mkdir("data")
            else:
                raise FileNotFoundError("""dataDir needs to be a valid directory""")
        subDirectories = ["screenshots", "html", "css", "datasets"]
        for subdir in map(lambda subdir: self.dataDir + "/" + subdir, subDirectories):
            if not os.path.isdir(subdir):
                os.mkdir(subdir)

    def installResources(self):
        '''Installs the chiSquaredAttributeEval package (a Feature Selection method),
        the SMOTE oversampler, and the Wayback Machine Firefox add_on
        (the resources I used for this project that required download)'''
        packages.install_package('chiSquaredAttributeEval')
        packages.install_package('SMOTE')
        file = requests.get(
            'https://addons.mozilla.org/firefox/downloads/file/3911106/wayback_machine-3.0-fx.xpi',
            allow_redirects=True)
        open(
            self.dataDir +
            '/wayback_machine-3.0-fx.xpi',
            'wb').write(
            file.content)

    def initializeSelenium(self, add_ons=None):
        '''Initializes Selenium with any add_ons that are passed to the method'''
        options = FirefoxOptions()
        options.add_argument("--headless")
        options.add_argument('--hide-scrollbars')
        options.add_argument('--disable-gpu')
        options.set_preference("javascript.enabled", False)
        driver = webdriver.Firefox(options=options)
        for add_on in add_ons:
            if add_on[len(add_on) - 4:len(add_on)].upper() == ".XPI":
                try:
                    driver.install_addon(add_on, temporary=True)
                except Exception:
                    logging.warning(add_on + " is not a valid Firefox addon!")
                    continue
        self.driver = driver
        self.driver.implicitly_wait(20)

    def initializePWW3(self, jvmOptions):
        '''Starts jvm using a list of optional parameters'''
        jvm.start(option for option in jvmOptions)

    def initializeBS(self, html):
        '''Initializes a Beautiful Soup object BS. Not called with initializeAll() as it requires
        the html of a website as an argument'''
        self.BS = BeautifulSoup(html, "html.parser")

    def initializeAll(self):
        '''A joint method that calls all the initialize methods (except for initializeBS). Packages
        are enabled, related resources are installed, and excessive warnings are limited.'''
        options = ["system_cp", "packages"]
        requests.packages.urllib3.disable_warnings(
            category=InsecureRequestWarning)
        cssutils.log.setLevel(logging.CRITICAL)  ### Terry ### Love logging
        self.initializePWW3(options)
        self.installResources()
        options = ['wayback_machine-3.0-fx.xpi']
        self.initializeSelenium(options)


class scrape(initialize):
    '''A class (inheriting from initialize) that defines useful scrape objects and methods'''

    def __init__(
            self,
            urlFile,
            database=None,
            screenshotDir=None,
            htmlDir=None,
            cssDir=None,
            cursor=None,
            id=0,
            errors={},
            **kwargs):
        '''Inherits the dataDir, driver, and BS attributes, and creates the necessary attribute,
        urlFile (a .txt file containing urls, one per line), and the optional
        database, screenshotDir, htmlDir, cssDir, cursor, id, and errors attributes.
        Database is for specifying a database that you want to record data in
        (specifically useful for storing hashes and database functionality),
        cursor is the associated sqlite3 cursor related to the database
        (initialized later on, really no reason to pass this as an argument),
        screenshotDir, htmlDir, and cssDir are directories containing code associated with urls
        in the urlFile that has already been scraped (useful for minimizing unnecessary scraping),
        errors is a dictionary of errors useful for debugging and collecting site information in
        the (optional but recommended) database, and id is the id number used for filenames
        and associated with primary keys in the database (specifically in the metadata, pageData,
        imageData, otherData, and allFeatures tables... the rest can be joined if necessary)'''
        super().__init__(**kwargs)
        self.urlFile = urlFile
        self.screenshotDir = screenshotDir
        self.htmlDir = htmlDir
        self.cssDir = cssDir
        self.database = database
        self.cursor = cursor
        self.id = id
        self.errors = errors
        if not os.path.isfile(self.urlFile):
            raise FileNotFoundError(
                """urlFile needs to be a path to a file with urls!""")
        else:
            with open(self.urlFile, "r") as f:
                ### Terry ### From the docs (since you're looping anyway):
                ### Terry ### For reading lines from a file, you can loop over the file object. This is memory efficient, fast, and leads to simple code:
                ### Terry ###
                ### Terry ### >>>
                ### Terry ### >>> for line in f:
                ### Terry ### ...     print(line, end='')
                ### Terry ### ...
                ### Terry ### This is the first line of the file.
                ### Terry ### Second line of the file
                urls = f.readlines()
                for url in urls:
                    url = url.replace("\n", "")
                    url = url.strip()
                    if not validators.url(url):
                        raise ValueError(
                            """Sorry, are you sure urlFile contains valid urls?""")
        if self.screenshotDir:
            if not os.path.isdir(self.screenshotDir):
                raise FileNotFoundError(
                    """screenshotDir needs to be a path to a directory with screenshots!""")
            ### Terry ### What is being toggled? Can you use a boolean that describes the reason is being extracted from the fist line?
            ### Terry ### Maybe extractedID = False, or maybe use if not self.id: instead of another variable
            toggle = 0 ### Terry ### What is being toggled? Can you use a boolean that describes
            for filename in os.listdir(self.screenshotDir):
                if toggle == 0:
                    self.id = filename[0:2]
                    self.id = self.id.replace("_", "")
                    self.id = int(self.id)
                    toggle += 1
                if is_image(filename):
                    continue
                else:
                    raise ValueError(
                        """Are you sure all the files in your screenshot directory are images?""")
        if self.htmlDir:
            if os.path.isdir(self.htmlDir):
                for filename in os.listdir(self.htmlDir):
                    if self.id == 0:
                        self.id = filename[0:2]
                        self.id = self.id.replace("_", "")
                        self.id = int(self.id)
                        toggle += 1 ### Terry ### is this an inconsistent use of toggle with self.id == 0 ?
                    ### Terry ### Consider using os.path (or pathlib) to extract the extension in an OS independent way
                    if filename[len(filename) -
                                5:len(filename)].upper() != ".HTML":
                        raise ValueError(
                            """Are you sure the files in htmlDir are all .html files?""")
        # Technically, the css files are never actually used,
        # but it's still important to have them for future research
        if self.cssDir:
            if os.path.isdir(self.cssDir):
                for filename in os.listdir(self.cssDir):
                    if self.id == 0:
                        self.id = filename[0:2]
                        self.id = self.id.replace("_", "")
                        self.id = int(self.id)
                        toggle += 1
                    if filename[len(filename) -
                                4:len(filename)].upper() != ".CSS":
                        raise ValueError(
                            """Are you sure the files in cssDir are all .css files?""")
        if self.database:
            if os.path.isfile(self.database):
                try:
                    db = SQL.connect(self.database)
                except Exception:
                    raise FileNotFoundError(
                        """Sorry, can't connect to that database!""")
                self.cursor = db.cursor()
                self.cursor.execute(
                    'SELECT name FROM sqlite_master WHERE TYPE = "table"')
                # Verifying db by using table names; efficient, but not thorough
                tables = {
                    "metadata": "CREATE TABLE metadata (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT UNIQUE, time INT, classification TEXT)",
                    "pageData": "CREATE TABLE pageData (id INTEGER PRIMARY KEY, externalURL FLOAT, redirectURL FLOAT, hostnameMismatch BINARY, numDash INT, numEmail INT, numDots INT)",
                    "errors": "CREATE TABLE errors (error TEXT)",
                    "imageData": "CREATE TABLE imageData (id INTEGER PRIMARY KEY, )",
                    "otherData": "CREATE TABLE otherData (id INTEGER PRIMARY KEY, numLinks INT, urlLength INT)",
                    "allFeatures": "CREATE TABLE allFeatures (id INTEGER PRIMARY KEY, )",
                    "hashes": "CREATE TABLE hashes (phash INT, dhash INT, url TEXT)"}
                for table in self.cursor.fetchall():
                    if table[0] in tables:
                        continue
                    else:
                        self.cursor.execute(tables[table[0]])
                if self.id == 0:
                    self.id = self.cursor.execute(
                        "SELECT id FROM metadata ORDER BY DESC LIMIT 1")
                    self.id = int(id[0]['id'])
                    if self.id == '':
                        self.id = 0

    def closeSelenium(self):
        '''Closes and quits Selenium using the Selenium.close() and Selenium.quit() methods.
        Should be called once the webscraping process is finished.'''
        self.driver.close()
        self.driver.quit()

    def shorten(self, url):
        '''Shortens the url using pyshorteners and the clckru shortener. 5 unique characters are
        generated at the end of the url which are then used to rename the file, and once the id in
        front of the filename is removed, https://clck.ru/ can be added back to the url and combined
        with the expand() method below to get the original url from a filename'''
        clckruShortener = pyshorteners.Shortener()
        shortUrl = clckruShortener.clckru.short(url)
        return shortUrl

    def expand(self, urlID):
        '''Expands a filename into the url associated with the file using pyshorteners and clck.ru.
        Explained more in the shorten() function above'''
        clckruShortener = pyshorteners.Shortener()
        filename = "https://clck.ru/" + urlID
        filename = filename.replace("_" + self.id + "_", "")
        url = clckruShortener.clckru.expand(filename)
        return url

    def generateFilename(self, url):
        '''A convenience method for generating a filename to name files associated with a website.
        Follow the naming conventions of "_<self.id>_<final 5 characters of shortened url>.png".'''
        shortUrl = self.shorten(url)
        filename = shortUrl.replace("https://clck.ru/", "")
        filename = "_" + str(self.id) + "_" + filename
        return filename

    ### Terry ### Does saveScreenshot assume that siteValidation was called first to retrievethe URL? If so, it should
    ### Terry ### check that the URL was retrieved (to help developers who forget to call in order).
    def saveScreenshot(self, url):
        '''Method for saving a screenshot of the full website. Scrolls the page (if possible) to get
        the height and width of a website. A minimum height and width of 10000 (unlikely to ever
        be hit unless intentional) are set to help prevent Selenium crashing.
        The screenshot is saved at dataDir/screenshots/filename.png (see the generate filename
        method above for more information regarding filenames)'''
        filename = self.generateFilename(url)
        original_size = self.driver.get_window_size()
        required_width = self.driver.execute_script(
            'return document.body.parentNode.scrollWidth')
        required_height = self.driver.execute_script(
            'return document.body.parentNode.scrollHeight')
        self.driver.set_window_size(
            min(10000, required_width), min(10000, required_height))
        self.driver.find_element(
            By.TAG_NAME,
            'body').screenshot(
            self.dataDir +
            "/screenshots/" +
            filename +
            ".png")
        self.driver.set_window_size(
            original_size['width'],
            original_size['height'])

    def siteValidation(self, url):
        '''Method that attempts to validate a site, specifically checking if Selenium can
        access the website, the website's url, and if the requests library does not return a
        404 error (which is often the case due to the slippery nature of phishing websites)'''
        try:
            self.driver.get(url)
        except Exception as e:
            self.errors.update(url=e)
            return False
        try:
            url = self.driver.current_url
        except Exception:
            time.sleep(10)
            try:
                url = self.driver.current_url
            except Exception as e:
                self.errors.update(url=e)
                return False
        try:
            if requests.head(url, verify=False, timeout=5).status_code == 404:
                self.errors.update(url=404)
                return False
        except Exception as e:
            self.errors.update(url=e)
            return False
        return True, url

    ### Terry ### If you want a particular string format, can you use strftime() instead of parsing the string?
    ### Terry ### Note, assuming a particular string format, if you don't explicitly specify it (e.g. str(now)) is brittle
    ### Terry ### time = datetime.now().strftime("%H:%M:%S")
    ### Terry ### https://www.w3schools.com/python/gloss_python_date_format_codes.asp
    def getTime(self):
        '''Generates a time value (dependent on location; the time used for the database at TODO is in
        Central time.'''
        time = str(datetime.now())
        time = time[11:19]
        hour = int(time[:2])
        meridian = time[8:]
        # Special-case for 12AM
        if (hour == 12):
            hour = 0
        if (meridian == 'PM'):
            hour += 12
        time = "%02d" % hour + time[2:8]
        return time


class page(scrape):
    '''A class for scraping page-based features'''

    def __init__(self, pageFeatures=None, **kwargs):
        '''Inherits all previous attributes, adds an optional attribute called pageFeatures
        (although the purpose of the function is to populate the pageFeatures list, so there
        isn't much of a point in passing in a value pageFeatures. If you already have a value,
        I recommend either scraping image data as well
        or creating an instance of the combine class to create datasets of your data)'''
        super().__init__(**kwargs)
        self.pageFeatures = pageFeatures

    def getPageFeatures(self, url):
        '''Searches through the html of a url to get the specified page-features.
        These features are defined in the research paper at TODO.'''
        # Search for elements with links
        ### Terry ### Whenand where was the URL loaded?
        aTags = self.driver.find_elements(By.TAG_NAME, "a")
        numLinks = len(aTags)
        features = []

        # Initialize arrays for storing the top 4 HTML-scraped features
        redirect = []
        mailTo = []
        external = []
        notHostname = []

        # The search is on!
        # Iterate through <a> tags, and check for link attributes
        if len(aTags) != 0:
            m = 0 ### Terry ### Use a more descriptive name (tagCount?)
            for element in aTags:
                # A time.sleep is added so the webdriver can process the element accordingly.
                # In addition to a limit of 1000 <a> tags
                time.sleep(0.01)
                if m >= 1000:
                    break
                try:
                    parsed = parse.urlparse(url) ### Terry ### Is the same URL parsed over and over?
                except Exception as e:
                    self.errors.update(url=e)
                    break
                # Check all <a> for the href element
                ### Terry ### I don't follow the repeated find_elements or repeated get_attribute calls in the exceptions
                try:
                    href = element.get_attribute("href")
                except Exception:
                    newTags = self.driver.find_elements(By.TAG_NAME, "a")
                    try:
                        href = newTags[m].get_attribute("href")
                    except Exception as e:
                        self.errors.update(url=e)
                        continue
                checkRequest = 0
                # Ignoring JS redirect urls
                if href:
                    if 'javascript:' not in href:
                        try:
                            response = requests.head(
                                href, verify=False, timeout=10)
                        except Exception:
                            checkRequest = 1
                    if "mailto:" in href:
                        mailTo.append(href)
                    if checkRequest == 0:
                        if response.url == url:
                            redirect.append(href)
                    if checkRequest == 0:
                        if parsed.netloc != url:
                            external.append(href)
                    notHostname.append(parsed.netloc)
                else:
                    continue
            m += 1

        # Store totals for table iteration
        numExternal = len(external)
        numMail = len(mailTo)
        numRedirects = len(redirect)

        if len(notHostname) != 1 and notHostname[0] != 0:
            hostname = parse.urlparse(url)
            numHostname = Counter(notHostname)
            freqHostname = numHostname.most_common(1)[0][0]
            if freqHostname == hostname.netloc:
                numNotHostname = 1
            else:
                numNotHostname = 0
        else:
            numNotHostname = 0

        # check and store number of dashes and number of periods in the URL
        numDashes = 0
        numPeriods = 0
        for char in url:
            if char == '-':
                numDashes += 1
            if char == '.':
                numPeriods += 1

        # Store the data in a double array so it can be iterated over
        try:
            features.append(numExternal / numLinks)
        except ZeroDivisionError:
            features.append(0)

        # domain-name mismatch is a binary (adds up the most frequent hostname,
        # and compares it to the domain name)
        features.append(numNotHostname)

        # numRedirects is a percent
        try:
            features.append(numRedirects / numLinks)
        except ZeroDivisionError:
            features.append(0)

        # numMail, numDashes, and numPeriods are numeric
        features.append(numMail)
        features.append(numDashes)
        features.append(numPeriods)
        return features

    def pageScrape(self):
        '''Automates the page-based scraping process by reading from the url file, validating the url,
        taking a screenshot (if necessary), saving html and css (if necessary), and then generating
        features by using Selenium and Beautiful Soup analysis'''
        # Begin to scrape using provided urls
        with open(self.urlFile, "r") as f:
            urls = f.readlines() ### Terry ### End the with statement after slurping the file. Alternatively loop on the file rather than use readlines()
            self.pageFeatures = [None] * len(urls)
            i = 0 ### Terry ### What is "i"
            for url in urls:
                if not self.siteValidation(url):
                    if self.database:
                        self.cursor.execute(
                            "INSERT INTO errors (error) VALUES (?)", self.errors[url])
                    continue
                placeholder, url = self.siteValidation(url) ### Wasn't siteValidation just called, why call it again? Especialy if it is a slow (e.g. network) method
                if not self.screenshotDir:
                    if self.database:
                        try:
                            time = self.getTime()
                            self.cursor.execute(
                                "INSERT INTO metadata (id, url, time) VALUES (?, ?, ?)",
                                self.id, url, time)
                        except Exception:
                            self.id = self.cursor.execute(
                                "SELECT id FROM metadata WHERE url = ?", url)
                            self.id = int(self.id[0]["id"])
                    self.saveScreenshot(url)
                filename = self.generateFilename(url)
                if not self.htmlDir:
                    html = self.driver.page_source
                    self.initializeBS(html)
                    prettyHTML = self.BS.prettify()
                    if not os.path.isfile(
                            self.dataDir + "/html" + filename + ".html"):
                        with open(self.dataDir + "/html" + filename + ".html", "w") as f:
                            f.write(prettyHTML)
                    else:
                        pass
                    del html
                else:
                    # Assumes that the filenames follow the naming conventions
                    # used throughout this code
                    try:
                        with open(self.htmlDir + "/" + filename + ".html", "r") as f:
                            html = f.read()
                    except Exception:
                        raise FileNotFoundError(
                            """Are you sure the html files in htmlDir follow the
                             naming conventions used in this code?""")

                # I never actually read the css, but it's still useful to have
                # for future research
                if not self.cssDir:
                    linkTags = self.driver.find_elements(By.TAG_NAME, "link")
                    for tag in linkTags:
                        css = tag.get_attribute("rel")
                        if css == "stylesheet":
                            cssFile = tag.get_attribute("href")
                            sheet = cssutils.parseUrl(cssFile)
                            break
                    if not os.path.isfile(
                            self.dataDir + "/css" + filename + ".css"):
                        with open(self.dataDir + "/css" + filename + ".css", "w") as f:
                            f.write(sheet.cssText.decode())

                self.pageFeatures[i] = self.getPageFeatures(url)
                self.id += 1
                i += 1
            if self.database:
                for features in self.pageFeatures:
                    self.cursor.execute("INSERT INTO results () VALUES ()", )
                self.cursor.commit()


class image(scrape):
    '''A class for scraping image-based features'''

    def __init__(self, imageFeatures=None, **kwargs):
        '''Similarily to the pageBased class, inherits all attributes from the initialize and scape classes,
        (not pageFeatures) and adds an optional attribute called imageFeatures'''
        super().__init__(**kwargs)
        self.imageFeatures = imageFeatures

    def getImagemagickData(self, result):
        '''Analyses the results of the imageMagick command:
        identify -verbose (screenshot) to store imageFeatures. Definitions and
        justification for scraping these features can be found in the research at TODO.'''
        CHANNEL = 0
        RED = 0
        GREEN = 0
        BLUE = 0
        alpha = 0
        IMData = []
        for split in result.split("\n"):
            # Get width and height
            if "Geometry: " in split:
                split = split.replace("Geometry:", "")
                split = split.replace(" ", "")
                split = split.replace("+0+0", "")
                width, height = split.split("x")
                IMData.append(width)
                IMData.append(height)
                continue
            # Toggle when reading channel statistics
            elif "Channel statistics:" in split:
                CHANNEL = 1
                continue
            elif CHANNEL == 1:
                # Toggle
                if "Red:" in split:
                    RED = 1
                    continue
                elif "Green:" in split:
                    GREEN = 1
                    continue
                elif "Blue:" in split:
                    BLUE = 1
                    continue
                elif "Alpha:" in split:
                    alpha = 1
                    CHANNEL = 0
                    continue
                elif CHANNEL == 0 and alpha:
                    IMData.append(alpha)
                    del alpha
                    continue
                # Check for values
                if RED == 1:
                    if "mean: " in split:
                        split = split.replace("mean: ", "")
                        split = split.replace(" ", "")
                        mean, temp = split.split("(")
                        rMean = mean
                        IMData.append(rMean)
                        continue
                    elif "standard deviation: " in split:
                        split = split.replace("standard deviation: ", "")
                        split = split.replace(" ", "")
                        stdDev, temp = split.split("(")
                        rstdDev = stdDev
                        IMData.append(rstdDev)
                        continue
                    elif "entropy:" in split:
                        RED = 0
                        continue
                elif GREEN == 1:
                    if "mean: " in split:
                        split = split.replace("mean: ", "")
                        split = split.replace(" ", "")
                        mean, temp = split.split("(")
                        gMean = mean
                        IMData.append(gMean)
                        continue
                    elif "standard deviation: " in split:
                        split = split.replace("standard deviation: ", "")
                        split = split.replace(" ", "")
                        stdDev, temp = split.split("(")
                        gstdDev = stdDev
                        IMData.append(gstdDev)
                        continue
                    elif "entropy:" in split:
                        GREEN = 0
                        continue
                elif BLUE == 1:
                    if "mean: " in split:
                        split = split.replace("mean: ", "")
                        split = split.replace(" ", "")
                        mean, temp = split.split("(")
                        bMean = mean
                        IMData.append(bMean)
                        continue
                    elif "standard deviation: " in split:
                        split = split.replace("standard deviation: ", "")
                        split = split.replace(" ", "")
                        stdDev, temp = split.split("(")
                        bstdDev = stdDev
                        IMData.append(bstdDev)
                        continue
                    elif "entropy:" in split:
                        BLUE = 0
                        continue
            elif "Gamma: " in split:
                split = split.replace("Gamma:", "")
                split = split.replace(" ", "")
                gamma = split
                IMData.append(gamma)
                break

        return IMData

    def imageHash(self, url, filename):
        '''A hash function that stores values from the perceptual and difference hash ImageHash
        functions. A database is required in order to take full advantage of the hash values,
        specifically once enough hashes have been generated, the data could possibly be combined
        with the predictive model to add blacklisting functionality based on hash similarity.'''
        if not self.database:
            return
        else:
            pHash = imagehash.phash(
                Image.open(
                    self.dataDir +
                    "/screenshots/" +
                    filename +
                    ".png"))
            dHash = imagehash.dhash(
                Image.open(
                    self.dataDir +
                    "/screenshots/" +
                    filename +
                    ".png"))
            self.cursor.execute(
                "INSERT INTO hashes (pHash, dHash, url) VALUES (?, ?, ?)",
                pHash,
                dHash,
                url)

    def getImageFeatures(self, filename):
        '''Searches through the html of a url to get the specified image-features.
        These features are defined in the research paper at TODO and broken down
        into the categories: layout, style, and other.'''
        totalTags = self.BS.find_all()
        selTotalTags = self.driver.find_elements(By.XPATH, "//*")
        linkTags = self.driver.find_elements(By.TAG_NAME, "link")
        ### Terry ### If this was a dictionary, it would be selfdocumenting (e.g. names to values),
        ### Terry ### and easier to modify (can add new value types anywhere without worrying about array order)
        features = []

        # LAYOUT
        # Get the total number of tags DIRECTLY in the HTML tag using Beautiful
        # Soup
        htmlTag = self.BS.find('html')
        inHTML = 0
        for tag in htmlTag:
            inHTML += 1
        features.append(inHTML)

        # Get the total number of tags in the head tag using Beautiful Soup
        headTag = self.BS.find('head')
        inHead = 0
        if headTag:
            headChildren = headTag.findChildren()
            for tag in headChildren:
                inHead += 1
        features.append(inHead)

        # Get the total number of tags in the main tag using Beautiful Soup
        mainTag = self.BS.find('main')
        inMain = 0
        if mainTag:
            mainChildren = mainTag.findChildren()
            for tag in mainChildren:
                inMain += 1
        features.append(inMain)

        # Get the total number of tags in the body tag using Beautiful Soup
        bodyTag = self.BS.find('body')
        inBody = 0
        if bodyTag:
            bodyChildren = bodyTag.findChildren()
            for tag in bodyChildren:
                inBody += 1
        features.append(inBody)

        # Get the percentage of img tags
        imgTags = self.driver.find_elements(By.TAG_NAME, "img")
        pctImgTags = len(imgTags) / len(totalTags)
        features.append(pctImgTags)

        # Use imagemagick to get image-related information
        # STYLE
        result = subprocess.run(["identify",
                                 "-verbose",
                                 self.dataDir + "/screenshots/" + filename + ".png"],
                                stdout=subprocess.PIPE)
        result = result.stdout.decode("utf-8")
        IMData = self.getImagemagickData(result)
        for data in IMData:
            features.append(data)

        # Initialize arrays for storing and iterating through attribute values
        sizes = []
        weights = []
        styles = []
        families = []
        for tag in selTotalTags:
            if tag.value_of_css_property("font-size"):
                sizes.append(tag.value_of_css_property("font-size"))
            if tag.value_of_css_property("font-style"):
                styles.append(tag.value_of_css_property("font-style"))
            if tag.value_of_css_property("font-weight"):
                weights.append(tag.value_of_css_property("font-weight"))
            if tag.value_of_css_property("font-family"):
                families.append(tag.value_of_css_property("font-family"))
            if tag.value_of_css_property("text-decoration"):
                styles.append(tag.value_of_css_property("text-decoration"))

        # Get the number of non-normal text, as well as the average font-weight
        boldTotal = 0
        numBold = 0
        totalWeights = 0
        for bold in weights:
            if int(bold) > 400:
                numBold += 1
            totalWeights += 1
            boldTotal += int(bold)

        # Calculate the font-weight average, append the number of font-weight properties
        # (should be equal to the number of text tags)
        # and append them to the features array
        try:
            boldAverage = boldTotal / totalWeights
        except ZeroDivisionError:
            boldAverage = 0
        features.append(numBold)
        features.append(boldAverage)

        # Get the most common font family
        fonts = []
        for family in families:
            family = family.replace("system-ui", "")
            family = family.replace("-apple-system", "")
            family = family.replace("-windows-system", "")
            family = family.replace("-linux-system", "")
            family = family.replace(" ", "")
            family = family.split(",")
            if family[0] == '':
                continue
            fonts.append(family[0])
        occurences = Counter(fonts)
        font = occurences.most_common(1)[0][0]
        features.append(font)

        # Get the average font-size (in pixels)
        totalSize = 0
        numSizes = 0
        for size in sizes:
            size = size.replace("px", "")
            totalSize += float(size)
            numSizes += 1

        try:
            averageSize = totalSize / numSizes
        except ZeroDivisionError:
            averageSize = 0
        features.append(averageSize)

        # Iterate through styles to get the number of style changes, the most common style,
        # and the percentage of italicized and underlined styles out of all the
        # changed styles
        numStyles = 0
        numUnderlines = 0
        numItalics = 0
        decorations = []
        for style in styles:
            # Replacing RGB in favor of the imagemagick analysis method
            if "rgb" in style:
                style = style.split("rgb")[0]
                if style == '':
                    continue
            if style == "normal" or style == "none":
                continue
            elif "italic" in style:
                numItalics += 1
            elif "underline" in style:
                numUnderlines += 1
            numStyles += 1
            for style in style.split(" "):
                if style == "":
                    continue
                decorations.append(style)

        occurences = Counter(decorations)
        fontStyle = occurences.most_common(1)[0][0]
        features.append(numStyles)
        features.append(fontStyle)
        features.append(numItalics / len(styles))
        features.append(numUnderlines / len(styles))

        # OTHER
        # Check for an image overlapping the address bar
        overlapping = 0
        for img in imgTags:
            location = img.location
            y = location["y"]
            if y < 0:
                overlapping = 1
                break
        features.append(overlapping)

        # Check if there is a rel=icon attribute in a link tag (check for a
        # favicon image)
        favicon = 0
        for link in linkTags:
            attribute = link.get_attribute("rel")
            if attribute == "icon":
                favicon = 1
                break
        features.append(favicon)

        return features

    def imageScrape(self, HASH=False):
        '''Automates the image-based scraping process by reading from the url file, validating the url,
        taking a screenshot (if necessary), saving html and css (if necessary), and then generating
        features by using Selenium and Beautiful Soup analysis TODO: should I combine this class?
        Ask Terry, it would be more effecient...'''
        # Begin to scrape using provided urls
        with open(self.urlFile, "r") as f:
            urls = f.readlines()
            self.imageFeatures = [None] * len(urls)
            i = 0
            for url in urls:
                if not self.siteValidation(url):
                    if self.database:
                        self.cursor.execute(
                            "INSERT INTO errors (error) VALUES (?)", self.errors[url])
                    continue
                placeholder, url = self.siteValidation(url)
                if not self.screenshotDir:
                    if self.database:
                        try:
                            time = self.getTime()
                            self.cursor.execute(
                                "INSERT INTO metadata (id, url, time) VALUES (?, ?, ?)",
                                self.id, url, time)
                        except Exception:
                            self.id = self.cursor.execute(
                                "SELECT id FROM metadata WHERE url = ?", url)
                            self.id = int(self.id[0]["id"])
                    self.saveScreenshot(url)
                else:
                    for filename in sorted(os.listdir(self.screenshotDir)):
                        self.id = filename[0:2]
                        self.id = self.id.replace("_", "")
                        self.id = int(self.id)
                filename = self.generateFilename(url)
                if not self.htmlDir:
                    html = self.driver.page_source
                    self.initializeBS(html)
                    prettyHTML = self.BS.prettify()
                    if not os.path.isfile(
                            self.dataDir + "/html" + filename + ".html"):
                        with open(self.dataDir + "/html" + filename + ".html", "w") as f:
                            f.write(prettyHTML)
                    else:
                        pass
                    del html
                else:
                    # Assumes that the filenames follow the naming conventions
                    # used throughout this code
                    try:
                        with open(self.dataDir + "/html" + filename + ".html", "r") as f:
                            html = f.read()
                    except Exception:
                        raise FileNotFoundError(
                            """Are you sure the html files in htmlDir follow the
                            naming conventions used in this code?""")

                # Never actually reads the css (so directory doesn't need to be checked),
                # but it's still useful to have the css for possible future
                # research
                if not self.cssDir:
                    linkTags = self.driver.find_elements(By.TAG_NAME, "link")
                    for tag in linkTags:
                        css = tag.get_attribute("rel")
                        if css == "stylesheet":
                            cssFile = tag.get_attribute("href")
                            sheet = cssutils.parseUrl(cssFile)
                            break
                    with open(self.dataDir + "/css" + filename + ".css", "w") as f:
                        f.write(sheet.cssText.decode())

                if HASH:
                    if self.database:
                        self.imageHash(url, filename)

                self.imageFeatures[i] = self.getImageFeatures(filename)
                self.id += 1
                i += 1
            if self.database:
                for features in self.imageFeatures:
                    self.cursor.execute("INSERT INTO results () VALUES ()", ) ### Terry ### What is being inserted?
                self.cursor.commit()


class combine(image, page):
    '''A function to combine the results, specifically using python weka wrapper 3
    to create .arff datasets that can be used for machine learning purposes'''

    def __init__(
            self,
            pageFeatures,
            imageFeatures,
            initialImageDataset=None,
            initialPageDataset=None,
            pageDataset=None,
            imageDataset=None,
            combinedDataset=None,
            combinedBalancedDataset=None,
            fullDataset=None,
            fullBalancedDataset=None,
            allFeatures=[],
            **kwargs):
        '''Inherits all prior attributes (TODO: also ask Terry about this; all it really needs is
        the dataDir attribute I believe, this probably isn't efficient), requires imageFeatures
        and pageFeatures as arguments (in order to create the datasets), and creates 9
        optional attributes, including: initialImageDataset and initialPageDataset; used for feature
        selection and to structure other datasets, pageDataset and imageDataset, datasets of only
        the image-based and page-based features, combinedDataset, a dataset with both page and image
        based features, combinedBalancedDataset, similar to the combined dataset except the SMOTE
        oversampler has been used to balance the class ratio, fullDataset, which contains all
        attributes (not just the ones selected via feature selection), fullBalancedDataset, which
        also uses SMOTE to balance class ratio, and allFeatures, an array of all the features.'''
        super().__init__(pageFeatures=pageFeatures, imageFeatures=imageFeatures, **kwargs)
        self.initialImageDataset = initialImageDataset
        self.initialPageDataset = initialPageDataset
        self.pageDataset = pageDataset
        self.imageDataset = imageDataset
        self.combinedDataset = combinedDataset
        self.combinedBalancedDataset = combinedBalancedDataset
        self.fullDataset = fullDataset
        self.fullBalancedDataset = fullBalancedDataset
        self.allFeatures = allFeatures
        self.pageFeatures = pageFeatures
        self.imageFeatures = imageFeatures
        i = 0
        for pageFeature in self.pageFeatures:
            features = pageFeature + self.imageFeatures[i]
            self.allFeatures.append(features)
            i += 1

    # Comparing attributes from ranker Feature Selection methods

    def FS(self, page=True, image=True):
        '''The feature selection process used; the correlational, information gain, and chiSquared
        ranked feature selection methods are run and stored in arrays, of which the index values are
        then used (with 0 being the highest value and len(array - 1) being the lowest value) to
        calculate the top overall ranked features. There are 2 pre-defined arguments, page and
        image, which default to True and represent the features that you want to perform feature
        selection on (TODO: I don't think this function is written correctly; specifically I have
        to be careful with the forloops).'''
        correlation = []
        information = []
        chiSquared = []
        ranked = {}

        search = ASSearch(classname="weka.attributeSelection.Ranker")
        # Correlational
        evaluator = ASEvaluation(
            classname="weka.attributeSelection.CorrelationAttributeEval")
        correlational = AttributeSelection()
        correlational.search(search)
        correlational.evaluator(evaluator)

        # Infogain
        evaluator = ASEvaluation(
            classname="weka.attributeSelection.InfoGainAttributeEval")
        infoGain = AttributeSelection()
        infoGain.search(search)
        infoGain.evaluator(evaluator)

        # Chi
        evaluator = ASEvaluation(
            classname="weka.attributeSelection.ChiSquaredAttributeEval")
        chi = AttributeSelection()
        chi.search(search)
        chi.evaluator(evaluator)

        selectors = {page: self.pageDataset, image: self.imageDataset}
        attributes = []
        for selected, dataset in selectors.items():
            if bool(selected) and dataset:
                correlational.select_attributes(dataset)
                infoGain.select_attributes(dataset)
                chi.select_attributes(dataset)

            for attribute in correlational.ranked_attributes:
                attribute = str(self.selected)
                attribute = selected.split(" ", 1)
                attribute = selected[0].replace("[", "")
                attribute = selected.replace(".", "")
                correlational.append(attribute)

            for attribute in infoGain.ranked_attributes:
                attribute = str(selected)
                attribute = selected.split(" ", 1)
                attribute = selected[0].replace("[", "")
                attribute = selected.replace(".", "")
                information.append(attribute)

            for attribute in chi.ranked_attributes:
                attribute = str(selected)
                attribute = selected.split(" ", 1)
                attribute = selected[0].replace("[", "")
                attribute = selected.replace(".", "")
                chiSquared.append(attribute)

            for i in range(49):
                if i in correlation:
                    if i in information:
                        if i in chi:
                            # Check for similarities between the feature
                            # selection methods
                            corrStrength = correlation.index(i)
                            infoStrength = information.index(i)
                            chiStrength = chi.index(i)
                            avgIndex = (
                                corrStrength + infoStrength + chiStrength) / 3
                            ranked[i] = avgIndex

            attributes.append(sorted(ranked, key=ranked.get))
        return attributes

    def generateInstances(self, combined=True, full=True):
        '''Uses the SMOTE weka filter to oversample the minority class. 2 optional parameters
        default to True, combined and full, each of which represent the dataset that you want
        to oversample (you will still have access to the original dataset even if you choose
        to oversample).'''
        self.combinedBalancedDataset = self.combinedDataset
        self.fullBalancedDataset = self.fullDataset
        if combined:
            legit = 0
            phish = 0
            for instance in self.combinedBalancedDataset:
                index = instance.class_index
                classVal = instance.get_value(index)
                if classVal == 0:
                    legit += 1
                elif classVal == 1:
                    phish += 1
            if legit < phish:
                ratio = (phish / legit) * 100
                classVal = "1"
            elif phish < legit:
                ratio = (legit / phish) * 100
                classVal = "0"
            else:
                return
            smote = Filter(
                classname="weka.filters.supervised.instance.SMOTE", options=[
                    "-C", classVal, "-P", ratio])
            smote.inputformat(self.combinedBalancedDataset)
            newInstances = smote.filter(self.combinedBalancedDataset)
            for instance in newInstances:
                self.combinedBalancedDataset.add_instance(instance)
            self.combinedBalancedDataset.sort(index)

        if full:
            legit = 0
            phish = 0
            for instance in self.fullBalancedDataset:
                index = instance.class_index
                classVal = instance.get_value(index)
                if classVal == 0:
                    legit += 1
                elif classVal == 1:
                    phish += 1
            if legit < phish:
                ratio = (phish / legit) * 100
                classVal = "0"
            elif phish < legit:
                ratio = (legit / phish) * 100
                classVal = "1"
            else:
                return
            smote = Filter(
                classname="weka.filters.supervised.instance.SMOTE", options=[
                    "-C", classVal, "-P", ratio])
            smote.inputformat(self.fullBalancedDataset)
            newInstances = smote.filter(self.fullBalancedDataset)
            for instance in newInstances:
                self.fullBalancedDataset.add_instance(instance)
            self.fullBalancedDataset.sort(index)

    def closePWW3(
            self,
            image=True,
            page=True,
            combined=True,
            combinedBalanced=True,
            full=True,
            fullBalanced=True):
        '''A function that saves all the altered datasets in dataDir/datasets/(dataset) and
        closes jvm. There are 6 predefined arguments, each of which True, representing the
        datasets that you want to save.'''
        datasetSaver = Saver(classname="weka.core.converters.ArffSaver")
        if image:
            if self.imageDataset:
                datasetSaver.save_file(
                    self.imageDataset,
                    self.dataDir +
                    '/datasets/imageDataset.arff')
        if page:
            if self.pageDataset:
                datasetSaver.save_file(
                    self.pageDataset,
                    self.dataDir +
                    '/datasets/pageDataset.arff')
        if combined:
            if self.combinedDataset:
                datasetSaver.save_file(
                    self.combinedDataset,
                    self.dataDir +
                    '/datasets/combinedDataset.arff')
        if combinedBalanced:
            if self.combinedBalancedDataset:
                datasetSaver.save_file(
                    self.combinedBalancedDataset,
                    self.dataDir +
                    '/datasets/combinedBalancedDataset.arff')
        if full:
            if self.fullDataset:
                datasetSaver.save_file(
                    self.fullDataset,
                    self.dataDir +
                    '/datasets/fullDataset.arff')
        if fullBalanced:
            if self.fullBalancedDataset:
                datasetSaver.save_file(
                    self.fullBalancedDataset,
                    self.dataDir +
                    '/datasets/fullBalancedDataset.arff')
        jvm.stop()

    def createAttributes(self):
        '''A function that creates the initial datasets for feature selection. 2 particular arrays
        are defined, imageAttNames and pageAttNames, which contain the attribute type and name for
        each respective attribute.'''
        ### Terry ### Why not use dictionaries in the first place to associate name and value?
        imageAtts = []
        imageAttNames = [
            Attribute.create_numeric("Total Width (px)"),
            Attribute.create_numeric("Total Height (px)"),
            Attribute.create_numeric("Num Tags in <html>"),
            Attribute.create_numeric("Num Tags in <head>"),
            Attribute.create_numeric("Num Tags in <main>"),
            Attribute.create_numeric("Num Tags in <body>"),
            Attribute.create_numeric("Pct <img> tags"),
            Attribute.create_numeric("Total Width"),
            Attribute.create_numeric("IM: red mean"),
            Attribute.create_numeric("IM: red std dev"),
            Attribute.create_numeric("IM: green mean"),
            Attribute.create_numeric("IM: green std dev"),
            Attribute.create_numeric("IM: blue mean"),
            Attribute.create_numeric("IM: blue std dev"),
            Attribute.create_numeric("Total Width"),
            Attribute.create_nominal("IM: AlphaChannel"),
            Attribute.create_numeric("IM: gamma/brightness"),
            Attribute.create_numeric("Num bold (font-weight > 400) tags"),
            Attribute.create_numeric("Average Font Weight"),
            Attribute.create_string("Most used font"),
            Attribute.create_numeric("Total Width"),
            Attribute.create_numeric("Average Font Size"),
            Attribute.create_numeric("Number of non-normal text-styles/decorations"),
            Attribute.create_numeric("Most common font style/decoration"),
            Attribute.create_numeric("Percentage of italics out of all styles"),
            Attribute.create_numeric("Percentage of underlines out of all styles"),
            Attribute.create_nominal("Image overlapping the top of the screen"),
            Attribute.create_numeric("Favicon tag exists")]
        pageAtts = []
        pageAttNames = {"": ""}
        # TODO
        # for instance in self.pageFeatures:
        #     for value in instance.values:

        # for instance in self.imageFeatures:
        #     for value in instance.values:

        #         Attribute.create_nominal

        # TODO
        self.initialPageDataset = Instances.create_instances(
            "initialPageDataset", [], 0)
        self.initialImageDataset = Instances.create_instances(
            "initialImageDataset", [], 0)

    # TODO
    def classify(self):


    def createDatasets(self):
        '''An encompassing function that automates creating the initial datasets,
        feature selection, instance generation, and saving and closing.'''
        # TODO: NEVER FINISHED
        # I used the ranked features from my training data to determine future data collection
        # However, more testing data would be helpful to help validate the
        # feature selection process
        self.createAttributes()
        rankedAtts = self.FS()
        self.pageDataset = Instances.create_instances("pageDataset", [], 0)
        self.imageDataset = Instances.create_instances("imageDataset", [], 0)
        self.combinedDataset = Instances.create_instances(
            "combinedDataset", [], 0)

        i = 0
        for features in self.pageFeatures:
            pageValues = [feature for feature in features]
            imageValues = [feature for feature in self.imageFeatures[i]]
            inst = Instance.create_instance(pageValues)
            self.pageDataset.add_instance(inst)
            inst = Instance.create_instance(imageValues)
            self.imageDataset.add_instance(inst)
            inst = Instance.create_instance(pageValues + imageValues)
            self.combinedDataset.add_instance(inst)
            i += 1

        self.closePWW3()




def main():
    # Initialization
    run = fisher()
    run.initializeAll()

    # PageBased data generation + initialization
    pageData = page(
        urlFile="data/urls.txt",
        dataDir="data",
        driver=run.driver,
        BS=run.BS)
    pageData.pageScrape()
    print(pageData.pageFeatures)

    # ImageBased data generation
    imageData = image(
        urlFile="data/urls.txt",
        dataDir="data",
        driver=run.driver,
        BS=run.BS)
    imageData.imageScrape()
    print(imageData.imageFeatures)

    # Data Combination
    DC = combine(
        pageFeatures=pageData.pageFeatures,
        imageFeatures=imageData.imageFeatures,
        urlFile="data/urls.txt",
        dataDir="data")
    DC.createDatasets()
    DC.classify()

    run.closeSelenium()


if __name__ == "__main__":
    main()
