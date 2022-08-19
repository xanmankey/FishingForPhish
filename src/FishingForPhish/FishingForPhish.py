# FishingForPhish.py: contains the major classes, functions, and objects
# I used throughout this research

## Using double comments to indicate refactoring notes and plans
## My first goal is to reimplement my code using scikit-learn
## (no drastic refactoring changes). Then, I plan on looking into optimization and edge cases.
## The goal is to get a stable release and easily usable API that I can use for my release of PhishAI
## I also need an alternative for graphing and data visualization (matplotlib?)
## I also want to branch the analyzers out into their own files without any dependency issues

# For scraping
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions

# scikit-learn
from sklearn import feature_selection
# Not sure if you can create datasets using sklearn (I might want to load them instead)
# I think maybe I'll use pandas instead
import pandas as pd
import numpy as np
# for graphing
from matplotlib import pyplot as plt
from matplotlib import style
# utility libs
import time
import pyshorteners
from overrides import overrides, EnforceOverides, final
from unshortenit import UnshortenIt
from bs4 import BeautifulSoup
from collections import Counter
import requests
from requests.exceptions import RequestException
import os
import sys
from filetype import is_image
## Replaced sqlite3 with postgres (the PyPi module is well-abstracted anyway)
from postgres import Postgres
import cssutils
import logging
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning
import validators
import operator
import urllib
from urllib.parse import urlparse
import socket
from socket import timeout
import tldextract
from IPy import IP
import subprocess
from PIL import Image
import imagehash
import copy
from math import isnan
# Importing analyzers (circular dependency?)
from .newImage import ImageAnalyzer
from .newPage import PageAnalyzer


## The SuperClass method
class startFishing():
    '''A class for initializing Selenium, Beautiful Soup, and the project filesystem'''

    def __init__(self, dataDir="data", driver=None, addons=['https://addons.mozilla.org/firefox/downloads/file/3911106/wayback_machine-3.0-fx.xpi'], **kwargs):
        '''Defines the dataDir, driver, and BS attributes, where dataDir is the home directory
        containing a screenshots directory for screenshots, an html directory for html,
        a css directory for css, and a datasets directory for datasets, and the driver and
        BS attributes store the current state of the Selenium Webdriver and Beautiful Soup
        objects respectively'''
        super().__init__(**kwargs)
        self.dataDir = dataDir
        self.addonDir = dataDir + '/addons'
        # Add more
        self.addonUrls = addons
        self.driver = driver
        self.initializeDirectories()

    def initializeDirectories(self):
        '''A class method for initializing the directories and data.
        '''
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
        '''Install Selenium Firefox addons. If the addons have already been downloaded
        and written, there is no need to call this function again.'''
        for url in self.addonUrls:
            try:
                addon = requests.get(
                    url,
                    allow_redirects=True)
            except requests.exceptions.RequestException as e:
                logging.warning("Installing addon failed; are you sure {url} is the correct url?")
            # note that rsplit splits a string from the back
            open(
                self.addonDir +
                url.rsplit('/', 1)[1],
                'wb').write(
                addon.content)
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

    def initializeSelenium(self, addons=True):
        '''Initializes Selenium with any add_ons that are passed to the method'''
        options = FirefoxOptions()
        options.add_argument("--headless")
        options.add_argument('--hide-scrollbars')
        options.add_argument('--disable-gpu')
        # In terms of security, a VPN and a VM is recommended
        # (but not necessary; Selenium + Firefox handles private browsing by default)
        # Additionally, cookies, session, and cache data are disabled
        # using Firefox preferences (found below)
        # http://kb.mozillazine.org/index.php?title=Category:Preferences&until=Places.frecency.unvisitedTypedBonus
        # Javascript is necessary for dynamic websites, but can be
        # disabled by uncommenting the below preference
        # options.set_preference("javascript.enabled", False)
        options.set_preference("network.cookie.cookieBehavior", 2)
        options.set_preference("Browser.sessionstore.privacy", 2)
        options.set_preference("Browser.cache.disk.enable", False)
        options.set_preference("browser.privatebrowsing.autostart", True)
        driver = webdriver.Firefox(options=options)
        if addons:
            for addon in os.listdir(self.addonDir):
                if addon[len(addon) - 4:len(addon)].upper() == ".XPI":
                    try:
                        driver.install_addon(os.path.abspath(self.dataDir + addon), temporary=True)
                        logging.info(addon + "was added on!")
                    except Exception:
                        logging.warning(" " + self.addonDir + addon + " is not a valid Firefox addon!")
                        continue
        self.driver = driver
        self.driver.implicitly_wait(20)

    # ## Alter this to work with scikit-learn or tensorflow
    # ## I don't believe scikitLearn requires any initialization (unlike the JVM)
    # def initializePWW3(self, jvmOptions):
    #     '''Starts jvm using a list of optional parameters'''
    #     if self.jvmToggle:
    #         logging.warning(""" Have you already started the jvm? Remember that you can't
    #         stop and then start it again mid-execution!""")
    #         return
    #     jvm.start(option for option in jvmOptions)
    #     self.jvmToggle = True

    ## I'll need to slightly alter this method (as is the case for a lot of the methods)
    def initializeAll(self):
        '''A joint method that calls all the initialize methods (except for initializeBS). Packages
        are enabled, related resources are installed, and excessive warnings are limited.'''
        # Not sure about scikit-learn options yet
        # options = [option for option in jvmOptions]
        requests.packages.urllib3.disable_warnings(
            category=InsecureRequestWarning)
        cssutils.log.setLevel(logging.CRITICAL)
        # if "packages" not in options:
        #     logging.warning(" Are you sure you want to run jvm without package support?")
        # self.initializePWW3(options)
        self.installResources()
        options = [addon for addon in os.listdir(self.addonDir)]
        self.initializeSelenium(options)


