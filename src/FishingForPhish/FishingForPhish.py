# FishingForPhish.py: contains the major classes, functions, and objects
# I used throughout this research
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions
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
from collections import Counter
import requests
import os
from filetype import is_image
import sqlite3 as SQL
import cssutils
import logging
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning
import validators
import operator
import urllib
from urllib.parse import urlparse
import tldextract
from IPy import IP
import subprocess
from PIL import Image
import imagehash
import copy
from math import isnan


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
        else:
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
        if add_ons:
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

    def name(self):
        return self.__class__.__name__

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
            errors=[],
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
        self.urlNum = 0
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
                # Verifying db by using table names; efficient, but not thorough
                tables = {
                    "metadata": """CREATE TABLE metadata (id INTEGER PRIMARY KEY,
                    url TEXT UNIQUE, UTCtime INT, classification TEXT)""",
                    "errors": """CREATE TABLE errors (id INTEGER PRIMARY KEY, url TEXT, error TEXT)""",
                    "hashes": """CREATE TABLE hashes (phash INT, dhash INT, url TEXT)"""}
                self.cursor.execute("SELECT name FROM sqlite_master WHERE TYPE='table'")
                currentTables = self.cursor.fetchall()
                currentTables = [item for table in currentTables for item in table]
                for tableName, creation in tables.items():
                    if tableName in currentTables:
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
        print(str(analyzer.name()) + " added!")
        self.analyzers.append(analyzer)
        # A table is created for each added analyzer in this function
        columns = []
        if self.database:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE TYPE='table'")
            currentTables = self.cursor.fetchall()
            currentTables = [item for table in currentTables for item in table]
            if analyzer.name() not in currentTables:
                for name, datatype in analyzer.featureNames.items():
                    # Still should add more support for different datatypes
                    # in regards to autogenerating databases and datasets
                    # and the relation between the two
                    if datatype.lower() == "numeric":
                        columns.append(name + " FLOAT")
                    elif datatype.lower() == "string":
                        columns.append(name + " TEXT")
                    # classVal are not included in the solo dataset
                    # elif datatype.lower() == "nominal":
                    #     columns.append(name + " BOOLEAN")
                self.cursor.execute("CREATE TABLE {} (id INTEGER PRIMARY KEY, {})".format(
                    analyzer.name(), ",".join(name for name in columns)))

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
                self.errors.append(e)
                return False
            try:
                url = self.driver.current_url
            except Exception:
                time.sleep(10)
                try:
                    url = self.driver.current_url
                except Exception as e:
                    self.errors.append(e)
                    return False
            try:
                if requests.head(url, verify=False, timeout=5).status_code == 404:
                    self.errors.append(404)
                    return False
            except Exception as e:
                self.errors.append(e)
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
                logging.warning("Could not take a screenshot of " + url + " due to " + self.errors[0])
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
        '''Automates the scraping process by reading from the url file, validating the url,
        taking a screenshot (if necessary), saving html and css (if necessary), and then generating
        features by using Selenium and Beautiful Soup analysis using created analyzers'''
        if not self.driver:
            raise ReferenceError("Cannot scrape without a valid driver instance")
        # Create the allData table
        if self.database:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE TYPE='table'")
            currentTables = self.cursor.fetchall()
            currentTables = [item for table in currentTables for item in table]
            if "allData" not in currentTables:
                featureNames = []
                analyzerNum = 1
                for analyzer in self.analyzers:
                    if analyzerNum != len(self.analyzers):
                        features = {key:val for key, val in analyzer.featureNames.items() if key != 'classVal'}
                    else:
                        features = analyzer.featureNames
                    for name, datatype in features.items():
                        if datatype.lower() == "numeric":
                            datatype = " FLOAT"
                        elif datatype.lower() == "string":
                            datatype = " TEXT"
                        elif datatype.lower() == "nominal":
                            datatype = " BOOLEAN"
                        featureNames.append(name + datatype)
                    analyzerNum += 1
                self.cursor.execute("CREATE TABLE allData (id INTEGER PRIMARY KEY, {})".format(
                    ",".join(name for name in featureNames)))
        with open(self.urlFile, "r") as f:
            for line in f:
                print("url: " + str(line))
                features = {}
                url = line.strip()
                if not self.siteValidation(url):
                    if self.database:
                        self.cursor.execute(
                            "INSERT INTO errors (id, url, error) VALUES (?, ?)", (self.id, url, self.errors))
                    continue
                url = self.driver.current_url
                if not self.screenshotDir:
                    if self.database:
                        try:
                            time = self.getTime()
                            self.cursor.execute(
                                "INSERT INTO metadata (url, UTCtime, classification) VALUES (?, ?, ?)",
                                (url, time, self.classVal))
                            error = self.cursor.execute("SELECT id FROM errors WHERE id = ?", self.id)
                            if not bool(error):
                                self.cursor.execute("INSERT INTO errors (id) VALUES (?)", (self.id,))
                        except Exception:
                            # Ensuring that the attribute values are caught up to the database values
                            # This could be optimized; I'm currently relying on dictionary values
                            # being replaced when identical keys-values are inserted
                            self.id = self.cursor.execute(
                                "SELECT id FROM metadata WHERE url = ?", (url,))
                            try:
                                self.id = list(self.id)[0][0]
                                features = self.cursor.execute(
                                    "SELECT * FROM allData WHERE id = ?",
                                    (self.id,))
                                allFeatures = {}
                                allFeatureNames = {}
                                for analyzer in self.analyzers:
                                    analyzerFeatures = self.cursor.execute(
                                    "SELECT * FROM {} WHERE id = ?".format(analyzer.name()),
                                    (self.id,))
                                    analyzerFeaturesIter = list(analyzerFeatures)[0]
                                    newAnalyzerFeatures = {}
                                    featureNum = 0
                                    for column in analyzerFeatures.description:
                                        if featureNum == 0:
                                            featureNum += 1
                                            continue
                                        newAnalyzerFeatures.update({column[0]:analyzerFeaturesIter[featureNum]})
                                        featureNum += 1
                                    classVal = self.cursor.execute("SELECT classification FROM metadata WHERE id = ?", (self.id,))
                                    classVal = list(classVal)[0]
                                    allFeatures = allFeatures | copy.deepcopy(newAnalyzerFeatures)
                                    newAnalyzerFeatures.update({'classVal':classVal[0]})
                                    analyzer.features.append(newAnalyzerFeatures)
                                    names = self.cursor.execute("""SELECT name, type FROM
                                        pragma_table_info('{}')""".format(analyzer.name()))
                                    names = dict(names)
                                    featureNum = 0
                                    for name, datatype in names.items():
                                        if featureNum == 0:
                                            featureNum += 1
                                            continue
                                        if datatype == "INTEGER" or datatype == "FLOAT" or datatype == "INT":
                                            datatype = "numeric"
                                        elif datatype == "TEXT":
                                            datatype = "string"
                                        elif datatype == "BOOLEAN":
                                            datatype = "nominal"
                                        analyzer.featureNames.update({name:datatype})
                                    analyzerFeatureNames = copy.deepcopy(analyzer.featureNames)
                                    analyzerFeatureNames.pop('classVal')
                                    allFeatureNames = allFeatureNames | analyzerFeatureNames
                                allFeatures.update({'classVal':classVal[0]})
                                if len(self.allFeatureNames) == 0:
                                    self.allFeatureNames = self.allFeatureNames | allFeatureNames
                                    self.allFeatureNames.update({'classVal':'nominal'})
                                self.allFeatures.append(allFeatures)
                                continue
                            except Exception:
                                raise ValueError("""Could not select the features from the url: """ + url)
                    self.saveScreenshot(url, validated=True)
                filename = self.generateFilename(url)
                if not self.htmlDir:
                    html = self.driver.page_source
                    self.initializeBS(html)
                    prettyHTML = self.BS.prettify()
                    if not os.path.isfile(
                            self.dataDir + "/html/" + filename + ".html"):
                        with open(self.dataDir + "/html/" + filename + ".html", "w") as f:
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
                            self.dataDir + "/css/" + filename + ".css"):
                        with open(self.dataDir + "/css/" + filename + ".css", "w") as f:
                            f.write(sheet.cssText.decode())
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
                    updatedResources = analyzer.analyze(url, filename, resources, self.urlNum)
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
                        if self.urlNum <= len(self.analyzers):
                            self.allFeatureNames = self.allFeatureNames | newFeatureNames
                    if self.database:
                        newFeatures = {key:val for key, val in newFeatures.items() if key != 'classVal'}
                        newFeatureNames = {key:val for key, val in newFeatureNames.items() if key != 'classVal'}
                        self.cursor.execute("""INSERT INTO {} ({}) VALUES ({})""".format(analyzer.name(),
                            ",".join(name for name in newFeatureNames.keys()),
                            ",".join("?" for i in range(len(newFeatureNames.keys())))),
                            [value for value in newFeatures.values()])
                    classCheck += 1
                if self.database:
                    self.cursor.execute("""INSERT INTO allData ({}) VALUES ({})""".format(
                        ",".join(name for name in self.allFeatureNames.keys()),
                        ",".join("?" for i in range(len(self.allFeatureNames.keys())))),
                        [value for value in features.values()])
                self.allFeatures.append(features)
                if self.database:
                    self.conn.commit()
                self.id += 1
                self.urlNum += 1


