# -*- coding: utf-8 -*-
##!/usr/bin/env python3

import requests
import os.path
#import json
#from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup as bs
import sys
import pypandoc
from PIL import Image
import re

apiToken = os.environ["atlassianAPIToken"]
userName = os.environ["atlassianUserEmail"]

try:
    atlassianSite = sys.argv[1]
except IndexError as exc:
    raise SystemExit(f"Options: <site> <page ID> <output folder>") from exc
print('Site: ' + atlassianSite)

try:
    pageID = sys.argv[2]
except IndexError as exc:
    raise SystemExit(f"Options: <site> <page ID> <output folder>") from exc
print('Page ID: ' + pageID)

# get some information from page properties report page
def getBodyExportView(argPageID):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageID) + '?expand=body.export_view'
    response = requests.get(serverURL, auth=(userName, apiToken),timeout=30)
    return(response)

# get page labels
def getPageLabels(argPageID):
    htmlLabels = []
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/api/v2/pages/' + str(argPageID) + '/labels'
    response = requests.get(serverURL, auth=(userName, apiToken),timeout=30).json()
    for l in response['results']:
        htmlLabels.append(l['name'])
    #htmlLabels = ",".join(htmlLabels)
    return(htmlLabels)

myReportBodyExportView = getBodyExportView(pageID).json()
myReportExportViewTitle = myReportBodyExportView['title']
myReportExportViewTitle = myReportExportViewTitle.replace("/","-")

currentDir = os.getcwd()
scriptDir = os.path.dirname(os.path.abspath(__file__))

try:
    outdir = sys.argv[3]
except IndexError as exc:
    outdir = os.path.join(scriptDir,"output")
    outdir = os.path.join(outdir,str(pageID) + " - " + str(myReportExportViewTitle))
    print('No output folder supplied, using script path: ' + outdir)
else:
    outdir = os.path.join(outdir,str(pageID) + " - " + str(myReportExportViewTitle))

# Create the output folders
attachDir = "_images/"
emoticonsDir = "_images/"
stylesDir = "_static/"
outdirAttach = os.path.join(outdir,attachDir)
outdirEmoticons = os.path.join(outdir,emoticonsDir)
outdirStyles = os.path.join(outdir,stylesDir)

if not os.path.exists(outdir):
    os.mkdir(outdir)

if not os.path.exists(outdirAttach):
    os.mkdir(outdirAttach)

if not os.path.exists(outdirEmoticons):
    os.mkdir(outdirEmoticons)

if not os.path.exists(outdirStyles):
    os.mkdir(outdirStyles)

if not os.path.exists(str(outdirStyles) + '/site.css'):
    os.system('cp ' + scriptDir + '/styles/site.css "' + outdirStyles + '"')

myPagePropertiesChildren = []
myPagePropertiesChildrenDict = {}
def getPagePropertiesChildren(argHTML):
    soup = bs(argHTML, "html.parser")
    myPagePropertiesItems = soup.findAll('td',class_="title")
    myPagePropertiesItemsCounter = 0
    for n in myPagePropertiesItems:
        myPageID = str(n['data-content-id'])
        myPagePropertiesChildren.append(str(n['data-content-id']))
        myPagePropertiesItemsCounter = myPagePropertiesItemsCounter + 1
        myPageName = getPageName(int(myPageID))
        myPageName = myPageName.rsplit('_',1)[1].replace(":","-").replace(" ","_").replace("%20","_")          # replace offending characters from file name
        myPagePropertiesChildrenDict.update({ myPageID:{}})
        myPagePropertiesChildrenDict[myPageID].update({"ID": myPageID})
        myPagePropertiesChildrenDict[myPageID].update({"Name": myPageName})
    print(str(myPagePropertiesItemsCounter) + " Pages")
    print("Exporting to: " + outdir)
    return(myPagePropertiesChildrenDict)

myAttachmentsList = []
def getAttachments(argPageID):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageID) + '?expand=children.attachment'
    response = requests.get(serverURL, auth=(userName, apiToken),timeout=30)
    myAttachments = response.json()['children']['attachment']['results']
    for attachment in myAttachments:
        attachmentTitle = attachment['title'].replace(":","-").replace(" ","_").replace("%20","_").replace("%80","").replace("%8B","").replace("%E2","").replace('\u200b','').replace('\u200c','')
        attachmentURL = 'https://' + atlassianSite + '.atlassian.net/wiki' + attachment['_links']['download']
        requestAttachment = requests.get(attachmentURL, auth=(userName, apiToken),allow_redirects=True,timeout=30)
        open(os.path.join(outdirAttach,attachmentTitle), 'wb').write(requestAttachment.content)
        myAttachmentsList.append(attachmentTitle)
    return(myAttachmentsList)

