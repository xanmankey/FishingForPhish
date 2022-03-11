# A website to showcase what I've done and collect more data
# For debugging: kill -9 $(ps -A | grep python | awk '{print $1}') command kills all processes on linux
# Test link 1: https://www.google.com/ (returns Localhost can't connect)
# For testing, you need to use unique URLs (reddit, stackOverflow, YT, Amazon, google, ect.)
# Reddit doesn't respond fast enough to avoid 504 Gateway Time-out; I think timeout limit is like 30 seconds, so I'm gonna need to make sure something responds
# Try debugging websites in Firefox, it seems like the Chrome inspector doesn't provide accurate line numbers
# If codespaces crashes, try running on a different port (ex: flask run --port 8000)
# Threads exit upon an error!
# Work music: https://www.youtube.com/watch?v=fz-Sstui9yc
# imageFilters can't handle missing class instance?
import os
import json
import time as Time
import javabridge
import weka.core.jvm as jvm
from weka.core.dataset import Attribute, Instance, Instances
from weka.filters import Filter
# Not sure what class PredictionOutput belongs to
from weka.classifiers import Classifier, Evaluation, PredictionOutput
from weka.core.converters import Loader, Saver
from weka.attribute_selection import ASSearch, ASEvaluation, AttributeSelection
import validators
import requests
from cs50 import SQL
import short_url
from selenium import webdriver
from flask import Flask, flash, redirect, render_template, request
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
import threading
from urllib import parse
from urllib3.exceptions import InsecureRequestWarning
from collections import Counter

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# TODO: figure out MongoDB
"""
# Setup MongoDB NoSQL database
app.config['MONGODB_SETTINGS'] = {
    'db': 'your_database',
    'host': 'localhost',
    'port': 27017
}

db = MongoEngine()
db.init_app(app)
"""

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# 2 PAGE SITE: uploading and results
# export FLASK_DEBUG=ON turns on debug mode for flask and allows you to print to the console (has to be done after every reload tho)
#
# CREATE TABLE screenshots (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT UNIQCREATE TABLE results (id INTEGER PRIMARY KEY AUTOINCREMENT, classification TEXT, time INT, externalURL FLOAT, redirectURL FLOAT, hostnameMismatch BINARY, numDash INT, numEmail INT, numDots INT, numLinks INT, urlLength INT, FCTHR1 JSON, FCTHR2 JSON, FCTHR3 JSON, FCTHR4 JSON, FCTHR5 JSON, PYRAMIDR1 JSON, PYRAMIDR2 JSON, PYRAMIDR3 JSON, PYRAMIDR4 JSON, PYRAMIDR5 JSON, EDGER1 JSON, EDGER2 JSON, EDGER3 JSON, EDGER4 JSON, EDGER5 JSON, COLORR1 JSON, COLORR2 JSON, COLORR3 JSON, COLORR4 JSON, COLORR5 JSON);UE, time INT);
# CREATE TABLE duplicates (url TEXT, time INT);
# CREATE TABLE errors (error TEXT)
# .schema <table-name> tells you the command used to create a table
db = SQL("sqlite:///results.db")

