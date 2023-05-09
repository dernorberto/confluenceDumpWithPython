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
#from pathvalidate import sanitize_filename

##
## dealing with retries
## src: https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/
##
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

apiToken = os.environ["atlassianAPIToken"]
userName = os.environ["atlassianUserEmail"]

try:
    atlassianSite = sys.argv[1]
except IndexError:
    raise SystemExit(f"Usage: <script>.py <site> <space Key>")
print('Site: ' + atlassianSite)

try:
    spaceKey = sys.argv[2]
except IndexError:
    raise SystemExit(f"Usage: <script>.py <site> <space Key>")
print('Looking for space: ' + spaceKey)

def getSpaceTitle(argSpaceId):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/api/v2/spaces/' + str(argSpaceId)
    response = requests.get(serverURL, auth=(userName, apiToken),timeout=30).json()['name']
    return(response)

spaceList = []
def getSpacesAll(argSite):
    serverURL = 'https://' + argSite + '.atlassian.net/wiki/api/v2/spaces/' + '?limit=250'
    response = requests.get(serverURL, auth=(userName, apiToken),timeout=30)
    spaceList = response.json()['results']
    while 'next' in response.json()['_links'].keys():
        print(str(response.json()['_links']))
        cursorServerURL = serverURL + '&cursor' + response.json()['_links']['next'].split('cursor')[1]
        print(serverURL)
        response = requests.get(cursorServerURL, auth=(userName, apiToken),timeout=30)
        spaceList = spaceList + response.json()['results']
    return(spaceList)

allSpacesFull = getSpacesAll(atlassianSite)
allSpacesShort = []
i = 0
for n in allSpacesFull:
    i = i +1
    #{'name': 'Team',
    #  'key': 'OPTEAM',
    # 'id': 1048577,
    # 'homepageId': 819205,
    # 'description': None, '
    # icon': None,
    # 'status': 'current'}
    if (n['key'] == spaceKey):
        spaceId = n['id']
        spaceName = n['name']
        currentParent = n['homepageId']
    allSpacesShort.append({
        'spaceKey' : n['key'],
        'spaceId' : n['id'],
        'spaceName' : n['name'],
        'homepageId' : n['homepageId'],
        'spaceDescription' : n['description'],
        }
    )


#for n in getSpacesAll(atlassianSite).json()['results']:
#    if (n['key'] == spaceKey):
#        spaceId = n['id']
#        print('Space Key: ' + str(spaceKey) + ', space ID: ' + str(spaceId))

pageList = []
def getPagesFromSpace(argSpaceId):
    # ref: https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-page/#api-spaces-id-pages-get
    #  url = "https://{your-domain}/wiki/api/v2/spaces/{id}/pages"
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/api/v2/spaces/' + str(argSpaceId) + '/pages?status=current&limit=250'
    response = requests.get(serverURL, auth=(userName, apiToken),timeout=30)
    pageList = response.json()['results']
    while 'next' in response.json()['_links'].keys():
        print(str(response.json()['_links']))
        cursorServerURL = serverURL + '&cursor' + response.json()['_links']['next'].split('cursor')[1]
        response = requests.get(cursorServerURL, auth=(userName, apiToken),timeout=30)
        pageList = pageList + response.json()['results']
    return(pageList)

allPagesFull = getPagesFromSpace(spaceId)
allPagesShort = []
i = 0
for n in allPagesFull:
    i = i +1
    #print(i, n['id'], n['title'], n['parentId'], n['spaceId'])
    #if n['parentId'] is None:               # only applies to TOP page
    #    currentParent = n['id']         # sets the parent for the next IF statent
    #    print('Parent page: ' + n['title'] + '(' + str(n['id']) + ')')
    allPagesShort.append({
        'pageId' : n['id'],
        'pageTitle' : n['title'],
        'parentId' : n['parentId'],
        'spaceId' : n['spaceId'],
        }
    )

#
# Handling output folder path
#
currentDir = os.getcwd()
scriptDir = os.path.dirname(os.path.abspath(__file__))

try:
    outdir = sys.argv[3]
except IndexError as exc:
    outdir = os.path.join(scriptDir,"output")
    outdir = os.path.join(outdir,str(spaceId) + "-" + str(spaceName))
    print('No output folder supplied, using current path: ' + outdir)
else:
    outdir = os.path.join(outdir,str(spaceId) + "-" + str(spaceName))

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
    response = requests.get(serverURL, auth=(userName, apiToken),timeout=30)
    return(response)

# get page labels
def getPageLabels(argPageID):           # copied from byLabel
    htmlLabels = []
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/api/v2/pages/' + str(argPageID) + '/labels'
    response = requests.get(serverURL, auth=(userName, apiToken),timeout=30).json()
    for l in response['results']:
        htmlLabels.append(l['name'])
    return(htmlLabels)

