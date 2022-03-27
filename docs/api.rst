API
===

The following section provides examples and goes into more depth about using FishingForPhish.
More examples and documentation will be added when time allows.

initialize
----------

In order to scrape, parse html, or work with datasets, you first have to initialize the library.
You can do that by creating an instance of the class initialize and then calling the method initializeAll.

.. code-block:: python

   from classes import initialize
   
   initializing = initialize(dataDir="data")
   initializing.initializeAll()

The initialize class has 3 attributes:

* dataDir=None
      The home directory for the scraped files. This includes a screenshots, html, css, and datasets directory. If left None, an empty
      "data" directory following the file system structure will be created.
* driver=None
      The instance of Selenium Webdriver. In most cases, this will be None (unless a webdriver instance has already been created; in which case
      the initialization process for it can be skipped).
* BS=None
      The instance of Beautiful Soup. In most cases, this will also be None (unless a Beautiful Soup object has been created). For the purposes of this library,       initializing a Beautiful Soup instance requires html, which is why the initializeBS() method of the initialize class is not included in the                     initializeAll() method.
      
The initialize class has 4 methods in addition to __init__() and initializeAll():

* installResources(self)
      Installs potentially-useful resources used during the methodology of the research here: TODO. This includes the chiSquaredAttributeEval feature selector for WEKA, the SMOTE oversampler for WEKA, and the Wayback Machine add-on for Firefox.
* initializeSelenium(self, add_ons=None)
      Creates the Selenium instance. A list of paths to add_ons (.xpi files) can be passed to enhance the scraping experience. The wayback_machine add-on is added to the webdriver instance with the method initializeAll().
* initializePWW3(self, jvmOptions)
      Starts JVM with a list of optional parameters, jvmOptions (some default options, system_cp and packages, are passed with the initializeAll() method).
* initializeBS(self, html)
      Creates a Beautiful Soup instance BS. Not called with initializeAll() as it cannot parse html without having any html as input. Typically called after storing the driver.page_source in an html variable.

scrape
----------

The scrape class is a useful compilation of all the scraping-related methods used, from saving a screenshot of a full webpage to checking if a site responded with no errors. There is no encompassing method (such as initializeAll()) in the scrape class, but the comprehensive __init__ function and variety of supporting methods provide a lot of inheritable functionality. You will probably not want to create an instance of the scrape class, as it serves as a base initialization class to be inherited from, and cannot be used effectively standalone.

The scrape class inherits 3 attributes (dataDir, driver, and BS) and declares 8 new ones:

* dataDir=None
      The home directory for the scraped files. This includes a screenshots, html, css, and datasets directory. If left None, an empty
      "data" directory following the file system structure will be created.
* driver=None
      The instance of Selenium Webdriver. In most cases, this will be None (unless a webdriver instance has already been created; in which case
      the initialization process for it can be skipped).
* BS=None
      The instance of Beautiful Soup. In most cases, this will also be None (unless a Beautiful Soup object has been created). For the purposes of this library,       initializing a Beautiful Soup instance requires html, which is why the initializeBS() method of the initialize class is not included in the                     initializeAll() method.
* dataDir=None
      The home directory for the scraped files. This includes a screenshots, html, css, and datasets directory. If left None, an empty
      "data" directory following the file system structure will be created.
* driver=None
      The instance of Selenium Webdriver. In most cases, this will be None (unless a webdriver instance has already been created; in which case
      the initialization process for it can be skipped).
* BS=None
      The instance of Beautiful Soup. In most cases, this will also be None (unless a Beautiful Soup object has been created). For the purposes of this library,       initializing a Beautiful Soup instance requires html, which is why the initializeBS() method of the initialize class is not included in the                     initializeAll() method.
* dataDir=None
      The home directory for the scraped files. This includes a screenshots, html, css, and datasets directory. If left None, an empty
      "data" directory following the file system structure will be created.
* driver=None
      The instance of Selenium Webdriver. In most cases, this will be None (unless a webdriver instance has already been created; in which case
      the initialization process for it can be skipped).
* BS=None
      The instance of Beautiful Soup. In most cases, this will also be None (unless a Beautiful Soup object has been created). For the purposes of this library,       initializing a Beautiful Soup instance requires html, which is why the initializeBS() method of the initialize class is not included in the                     initializeAll() method.
      
The initialize class has 4 methods in addition to __init__() and initializeAll():

* installResources(self)
      Installs potentially-useful resources used during the methodology of the research here: TODO. This includes the chiSquaredAttributeEval feature selector for WEKA, the SMOTE oversampler for WEKA, and the Wayback Machine add-on for Firefox.
* initializeSelenium(self, add_ons=None)
      Creates the Selenium instance. A list of paths to add_ons (.xpi files) can be passed to enhance the scraping experience. The wayback_machine add-on is added to the webdriver instance with the method initializeAll().
* initializePWW3(self, jvmOptions)
      Starts JVM with a list of optional parameters, jvmOptions (some default options, system_cp and packages, are passed with the initializeAll() method).
* initializeBS(self, html)
      Creates a Beautiful Soup instance BS. Not called with initializeAll() as it cannot parse html without having any html as input. Typically called after storing the driver.page_source in an html variable.

.. autosummary::
   :toctree: generated

   FishingForPhish

   This is where I go more in-depth about my code and explain it (see here for an example: https://fracpete.github.io/python-weka-wrapper/api.html)