# @app.route("/")
def getData(ID, dataDir, features):
    print("GET DATA")
    # Load newImageDataset
    loader = Loader(classname="weka.core.converters.ArffLoader")
    imageDataset = loader.load_file(dataDir + "screenshots/" + 'newImageDataset')

    # Create combined dataset ONLY attributes
    externalATT = Attribute.create_numeric("PctExtHyperlinks")
    redirectsATT = Attribute.create_numeric("PctNullSelfRedirectHyperlinks")
    notHostnameATT = Attribute.create_numeric("FrequentDomainNameMismatch")
    dashesATT = Attribute.create_numeric("NumDash")
    mailATT = Attribute.create_numeric("SubmitInfoToEmail")
    periodsATT = Attribute.create_numeric("NumDots")
    pageBased = []
    pageBased = [externalATT, redirectsATT, notHostnameATT, dashesATT, mailATT, periodsATT]

    # Store all combinedDataset attributes
    attributes = []

    for attribute in pageBased:
        attributes.append(attribute)
    for attribute in imageDataset.attributes():
        attributes.append(attribute)

    # Check if a combined dataset has already been created
    try:
        dataset = loader.load_file(dataDir + "screenshots/" + 'combinedDataset')
    except Exception:
        # Create the combined dataset
        dataset = Instances.create_instances("Combined page and image based data", [attributes], 0)

    # Create the new dataset (for classification)
    newDataset = Instances.create_instances("New dataset", [attributes], 0)

    # Breaking down the values from features + imageDataset into instances
    values = []
    for feature in features:
        values.append(feature)
    for instance in imageDataset:
        for value in instance.values:
            values.append(value)

    # Add the instance to and save the dataset
    inst = Instance.create_instance(values)
    dataset.add_instance(inst)
    newDataset.add_instance(inst)

    saver = Saver(classname="weka.core.converters.ArffSaver")
    saver.save_file(dataset, dataDir + "screenshots/" + 'combinedDataset')

    # Classify using the newData and a prior model (I'd need to use the full model most likely...)
    print("CLASSIFY")
    newDataset.class_is_last()
    # TODO: Load the full combined dataset to build the model
    fullTrain = loader.load_file(dataDir + "screenshots/" + 'combinedFullDataset.arff')
    cls = Classifier(classname="weka.classifiers.trees.J48")
    cls.build_classifier(fullTrain)
    output = PredictionOutput(classname="weka.classifiers.evaluation.output.prediction.CSV", options=["-distribution"])
    evl = Evaluation(fullTrain)
    evl.test_model(cls, newDataset, output=output)
    # TODO: figure out what output.buffer_content does
    # Store the time the webdriver visited the user-inputted website
    time = str(datetime.now())
    time = time[11:19]
    hour = int(time[:2])
    meridian = time[8:]
    # Special-case '12AM' -> 0, '12PM' -> 12 (not 24)
    if (hour == 12):
        hour = 0
    if (meridian == 'PM'):
        hour += 12
    time = "%02d" % hour + time[2:8]

    print(output.buffer_content())
    db.execute("INSERT INTO results (classification, time) VALUES (?, ?) WHERE id = ?", output.buffer_content(), time, ID)

    # Remove newImageDataset, stop jvm (I might want to leave it running, because it does take time to boot up, and the user may want to try another URL)
    os.remove(dataDir + "screenshots/" + 'newImageDataset')
    jvm.stop()

    return


# @app.route("/")

