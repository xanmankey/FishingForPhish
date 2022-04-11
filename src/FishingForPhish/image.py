# image.py: a python file showcasing the selected features
# used as an example instance of the analyzer class
# and bundled with the module
# (the file itself is never called by FishingForPhish.py due to the possibility of a circular import)
from FishingForPhish import startFishing, analyzer, scrape, saveFish
from selenium.webdriver.common.by import By
from weka.core.dataset import Instance
import subprocess
from collections import Counter
from PIL import Image
import imagehash
from urllib3.exceptions import InsecureRequestWarning
import cssutils
import requests
import logging

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
    }, **kwargs):
        '''Similarily to the pageBased class, inherits all attributes from the initialize and scape classes,
        (not pageFeatures) and adds an optional attribute called imageFeatures'''
        super().__init__(**kwargs)
        self.features = features
        self.featureNames = featureNames
        self.classVal = Instance.missing_value()

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

    def analyze(self, url, filename, resources, urlNum, HASH=False):
        '''Searches through the html of a url to get the specified image-features.
        These features are defined in the research paper at
        https://github.com/xanmankey/FishingForPhish/tree/main/research and broken down
        into the categories: layout, style, and other.'''
        features = {}
        totalTags = resources["BS"].find_all()
        selTotalTags = resources["driver"].find_elements(By.XPATH, "//*")
        linkTags = resources["driver"].find_elements(By.TAG_NAME, "link")

        if HASH:
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

if __name__ == "__main__":
    from FishingForPhish import startFishing, analyzer, scrape, saveFish
    requests.packages.urllib3.disable_warnings(
            category=InsecureRequestWarning)
    cssutils.log.setLevel(logging.CRITICAL)
    run = startFishing()
    run.installResources()
    run.initializeSelenium()

    fisher = scrape(
        urlFile="data/urls.txt",
        dataDir="data",
        driver=run.driver,
        classVal=0
    )

    imageData = imageAnalyzer()
    fisher.addAnalyzer(imageData)

    fisher.goFish()
    print(imageData.features)

    DC = saveFish(
        urlFile="data/urls.txt",
        dataDir="data",
        driver=run.driver,
        classVal=0,
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
