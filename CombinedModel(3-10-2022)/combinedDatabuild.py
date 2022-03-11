# This file is for creating a combined dataset using data from the 200 legitimate websites obtained from Open Page Rank
# And the 100 phishing websites from PhishStats
import os
from collections import Counter
import weka.core.jvm as jvm
from weka.core.dataset import Attribute, Instance, Instances
from weka.core.converters import Saver
from weka.filters import Filter
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, WebDriverException, UnexpectedAlertPresentException
import time
import short_url
from urllib import parse
from urllib3.exceptions import InsecureRequestWarning
import requests
import sys
import validators


def getData(names, features, imageDataset):
    # Create combined dataset ONLY attributes
    filenameATT = Attribute.create_string("filename")
    class_nom_att = Attribute.create_nominal("nom", ['0', '1'])
    externalATT = Attribute.create_numeric("PctExtHyperlinks")
    redirectsATT = Attribute.create_numeric("PctNullSelfRedirectHyperlinks")
    notHostnameATT = Attribute.create_numeric("FrequentDomainNameMismatch")
    dashesATT = Attribute.create_numeric("NumDash")
    mailATT = Attribute.create_numeric("SubmitInfoToEmail")
    periodsATT = Attribute.create_numeric("NumDots")

    # Seperating the values into arrays
    print(features)
    external = []
    notHostname = []
    redirects = []
    mail = []
    dashes = []
    numPeriods = []
    j = -1
    i = 0
    # TODO: list index of range
    for feature in features:
        j += 1
        for value in feature:
            value = value[0]
            if j == 0:
                external.append(value)
            elif j == 1:
                notHostname.append(value)
            elif j == 2:
                redirects.append(value)
            elif j == 3:
                mail.append(value)
            elif j == 4:
                dashes.append(value)
            elif j == 5:
                numPeriods.append(value)
            elif j > 5:
                break

    # Store all imageDataset attributes
    attributes = []
    for attribute in imageDataset.attributes():
        attributes.append(attribute)

    # Create the new dataset
    dataset = Instances.create_instances("Combined page and image based data", [filenameATT, externalATT, redirectsATT, notHostnameATT,
    dashesATT, mailATT, periodsATT, attributes[1], attributes[2], attributes[3], attributes[4], attributes[5], attributes[6],
    attributes[7], attributes[8], attributes[9], attributes[10], attributes[11], attributes[12], attributes[13], attributes[14],
    attributes[15], attributes[16], attributes[17], attributes[18], attributes[19], attributes[20], class_nom_att], 0)

    # Breaking down the values from features + imageDataset into instances
    j = 0
    for instance in imageDataset:
        values = []
        i = 0
        j += 1
        for value in instance.values:
            if i == 0:
                value = filenameATT.add_string_value(names[j - 1])
            values.append(value)
            i += 1
            if i == 1:
                values.append(external[j-1])
                values.append(notHostname[j-1])
                values.append(redirects[j-1])
                values.append(mail[j-1])
                values.append(dashes[j-1])
                values.append(numPeriods[j-1])
        # Append the instances to the combined dataset
        inst = Instance.create_instance(values)
        dataset.add_instance(inst)

    print(dataset)

    return dataset