## The analyzer base class
class Analyzer(EnforceOverrides):
    '''A base class for adding analyzers to analyze scraped values which can be called during the url
    processing step (the goFish method). See the analyze shell function for more information.
    I'm still working on finding a way to make this class more inheritable and
    easier to work with.'''

    # shell function (override is required)
    def __init__(self):
        '''There are currently no inheritable attributes, largely because of my lack of
        knowledge regarding class inheritance (the attributes ended up overwriting one another).
        However, when creating an instance of the analyzer class, there are a couple REQUIRED
        attributes: features (an array of features, a dict in name:featureValue format),
        featureNames (a dict in featureName:wekaDatatype format, see the docs at
        https://fishingforphish.readthedocs.io/ for more info), and classVal. And of course,
        if you are making your own analyzer,
        you can create attributes of your own, just make sure to consider them in regards to
        the goFish method, especially in consideration of the resources dictionary'''
        raise NotImplementedError

    ## Changed to a classmethod
    @classmethod
    @final
    def name(cls):
        '''Returns the class name (used for table and dataset names respectively)'''
        return cls.__name__

    # Shell function (override is required)
    def analyze(self):
        # Your analysis code here
        # Every class inheriting from the analyzer class
        # Has a different analyze method
        # These classes are not standalone
        # But can function with a self.addAnalyzer(analyzer)
        # and self.goFish() call from the scrape class
        raise NotImplementedError

class Selector():
    def __init__(self):
        """A class with default feature selection methods,
        as well as a custom feature selection method that can be overriden."""

    def InfoGain(self):

    def Correlational(self):

    def ChiSquared(self):

    def FS(self):

class Classifier():
    def __init__(self):
        """A class with default classification methods,
        as well as a custom classification method that can be overriden."""

    def NaiveBayes(self):

    def J48(self):

    def JRIP(self):

    def Classify(self):

# The scrape class; inherits from the startFishing initialization class.
# Provides many useful scraping methods and initializes file system and variables
# This class IS NOT inherited from due to the dynamic nature of scraping variables;
# rather the variables are passed as arguments into the analyzers
# and the analyzers return the respective features and feature names
# which are then used in the data class which inherits from the scrape class

