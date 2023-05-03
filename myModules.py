import requests
import os.path
import json
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup as bs
import sys
import pypandoc
from PIL import Image
import re

"""
Arguments needed to run these functions centrally:
* outdirs: outdir, attachDir, emoticonDir, stylesDir
* page details: Title, ID, Parent, orig URL, Space
* space details: Title, ID, site
* Confluence API: Username, Password

CURRENT STATE
* fixed getting output folders
* next up: getAttachments

"""
#
# Set path for where script is
#
scriptDir = os.path.dirname(os.path.abspath(__file__))

#
# Create the output folders, set to match Sphynx structure
#
def setDirs(argOutdir="output"):        # setting default to output
    attachDir = "_images/"
    emoticonsDir = "_images/"
    stylesDir = "_static/"
    outdirAttach = os.path.join(argOutdir,attachDir)
    outdirEmoticons = os.path.join(argOutdir,emoticonsDir)
    outdirStyles = os.path.join(argOutdir,stylesDir)
    #return outdirAttach,outdirEmoticons,outdirStyles
    return[outdirAttach, outdirEmoticons, outdirStyles]      # returns a list

def mkOutdirs(argOutdir="output"):       # setting default to output
    outdirList = setDirs(argOutdir)
    outdirAttach = outdirList[0]
    outdirEmoticons = outdirList[1]
    outdirStyles = outdirList[2]

    if not os.path.exists(argOutdir):
        os.mkdir(argOutdir)

    if not os.path.exists(outdirAttach):
        os.mkdir(outdirAttach)

    if not os.path.exists(outdirEmoticons):
        os.mkdir(outdirEmoticons)

    if not os.path.exists(outdirStyles):
        os.mkdir(outdirStyles)

    if not os.path.exists(outdirStyles + '/site.css'):
        os.system('cp ' + scriptDir + '/styles/site.css "' + outdirStyles + '"')
    return(outdirList)

def getSpaceTitle(argSite,argSpaceId,argUsername,argApiToken):
    serverURL = 'https://' + argSite + '.atlassian.net/wiki/api/v2/spaces/' + str(argSpaceId)
    response = requests.get(serverURL, auth=(argUsername, argApiToken),timeout=30).json()['name']
    return(response)

def getSpacesAll(argSite,argUsername,argApiToken):
    #spaceList = []
    serverURL = 'https://' + argSite + '.atlassian.net/wiki/api/v2/spaces/?limit=250'
    response = requests.get(serverURL, auth=(argUsername,argApiToken),timeout=30)
    response.raise_for_status()  # raises exception when not a 2xx response
    print(response.json().keys())
    spaceList = response.json()['results']
    while 'next' in response.json()['_links'].keys():
        #print(str(response.json()['_links']))
        cursorServerURL = serverURL + '&cursor' + response.json()['_links']['next'].split('cursor')[1]
        #print(serverURL)
        response = requests.get(cursorServerURL, auth=(argUsername,argApiToken),timeout=30)
        spaceList = spaceList + response.json()['results']
    return(spaceList)

def getPagesFromSpace(argSite,argSpaceId,argUsername,argApiToken):
    pageList = []
    serverURL = 'https://' + argSite + '.atlassian.net/wiki/api/v2/spaces/' + str(argSpaceId) + '/pages?status=current&limit=250'
    response = requests.get(serverURL, auth=(argUsername,argApiToken),timeout=30)
    pageList = response.json()['results']
    while 'next' in response.json()['_links'].keys():
        print(str(response.json()['_links']))
        cursorServerURL = serverURL + '&cursor' + response.json()['_links']['next'].split('cursor')[1]
        response = requests.get(cursorServerURL, auth=(argUsername,argApiToken),timeout=30)
        pageList = pageList + response.json()['results']
    return(pageList)

def getBodyExportView(argSite,argPageId,argUsername,argApiToken):
    serverURL = 'https://' + argSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageId) + '?expand=body.export_view'
    response = requests.get(serverURL, auth=(argUsername, argApiToken))
    return(response)

def getPageName(argSite,argPageId,argUsername,argApiToken):
    serverURL = 'https://' + argSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageId)
    r_pagetree = requests.get(serverURL, auth=(argUsername, argApiToken),timeout=30)
    return(r_pagetree.json()['id'] + "_" + r_pagetree.json()['title'])

