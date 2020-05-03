# W3C Audiobooks Generator from Librivox content

Command-line interface tool written in Python 3, useful for generating W3C Audiobooks packaged in LPF format out of content downloaded from the Librivox website. 

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](/LICENSE)

## Rationale

The [W3C Audiobooks](https://www.w3.org/TR/audiobooks/) format is currently (May 2020) a Candidate Recommandation; the [W3C Lightweight Packaging Format (LPF)](https://www.w3.org/TR/lpf/) is a Note. 

Members of the W3C publication WG (EDRLab is one of them) are now promoting this format, i.e. trying to catch the attention of publishers, audiobooks studios, e-distributors and e-bookselers.

[Thorium Reader](https://www.edrlab.org/software/thorium-reader/) is now able to open and read audiobooks formatted as W3C Audiobooks. Other apps based on [Readium Desktop](https://www.edrlab.org/software/readium-desktop/) or [Readium Mobile](https://www.edrlab.org/software/readium-mobile/) will soon be able to do the same. This is a huge step for convincing audiobook creators to adopt this format.

In order to test such apps, and also for proving to the industry that generating standard W3C Audiobooks is easy, there is a need for producing samples as automatically as possible, from open content. 

[Librivox](https://librivox.org/) is a non-commercial, non-profit and ad-free project, in which volunteers record chapters of books in the public domain, and which distributes such content in the public domain available, for free. Audio content is [avaiable in multiple languages(https://librivox.org/search?primary_key=0&search_category=language&search_page=1&search_form=get_results)]. This is a marvelous source of content for the samples we need. 

## Installation

Python 3.5+ is required for using this command-line interface tool.

After cloning the project, install the following dependencies: 

```
pip install lxml
pip install jsons
pip install jsonschema
```

### Notes

Why using the RSS feed provided by Librivox? 
This is an xml file, easy to download from each Librivox web page. The Internet Archive has an API which enable fetching a JSON Readium WebPub Manifest but the implementation is still in beta.   

Why using jsons?
`jsons` is much easier to use than the natif json lib for marshalling JSON from Python objects. 

## Usage

### Dowload content from Librivox

* Choose an audiobook in [Librivox](https://librivox.org/). 
  * The size of each audiobook is clearly displayed. Consider choosing a small one.  
  * For instance, select some [French poetry](https://librivox.org/compilation-de-poemes-001-by-various/) .
* On the left side of the page:
  * Right-click on "Download" beside "Whole book (zip file)" and save the zip file into the directory of your choice (you can keep the file name as-is).  
  * Right-click on "RSS" beside "RSS Feed" and save it into the same directory __with a .xml extension__ (no other requirement on the file name).
* On the right side, below the cover image:
  * Right-click on "Download cover art" and save it into the same directory (no other requirement on the file name).

### Use librivox2lpf

From the directory which contains the cloned project, type:

'''
python3 librivox2lpf.py &lt;filePath>
'''

Where `filePath`is the directory in which you have saved the zip file, xml file and cover image. 

You should see notifications like:

```
rss file:  3145.xml
zip file:  compilationpoemes_001_1007_librivox.zip
cover file:  Compilation_poemes_001_1209.jpg
Validation succeeded
lpf packaged publication generated
```

The three source files have been replaced by a `.lpf` file. 

If you have installed Thorium Reader, you can double-click on this file, select Thorium Reader and the file will directly be played. An alternative is to open Thorium Reader and drag&drop the audiobook.  








