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
from weka.classifiers import Classifier
# Optionally, for graphing purposes, pygraphviz and PIL can be installed and the
# weka.plot.graph class can be imported
# Check the installation process here for more details:
# https://fracpete.github.io/python-weka-wrapper3/install.html
import weka.plot.graph as graph
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


class startFishing():
    '''A class for initializing Selenium, Beautiful Soup, and the project filesystem'''

    def __init__(self, dataDir="data", driver=None, jvmToggle=False, **kwargs):
        '''Defines the dataDir, driver, and BS attributes, where dataDir is the home directory
        containing a screenshots directory for screenshots, an html directory for html,
        a css directory for css, and a datasets directory for datasets, and the driver and
        BS attributes store the current state of the Selenium Webdriver and Beautiful Soup
        objects respectively'''
        super().__init__(**kwargs)
        self.dataDir = dataDir
        self.driver = driver
        self.jvmToggle = jvmToggle
        if not os.path.isdir(self.dataDir):
            if self.dataDir == "data":
                os.mkdir("data")
            else:
                raise FileNotFoundError("""dataDir needs to be a valid directory""")
        subDirectories = ["screenshots", "html", "css", "datasets", "graphs"]
        for subdir in map(lambda subdir: self.dataDir + "/" + subdir, subDirectories):
            if not os.path.isdir(subdir):
                os.mkdir(subdir)

    def installResources(self):
        '''Installs the chiSquaredAttributeEval package (a Feature Selection method),
        the SMOTE oversampler, and the Wayback Machine Firefox add_on
        (the resources I used for this project that required download)'''
        if not self.jvmToggle:
            logging.warning(" Are you sure the jvm has been activated?")
            return
        packages.install_package('chiSquaredAttributeEval')
        packages.install_package('SMOTE')
        wayback_machine = requests.get(
            'https://addons.mozilla.org/firefox/downloads/file/3911106/wayback_machine-3.0-fx.xpi',
            allow_redirects=True)
        open(
            self.dataDir +
            '/wayback_machine-3.0-fx.xpi',
            'wb').write(
            wayback_machine.content)
        # Another possible add_on would be a popup blocker (one is found below),
        # although not used for the purposes of this research to get representative
        # screenshots of what the average user might be seeing
        # no_cookies = requests.get(
        #     'https://addons.mozilla.org/firefox/downloads/file/3925251/i_dont_care_about_cookies-3.3.8-an+fx.xpi',
        #     allow_redirects=True)
        # open(self.dataDir +
        #     '/i_dont_care_about_cookies-3.3.8-an+fx.xpi',
        #     'wb').write(
        #     no_cookies.content))

    def initializeSelenium(self, add_ons=None):
        '''Initializes Selenium with any add_ons that are passed to the method'''
        options = FirefoxOptions()
        options.add_argument("--headless")
        options.add_argument('--hide-scrollbars')
        options.add_argument('--disable-gpu')
        # In terms of security, a VPN and a VM is recommended.
        # Additionally, cookies, session, and cache data are disabled
        # using Firefox preferences (found below)
        # http://kb.mozillazine.org/index.php?title=Category:Preferences&until=Places.frecency.unvisitedTypedBonus
        # Javascript is necessary for dynamic websites, but can be
        # disabled by uncommenting the below preference
        # options.set_preference("javascript.enabled", False)
        options.set_preference("network.cookie.cookieBehavior", 2)
        options.set_preference("Browser.sessionstore.privacy", 2)
        options.set_preference("Browser.cache.disk.enable", False)
        driver = webdriver.Firefox(options=options)
        for add_on in add_ons:
            if add_on[len(add_on) - 4:len(add_on)].upper() == ".XPI":
                try:
                    driver.install_addon(os.path.abspath(self.dataDir + add_on), temporary=True)
                except Exception:
                    logging.warning(" " + self.dataDir + add_on + " is not a valid Firefox addon!")
                    continue
        self.driver = driver
        self.driver.implicitly_wait(20)

    def initializePWW3(self, jvmOptions):
        '''Starts jvm using a list of optional parameters'''
        if self.jvmToggle:
            logging.warning(""" Have you already started the jvm? Remember that you can't
            stop and then start it again mid-execution!""")
            return
        jvm.start(option for option in jvmOptions)
        self.jvmToggle = True

    def initializeAll(self, jvmOptions=["system_cp", "packages"], add_ons=['/wayback_machine-3.0-fx.xpi']):
        '''A joint method that calls all the initialize methods (except for initializeBS). Packages
        are enabled, related resources are installed, and excessive warnings are limited.'''
        options = [option for option in jvmOptions]
        requests.packages.urllib3.disable_warnings(
            category=InsecureRequestWarning)
        cssutils.log.setLevel(logging.CRITICAL)
        if "packages" not in options:
            logging.warning(" Are you sure you want to run jvm without package support?")
        self.initializePWW3(options)
        self.installResources()
        options = [add_on for add_on in add_ons]
        self.initializeSelenium(options)


# The analyzer base class
class analyzer():
    def __init__(self):
        pass

    def name():
      return analyzer.__class__.__name__

    # Shell function
    # def analyze(self):
        # Your analysis code here
        # Every class inheriting from the analyzer class
        # Has a different analyze method
        # These classes are not standalone
        # But can function with a self.addAnalyzer(analyzer)
        # and self.goFish() call from the scrape class

