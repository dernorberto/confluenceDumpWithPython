# -*- coding: utf-8 -*-
##!/usr/bin/env python3

#import pypandoc # only needed if converting HTML to MD
import requests
import os.path
import json
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup as bs
import sys


apiToken = os.environ["atlassianAPIToken"]
userName = os.environ["atlassianUserEmail"]

try:
    atlassianSite = sys.argv[1]
except IndexError:
    raise SystemExit(f"Usage: <script>.py {sys.argv[1]} <pageID>")
print('Site: ' + atlassianSite)

try:
    pageID = sys.argv[2]
except IndexError:
    raise SystemExit(f"Usage:<script>.py <site> {sys.argv[2]}")
print('Page ID: ' + pageID)

def getBodyExportView(pageid):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(pageID) + '?expand=body.export_view'
    response = requests.get(serverURL, auth=(userName, apiToken))
    return(response)

def getPageName(pageid):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(pageid)
    r_pagetree = requests.get(serverURL, auth=(userName, apiToken))
    return(r_pagetree.json()['id'] + "_" + r_pagetree.json()['title'])

# get page labels
def getPageLabels(argPageID):
    htmlLabels = []
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/api/v2/pages/' + str(argPageID) + '/labels'
    response = requests.get(serverURL, auth=(userName, apiToken),timeout=30).json()
    for l in response['results']:
        htmlLabels.append(l['name'])
    #htmlLabels = ",".join(htmlLabels)
    return(htmlLabels)

myBodyExportView = getBodyExportView(pageID).json()
myBodyExportViewHtml = myBodyExportView['body']['export_view']['value']
myBodyExportViewTitle = myBodyExportView['title']
myBodyExportViewTitle = myBodyExportViewTitle.replace("/","-")

currentDir = os.getcwd()
scriptDir = os.path.dirname(os.path.abspath(__file__))

try:
    outdir = sys.argv[3]
except IndexError as exc:
    outdir = os.path.join(scriptDir,"output")
    outdir = os.path.join(outdir,str(pageID) + " - " + str(myBodyExportViewTitle))
    print('No output folder supplied, using script path: ' + outdir)
else:
    outdir = os.path.join(outdir,str(pageID) + " - " + str(myBodyExportViewTitle))

# Create the output directory

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

if not os.path.exists(outdirStyles + '/site.css'):
    os.system('cp ' + scriptDir + '/styles/site.css "' + outdirStyles + '"')

def getBodyExportView(pageid):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(pageID) + '?expand=body.export_view'
    response = requests.get(serverURL, auth=(userName, apiToken))
    return(response)

myAttachmentsList = []
def getAttachments(pageid):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(pageID) + '?expand=children.attachment'
    response = requests.get(serverURL, auth=(userName, apiToken))
    myAttachments = response.json()['children']['attachment']['results']
    for n in myAttachments:
        myTitle = n['title']
        myTail = n['_links']['download']
        url = 'https://' + atlassianSite + '.atlassian.net/wiki' + myTail
        requestAttachment = requests.get(url, auth=(userName, apiToken),allow_redirects=True)
        filePath = os.path.join(outdirAttach,myTitle)
        #if (requestAttachment.content.decode("utf-8")).startswith("<!doctype html>"):
        #    filePath = str(filePath) + ".html"
        open(filePath, 'wb').write(requestAttachment.content)
        myAttachmentsList.append(myTitle)
    return(myAttachmentsList)


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

def dumpHtml(argHTML,argTitle,argPageID):
    soup = bs(argHTML, "html.parser")
    htmlFileName = str(argTitle) + '.html'
    htmlFilePath = os.path.join(outdir,htmlFileName)
    myAttachments = getAttachments(argPageID)
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
        toDownload = requests.get(origAttachmentPath, allow_redirects=True)
        open(myAttachmentPath,'wb').write(toDownload.content)
        print(myAttachmentPath)
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
        print(myAttachmentPath)
        n['src'] = myAttachmentPath
    #
    # dealing with "emoticon"
    #
    myEmoticons = soup.findAll('img',class_="emoticon")     # atlassian-check_mark, or
    for e in myEmoticons:
        requestEmoticons = requests.get(e['src'], auth=(userName, apiToken))
        myEmoticonTitle = e['src']
        myEmoticonTitle = myEmoticonTitle.rsplit('/',1)[-1]
        filePath = os.path.join(outdirEmoticons,myEmoticonTitle)
        open(filePath, 'wb').write(requestEmoticons.content)
        origEmoticonPath = e['src']
        myEmoticonPath = "emoticons/" + myEmoticonTitle
        e['src'] = myEmoticonPath
    prettyHTML = soup.prettify()
    f = open(htmlFilePath, 'w')
    f.write(htmlPageHeader)
    f.write(prettyHTML)
    f.write(footersHTML)
    f.close()
    print("Exported file " + htmlFilePath)

def setPageHeader(argTitle,argURL,argLabels):
    myHeader = """<html>
<head>
<title>""" + argTitle + """</title>
<link rel="stylesheet" href="styles/site.css" type="text/css" />
<meta name="generator" content="confluenceExportHTML" />
<META http-equiv="Content-Type" content="text/html; charset=UTF-8">
<meta name="labels" content=\"""" + str(argLabels) + """\">
</head>
<body>
<h2>""" + argTitle + """</h2>
<p>Original URL: <a href=\"""" + argURL + """\"> """+argTitle+"""</a><hr>"""
    return(myHeader)

myBodyExportViewName = getPageName(pageID)
myBodyExportViewLabels = getPageLabels(pageID)
myBodyExportViewLabels = ",".join(myBodyExportViewLabels)
myPageURL = str(myBodyExportView['_links']['base']) + str(myBodyExportView['_links']['webui'])
htmlPageHeader = setPageHeader(myBodyExportViewTitle,myPageURL,myBodyExportViewLabels)
dumpHtml(myBodyExportViewHtml,myBodyExportViewTitle,pageID)
