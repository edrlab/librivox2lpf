""" Transforms audiobook content from Librivox into an LPF packaged W3C Audiobook.

    Copyright 2020 European Digital Reading Lab. All rights reserved.
    Use of this source code is governed by a BSD-style license
    available in the project repository on Github.

    Creator: Laurent Le Meur, EDRLab, 2020
"""
""" sample content: download from https://librivox.org/compilation-de-poemes-001-by-various/ """

import io, os, sys
import argparse
from lxml import etree
import jsons
import json, jsonschema
from zipfile import ZipFile 

# Publication class
class Publication:
  """A W3C Publication, init limited to required properties""" 
  _context = ["https://schema.org","https://www.w3.org/ns/pub-context"]
  conformsTo = "https://www.w3/org/TR/audiobooks/"
  type = "Audiobook"
  readingOrder = []

  def __init__(self, name, id):
    self.name = name
    self.id = id

# Link class
class Link:
  """A W3C Link""" 
  def __init__(self, url):
    self.url = url

# MediaType is a global dictionary of image content-types
MediaType = {
  ".jpg":   "image/jpeg",
  ".jpeg":  "image/jpeg",
  ".png":   "image.png",
  ".gif":   "image/gif",
  ".webp":  "image/webp"
}



def getStrProperty(item, xpath, nsmap=None):
  """Get a string property found at the location specified by an XPath locator.
      The xpath can point to xml elements or attributes.

      In Internet Archive rss feeds, each text node inside an element is a CDATA 
      (which is bad) with extra spaces (which is also bad), therefore the string 
      must be cleaned before being returned """
 
  values = item.xpath(xpath, namespaces=nsmap)
  if len(values) == 0:
    return ""
  return values[0].text.strip() if isinstance(values[0], etree._Element) else values[0]



def getStrProperties(item, xpath, nsmap=None):
  """Get an array of string properties found at the location specified by an XPath locator.
      The xpath can point to xml elements or attributes."""
 
  array = []
  values = item.xpath(xpath, namespaces=nsmap)
  if len(values) > 0:
    for v in values:
      array.append(v.text.strip() if isinstance(v, etree._Element) else v)
  return array



def findFileWithExtension(filePath, extensions):
  """Find a file name in the given path with the given extension"""

  try:
    fileNames = os.listdir(filePath)
  except:
    print("Folder", filePath, " not found")
    return

  for fileName in fileNames:
    ext = os.path.splitext(fileName)
    if ext[1] in extensions:
      return fileName
  
  return None



def convertRSSFeedToW3PM(filePath, rssFileName, zipFileName, coverFileName):
  """Convert a RSS feed from the Internet Archive to a W3C Publication Manifest"""

  rssPath = os.path.join(filePath, rssFileName)

  # get the list of files in the zip, will be used to control manifest entries vs zip entries
  zipPath = os.path.join(filePath, zipFileName)
  with ZipFile(zipPath, mode='r') as zip: 
    filesInZip = {item for item in zip.namelist()} 
  filesInManifest = set()

  # parse the source XML
  parser = etree.XMLParser(remove_comments=True)
  try:
    xdoc =etree.parse(rssPath, parser)
    rss = xdoc.getroot()
  except (etree.XMLSyntaxError):
    print("Cannot parse this file, XML syntax error")
    return None

  # map required info from the rss structure to a new W3C Publication Manifest structure
  title = getStrProperty(xdoc, "/rss/channel/title")
  id    = getStrProperty(xdoc, "/rss/channel/link")
  if title == None or id == None:
    return None
  pub = Publication(title, id)

  # map useful metadata from the rss structure to the W3C Publication
  pub.url  = getStrProperty(xdoc, "/rss/channel/atom:link[@rel='self']/@href", nsmap=rss.nsmap)
  pub.author = getStrProperty(xdoc, "/rss/channel/itunes:author", nsmap=rss.nsmap)
  pub.publisher = getStrProperty(xdoc, "/rss/channel/itunes:owner/itunesname", nsmap=rss.nsmap)
  pub._description = getStrProperty(xdoc, "/rss/channel/description")
  pub._subjects = getStrProperties(xdoc, "/rss/channel//itunes:category/@text", nsmap=rss.nsmap)

  # loop through rss items, create a reading order
  for item in rss.iter("item"):
    url = getStrProperty(item, "media:content/@url", nsmap=rss.nsmap)
    if url == None:
      continue
    # add an item to a set, will be used to control manifest entries vs zip entries
    filesInManifest.add(os.path.basename(url))

    # the url becomes a file name inside the zip (files are at the root of the archives)
    track = Link(os.path.basename(url))
    track.name = getStrProperty(item, "title")
    track.encodingFormat = getStrProperty(item, "media:content/@type", nsmap=rss.nsmap)
    # convert duration from hh:mm:ss to PThhHmmMssS
    duration = getStrProperty(item, "itunes:duration", nsmap=rss.nsmap).split(":")  
    if len(duration) == 3:
      track.duration = "PT" + duration[0] + "H" + duration[1] + "M" + duration[2] + "S"

    pub.readingOrder.append(track)

  # compare filesInManifest and filesInZip
  # error if the manifest references files absent from the zi
  diffFiles1 = filesInManifest - filesInZip
  if diffFiles1:
    print("The manifest references files absent from the zip")
    print(diffFiles1)
    return None
  # warning if there are un-referenced files in the zip
  diffFiles2 =  filesInZip - filesInManifest
  if diffFiles2:
    print("The zip archive contains files un-referenced in the manifest")
    print(diffFiles2)

  # add the cover as a resource
  if coverFileName:
    pub.resources = []
    cover = Link(coverFileName)
    ext = os.path.splitext(coverFileName)[1]
    cover.encodingFormat = MediaType[ext]
    cover.rel = "cover"
    pub.resources.append(cover)
  
  # we can't create a variable with an @ or a namespace prefix, 
  # therefore rely on replacing substrings.
  # ensure_ascii False avoids accented characters to be json encoded (e.g. '\u00e9' for 'é')
  # ident could be used as a pretty-print param (add "indent":2 to the jswargs set if needed)
  jpub = jsons.dumps(pub, jdkwargs={"ensure_ascii":False} )
  jpub = jpub.replace("_context", "@context")
  jpub = jpub.replace("_description", "dcterms:description")
  jpub = jpub.replace("_subjects", "dcterms:subject")

  return jpub



