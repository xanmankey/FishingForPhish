Usage
=====

.. _installation:

Installation
------------

Prerequisites
^^^^^^^^^^^^^

**In order to use this library, a java deployment kit (JDK) needs to be installed, and the JAVA_HOME environmental variable needs to be set; note that java-17-oracle was used for the development of this library, and therefore is the recommended JDK version.**

In order to setup java-17-orcacle, follow the steps listed below (please note that the below only accounts for the linux (specifically WSL) installation of java-17-oracle, I haven't had time to test installation on other OS yet):

* Download and extract the OS-appropriate java development kit from https://www.oracle.com/java/technologies/javase/jdk17-archive-downloads.html (in the case of a WSL build, I downloaded the Linux x64 Compressed Archive)
* Set the JAVA_HOME environmental variable to the installation directory using the below command:

.. code-block:: console

   $ export JAVA_HOME = "path/to/your/installation/here"

Additionally, the below is recommended:

* Knowledge of machine learning (as well as an api to experiment with; WEKA was primarily used throughout this project)
* Prior programming background (as well as experience with an IDE)
* A positive mindset (yeah, it's kinda hard to do data analysis without one)
* Knowledge of positive web-scraping practices (try not to consume too many server resources; know website policies beforehand if possible)

Installation (via pip)
^^^^^^^^^^^^^^^^^^^^^^

To use FishingForPhish, first install it using pip:

.. code-block:: console

   $ pip install FishingForPhish

Then you should have access to the API in classes.py. 

Installation (from source)
^^^^^^^^^^^^^^^^^^^^^^^^^^

Alternatively, the library can be installed from source by cloning the github repository using the command

.. code-block:: console

   $ git clone https://github.com/xanmankey/FishingForPhish.git

How to use it?
--------------

A common usage example can be found below, where scraping is initialized, the scraping filesystem is automatically setup, 
2 analyzers (page and image) automatically generate features, a variety of datasets are automatically created, classification algorithms are run 
on the datasets, and then the scraping session and machine learning wrapper are closed and the program exits.

.. code-block:: python

    from classes import startFishing, scrape, page, image, saveFish
    
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
    
----

Specifics regarding usage cases, classes, methods, and attributes can all be found in the API section of the documentation