# The scrape class; inherits from the startFishing initialization class.
# Provides many useful scraping methods and initializes file system and variables
# This class IS NOT inherited from due to the dynamic nature of scraping variables;
# rather the variables are passed as arguments into the analyzers
# and the analyzers return the respective features and feature names
# which are then used in the data class which inherits from the scrape class
class scrape(startFishing):
    '''A class (inheriting from initialize) that defines useful scrape objects and methods'''

    def __init__(
            self,
            urlFile,
            database=None,
            screenshotDir=None,
            htmlDir=None,
            cssDir=None,
            cursor=None,
            conn=None,
            id=0,
            classVal=Instance.missing_value(),
            errors={},
            allFeatures=[],
            allFeatureNames={},
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
        # Still need to find a way to have analyzers as an attribute, rather than a global variable
        self.screenshotDir = screenshotDir
        self.htmlDir = htmlDir
        self.cssDir = cssDir
        self.database = database
        self.conn = conn
        self.cursor = cursor
        self.classVal = classVal
        self.id = id
        self.BS = None
        self.analyzers = []
        self.errors = errors
        self.allFeatures = allFeatures
        self.allFeatureNames = allFeatureNames
        if not os.path.isfile(self.urlFile):
            raise FileNotFoundError(
                """urlFile needs to be a path to a file with urls!""")
        else:
            with open(self.urlFile, "r") as f:
                for line in f:
                    url = line.strip()
                    if not validators.url(url):
                        raise ValueError(
                            """Sorry, are you sure urlFile contains valid urls?""")
        if self.screenshotDir:
            if not os.path.isdir(self.screenshotDir):
                raise FileNotFoundError(
                    """screenshotDir needs to be a path to a directory with screenshots!""")
            for filename in os.listdir(self.screenshotDir):
                if self.id == 0:
                    self.id = filename[0:2]
                    self.id = self.id.replace("_", "")
                    self.id = int(self.id)
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
                self.conn = db
                self.cursor.execute(
                    'SELECT name FROM sqlite_master WHERE TYPE = "table"')
                # Verifying db by using table names; efficient, but not thorough
                # TODO: update table creation accordingly IF I get public access to all feature-scraping
                # methods (referring to those found at https://data.mendeley.com/datasets/h3cgnj8hft/1)
                tables = {
                    "metadata": """CREATE TABLE metadata (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE, UTCtime INT, classification TEXT)""",
                    "page": """CREATE TABLE page (id INTEGER PRIMARY KEY, externalURL FLOAT,
                    redirectURL FLOAT, hostnameMismatch BINARY,
                    numDash INT, numEmail INT, numDots INT)""",
                    "errors": """CREATE TABLE errors (error TEXT)""",
                    "image": """CREATE TABLE image (id INTEGER PRIMARY KEY, totalWidth FLOAT,
                    totalHeight FLOAT, numTagsInHtml INT, numTagsInHead INT, numTagsInMain INT,
                    numTagsInBody INT, pctImgTags FLOAT, IMredMean FLOAT, IMredStdDev FLOAT,
                    IMgreenMean FLOAT, IMgreenStdDev FLOAT, IMblueMean FLOAT, IMblueStdDev FLOAT,
                    IMalphaChannel BOOLEAN, IMgamma FLOAT, numBoldTags INT, averageFontWeight FLOAT,
                    mostUsedFont TEXT, averageFontSize FLOAT, numStyles INT, mostUsedStyle TEXT,
                    pctItalics FLOAT, pctUnderline FLOAT, imageOverlappingTop BOOLEAN, favicon BOOLEAN)""",
                    "all": """CREATE TABLE all (id INTEGER PRIMARY KEY, externalURL FLOAT, redirectURL FLOAT,
                    hostnameMismatch BINARY, numDash INT, numEmail INT, numDots INT, totalWidth FLOAT,
                    totalHeight FLOAT, numTagsInHtml INT, numTagsInHead INT, numTagsInMain INT, numTagsInBody INT,
                    pctImgTags FLOAT, IMredMean FLOAT, IMredStdDev FLOAT, IMgreenMean FLOAT, IMgreenStdDev FLOAT,
                    IMblueMean FLOAT, IMblueStdDev FLOAT, IMalphaChannel BOOLEAN, IMgamma FLOAT, numBoldTags INT,
                    averageFontWeight FLOAT, averageFontSize FLOAT, numStyles INT, pctItalics FLOAT,
                    pctUnderline FLOAT, imageOverlappingTop BOOLEAN, favicon BOOLEAN, numLinks INT, urlLength INT,
                    mostUsedStyle TEXT, mostUsedFont TEXT)""",
                    "hashes": """CREATE TABLE hashes (phash INT, dhash INT, url TEXT)"""}
                for tableName, creation in tables.items():
                    if tableName in self.cursor.fetchall():
                        continue
                    else:
                        self.cursor.execute(creation)
                self.conn.commit()
            else:
                os.path.mkfile(self.dataDir + "data.db")
                db = SQL.connect(self.database)
                self.cursor = db.cursor()
                self.conn = db
                for creation in tables.values():
                    self.cursor.execute(creation)
                self.conn.commit()
                if self.id == 0:
                    self.id = self.cursor.execute(
                        "SELECT id FROM metadata ORDER BY DESC LIMIT 1")
                    self.id = int(id[0]['id'])
                    if self.id == '':
                        self.id = 0

    def closeSelenium(self):
        '''Closes and quits Selenium using the Selenium.close() and Selenium.quit() methods.
        Should be called once the webscraping process is finished.'''
        if not self.driver:
            logging.warning(" Are you sure that's a valid Selenium instance?")
            return
        self.driver.close()
        self.driver.quit()

    def initializeBS(self, html):
        '''Initializes a Beautiful Soup object BS. Not called with initializeAll() as it requires
        the html of a website as an argument'''
        try:
            self.BS = BeautifulSoup(html, "html.parser")
        except Exception as e:
            logging.warning(" Couldn't initialize due to " + e + """. Are you sure you
            inputted valid html?""")

    # When an analyzer is to be added
    # The addAnalyzer function should be called
    # With an instance of the analyzer itself
    def addAnalyzer(self, analyzer):
        self.analyzers.append(analyzer)

    def shorten(self, url, validate=False):
        '''Shortens the url using pyshorteners and the clckru shortener. 5 unique characters are
        generated at the end of the url which are then used to rename the file, and once the id in
        front of the filename is removed, https://clck.ru/ can be added back to the url and combined
        with the expand() method below to get the original url from a filename'''
        if not validate:
            if not validators.url(url):
                raise ValueError("Invalid url: " + url)
        clckruShortener = pyshorteners.Shortener()
        shortUrl = clckruShortener.clckru.short(url)
        return shortUrl

    def expand(self, urlID):
        '''Expands a filename into the url associated with the file using pyshorteners and clck.ru.
        Explained more in the shorten() function above'''
        if len(urlID) != 5:
            raise ValueError("Invalid urlID: " + urlID)
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

    def siteValidation(self, url, validated=False):
        '''Method that attempts to validate a site, specifically checking if Selenium can
        access the website, the website's url, and if the requests library does not return a
        404 error (which is often the case due to the slippery nature of phishing websites)'''
        if not validated:
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
            return True

    def saveScreenshot(self, url, validated=False):
        '''Method for saving a screenshot of the full website. Scrolls the page (if possible) to get
        the height and width of a website. A minimum height and width of 10000 (unlikely to ever
        be hit unless intentional) are set to help prevent Selenium crashing.
        The screenshot is saved at dataDir/screenshots/filename.png (see the generate filename
        method above for more information regarding filenames)'''
        if not validated:
            if not self.siteValidation(url):
                logging.warning(" Could not take a screenshot of " + url + " due to " + self.errors[url])
                return
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

    def getTime(self):
        '''Generates a time value (uses Coordinated Universal Time, or UTC)'''
        time = datetime.now().strftime("%H:%M:%S")
        return time

    def goFish(self):
            '''Automates the page-based scraping process by reading from the url file, validating the url,
            taking a screenshot (if necessary), saving html and css (if necessary), and then generating
            features by using Selenium and Beautiful Soup analysis using created analyzers'''
            if not self.driver:
                raise ReferenceError("Cannot scrape without a valid driver instance")
            with open(self.urlFile, "r") as f:
                urlNum = 0
                for line in f:
                    url = line.strip()
                    if not self.siteValidation(url):
                        if self.database:
                            self.cursor.execute(
                                "INSERT INTO errors (error) VALUES (?)", self.errors[url])
                        continue
                    url = self.driver.current_url
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
                        self.saveScreenshot(url, validated=True)
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
                                self.initializeBS(html)
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
                    features = {}
                    classCheck = 1
                    for analyzer in self.analyzers:
                        # features: {name:value}
                        # featureNames: {name:PWW3Type}
                        # The resources below can be expanded on if necessary for the analyzers being used
                        resources = {
                            "dataDir":self.dataDir,
                            "driver":self.driver,
                            "database":self.database,
                            "BS":self.BS,
                            "cursor":self.cursor,
                            "connection":self.conn,
                            "id":self.id,
                            "classVal":self.classVal,
                            "errors":self.errors
                        }
                        # updating resources accordingly
                        filename = self.generateFilename(url)
                        updatedResources = analyzer.analyze(url, filename, resources)
                        for resource, value in updatedResources.items():
                            if resource in resources.keys():
                                if resource == "features":
                                    newFeatures = value
                                elif resource == "featureNames":
                                    newFeatureNames = value
                                else:
                                    self.resource = value
                        if classCheck != len(self.analyzers):
                            features = {key:val for key, val in newFeatures.items() if key != 'classVal'}
                            self.allFeatureNames = self.allFeatureNames | {key:val for key,val in newFeatureNames.items() if key != 'classVal'}
                        else:
                            features = features | newFeatures
                            if urlNum <= len(self.analyzers):
                                self.allFeatureNames = self.allFeatureNames | newFeatureNames
                        if self.database:
                            self.cursor.execute("""INSERT INTO {} ({}) VALUES (?, ?, ?, ?, ?, ?)""".format(analyzer.__class__.__name__,
                                ",".join(name for name in newFeatureNames.keys())), (value for value in newFeatures[self.id].values()))
                        classCheck += 1
                    if self.database:
                        self.cursor.execute("""INSERT INTO full ({}) VALUES (?, ?, ?, ?, ?, ?)""".format(
                            ",".join(name for name in self.allFeatureNames.keys())), (value for value in features.values()))
                    self.allFeatures.append(features)
                    if self.database:
                        self.conn.commit()
                    self.id += 1
                    urlNum += 1


class page(analyzer):
    '''A class for scraping page-based features'''

    def __init__(self, pageFeatures=[], pageFeatureNames={"externalURL":"numeric", "hostnameMismatch":"numeric",
        "redirectURL":"numeric", "numEmail":"numeric", "numDash":"numeric", "numDots":"numeric", "classVal":"nominal"}, **kwargs):
        '''Inherits all previous attributes, adds an optional attribute called pageFeatures
        (although the purpose of the function is to populate the pageFeatures list, so there
        isn't much of a point in passing in a value pageFeatures. If you already have a value,
        I recommend either scraping image data as well
        or creating an instance of the combine class to create datasets of your data)'''
        super().__init__(**kwargs)
        # For each analyzer, it is recommended that you create attributes for features and featureNames
        # You can return them as values instead in the analyze function, but it may be useful for convenience purposes
        self.features = pageFeatures
        self.featureNames = pageFeatureNames
        self.classVal = Instance.missing_value()

    # Where resources is a dictionary of all scrape elements
    # That gets returned and updated accordingly in the goFish method
    def analyze(self, url, filename, resources):
        '''Searches through the html of a url to get the specified page-features.
        These features are defined in the research paper at
        https://github.com/xanmankey/FishingForPhish.git.'''
        # If you want to update class value mid-goFish(), two things are required:
        # Knowledge of when your urlFile shifts from 1 class to another
        # And an associated change of the class value in resources
        features = {}
        # Search for elements with links
        aTags = resources["driver"].find_elements(By.TAG_NAME, "a")
        numLinks = len(aTags)

        # Initialize arrays for storing the top 4 HTML-scraped features
        redirect = []
        mailTo = []
        external = []
        notHostname = []

        # The search is on!
        # Iterate through <a> tags, and check for link attributes
        if len(aTags) != 0:
            tagCount = 0
            for element in aTags:
                # A time.sleep is added so the webdriver can process the element accordingly.
                # In addition to a limit of 1000 <a> tags
                time.sleep(0.01)
                if tagCount >= 1000:
                    break
                # Check all <a> for the href element
                try:
                    href = element.get_attribute("href")
                except Exception as e:
                    resources["errors"].update(url=e)
                    continue
                checkRequest = 0
                # Ignoring JS redirect urls
                if href:
                    if 'javascript:' not in href:
                        try:
                            parsed = parse.urlparse(url)
                        except Exception as e:
                            resources["errors"].update(url=e)
                            continue
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
                tagCount += 1

        # Store totals for table iteration
        numExternal = len(external)
        numMail = len(mailTo)
        numRedirects = len(redirect)

        if len(notHostname) != 1 and notHostname[0] != 0:
            hostname = parse.urlparse(url)
            numHostname = Counter(notHostname)
            freqHostname = numHostname.most_common(1)[0][0]
            if freqHostname == hostname.netloc:
                numNotHostname = 0
            else:
                numNotHostname = 1
        else:
            numNotHostname = 1

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
            features.update({"externalURL":numExternal / numLinks})
        except ZeroDivisionError:
            features.update({"externalURL":0})

        # domain-name mismatch is a binary (adds up the most frequent hostname,
        # and compares it to the domain name; 0 is False, 1 is True)
        features.update({"hostnameMismatch":numNotHostname})

        # numRedirects is a percent
        try:
            features.update({"redirectURL":numRedirects / numLinks})
        except ZeroDivisionError:
            features.update({"redirectURL":0})

        # numMail, numDashes, and numPeriods are numeric
        features.update({"numEmail":numMail})
        features.update({"numDash":numDashes})
        features.update({"numDots":numPeriods})

        features.update({"classVal":self.classVal})
        self.features.append(features)
        resources.update({"features":features})
        resources.update({"featureNames":self.featureNames})
        return resources


class image(analyzer):
    '''A class for scraping image-based features'''

    def __init__(self, imageFeatures=[], imageFeatureNames={"numTagsIn<html>":"numeric", "numTagsIn<head>":"numeric",
        "numTagsIn<main>":"numeric", "numTagsIn<body>":"numeric", "pct<img>Tags":"numeric", "totalWidth":"numeric",
        "totalHeight":"numeric", "IMredMean":"numeric", "IMredStdDev":"numeric", "IMgreenMean":"numeric",
        "IMgreenStdDev":"numeric", "IMblueMean":"numeric", "IMblueStdDev":"numeric", "IMalphaChannel":"numeric",
        "IMgamma":"numeric", "numBoldTags":"numeric", "averageFontWeight":"numeric", "mostUsedFont":"string",
        "averageFontSize":"numeric", "numStyles":"numeric", "mostUsedStyle":"string", "pctItalics":"numeric",
        "pctUnderline":"numeric", "imageOverlappingTop":"numeric", "favicon":"numeric", "classVal":"nominal"}, **kwargs):
        '''Similarily to the pageBased class, inherits all attributes from the initialize and scape classes,
        (not pageFeatures) and adds an optional attribute called imageFeatures'''
        super().__init__(**kwargs)
        self.features = imageFeatures
        self.featureNames = imageFeatureNames
        self.classVal = Instance.missing_value()

    def getImagemagickData(self, result):
        if result[0:6] != "Image:":
            logging.warning(""" Are you sure that's the result of an identify -verbose <imagePath>
            imagemagick command?""")
        '''Analyses the results of the imageMagick command:
        identify -verbose (screenshot) to store imageFeatures. Definitions and
        justification for scraping these features can be found in the research at
        https://github.com/xanmankey/FishingForPhish.git.'''
        CHANNEL = 0
        RED = 0
        GREEN = 0
        BLUE = 0
        alpha = 0
        IMData = {}
        for split in result.split("\n"):
            # Get width and height
            if "Geometry: " in split:
                split = split.replace("Geometry:", "")
                split = split.replace(" ", "")
                split = split.replace("+0+0", "")
                width, height = split.split("x")
                IMData.update({"totalWidth":width})
                IMData.update({"totalHeight":height})
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
                    IMData.update({"IMalphaChannel":alpha})
                elif "Image statistics: " in split:
                    IMData.update({"IMalphaChannel":alpha})
                    CHANNEL = 0
                    continue
                # Check for values
                if RED == 1:
                    if "mean: " in split:
                        split = split.replace("mean: ", "")
                        split = split.replace(" ", "")
                        mean, temp = split.split("(")
                        rMean = mean
                        IMData.update({"IMredMean":rMean})
                        continue
                    elif "standard deviation: " in split:
                        split = split.replace("standard deviation: ", "")
                        split = split.replace(" ", "")
                        stdDev, temp = split.split("(")
                        rstdDev = stdDev
                        IMData.update({"IMredStdDev":rstdDev})
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
                        IMData.update({"IMgreenMean":gMean})
                        continue
                    elif "standard deviation: " in split:
                        split = split.replace("standard deviation: ", "")
                        split = split.replace(" ", "")
                        stdDev, temp = split.split("(")
                        gstdDev = stdDev
                        IMData.update({"IMgreenStdDev":gstdDev})
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
                        IMData.update({"IMblueMean":bMean})
                        continue
                    elif "standard deviation: " in split:
                        split = split.replace("standard deviation: ", "")
                        split = split.replace(" ", "")
                        stdDev, temp = split.split("(")
                        bstdDev = stdDev
                        IMData.update({"IMblueStdDev":bstdDev})
                        continue
                    elif "entropy:" in split:
                        BLUE = 0
                        continue
                elif "Gamma: " in split:
                    split = split.replace("Gamma:", "")
                    split = split.replace(" ", "")
                    gamma = split
                    IMData.update({"IMgamma":gamma})
                    break
        return IMData

    def imageHash(self, url, filename):
        '''A hash function that stores values from the perceptual and difference hash ImageHash
        functions. A database is required in order to take full advantage of the hash values,
        specifically once enough hashes have been generated, the data could possibly be combined
        with the predictive model to add blacklisting functionality based on hash similarity.'''
        if not self.database:
            logging.warning(" Can't store a hash value without database functionality")
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

    def analyze(self, url, filename, resources):
        '''Searches through the html of a url to get the specified image-features.
        These features are defined in the research paper at
        https://github.com/xanmankey/FishingForPhish.git and broken down
        into the categories: layout, style, and other.'''
        features = {}
        totalTags = resources["BS"].find_all()
        selTotalTags = resources["driver"].find_elements(By.XPATH, "//*")
        linkTags = resources["driver"].find_elements(By.TAG_NAME, "link")

        # LAYOUT
        # Get the total number of tags DIRECTLY in the HTML tag using Beautiful
        # Soup
        htmlTag = resources["BS"].find('html')
        inHTML = 0
        for tag in htmlTag:
            inHTML += 1
        features.update({"numTagsIn<html>":inHTML})

        # Get the total number of tags in the head tag using Beautiful Soup
        headTag = resources["BS"].find('head')
        inHead = 0
        if headTag:
            headChildren = headTag.findChildren()
            for tag in headChildren:
                inHead += 1
        features.update({"numTagsIn<head>":inHead})

        # Get the total number of tags in the main tag using Beautiful Soup
        mainTag = resources["BS"].find('main')
        inMain = 0
        if mainTag:
            mainChildren = mainTag.findChildren()
            for tag in mainChildren:
                inMain += 1
        features.update({"numTagsIn<main>":inMain})

        # Get the total number of tags in the body tag using Beautiful Soup
        bodyTag = resources["BS"].find('body')
        inBody = 0
        if bodyTag:
            bodyChildren = bodyTag.findChildren()
            for tag in bodyChildren:
                inBody += 1
        features.update({"numTagsIn<body>":inBody})

        # Get the percentage of img tags
        imgTags = resources["driver"].find_elements(By.TAG_NAME, "img")
        pctImgTags = len(imgTags) / len(totalTags)
        features.update({"pct<img>Tags":pctImgTags})

        # Use imagemagick to get image-related information
        # STYLE
        result = subprocess.run(["identify",
                                 "-verbose",
                                 resources["dataDir"] + "/screenshots/" + filename + ".png"],
                                stdout=subprocess.PIPE)
        result = result.stdout.decode("utf-8")
        IMData = self.getImagemagickData(result)
        for key, value in IMData.items():
            features.update({key:value})

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
        features.update({"numBoldTags":numBold})
        features.update({"averageFontWeight":boldAverage})

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
        features.update({"mostUsedFont":font})

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
        features.update({"averageFontSize":averageSize})

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
        features.update({"numStyles":numStyles})
        features.update({"mostUsedStyle":fontStyle})
        features.update({"pctItalics":numItalics / len(styles)})
        features.update({"pctUnderline":numUnderlines / len(styles)})

        # OTHER
        # Check for an image overlapping the address bar
        overlapping = 0
        for img in imgTags:
            location = img.location
            y = location["y"]
            if y < 0:
                overlapping = 1
                break
        features.update({"imageOverlappingTop":overlapping})

        # Check if there is a rel=icon attribute in a link tag (check for a
        # favicon image)
        favicon = 0
        for link in linkTags:
            attribute = link.get_attribute("rel")
            if attribute == "icon":
                favicon = 1
                break
        features.update({"favicon":favicon})
        features.update({"classVal":self.classVal})
        self.features.append(features)
        resources.update({"features":features})
        resources.update({"featureNames":self.featureNames})
        return resources


# The saveFish class is for interpreting the data from the scrape class
# in regards to machine learning
# The functions that need to be refactored in regards to this class are
# generateInstances():
# createDatasets():
# classify():
# After refactoring, I might also try to build some tests (if it makes sense to test my code)
# I'll build the tests off the examples
class saveFish(scrape):
    '''A function to combine the results, specifically using python weka wrapper 3
    to create .arff datasets that can be used for machine learning purposes'''

    def __init__(self, datasets={}, analyzers=[], allFeatures=None, allFeatureNames=None, graphVal=False, **kwargs):
        '''Inherits all prior attributes, requires pageFeatures,
        pageFeatureNames, imageFeatures, and imageFeatureNames as arguments (in order to create the
        datasets), and creates 9 optional attributes, including: initialImageDataset and initialPageDataset;
        used for featureselection and to structure other datasets, pageDataset and imageDataset, datasets
        of only the image-based and page-based features, rankedDataset, a dataset with both page and image
        based features, rankedBalancedDataset, similar to the ranked dataset except the SMOTE
        oversampler has been used to balance the class ratio, fullDataset, which contains all
        attributes (not just the ones selected via feature selection), fullBalancedDataset, which
        also uses SMOTE to balance class ratio, and allFeatures, an array of all the features.'''
        super().__init__(**kwargs)
        self.datasets = datasets
        self.analyzers = analyzers
        self.newDatasetOptions = {"full":True, "ranked":True, "fullBalanced":True, "rankedBalanced":True}
        # Verifying that the datasets are valid (if passed as a parameter)
        # Remember that you CANNOT add attributes to a dataset (at least the way this was written)
        # You can only add instances of the same attributes
        if len(datasets) != 0:
            analyzerNames = []
            for analyzer in self.analyzers:
                analyzerNames.append(analyzer.__class__.__name__)
            for datasetName in self.datasets.keys():
                if datasetName in analyzerNames or datasetName in self.newDatasetOptions.keys():
                    try:
                        os.path.isfile(self.dataDir + "/datasets/" + datasetName + "Dataset")
                    except FileNotFoundError:
                        self.datasets.pop(datasetName)
        self.allFeatures = allFeatures
        self.allFeatureNames = allFeatureNames
        if not allFeatures:
            raise ValueError("""No features were passed; remember to pass the
            allFeatures attribute from the scrape class!""")
        if not allFeatureNames:
            raise ValueError("""No featureNames were passed; remember to pass the
            allFeatureNames attribute from the scrape class!""")
        # Where predictions and classifications are dictionaries,
        # key is datasetName and value is eval object
        self.classifications = {}
        self.score = {}
        self.graph = graphVal

    # Comparing attributes from ranker Feature Selection methods
    def FS(self):
        '''The feature selection process used; the correlational, information gain, and chiSquared
        ranked feature selection methods are run and stored in arrays, of which the index values are
        then used (with 0 being the highest value and len(array - 1) being the lowest value) to
        calculate the top overall ranked features. There are 2 pre-defined arguments, page and
        image, which default to True and represent the features that you want to perform feature
        selection on.'''

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

        attributes = []
        # Select the best features from the analyzer datasets
        for name, dataset in self.datasets.items():
            if name in self.newDatasetOptions:
                continue
            correlation = []
            information = []
            chiSquared = []
            ranked = {}
            try:
                correlational.select_attributes(dataset)
                infoGain.select_attributes(dataset)
                chi.select_attributes(dataset)
            except Exception:
                logging.warning("""Sorry, you can't select attributes if there aren't enough class labels
                (requires > 0) """)
                return False

            for attributeNum in correlational.ranked_attributes:
                attributeNum = str(attributeNum)
                attributeNum = attributeNum.split(" ", 1)
                attributeNum = attributeNum[0].replace("[", "")
                attributeNum = attributeNum.replace(".", "")
                correlation.append(attributeNum)

            for attributeNum in infoGain.ranked_attributes:
                attributeNum = str(attributeNum)
                attributeNum = attributeNum.split(" ", 1)
                attributeNum = attributeNum[0].replace("[", "")
                attributeNum = attributeNum.replace(".", "")
                information.append(attributeNum)

            for attributeNum in chi.ranked_attributes:
                attributeNum = str(attributeNum)
                attributeNum = attributeNum.split(" ", 1)
                attributeNum = attributeNum[0].replace("[", "")
                attributeNum = attributeNum.replace(".", "")
                chiSquared.append(attributeNum)

            index = 0
            for attribute in dataset.attributes():
                if str(index) in correlation:
                    if str(index) in information:
                        if str(index) in chiSquared:
                            # Check for similarities between the feature
                            # selection methods
                            corrStrength = correlation.index(str(index))
                            infoStrength = information.index(str(index))
                            chiStrength = chiSquared.index(str(index))
                            avgIndex = (
                                corrStrength + infoStrength + chiStrength) / 3
                            ranked.update({attribute:float(avgIndex)})
                index += 1
            attributes.append(sorted(ranked, key=ranked.get))
        return attributes

    def generateInstances(self):
        '''Uses the SMOTE weka filter to oversample the minority class. 2 optional parameters
        default to True, ranked and full, each of which represent the dataset that you want
        to oversample (you will still have access to the original dataset even if you choose
        to oversample).'''
        for analyzer in self.analyzers:
            dataset = self.datasets[analyzer.__class__.__name__]
            class1 = 0
            class2 = 0
            for instance in dataset:
                index = instance.class_index
                classVal = instance.get_value(index)
                if classVal == 0:
                    class1 += 1
                elif classVal == 1:
                    class2 += 1
            if class1 < class2:
                ratio = (class2 / class1) * 100
                classVal = "1"
            elif class1 < class2:
                ratio = (class2 / class1) * 100
                classVal = "0"
            else:
                return
            smote = Filter(
                classname="weka.filters.supervised.instance.SMOTE", options=[
                    "-C", classVal, "-P", ratio])
            smote.inputformat(dataset)
            newInstances = smote.filter(dataset)
            for instance in newInstances:
                dataset.add_instance(instance)
            dataset.sort(index)
            self.datasets.update({analyzer.__class__.__name__ + "Balanced":dataset})

        for option in self.newDatasetOptions.keys():
            if self.newDatasetOptions[option] and "Balanced" in option:
                datasetName = option.split("Balanced")
                if self.newDatasetOptions[datasetName]:
                    dataset = self.datasets[datasetName]
                    class1 = 0
                    class2 = 0
                    for instance in dataset:
                        index = instance.class_index
                        classVal = instance.get_value(index)
                        if classVal == 0:
                            class1 += 1
                        elif classVal == 1:
                            class2 += 1
                    if class1 < class2:
                        ratio = (class2 / class1) * 100
                        classVal = "1"
                    elif class1 < class2:
                        ratio = (class2 / class1) * 100
                        classVal = "0"
                    else:
                        return
                    smote = Filter(
                        classname="weka.filters.supervised.instance.SMOTE", options=[
                            "-C", classVal, "-P", ratio])
                    smote.inputformat(dataset)
                    newInstances = smote.filter(dataset)
                    for instance in newInstances:
                        dataset.add_instance(instance)
                    dataset.sort(index)
                    self.datasets.update({"{}Balanced".format(option):dataset})
                else:
                    continue

    def closePWW3(self):
        '''A function that saves all the altered datasets in dataDir/datasets/(dataset) and
        closes jvm. There are 6 predefined arguments, each of which True, representing the
        datasets that you want to save.'''
        datasetSaver = Saver(classname="weka.core.converters.ArffSaver")
        for datasetName, dataset in self.datasets.items():
            datasetSaver.save_file(
                dataset,
                self.dataDir +
                '/datasets/' + datasetName + "Dataset" + ".arff")
        jvm.stop()

    # Returns a list of all the dataset attributes
    def attributeCreation(self, featureNames, class1="Legitimate", class2="Phishing"):
        '''A convenience function to create the attributes
        for a specific dataset based off of the featureName
        class attributes.'''
        atts = []
        for key, value in featureNames.items():
            if value == "numeric":
                att = Attribute.create_numeric(key)
            elif value == "nominal":
                att = Attribute.create_nominal(key, [class1, class2])
            elif value == "string":
                att = Attribute.create_string(key)
            elif value == "date":
                att = Attribute.create_date(key)
            elif value == "relational":
                att = Attribute.create_relational(key)
            atts.append(att)
        return atts

    # The classify_instance pww3 method ALSO generates predictions if the value is a missing instance
    # All output data is stored in the classifications dictionary
    def classify(self):
        '''A function that classifies the resulting datasets
        from the data creation process.'''

        # The classification options used in the research are set by default
        NaiveBayes = Classifier(classname="weka.classifiers.bayes.NaiveBayes", options=["-D"])
        J48 = Classifier(classname="weka.classifiers.trees.J48")
        Jrip = Classifier(classname="weka.classifiers.rules.JRip")
        classifiers = {"NaiveBayes":NaiveBayes, "J48":J48, "Jrip":Jrip}
        for analyzer in self.analyzers:
            classifications = []
            if self.datasets[analyzer.__class__.__name__]:
                dataset = self.datasets[analyzer.__class__.__name__]
                dataset.class_is_last()
                for classifierName, classifier in classifiers.items():
                    try:
                        classifier.build_classifier(dataset)
                        # The graphs generated can be varied if you so choose; I just decided to graph after 
                        # first building the classifier
                        if self.graph:
                            graph.plot_dot_graph(cls.graph, self.dataDir + "/graph/" + analyzer.__clas__.__name__ + "Graph.png")
                        for instance in dataset:
                            classifications.append(classifier.classify_instance(instance))
                    except Exception as e:
                        print(e)
                        logging.warning("Error using the " + classifierName + " classifier")
                        continue
                if len(classifications) != 0:
                    counting = Counter(classifications)
                    prediction = str(counting.most_common(1)[0][0]) + ":" + str(counting.most_common(2)[0][0])
                    classification = counting.most_common(1)[0][0]
                    self.classifications.update({analyzer.__class__.__name__:classification})
                    self.score.update({analyzer.__class__.__name__:prediction})
        for name, value in self.newDatasetOptions.items():
            if value:
                classifications = []
                try:
                    if self.datasets[name]:
                        dataset = self.datasets[name]
                        dataset.class_is_last()
                        for classifierName, classifier in classifiers.items():
                            try:
                                classifier.build_classifier(dataset)
                                if self.graph:
                                    graph.plot_dot_graph(cls.graph, self.dataDir + "/graph/" + name + "Graph.png")
                                for instance in dataset:
                                    classifications.append(classifier.classify_instance(instance))
                            except Exception as e:
                                print(e)
                                logging.warning("Error using the " + classifierName + " classifier")
                                continue
                        if len(classifications) != 0:
                            counting = Counter(classifications)
                            prediction = str(counting.most_common(1)[0][1]) + ": " + str(counting.most_common(2)[0][1])
                            classification = counting.most_common(1)[0][0]
                            self.classifications.update({name:classification})
                            self.score.update({name:prediction})
                except Exception:
                    continue

    def createDatasets(self):
        '''A function that creates the initial datasets for feature selection. 2 particular arrays
        are defined, imageAttNames and pageAttNames, which contain the attribute type and name for
        each respective attribute.'''
        # Converting string attributes to nominal attributes (for machine learning purposes)
        # String attributes will remain string attributes when inserted into the database
        stringToNom = Filter(
            classname="weka.filters.unsupervised.attribute.StringToNominal", options=["-R", "first-last"])
        for analyzer in self.analyzers:
            atts = self.attributeCreation(analyzer.featureNames)
            datasetAtts = [att for att in atts]
            values = []
            if analyzer.__class__.__name__ in self.datasets.keys():
                dataset = self.datasets[analyzer.__class__.__name__]
            else:
                dataset = Instances.create_instances(
                    analyzer.__class__.__name__ + "Dataset", [att for att in datasetAtts], 0)
            for instance in analyzer.features:
                values = []
                attNum = 0
                for value in instance.values():
                    try:
                        float(value)
                        values.append(value)
                    except ValueError:
                        values.append(datasetAtts[attNum].add_string_value(value))
                    attNum += 1
                inst = Instance.create_instance(values)
                dataset.add_instance(inst)
            stringToNom.inputformat(dataset)
            dataset = stringToNom.filter(dataset)
            if analyzer.__class__.__name__ not in self.datasets.keys():
                self.datasets.update({analyzer.__class__.__name__:dataset})

        # I feel like there's probably a way to avoid (or minimize) all this iteration here and below
        # But because the datasets have different creation processes, I haven't figured out how yet
        if self.newDatasetOptions["ranked"]:
            # Where self.FS returns a dictionary of lists of attributes (if multiple datasets)
            attributes = self.FS()
            if not attributes:
                self.newDatasetOptions["ranked"] = False
            if self.newDatasetOptions["ranked"]:
                atts = []
                if len(attributes) != 0:
                    for dataset in attributes:
                        for attribute in dataset:
                            atts.append(attribute)
                else:
                    logging.warning("No attributes were returned from FS")
                if "ranked" in self.datasets.keys():
                    rankedDataset = self.datasets["ranked"]
                else:
                    rankedDataset = Instances.create_instances(
                        "rankedDataset", [att for att in atts], 0)
                for dataset in self.datasets.values():
                    index = []
                    for attribute in dataset.attributes():
                        if attribute in atts:
                            index.append(attribute.index())
                    for instance in dataset:
                        values = []
                        valueNum = 0
                        for value in instance.values:
                            if valueNum in index:
                                try:
                                    float(value)
                                    values.append(value)
                                except ValueError:
                                    values.append(atts[valueNum].add_string_value(value))
                            valueNum += 1
                        inst = Instance.create_instance(values)
                        rankedDataset.add_instance(inst)
                stringToNom.inputformat(rankedDataset)
                rankedDataset = stringToNom.filter(rankedDataset)
                if "ranked" not in self.datasets.keys():
                    self.datasets.update({"ranked":rankedDataset})

        if self.newDatasetOptions["full"]:
            values = []
            atts = [att for att in self.attributeCreation(self.allFeatureNames)]
            if "full" in self.datasets.keys():
                fullDataset = self.datasets["full"]
            else:
                fullDataset = Instances.create_instances(
                    "fullDataset", [att for att in atts], 0)
            for instance in self.allFeatures:
                attNum = 0
                for value in instance.values():
                    try:
                        float(value)
                        values.append(value)
                    except ValueError:
                        values.append(atts[attNum].add_string_value(value))
                    attNum += 1
                inst = Instance.create_instance(values)
                fullDataset.add_instance(inst)
            stringToNom.inputformat(fullDataset)
            fullDataset = stringToNom.filter(fullDataset)
            if "full" not in self.datasets.keys():
                self.datasets.update({"full":fullDataset})

        if self.newDatasetOptions["rankedBalanced"] or self.newDatasetOptions["rankedFull"]:
            self.generateInstances()


def main():
    # Initialization
    run = startFishing()
    run.initializeAll()

    fisher = scrape(urlFile="data/urls.txt",
        dataDir="data",
        driver=run.driver,
        classVal=0)

    # Initialization of the page analyzer
    pageData = page()
    fisher.addAnalyzer(pageData)

    # Initialization of the image analyzer
    imageData = image()
    fisher.addAnalyzer(imageData)

    # Once the analyzers have been added, it doesn't matter what
    # instance the goFish method is called with
    fisher.goFish()
    print(pageData.features)
    print(imageData.features)

    # Data Combination
    # The features generated from the other instances are then used
    # when dealing with (creating datasets, classifying, ect.) data
    # Takes the same arguments as the scrape class
    DC = saveFish(urlFile="data/urls.txt",
        dataDir="data",
        driver=run.driver,
        classVal=0,
        analyzers=fisher.analyzers,
        allFeatures=fisher.allFeatures,
        allFeatureNames=fisher.allFeatureNames)
    DC.createDatasets()
    DC.classify()
    print(DC.score)
    print(DC.classifications)
    
    DC.closePWW3()
    DC.closeSelenium()


if __name__ == "__main__":
    main()
