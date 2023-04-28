# -*- coding: utf-8 -*-
##!/usr/bin/env python3

#import pypandoc # only needed if converting HTML to MD
import requests
import os.path
import json
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup as bs
import sys
import pypandoc
from PIL import Image
import re

apiToken = os.environ["atlassianAPIToken"]
userName = os.environ["atlassianUserEmail"]

try:
    atlassianSite = sys.argv[1]
except IndexError:
    raise SystemExit(f"Usage: <script>.py {sys.argv[1]} <pageID>")
print('Site: ' + atlassianSite)

try:
    spaceKey = sys.argv[2]
except IndexError:
    raise SystemExit(f"Usage:<script>.py <site> {sys.argv[2]}")
print('Space ID: ' + spaceKey)


def getSpaceTitle(argSpaceId):
    url = "https://{your-domain}/wiki/api/v2/spaces/{id}"
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/api/v2/spaces/' + str(argSpaceId)
    response = requests.get(serverURL, auth=(userName, apiToken))
    return(response)

def getSpacesAll(atlassianSite):
    url = "https://{your-domain}/wiki/api/v2/spaces"
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/api/v2/spaces/'
    response = requests.get(serverURL, auth=(userName, apiToken))
    return(response)

for n in getSpacesAll(atlassianSite).json()['results']:
    if (n['key'] == spaceKey):
        spaceId = n['id']
        print(str(spaceKey) + ' = ' + str(spaceId))

spaceTitle = getSpaceTitle(spaceId)

pageList = []
def getPagesFromSpace(argSpaceId):
    # ref: https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-page/#api-spaces-id-pages-get
    #  url = "https://{your-domain}/wiki/api/v2/spaces/{id}/pages"
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/api/v2/spaces/' + str(argSpaceId) + '/pages?status=current&limit=250'
    response = requests.get(serverURL, auth=(userName, apiToken))
    pageList = response.json()['results']
    while 'next' in response.json()['_links'].keys():
        print(str(response.json()['_links']))
        serverURL = serverURL + '&cursor' + response.json()['_links']['next'].split('cursor')[1]
        response = requests.get(serverURL, auth=(userName, apiToken))
        pageList = pageList + response.json()['results']
    print(str(len(pageList)) + ' pages in space ' + spaceKey)
    return(pageList)

allPagesFull = getPagesFromSpace(spaceId)
allPagesShort = []
i = 0
for n in allPagesFull:
    i = i +1
    #print(i, n['id'], n['title'], n['parentId'], n['spaceId'])
    allPagesShort.append({
        'pageId' : n['id'],
        'pageTitle' : n['title'],
        'parentId' : n['parentId'],
        'spaceId' : n['spaceId'],
        }
    )

for n in allPagesShort:
    if n['parentId'] is None:       # only applies to TOP page
        # create parent page using n['pageTitle']
        # create parent folder (same name as parent page)
        currentParent = n['pageId']         # sets the parent for the next IF statent
    break

#
# Handling output folder path
#
currentDir = os.getcwd()
scriptDir = os.path.dirname(os.path.abspath(__file__))

try:
    outdir = sys.argv[3]
except IndexError as exc:
    outdir = os.path.join(scriptDir,"output")
    outdir = os.path.join(outdir,str(spaceId) + "-" + str(spaceTitle.json()['name']))
    print('No output folder supplied, using current path: ' + outdir)
else:
    outdir = os.path.join(outdir,str(spaceId) + "-" + str(spaceTitle.json()['name']))

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

if not os.path.exists(outdirStyles + '/site.css'):
    os.system('cp ' + scriptDir + '/styles/site.css "' + outdirStyles + '"')

def getBodyExportView(argPageID):       # copied from byLabel
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageID) + '?expand=body.export_view'
    response = requests.get(serverURL, auth=(userName, apiToken))
    return(response)

# get page labels
def getPageLabels(argPageID):           # copied from byLabel
    htmlLabels = []
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/api/v2/pages/' + str(argPageID) + '/labels'
    response = requests.get(serverURL, auth=(userName, apiToken),timeout=30).json()
    for l in response['results']:
        htmlLabels.append(l['name'])
    #htmlLabels = ",".join(htmlLabels)
    return(htmlLabels)

def getAttachments(argPageID):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageID) + '?expand=children.attachment'
    response = requests.get(serverURL, auth=(userName, apiToken),timeout=30)
    myAttachments = response.json()['children']['attachment']['results']
    for attachment in myAttachments:
        attachmentTitle = attachment['title'].replace(":","-").replace(" ","_").replace("%20","_").replace("%80","").replace("%8B","").replace("%E2","").replace('\u200b','').replace('\u200c','').replace("%5B","[").replace("%5D","]")
        attachmentURL = 'https://' + atlassianSite + '.atlassian.net/wiki' + attachment['_links']['download']
        requestAttachment = requests.get(attachmentURL, auth=(userName, apiToken),allow_redirects=True,timeout=30)
        open(os.path.join(outdirAttach,attachmentTitle), 'wb').write(requestAttachment.content)
        myAttachmentsList.append(attachmentTitle)
    return(myAttachmentsList)

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

#
# Define RST file header
#
def setRstHeader(argLabels):
    myHeader = """.. tags:: """ + str(argLabels) + """

"""
    return(myHeader)