class pageAnalyzer(analyzer):
    '''A class for scraping page-based features'''

    def __init__(self, features=[], featureNames={
        'NumDots':"numeric",
        'SubdomainLevel':"numeric",
        'PathLevel':"numeric",
        'UrlLength':"numeric",
        'NumDash':"numeric",
        'NumDashInHostname':"numeric",
        'AtSymbol':"numeric",
        'TildeSymbol':"numeric",
        'NumUnderscore':"numeric",
        'NumPercent':"numeric",
        'NumQueryComponents':"numeric",
        'NumAmpersand':"numeric",
        'NumHash':"numeric",
        'NumNumericChars':"numeric",
        'NoHttps':"numeric",
        'RandomString':"numeric",
        'IpAddress':"numeric",
        'DomainInSubdomains':"numeric",
        'DomainInPaths':"numeric",
        'HttpsInHostname':"numeric",
        'HostnameLength':"numeric",
        'PathLength':"numeric",
        'QueryLength':"numeric",
        'DoubleSlashInPath':"numeric",
        'NumSensitiveWords':"numeric",
        'EmbeddedBrandName':"numeric",
        'PctExtHyperlinks':"numeric",
        'PctExtResourceUrls':"numeric",
        'ExtFavicon':"numeric",
        'InsecureForms':"numeric",
        'RelativeFormAction':"numeric",
        'ExtFormAction':"numeric",
        'AbnormalFormAction':"numeric",
        'PctNullSelfRedirectHyperlinks':"numeric",
        'FrequentDomainNameMismatch':"numeric",
        'FakeLinkInStatusBar':"numeric",
        'RightClickDisabled':"numeric",
        'PopUpWindow':"numeric",
        'SubmitInfoToEmail':"numeric",
        'IframeOrFrame':"numeric",
        'MissingTitle':"numeric",
        'ImagesOnlyInForm':"numeric",
        'SubdomainLevelRT':"numeric",
        'UrlLengthRT':"numeric",
        'PctExtResourceUrlsRT':"numeric",
        'AbnormalExtFormActionR':"numeric",
        'ExtMetaScriptLinkRT':"numeric",
        'PctExtNullSelfRedirectHyperlinksRT':"numeric",
        "classVal":"nominal"
    }, classVal=Instance.missing_value(), **kwargs):
        '''Inherits all previous attributes, adds an optional attribute called pageFeatures
        (although the purpose of the function is to populate the pageFeatures list, so there
        isn't much of a point in passing in a value pageFeatures. If you already have a value,
        I recommend either scraping image data as well
        or creating an instance of the combine class to create datasets of your data)'''
        super().__init__(**kwargs)
        # For each analyzer, it is recommended that you create attributes for features and featureNames
        # You can return them as values instead in the analyze function, but it may be useful for convenience purposes
        self.features = features
        self.featureNames = featureNames
        self.classVal = classVal

    def get_complete_webpage_url(self, saved_actual_url):
        parsed = urlparse(saved_actual_url)

        if saved_actual_url.endswith('/') and '?' not in saved_actual_url:

            complete_webpage_url = saved_actual_url + 'index.html'

        elif parsed.netloc != '' and parsed.path == '':

            complete_webpage_url = saved_actual_url + '/index.html'

        # parsed.path has some string but no filename extension
        elif not saved_actual_url.endswith('/') and parsed.path != '':

            if not saved_actual_url.endswith('.htm') and not saved_actual_url.endswith('.html'):

                complete_webpage_url = saved_actual_url + '.html'
            else:
                complete_webpage_url = saved_actual_url

        return complete_webpage_url

    def analyze(self, url, filename, resources, urlNum):

        # Initialize feature dictionary
        features = {}

        for name in self.featureNames.keys():
            features.update({name:0})

        parsed = urlparse(url)

        # Count number of dots in full URL
        features.update({'NumDots':url.count('.')})

        # Count path level
        if parsed.path != '':

            if parsed.path == '/':
                features.update({'PathLevel':0})
            else:
                parsed_path_list = parsed.path.split('/')
                features.update({'PathLevel':len(parsed_path_list) - 1})

        # no path
        else:
            features.update({'PathLevel':0})

        # Count total characters in URL
        features.update({'UrlLength':len(url)})

        # Count total characters in URL (RT)
        if len(url) < 54:
            features.update({'UrlLengthRT':1})
        elif len(url) >= 54 and len(url) <= 75:
            features.update({'UrlLengthRT':0})
        else:
            features.update({'UrlLengthRT':-1})

        # Count dash symbol in full URL
        features.update({'NumDash':url.count('-')})

        # Count dash symbol in hostname
        features.update({'NumDashInHostname':parsed.netloc.count('-')})

        # Check @ symbol in URL
        if '@' in url:
            features.update({'AtSymbol':1})
        else:
            features.update({'AtSymbol':0})

        # Check tilde symbol in URL
        if '~' in url:
            features.update({'TildeSymbol':1})
        else:
            features.update({'TildeSymbol':0})

        # Count underscore symbol in URL
        features.update({'NumUnderscore':url.count('_')})

        # Count percent symbol in URL
        features.update({'NumPercent':url.count('%')})

        # Count number of query components in URL
        features.update({'NumQueryComponents':parsed.query.count('=')})

        # Count ampersand symbol in URL
        features.update({'NumAmpersand':url.count('&')})

        # Count hash symbol in URL
        features.update({'NumHash':url.count('#')})

        # Count numeric characters in URL
        features.update({'NumNumericChars':sum(char.isdigit() for char in url)})

        # Check no HTTPS
        if parsed.scheme == 'http':
            features.update({'NoHttps':1})
        elif parsed.scheme == 'https':
            features.update({'NoHttps':0})

        # Check random string in URL
        parsed_netloc_str = parsed.netloc

        # check for hostname part
        for token in parsed_netloc_str.replace(
                '.', ' ').replace('-', ' ').split(' '):
            consonant_count = 0

            for char in token.lower():
                if (char != 'a' and char != 'e' and char != 'i' and char != 'o' and char != 'u'):
                    consonant_count += 1
                else:
                    # reset consonant count
                    consonant_count = 0

                # assume 4 consonants is not pronounciable
                if consonant_count == 4:
                    features.update({'RandomString':1})
                    break
                else:
                    features.update({'RandomString':0})

        # continue checking path if no random string found previously
        if features['RandomString'] != 1:

            # check for path part
            for token in parsed.path.replace(
                    '/',
                    ' ').strip().replace(
                    '-',
                    ' ').replace(
                    '_',
                    ' ').replace(
                        '.',
                    ' ').split(' '):
                consonant_count = 0
                possible_random_str = ''

                for char in token.lower():
                    if (char != 'a' and char != 'e' and char !=
                            'i' and char != 'o' and char != 'u'):
                        consonant_count += 1
                        possible_random_str += char
                    else:
                        # reset consonant count
                        consonant_count = 0

                    if consonant_count == 4 and possible_random_str not in [
                            'html', 'xhtml']:
                        features.update({'RandomString':1})
                        break

        base_url_to_be_replaced = 'file:' + urllib.request.pathname2url(resources["dataDir"]) + str(urlNum) + '/'

        url_scheme = parsed.scheme + '://'

        # ext = tldextract.TLDExtract(suffix_list_urls=None, fallback_to_snapshot=False)
        ext = tldextract.TLDExtract(suffix_list_urls=None)
        ext1 = ext(url)
        domain_query = ext1.domain + '.' + ext1.suffix

        if ext1.suffix == '':
            try:
                IP(ext1.domain)
                domain_query = ext1.domain

                features.update({'IpAddress':1})

            except BaseException:
                pass
                features.update({'IpAddress':0})

        # Count level of subdomains
        if ext1.subdomain == '':
            features.update({'SubdomainLevel':0})
        else:
            subdomain_list = ext1.subdomain.split('.')
            features.update({'SubdomainLevel':len(subdomain_list)})

        # Check multiple subdomains (RT)
        if ext1.subdomain == '':
            features.update({'SubdomainLevelRT':1})
        else:
            subdomain_domain_str = ext1.subdomain + '.' + ext1.domain

            if subdomain_domain_str.lower().startswith('www.'):
                # discard 'www.' string
                subdomain_domain_str = subdomain_domain_str[4:]

            if subdomain_domain_str.count('.') <= 1:
                features.update({'SubdomainLevelRT':1})

            elif subdomain_domain_str.count('.') == 2:
                features.update({'SubdomainLevelRT':0})

            else:
                features.update({'SubdomainLevelRT':-1})

        extraction = tldextract.extract(url)
        urlSuffix = extraction.suffix

        # Check TLD or ccTLD used in subdomain part
        if ext1.subdomain == '':
            features.update({'DomainInSubdomains':0})
        else:
            for token in urlSuffix:
                # if token in ext1.subdomain.lower():
                token_location = ext1.subdomain.lower().find(token)
                if token_location != -1:

                    if ext1.subdomain.lower().startswith(token):
                        pass

                    elif ext1.subdomain.lower().endswith(token):
                        if not ext1.subdomain[token_location - 1].isalnum():

                            features.update({'DomainInSubdomains':1})
                            break

                    elif not ext1.subdomain[token_location - 1].isalnum() and not ext1.subdomain[token_location + len(token)].isalnum():

                        features.update({'DomainInSubdomains':1})
                        break

        # Check TLD or ccTLD used in path part
        if parsed.path == '':
            features.update({'DomainInPaths':0})
        else:
            for token in urlSuffix:
                token_location = parsed.path.lower().find(token)

                if token_location != -1:

                    if parsed.path.lower().startswith(token):
                        pass

                    elif parsed.path.lower().endswith(token):
                        if not parsed.path[token_location - 1].isalnum():

                            features.update({'DomainInPaths':1})
                            break

                    elif not parsed.path[token_location - 1].isalnum() and not parsed.path[token_location + len(token)].isalnum():

                        features.update({'DomainInPaths':1})
                        break

        # Check https is obfuscated in hostname
        if 'https' in parsed.netloc.lower():
            features.update({'HttpsInHostname':1})
        else:
            features.update({'HttpsInHostname':0})

        # Count length of hostname
        features.update({'HostnameLength':len(parsed.netloc)})

        # Count length of path
        features.update({'PathLength':len(parsed.path)})

        # Count length of query
        features.update({'QueryLength':len(parsed.query)})

        # Check double slash exist in path
        if '//' in parsed.path:
            features.update({'DoubleSlashInPath':1})

        else:
            features.update({'DoubleSlashInPath':0})

        # Check how many sensitive words occur in URL
        sensitive_word_list = [
            'secure',
            'account',
            'webscr',
            'login',
            'ebayisapi',
            'signin',
            'banking',
            'confirm']
        features.update({'NumSensitiveWords':0})
        for word in sensitive_word_list:
            if word in url.lower():
                features['NumSensitiveWords'] += 1

        caching = False

        if not caching:
            resources["driver"].set_page_load_timeout(120)

            try:
                resources["driver"].get(url)
            except BaseException:
                pass

            # SWITCH OFF ALERTS
            while True:
                try:
                    WebDriverWait(
                        resources["driver"], 3).until(
                        expected_conditions.alert_is_present())

                    # alert = resources["driver"].switch_to_alert()
                    alert = resources["driver"].switch_to.alert
                    alert.dismiss()

                except TimeoutException:
                    break

            total_input_field = 0

            captured_domains = []

            resource_URLs = []
            hyperlink_URLs = []
            meta_script_link_URLs = []
            request_URLs = []
            null_link_count = 0
            original_link_count = 0

            # Extracts main visible text from HTML
            iframe_frame_elems = ''
            iframe_frame_elems = resources["driver"].find_elements(By.TAG_NAME, 'iframe')
            iframe_frame_elems.extend(
                resources["driver"].find_elements(
                    By.TAG_NAME, 'frame'))

            # Check iframe or frame exist
            if len(iframe_frame_elems) > 0:
                features.update({'IframeOrFrame':1})
            else:
                features.update({'IframeOrFrame':0})

            for iframe_frame_elem in iframe_frame_elems:
                iframe_frame_style = iframe_frame_elem.get_attribute(
                    'style').replace(' ', '')
                if iframe_frame_style.find(
                        "visibility:hidden") == -1 and iframe_frame_style.find("display:none") == -1:

                    try:
                        resources["driver"].switch_to.frame(iframe_frame_elem)
                    except BaseException:
                        continue

                    try:
                        input_field_list = resources["driver"].find_elements(
                            By.XPATH, '//input')
                    except BaseException:
                        input_field_list = []

                    total_input_field += len(input_field_list)

                    tag_attrib = ['src', 'href']
                    tag_count = 0
                    link_count = 0

                    # Extract all URLs
                    while tag_count <= 1:
                        elements = resources["driver"].find_elements(
                            By.XPATH, '//*[@' + tag_attrib[tag_count] + ']')
                        if elements:
                            for elem in elements:
                                try:
                                    link = ''
                                    link = elem.get_attribute(
                                        tag_attrib[tag_count])

                                    # Check null link
                                    null_link_detected = False
                                    if tag_count == 1 and elem.get_attribute('outerHTML').lower().startswith('<a') and (
                                        link.startswith('#') or link == '' or link.lower().replace(
                                            ' ', '').startswith('javascript::void(0)')):
                                        null_link_count += 1
                                        null_link_detected = True

                                    # Construct full URL from relative URL (if
                                    # webpage sample is processed offline)
                                    if not link.startswith('http') and not link.startswith(
                                            "javascript"):
                                        # link = base_url + '/' + link    # this is
                                        # for live relative URLs

                                        # link = link.replace(base_url_to_be_replaced, url)

                                        link = link.replace(
                                            base_url_to_be_replaced, url_scheme)
                                        link = link.replace('///', '//')
                                        link = link.replace(
                                            'file://C:/', url)
                                        # link = link.replace('file:///', url_scheme)
                                        link = link.replace(
                                            'file://', url_scheme)

                                        # pass

                                    link_count += 1
                                    original_link_count += 1

                                    # Check null link after constructing full URL
                                    # from local URL (if webpage sample is
                                    # processed offline)
                                    if tag_count == 1 and elem.get_attribute('outerHTML').lower().startswith('<a') and not null_link_detected and (
                                            link == self.get_complete_webpage_url(url, urlNum) or link == self.get_complete_webpage_url(url, urlNum) + '#'):
                                        null_link_count += 1

                                    # print link
                                    # if link not in captured_domains and link !=
                                    # "":
                                    if link != '' and link.startswith('http'):

                                        captured_domains.append(link)

                                        if tag_count == 0:
                                            resource_URLs.append(link)
                                        elif tag_count == 1:
                                            if not elem.get_attribute('outerHTML').lower(
                                            ).startswith('<link'):
                                                hyperlink_URLs.append(link)
                                            else:
                                                if elem.get_attribute('rel') in [
                                                'stylesheet', 'shortcut icon', 'icon']:
                                                    resource_URLs.append(link)

                                        # RT
                                        if elem.get_attribute('outerHTML').lower().startswith('<meta') or \
                                                elem.get_attribute('outerHTML').lower().startswith('<script') or \
                                                elem.get_attribute('outerHTML').lower().startswith('<link'):

                                            meta_script_link_URLs.append(link)

                                        elif elem.get_attribute('outerHTML').lower().startswith('<a'):
                                            pass
                                        else:
                                            request_URLs.append(link)

                                except BaseException:
                                    pass

                        tag_count += 1

                    resources["driver"].switch_to.default_content()

            resources["driver"].switch_to.default_content()

            try:
                input_field_list = resources["driver"].find_elements(By.XPATH, '//input')
            except BaseException:
                pass

            total_input_field += len(input_field_list)

            tag_attrib = ['src', 'href']
            tag_count = 0
            link_count = 0

            # Extract all URLs
            while tag_count <= 1:
                elements = ''
                elements = resources["driver"].find_elements(
                    By.XPATH, '//*[@' + tag_attrib[tag_count] + ']')

                for elem in elements:

                    try:
                        link = ''
                        link = elem.get_attribute(tag_attrib[tag_count])

                        # Check null links
                        null_link_detected = False
                        # if tag_count == 1 and (link.startswith('#') or link ==
                        # ''):
                        if tag_count == 1 and elem.get_attribute('outerHTML').lower().startswith('<a') and (
                            link.startswith('#') or link == '' or link.lower().replace(
                                ' ', '').startswith('javascript::void(0)')):
                            null_link_count += 1
                            null_link_detected = True

                        # Construct full URL from relative URL (if webpage sample
                        # is processed offline)
                        if not link.startswith('http') and not link.startswith(
                                "javascript"):
                            # link = base_url + '/' + link

                            # link = link.replace(base_url_to_be_replaced, url)

                            link = link.replace(
                                base_url_to_be_replaced, url_scheme)
                            link = link.replace('///', '//')
                            link = link.replace('file://C:/', url)

                            link = link.replace('file://', url_scheme)

                        link_count += 1
                        original_link_count += 1

                        # Check null links after constructing full URL from local
                        # URL (if webpage sample is processed offline)
                        if tag_count == 1 and elem.get_attribute('outerHTML').lower().startswith('<a') and not null_link_detected and (
                                link == self.get_complete_webpage_url(url) or link == self.get_complete_webpage_url(url) + '#'):
                            null_link_count += 1
                            null_link_detected = True

                        if link != '' and link.startswith('http'):

                            captured_domains.append(link)

                            if tag_count == 0:
                                resource_URLs.append(link)
                            elif tag_count == 1:
                                if not elem.get_attribute('outerHTML').lower(
                                ).startswith('<link'):
                                    hyperlink_URLs.append(link)
                                else:
                                    if elem.get_attribute('rel') in [
                                    'stylesheet', 'shortcut icon', 'icon']:
                                        resource_URLs.append(link)

                            if elem.get_attribute('outerHTML').lower().startswith('<meta') or \
                                    elem.get_attribute('outerHTML').lower().startswith('<script') or \
                                    elem.get_attribute('outerHTML').lower().startswith('<link'):

                                meta_script_link_URLs.append(link)

                            elif elem.get_attribute('outerHTML').lower().startswith('<a'):
                                pass
                            else:
                                request_URLs.append(link)

                    except BaseException:
                        pass

                tag_count += 1

            # Calculate null or self redirecct hyperlinks

            # feature['PctNullSelfRedirectHyperlinks'] =
            # float('{:.6f}'.format(float(null_link_count)/float(original_link_count)))
            # fixed to 10 decimal places
            if len(hyperlink_URLs) > 0:
                features.update({'PctNullSelfRedirectHyperlinks':'{:.10f}'.format(float(
                    null_link_count) / float(len(hyperlink_URLs)))})
            else:
                features.update({'PctNullSelfRedirectHyperlinks':'{:.10f}'.format(
                    0)})

        # Check whether brand name appears in subdomains and paths

        # domain_tokens = tldextract.TLDExtract(suffix_list_urls=None, fallback_to_snapshot=False)
        domain_tokens = tldextract.TLDExtract(suffix_list_urls=None)
        domains = []
        domains_freq = {}

        # create dictionary of domain frequencies
        # (I think iterating over captured_domains is fine;
        # I had to refactor the code slightly)
        for url in captured_domains:
            domain_str = domain_tokens(url).domain + '.' + domain_tokens(url).suffix

            if url.startswith('http') and domain_str not in domains:

                domains.append(domain_str)

            if url.startswith('http'):
                if domain_str not in domains_freq:
                    domains_freq[domain_str] = 1
                else:
                    domains_freq[domain_str] += 1

            if len(url) > 0:
                max_freq_domain = max(
                    domains_freq.items(),
                    key=operator.itemgetter(1))[0]
            else:
                max_freq_domain = ''

            try:
                # is IP
                IP(max_freq_domain)
                brand_name = max_freq_domain

            # not IP, extract first dot separated token
            except BaseException:
                pass
                brand_name = max_freq_domain.split('.')[0]

        parsed = urlparse(url)
        # ext = tldextract.TLDExtract(suffix_list_urls=None, fallback_to_snapshot=False)
        ext = tldextract.TLDExtract(suffix_list_urls=None)
        ext1 = ext(url)
        if brand_name.lower() in ext1.subdomain.lower(
        ) or brand_name.lower() in parsed.path.lower():
            if brand_name != '':
                features.update({'EmbeddedBrandName':1})
            else:
                features.update({'EmbeddedBrandName':0})
        else:
            features.update({'EmbeddedBrandName':0})

        # Check frequent domain name in HTML matches with webpage domain name
        if max_freq_domain != domain_query:
            features.update({'FrequentDomainNameMismatch':1})
        else:
            features.update({'FrequentDomainNameMismatch':0})

        # Count percentage of external hyperlinks
        external_hyperlink_count = 0

        for link in hyperlink_URLs:

            ext2 = ext(link)

            domain_str_ext2 = ext2.domain + '.' + ext2.suffix
            if ext2.suffix == '':
                try:
                    IP(ext2.domain)
                    domain_str_ext2 = ext2.domain

                except BaseException:
                    pass

            if domain_str_ext2 != domain_query:
                external_hyperlink_count += 1

        # print 'len(hyperlink_URLs) = ' + str(len(hyperlink_URLs))
        # feature['PctExtHyperlinks'] =
        # float('{:.6f}'.format(float(external_hyperlink_count)/float(len(hyperlink_URLs))))
        # fixed to 10 decimal places
        if len(hyperlink_URLs) > 0:
            features.update({'PctExtHyperlinks':'{:.10f}'.format(
                float(external_hyperlink_count) /
                float(
                    len(hyperlink_URLs)))})
        else:
            features.update({'PctExtHyperlinks':'{:.10f}'.format(0)})

        # Calculate URL of anchor (RT)
        percent_external_or_null_hyperlinks = float(
            features['PctExtHyperlinks']) + float(features['PctNullSelfRedirectHyperlinks'])

        if percent_external_or_null_hyperlinks < 0.31:
            features.update({'PctExtNullSelfRedirectHyperlinksRT':1})
        elif percent_external_or_null_hyperlinks >= 0.31 and percent_external_or_null_hyperlinks <= 0.67:
            features.update({'PctExtNullSelfRedirectHyperlinksRT':0})
        else:
            features.update({'PctExtNullSelfRedirectHyperlinksRT':-1})

        # Count percentage of external resources
        external_resource_count = 0

        for url in resource_URLs:

            ext2 = ext(url)

            domain_str_ext2 = ext2.domain + '.' + ext2.suffix
            if ext2.suffix == '':
                try:
                    IP(ext2.domain)
                    domain_str_ext2 = ext2.domain

                except BaseException:
                    pass

            if domain_str_ext2 != domain_query:
                external_resource_count += 1

        if len(resource_URLs) > 0:
            # fix to 10 decimal places
            features.update({'PctExtResourceUrls':'{:.10f}'.format(
                float(external_resource_count) /
                float(
                    len(resource_URLs)))})
        else:
            # fix to 10 decimal places
            features.update({'PctExtResourceUrls':'{:.10f}'.format(
                0)})

        # Count percentage of external request URLs (RT)
        external_request_URLs = 0
        for url in request_URLs:

            ext2 = ext(url)

            domain_str_ext2 = ext2.domain + '.' + ext2.suffix
            if ext2.suffix == '':
                try:
                    IP(ext2.domain)
                    domain_str_ext2 = ext2.domain

                except BaseException:
                    pass

            if domain_str_ext2 != domain_query:
                external_request_URLs += 1

        # print 'len(request_URLs) = ' + str(len(request_URLs))

        if len(request_URLs) > 0:
            if float(external_request_URLs) / float(len(request_URLs)) < 0.22:
                features.update({'PctExtResourceUrlsRT':1})
            elif float(external_request_URLs) / float(len(request_URLs)) >= 0.22 and float(external_request_URLs) / float(len(request_URLs)) <= 0.61:
                features.update({'PctExtResourceUrlsRT':0})
            else:
                features.update({'PctExtResourceUrlsRT':-1})
        else:
            features.update({'PctExtResourceUrlsRT':1})

        # Count percentage external meta script link (RT)
        external_meta_script_link_count = 0
        for meta_script_link_URL in meta_script_link_URLs:

            ext_meta_script_link = ext(meta_script_link_URL)

            domain_str_ext_meta_script_link = ext_meta_script_link.domain + \
                '.' + ext_meta_script_link.suffix
            if ext_meta_script_link.suffix == '':
                try:
                    IP(ext_meta_script_link.domain)
                    domain_str_ext_meta_script_link = ext_meta_script_link.domain

                except BaseException:
                    pass

            if domain_str_ext_meta_script_link != domain_query:
                external_meta_script_link_count += 1

        # print 'len(meta_script_link_URLs) = ' + str(len(meta_script_link_URLs))
        if len(meta_script_link_URLs) > 0:
            if float(external_meta_script_link_count) / \
                    float(len(meta_script_link_URLs)) < 0.17:
                features.update({'ExtMetaScriptLinkRT':1})
            elif float(external_meta_script_link_count) / float(len(meta_script_link_URLs)) >= 0.17 and float(external_meta_script_link_count) / float(len(meta_script_link_URLs)) <= 0.81:
                features.update({'ExtMetaScriptLinkRT':0})
            else:
                features.update({'ExtMetaScriptLinkRT':-1})
        else:
            features.update({'ExtMetaScriptLinkRT':1})

        # Check whether favicon is external
        # <link rel="shortcut icon" type="image/ico" href="favicon.ico" />

        link_elems = resources["driver"].find_elements(By.XPATH, 'link')
        favicon_URL = ''

        for link_elem in link_elems:
            if link_elem.get_attribute(
                    'rel') == 'shortcut icon' or link_elem.get_attribute('rel') == 'icon':
                favicon_URL = link_elem.get_attribute('href')
                break

        if favicon_URL != '':
            # if favicon_URL.startswith('http'):
            ext_fav = ext(favicon_URL)

            domain_str_ext_fav = ext_fav.domain + '.' + ext_fav.suffix
            if ext_fav.suffix == '':
                try:
                    IP(ext_fav.domain)
                    domain_str_ext_fav = ext_fav.domain

                except BaseException:
                    pass

            if domain_str_ext_fav != domain_query:
                features.update({'ExtFavicon':1})
            else:
                features.update({'ExtFavicon':0})

        else:
            features.update({'ExtFavicon':0})

        form_elems = resources["driver"].find_elements(By.TAG_NAME, 'form')

        # Check for external form action
        for form_elem in form_elems:

            if form_elem.get_attribute('action') is not None:
                if form_elem.get_attribute('action').startswith('http'):

                    # check internal or external form
                    ext_form = ext(form_elem.get_attribute('action'))

                    domain_str_ext_form = ext_form.domain + '.' + ext_form.suffix
                    if ext_form.suffix == '':
                        try:
                            IP(ext_form.domain)
                            domain_str_ext_form = ext_form.domain

                        except BaseException:
                            pass

                    if domain_str_ext_form != domain_query:
                        features.update({'ExtFormAction':1})
                        break

        # Check for insecure form action
        for form_elem in form_elems:

            if form_elem.get_attribute('action') is not None:

                if form_elem.get_attribute('action').startswith('http'):

                    if form_elem.get_attribute('action').startswith('https'):
                        pass
                    else:
                        features.update({'InsecureForms':1})
                        break

                else:
                    # look at page URL
                    if parsed.scheme == 'https':
                        pass
                    else:
                        features.update({'InsecureForms':1})
                        break

        # Check for relative form action
        for form_elem in form_elems:

            if form_elem.get_attribute('action') is not None:

                if form_elem.get_attribute('action').startswith('http'):
                    pass

                else:
                    features.update({'RelativeFormAction':1})
                    break

        # Check for abnormal form action
        for form_elem in form_elems:

            if form_elem.get_attribute('action') is not None:
                # if normal form
                if form_elem.get_attribute('action').startswith('http'):
                    pass
                else:

                    if form_elem.get_attribute('action').lower().replace(' ', '') in [
                            '', '#', 'about:blank', 'javascript:true']:
                        features.update({'AbnormalFormAction':1})
                        break

        # Check server form handler (R)
        # otherwise legitimate state
        features.update({'AbnormalExtFormActionR':1})
        for form_elem in form_elems:

            if form_elem.get_attribute('action') is not None:
                # check link to external domain
                if form_elem.get_attribute('action').startswith(
                        'http'):
                    # pass

                    ext_form = ext(form_elem.get_attribute('action'))

                    domain_str_form = ext_form.domain + '.' + ext_form.suffix
                    if ext_form.suffix == '':
                        try:
                            IP(ext_form.domain)
                            domain_str_form = ext_form.domain

                        except BaseException:
                            pass

                    if domain_str_form != domain_query:
                        features.update({'AbnormalExtFormActionR':0})
                        break

                else:

                    if form_elem.get_attribute('action').lower().replace(
                            ' ', '') in ['', 'about:blank']:
                        features.update({'AbnormalExtFormActionR':-1})
                        break

        # Check for right click disabled
        page_src_str = resources["driver"].page_source
        page_src_no_space_lower_str = page_src_str.replace(' ', '').lower()

        # document.addEventListener('contextmenu', event =>
        # event.preventDefault());

        if 'addEventListener'.lower() in page_src_no_space_lower_str and 'contextmenu' in page_src_no_space_lower_str and 'preventDefault' in page_src_no_space_lower_str:
            features.update({"RightClickDisabled":1})

        elif 'event.button==2' in page_src_no_space_lower_str:
            features.update({'RightClickDisabled':1})

        else:
            disable_right_click_list = resources["driver"].find_elements(
                By.XPATH, '//*[@oncontextmenu="return false"]')
            disable_right_click_list.extend(resources["driver"].find_elements(
                By.XPATH, '//*[@oncontextmenu="return false;"]'))

            if len(disable_right_click_list) > 0:
                features.update({'RightClickDisabled':1})

        # Check for pop-up

            # if 'window.open(' in page_src_no_space_lower_str and
            # ('onLoad="'.lower() in page_src_no_space_lower_str or
            # 'onClick="'.lower() in page_src_no_space_lower_str):

        onload_count = len(resources["driver"].find_elements(By.XPATH, '//*[@onLoad]'))
        onclick_count = len(resources["driver"].find_elements(By.XPATH, '//*[@onClick]'))

        if 'window.open(' in page_src_no_space_lower_str and (
                onload_count > 0 or onclick_count > 0):
            features.update({'PopUpWindow':1})
        else:
            features.update({'PopUpWindow':0})

        # Check mailto function exist
        if 'mailto:' in page_src_no_space_lower_str:
            features.update({'SubmitInfoToEmail':1})
        else:
            features.update({'SubmitInfoToEmail':0})

        # Check for empty webpage title
        if resources["driver"].title.strip() == '':
            features.update({'MissingTitle':1})
        else:
            features.update({'MissingTitle':0})

        # Check whether form contain only images without text
        form_elems = resources["driver"].find_elements(By.TAG_NAME, 'form')
        visible_text_in_form = ''
        image_elems_in_form = []
        for form_elem in form_elems:

            # visible_text_in_form += form_elem.text.strip() + ' '
            try:
                visible_text_in_form += form_elem.text.strip() + ' '
            except BaseException:
                pass

            image_elems_in_form.extend(form_elem.find_elements(By.XPATH, './/img'))

        if visible_text_in_form.strip() == '' and len(image_elems_in_form) > 0:
            features.update({'ImagesOnlyInForm':1})
        else:
            features.update({'ImagesOnlyInForm':0})

        # Check for fake links in status bar

        # case 1 - mentioned alot in literature
        hyperlinks_case_1 = resources["driver"].find_elements(
            By.XPATH, '//a[@onmouseover and @onmouseout]')
        if 'window.status=' in page_src_no_space_lower_str and len(
                hyperlinks_case_1) > 0:
            features.update({'FakeLinkInStatusBar':1})

        # #case2  - Google search result ads using this           # Disable this temporarily
        # hyperlinks_case_2 = resources["driver"].find_elements_by_xpath('//a[@onclick]')
        # if len(hyperlinks_case_2) > 0 and ('location.href=' in page_src_no_space_lower_str or 'document.location=' in page_src_no_space_lower_str or 'window.location=' in page_src_no_space_lower_str or 'this.href=' in page_src_no_space_lower_str):
            # feature['FakeLinkInStatusBar'] = 1

        # case 3
        if 'onclick=' in page_src_no_space_lower_str and 'stopEvent'.lower() in page_src_no_space_lower_str and (
                'location.href=' in page_src_no_space_lower_str or 'document.location=' in page_src_no_space_lower_str or 'window.location=' in page_src_no_space_lower_str or 'this.href=' in page_src_no_space_lower_str):
            features.update({'FakeLinkInStatusBar':1})

        features.update({"classVal":self.classVal})
        self.features.append(features)
        resources.update({"features":features})
        resources.update({"featureNames":self.featureNames})
        return resources


