API
===

The following section provides examples and goes into more depth about using FishingForPhish.
More examples and documentation will be added when time allows. 
The API examples are currently broken down into example code snippets (*which won't always be able to stand alone*) and a simple combined example at the end of the documentation.

initialize
----------

In order to scrape, parse html, or work with datasets, you first have to initialize the library.
You can do that by creating an instance of the class initialize and then calling the method initializeAll.

.. code-block:: python

   from classes import startFishing
   
   run = startFishing(dataDir="data")
   run.initializeAll()
   
   # Additionally call .closeSelenium() to close and quit the webdriver process
   run.closeSelenium()

The initialize class has 4 attributes:

* dataDir=None
      The home directory for the scraped files. This includes a screenshots, html, css, and datasets directory. If left None, an empty
      "data" directory following the file system structure will be created.
* driver=None
      The instance of Selenium Webdriver. In most cases, this will be None (unless a webdriver instance has already been created; in which case
      the initialization process for it can be skipped).
* jvmToggle=False
      A toggle attribute that follows the state of the jvm (as python weka wrapper currently doesn't support checking the current run state of the jvm). A value should **NOT** be passed for this variable, otherwise functions reliant on the jvm can be called before the jvm's initialization.
* BS=None
      The instance of Beautiful Soup. In most cases, this will also be None (unless a Beautiful Soup object has been created). For the purposes of this library,       initializing a Beautiful Soup instance requires html, which is why the initializeBS() method of the initialize class is not included in the                     initializeAll() method.
      
The initialize class has 5 methods in addition to __init__():

* installResources(self)
      Installs potentially-useful resources used during the methodology of the research here: TODO. This includes the chiSquaredAttributeEval feature selector for WEKA, the SMOTE oversampler for WEKA, and the Wayback Machine add-on for Firefox.
* initializeSelenium(self, add_ons=None)
      Creates the Selenium instance. A list of paths to add_ons (.xpi files) can be passed to enhance the scraping experience. The wayback_machine add-on is added to the webdriver instance with the method initializeAll().
* initializePWW3(self, jvmOptions)
      Starts JVM with a list of optional parameters, jvmOptions (some default options, system_cp and packages, are passed with the initializeAll() method). The attribute jvmToggle is updated to be True.
* initializeBS(self, html)
      Creates a Beautiful Soup instance BS. Not called with initializeAll() as it cannot parse html without having any html as input. Typically called after storing the driver.page_source in an html variable.
* initializeAll(self, jvmOptions=["system_cp", "packages"], add_ons=['wayback_machine-3.0-fx.xpi'])
      As used in the example above, sequentially handles logging accordingly (to avoid console spam), calls initializePWW3 (with the default options, system_cp and packages. Packages must be True if you want to use any packages), installResources(), and then initializeSelenium using the specified add_ons, which defaults to the installed 'wayback_machine-3.0-fx.xpi' from the call to installResources. This method can be adapted, but currently defaults to using the settings used during the research at TODO. 

scrape
------

The scrape class is a useful compilation of all the scraping-related methods used, from saving a screenshot of a full webpage to checking if a site responded with no errors. There is no encompassing method (such as initializeAll()) in the scrape class, but the comprehensive __init__ function and variety of supporting methods provide a lot of inheritable functionality. You will probably not want to create an instance of the scrape class, as it serves as a base initialization class to be inherited from, and cannot be used effectively standalone.

The scrape class inherits all attributes from the initialize class and declares 8 new ones:

* urlFile
      A required argument; the path to a .txt file with a url on each line.
* database=None
      An optional (but recommended) argument; database functionality (especially with a filesystem mirroring that of integer primary keys) is useful for carrying results over, storing and accessing data, and provides more opportunities (for example hash storage) for future classification. If you input a valid database (even if empty), 7 tables are created (unless they already exist) including:
|
#. metadata: CREATE TABLE metadata (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT UNIQUE, time INT, classification TEXT)
      
#. pageData: TODO ALL OF THIS
      
#. errors:
      
#. imageData:
      
#. otherData:
      
#. allFeatures:
      
#. hashes:

|

* screenshotDir=None
      A path to a directory with screenshots. This is useful to minimize necessary scraping and avoid duplicate screenshots if you already have screenshots and associated urls in urlFile.
* htmlDir=None
      Similarly, htmlDir is a path to a directory with html files, and is useful for minimizing necessary scraping
* cssDir=None
      cssDir also has a similar function, and is a path to a directory with css files and can be passed as an argument to minimize scraping as long as the url file passed relates to the ids of the files.
* cursor=None
      An sqlite3 cursor attribute; if you pass a database object, a cursor object will be initialized with an associated database, so no need to pass a preexisting one.
* id=0
      Used for naming filenames, databases, and selecting urls. Defaults to 0, but if you are resuming the script from where you left off (existing files/database) the script will attempt to determine the id for you (alternatively you can manually pass a value as well).
* errors={}
      A dictionary that stores urls and errors as key value pairs. Updates the errors sqlite3 table if database functionality is enabled.
      
The scrape class also has 7 methods in addition to __init__():

* closeSelenium(self)
      Calls self.driver.close() and self.driver.quit(). Should be called once the scraping process has finished.
* shorten(self, url)
      Uses pyshorteners to create a shortened version of the url with 5 unique characters at the end; those characters are then incorporated into the filename in a _<self.id>_<5 characters>.png filename that can be reverse engineered to get the url from a filename with a specific id (database functionality makes this process even easier, and is recommended).
* expand(self, urlID)
      Takes the 5 characters used at the end of a filename (excluding .png) as input, and expands and returns the original url.
* generateFilename(self, url)
      A convenience method for generating a filename to name all the files associated with a website (returns a filename structured as _<self.id>_<5 characters>).
* saveScreenshot(self, url)
      Takes a url as input, uses selenium.screenshot in combination with a workaround involving website width, height, and automated scrolling to screenshot the entire website. Screenshot can be found in the <dataDir>/screenshots directory and uses the naming structure returned by the generateFilename method.
* siteValidation(self, url)
      Check to make sure there is no error upon making a website request; specifically checks for errors while trying to access the website and it's url using Selenium, as well as checks for a 404 error using the requests library.
* getTime(self)
      Gets the current time based on time zone; only called if database functionality is enabled.
      
page
----

The page class is for scraping the page-based features outlined by the research here: TODO. It relies on many of the methods provided by the scrape class.
An example of using the page class to print a set of full pageFeatures can be seen below (**Remember that selenium webdriver MUST be initialized first before scraping, and remember to close it AFTER scraping!**).

.. code-block:: python

   from classes import page
   
   pageData = page(urlFile="data/urls.txt", dataDir="data", driver=run.driver, BS=run.BS)
   pageData.pageScrape()
   print(pageData.pageFeatures)

The page class inherits all attributes from the initialize and scrape classes and declares 1 more:

* pageFeatures=None
      A 2D list containing the values of each page feature for each url. The scraped features are defined below:
|

#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a

|

The page class also has 1 other method in addition to __init__() and pageScrape():

* getPageFeatures(self, url)
      Searches through the html of a url to populate the paegFeatures list accordingly.

image
-----

The image class is similar to the page class, where it's primary use is for scraping image-based features (the justification for feature selection can be found in the research at TODO; each feature can be categorized under the layout, style, or other category).
An example of using the image class to print a set of full imageFeatures can be seen below (**Again, don't forget about initialization and shutdown!**).

.. code-block:: python

   from classes import image
   
   imageData = page(urlFile="data/urls.txt", dataDir="data", driver=run.driver, BS=run.BS)
   # If imageScrape is run with the HASH=True parameter then the phash and dhash ImageHash algorithms will be run
   # and the resulting hashes will be inserted in the hashes table for future use
   imageData.imageScrape(HASH=True)
   print(pageData.imageFeatures)
   

The image class inherits all attributes from the initialize and scrape classes and declares 1 more:

* imageFeatures=None
      A 2D list containing the values of each page feature for each url. The scraped features are defined below:
|

#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a
#. a

|

The image class also has 3 other methods in addition to __init__() and imageScrape():

* getImageFeatures(self, filename)
      Searches through the html of a url to populate the pageFeatures list accordingly.
* getImagemagickData(self, result)
      Runs the imagemagick identify -verbose <datadir>/screenshots/<filename> + .png as a subprocess, where color, brightness, and other resulting data is returned from the screenshot of the website.
* imageHash(self, url, filename)
      Runs the perceptual and difference hash algorithms from the ImageHash library IF database functionality is enabled. Inserts resulting data into the hashes table, which couldbe used for future research once enough data has been collected.
      
data
-------

The data class helps tie the data together, with methods that create .arff files from the data, oversample the data, perform feature selection, and classify the data. 
An example of using the data class to create and classify the ranked (selected feature) datasets is seen below

.. code-block:: python

   from classes import data
   
    # Data Combination
    DC = data(
        pageFeatures=pageData.pageFeatures,
        imageFeatures=imageData.imageFeatures,
        urlFile="data/urls.txt",
        dataDir="data")
    DC.createDatasets()
    DC.classify()

The data class inherits all attributes from all previously defined classes and declares 25 new ones, with each attribute falling into one of four categories (with the exception of the allFeatures attribute); dataset, accuracy, false positive, or false negatives (the attributes are grouped below into sets of 4 by their dataset attribute; note that all datasets are saved as <dataDir>/datasets/<filename> + ".arff".):

* pageDataset
      A dataset object (see python weka wrapper's documentation here for more information: https://fracpete.github.io/python-weka-wrapper/weka.core.html#module-weka.core.dataset) created from the pageFeatures array.
      
      * pageAccuracy
         The classification accuracy of the pageDataset.
      * pageFP
         The false positive percentage of the pageDataset.
      * pageFN
         The false negative percentage of the pageDataset.
* imageDataset
      A dataset object created from the imageFeatures array.
      
      * imageAccuracy
         The classification accuracy of the imageDataset.
      * imageFP
         The false positive percentage of the imageDataset.
      * imageFN
         The false negative percentage of the imageDataset.
* combinedDataset
      A dataset object created from both the top ranked (in regards to feature selection) pageDataset and imageDataset. 
      
      * combinedAccuracy
         The classification accuracy of the combinedDataset.
      * combinedFP
         The false positive percentage of the combinedDataset.
      * combinedFN
         The false negative percentage of the combinedDataset.
* combinedBalancedDataset
      A resulting dataset object from oversampling performed on the combinedDataset (in order to balance the classes).
      
      * combinedBalancedAccuracy
         The classification accuracy of the combinedBalancedDataset.
      * combinedBalancedFP
         The false positive percentage of the combinedBalancedDataset.
      * combinedBalancedFN
         The false negative percentage of the combinedBalancedDataset.
* fullDataset
      A dataset object created from all the pageDataset and imageDataset attributes and instances. 
      
      * fullAccuracy
         The classification accuracy of the fullDataset.
      * fullAccuracyFP
         The false positive percentage of the fullDataset.
      * fullAccuracyFN
         The false negative percentage of the fullDataset.
* fullBalancedDataset
      A resulting dataset object from oversampling performed on the fullDataset.
      
      * fullBalancedAccuracy
         The classification accuracy of the fullBalancedDataset.
      * fullBalancedAccuracyFP
         The false positive percentage of the fullBalancedDataset.
      * fullBalancedAccuracyFN
         The false negative percentage of the fullBalancedDataset.
* allFeatures
   A combination list composed of the pageFeature + imageFeature values.
      
The data class also has 5 methods in addition to __init__() and createDatasets():

* FS(self, page=True, image=True)
      Uses the feature selection process followed in the research at TODO to select the top ranked features (the correlational, information gain, and chiSquared ranked feature selection methods are run and the output is stored in arrays, of which the index values are then used (with 0 being the highest value and len(array - 1) being the lowest value) to calculate the top overall ranked features). Parameters for selecting page and/or image features are available, and defaults to returning a length 2 array of the top ranked page and then image features respectively (the numerical index of the attribute is returned).
* generateInstances(self, combined=True, full=True)
      Uses the SMOTE weka filter to oversample the minority class. 2 optional parameters default to True, combined and full, each of which represent the dataset that you want to oversample (note that oversampling does not edit a dataset, but rather generates a new one).
* closePWW3(self, image=True, page=True, combined=True, combinedBalanced=True, full=True, fullBalanced=True)
      A function that saves all the altered datasets in dataDir/datasets/(dataset) and closes jvm. There are 6 predefined arguments, each of which True, representing the datasets that you want to save. A convenience method for generating a filename to name all the files associated with a website (returns a filename structured as _<self.id>_<5 characters>).
* classify(self, image=True, page=True, combined=True, combinedBalanced=True, full=True, fullBalanced=True)
      A function for classifying the resulting datasets. Specifically the J48, Jrip, and Naive Bayes models were used for the purposes of this research, but many more can easily be added for customization. A model output file is saved in the output directory, and model percentage and confusion matrices are returned as output.
      
Example (FINALLY)
-----------------

This example is the result of all the code snippets above, and is also included in the class file itself for standalone usage.

.. code-block:: python
   
   from classes import initialize, page, image, data 
   
   def main():
      # Initialization
      run = initialize()
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
      DC = data(
         pageFeatures=pageData.pageFeatures,
         imageFeatures=imageData.imageFeatures,
         urlFile="data/urls.txt",
         dataDir="data")
      DC.createDatasets()
      DC.classify()

      # Where FP stands for False Positive and FN for False Negative
      print(DC.combinedBalancedAccuracy)
      print(DC.combinedBalancedFP)
      print(DC.combinedBalancedFN)
      print(DC.fullAccuracy)
      print(DC.fullFP)
      print(DC.fullFN)
      
      DC.closePWW3()
      run.closeSelenium()


   if __name__ == "__main__":
      main()

.. autosummary::
   :toctree: generated