def getPageName(argPageID):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageID)
    r_pagetree = requests.get(serverURL, auth=(userName, apiToken),timeout=30)
    return(r_pagetree.json()['id'] + "_" + r_pagetree.json()['title'])


def setHtmlHeader(argTitle,argURL,argLabels):
    myHeader = """<html>
<head>
<title>""" + argTitle + """</title>
<link rel="stylesheet" href=\"""" + stylesDir + """site.css" type="text/css" />
<meta name="generator" content="confluenceExportHTML" />
<META http-equiv="Content-Type" content="text/html; charset=UTF-8">
<meta name="labels" content=\"""" + str(argLabels) + """\">
</head>
<body>
<h2>""" + argTitle + """</h2>
<p>Original URL: <a href=\"""" + argURL + """\"> """+argTitle+"""</a><hr>"""
    return(myHeader)

#
# Define HTML page footer
#
footersHTML = """</body>
</html>"""

myAttachments = []
myAttachmentsList = []
myEmbeds = []
myEmbedsExternals = []
myEmoticons = []
myEmoticonsList = []
def dumpHtml(argHTML,argTitle,argURL,argPageID,argType):
    ## get Page Labels
    pageLabels = getPageLabels(argPageID)
    htmlPageLabels = ",".join(pageLabels)
    ## get and parse the page
    soup = bs(argHTML, "html.parser")
    htmlFileName = str(argTitle) + '.html'
    htmlFilePath = os.path.join(outdir,htmlFileName)
    #headersHTML = setHTMLHeader(argTitle,htmlLabels)
    myAttachments = getAttachments(argPageID)
    if (argType != "report"):
        myPagePropertiesChildrenDict[argPageID].update({"Filename": htmlFileName})
    if (argType == "report"):
        myPagePropertiesItems = soup.findAll('td',class_="title")
        for item in myPagePropertiesItems:
            id = item['data-content-id']
            item.a['href'] = myPagePropertiesChildrenDict[id]['Filename']
    #
    # dealing with "confluence-embedded-image confluence-external-resource"
    #
    myEmbedsExternals = soup.findAll('img',class_="confluence-embedded-image confluence-external-resource")
    myEmbedsExternalsCounter = 0
    for embedExt in myEmbedsExternals:
        origEmbedExternalPath = embedExt['src']
        origEmbedExternalName = origEmbedExternalPath.rsplit('/',1)[-1].rsplit('?')[0]
        origEmbedExternalName = str(argPageID) + "-" + str(myEmbedsExternalsCounter) + "-" + origEmbedExternalName
        myEmbedExternalPath = os.path.join(outdirAttach,origEmbedExternalName)
        toDownload = requests.get(origEmbedExternalPath, allow_redirects=True)
        myEmbedExternalPath = myEmbedExternalPath.replace(":","-").replace("%20"," ")      # replace offending characters from file name
        try:
            open(myEmbedExternalPath,'wb').write(toDownload.content)
        except:
            print(origEmbedExternalPath)
        print("Embed External path: " + str(myEmbedExternalPath))
        img = Image.open(myEmbedExternalPath)
        if img.width < 600:
            embedExt['width'] = img.width
        else:
            embedExt['width'] = 600
        img.close
        embedExt['height'] = "auto"
        embedExt['onclick'] = "window.open(\"" + myEmbedExternalPath + "\")"
        embedExt['src'] = myEmbedExternalPath
        myEmbedsExternalsCounter = myEmbedsExternalsCounter + 1
    #
    # dealing with "confluence-embedded-image"
    #
    myEmbeds = soup.findAll('img',class_=re.compile("^confluence-embedded-image"))
    print(str(len(myEmbeds)) + " embedded images.")
    for embed in myEmbeds:
        origEmbedPath = embed['src']            # online link to embedded file
        origEmbedName = origEmbedPath.rsplit('/',1)[-1].rsplit('?')[0]          # just the file name
        myEmbedName = origEmbedName.replace(":","-").replace(" ","_").replace("%20","_").replace("%80","").replace("%8B","").replace("%E2","")       # replace offending characters from file name
        myEmbedPath = attachDir + myEmbedName           # relative local path to file
        myEmbedPathFull = os.path.join(outdir,myEmbedPath)            # absolute local path to file
        #print("Embed path: " + myEmbedPath)
        #print("Embed full path: " + myEmbedPathFull)
        img = Image.open(myEmbedPathFull)
        if img.width < 600:
            embed['width'] = img.width
            print("image width < 600px")
        else:
            embed['width'] = 600
            print("image width > 600px")
        img.close
        embed['height'] = "auto"
        embed['onclick'] = "window.open(\"" + myEmbedPath + "\")"
        embed['src'] = myEmbedPath    #
    # dealing with "emoticon"
    #
    myEmoticons = soup.findAll('img',class_="emoticon")      # any emoticon like atlassian-check_mark
    print(str(len(myEmoticons)) + " emoticons.")
    for emoticon in myEmoticons:
        requestEmoticons = requests.get(emoticon['src'], auth=(userName, apiToken),timeout=30)
        myEmoticonTitle = emoticon['src'].rsplit('/',1)[-1]
        if myEmoticonTitle not in myEmoticonsList:
            myEmoticonsList.append(myEmoticonTitle)
            print("Getting emoticon: " + myEmoticonTitle)
            filePath = os.path.join(outdirEmoticons,myEmoticonTitle)
            open(filePath, 'wb').write(requestEmoticons.content)
        myEmoticonPath = emoticonsDir + myEmoticonTitle
        emoticon['src'] = myEmoticonPath
    #
    # When the file is the report
    #
    htmlPageHeader = setHtmlHeader(argTitle,argURL,htmlPageLabels)         # dealing with page header
    prettyHTML = soup.prettify()
    htmlFile = open(htmlFilePath, 'w')
    htmlFile.write(htmlPageHeader)
    htmlFile.write(prettyHTML)
    htmlFile.write(footersHTML)
    htmlFile.close()
    print("Exported file: " + htmlFileName)
    # convert html to rst
    rstFileName = str(argTitle) + '.rst'
    rstFilePath = os.path.join(outdir,rstFileName)
    outputRST = pypandoc.convert_file(str(htmlFilePath), 'rst', format='html',extra_args=['--standalone','--wrap=none','--list-tables'])
    rstPageHeader = setRstHeader(htmlPageLabels)
    rstFile = open(rstFilePath, 'w')
    rstFile.write(rstPageHeader)            # assing .. tags:: to rst file for future reference
    rstFile.write(outputRST)
    rstFile.close()
    print("Exported RST file: " + rstFileName)