def getImageData(filenameATT, class_nom_att, tempImageDataset):
    print("imagedata calls")
    # Initialize the filename (with the new filenames) and class_nom_att attributes
    i = 0
    names = []
    nominals = []

    for filename in sorted(os.listdir(str(sys.argv[1]))):
        try:
            url = filename.replace('.jpg', '')
            url = url.replace('.png', '')
            url = url[1:len(url)]
            decoded = short_url.decode_url(url)
        except Exception:
            print(Exception)
            continue
        names.append(filename)
        nominals.append(int(sys.argv[5]))
        values = [filenameATT.add_string_value(names[i]), nominals[i]]
        i += 1
        inst = Instance.create_instance(values)
        tempImageDataset.add_instance(inst)

    if len(names) == 0:
        print("Sorry, we couldn't process any of the urls!")
        return 1

    # Initialize the ImageFilters weka package (passing the image directory as an option, -D indicates directory)
    fcth = Filter(classname="weka.filters.unsupervised.instance.imagefilter.FCTHFilter", options=["-D", sys.argv[1]])
    color = Filter(classname="weka.filters.unsupervised.instance.imagefilter.ColorLayoutFilter", options=["-D", sys.argv[1]])
    edge = Filter(classname="weka.filters.unsupervised.instance.imagefilter.EdgeHistogramFilter", options=["-D", sys.argv[1]])
    pyramid = Filter(classname="weka.filters.unsupervised.instance.imagefilter.BinaryPatternsPyramidFilter", options=["-D", sys.argv[1]])

    # Indicate the datatype for the filters
    fcth.inputformat(tempImageDataset)
    color.inputformat(tempImageDataset)
    edge.inputformat(tempImageDataset)
    pyramid.inputformat(tempImageDataset)

    # Run the filters (and store the generated attributes)
    fcthData = fcth.filter(tempImageDataset)
    colorData = color.filter(tempImageDataset)
    edgeData = edge.filter(tempImageDataset)
    pyramidData = pyramid.filter(tempImageDataset)

    datasets = [fcthData, colorData, edgeData, pyramidData]

    # Attributes to represent the top ranked attributes for dataset creation
    # TODO: maybe experiment with adaptive feature selection for the website
    FCTH1 = Attribute.create_numeric("FCTH18")
    FCTH2 = Attribute.create_numeric("FCTH24")
    FCTH3 = Attribute.create_numeric("FCTH25")
    FCTH4 = Attribute.create_numeric("FCTH42")
    FCTH5 = Attribute.create_numeric("FCTH43")
    PYRAMID1 = Attribute.create_numeric("Spatial Pyramid of Local Binary Patterns0")
    PYRAMID2 = Attribute.create_numeric("Spatial Pyramid of Local Binary Patterns1")
    PYRAMID3 = Attribute.create_numeric("Spatial Pyramid of Local Binary Patterns34")
    PYRAMID4 = Attribute.create_numeric("Spatial Pyramid of Local Binary Patterns36")
    PYRAMID5 = Attribute.create_numeric("Spatial Pyramid of Local Binary Patterns37")
    EDGE1 = Attribute.create_numeric("MPEG-7 Edge Histogram17")
    EDGE2 = Attribute.create_numeric("MPEG-7 Edge Histogram20")
    EDGE3 = Attribute.create_numeric("MPEG-7 Edge Histogram37")
    EDGE4 = Attribute.create_numeric("MPEG-7 Edge Histogram39")
    EDGE5 = Attribute.create_numeric("MPEG-7 Edge Histogram42")
    COLOR1 = Attribute.create_numeric("MPEG-7 Color Layout1")
    COLOR2 = Attribute.create_numeric("MPEG-7 Color Layout3")
    COLOR3 = Attribute.create_numeric("MPEG-7 Color Layout4")
    COLOR4 = Attribute.create_numeric("MPEG-7 Color Layout5")
    COLOR5 = Attribute.create_numeric("MPEG-7 Color Layout8")

    newImageDataset = Instances.create_instances("Ranked image dataset", [filenameATT, FCTH1, FCTH2, FCTH3, FCTH4, FCTH5, PYRAMID1, PYRAMID2, PYRAMID3, PYRAMID4,
    PYRAMID5, EDGE1, EDGE2, EDGE3, EDGE4, EDGE5, COLOR1, COLOR2, COLOR3, COLOR4, COLOR5, class_nom_att], 0)

    # Preparation to remove non-ranked instances and attributes
    attributes = []
    rankedAtts = [str(FCTH1), str(FCTH2), str(FCTH3), str(FCTH4), str(FCTH5), str(PYRAMID1), str(PYRAMID2), str(PYRAMID3),
    str(PYRAMID4), str(PYRAMID5), str(EDGE1), str(EDGE2), str(EDGE3), str(EDGE4), str(EDGE5), str(COLOR1),
    str(COLOR2), str(COLOR3), str(COLOR4), str(COLOR5)]
    datasets = [fcthData, pyramidData, colorData, edgeData]
    newDatasets = []

    # Remove non-ranked instances and attributes from each filtered dataset
    i = -1
    for data in datasets:
        attributeNum = 0
        attributeTotal = data.num_attributes
        DATASET = data
        toggle = 0
        i += 1
        for attribute in DATASET.attributes():
            if str(attribute) in rankedAtts:
                attributes.append(attribute)
                attributeNum += 1
            elif attributeNum == attributeTotal - 1:
                newDatasets.append(newDataset)
                break
            else:
                if toggle == 0:
                    name = str(attribute).replace("@attribute ", "")
                    name = name.replace(" numeric", "")
                    remove = Filter(classname="weka.filters.unsupervised.attribute.RemoveByName", options=["-E", '^.*' + name + '$'])
                    remove.inputformat(DATASET)
                    newDataset = remove.filter(DATASET)
                    toggle += 1
                else:
                    name = str(attribute).replace("@attribute ", "")
                    name = name.replace(" numeric", "")
                    name = name.replace("'", "")
                    remove = Filter(classname="weka.filters.unsupervised.attribute.RemoveByName", options=["-E", '^.*' + name + '$'])
                    remove.inputformat(newDataset)
                    newDataset = remove.filter(newDataset)
                attributeNum += 1

    # Put the datasets together
    for m in range(len(names)):
        values = []
        cycle = 0
        toggle = 0
        j = 0
        i = 0
        for dataset in newDatasets:
            cycle += 1
            i = 0
            for instance in dataset:
                for value in instance.values:
                    if toggle == 0:
                        toggle = 1
                        values.append(filenameATT.add_string_value(names[m]))
                    if i >= 1 and i != 6:
                        values.append(value)
                    if cycle == 4:
                        j += 1
                        if j == 7:
                            values.append(value)
                            inst = Instance.create_instance(values)
                    i += 1
                dataset.delete(0)
                break
        newImageDataset.add_instance(inst)

    print(newImageDataset)

    return newImageDataset, names

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

