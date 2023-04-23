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
except IndexError as exc:
    raise SystemExit(f"Options: <site> <page label> <output folder>") from exc
print('Site: ' + atlassianSite)

try:
    pageLabel = sys.argv[2]
except IndexError as exc:
    raise SystemExit(f"Options: <site> <page label> <output folder>") from exc
print('Label: ' + pageLabel)



currentDir = os.getcwd()
scriptDir = os.path.dirname(os.path.abspath(__file__))

try:
    outdir = sys.argv[3]
except IndexError as exc:
    outdir = os.path.join(scriptDir,"output")
    outdir = os.path.join(outdir,pageLabel)
    print('No output folder supplied, using script path: ' + outdir)
else:
    outdir = os.path.join(outdir,pageLabel)

# Create the output folders

outdirAttach = os.path.join(outdir,"images")
outdirEmoticons = os.path.join(outdir,"images")
outdirStyles = os.path.join(outdir,"_static")

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

def getPagesByLabel():
    url = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/search?cql=type=page AND label=\'' + pageLabel + '\''
    auth = HTTPBasicAuth(userName, apiToken)
    headers = { "Accept": "application/json" }
    query = {'cql': '{cql}'}
    response = requests.request("GET", url, headers=headers, params=query, auth=auth, timeout=30)
    return response.json()['results']

# get page labels
def getPageLabels(argPageID):
    htmlLabels = []
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/api/v2/pages/' + str(argPageID) + '/labels'
    response = requests.get(serverURL, auth=(userName, apiToken),timeout=30).json()
    for l in response['results']:
        htmlLabels.append(l['name'])
    #htmlLabels = ",".join(htmlLabels)
    return(htmlLabels)

def getIDs(myResults):
    myListOfIDs = []
    for n in myResults:
        myListOfIDs.append(n['content']['id'])
    return myListOfIDs

def getTitles(myResults):
    myListOfTitles = []
    for n in myResults:
        myListOfTitles.append(n['content']['title'])
    return myListOfTitles

myPages = getPagesByLabel()
myPageIDs = getIDs(myPages)
myPageTitles = getTitles(myPages)

def getBodyExportView(argPageID):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageID) + '?expand=body.export_view'
    response = requests.get(serverURL, auth=(userName, apiToken))
    return(response)

myAttachmentsList = []

def getAttachments(argPageID):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageID) + '?expand=children.attachment'
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

def getPageName(argPageID):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageID)
    r_pagetree = requests.get(serverURL, auth=(userName, apiToken))
    return(r_pagetree.json()['id'] + "_" + r_pagetree.json()['title'])

def dumpHtml(argHTML,argTitle,argPageID):
    soup = bs(argHTML,features="html.parser")
    htmlFileName = str(argTitle) + '.html'
    htmlFilePath = os.path.join(outdir,htmlFileName)
    myAttachments = getAttachments(argPageID)
    myEmbeds = soup.findAll('img',class_="confluence-embedded-image")
    #
    # dealing with "confluence-embedded-image"
    #
    for n in myEmbeds:
        origAttachmentPath = n['src']
        attachmentName = origAttachmentPath.rsplit('/',1)[-1]
        attachmentName = attachmentName.rsplit('?')[0]
        origAttachmentPath = 'https://' + atlassianSite + '.atlassian.net/wiki/download/attachments/' + str(argPageID) + '/' + attachmentName
        myAttachmentPath =  'attachments/' + attachmentName
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
    print('Created: ' + str(htmlFileName))


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

footersHTML = """</body>
</html>"""

for p in myPageIDs:
    myBodyExportView = getBodyExportView(p).json()
    myBodyExportViewHtml = myBodyExportView['body']['export_view']['value']
    myBodyExportViewName = getPageName(p)
    myBodyExportViewTitle = myBodyExportView['title']
    myBodyExportViewTitle = myBodyExportViewTitle.replace("/","-")
    myBodyExportViewLabels = getPageLabels(p)
    myBodyExportViewLabels = ",".join(myBodyExportViewLabels)
    myPageURL = str(myBodyExportView['_links']['base']) + str(myBodyExportView['_links']['webui'])
    htmlPageHeader = setPageHeader(myBodyExportViewTitle,myPageURL,myBodyExportViewLabels)
    dumpHtml(myBodyExportViewHtml,myBodyExportViewTitle,p)
