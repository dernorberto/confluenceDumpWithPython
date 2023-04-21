# -*- coding: utf-8 -*-
##!/usr/bin/env python3

import requests
import os.path
#import json
#from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup as bs
import sys


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

outdirAttach = os.path.join(outdir,"attachments")
outdirEmoticons = os.path.join(outdir,"emoticons")
outdirStyles = os.path.join(outdir,"styles")

if not os.path.exists(outdir):
    os.mkdir(outdir)

if not os.path.exists(outdirAttach):
    os.mkdir(outdirAttach)

if not os.path.exists(outdirEmoticons):
    os.mkdir(outdirEmoticons)

if not os.path.exists(outdirStyles):
    os.mkdir(outdirStyles)

if not os.path.exists(str(outdirStyles) + '/site.css'):
    os.system('cp ' + currentdir + '/styles/site.css "' + outdirStyles + '"')

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
        myPageName = myPageName.rsplit('_',1)[1]
        myPagePropertiesChildrenDict.update({ myPageID:{}})
        myPagePropertiesChildrenDict[myPageID].update({"ID": myPageID})
        myPagePropertiesChildrenDict[myPageID].update({"Name": myPageName})
    print(str(myPagePropertiesItemsCounter) + " Pages")
    print("Exporting to: " + outdir)
    return(myPagePropertiesChildrenDict)

myAttachmentsList = []
def getAttachments(argPageID):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageID) + '?expand=children.attachment'
    response = requests.get(serverURL, auth=(userName, apiToken),timeout=60)
    myAttachments = response.json()['children']['attachment']['results']
    for n in myAttachments:
        myTitle = n['title']
        myTail = n['_links']['download']
        url = 'https://' + atlassianSite + '.atlassian.net/wiki' + myTail
        requestAttachment = requests.get(url, auth=(userName, apiToken),allow_redirects=True,timeout=60)
        filePath = os.path.join(outdirAttach,myTitle)
        open(filePath, 'wb').write(requestAttachment.content)
        myAttachmentsList.append(myTitle)
    return(myAttachmentsList)

def getPageName(argPageID):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageID)
    r_pagetree = requests.get(serverURL, auth=(userName, apiToken),timeout=60)
    return(r_pagetree.json()['id'] + "_" + r_pagetree.json()['title'])

htmlPageHeader = """    <head>
        <title>python title TODO</title>
        <link rel="stylesheet" href="styles/site.css" type="text/css" />
        <META http-equiv="Content-Type" content="text/html; charset=UTF-8">
    </head>
"""

def setHTMLHeader(argTitle,argLabels):
    headersHTML = """<html>
<head>
<meta charset="utf-8" />
<meta name="generator" content="confluenceExportHTML" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes" />
<meta name="labels" content=\"""" + argLabels + """\">
<title>""" + argTitle + """</title>
<link rel="stylesheet" type="text/css" href="site.css" media="screen" />
</head>
<body>"""
    return(headersHTML)

footersHTML = """</body>
</html>"""


def dumpHtml(argHTML,argTitle,argURL,argPageID,argType):
    ## get Page Labels
    #htmlLabels = []
    labels = getPageLabels(argPageID)
    #jsonLabels = labels.json()
    #for l in jsonLabels['results']:
    #    htmlLabels.append(l['name'])
    htmlLabels = ",".join(labels)


    ## get and parse the page
    soup = bs(argHTML, "html.parser")
    htmlFileName = str(argTitle) + '.html'
    htmlFilePath = os.path.join(outdir,htmlFileName)
    #headersHTML = setHTMLHeader(argTitle,htmlLabels)
    #myAttachments = getAttachments(argPageID)
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
    for n in myEmbedsExternals:
        origAttachmentPath = n['src']
        attachmentName = origAttachmentPath.rsplit('/',1)[-1]
        attachmentName = attachmentName.rsplit('?')[0]
        attachmentName = str(argPageID) + "-" + str(myEmbedsExternalsCounter) + "-" + attachmentName
        myAttachmentPath = os.path.join(outdirAttach,attachmentName)
        toDownload = requests.get(origAttachmentPath, allow_redirects=True,timeout=30)
        open(myAttachmentPath,'wb').write(toDownload.content)
        #print(myAttachmentPath)            # not printing path to exported embeds
        n['width'] = "1024px"
        n['height'] = "auto"
        n['onclick'] = "window.open(\"" + myAttachmentPath + "\")"
        n['src'] = myAttachmentPath
        myEmbedsExternalsCounter = myEmbedsExternalsCounter + 1
    #
    # dealing with "confluence-embedded-image"
    #
    myEmbeds = soup.findAll('img',class_="confluence-embedded-image")
    for n in myEmbeds:
        origAttachmentPath = n['src']
        attachmentName = origAttachmentPath.rsplit('/',1)[-1]
        attachmentName = attachmentName.rsplit('?')[0]
        origAttachmentPath = 'https://' + atlassianSite + '.atlassian.net/wiki/download/attachments/' + str(argPageID) + '/' + attachmentName
        myAttachmentPath =  "attachments/" + attachmentName
        #print(myAttachmentPath)            # not printing path to exported embeds
        n['src'] = myAttachmentPath
    #
    # dealing with "emoticon"
    #
    myEmoticons = soup.findAll('img',class_="emoticon")      # any emoticon like atlassian-check_mark
    for e in myEmoticons:
        requestEmoticons = requests.get(e['src'], auth=(userName, apiToken),timeout=60)
        myEmoticonTitle = e['src']
        myEmoticonTitle = myEmoticonTitle.rsplit('/',1)[-1]
        filePath = os.path.join(outdirEmoticons,myEmoticonTitle)
        open(filePath, 'wb').write(requestEmoticons.content)
        origEmoticonPath = e['src']
        myEmoticonPath = "emoticons/" + myEmoticonTitle
        e['src'] = myEmoticonPath
    #
    # When the file is the report
    #
    htmlPageHeader = setPageHeader(argTitle,argURL,htmlLabels)         # dealing with page header
    prettyHTML = soup.prettify()
    f = open(htmlFilePath, 'w')
    f.write(htmlPageHeader)
    f.write(prettyHTML)
    f.write(footersHTML)
    f.close()
    print("Exported file: " + htmlFileName)

def setPageHeader(argTitle,argURL,argLabels):
    myHeader = """    <head>
        <title>""" + argTitle + """</title>
        <link rel="stylesheet" href="styles/site.css" type="text/css" />
        <meta name="generator" content="confluenceExportHTMLrequests" />
        <META http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="labels" content=\"""" + str(argLabels) + """\">
    </head>
    <h2>""" + argTitle + """</h2>
    <p>Original URL: <a href=\"""" + argURL + """\"> """+argTitle+"""</a><hr>
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
    myChildExportView = getBodyExportView(p).json()
    myChildExportViewHtml = myChildExportView['body']['export_view']['value']
    myChildExportViewName = myPagePropertiesChildrenDict[p]['Name']
    myChildExportViewLabels = getPageLabels(p)
    myChildExportViewTitle = myChildExportView['title']
    myChildExportViewTitle = myChildExportViewTitle.replace("/","-")
    myChildExportPageURL = str(myChildExportView['_links']['base']) + str(myChildExportView['_links']['webui'])
    dumpHtml(myChildExportViewHtml,myChildExportViewTitle,myChildExportPageURL,p,"child")                  # creates html files for every child

dumpHtml(myReportExportViewHtml,myReportExportViewTitle,myReportExportPageURL,pageID,"report")         # finally creating the HTML for the report page

