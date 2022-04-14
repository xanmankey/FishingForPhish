Usage
=====

.. _installation:

Installation
------------

Prerequisites
^^^^^^^^^^^^^

**In order to use this library, python weka wrapper3 is required. This library, in turn, depends on a java deployment kit (JDK) and a set JAVA_HOME environmental variable, as well as the Microsoft Visual C++ Build Tools; the full installation process for python weka wrapper3 can be found at https://fracpete.github.io/python-weka-wrapper3/install.html, but the process for the installation of the Microsoft Visual C++ Build Tools and the java-11-oracle (the oracle version tested with this library and recommended by the devs behind Python-Weka-Wrapper3) and initialization of JAVA_HOME can be found below.**

To install the Microsoft C++ Build Tools, run the below command (if on Ubuntu; however I also know that the build tools can also be downloaded here if using Windows, with version 15 being the version linked in the Python Weka Wrapper 3 documentation: https://www.microsoft.com/en-us/download/details.aspx?id=48159)

.. code-block:: console

   $ sudo apt-get install build-essential python3-dev


.. code-block:: console

   $ export JAVA_HOME="path/to/your/installation/here"

In order to setup java-11-orcacle, follow the steps listed below (please note that the below only accounts for a WSL-Ubuntu installation of java-11-oracle, I haven't had time to test installation on any other system yet and that you may need to restart your IDE/computer at times during the installation process in order for the JDK to be recognized):

* Download and extract the OS-appropriate java development kit from https://adoptium.net/temurin/releases (in the case of an WSL-Ubuntu build, I downloaded the Linux x64 Compressed Archive)
* Set the JAVA_HOME environmental variable to the installation directory using the below command:

.. code-block:: console

   $ export JAVA_HOME="path/to/your/installation/here"
   
Additionally, the imagemagick package is required to use the imageAnalyzer example analyzer. For more OS-specific information regarding installation see here: https://imagemagick.org/script/download.php
   
The rest of the installations required can be found as a list of commands here: https://fracpete.github.io/python-weka-wrapper3/install.html (depending on the OS; I followed the commands here specifically: https://fracpete.github.io/python-weka-wrapper3/install.html#ubuntu; in order to get graphing functionality, there may be additional steps that you will need to take).

Additionally, the below is recommended:

* Knowledge of machine learning (as well as an api to experiment with; WEKA was primarily used throughout this project)
* Prior programming background (as well as experience with an IDE)
* A positive mindset (yeah, it's kinda hard to do data analysis without one)
* Knowledge of positive web-scraping practices (try not to consume too many server resources; know website policies beforehand if possible)

In regards to accessing the mongodb database (which stores the data from the website at TODO), some great tutorials can be found below:

* Installation: https://www.digitalocean.com/community/tutorials/how-to-install-mongodb-on-ubuntu-20-04
* Usage: https://www.digitalocean.com/community/tutorials/how-to-install-mongodb-on-ubuntu-20-04

Installation (via pip)
^^^^^^^^^^^^^^^^^^^^^^

To use FishingForPhish, first install it using pip:

.. code-block:: console

   $ pip install FishingForPhish

Then you should have access to the API in classes.py. 

Installation from source (not recommended unless you want to download the initial research documents)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Alternatively, the library can be installed from source by cloning the github repository using the command

.. code-block:: console

   $ git clone https://github.com/xanmankey/FishingForPhish.git
   
Errors (at least that I know about)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you get an error regarding python-javabridge and numpy when trying to install from requirements or requirements-dev.txt, specifically:
..warning:
   ModuleNotFoundError: No module named 'numpy'
   
The setup.py of python-javabridge requires numpy, so install numpy first.
(the numpy warning might be a red-herring; I'm still trying to figure it out, more info here: https://github.com/LeeKamentsky/python-javabridge/issues/28)

How to use it?
--------------

A common usage example can be found below, where scraping is initialized, the scraping filesystem is automatically setup, 
2 analyzers (page and image) automatically generate features, a variety of datasets are automatically created, classification algorithms are run 
on the datasets, and then the scraping session and machine learning wrapper are closed and the program exits.

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
    
----

Specifics regarding usage cases, classes, methods, and attributes can all be found in the :doc:`API` section of the documentation