# TODO: rerun with fixes
def main():
    # TODO: figure out the logical errors/webdriver for the phishing websites
    # CL check
    # My Example run commands: python combinedDatabuild.py LegitScreenshots static/ Legitimate Phishing 0
    # python combinedDatabuild.py PhishScreenshotsTest static/ Legitimate Phishing 1
    if len(sys.argv) != 6:
        print("Usage: python combinedDatabuild.py screenshotDirectoryWithAppropriateNamingConventions dataDirectory/ class1 class2 binaryCurrentClass")
        print("Assuming you have screenshot data with URL names w/ proper naming conventions (which can be found at PROVIDE LINK TO GITHUB)")
        exit()

    # Initializization
    jvm.start(system_cp=True, packages=True)

    # For Firefox
    options = FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument('--hide-scrollbars')
    options.add_argument('--disable-gpu')
    driver = webdriver.Firefox(options=options)
    driver.set_window_size(1200, 600)
    try:
        # type the path to your wayback machine file extension here.
        wayback_path = "/mnt/c/CODING/JS(java)/machineLearning/DataCombinationScript/phishAIurl/firefoxExtensions/wayback_machine-3.0-fx.xpi"
        driver.install_addon(wayback_path, temporary=True)
    except Exception:
        pass

    dataDir = sys.argv[2]

    # Ignoring warnings about insecure requests due to disabled SSL. You need to be careful with turning off SSL certification;
    # However, because I'm just scraping and not inputting sensitive data, disabling it is fine
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


    # Create attributes (for both datasets)
    # Error checking
    filenameATT = Attribute.create_string("filename")
    try:
        class_nom_att = Attribute.create_nominal("nom", [str(sys.argv[3]), str(sys.argv[4])])
    except TypeError:
        print("Class name must be castable to a string!")
        jvm.stop()
        driver.quit()
        exit()
    try:
        int(sys.argv[5])
    except TypeError:
        print("The class index (binaryCurrentClass) must be castbale to an integer!")
        jvm.stop()
        driver.quit()
        exit()

    # Create initial image dataset (which is used to pass filtered values later on)
    tempImageDataset = Instances.create_instances("temporary Image Dataset", [filenameATT, class_nom_att], 0)

    # Initialization for storing scrapd page-based features
    # As well as a failedRequests array (contains selenium request fails and request lib fails)
    features = [[],[], [], [], [], []]
    originalName = []
    newName = []
    urlFails = {}
    urls = {}
    i = 1
    j = 0
    # Iterating and scraping for each file
    # Provided the file has the proper naming conventions and can function as a URL
    # There are 2 stages to the naming process: one is character replacement, where I replaced TODO
    for filename in sorted(os.listdir(str(sys.argv[1]))):
        newFilename = filename
        if "https__" in newFilename:
            newFilename = newFilename.replace("https__", "https://")
        elif "http__" in newFilename:
            newFilename = newFilename.replace("http__", "http://")
        # TODO: TEMP one '_' only for phish websites
        elif "https_" in newFilename:
            newFilename = newFilename.replace("https_", "https://")
        elif "http_" in newFilename:
            newFilename = newFilename.replace("http_", "http://")
        if '_' in newFilename:
            newFilename = newFilename.replace("_", "/")
        if '.jpg' in newFilename:
            newFilename = newFilename.replace(".jpg", "")
        if '.png' in newFilename:
            newFilename = newFilename.replace(".png", "")

        if validators.url(newFilename) != True:
            print("Remember that your filenames need to follow the naming conventions at (GITHUB LINK HERE)")
            originalName.append('nameError')
            newName.append('nameError')
            # jvm.stop()
            # driver.quit()
            # exit()
            continue

        # Get the URL (accounting for redirection)
        # Unfortunately, WebDriverException and TimeoutException are common, as many phishing URLs are taken down or made private
        print(newFilename)
        driver.implicitly_wait(20)
        try:
            driver.get(newFilename)
        except BaseException:
            # TODO: I think this is how you append a key-value pair to a dict
            urlFails.update(newFilename=BaseException)
            originalName.append('nameError')
            newName.append('nameError')
            continue

        # Ensure that the website loads
        # TODO: a final catch just in case the URL is stale the second time around
        time.sleep(5)
        try:
            url = driver.current_url
        except BaseException:
            time.sleep(10)
            try:
                url = driver.current_url
            except BaseException:
                print("driver.current_url error")
                urlFails.update(newFilename=BaseException)
                originalName.append('nameError')
                newName.append('nameError')
                continue

        # Checking if the url returns a 404 error
        # TODO: consider more error codes
        if url:
            try:
                # Check to make sure the page isn't an error page
                if requests.head(url, verify=False, timeout=5).status_code == 404:
                    urlFails.update(url=404)
            except BaseException:
                print("404 error")
                urlFails.update(url=BaseException)
                originalName.append('nameError')
                newName.append('nameError')
                continue

        # Stage 2 of naming: encoding and storing the url using short_url (1 indexed)
        # TODO: Is this actually encoding a URL?
        fileEncode = short_url.encode_url(i)
        urls.update(url=i)

        originalName.append(filename)
        newName.append(fileEncode + '.jpg')

        if fileEncode + '.jpg' in sorted(os.listdir(str(sys.argv[1]))):
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
            # Search for tags with links (looking for the "a" and "link" tags specifically)
            aTags = driver.find_elements(By.TAG_NAME, "a")
            linkTags = driver.find_elements(By.TAG_NAME, "link")
            numLinks = len(aTags) + len(linkTags)
            print(numLinks)

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
                    time.sleep(0.01)
                    if m >= 1000:
                        break
                    try:
                        parsed = parse.urlparse(url)
                    except BaseException:
                        urlFails.update(url=BaseException)
                        originalName.append('nameError')
                        newName.append('nameError')
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
                            print("Stale reference error")
                            urlFails.update(url=BaseException)
                            originalName.append('nameError')
                            newName.append('nameError')
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
                    time.sleep(0.01)
                    if m >= 1000:
                        break
                    try:
                        parsed = parse.urlparse(url)
                    except BaseException:
                        originalName.append('nameError')
                        newName.append('nameError')
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
                            print("Stale reference error")
                            originalName.append('nameError')
                            newName.append('nameError')
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
            # TODO: find a better solution for 0 found external links then setting all scraped feature values to 0
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

            # Store the data in a double array so it can be iterated over
            # numExternal hyperlinks is a percent
            # TODO: fix the percentage ones (I need a better solution than just '0'; this is temporary)
            # TODO: if legitimate works during the night, I'd like to try to run phishing quickly in the morning
            if newName != 'nameError':
                try:
                    features[j].append([numExternal / numLinks])
                except ZeroDivisionError:
                    features[j].append([0])

                # domain-name mismatch is a binary (adds up the most frequent hostname, and compares it to the domain name)
                features[j + 1].append([numNotHostname])

                # numRedirects is a percent
                try:
                    features[j + 2].append([numRedirects / numLinks])
                except ZeroDivisionError:
                    features[j + 2].append([0])

                # numMail, numDashes, and numPeriods are numeric
                features[j + 3].append([numMail])
                features[j + 4].append([numDashes])
                features[j + 5].append([numPeriods])

                i += 1

    print("done w/ feature initialization")
    # Renaming according to the naming process defined earlier
    i = 0
    try:
        # I used ascii to keep the filenames in the same order
        for filename in sorted(os.listdir(str(sys.argv[1]))):
            if newName[i] == "nameError":
                print("nameError")
                i += 1
                continue
            nameID = naming(i)
            os.rename(str(sys.argv[1]) + '/' + originalName[i], str(sys.argv[1]) + '/' + nameID + newName[i])
            i += 1
    except IndexError:
        print("index error")
        jvm.stop()
        driver.close()
        driver.quit()
        exit()


    # Filter the images and store filter values in a second temporary dataset
    imageData, names = getImageData(filenameATT, class_nom_att, tempImageDataset)

    if type(imageData) == int:
        jvm.stop()
        driver.close()
        driver.quit()
        exit()

    # Pass the second temporary dataset so it can be incorporated into a combined dataset
    # Along with the page-based features
    finalDataset = getData(names, features, imageData)

    # SAVE THE COMBINED DATASET
    datasetSaver = Saver(classname="weka.core.converters.ArffSaver")
    datasetSaver.save_file(finalDataset, dataDir + '/datasets/combinedDataset.arff')

    # Temp print
    print(urlFails)

    # Exit all processes
    jvm.stop()
    driver.close()
    driver.quit()
    exit()


if __name__ == "__main__":
    main()