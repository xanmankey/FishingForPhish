API
===

The following section provides examples and goes into more depth about using FishingForPhish.
More examples and documentation will be added when time allows, and similar documentation can be found in docstrings for classes and methods. 
The API examples are currently broken down into example code snippets (*which unfortunately aren't always  able to stand alone due to the reliance on other sections of the code, for example initialization*) and a simple combined example at the end of the documentation.

startFishing
----------

In order to scrape, parse html, or work with datasets, you first have to initialize the library.
You can do that by creating an instance of the class startFishing and then calling the method initializeAll.
**Note: whenever you initialize either a webdriver instance or start the JVM, the associated exit method should be run in order to exit properly**

.. code-block:: python

   from classes import startFishing
   
   run = startFishing(dataDir="data")
   run.initializeAll()

The startFishing class has 3 attributes:

* dataDir=None
      The home directory for the scraped files. This includes a screenshots, html, css, and datasets directory. If left None, an empty
      "data" directory following the file system structure will be created.
* driver=None
      The instance of Selenium Webdriver. In most cases, this will be None (unless a webdriver instance has already been created; in which case
      the initialization process for it can be skipped).
* jvmToggle=False
      A toggle attribute that follows the state of the jvm (as python weka wrapper currently doesn't support checking the current run state of the jvm). A value should **NOT** be passed for this variable, otherwise functions reliant on the jvm can be called before the jvm's initialization.
      
The startFishing class has 4 methods in addition to __init__():

* installResources(self)
      Installs potentially-useful resources used during the methodology of the research here: https://github.com/xanmankey/FishingForPhish/tree/main/research. This includes the chiSquaredAttributeEval feature selector for WEKA, the SMOTE oversampler for WEKA, and the Wayback Machine add-on for Firefox, and has a commented out option for installing a popup blocker to remove popups in screenshots. If WEKA packages are installed, **note that they won't be activate until the NEXT startup of the JVM**.
* initializeSelenium(self, add_ons=None)
      Creates the Selenium instance. A list of paths to add_ons (.xpi files) can be passed to enhance the scraping experience. The wayback_machine add-on is added to the webdriver instance with the method initializeAll(). Selenium is initialized in headless mode, with a disabled-gpu and hidden scrollbars, and also doesn't store any cookie, cache, or session data for security reasons. Unfortunately, javascript does need to be enabled due to the reliance of the DOM on JS for some dynamic websites, and in the context of scraping phishing websites could be a potential safety-flaw, so VPN and VM usage are strongly recommended.
* initializePWW3(self, jvmOptions)
      Starts JVM with a list of optional parameters, jvmOptions (some default options, system_cp and packages, are passed with the initializeAll() method). The attribute jvmToggle is updated to be True.
* initializeAll(self, jvmOptions=["system_cp", "packages"], add_ons=['wayback_machine-3.0-fx.xpi'])
      As used in the example above, sequentially handles logging accordingly (to avoid console spam), calls initializePWW3 (with the default options, system_cp and packages. Packages must be True if you want to use any packages), installResources(), and then initializeSelenium using the specified add_ons, which defaults to the installed 'wayback_machine-3.0-fx.xpi' from the call to installResources. This method can be adapted, but currently defaults to using the settings used during the research at https://github.com/xanmankey/FishingForPhish/tree/main/research. 

analyzer
--------

The analyzer class is a base class, inherited by all analyzers (which in this context refers to feature selection classes with an **analyze** function that returns appropriate features: more on this below). 

The analyzer class has NO attributes. However, 3 attributes are **required** (where required implies that the user creates their own code that follows these guidelines; as of right now my attempts at inheritance have ended up in overwriting values, but this could probably be refactored to allow for inheritable and editable attributes, I just wasn't able to on my initial attempt and haven't yet had time to update the code):

* self.features
   An array of dictionaries, where each dictionary is composed of a key-value pair of featureName:value
* self.featureNames
   A dictionary where each key-value pair follows the featureName:stringWekaDatasetType (more informat regarding weka dataset types can be found at https://waikato.github.io/weka-wiki/formats_and_processing/arff_stable/)
* self.classVal
   The class value of the scraped instances used in the Weka dataset. The value of self.classVal is used in the goFish() method via passing of the resources dictionary.

The analyzer class has 1 inheritible method and 1 **required** method:

* name
   A convenience method for getting the analyzer name, or the name of the class.
* analyzer
   The analyzer function is a user created function; it is not inherited via code, and needs to be made by hand. The analyzer functions work in tandem with the goFish() method of the scrape class, which iterates through the provided urlFile and scrapes necessary data, whereas the analyzer functions analyze this data by taking a dictionary of resources resources (this includes the driver, database, BS instance, ect.; update this list if you need to access another resource from the scrape class), using them for analysis accordingly, and then returning the updated features, along with new key-value pairs, including "classVal":self.classVal, "features":features, and "featureNames":self.featureNames. Once these values are passed back to the goFish() method, it updates accordingly, and then the process either repeats for the next url in the urlFile or completes. 

scrape
------

The scrape class is a useful compilation of all the scraping-related methods used, from saving a screenshot of a full webpage to checking if a site responded with no errors. The goFish() method is used to encompass the majority of the scrape class's functionality, providing a method for iterating and validating urls, in addition to parsing html, css, and taking a screenshot for analysis, and the comprehensive __init__ function and variety of supporting methods provide a lot of inheritable functionality.

The scrape class inherits all attributes from the initialize class and declares 8 new ones:

* urlFile
      A required argument; the path to a .txt file with a url on each line.
* database=None
      An optional (but recommended) argument; database functionality (especially with a filesystem mirroring that of integer primary keys) is useful for carrying results over, storing and accessing data, and provides more opportunities (for example hash storage) for future classification. The database (along with the WEKA datasets) should reflect the datatypes of your features if you create a new table or dataset. If you input a valid database (even if empty), 7 tables are created (unless they already exist) including:
|
#. metadata: CREATE TABLE metadata (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT UNIQUE, UTCtime INT, classification TEXT)
      
#. page: CREATE TABLE page (id INTEGER PRIMARY KEY, NumDots INT, SubdomainLevel INT, PathLevel INT, UrlLength INT, NumDash INT, NumDashInHostname INT, AtSymbol BOOLEAN, TildeSymbol INT, NumUnderscore INT, NumPercent INT, NumQueryComponents INT, NumAmpersand INT, NumHash INT, NumNumericChars INT, NoHttps INT, RandomString INT, IpAddress INT, DomainInSubdomains INT, DomainInPaths INT, HttpsInHostname INT, HostnameLength INT, PathLength INT, QueryLength INT, DoubleSlashInPath INT, NumSensitiveWords INT, EmbeddedBrandName INT, PctExtHyperlinks FLOAT, PctExtResourceUrls FLOAT, ExtFavicon INT, InsecureForms INT, RelativeFormAction INT, ExtFormAction INT, AbnormalFormAction INT, PctNullSelfRedirectHyperlinks FLOAT, FrequentDomainNameMismatch INT, FakeLinkInStatusBar INT, RightClickDisabled INT, PopUpWindow INT, SubmitInfoToEmail INT, IframeOrFrame INT, MissingTitle INT, ImagesOnlyInForm INT, SubdomainLevelRT INT, UrlLengthRT INT, PctExtResourceUrlsRT INT, AbnormalExtFormActionR INT, ExtMetaScriptLinkRT INT, PctExtNullSelfRedirectHyperlinksRT INT)
      
#. errors: CREATE TABLE errors (url TEXT, error TEXT)
      
#. image: CREATE TABLE image (id INTEGER PRIMARY KEY, numTagsInHtml INT, numTagsInHead INT, numTagsInMain INT, numTagsInBody INT, pctImgTags FLOAT, totalWidth FLOAT, totalHeight FLOAT, IMredMean FLOAT, IMredStdDev FLOAT, IMgreenMean FLOAT, IMgreenStdDev FLOAT, IMblueMean FLOAT, IMblueStdDev FLOAT, IMalphaChannel INT, IMgamma FLOAT, numBoldTags INT, averageFontWeight FLOAT, mostUsedFont TEXT, averageFontSize FLOAT, numStyles INT, mostUsedStyle TEXT, pctItalics FLOAT, pctUnderline FLOAT, favicon INT)
            
#. allData: CREATE TABLE allData (id INTEGER PRIMARY KEY, NumDots INT, SubdomainLevel INT, PathLevel INT, UrlLength INT, NumDash INT, NumDashInHostname INT, AtSymbol INT, TildeSymbol INT, NumUnderscore INT, NumPercent INT, NumQueryComponents INT, NumAmpersand INT, NumHash INT, NumNumericChars INT, NoHttps INT, RandomString INT, IpAddress INT, DomainInSubdomains INT, DomainInPaths INT, HttpsInHostname INT, HostnameLength INT, PathLength INT, QueryLength INT, DoubleSlashInPath INT, NumSensitiveWords INT, EmbeddedBrandName INT, PctExtHyperlinks FLOAT, PctExtResourceUrls FLOAT, ExtFavicon INT, InsecureForms INT, RelativeFormAction INT, ExtFormAction INT, AbnormalFormAction INT, PctNullSelfRedirectHyperlinks FLOAT, FrequentDomainNameMismatch INT, FakeLinkInStatusBar INT, RightClickDisabled INT, PopUpWindow INT, SubmitInfoToEmail INT, IframeOrFrame INT, MissingTitle INT, ImagesOnlyInForm INT, SubdomainLevelRT INT, UrlLengthRT INT, PctExtResourceUrlsRT INT, AbnormalExtFormActionR INT, ExtMetaScriptLinkRT INT, PctExtNullSelfRedirectHyperlinksRT INT, numTagsInHtml INT, numTagsInHead INT, numTagsInMain INT, numTagsInBody INT, pctImgTags FLOAT, totalWidth FLOAT, totalHeight FLOAT, IMredMean FLOAT, IMredStdDev FLOAT, IMgreenMean FLOAT, IMgreenStdDev FLOAT, IMblueMean FLOAT, IMblueStdDev FLOAT, IMalphaChannel INT, IMgamma FLOAT, numBoldTags INT, averageFontWeight FLOAT, mostUsedFont TEXT, averageFontSize FLOAT, numStyles INT, mostUsedStyle TEXT, pctItalics FLOAT, pctUnderline FLOAT, favicon INT)
      
#. hashes: CREATE TABLE hashes (phash TEXT, dhash TEXT, url TEXT)
|

* screenshotDir=None
      A path to a directory with screenshots. This is useful to minimize necessary scraping and avoid duplicate screenshots if you already have screenshots and associated urls in urlFile.
* htmlDir=None
      Similarly, htmlDir is a path to a directory with html files, and is useful for minimizing necessary scraping
* cssDir=None
      cssDir also has a similar function, and is a path to a directory with css files and can be passed as an argument to minimize scraping as long as the url file passed relates to the ids of the files.
* cursor=None
      An sqlite3 cursor attribute; if you pass a database object, a cursor object will be initialized with an associated database, so no need to pass a preexisting one.
* conn=None
      An sqlite3 connection attribute; similar to the cursor attribute, where if you pass a database object, a connection object will be initialized with an associated database, so no need to pass a preexisting one.
* BS=None
      An object representing an instance of Beautiful Soup; an html parser useful for web scraping and analysis. Updated using the initializeBS() method for every url in urlFile (if validated).
* id=0
      Used for naming filenames, databases, and selecting urls. Defaults to 0, but if you are resuming the script from where you left off (existing files/database) the script will attempt to determine the id for you (alternatively you can manually pass a value as well).
* classVal=Instance.missing_value()
      By default, the classVal attribute (which is used for dataset creation and therefore classification) is set to Instance.missing_value(), but it can be changed by updating it accordingly in your analyzer() function (you just have to know your class values, as well as when to update them in regards to the current file position in the open url file).
* errors={}
      A dictionary that stores urls and errors as key value pairs. Updates the errors sqlite3 table if database functionality is enabled.
* allFeatures=[]
      An array of dictionaries composed of ALL features (all name:value pairs generated from all analyzers).
* allFeatureNames={}
      A dictionary that stores the combined featureNames of ALL analyzers (in name:stringWekaDataType format).
      
The scrape class also has 7 methods in addition to __init__():

* closeSelenium(self)
      Calls self.driver.close() and self.driver.quit(). Should be called once the scraping process has finished.
* initializeBS(self, html)
      Creates a Beautiful Soup instance BS. Not called with initializeAll() as it cannot parse html without having any html as input. Typically called after storing the driver.page_source in an html variable.
* shorten(self, url)
      Uses pyshorteners to create a shortened version of the url with 5 unique characters at the end; those characters are then incorporated into the filename in a _<self.id>_<5 characters>.png filename that can be reverse engineered to get the url from a filename with a specific id (database functionality makes this process even easier, and is recommended).
* expand(self, urlID)
      Takes the 5 characters used at the end of a filename (excluding .png) as input, and expands and returns the original url.
* generateFilename(self, url)
      A convenience method for generating a filename to name all the files associated with a website (returns a filename structured as _<self.id>_<5 characters>).
* siteValidation(self, url)
      Check to make sure there is no error upon making a website request; specifically checks for errors while trying to access the website and it's url using Selenium, as well as checks for a 404 error using the requests library.
* saveScreenshot(self, url)
      Takes a url as input, uses selenium.screenshot in combination with a workaround involving website width, height, and automated scrolling to screenshot the entire website. Screenshot can be found in the <dataDir>/screenshots directory and uses the naming structure returned by the generateFilename method.
* exitHandler(self, exctype, value, traceback)
      A method that closes down the main scraping loop and cleanly shuts down the program in the case of an exception (for example, if you lose internet connection).
* resume(self, id=False)
      Resumes the program if it crashes and values were stored in a database (by iterating through the database and adding values to attributes accordingly). If an id is passed, the method can also be used to add values related to a specific id in the database, which is useful, especially in the context of a duplicate url.
* getTime(self)
      Gets the current time based on time zone; only called if database functionality is enabled.
* checkInternet(self, validated=False)
      A method that attempts to access https://www.google.com using the Selenium instance and checks the status of the request accordingly. If it isn't the expected response (an error code or an exception), a SystemError is raised. Called inside the goFish scraping loop if siteValidation doesn't pass, the check can be disabled by passing True for the validated parameter.
* goFish(self)
      Automates the scraping process; iterates over the provided urlFile, validates the url (based on checks from Selenium and Requests), and parses html, css, and screenshots, initializes BS and the database, gets the time, and passes all the initialized data (dataDir, driver, database, BS, cursor, connection, id, classVal, and errors) in a dictionary, resources.
      
page
----

The page class is an example class that inherits from the base analyzer class, with the purpose of scraping the page-based features outlined by the research here: https://github.com/xanmankey/FishingForPhish/blob/main/research/FishingForPhish.md. It recieves the resources dictionary from the goFish() method of the scrape class, uses the information to scrape the necessary features, and returns the updated resources objects in addition to the new attributes, features and featureNames
An example of using the page class to print a set of full pageFeatures can be seen below (**Remember that selenium webdriver MUST be initialized first before scraping, and remember to close it AFTER scraping!**).

.. code-block:: python

   from classes import page
   
   # Instance of the scrape class, where class value is equal to the 0-indexed class value
   # In the context of this research, "Legitimate"
   fisher = scrape(urlFile="data/urls.txt",
        dataDir="data",
        driver=run.driver,
        classVal=0)
        
   # Initialization of the page analyzer
   pageData = page()
   fisher.addAnalyzer(pageData)

The page class creates 3 attributes:

* features=None
      A list of dictionaries, with each dictionary containing the featureNames and scraped values of each page feature for each url. The features scraped by this example class are defined at (https://thesai.org/Downloads/Volume11No1/Paper_19-Malicious_URL_Detection_based_on_Machine_Learning.pdf) and the related research can be found at (https://www.sciencedirect.com/science/article/abs/pii/S0957417418302070).
* featureNames=A long dictionary; can be found at the link above
      A dictionary containing key-value pairs of name:stringWekaDataType (remember that weka data types can be found here: https://waikato.github.io/weka-wiki/formats_and_processing/arff_stable/) for the scraped features of the class. Only initialized once.
* classVal=Instance.missing_value()
      The classVal regarding the url. Defaults to nan, or a "?" value in a .arff file. If you want to update the classVal, you NEED to know the class value of each url so you can update the value accordingly and pass it back to goFish() using the resources dictionary. 
      
The page class inherits inherits the name method (and **requires** the creation of the analyze method) from the analyzer class:

* analyze(self, url, filename, urlNum, resources)
      Searches through the html of a url to populate the features list accordingly; uses and updates the values in the resources array. The filename value is passed, as it may be used in other analyzer classes (for example in the image class), but it isn't used in the page class.

image
-----

The image class is an example class that inherits from the base analyzer class, with the purpose of scraping the page-based features outlined by the research at https://github.com/xanmankey/FishingForPhish/tree/main/research; each feature can be categorized under the layout, style, or other category).
An example of using the image class in tandem with the goFish() can be seen below (**Again, don't forget about initialization and shutdown!**).

.. code-block:: python

   from classes import image
   
   # Initialization of the image analyzer
   # If imageData is run with the HASH=True parameter then the phash and dhash ImageHash algorithms will be run and the hashes table will be updated
   imageData = image(HASH=True)
   fisher.addAnalyzer(imageData)

The image class shares the same attributes as the page class. The features attribute (along with the features) for the class is defined below:

* features=None
      Same structure as the features attribute of the page class. Features can be found below (where RGB color values are used, and IM indicates a feature that imagemagick was used to collect):      
|
#. numTagsInHtml: Number of tags DIRECTLY (does not include nested tags) inside the HTML tag
#. numTagsInHead: Number of tags directly inside the Head tag
#. numTagsInMain: Number of tags directly inside the Main tag
#. numTagsInBody: Number of tags directly inside the Body tag
#. pctImgTags: Percentage of all tags that are image tags
#. totalWidth: Total width of the website (in px)
#. totalHeight: Total height of the website (in px)
#. IMredMean: The mean red value of the full website screenshot
#. IMredStdDev: The mean red standard deviation of the full website screenshot
#. IMgreenMean: The mean green value of the full website screenshot
#. IMgreenStdDev: The mean green standard deviation of the full website screenshot
#. IMblueMean: The mean blue value of the full website screenshot
#. IMblueStdDev: The mean blue value of the full website screenshot
#. IMalphaChannel: A binary; checking if imagemagick identified an alpha channel or not from the full website screenshot.
#. IMgamma: The gamma value of the full website screenshot.
#. numBoldTags: The number of tags that have a font-weight property greater than the normal, 400.
#. averageFontWeight: The total font-weight divided by the number of tags with a font-weight (so all with text).
#. mostUsedFont: The most common font used throughout all tags with the font-family property.
#. averageFontSize: The total font size (in px) divided by the number of tags with the font-size property.
#. numStyles: The number of tags with a font-style or text-decoration value that isn't equal to normal or none.
#. mostUsedStyle: The most common style through all tags with a font-style or text-decoration value that isn't equal to normal or none.
#. pctItalics: The percentage of style tags that have the italic property set.
#. pctUnderline: The percentage of style tags that have the underline property set.
#. favicon: Checks whether a link tag with the rel="icon" property exists
|
* featureNames=A long dictionary; can be found at the link above
      The featureNames can be found above as the keys for the features array; the featureNames dictionary follows the featureName:stringWekaDataType structure.
* classVal=Instance.missing_value()
      The classVal regarding the url. Defaults to nan, or a "?" value in a .arff file. If you want to update the classVal, you NEED to know the class value of each url so you can update the value accordingly and pass it back to goFish() using the resources dictionary. 
* HASH=False
      A binary value that indicates whether you want to store hash values or not in the hashes table; elaborated upon more below with the imageHash function.
* hashes=[]
      An array to prevent hash functionality being locked behind database functionality; requires an alternate method of storage to save session data, for example a csv file, as the data is not written to one by default.

The image class also has 3 other methods in addition to __init__() and analyze():

* getImagemagickData(self, result)
      Runs the imagemagick identify -verbose <datadir>/screenshots/<filename> + .png as a subprocess, where color, brightness, and other resulting data is returned from the screenshot of the website.
* imageHash(self, url, filename)
      Runs the perceptual and difference hash algorithms from the ImageHash library IF database functionality is enabled. Inserts resulting data into the hashes table, which couldbe used for future research once enough data has been collected.
* analyze(self, url, filename, urlNum, resources)
      Similar to the page class, except uses the getImagemagickData function to get features from website screenshots (imagemagick is NOT a required dependency found in requirements-txt, which means that the image class will NOT be able to run without it, but it can be installed as a command-line tool; note that analyzers may rely on other software, so install as necessary) and has the imageHash function that can be called if the HASH attribute is set to True; updates the hashes table in the database (if enabled) with perceptual and differential hash values for possible use in future early detection.
      
saveFish
--------

The saveFish class helps tie the data together, with methods that create .arff files from the data, oversample the data, perform feature selection, and classify the data. 
An example of using the data class to create the datasets (one dataset for each analyzer, in addition to a possible ranked dataset based on feature selection, a full dataset where all analyzer features are combined, and a rankedBalanced and fullBalanced dataset where a WEKA oversampler, SMOTE, is used to balance the classes) and classify the ranked datasets is seen below:

.. code-block:: python

   from classes import saveFish
   
    # Data Combination
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

The saveFish class inherits all attributes from the initialize and scrape classes, updates 3 attributes using values from the scrape class (specifically analyzers, allFeatures and allFeatureNames are initialized to fisher (the example name for the instance of the scrape class).analyzers, fisher.allFeatures, and fisher.allFeatureNames) and declares 5 new ones:

* datasets={}
      Where datasets is a dictionary of stringDatasetName:datasetObject that is updated throughout and many methods rely on.
* analyzers=[] (see above; the value of analyzers should be passed from your created instance of the scrape class)
      Where analyzers is a list of created analyzers objects.
* newDatasetOptions={"full":True, "ranked":True, "fullBalanced":True, "rankedBalanced":True}
      A list of options for the datasets that you want to create; initializes all values to True.
* allFeatures=None (see above)
      A combination list composed of dictionaries with the pageFeature + imageFeature values.
* allFeatureNames=None (see above)
      A dictionary composed of allFeatureNames in the featureName:stringWekaDatatype. 
      
The data class also has 5 methods in addition to __init__() and createDatasets():

* FS(self)
      Uses the feature selection process followed in the research at https://github.com/xanmankey/FishingForPhish/tree/main/research to select the top ranked features (the correlational, information gain, and chiSquared ranked feature selection methods are run and the output is stored in arrays, of which the index values are then used (with 0 being the highest value and len(array - 1) being the lowest value) to calculate the top overall ranked features). Features are selected by getting the features from all instances of the analyzer class (by iterating through the analyzers list).
* generateInstances(self)
      Uses the SMOTE weka filter to oversample the minority class. The newDatasetOptions attribute is used to determine which if the new datasets to oversample (which results in the creation of a NEW dataset, rather than just updating the old one).
* closePWW3(self)
      A function that saves all datasets in the datasets attribute at dataDir/datasets/(dataset) and then closes jvm afterward.
* attributeCreation(self, featureNames, class1="Legitimate", class2="Phishing")
      A class that creates and returns a list of attributes for creating datsets. Takes 3 parameters, featureNames (where you can pass the appropriate featureNames attribute), and class1 and class2, which are class names for the created datasets (where you can pass the classVal attributes).
* classify(self)
      A function for classifying the resulting datasets set to True in newDatasetOptions, in addition to the datasets from the analyzers attribute. Specifically the J48, Jrip, and Naive Bayes models were used for the purposes of this research, but many more can easily be added for customization. A model output file is saved in the output directory, and model percentage and confusion matrices are returned as output. Note that if there are NO non-null class instances, classification might not succeed.
* createDatasets(self)
      The createDatasets method is a combination method that uses the list of analyzers, newDatasetOptions, and calls class methods to create datasets (a dataset for each analyzer, and a dataset for each newDatasetOption set to True if possible). Note that it doesn't call the classify class method, which needs to be called seperately after the createDatasets method is called.
      
Example (FINALLY)
-----------------

This example is the result of all the code snippets above, and is also included in the class file itself for standalone usage.

.. code-block:: python
   
   from classes import startFishing, scrape, page, image, saveFish 
   
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

.. autosummary::
   :toctree: generated