def validateManifest(jpub):
  """Validate a W3C Publication Manifest vs the corresponding schema"""

  # de-serialize the publication manifest
  pub = json.loads(jpub)

  # set the relative path of the W3C schemas (relative to the python code)
  schema_search_path = "schema"

  ok = False
  try:
    # load the different W3C sub-schemas in a dictionary
    schemastore = {}
    schema = None
    fnames = os.listdir(schema_search_path)
    for fname in fnames:
      fpath = os.path.join(schema_search_path, fname)
      if fpath[-5:] == ".json":
        with open(fpath, "r") as schemaf:
          schema = json.load(schemaf)
          if "$id" in schema:
            schemastore[schema["$id"]] = schema

    # create a resolver for all $ref present in the dictionary
    resolver = jsonschema.RefResolver("", "", schemastore)

    # validate the json structure vs the json schema
    jsonschema.validate(pub, schema, resolver=resolver, format_checker=jsonschema.FormatChecker())

    print("Validation succeeded")
    ok = True

  except jsonschema.exceptions.ValidationError as err:
      print("Validation failed")
      print(err.message)
  
  return ok



def saveInZip(jpub, filePath, zipFileName, coverFileName):
  """Save a json manifest into the zip archive, rename the zip as .lpf"""

  zipPath = os.path.join(filePath, zipFileName)
  coverPath = os.path.join(filePath, coverFileName) if coverFileName else None

  # open the zip file in append mode, uncompressed
  with ZipFile(zipPath, mode='a') as zip: 
    # append the json manifest
    zip.writestr("publication.json", jpub)
    # append (optionally) the cover
    if coverFileName:
      zip.write(coverPath, coverFileName)
    # check the integrity of the zip archive
    if zip.testzip():
      print("Zip integrity check failed")



def finalizeTransformation(filePath, rssFileName, zipFileName, coverFileName):
  """Rename the zip file to .lpf, delete the rss and cover files"""

  baseName = os.path.splitext(zipFileName)[0]
  sourcePath = os.path.join(filePath, zipFileName)
  targetPath = os.path.join(filePath, baseName + ".lpf")
  os.rename(sourcePath, targetPath)

  os.remove(os.path.join(filePath, rssFileName))
  if coverFileName:
    os.remove(os.path.join(filePath, coverFileName))



def main():

  parser = argparse.ArgumentParser(description="Internet Archive rss feed to W3C Publication Manifest")
  parser.add_argument("filePath", help="path to the xml and zip file")
  args = parser.parse_args()

  # find the rss manifest
  rssFileName = findFileWithExtension(args.filePath, {".xml"})
  if rssFileName == None:
    print("The source xml file wasn't found")
    return

  # find the zip archive
  zipFileName = findFileWithExtension(args.filePath, {".zip"})
  if zipFileName == None:
    print("The source zip file wasn't found")
    return

  # find the optional cover 
  extensions = {ext for ext in MediaType}
  coverFileName = findFileWithExtension(args.filePath, extensions)

  # log
  print("rss file: ", rssFileName)
  print("zip file: ", zipFileName)
  print("cover file: ", coverFileName)

  # convert the rss feed into a W3C Publication Manifest
  jpub = convertRSSFeedToW3PM(args.filePath, rssFileName, zipFileName, coverFileName)
  if jpub == None:
    return

  """
  # save the json file (only for debug purpose)
  with open("sample/publication.json", "w") as jsonf:
    jsonf.write(jpub)
  """
  
  # validate the json manifest vs the corresponding schema
  ok = validateManifest(jpub)
  if not ok:
    return

  # save the json manifest into the zip containing audio tracks
  saveInZip(jpub, args.filePath, zipFileName, coverFileName)

  # finalize the transformation
  finalizeTransformation(args.filePath, rssFileName, zipFileName, coverFileName)

  # final message
  print("lpf packaged publication generated")

if __name__ == "__main__":
    main()


