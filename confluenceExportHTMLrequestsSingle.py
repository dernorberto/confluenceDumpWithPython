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
    raise SystemExit(f"Usage: {sys.argv[0]} <string_to_reverse>")
print('Site: ' + atlassianSite)

try:
    pageID = sys.argv[2]
except IndexError:
    raise SystemExit(f"Usage: {sys.argv[1]} <string_to_reverse>")
print('Page ID: ' + pageID)


# Create the output directory
currentdir = os.getcwd()
base_outdir = os.path.join(currentdir,"output")
outdir = os.path.join(currentdir,"output")
outdirAttach = os.path.join(outdir,"attachments")
outdirEmoticons = os.path.join(outdir,"emoticons")
if not os.path.exists(outdir):
    os.mkdir(outdir)

if not os.path.exists(outdirAttach):
    os.mkdir(outdirAttach)

if not os.path.exists(outdirEmoticons):
    os.mkdir(outdirEmoticons)

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
    f.close()

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

myBodyExportView = getBodyExportView(pageID).json()
myBodyExportViewHtml = myBodyExportView['body']['export_view']['value']
myBodyExportViewName = getPageName(pageID)
myBodyExportViewTitle = myBodyExportView['title']
myPageURL = str(myBodyExportView['_links']['base']) + str(myBodyExportView['_links']['webui'])
htmlPageHeader = setPageHeader(myBodyExportViewTitle,myPageURL)
dumpHtml(myBodyExportViewHtml,myBodyExportViewTitle,pageID)
