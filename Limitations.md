# DNF (the purpose of this file is to showcase limitations and issues with my methodology that I noticed (for the purpose of peer review + future work)
Try formatting this as Markdown if txt isn't working
Then begin phase 2, reformatting and reworking code for Selenium Webdriver, as well as figuring out how to tie the data to the table to the model so 
my ML algorithm can grow?? Maybe? Or at the very least, figure out how to tie it to the Github repo somehow (both would be awesome).
THINGS THAT I'LL MENTION IN THE PAPER (and that I'm just noting here because I had this tab open)
LIMITATIONS (TODO)
It's difficult to take screenshots of confirmed phishing sites, as many times once they are confirmed they get taken down by the person hosting them, 
and a new one is put up. However, I couldn't find many databases with screenshots and urls for the purposes of this experiment, and I was getting a ratelimit no matter what I tried to do with PhishTank (I'm still not sure why). In hindsight, my methodology here was very short sighted... I need to figure out some way to root out the "not a valid website" I did end up manually removing some screenshots (those with personal information, screenshot errors (for example blacklisted websites, taken down websites (404 Not Found error), or the website failed to load in properly), or those that might be deemed unacceptable in a school setting; this is a school research project after all, and that may hurt the overall replicability of my method, but I did provide the reviewed datasets)
Is SMOTE ok? I wonder if it's bad to autogenerate half a dataset, but I figured I'd at least give it a shot
I was getting errors w/ Selenium webdriver and Chromedriver, so I decided to migrate to Firefox-geckodriver (for the purposes of this research)
(I'm realizing I don't have a good defense for a decent amount of my methodology, specifically my choices for feature selection and classification, and that's probably due to a lack of knowledge still).
It seems like Firefox + Selenium Webdriver has some kind of a limit put into place (50 successful .get calls? I'm not quite sure. It's annoying for big data, but can be worked around, and shouldn't be a problem for my website because Selenium only needs to run once).
FUTURE CONSIDERATIONS (TODO)
Country, IP address
OTHER NOTES (TODO)
I didn't preprocess my testing data
0 is legit, 1 is phish (the way I did it at least)

CURRENT PROBLEM: the imagefilters package generates attributes, how do I weight this appropriately?
I NEED TO REFORMAT AND FIX FS SCRIPTS
The thing that is most likely incorrect are my averaging scripts (especially for image analysis, if one filter ranks the highest, shouldn't I be using that filter?)
ASK about PctExtNullSelfRedirectHyperlinksRT
I should mention that I used the source I found here: https://pdfs.semanticscholar.org/2589/5814fe70d994f7d673b6a6e2cc49f7f8d3b9.pdf for test legitimate websites (Malicious_n_Non-Malicious URL)
Why does the Selenium web rename file method delete some files? Maybe search recycle bin? I want to get my Github out right away for use tomorrow


POST PAPER
Maybe look into CITATION.cff files
Finalize GitHub and make it public
I THINK IN ORDER TO GET MY COMBINED DATASET I'LL USE PYWEB THING OR SELENIUM WEB DRIVER TO INTERACT W/ MY WEBSITE AND INPUT DATA INTO THE RESULTS TABLE (provided .model files are what I think they are)
Remember that I replaced '/' with '_', ':' with '', and '%' with '^' for filenames (following PhishStats and WEKA naming conventions). These are the characters I have to convert
(the problem is _ are valid in urls, so I need to change all my _ naming convention so I can accurately replace characters. 
I need to test making a name conversion strategy using this info: https://stackoverflow.com/questions/1547899/which-characters-make-a-url-invalid
I think the only character I need to replace are % with ^
Also should probably mention that I did enable long path support on windows, so others might have issues downloading the github
When coding databuild.py, I need to include the file renaming for Legit and Phishing (with proper naming conventions), as the filename length and the nature of phishing urls makes it difficult, but the actual URLs might be shorter once you've redirected to the website
Also, some websites (for example https://api.whatsapp.com/) will not load/end up in timeout errors. Unfortunately, I did have to remove these websites from my training dataset. In the case of whatsapp, I replaced it with https://www.booking.com/, the next website in the list of legitimate websites that I hadn't included in my dataset