#
# Clear all lists (just in case)
#
myAttachments = []
myAttachmentsList = []
myEmbeds = []
myEmbedsExternals = []
myEmoticons = []
myEmoticonsList = []
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
    for embedExt in myEmbedsExternals:
        origEmbedExternalPath = embedExt['src']
        origEmbedExternalName = origEmbedExternalPath.rsplit('/',1)[-1].rsplit('?')[0]
        origEmbedExternalName = str(argPageID) + "-" + str(myEmbedsExternalsCounter) + "-" + origEmbedExternalName
        myEmbedExternalPath = os.path.join(outdirAttach,origEmbedExternalName)
        toDownload = requests.get(origEmbedExternalPath, allow_redirects=True)
        #myEmbedExternalPath = myEmbedExternalPath.replace(":","-").replace("%20"," ")      # replace offending characters from file name
        myEmbedExternalPath = myEmbedExternalPath.replace(":","-").replace(" ","_").replace("%20","_").replace("%80","").replace("%8B","").replace("%E2","").replace('\u200b','').replace('\u200c','').replace("%5B","[").replace("%5D","]")
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
        origEmbedPath = embed['src']
        origEmbedName = origEmbedPath.rsplit('/',1)[-1].rsplit('?')[0]
        #myEmbedName = origEmbedName.replace(":","-").replace(" ","_").replace("%20","_")        # replace offending characters from file name
        myEmbedName = origEmbedName.replace(":","-").replace(" ","_").replace("%20","_").replace("%80","").replace("%8B","").replace("%E2","").replace('\u200b','').replace('\u200c','').replace("%5B","[").replace("%5D","]")
        myEmbedPath = attachDir + myEmbedName
        myEmbedPathFull = os.path.join(outdir,myEmbedPath)
        print("Embed path: " + myEmbedPath)
        img = Image.open(myEmbedPathFull)
        if img.width < 600:
            embed['width'] = img.width
        else:
            embed['width'] = 600
        img.close
        embed['height'] = "auto"
        embed['onclick'] = "window.open(\"" + myEmbedPath + "\")"
        embed['src'] = myEmbedPath
    #
    # dealing with "emoticon"
    #
    myEmoticons = soup.findAll('img',class_="emoticon")     # atlassian-check_mark, or
    print(str(len(myEmoticons)) + " emoticons.")
    for emoticon in myEmoticons:
        requestEmoticons = requests.get(emoticon['src'], auth=(userName, apiToken))
        myEmoticonTitle = emoticon['src'].rsplit('/',1)[-1]
        if myEmoticonTitle not in myEmoticonsList:
            myEmoticonsList.append(myEmoticonTitle)
            print("Getting emoticon: " + myEmoticonTitle)
            filePath = os.path.join(outdirEmoticons,myEmoticonTitle)
            open(filePath, 'wb').write(requestEmoticons.content)
        myEmoticonPath = emoticonsDir + myEmoticonTitle
        emoticon['src'] = myEmoticonPath
    #
    # Putting HTML together
    #
    prettyHTML = soup.prettify()
    htmlFile = open(htmlFilePath, 'w')
    htmlFile.write(htmlPageHeader)
    htmlFile.write(prettyHTML)
    htmlFile.write(footersHTML)
    htmlFile.close()
    print("Exported HTML file " + htmlFileName)
    #
    # convert html to rst
    #
    rstFileName = str(argTitle) + '.rst'
    rstFilePath = os.path.join(outdir,rstFileName)
    outputRST = pypandoc.convert_file(str(htmlFilePath), 'rst', format='html',extra_args=['--standalone','--wrap=none','--list-tables'])
    rstPageHeader = setRstHeader(myBodyExportViewLabels)
    rstFile = open(rstFilePath, 'w')
    rstFile.write(rstPageHeader)            # assing .. tags:: to rst file for future reference
    rstFile.write(outputRST)
    rstFile.close()
    print("Exported RST file: " + rstFileName)

###


## based on byLabel
## available values
### ['id'],
### ['title'],
### ['parentId'],
### ['spaceId'],
###        'pageId' : n['id'],
###        'pageTitle' : n['title'],
###        'parentId' : n['parentId'],
###        'spaceId' : n['spaceId'],


for p in allPagesShort:
    print(str(p['pageId']))
    myBodyExportView = getBodyExportView(p['pageId']).json()
    myBodyExportViewHtml = myBodyExportView['body']['export_view']['value']
    myBodyExportViewName = p['pageTitle']
    myBodyExportViewTitle = p['pageTitle'].replace("/","-")
    myBodyExportViewLabels = getPageLabels(p['pageId'])
    myBodyExportViewLabels = ",".join(myBodyExportViewLabels)
    myPageURL = str(myBodyExportView['_links']['base']) + str(myBodyExportView['_links']['webui'])
    htmlPageHeader = setHtmlHeader(myBodyExportViewTitle,myPageURL,myBodyExportViewLabels)
    dumpHtml(myBodyExportViewHtml,myBodyExportViewTitle,p['pageId'])


"""
        print('Top Parent: ' + str(n['pageId']))
        print('CurrentParent = ' + str(type(currentParent)))
        #break
    elif (n['parentId'] == currentParent):
        print("match for (n[parentId] == currentParent)")
        print(str(n['pageId']) + ' = ' + str(type(n['pageId'])))
        # the current page has the currentParent
        print("create page under parent folder")
        print('Creating page ' + str(n['pageTitle']) + ' under ' + str(currentParent))
        nextParent = n['pageId']
        print('Next parent will be ' + str(nextParent))
    elif (n['parentId'] is not currentParent):
        print("Match for: (n['parentId'] is not currentParent)")
        #print(str(n['pageId']) + ' = ' + str(type(n['pageId'])))
        #currentParent = n['pageId']
        #print('Next parent will be ' + str(nextParent))
"""