#
# Define RST file header
#
def setRstHeader(argLabels):
    myHeader = """
.. tags:: """ + str(argLabels) + """

"""
    return(myHeader)



# Get Page Properties REPORT
myReportBodyExportView = getBodyExportView(pageID).json()
myReportExportViewTitle = myReportBodyExportView['title']
myReportExportViewHtml = myReportBodyExportView['body']['export_view']['value']
myReportExportViewName = getPageName(pageID)
myReportExportViewLabels = getPageLabels(pageID)
myReportExportPageURL = str(myReportBodyExportView['_links']['base']) + str(myReportBodyExportView['_links']['webui'])
getPagePropertiesChildren(myReportExportViewHtml)                                  # get list of all page properties children

# Get Page Properties CHILDREN
for p in myPagePropertiesChildren:
    print("Handling child: " + p)
    myChildExportView = getBodyExportView(p).json()
    myChildExportViewHtml = myChildExportView['body']['export_view']['value']
    myChildExportViewName = myPagePropertiesChildrenDict[p]['Name']
    myChildExportViewLabels = getPageLabels(p)
    myChildExportViewTitle = myChildExportView['title']
    myChildExportViewTitle = myChildExportViewTitle.replace("/","-")
    myChildExportPageURL = str(myChildExportView['_links']['base']) + str(myChildExportView['_links']['webui'])
    dumpHtml(myChildExportViewHtml,myChildExportViewTitle,myChildExportPageURL,p,"child")                  # creates html files for every child

dumpHtml(myReportExportViewHtml,myReportExportViewTitle,myReportExportPageURL,pageID,"report")         # finally creating the HTML for the report page

