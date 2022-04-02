# In case you name the files incorrectly (or struggle to reverse engineer the image names using rename.py)
# You can use string comparison and compare against the actual URLs
from difflib import SequenceMatcher
import os
import sys
from rename import URLsToFilenames

# You most likely won't need this file; I just had to create it as a workaround to accidentally changing / to _, I didn't realize 
# that _ was a safe url character. That ruined a lot of my URLs
if len(sys.argv) != 4:
    print("Usage: python backupRename.py originalLinks.txt yourFileForNewNames.txt directoryToRenameFiles")
    print("Requires a file with the original links")

with open(sys.argv[1], 'r') as f:
    Full = f.readlines()
    with open(sys.argv[2], 'w') as r:
        for file in os.listdir(sys.argv[3]):
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

        URLsToFilenames(sys.argv[2])
        with open("filenames.txt", "r") as rename:
            names = rename.readlines()
            i = 0
            for file in os.listdir(sys.argv[3]):
                names[i] = names[i].replace('\n', '')
                os.rename(sys.argv[3] + '/' + file, sys.argv[3] + '/' + names[i])
                i += 1
