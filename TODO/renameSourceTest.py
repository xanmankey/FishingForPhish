import short_url
import os


# Fix naming conventions to be in line with these (simpler; integrates with databases better)
if __name__ == "__main__":
    for i in range(1, 188):
        fileEncode = short_url.encode_url(i)
        for filename in sorted(os.listdir("static/legitSource/")):
            os.rename("static/legitSource/" + filename, "static/legitSource/" + "_" + str(i) + "_" + fileEncode + ".html")
            break