## The scrape class doesn't need to be refactored (except for optimization and edge cases)
## I would like to try and cut tinyurl functionality however and have a seperate table of urls
## I also might want to replace the dataset functionality with something a little similar
## (namely, pandas functionality, and then write pandas to a database later)
## A subclass of startFishing; inherits initialization params
class scrape(startFishing):
    '''A class (inheriting from initialize) that defines useful scrape objects and methods'''

    def __init__(
            self,
            urlFile,
            database=None,
            screenshotDir=None,
            htmlDir=None,
            cssDir=None,
            # dataframe=None,
            # numpyArray=None,
            urlNum=1,
            id=1,
            classVal=Instance.missing_value(),
            allErrors=[],
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
        self.urlNum = urlNum
        ## Still need to find a way to have analyzers as an attribute, rather than a global variable
        self.screenshotDir = screenshotDir
        self.htmlDir = htmlDir
        self.cssDir = cssDir
        # For turning off database functionality
        self.database = database
        # A dictionary of lists, eventually appending to a database (if desired)
        self.db = None
        self.classVal = classVal
        ## Note that id is = 1 because id INTEGER PRIMARY KEY defaults to 1 in sqlite3 databases
        self.id = id
        self.BS = None
        self.analyzers = []
        self.errors = []
        self.allErrors = allErrors
        self.data = {}
        ## TODO: I'm working on restructuring this __init__ method
        ## Having allFeatures and allFeatureNames bugs me a bit
        # self.shortener = pyshorteners.Shortener()
        # self.unshortener = UnshortenIt()
        self.allFeatures = allFeatures
        self.allFeatureNames = allFeatureNames
        if not os.path.isfile(self.urlFile):
            raise FileNotFoundError(
                """urlFile needs to be a path to a file with urls!""")
        else:
            with open(self.urlFile, "r") as f:
                numUrls = 0
                for line in f:
                    url = line.strip()
                    if not validators.url(url):
                        raise ValueError(
                            """Sorry, are you sure urlFile contains valid urls?""")
                numUrls += 1
            # pre-allocate memory for a numpy array?

        # INFO: I haven't had the time to test running the program with a standalone
        # screenshotDir, cssDir, or htmlDir as of right now
        if self.screenshotDir:
            if not os.path.isdir(self.screenshotDir):
                raise FileNotFoundError(
                    """screenshotDir needs to be a path to a directory with screenshots!""")
            # Empty lists are considered false
            if not all(lambda file: file for file in os.listdir(self.screenshotDir) if is_image(file) else False):
                raise ValueError(
                    """Are you sure all the files in your screenshot directory are images?""")
        if self.htmlDir:
            if os.path.isdir(self.htmlDir):
                if not all(lambda file: file for file in os.listdir(self.htmlDir) if file[len(file) -
                    5:len(file)].upper() == ".HTML" else False):
                    raise ValueError(
                        """Are you sure the files in htmlDir are all .html files?""")
        # Technically, the css files are never actually used,
        # but it's still important to have them for future research
        if self.cssDir:
            if os.path.isdir(self.cssDir):
                if not all(lambda file: file for file in os.listdir(self.cssDir) if file[len(file) -
                    4:len(file)].upper() == ".CSS" else False):
                        raise ValueError(
                            """Are you sure the files in cssDir are all .css files?""")
        ## I think I'm going to need to keep database functionality around
        ## In order to preserve resuming functionality (I'm just not going to write every time)
        # Initializing database (pre-existing or not) if desired
        if self.database:
            ## It's a HORRIBLE idea to append to a numpy array or a pandas dataframe
            ## Converted databases to pandas dataframes
            # Consistent db table names
            tables = {
                "metadata": """CREATE TABLE metadata (id INTEGER PRIMARY KEY,
                url TEXT UNIQUE, UTCtime INT, classification TEXT)""",
                # note that 2000 is the de-facto standard for urls (so any urls longer than 2000 will be refused)
                "errors": """CREATE TABLE errors (url VARCHAR(2000) UNIQUE, error TEXT)""",
                "hashes": """CREATE TABLE hashes (phash TEXT, dhash TEXT, url TEXT)"""
            }
            if os.path.isfile(self.database):
                try:
                    self.db = Postgres(self.database)
                except Exception:
                    raise FileNotFoundError(
                        """Sorry, can't connect to database {self.database}""")
                # With postgres, use one to return one value, all to return all values, and run
                # to not return anything
                currentTables = self.db.all("SELECT * FROM information_schema.tables")
                # currentTables = [item for table in currentTables for item in table]
                logging.info("current db tables" + str(currentTables))
                for tableName, creation in tables.items():
                    if tableName in currentTables:
                        continue
                    else:
                        # execute is an alias for run
                        # self.db refers to the data
                        self.db.execute(creation)
                ## Not sure if committing is necessary with postgres
                # self.conn.commit()
            else:
                open(self.dataDir + "/data.db", "w").close()
                self.db = Postgres(self.dataDir + "/data.db")
                # self.conn = sqlite3.connect(self.database)
                # self.conn.row_factory = sqlite3.Row
                # self.cursor = self.conn.cursor()
                for creation in tables.values():
                    self.db.execute(creation)
                # self.conn.commit()

    def preallocate(length):
        '''Preallocate memory for a numpy array and pandas dataframe.
        Data will eventually be written to storage, but it's a lot faster
        to work in memory and THEN write to storage after the fact.
        '''
        # self.numpyArray = np.empty(length)
        # I need to figure out how to handle data (numpy, pandas, ect)

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
            logging.warning(" Couldn't initialize due to " + str(e) + ". Are you sure you inputted valid html?")

    # When an analyzer is to be added
    # The addAnalyzer function should be called
    # With an instance of the analyzer itself
    def addAnalyzer(self, analyzer):
        '''A function that takes the name of an analyzer passed to it, and adds it
        to the self.analyzers array, which is then used
        to collect data accordingly throughout (tables, dataset, attributes)'''
        logging.info(str(analyzer.name()) + " added!")
        self.analyzers.append(analyzer)
        # A table is created for each added analyzer in this function
        columns = []
        if self.database:
            # self.cursor.execute("SELECT name FROM sqlite_master WHERE TYPE='table'")
            currentTables = self.db.all("SELECT * FROM information_schema.tables")
            if analyzer.name() not in currentTables:
                for name, datatype in analyzer.featureNames.items():
                    # The 3 datatypes I ended up working with are below
                    if datatype.lower() == "numeric":
                        columns.append(name + " FLOAT")
                    elif datatype.lower() == "string":
                        columns.append(name + " TEXT")
                    elif datatype.lower() == "nominal":
                        columns.append(name + " BOOLEAN")
                self.db.execute("CREATE TABLE {} (id INTEGER PRIMARY KEY, {})".format(
                    analyzer.name(), ",".join(name for name in columns)))

    # def shorten(self, url, validate=False):
    #     '''Shortens the url using pyshorteners and the clckru shortener. Unique characters are
    #     generated at the end of the url which are then used to rename the file, and once the id in
    #     front of the filename is removed, https://tinyurl.com/" can be added back to the url and combined
    #     with the expand() method below to get the original url from a filename'''
    #     if not validate:
    #         if not validators.url(url):
    #             raise ValueError("Invalid url: " + url)
    #     try:
    #         shortUrl = self.shortener.tinyurl.short(url)
    #     except Exception as e:
    #         self.errors.append(e)
    #         return False
    #     print("shortUrl: " + str(shortUrl))
    #     return shortUrl

    # def expand(self, urlID):
    #     '''Expands a filename into the url associated with the file using pyshorteners and clck.ru.
    #     Explained more in the shorten() function above'''
    #     filename = "https://tinyurl.com/" + urlID
    #     filename = filename.replace("_" + str(self.id) + "_", "")
    #     try:
    #         url = self.unshortener.unshorten(filename)
    #         print("unshortenedUrl: " + url)
    #     except Exception as e:
    #         print(str(e))
    #         logging.warning("Could not expand the url!")
    #         self.errors.append(e)
    #         return False
    #     return url

    # def generateFilename(self, url):
    #     '''A convenience method for generating a filename to name files associated with a website.
    #     Follow the naming conventions of "_<self.id>_<final 5 characters of shortened url>.png".'''
    #     shortUrl = self.shorten(url)
    #     if not shortUrl:
    #         return False
    #     filename = shortUrl.replace("https://tinyurl.com/", "")
    #     filename = "_" + str(self.id) + "_" + filename
    #     return filename

    def siteValidation(self, url, validated=False):
        '''Method that attempts to validate a site, specifically checking if Selenium can
        access the website, the website's url, and if the requests library does not return a
        404 error (which is often the case due to the slippery nature of phishing websites)'''
        if len(url) > 2000:
            return False
        if not validated:
            try:
                self.driver.get(url)
            except Exception as e:
                self.errors.append(e)
                return False
            try:
                url = self.driver.current_url
            except Exception:
                # time.sleep(10)
                try:
                    url = self.driver.current_url
                except Exception as e:
                    self.errors.append(e)
                    return False
            try:
                r = requests.head(url, verify=False, timeout=5)
                if r.status_code >= 400:
                    self.errors.append(r.status_code)
                    return False
            except Exception as e:
                self.errors.append(e)
                return False
        return True

    def saveScreenshot(self, url, filename, validated=False):
        '''Method for saving a screenshot of the full website. Scrolls the page (if possible) to get
        the height and width of a website. A minimum height and width of 10000 (unlikely to ever
        be hit unless intentional) are set to help prevent Selenium crashing.
        The screenshot is saved at dataDir/screenshots/filename.png (see the generate filename
        method above for more information regarding filenames)'''
        if not validated:
            if not self.siteValidation(url):
                logging.warning("Could not take a screenshot of " + url + " due to " + str(self.errors[0]))
                return
        screenshot = False
        try:
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
            screenshot = True
            return True
        except Exception as e:
            self.errors.append(e)
            if screenshot:
                os.remove(self.dataDir + "/screenshots/" + filename + ".png")
            return False

    def getTime(self):
        '''Generates a time value (uses Coordinated Universal Time, or UTC)'''
        time = datetime.now().strftime("%H:%M:%S")
        return time

    def exitHandler(self, exctype, value, traceback):
        '''Exit the code correctly on an exception and adapt databases
        accordingly (if enabled)'''
        if self.database:
            self.db.execute("SELECT id FROM metadata")
            numMetadata = len(self.cursor.fetchall())
            self.db.execute("SELECT id FROM allData")
            numAllData = len(self.cursor.fetchall())
            if numMetadata != numAllData:
                for i in range(numMetadata - numAllData):
                    self.db.execute("DELETE FROM metadata ORDER BY id DESC LIMIT 1")
                # self.conn.commit()
            if len(self.allFeatures) == 0 or len(self.allFeatureNames) == 0:
                try:
                    self.driver.close()
                    self.driver.quit()
                except Exception:
                    pass
            else:
                closing = saveFish(urlFile="data/urls.txt",
                        dataDir="data",
                        driver=self.driver,
                        analyzers=self.analyzers,
                        allFeatures=self.allFeatures,
                        allFeatureNames=self.allFeatureNames)
                closing.closeSelenium()
                closing.closePWW3()
            sys.__excepthook__(exctype, value, traceback)
        else:
            if len(self.allFeatures) == 0 or len(self.allFeatureNames) == 0:
                try:
                    self.driver.close()
                    self.driver.quit()
                except Exception:
                    pass
            else:
                closing = saveFish(urlFile="data/urls.txt",
                        dataDir="data",
                        driver=self.driver,
                        analyzers=self.analyzers,
                        allFeatures=self.allFeatures,
                        allFeatureNames=self.allFeatureNames)
                closing.closeSelenium()
                closing.closePWW3(save=False)
            sys.__excepthook__(exctype, value, traceback)

    def resume(self, id=False):
        '''A function to resume the program if it crashes and you were storing data
        in a database. Called before calling goFish, initializes attributes with the
        previously scraped information from the previous session. Note that
        your urlFile, self.id, and self.urlNum will need to be updated to where you left off.'''
        # If the program crashed, pick up where you left off (if database functionality was and is still enabled)
        # Note that self.allFeatureNames will autogenerate later on and doesn't need to be initialized upon rerunning
        # And remember that database functionality assumes that the featureNames are the same as the columnNames (analyzer.featureNames)
        # and are still in the same order
        if self.database:
            if not id:
                classToggle = 0
                ## TODO: I need to re-examine this function (and a lot of functions in this class)
                ## In the context of refactoring; I want a lot of this to be semi-standalone and simple
                ## (but this class seems fairly complex; I'm asking myself "why did I do this again"?
                ## As the person who wrote this code, I shouldn't have to be doing that)
                for analyzer in self.analyzers:
                    for name, datatype in analyzer.featureNames.items():
                        if name == "classVal" and classToggle == 0:
                            classToggle += 1
                            continue
                        self.allFeatureNames.update({name:datatype})
                    features = self.db.all("SELECT * FROM {}".format(analyzer.name()))
                    for instance in features:
                        featureNum = 0
                        values = {}
                        for name, value in dict(instance).items():
                            if featureNum == 0:
                                featureNum += 1
                                continue
                            values.update({name:value})
                        analyzer.features.append(values)
                allFeatures = self.db.all("SELECT * FROM allData")
                for instance in allFeatures:
                    featureNum = 0
                    features = {}
                    for name, value in dict(instance).items():
                        if featureNum == 0:
                            featureNum += 1
                            continue
                        features.update({name:value})
                    self.allFeatures.append(features)
                allErrors = self.db.all("SELECT error FROM errors")
                for instance in allErrors:
                    for name, errors in dict(instance).items():
                        if name == "error":
                            error = errors.split(", ")
                            for exception in error:
                                self.allErrors.append(exception)
            elif type(id) == int:
                # Used if the values are already in the database
                # To update the runtime values with the database values
                for analyzer in self.analyzers:
                    features = self.db.execute("SELECT * FROM {} WHERE id = ?".format(analyzer.name()), id)
                    for instance in features:
                        featureNum = 0
                        values = {}
                        for name, value in dict(instance).items():
                            if featureNum == 0:
                                featureNum += 1
                                continue
                            values.update({name:value})
                        analyzer.features.append(values)
                allFeatures = self.db.execute("SELECT * FROM allData WHERE id = ?", id)
                for instance in allFeatures:
                    featureNum = 0
                    features = {}
                    for name, value in dict(instance).items():
                        if featureNum == 0:
                            featureNum += 1
                            continue
                        features.update({name:value})
                    self.allFeatures.append(features)
                errors = self.db.execute("SELECT error FROM errors INNER JOIN metadata ON metadata.url = errors.url")
                for error in errors.values():
                    error = error.split(", ")
                for exception in error:
                    self.allErrors.append(exception)

    def checkInternet(self, validated=False):
        '''A function that can optionally be called upon a failed validation to
        ensure the program exits upon failure to send a request to google.com. Saves
        computational power and time alike.'''
        if not validated:
            try:
                self.driver.get("https://www.google.com")
            except Exception as e:
                raise SystemError(e)
        return

    def goFish(self):
        '''Automates the scraping process by reading from the url file, validating the url,
        taking a screenshot (if necessary), saving html and css (if necessary), and then generating
        features by using Selenium and Beautiful Soup analysis using created analyzers'''
        if not self.driver:
            raise ReferenceError("Cannot scrape without a valid driver instance")
        # Create the allData table
        if self.database:
            currentTables = self.db.all("SELECT * FROM information_schema.tables")
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
                self.db.execute("CREATE TABLE allData (id INTEGER PRIMARY KEY, {})".format(
                    ",".join(name for name in featureNames)))
        with open(self.urlFile, "r") as f:
            for line in f:
                self.errors = []
                print("url: " + str(line))
                initialTime = datetime.now()
                print("initialTime: " + str(initialTime - initialTime))
                features = {}
                url = line.strip()
                if not self.siteValidation(url):
                    if self.database:
                        try:
                            self.db.execute(
                                "INSERT INTO errors (url, error) VALUES (?, ?)",
                                (url, ", ".join(str(error) for error in self.errors)))
                        except Exception:
                            pass
                    self.checkInternet()
                    self.urlNum += 1
                    self.allErrors.append(self.errors)
                    continue
                print("validationTime: " + str(datetime.now() - initialTime))
                url = self.driver.current_url
                filename = self.generateFilename(url)
                if not filename:
                    if self.database:
                        try:
                            self.db.execute(
                                "INSERT INTO errors (url, error) VALUES (?, ?)",
                                (url, ", ".join(str(error) for error in self.errors)))
                        except Exception:
                            pass
                    self.urlNum += 1
                    continue
                urlID = filename.replace("https://tinyurl.com/", "")
                urlID = urlID.replace("_" + str(self.id) + "_", "")
                if not self.expand(urlID):
                    if self.database:
                        try:
                            self.db.execute(
                                "INSERT INTO errors (url, error) VALUES (?, ?)",
                                (url, ", ".join(str(error) for error in self.errors)))
                        except Exception:
                            pass
                    self.urlNum += 1
                    self.allErrors.append(self.errors)
                    continue
                if not self.screenshotDir:
                    if self.database:
                        try:
                            time = self.getTime()
                            self.db.execute(
                                "INSERT INTO metadata (url, UTCtime, classification) VALUES (?, ?, ?)",
                                (url, time, self.classVal))
                        except Exception as e:
                            # In case the url is already in the database, just continuing with the
                            # main event loop
                            # Code is commented out for ensuring adding the database values
                            # to the current attribute values
                            # self.errors.append(e)
                            # self.cursor.execute(
                            #     "SELECT id FROM metadata WHERE url = ?", url)
                            # id = dict(self.cursor.fetchall())
                            # id = id.items()['id']
                            logging.warning(url + " is already in the database, skipping another screenshot")
                            # self.resume(id=id)
                            self.urlNum += 1
                            # self.allErrors.append(self.errors)
                            # self.cursor.execute(
                            #     "INSERT INTO errors (url, error) VALUES (?, ?)",
                            #     (url, ", ".join(str(error) for error in self.errors)))
                            # self.conn.commit()
                            continue
                    if not self.saveScreenshot(url, filename, validated=True):
                        if self.database:
                            try:
                                self.db.execute(
                                    "INSERT INTO errors (url, error) VALUES (?, ?)",
                                    (url, ", ".join(str(error) for error in self.errors)))
                            except Exception:
                                pass
                            self.db.execute("DELETE FROM metadata ORDER BY id DESC LIMIT 1")
                        self.urlNum += 1
                        self.allErrors.append(self.errors)
                        continue
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
                        try:
                            css = tag.get_attribute("rel")
                            if css == "stylesheet":
                                cssFile = tag.get_attribute("href")
                                sheet = cssutils.parseUrl(cssFile)
                                break
                        except Exception:
                            continue
                    if not os.path.isfile(
                            self.dataDir + "/css/" + filename + ".css"):
                        with open(self.dataDir + "/css/" + filename + ".css", "w") as f:
                            try:
                                f.write(sheet.cssText.decode())
                            except Exception as e:
                                # I'm skipping the url on failure to get the css
                                # But alternatively you can just pass out of this exception
                                # pass
                                self.errors.append(e)
                                if self.database:
                                    try:
                                        self.db.execute(
                                            "INSERT INTO errors (url, error) VALUES (?, ?)",
                                            (url, ", ".join(str(error) for error in self.errors)))
                                    except Exception:
                                        pass
                                    self.db.execute("DELETE FROM metadata ORDER BY id DESC LIMIT 1")
                                try:
                                    os.remove(self.dataDir + "/screenshots/" + filename + ".png")
                                except FileNotFoundError:
                                    pass
                                try:
                                    os.remove(self.dataDir + "/html/" + filename + ".html")
                                except FileNotFoundError:
                                    pass
                                try:
                                    os.remove(self.dataDir + "/css/" + filename + ".css")
                                except FileNotFoundError:
                                    pass
                                self.urlNum += 1
                                self.allErrors.append(self.errors)
                                continue
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
                    updatedResources = analyzer.analyze(url, filename, resources, self.urlNum)
                    print("analyzerTime: " + str(datetime.now() - initialTime))
                    for resource, value in updatedResources.items():
                        if resource in resources.keys():
                            if resource != "features" and resource != "featureNames":
                                # essentially updating the variable itself by updating the dict
                                resources[resource] = value
                            if resource == "features":
                                newFeatures = value
                            elif resource == "featureNames":
                                newFeatureNames = value
                            # Even though only classVal is updated in the analyzers
                            # It's important to update the state of some of the attributes
                            else:
                                self.classVal = value
                    if len(newFeatures.values()) != len(newFeatureNames.values()):
                        for analyzer in self.analyzers:
                            if len(analyzer.features) == len(self.allFeatures) + 1:
                                analyzer.features.pop()
                            if classCheck > 1:
                                for i in range(classCheck - 1):
                                    self.cursor.execute("DELETE FROM {} ORDER BY id DESC LIMIT 1".format(self.analyzers[i].name()))
                                # To avoid insertion into allData
                                classCheck = 0
                        if self.database:
                            self.errors.append('analyzerError')
                            try:
                                self.db.execute(
                                    "INSERT INTO errors (url, error) VALUES (?, ?)",
                                    (url, ", ".join(str(error) for error in self.errors)))
                            except Exception:
                                pass
                            self.db.execute("DELETE FROM metadata ORDER BY id DESC LIMIT 1")
                        self.allErrors.append(self.errors)
                        self.id -= 1
                        try:
                            os.remove(self.dataDir + "/screenshots/" + filename + ".png")
                        except FileNotFoundError:
                            pass
                        try:
                            os.remove(self.dataDir + "/html/" + filename + ".html")
                        except FileNotFoundError:
                            pass
                        try:
                            os.remove(self.dataDir + "/css/" + filename + ".css")
                        except FileNotFoundError:
                            pass
                        break
                    if classCheck != len(self.analyzers):
                        features = {key:val for key, val in newFeatures.items() if key != 'classVal'}
                        self.allFeatureNames = self.allFeatureNames | {key:val for key,val in newFeatureNames.items() if key != 'classVal'}
                    else:
                        features = features | newFeatures
                        if len(self.allFeatureNames) < len(features):
                            self.allFeatureNames = self.allFeatureNames | newFeatureNames
                    if self.database:
                        # newFeatures = {key:val for key, val in newFeatures.items() if key != 'classVal'}
                        # newFeatureNames = {key:val for key, val in newFeatureNames.items() if key != 'classVal'}
                        self.db.execute("""INSERT INTO {} ({}) VALUES ({})""".format(analyzer.name(),
                            ",".join(name for name in newFeatureNames.keys()),
                            ",".join("?" for i in range(len(newFeatureNames.keys())))),
                            [value for value in newFeatures.values()])
                    classCheck += 1
                if classCheck == len(self.analyzers) + 1:
                    if self.database:
                        self.db.execute("""INSERT INTO allData ({}) VALUES ({})""".format(
                            ",".join(name for name in self.allFeatureNames.keys()),
                            ",".join("?" for i in range(len(self.allFeatureNames.keys())))),
                    self.allFeatures.append(features)
                self.id += 1
                self.urlNum += 1

# The saveFish class is for interpreting the data from the scrape class
# in regards to machine learning
# The functions that need to be refactored in regards to this class are
# generateInstances():
# createDatasets():
# classify():
# After refactoring, I might also try to build some tests (if it makes sense to test my code)
# I'll build the tests off the examples

## This is the class that is going to need to get drastically refactored
## This is also the class I'm going to look at and optimize first

## A subclass of a subclass, directly inherits the attributes of scrape
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

    ## For FS and probably classification, I plan on keeping up with the @override functionality
    ## (to allow for maximum customization).
    ## Not sure how I want to group these yet though (maybe static methods of a selection class? Similar to analyzer)

    ## Feature selection with Scikit-learn?
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

    ## Oversampling with scikit-learn??
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
            newDataset = dataset
            for instance in newInstances:
                newDataset.add_instance(instance)
            newDataset.sort(index)
            self.datasets.update({analyzer.name() + "Balanced":newDataset})

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
                    newDataset = dataset
                    for instance in newInstances:
                        newDataset.add_instance(instance)
                    newDataset.sort(index)
                    self.datasets.update({"{}Balanced".format(option):newDataset})
                else:
                    continue

    ## Saving and safely closing w/ scikit-learn
    def closePWW3(self, save=True):
        '''A function that saves all the altered datasets in dataDir/datasets/(dataset) and
        closes jvm. There are 6 predefined arguments, each of which True, representing the
        datasets that you want to save.'''
        if save:
            datasetSaver = Saver(classname="weka.core.converters.ArffSaver")
            for datasetName, dataset in self.datasets.items():
                print(datasetName)
                datasetSaver.save_file(
                    dataset,
                    self.dataDir +
                    '/datasets/' + datasetName + "Dataset" + ".arff")
        jvm.stop()

    # Returns a list of all the dataset attributes
    ## Creating datasets with scikit-learn??
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
    ## Classification with scikit-learn??
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
                        logging.warning("Error using the " + str(classifierName) + " classifier")
                        classifications.append(Instance.missing_value())
                        continue
                if len(classifications) != 0:
                    counting = Counter(classifications)
                    prediction = str(counting.most_common(1)[0][0]) + ":" + str(counting.most_common(2)[0][0])
                    classification = str(counting.most_common(1)[0][0])
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
                                logging.warning("Error using the " + str(classifierName) + " classifier")
                                continue
                        if len(classifications) != 0:
                            counting = Counter(classifications)
                            prediction = str(counting.most_common(1)[0][0]) + ": " + str(counting.most_common(2)[0][0])
                            classification = str(counting.most_common(1)[0][0])
                            self.classifications.update({name:classification})
                            self.score.update({name:prediction})
                except Exception:
                    continue

    ## Again, creating datasets with scikit-learn??
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
            dataset.class_is_last()
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
                rankedDataset.class_is_last()
                print(rankedDataset)
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
            fullDataset.class_is_last()
            print(fullDataset)
            if "full" not in self.datasets.keys():
                self.datasets.update({"full":fullDataset})

        if self.newDatasetOptions["rankedBalanced"] or self.newDatasetOptions["rankedFull"]:
            self.generateInstances()


def main():
    # Initialization
    run = startFishing()
    run.initializeAll()

    fisher = scrape(
        urlFile="data/urls.txt",
        dataDir="data",
        database="data/data.db",
        driver=run.driver
        # urlNum=default is 1, update this value accordingly if resuming after an exit,
        # id=default is 1, update this value accordingly if resuming after an exit
    )
    # Handling an exception
    sys.excepthook = fisher.exitHandler

    # Initialization of the page analyzer
    pageData = pageAnalyzer(classVal=1)
    fisher.addAnalyzer(pageData)

    # Initialization of the image analyzer
    imageData = imageAnalyzer(classVal=1, HASH=True)
    fisher.addAnalyzer(imageData)

    # If resuming, uncomment the below line
    # fisher.resume()
    # Once the analyzers have been added, it doesn't matter what
    # instance the goFish method is called with
    fisher.goFish()
    print(pageData.features)
    print(imageData.features)

    # Data Combination
    # The features generated from the other instances are then used
    # when dealing with (creating datasets, classifying, ect.) data
    # Takes the same arguments as the scrape class
    # To continue scraping (in case the program crashes and you stored info in a database)
    # just adapt your urlFile to the url the program left off on
    # your id to 1 after the latest screenshot/html/css file
    # and your urlNum to the 1 + the number of urls that you've already scraped
    # and finally call the resume function to re-initialize necessary attributes
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

    occurences = Counter(fisher.allErrors)
    error = occurences.most_common(1)[0][0]
    print("Most common error: " + str(error))

    DC.closePWW3()
    DC.closeSelenium()


if __name__ == "__main__":
    main()