def getImageData(ID, filename, dataDir, filenameATT, tempImageDataset, features):
    # Initialize the filename (with the new filenames) and class_nom_att attributes
    # I can't thread this function unfortunately... https://groups.google.com/g/python-weka-wrapper/c/drN24Rc5T4M
    print(filename)
    print(tempImageDataset)
    print(filenameATT)
    # ImageFilters can't use Instance.missing_values(), so I'm just using legitimate as a temporary class (I drop the values later)
    values = [filenameATT.add_string_value(filename), 0]
    inst = Instance.create_instance(values)
    tempImageDataset.add_instance(inst)

    # Initialize the ImageFilters weka package (passing the image directory as an option, -D indicates directory)
    fcth = Filter(classname="weka.filters.unsupervised.instance.imagefilter.FCTHFilter", options=["-D", dataDir + "screenshots"])
    color = Filter(classname="weka.filters.unsupervised.instance.imagefilter.ColorLayoutFilter", options=["-D", dataDir + "screenshots"])
    edge = Filter(classname="weka.filters.unsupervised.instance.imagefilter.EdgeHistogramFilter", options=["-D", dataDir + "screenshots"])
    pyramid = Filter(classname="weka.filters.unsupervised.instance.imagefilter.BinaryPatternsPyramidFilter", options=["-D", dataDir + "screenshots"])

    # Indicate the datatype for the filters
    fcth.inputformat(tempImageDataset)
    color.inputformat(tempImageDataset)
    edge.inputformat(tempImageDataset)
    pyramid.inputformat(tempImageDataset)

    # Run the filters (and store the generated attributes)
    print("IMAGEFILTERS")
    fcthData = fcth.filter(tempImageDataset)
    colorData = color.filter(tempImageDataset)
    edgeData = edge.filter(tempImageDataset)
    pyramidData = pyramid.filter(tempImageDataset)

    datasets = [fcthData, colorData, edgeData, pyramidData]

    # Attributes to represent the top ranked attributes for dataset creation
    # Initializing attribute selection (only using InfoGain for the purposes of the website)
    # To keep full data, remove attribute selection code
    # LEFT OFF: TypeError: Object does not implement or subclass weka.attributeSelection.ASSearch: weka.attributeSelection.InfoGainAttributeEval
    print("FS")
    search = ASSearch(classname="weka.attributeSelection.InfoGainAttributeEval")
    evaluator = ASEvaluation(classname="weka.attributeSelection.Ranker")
    attsel = AttributeSelection()
    attsel.search(search)
    attsel.evaluator(evaluator)

    # Preparation to remove non-ranked instances and attributes
    rankedAtt = []
    datasets = [fcthData, pyramidData, colorData, edgeData]
    allAtt = []

    # Store the top 20 attributes
    for dataset in datasets:
        i = 0
        selection = attsel.select_attributes(dataset)
        for selected in selection:
            i += 1
            # Continue one time due to the filename attribute
            if i <= 6 and i != 1:
                rankedAtt.append(selected)
            else:
                break

    # Create a full dataset the first time around, adding Instance.missing_value() where not ranked
    # Load and append to it the second time around
    # TODO: not sure if this actually drops the class value
    print("ADD IMAGE DATA")
    for dataset in datasets:
        totalAttributes = dataset.num_attributes
        attributeNum = 1
        datasetNum = 1
        for attribute in dataset.attributes():
            if attributeNum == totalAttributes and datasetNum != 4:
                break
            if attribute in rankedAtt:
                values.append(attribute.value(0))
                pos = rankedAtt.index(attribute)
                if pos % 5 == 0:
                    # TODO: debug + figure out how JSON works
                    db.execute("INSERT INTO results (?) VALUES (?) WHERE id = ?", rankedAtt[(pos % 5) * (datasets.index(dataset) + 1)], json.dumps({attribute: attribute.value(0)}, ID))
                elif pos % 5 == 1:
                    db.execute("INSERT INTO results (?) VALUES (?) WHERE id = ?", rankedAtt[(pos % 5) * (datasets.index(dataset) + 1)], json.dumps({attribute: attribute.value(0)}, ID))
                elif pos % 5 == 2:
                    db.execute("INSERT INTO results (?) VALUES (?) WHERE id = ?", rankedAtt[(pos % 5) * (datasets.index(dataset) + 1)], json.dumps({attribute: attribute.value(0)}, ID))
                elif pos % 5 == 3:
                    db.execute("INSERT INTO results (?) VALUES (?) WHERE id = ?", rankedAtt[(pos % 5) * (datasets.index(dataset) + 1)], json.dumps({attribute: attribute.value(0)}, ID))
                elif pos % 5 == 4:
                    db.execute("INSERT INTO results (?) VALUES (?) WHERE id = ?", rankedAtt[(pos % 5) * (datasets.index(dataset) + 1)], json.dumps({attribute: attribute.value(0)}, ID))
            else:
                values.append(Instance.missing_value())
            allAtt.append(attribute)
            attributeNum += 1

    # Create a second temporary image dataset using the attributes
    print("CREATE IMAGE DATASET")
    newImageDataset = Instances.create_instances("Image dataset for testing imagefilters", [allAtt], 0)
    inst = Instance.create_instance(values)
    newImageDataset.add_instance(inst)

    saver = Saver(classname="weka.core.converters.arffSaver")
    saver.save_file(newImageDataset, dataDir + "screenshots/" + 'newImageDataset')

    getData(ID[0]['id'], dataDir, features)


@app.route("/", methods=["GET", "POST"])
def home():
    # If the user inputs a website
    if request.method == "POST":
        # Initialize error checking, user input, and filesystem
        validate = 0
        usrInput = request.form.get("url")
        dataDir = 'static/'

        # Checking if the URL is valid
        if validators.url(usrInput) != True:
            validate = 1

        # Checking for HTML injection (just in case; < and > are unsafe for urls so they shouldn't be in many anyway)
        if '<>' in usrInput:
            validate = 2

        if validate == 0:
            # Calling the thread, which runs the driver functions and generates the dataset, and then redirecting
            global generate
            generate = threading.Thread(target=generate, args=[usrInput, dataDir])
            generate.start()
            print("thread called")
            generate.join()
            print("thread exits")

            # Load results
            return redirect('/results')
        else:
            # If there's a validation error with user input, allow the user to change their input and send an error message
            flash("That's not a valid url... can you please try again?", category="error")
            return redirect('/')

    else:
        try:
            validate
        except NameError:
            validate = 0
        try:
            usrInput
        except NameError:
            usrInput = "temp"
        return render_template("home.html", validate=validate, url=usrInput)

