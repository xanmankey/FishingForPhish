from setuptools import setup, find_packages
import pathlib

repo = pathlib.Path(__file__).parent.resolve()
long_description = (repo / "README.md").read_text(encoding="utf-8")

setup(
    name = "FishingForPhish",
    author = "Xander Kutulas",
    author_email = "Xander.Kutulas@gmail.com",
    url = "https://github.com/xanmankey/FishingForPhish.git"
    version = "1.0.0"
    description = "FishingForPhish is a phishing detection framework focused on adaptive web scraping and the analysis of website image and page based features.",
    long_description = long_description
    keywords = phishing-detection, machine learning, data analysis
    license = BSD 3-Clause License
    
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Researchers",
        "Topic :: Software Development :: Build Tools",
        # Pick your license as you wish
        "License :: OSI Approved :: MIT License",
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate you support Python 3. These classifiers are *not*
        # checked by 'pip install'. See instead 'python_requires' below.
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
    ]


)
# Setup.py file; initializes parsing of setup.cfg
if __name__ == "__main__":
    setup()
