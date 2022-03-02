# A Backup renaming file (I figured I'd include it because I made the mistake of renaming my files to numbers, I don't imagine you will, 
# but this helped me out just in case you make that same error)
# In case you name the files incorrectly (or struggle to reverse engineer the image names using rename.py)
# You can use string comparison and compare against the actual URLs
from difflib import SequenceMatcher
import os
import sys


if len(sys.argv) != 2:
    print("Usage: backupGetURLs.py yourFileForNames.txt")

# If you want to use this with the list of the legitimate websites, just change the file input stream
with open('AllPhishLinks.txt', 'r') as f:
    Full = f.readlines()
    with open(sys.argv[1], 'w') as r:
        for file in os.listdir("LegitScreenshots"):
            lineNum = 0
            similarity = {}
            for line in Full:
                similarity[lineNum] = SequenceMatcher(a=line,b=file).ratio()
                lineNum += 1
            # Write the corresponding line in the new file of choice
            value = list(similarity.values())
            position = value.index(max(value))
            keys = list(similarity.keys())
            r.write(Full[keys[position]])