def getAttachments(argSite,argPageId,argOutdirAttach,argUsername,argApiToken):
    myAttachmentsList = []
    serverURL = 'https://' + argSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageId) + '?expand=children.attachment'
    response = requests.get(serverURL, auth=(argUsername, argApiToken),timeout=30)
    myAttachments = response.json()['children']['attachment']['results']
    for attachment in myAttachments:
        attachmentTitle = requests.utils.unquote(attachment['title'])
        print("Downloading: " + attachmentTitle)
        #attachmentTitle = n['title']
        #attachmentTitle = attachmentTitle.replace(":","-").replace(" ","_").replace("%20","_")          # replace offending characters from file name
        #myTail = n['_links']['download']
        attachmentURL = 'https://' + argSite + '.atlassian.net/wiki' + attachment['_links']['download']
        requestAttachment = requests.get(attachmentURL, auth=(argUsername, argApiToken),allow_redirects=True,timeout=30)
        filePath = os.path.join(argOutdirAttach,attachmentTitle)
        #if (requestAttachment.content.decode("utf-8")).startswith("<!doctype html>"):
        #    filePath = str(filePath) + ".html"
        open(os.path.join(argOutdirAttach,attachmentTitle), 'wb').write(requestAttachment.content)
        myAttachmentsList.append(attachmentTitle)
    return(myAttachmentsList)

# get page labels
def getPageLabels(argSite,argPageId,argUsername,argApiToken):
    htmlLabels = []
    serverURL = 'https://' + argSite + '.atlassian.net/wiki/api/v2/pages/' + str(argPageId) + '/labels'
    response = requests.get(serverURL, auth=(argUsername,argApiToken),timeout=30).json()
    for l in response['results']:
        htmlLabels.append(l['name'])
    #htmlLabels = ",".join(htmlLabels)
    return(htmlLabels)

