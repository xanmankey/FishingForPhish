Usage
=====

.. _installation:

Installation
------------

**🛈 A word of caution before attempting to replicate my methodology, your data may be at risk if you don't take proper precautions, due to the nature of phishing websites. I used a VPN (ProtonVPN + OpenVPN protocol) and an Ubuntu VM in tandem to attempt to minimize possible security threats.**

Prerequisites
^^^^^^^^^^^^^

**Python Weka Wrapper3: requires a java deployment kit (JDK) and a set JAVA_HOME environmental variable among other things; the full installation process for python weka wrapper3 can be found at https://fracpete.github.io/python-weka-wrapper3/install.html, but the process for the installation of the java-11-oracle (the oracle version tested with this library and recommended by the devs behind Python-Weka-Wrapper3) and initialization of JAVA_HOME can be found below.**

* Download and extract the OS-appropriate java development kit from https://adoptium.net/temurin/releases (in the case of an WSL-Ubuntu build, I downloaded the Linux x64 Compressed Archive)
* Set the JAVA_HOME environmental variable to the installation directory using the below command:

.. code-block:: console

   $ export JAVA_HOME="path/to/your/installation/here"
   
* Also, I was unable to get one of the libraries python-weka-wrapper3 is reliant on to install without running the below command. According to the official library, it's not required, but it was the only way I was able to make the installation process consistent, so remember to run it as well before running the pip install python-weka-wrapper3 command!:

.. code-block:: console

   $ pip install git+https://github.com/LeeKamentsky/python-javabridge.git@master

**Selenium Webdriver: requires a valid Selenium instance and a valid Webdriver (Firefox is reccomended as of right now, as the module doesn't have support for other drivers, although it could easily be added), see here for more information: https://www.selenium.dev/documentation/webdriver/getting_started/, and make sure you use compatible versions!**
   
**The imagemagick package is required to use the example imageAnalyzer analyzer if so desired. For more OS-specific information regarding installation see here: https://imagemagick.org/script/download.php**

Installation (via pip)
^^^^^^^^^^^^^^^^^^^^^^

To use FishingForPhish, first install it using pip:

.. code-block:: console

   $ pip install FishingForPhish

Then you should have access to the API in classes.py. 

Installation from source (not recommended unless you want to download the initial research documents)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The library can be cloned either by downloading a zip or cloning the github repository using the command below:

.. code-block:: console

   $ git clone https://github.com/xanmankey/FishingForPhish.git
   
TODO: From there, I'm actually not sure how to install it from source using setup.cfg and pyproject.toml, or what the best way to allow for installation from source is
   
Errors (at least that I'm aware of)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you get an error regarding python-javabridge and numpy when trying to install from requirements or requirements-dev.txt, specifically:
..warning:
   ModuleNotFoundError: No module named 'numpy'
   
you may have forgotten to run the below command:

.. code-block:: console

   $ pip install git+https://github.com/LeeKamentsky/python-javabridge.git@master
   
If you get a "TypeError: expected str, bytes or os.PathLike object, not NoneType" error when installing javabridge, you most likely forgot to install the JDK or set the JAVA_HOME incorrectly. In my case, the Github forum here helped me out: https://github.com/LeeKamentsky/python-javabridge/issues/152

Resources
^^^^^^^^^

**Original Phishing-Legitimate datasets**

- Phishing-legitimate dataset (https://doi.org/10.17632/h3cgnj8hft.1).
- Phishing screenshots (https://phishstats.info/). I only took screenshots of phishing sites with phish scores of 7 and up (where 10 is defined as "OMG PHISHING" by PhishStats) to help differentiate phishing sites from non-phishing sites for my dataset.
- Legitimate screenshots (https://www.domcop.com/top-10-million-domains). I selected websites ranked from 6.39/10 to 10/10 by Open Page Rank.

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
