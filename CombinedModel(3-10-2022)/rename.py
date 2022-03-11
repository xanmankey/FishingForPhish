import os
import sys

# There may be some flaws in the naming, and hashing would've been much easier, but this is what I started with
def FilenamesToURLs(directory):
    with open("URLs.txt", "w") as f:
        # Input the directory that you want to get the URLs of
        # Assuming that the directory uses the naming conventions that I chose,
        # Write the url to the file "URLs.txt"
        for filename in os.listdir(directory):
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
            filename = filename.replace('.png', '')

            f.write(filename)
            f.write('\n')


def URLsToFilenames(URLs):
    with open(URLs, "r") as f:
        with open("filenames.txt", "w") as w:
            urls = f.readlines()
            for line in urls:
                line = line.replace('\n', '')
                line = line.replace('\t', '')
                line = line.replace(' ', '')
                line = line.replace(',', '^')
                line = line.replace('%', '`')
                line = line.replace('{', 'lHash')
                line = line.replace('}', 'rHash')
                line = line.replace(':', '#')
                line = line.replace('/', 'bSlash')
                line = line + '.jpg'

                w.write(line)
                w.write('\n')     
            

def main(option, usrInput):
    if option == "0":
        FilenamesToURLs(usrInput)
    else:
        URLsToFilenames(usrInput)


if __name__ == "__main__":
    option = input("Filenames to URLs or URLs to filenames? (0 or 1)")
    if option == "0":
        fileDirectory = input("Directory with filenames: ")
        try:
            os.path.isdir(fileDirectory)
        except Exception:
            print("Invalid directory")
            exit()
        main(option, fileDirectory)
    elif option == "1":
        URLs = input("URL file: ")
        try:
            os.path.isfile(URLs)
        except Exception:
            print("Invalid file")
            exit()
        main(option, URLs)
    else:
        print("Invalid option")
        exit()