def naming(ID):
    nameID = ''
    count = int(ID / 26) + 1
    for j in range(count):
        if ID > 25:
            asciiNum = ID % 26
            asciiNum = asciiNum + 65
            nameID += chr(asciiNum)
        else:
            nameID += chr(ID + 65)
    return nameID

# Can I call a function in '/' path and then redirect?
# What route does this need function need? I can't pass arguments via redirect, so unless I go global I need to call it from '/'
# I could either go w/ this threading solution or after_this_request and response.call_on_close:
# TODO: fix the app in accordance with database functionality (unsupervised; predictions)
# @app.route('/')
def generate(usrInput, dataDir):
    print("THREAD CALLED 2")
    # Initializization
    jvm.start(system_cp=True, packages=True)

    # For Firefox
    options = FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument('--hide-scrollbars')
    options.add_argument('--disable-gpu')
    driver = webdriver.Firefox(options=options)
    driver.set_window_size(1200, 600)

    dataDir = 'static/'

    try:
        db.execute("DELETE FROM errors")
    except BaseException:
        pass

    # Ignoring warnings about insecure requests due to disabled SSL. You need to be careful with turning off SSL certification;
    # However, because I'm just scraping and not inputting sensitive data, disabling it is fine
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


    # Create attributes (for both datasets)
    # Error checking
    print("CREATE ATT")
    filenameATT = Attribute.create_string("filename")
    class_nom_att = Attribute.create_nominal("nom", ['Legitimate', 'Phishing'])

    # Create initial image dataset (which is used to pass filtered values later on)
    tempImageDataset = Instances.create_instances("temporary Image Dataset", [filenameATT, class_nom_att], 0)
    print(tempImageDataset)

    # Initialization for storing scrapd page-based features
    # As well as a failedRequests array (contains selenium request fails and request lib fails)
    features = []
    originalName = 'temp'
    checkName = 'temp'
    urlFails = {}
    # Iterating and scraping for each file
    # Provided the file has the proper naming conventions and can function as a URL
    # There are 2 stages to the naming process: one is character replacement, where I replaced TODO

    # Get the URL (accounting for redirection)
    # Unfortunately, WebDriverException and TimeoutException are common, as many phishing URLs are taken down or made private
    driver.implicitly_wait(20)
    try:
        driver.get(usrInput)
    except BaseException:
        urlFails.update(newFilename=BaseException)
        checkName = 'nameError'
        db.execute("INSERT INTO errors (error) VALUES (?)", BaseException)

    print(checkName)
    # Ensure that the website loads
    # TODO: a final catch just in case the URL is stale the second time around
    if checkName != 'nameError':
        Time.sleep(5)
        try:
            url = driver.current_url
        except BaseException:
            Time.sleep(10)
            try:
                url = driver.current_url
            except BaseException:
                urlFails.update(newFilename=BaseException)
                checkName = 'nameError'
                db.execute("INSERT INTO errors (error) VALUES (?)", BaseException)

    # Check if the url is in the screenshots database
    # global dbID
    # dbID = db.execute("SELECT id FROM screenshots WHERE url = ?", url)
    # if dbID:
    #     # TEMPORARY PASS
    #     return


    # Checking if the url returns a 404 error
    # TODO: consider more error codes
    print(checkName)
    if checkName != 'nameError':
        try:
            # Check to make sure the page isn't an error page
            if requests.head(url, verify=False).status_code == 404:
                urlFails.update(url=404)
        except BaseException:
            urlFails.update(url=BaseException)
            checkName = 'nameError'
            db.execute("INSERT INTO errors (error) VALUES (?)", BaseException)

    # Store the time the webdriver visited the user-inputted website
    print("time")
    time = str(datetime.now())
    time = time[11:19]
    hour = int(time[:2])
    meridian = time[8:]
    # Special-case '12AM' -> 0, '12PM' -> 12 (not 24)
    if (hour == 12):
        hour = 0
    if (meridian == 'PM'):
        hour += 12
    time = "%02d" % hour + time[2:8]

    # Append to database
    print("append")
    db.execute('INSERT INTO screenshots (url, time) VALUES (?, ?)', url, time)
    ID = db.execute("SELECT id FROM screenshots ORDER BY id DESC LIMIT 1")
    print(ID)

    # Encode the url to name the screenshot
    print("naming")
    fileEncode = short_url.encode_url(ID[0]['id'])

    if fileEncode + '.png' in sorted(dataDir + 'screenshots'):
        with open(dataDir + 'source/' + fileEncode + '.html', 'r') as f:
            html = f.read()
    else:
        # After temptempImageDataset has been updated w/ values, load the html to obtain page-based data (using Selenium)
        html = driver.page_source

        # Save page source (in case the same website is called again in the future; saves download time)
        # TODO: figure out mongoDB + files + website/vercel
        with open(dataDir + 'source/' + fileEncode + '.html', 'w') as f:
            f.write(html)

    if html:
        print("SCRAPING")
        # Search for tags with links (looking for the "a" and "link" tags specifically)
        aTags = driver.find_elements(By.TAG_NAME, "a")
        linkTags = driver.find_elements(By.TAG_NAME, "link")
        numLinks = len(aTags) + len(linkTags)

        # Initialize arrays for storing the top 4 HTML-scraped features
        redirect = []
        mailTo = []
        external = []
        notHostname = []

        # The search is on!
        # Iterate through link tags, and check for link attributes
        # A check is included to only search the first 100 URLS (for the website, for this code the check is 1000 a tags and 1000 link tags)
        if len(aTags) != 0:
            m = 0
            for element in aTags:
                Time.sleep(0.01)
                if m >= 1000:
                    break
                try:
                    parsed = parse.urlparse(url)
                except BaseException:
                    urlFails.update(url=BaseException)
                    checkName = 'nameError'
                    break
                # Check all <a> for the href element
                # TODO: If the check fails twice, insert a placeholder
                try:
                    href = element.get_attribute("href")
                except BaseException:
                    newTags = driver.find_elements(By.TAG_NAME, "a")
                    try:
                        href = newTags[m].get_attribute("href")
                    except BaseException:
                        urlFails.update(url=BaseException)
                        checkName = 'nameError'
                        continue
                # TODO: get rid of if href once the placeholder insertion has been completed
                if href:
                    checkRequest = 0
                    if href != 'javascript:void(0)':
                        try:
                            response = requests.head(href, verify=False, timeout=10)
                        except BaseException:
                            checkRequest = 1
                    if "mailto:" in href:
                        mailTo.append({"mail": href})
                    if response.url == url and checkRequest == 0:
                        redirect.append({"redirect": href})
                    if parsed.netloc != url and checkRequest == 0:
                        external.append({"external": href})
                    notHostname.append(parsed.netloc)
                m += 1
        if len(linkTags) != 0:
            m = 0
            for element in linkTags:
                Time.sleep(0.01)
                if m >= 1000:
                    break
                try:
                    parsed = parse.urlparse(url)
                except BaseException:
                    checkName = 'nameError'
                    urlFails.update(url=BaseException)
                    break
                # Check all <link> for the href element
                # TODO: SAME ABOVE
                try:
                    href = element.get_attribute("href")
                except BaseException:
                    newTags = driver.find_elements(By.TAG_NAME, "link")
                    try:
                        href = newTags[m].get_attribute("href")
                    except BaseException:
                        checkName = 'nameError'
                        urlFails.update(url=BaseException)
                        continue
                if href:
                    checkRequest = 0
                    if href != 'javascript:void(0)':
                        try:
                            response = requests.head(href, verify=False, timeout=10)
                        except BaseException:
                            checkRequest = 1
                    if "mailto:" in href:
                        mailTo.append({"mail": href})
                    if response.url == url and checkRequest == 0:
                        redirect.append({"redirect": href})
                    if parsed.netloc not in url and checkRequest == 0:
                        external.append({"external": href})
                    notHostname.append(parsed.netloc)
                m += 1
        # TODO: maybe look for a better solution for 0 found external links then setting all scraped feature values to 0
        else:
            external.append(0)
            mailTo.append(0)
            redirect.append(0)
            notHostname.append(0)

        # Store totals for table iteration
        numExternal = len(external)
        numMail = len(mailTo)
        numRedirects = len(redirect)
        # DEBUG
        if len(notHostname) != 1 and notHostname[0] != 0:
            hostname = parse.urlparse(url)
            numHostname = Counter(notHostname)
            freqHostname = numHostname.most_common
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

        # image-based
        # Using Selenium to take a screenshot of the website
        try:
            driver.save_screenshot(dataDir + 'screenshots/' + fileEncode + '.png')
        except BaseException:
            checkName = 'nameError'
            urlFails.update(url=BaseException)
        originalName = fileEncode + '.png'

        # Store the data in a double array so it can be iterated over
        # numExternal hyperlinks is a percent
        # TODO: fix the percentage ones (I need a better solution than just '0'; this is temporary)
        # TODO: if legitimate works during the night, I'd like to try to run phishing quickly in the morning
        if checkName != 'nameError':
            print("APPENDING FEATURES")
            try:
                features.append(numExternal / numLinks)
            except ZeroDivisionError:
                features.append(0)

            # domain-name mismatch is a binary (adds up the most frequent hostname, and compares it to the domain name)
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

            # Extra features
            features.append(numLinks)
            features.append(len(url))

            # Even though this currently isn't pythonic, it seems faster then individual db insertions for right now
            # The individual insertion also sets the INTEGER PRIMARY KEY equivalent to that of TABLE screenshots
            db.execute("INSERT INTO results (externalURL, redirectURL, hostnameMismatch, numDash, numEmail, numDots, numLinks, urlLength) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            features[0], features[1], features[2], features[3], features[4], features[5], features[6], features[7])

            print(features)

    # I used ascii to keep the filenames in the same order (alphabetical)
    if checkName != "nameError":
        nameID = naming(ID[0]['id'])
        os.rename(dataDir + 'screenshots/' + originalName, dataDir + 'screenshots/' + nameID + originalName)

    # Exiting Selenium
    driver.close()
    driver.quit()

    # Calling the ImageData function
    print("IMAGE DATA THREAD")
    print(filenameATT)
    getImageData(ID[0]['id'], nameID + originalName, dataDir, filenameATT, tempImageDataset, features)
    # imageData.start()
    # imageData.join()

    # Calling the getData function
    print("COMBINED DATA THREAD")
    # combinedData = threading.Thread(target=getData, args=[ID[0]['id'], dataDir, features])
    # combinedData.start()
    # combinedData.join()

    print("RETURN")
    return

# I'm going to be using a thread to run all the code above that way I can display a loading screen until it's loaded
# Read the model data (from the results and features tables) and visualize them accordingly
@app.route("/results", methods=["GET", "POST"])
def results():
    if request.method == "POST":
        return redirect('/')
    else:
        print("GET RESULTS")
        # global dbID
        # if dbID:
        #     screenshots = db.execute("SELECT * FROM screenshots WHERE id = ?", dbID[0]['id'])
        #     data = db.execute("SELECT * FROM results WHERE id = ?", dbID[0]['id'])
        # I might make this check less harsh, for now I am going to redirect to errors on any error
        errors = db.execute("SELECT * FROM errors")
        if len(errors) != 0:
            return redirect('/errors')
        screenshots = db.execute("SELECT * FROM screenshots ORDER BY id DESC LIMIT 1")

        # Check if any thread is running (specifically generate; I might come up w/ a more pythonic solution than global vars later)
        if generate.is_alive():
            # Loading screen
            global loading
            loading = 0
            print("still loading!")
            return redirect('/loading')

        data = db.execute("SELECT * FROM results ORDER BY id DESC LIMIT 1")

        ID = screenshots[0]['id']
        url = screenshots[0]['url']
        fileEncode = short_url.encode_url(ID)
        nameID = naming(ID)
        filename = nameID + fileEncode

        otherNames = ["urlLength", "Total number of links in <a> and <link> tags"]

        print("DATA")
        print(data)
        otherData = [data[0]["urlLength"], data[0]["numLinks"]]

        pageBasedNames = ["percentage of eternal URLs", "percentage of self redirect URLs", "percentage of redirect domains that are the same as the current domain",
        "Number of dashes in the URL", "Number of external URLs involving mailTo", "Number of dots in the URL"]

        pageBasedData = [data[0]["externalURL"], data[0]["redirectURL"], data[0]["hostnameMismatch"],
        data[0]["numDash"], data[0]["numEmail"], data[0]["numDots"]]

        # dumps = convert to, loads = convert from when using json. Remember that load converts to dictionary
        imageBasedNames = [json.loads(data[0]["FCTHR1"]).keys(), json.loads(data[0]["FCTHR2"]).keys(), json.loads(data[0]["FCTHR3"]).keys(),
        json.loads(data[0]["FCTHR4"]).keys(), json.loads(data[0]["FCTHR5"]).keys(), json.loads(data[0]["PYRAMIDR1"]).keys(), json.loads(data[0]["PYRAMIDR2"]).keys(),
        json.loads(data[0]["PYRAMIDR3"]).keys(), json.loads(data[0]["PYRAMIDR4"]).keys(), json.loads(data[0]["PYRAMIDR5"]).keys(),
        json.loads(data[0]["EDGER1"]).keys(), json.loads(data[0]["EDGER2"]).keys(), json.loads(data[0]["EDGER3"]).keys(), json.loads(data[0]["EDGER4"]).keys(),
        json.loads(data[0]["EDGER5"]).keys(), json.loads(data[0]["COLORR1"]).keys(), json.loads(data[0]["COLORR2"]).keys(), json.loads(data[0]["COLORR3"]).keys(),
        json.loads(data[0]["COLORR4"]).keys(), json.loads(data[0]["COLORR5"]).keys()]

        imageBasedData = [json.loads(data[0]["FCTHR1"]).values(), json.loads(data[0]["FCTHR2"]).values(), json.loads(data[0]["FCTHR3"]).values(), json.loads(data[0]["FCTHR4"]).values(),
        json.loads(data[0]["FCTHR5"]).values(), json.loads(data[0]["PYRAMIDR1"]).values(), json.loads(data[0]["PYRAMIDR2"]).values(), json.loads(data[0]["PYRAMIDR3"]).values(),
        json.loads(data[0]["PYRAMIDR4"]).values(), json.loads(data[0]["PYRAMIDR5"]).values(), json.loads(data[0]["EDGER1"]).values(), json.loads(data[0]["EDGER2"]).values(),
        json.loads(data[0]["EDGER3"]).values(), json.loads(data[0]["EDGER4"]).values(), json.loads(data[0]["EDGER5"]).values(), json.loads(data[0]["COLORR1"]).values(),
        json.loads(data[0]["COLORR2"]).values(), json.loads(data[0]["COLORR3"]).values(), json.loads(data[0]["COLORR4"]).values(), json.loads(data[0]["COLORR5"]).values()]


        return render_template("results.html", filename=filename, url=url, classify=data[0]['classification'], finalTime=data[0]["time"], screenshotTime=screenshots[0]["time"],
        otherData=otherData, otherNames=otherNames, pageBasedNames=pageBasedNames, pageBasedData=pageBasedData, imageBasedNames=imageBasedNames, imageBasedData=imageBasedData)


@app.route("/errors", methods=["GET", "POST"])
def error():
    errors = db.execute("SELECT * FROM errors")
    if request.method == "POST":
        return redirect('/')
    else:
        return render_template("errors.html", errors=errors[0]["error"])


@app.route("/loading", methods=["GET", "POST"])
def load():
    screenshots = db.execute("SELECT url FROM screenshots ORDER BY id DESC LIMIT 1")
    global loading
    if request.method == "POST":
        return redirect('/')
    else:
        if not generate.is_alive():
            return redirect('/results')
        elif loading == 0:
            loading = 1
            return render_template("loading.html", url=screenshots[0]["url"])



# For status error handling, I'll just flash a message
def errorhandler(e):
    "Handle error"
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return flash("Sorry, that action returned " + e.name + ", code " + str(e.code))


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


if __name__ == '__main__':
    app.run()