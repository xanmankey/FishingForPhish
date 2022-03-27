Usage
=====

.. _installation:

Installation
------------

Precursors
^^^^^^^^^^

In order to use FishingForPhish, there are a few **recommendations**.

* Knowledge of machine learning (as well as an api to experiment with; WEKA was primarily used throughout this project)
* Prior programming background (as well as experience with an IDE)
* A positive mindset (yeah, it's kinda hard to do data analysis without one)
* Knowledge of positive web-scraping practices (try not to consume too many server resources; know website policies beforehand if possible)

Setup
^^^^^

To use FishingForPhish, first install it using pip:

.. code-block:: console

   (.venv) $ pip install FishingForPhish

Then you should have access to the API in classes.py. 

How to use it?
--------------

A common usage example can be found below, where scraping is initialized, the scraping filesystem is automatically setup, 
features are automatically generated, a variety of datasets are automatically created, classification algorithms are run 
on the datasets, and then the scraping session and machine learning wrapper are closed and the program exits.

.. code-block:: python
    from classes import initialize, page, image, combine
    
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
       DC = combine(
           pageFeatures=pageData.pageFeatures,
           imageFeatures=imageData.imageFeatures,
           urlFile="data/urls.txt",
           dataDir="data")
       DC.createDatasets()

       # Classification     
       DC.classify()

       # Exiting
       run.closeSelenium()
       
   if __name__ == "__main__":
      main()
    
----

.. code-block:: python
    from classes import initialize, page, image, combine
    
    def main():
       # Initialization
       print("test")
       
    if __name__ == "__main__":
       main()
      
----


Specifics regarding usage cases, classes, methods, and attributes can all be found in the documentation
