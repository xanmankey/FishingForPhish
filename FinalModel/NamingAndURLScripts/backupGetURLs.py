# In case you name the files incorrectly (or struggle to reverse engineer the image names using rename.py)
# You can use string comparison and compare against the actual URLs
from difflib import SequenceMatcher
import os
import sys

if len(sys.argv) != 2:
    print("Usage: backupRename.py yourFileForNames.txt")

with open('Phishlinks.txt', 'r') as f:
    Full = f.readlines()
    with open(sys.argv[1], 'w') as r:
        for file in os.listdir("PhishScreenshots"):
            lineNum = 0
            similarity = {}
            for line in Full:
                similarity[lineNum] = SequenceMatcher(a=line,b=file).ratio()
                lineNum += 1
            # Write the corresponding line in newFiles.txt
            value = list(similarity.values())
            position = value.index(max(value))
            keys = list(similarity.keys())
            r.write(Full[keys[position]])
