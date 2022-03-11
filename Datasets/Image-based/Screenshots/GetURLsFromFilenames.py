import os
import sys

if len(sys.argv) != 2:
    print("Usage: GetURLsFromFilenames.py yourFileForURLs.txt")

with open("URLs.txt", "w") as f:
    # Input the directory that you want to get the URLs of
    # Assuming that the directory uses the naming conventions that I chose,
    # Write the url to the file "URLs.txt"
    for filename in os.listdir(sys.argv[1]):
        # The 2 lines commented out below are useful for trimming if whitespace is an issue
        filename = filename.replace('\n', '')
        filename = filename.replace('\t', '')
        filename = filename.replace(' ', '')
        filename = filename.replace('^', ',')
        filename = filename.replace('`', '%')
        filename = filename.replace('lHash', '{')
        filename = filename.replace('rHash', '}')
        filename = filename.replace('#', ':')
        filename = filename.replace('bSlash', '/')
        filename = filename.replace('.jpg', '')

        f.write(filename)
        f.write('\n')