class imageAnalyzer(analyzer):
    '''A class for scraping image-based features'''

    def __init__(self, features=[], featureNames={
        "numTagsInHtml":"numeric",
        "numTagsInHead":"numeric",
        "numTagsInMain":"numeric",
        "numTagsInBody":"numeric",
        "pctImgTags":"numeric",
        "totalWidth":"numeric",
        "totalHeight":"numeric",
        "IMredMean":"numeric",
        "IMredStdDev":"numeric",
        "IMgreenMean":"numeric",
        "IMgreenStdDev":"numeric",
        "IMblueMean":"numeric",
        "IMblueStdDev":"numeric",
        "IMalphaChannel":"numeric",
        "IMgamma":"numeric",
        "numBoldTags":"numeric",
        "averageFontWeight":"numeric",
        "mostUsedFont":"string",
        "averageFontSize":"numeric",
        "numStyles":"numeric",
        "mostUsedStyle":"string",
        "pctItalics":"numeric",
        "pctUnderline":"numeric",
        "imageOverlappingTop":"numeric",
        "favicon":"numeric",
        "classVal":"nominal"
    }, HASH=False, classVal=Instance.missing_value(), **kwargs):
        '''Similarily to the pageBased class, inherits all attributes from the initialize and scape classes,
        (not pageFeatures) and adds an optional attribute called imageFeatures'''
        super().__init__(**kwargs)
        self.features = features
        self.featureNames = featureNames
        self.classVal = classVal
        self.HASH = HASH
        # An alternative attribute so imagehashing isn't locked behind database functionality
        self.hashes = []

    def getImagemagickData(self, result):
        if result[0:6] != "Image:":
            logging.warning(""" Are you sure that's the result of an identify -verbose <imagePath>
            imagemagick command?""")
        '''Analyses the results of the imageMagick command:
        identify -verbose (screenshot) to store imageFeatures. Definitions and
        justification for scraping these features can be found in the research at
        https://github.com/xanmankey/FishingForPhish/tree/main/research'''
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
            logging.warning("Hashing without database functionality; previous hashing is not stored unless done manually")
            hashes = {}
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
            hashes.update({"phash":pHash})
            hashes.update({"dhash":dHash})
            self.hashes.append(hashes)
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
                (pHash, dHash, url))

    def analyze(self, url, filename, resources, urlNum):
        '''Searches through the html of a url to get the specified image-features.
        These features are defined in the research paper at
        https://github.com/xanmankey/FishingForPhish/tree/main/research and broken down
        into the categories: layout, style, and other.'''
        features = {}
        totalTags = resources["BS"].find_all()
        selTotalTags = resources["driver"].find_elements(By.XPATH, "//*")
        linkTags = resources["driver"].find_elements(By.TAG_NAME, "link")

        if self.HASH:
            # Optionally, update the hashes table if database functionality is enabled
            self.imageHash(url, filename)

        # LAYOUT
        # Get the total number of tags DIRECTLY in the HTML tag using Beautiful
        # Soup
        htmlTag = resources["BS"].find('html')
        inHTML = 0
        for tag in htmlTag:
            inHTML += 1
        features.update({"numTagsInHtml":inHTML})

        # Get the total number of tags in the head tag using Beautiful Soup
        headTag = resources["BS"].find('head')
        inHead = 0
        if headTag:
            headChildren = headTag.findChildren()
            for tag in headChildren:
                inHead += 1
        features.update({"numTagsInHead":inHead})

        # Get the total number of tags in the main tag using Beautiful Soup
        mainTag = resources["BS"].find('main')
        inMain = 0
        if mainTag:
            mainChildren = mainTag.findChildren()
            for tag in mainChildren:
                inMain += 1
        features.update({"numTagsInMain":inMain})

        # Get the total number of tags in the body tag using Beautiful Soup
        bodyTag = resources["BS"].find('body')
        inBody = 0
        if bodyTag:
            bodyChildren = bodyTag.findChildren()
            for tag in bodyChildren:
                inBody += 1
        features.update({"numTagsInBody":inBody})

        # Get the percentage of img tags
        imgTags = resources["driver"].find_elements(By.TAG_NAME, "img")
        pctImgTags = len(imgTags) / len(totalTags)
        features.update({"pctImgTags":pctImgTags})

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
        if len(occurences) > 0:
            fontStyle = occurences.most_common(1)[0][0]
        else:
            fontStyle = Instance.missing_value()
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
                overlapping = 1a
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
                analyzerNames.append(analyzer.name())
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
                logging.warning("""Sorry, you can't select attributes if there aren't enough class labels (requires > 0) """)
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
            dataset = self.datasets[analyzer.name()]
            class1 = 0
            class2 = 0
            for instance in dataset:
                index = instance.class_index
                classVal = instance.get_value(index)
                if not isnan(classVal):
                    if int(classVal) == 0:
                        class1 += 1
                    elif int(classVal) == 1:
                        class2 += 1
            if class1 != 0 and class2 != 0:
                if class1 < class2:
                    try:
                        ratio = (class2 / class1) * 100
                    except ZeroDivisionError:
                        ratio = 100
                    classVal = "0"
                elif class2 < class1:
                    try:
                        ratio = (class1 / class2) * 100
                    except ZeroDivisionError:
                        ratio = 100
                    classVal = "1"
                else:
                    logging.warning("The classes are already balanced, no need to oversample")
                    return
            else:
                logging.warning("Can't oversample using nearest neighbors if there are no nearest neighbors")
                return
            smote = Filter(
                classname="weka.filters.supervised.instance.SMOTE", options=[
                    "-C", classVal, "-P", str(ratio)])
            smote.inputformat(dataset)
            newInstances = smote.filter(dataset)
            for instance in newInstances:
                dataset.add_instance(instance)
            dataset.sort(index)
            self.datasets.update({analyzer.name() + "Balanced":dataset})

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
                        if int(classVal) == 0:
                            class1 += 1
                        elif int(classVal) == 1:
                            class2 += 1
                    if class1 != 0 and class2 != 0:
                        if class1 < class2:
                            try:
                                ratio = (class2 / class1) * 100
                            except ZeroDivisionError:
                                ratio = 100
                            classVal = "0"
                        elif class2 < class1:
                            try:
                                ratio = (class1 / class2) * 100
                            except ZeroDivisionError:
                                ratio = 100
                            classVal = "1"
                        else:
                            logging.warning("The classes are already balanced, no need to oversample")
                            return
                    else:
                        logging.warning("Can't oversample using nearest neighbors if there are no nearest neighbors")
                        return
                    smote = Filter(
                        classname="weka.filters.supervised.instance.SMOTE", options=[
                            "-C", classVal, "-P", str(ratio)])
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
            print(datasetName)
            datasetSaver.save_file(
                dataset,
                self.dataDir +
                '/datasets/' + datasetName + "Dataset" + ".arff")
        jvm.stop()

    # Returns a list of all the dataset attributes
    def attributeCreation(self, featureNames, class1="legit", class2="phish"):
        '''A convenience function to create the attributes
        for a specific dataset based off of the featureName
        class attributes.'''
        atts = []
        for key, value in featureNames.items():
            if value == "numeric":
                att = Attribute.create_numeric(key)
            elif value == "nominal" and key == "classVal":
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
            if self.datasets[analyzer.name()]:
                dataset = self.datasets[analyzer.name()]
                dataset.class_is_last()
                for classifierName, classifier in classifiers.items():
                    try:
                        classifier.build_classifier(dataset)
                        # The graphs generated can be varied if you so choose; I just decided to graph after
                        # first building the classifier
                        if self.graph:
                            graph.plot_dot_graph(classifier.graph, self.dataDir + "/graph/" + analyzer.name() + "Graph.png")
                        for instance in dataset:
                            classifications.append(classifier.classify_instance(instance))
                    except Exception:
                        logging.warning("Error using the " + classifierName + " classifier")
                        classifications.append(Instance.missing_value())
                        continue
                if len(classifications) != 0:
                    counting = Counter(classifications)
                    prediction = str(counting.most_common(1)[0][0]) + ":" + str(counting.most_common(2)[0][0])
                    classification = counting.most_common(1)[0][0]
                    self.classifications.update({analyzer.name():classification})
                    self.score.update({analyzer.name():prediction})
                    if self.database:
                        for num in range(self.urlNum):
                            classification = [classifications[0], classifications[num], classifications[num * 2]]
                            counting = Counter(classification)
                            classification = counting.most_common(1)[0][0]
                            self.cursor.execute(
                                "UPDATE metadata SET classification = ? WHERE id = ?",
                                (classification,), (num,))
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
                                    graph.plot_dot_graph(classifier.graph, self.dataDir + "/graph/" + name + "Graph.png")
                                for instance in dataset:
                                    classifications.append(classifier.classify_instance(instance))
                            except Exception:
                                logging.warning("Error using the " + classifierName + " classifier")
                                continue
                        if len(classifications) != 0:
                            counting = Counter(classifications)
                            prediction = str(counting.most_common(1)[0][0]) + ": " + str(counting.most_common(2)[0][0])
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
            if analyzer.name() in self.datasets.keys():
                dataset = self.datasets[analyzer.name()]
            else:
                dataset = Instances.create_instances(
                    analyzer.name() + "Dataset", [att for att in datasetAtts], 0)
            for instance in analyzer.features:
                values = []
                attNum = 0
                for value in instance.values():
                    if type(value) == type('string'):
                        values.append(datasetAtts[attNum].add_string_value(value))
                    elif type(value) == type(1) or type(value) == type(1.0):
                        float(value)
                        values.append(value)
                    elif not value:
                        values.append(Instance.missing_value())
                    attNum += 1
                inst = Instance.create_instance(values)
                dataset.add_instance(inst)
            stringToNom.inputformat(dataset)
            dataset = stringToNom.filter(dataset)
            if analyzer.name() not in self.datasets.keys():
                self.datasets.update({analyzer.name():dataset})

        if self.newDatasetOptions["ranked"]:
            # Where self.FS returns a dictionary of lists of attributes (if multiple datasets)
            # Keep in mind that datasets cannot SHARE the same attributes
            # You can create new ones based off of current ones in use for another dataset however
            attributes = self.FS()
            if not attributes:
                self.newDatasetOptions["ranked"] = False
            if self.newDatasetOptions["ranked"]:
                attributeNames = []
                for dataset in attributes:
                    for attribute in dataset:
                        attributeNames.append(attribute.name)
                atts = []
                if len(attributes) != 0:
                    for dataset in attributes:
                        for attribute in dataset:
                            if attribute.name in attributeNames:
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
                                if type(value) == type('string'):
                                    values.append(datasetAtts[attNum].add_string_value(value))
                                elif type(value) == type(1) or type(value) == type(1.0):
                                    float(value)
                                    values.append(value)
                                elif not value:
                                    values.append(Instance.missing_value())
                            valueNum += 1
                        inst = Instance.create_instance(values)
                        rankedDataset.add_instance(inst)
                stringToNom.inputformat(rankedDataset)
                rankedDataset = stringToNom.filter(rankedDataset)
                if "ranked" not in self.datasets.keys():
                    self.datasets.update({"ranked":rankedDataset})

        if self.newDatasetOptions["full"]:
            atts = [att for att in self.attributeCreation(self.allFeatureNames)]
            if "full" in self.datasets.keys():
                fullDataset = self.datasets["full"]
            else:
                fullDataset = Instances.create_instances(
                    "fullDataset", [att for att in atts], 0)
            for instance in self.allFeatures:
                values = []
                attNum = 0
                for value in instance.values():
                    if type(value) == type('string'):
                        values.append(atts[attNum].add_string_value(value))
                    elif type(value) == type(1) or type(value) == type(1.0):
                        float(value)
                        values.append(value)
                    elif not value:
                        values.append(Instance.missing_value())
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
    # Currently testing w/ switched classVal (on analyzers)
    # and database func.
    # Initialization
    run = startFishing()
    run.initializeAll()

    fisher = scrape(
        urlFile="data/urls.txt",
        dataDir="data",
        database="data/data.db",
        driver=run.driver,
    )

    # Initialization of the page analyzer
    pageData = pageAnalyzer(classVal=0)
    fisher.addAnalyzer(pageData)

    # Initialization of the image analyzer
    imageData = imageAnalyzer(classVal=0)
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
    DC = saveFish(
        urlFile="data/urls.txt",
        dataDir="data",
        driver=run.driver,
        analyzers=fisher.analyzers,
        allFeatures=fisher.allFeatures,
        allFeatureNames=fisher.allFeatureNames
    )
    DC.createDatasets()
    DC.classify()
    print(DC.score)
    print(DC.classifications)

    DC.closePWW3()
    DC.closeSelenium()


if __name__ == "__main__":
    main()