def getAttachments(argPageID):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageID) + '?expand=children.attachment'
    response = requests.get(serverURL, auth=(userName, apiToken),timeout=30)
    myAttachments = response.json()['children']['attachment']['results']
    for attachment in myAttachments:
        attachmentTitle = requests.utils.unquote(attachment['title'])
        print("Getting attachment: " + attachmentTitle)
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
    myEmbedsExternals = soup.findAll('img',class_=re.compile("confluence-external-resource$"))
    myEmbedsExternalsCounter = 0
    for embedExt in myEmbedsExternals:
        origEmbedExternalPath = embedExt['src']
        if "confluence/placeholder/unknown-attachment" in embedExt['src']:
            ##
            ## dealing with: "Max retries exceeded with url: /plugins/servlet/confluence/placeholder/unknown-attachment"
            ##
            print('Ignoring unknown-attachment')
        else:
            origEmbedExternalName = requests.utils.unquote(origEmbedExternalPath.rsplit('/',1)[-1].rsplit('?')[0])
            origEmbedExternalName = str(argPageID) + "-" + str(myEmbedsExternalsCounter) + "-" + origEmbedExternalName
            myEmbedExternalPath = os.path.join(outdirAttach,origEmbedExternalName)
            toDownload = requests.get(origEmbedExternalPath, allow_redirects=True,timeout=30)
            try:
                open(myEmbedExternalPath,'wb').write(toDownload.content)
            except:
                print('Did not save ' + myEmbedExternalPath)
            print("Embed External path: " + str(myEmbedExternalPath))
            try:
                img = Image.open(myEmbedExternalPath)
            except:
                print('invalid embed external')
            else:
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
        if "confluence/placeholder/unknown-attachment" in embed['src']:
            ##
            ## dealing with: "Max retries exceeded with url: /plugins/servlet/confluence/placeholder/unknown-attachment"
            ##
            print('Skipping unknown-attachment')
        else:
            origEmbedName = origEmbedPath.rsplit('/',1)[-1].rsplit('?')[0]
            myEmbedName = requests.utils.unquote(origEmbedName)
            #print("origEmbedName: " + origEmbedName)
            #print("myEmbedName: " + myEmbedName)
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
        if emoticon['src'].startswith('https://' + atlassianSite):
            requestEmoticons = requests.get(emoticon['src'], auth=(userName, apiToken),timeout=30)
            #print('Getting emoticon: ' + emoticon['src'])
            myEmoticonTitle = emoticon['src'].rsplit('/',1)[-1]
            if myEmoticonTitle not in myEmoticonsList:
                myEmoticonsList.append(myEmoticonTitle)
                print("Getting emoticon: " + myEmoticonTitle)
                filePath = os.path.join(outdirEmoticons,myEmoticonTitle)
                open(filePath, 'wb').write(requestEmoticons.content)
            myEmoticonPath = emoticonsDir + myEmoticonTitle
            emoticon['src'] = myEmoticonPath
        else:
            ##
            ## dealing with: "Invalid URL '/wiki/s/... ': No scheme supplied"
            ##
            print('Skipping, url starts with /wiki/s or /s/ or No scheme supplied')
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
    try:
        rstFileName = str(argTitle) + '.rst'
        rstFilePath = os.path.join(outdir,rstFileName)
        outputRST = pypandoc.convert_file(str(htmlFilePath), 'rst', format='html',extra_args=['--standalone','--wrap=none','--list-tables'])
    except:
        print("WARNING, could not export RST due to an issue")
    else:
        rstPageHeader = setRstHeader(myBodyExportViewLabels)
        rstFile = open(rstFilePath, 'w')
        rstFile.write(rstPageHeader)            # assing .. tags:: to rst file for future reference
        rstFile.write(outputRST)
        rstFile.close()
        print("Exported RST file: " + rstFileName)

###


## based on byLabel
## available values
###        'pageId' : n['id'],
###        'pageTitle' : n['title'],
###        'parentId' : n['parentId'],
###        'spaceId' : n['spaceId'],

print(str(len(allPagesShort)) + ' pages to export')
pageCounter = 0
for p in allPagesShort:
    pageCounter = pageCounter + 1
    myBodyExportView = getBodyExportView(p['pageId']).json()
    myBodyExportViewHtml = myBodyExportView['body']['export_view']['value']
    myBodyExportViewName = p['pageTitle']
    myBodyExportViewTitle = p['pageTitle'].replace("/","-")
    print()
    print("Getting page #" + str(pageCounter) + '/' + str(len(allPagesShort)) + ', ' + myBodyExportViewTitle + ', ' + str(p['pageId']))
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