def dumpHtml(argSite,argHTML,argTitle,argPageId,argOutdir,argPageLabels,argUserName,argApiToken):
    myEmoticonsList = []
    myOutdirs = mkOutdirs(argOutdir)
    soup = bs(argHTML, "html.parser")
    htmlFileName = str(argTitle) + '.html'
    htmlFilePath = os.path.join(argOutdir,htmlFileName)
    myAttachments = getAttachments(argSite,argPageId,str(myOutdirs[0]),argUserName,argApiToken)

    #
    # dealing with "confluence-embedded-image confluence-external-resource"
    #
    myEmbedsExternals = soup.findAll('img',class_="confluence-embedded-image confluence-external-resource")
    print(myEmbedsExternals)
    myEmbedsExternalsCounter = 0
    for embedExt in myEmbedsExternals:
        origEmbedExternalPath = embedExt['src']
        origEmbedExternalName = origEmbedExternalPath.rsplit('/',1)[-1].rsplit('?')[0]
        origEmbedExternalName = str(argPageId) + "-" + str(myEmbedsExternalsCounter) + "-" + origEmbedExternalName
        myEmbedExternalPath = os.path.join(myOutdirs[0],origEmbedExternalName)
        toDownload = requests.get(origEmbedExternalPath, allow_redirects=True)
        myEmbedExternalPath = myEmbedExternalPath.replace(":","-").replace("%20"," ")      # replace offending characters from file name
        try:
            open(myEmbedExternalPath,'wb').write(toDownload.content)
        except:
            print(origEmbedExternalPath)
        #print("Embed External path: " + str(myEmbedExternalPath))
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
        #print("origEmbedPath = " + origEmbedPath)
        origEmbedName = origEmbedPath.rsplit('/',1)[-1].rsplit('?')[0]
        #print("origEmbedName = " + origEmbedName)
        myEmbedName = requests.utils.unquote(origEmbedName)
        #print("myEmbedName = " + myEmbedName)
        #myEmbedName = origEmbedName.replace(":","-").replace(" ","_").replace("%20","_")        # replace offending characters from file name
        myEmbedPath = myOutdirs[0] + myEmbedName
        #print("myEmbedPath = " + myEmbedPath)
        #myEmbedPathFull = os.path.join(argOutdir,myEmbedPath)
        #print("argOutdir = " + argOutdir)
        #print("myEmbedPathFull = " + myEmbedPathFull)
        try:
            img = Image.open(myEmbedPath)
        except:
            print("WARNING: Skipping embed file " + myEmbedPath + " due to issues.")
        else:
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
    #myEmoticons = soup.findAll('img',class_="emoticon")     # atlassian-check_mark, or
    myEmoticons = soup.findAll('img',class_=re.compile("emoticon"))     # atlassian-check_mark, or
    print(str(len(myEmoticons)) + " emoticons.")
    for emoticon in myEmoticons:
        requestEmoticons = requests.get(emoticon['src'], auth=(argUserName, argApiToken))
        myEmoticonTitle = emoticon['src'].rsplit('/',1)[-1]
        if myEmoticonTitle not in myEmoticonsList:
            myEmoticonsList.append(myEmoticonTitle)
            print("Getting emoticon: " + myEmoticonTitle)
            filePath = os.path.join(myOutdirs[1],myEmoticonTitle)
            open(filePath, 'wb').write(requestEmoticons.content)
        myEmoticonPath = myOutdirs[1] + myEmoticonTitle
        emoticon['src'] = myEmoticonPath
    myBodyExportView = getBodyExportView(argSite,argPageId,argUserName,argApiToken).json()
    pageUrl = str(myBodyExportView['_links']['base']) + str(myBodyExportView['_links']['webui'])
    myHeader = """<html>
<head>
<title>""" + argTitle + """</title>
<link rel="stylesheet" href=\"""" + myOutdirs[2] + """site.css" type="text/css" />
<meta name="generator" content="confluenceExportHTML" />
<META http-equiv="Content-Type" content="text/html; charset=UTF-8">
<meta name="labels" content=\"""" + str(argPageLabels) + """\">
<meta name="pageID" content=\"""" + str(argPageId) + """\">
</head>
<body>
<h2>""" + argTitle + """</h2>
<p>Original URL: <a href=\"""" + pageUrl + """\"> """+argTitle+"""</a><hr>"""


    #
    # Putting HTML together
    #
    prettyHTML = soup.prettify()
    htmlFile = open(htmlFilePath, 'w')
    htmlFile.write(myHeader)
    htmlFile.write(prettyHTML)
    htmlFile.write(setFooterHTML())
    htmlFile.close()
    print("Exported HTML file " + htmlFileName)
    #
    # convert html to rst
    #
    rstFileName = str(argTitle) + '.rst'
    rstFilePath = os.path.join(argOutdir,rstFileName)
    try:
        outputRST = pypandoc.convert_file(str(htmlFilePath), 'rst', format='html',extra_args=['--standalone','--wrap=none','--list-tables'])
    except:
        print("There was an issue generating an RST file from the page.")
    else:
        rstPageHeader = setRstHeader(argPageLabels)
        rstFile = open(rstFilePath, 'w')
        rstFile.write(rstPageHeader)            # assing .. tags:: to rst file for future reference
        rstFile.write(outputRST)
        rstFile.close()
        print("Exported RST file: " + rstFileName)


#
# Define HTML page header
#
def setHtmlHeader(argTitle,argURL,argLabels,argPageId,argOutdirStyles):
    myHeader = """<html>
<head>
<title>""" + argTitle + """</title>
<link rel="stylesheet" href=\"""" + argOutdirStyles + """site.css" type="text/css" />
<meta name="generator" content="confluenceExportHTML" />
<META http-equiv="Content-Type" content="text/html; charset=UTF-8">
<meta name="labels" content=\"""" + str(argLabels) + """\">
<meta name="pageID" content=\"""" + str(argPageId) + """\">
</head>
<body>
<h2>""" + argTitle + """</h2>
<p>Original URL: <a href=\"""" + argURL + """\"> """+argTitle+"""</a><hr>"""
    return(myHeader)

#
# Define HTML page footer
#
def setFooterHTML():
    n = """</body>
</html>"""
    return(n)


#
# Define RST file header
#
def setRstHeader(argLabels):
    myHeader = """.. tags:: """ + str(argLabels) + """

"""
    return(myHeader)
