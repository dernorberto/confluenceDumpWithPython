# -*- coding: utf-8 -*-
##!/usr/bin/env python3

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

# get some information from page properties report page
def getBodyExportView(pageid):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(pageid) + '?expand=body.export_view'
    response = requests.get(serverURL, auth=(userName, apiToken))
    return(response)

myReportBodyExportView = getBodyExportView(pageID).json()
myReportExportViewTitle = myReportBodyExportView['title']
myReportExportViewTitle = myReportExportViewTitle.replace("/","-")

# Create the output directory
currentdir = os.getcwd()
base_outdir = os.path.join(currentdir,"output")
outdir = os.path.join(currentdir,"output")
outdir = os.path.join(outdir,str(pageID) + " - " + str(myReportExportViewTitle))
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
    return(myPagePropertiesChildrenDict)

myAttachmentsList = []
def getAttachments(pageid):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(pageid) + '?expand=children.attachment'
    response = requests.get(serverURL, auth=(userName, apiToken))
    myAttachments = response.json()['children']['attachment']['results']
    for n in myAttachments:
        myTitle = n['title']
        myTail = n['_links']['download']
        url = 'https://' + atlassianSite + '.atlassian.net/wiki' + myTail
        requestAttachment = requests.get(url, auth=(userName, apiToken),allow_redirects=True)
        filePath = os.path.join(outdirAttach,myTitle)
        open(filePath, 'wb').write(requestAttachment.content)
        myAttachmentsList.append(myTitle)
    return(myAttachmentsList)

def getPageName(pageid):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(pageid)
    r_pagetree = requests.get(serverURL, auth=(userName, apiToken))
    return(r_pagetree.json()['id'] + "_" + r_pagetree.json()['title'])

htmlPageHeader = """    <head>
        <title>python title TODO</title>
        <link rel="stylesheet" href="styles/site.css" type="text/css" />
        <META http-equiv="Content-Type" content="text/html; charset=UTF-8">
    </head>
"""

def dumpHtml(argHTML,argTitle,argPageID,argType):
    soup = bs(argHTML, "html.parser")
    htmlFileName = str(argTitle) + '.html'
    htmlFilePath = os.path.join(outdir,htmlFileName)
    myAttachments = getAttachments(argPageID)
    if (argType != "report"):
        myPagePropertiesChildrenDict[argPageID].update({"Filename": htmlFileName})
    if (argType == "report"):
        myPagePropertiesItems = soup.findAll('td',class_="title")
        for o in myPagePropertiesItems:
            p = o['data-content-id']
            o.a['href'] = myPagePropertiesChildrenDict[p]['Filename']
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
    #
    # When the file is the report
    #
    prettyHTML = soup.prettify()
    f = open(htmlFilePath, 'w')
    f.write(htmlPageHeader)
    f.write(prettyHTML)
    f.close()
    print("Exported file " + htmlFilePath)

def setPageHeader(argTitle,argURL):
    myHeader = """    <head>
        <title>""" + argTitle + """</title>
        <link rel="stylesheet" href="styles/site.css" type="text/css" />
        <META http-equiv="Content-Type" content="text/html; charset=UTF-8">
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
myPageURL = str(myReportBodyExportView['_links']['base']) + str(myReportBodyExportView['_links']['webui'])
htmlPageHeader = setPageHeader(myReportExportViewTitle,myPageURL)
#dumpHtml(myReportExportViewHtml,myReportExportViewTitle,pageID,"report")         # not generating an HTML for report just yet

getPagePropertiesChildren(myReportExportViewHtml)                                  # get list of all page properties children

# Get Page Properties CHILDREN
for p in myPagePropertiesChildren:
    myBodyExportView = getBodyExportView(p).json()
    myBodyExportViewHtml = myBodyExportView['body']['export_view']['value']
    myBodyExportViewName = myPagePropertiesChildrenDict[p]['Name']
    myBodyExportViewTitle = myBodyExportView['title']
    myBodyExportViewTitle = myBodyExportViewTitle.replace("/","-")
    myPageURL = str(myBodyExportView['_links']['base']) + str(myBodyExportView['_links']['webui'])
    htmlPageHeader = setPageHeader(myBodyExportViewTitle,myPageURL)
    dumpHtml(myBodyExportViewHtml,myBodyExportViewTitle,p,"child")                  # creates html files for every child

dumpHtml(myReportExportViewHtml,myReportExportViewTitle,pageID,"report")         # finally creating the HTML for the report page
