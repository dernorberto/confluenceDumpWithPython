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
def getDirs(argOutdir):
    attachDir = "_images/"
    emoticonsDir = "_images/"
    stylesDir = "_static/"
    outdirAttach = os.path.join(argOutdir,attachDir)
    outdirEmoticons = os.path.join(argOutdir,emoticonsDir)
    outdirStyles = os.path.join(argOutdir,stylesDir)
    #return outdirAttach,outdirEmoticons,outdirStyles
    return[outdirAttach, outdirEmoticons, outdirStyles]      # returns a list

def getOutdirs(argOutdir):
    outdirAttach = getDirs(argOutdir)[0]
    outdirEmoticons = getDirs(argOutdir)[1]
    outdirStyles = getDirs(argOutdir)[2]

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

def getBodyExportView(argSite,argPageID,argUsername,argApiToken):
    serverURL = 'https://' + argSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageID) + '?expand=body.export_view'
    response = requests.get(serverURL, auth=(argUsername, argApiToken))
    return(response)

def getPageName(argSite,argPageID,argUsername,argApiToken):
    serverURL = 'https://' + argSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageID)
    r_pagetree = requests.get(serverURL, auth=(argUsername, argApiToken),timeout=30)
    return(r_pagetree.json()['id'] + "_" + r_pagetree.json()['title'])

def getAttachments(argPageID):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageID) + '?expand=children.attachment'
    response = requests.get(serverURL, auth=(userName, apiToken),timeout=30)
    myAttachments = response.json()['children']['attachment']['results']
    for attachment in myAttachments:
        attachmentTitle = requests.utils.unquote(attachment['title'])
        print("Downloading: " + attachmentTitle)
        #attachmentTitle = n['title']
        #attachmentTitle = attachmentTitle.replace(":","-").replace(" ","_").replace("%20","_")          # replace offending characters from file name
        #myTail = n['_links']['download']
        attachmentURL = 'https://' + atlassianSite + '.atlassian.net/wiki' + attachment['_links']['download']
        requestAttachment = requests.get(attachmentURL, auth=(userName, apiToken),allow_redirects=True,timeout=30)
        filePath = os.path.join(outdirAttach,attachmentTitle)
        #if (requestAttachment.content.decode("utf-8")).startswith("<!doctype html>"):
        #    filePath = str(filePath) + ".html"
        open(os.path.join(outdirAttach,attachmentTitle), 'wb').write(requestAttachment.content)
        myAttachmentsList.append(attachmentTitle)
    return(myAttachmentsList)

# get page labels
def getPageLabels(argSite,argPageID,argUsername,argApiToken):
    htmlLabels = []
    serverURL = 'https://' + argSite + '.atlassian.net/wiki/api/v2/pages/' + str(argPageID) + '/labels'
    response = requests.get(serverURL, auth=(argUsername,argApiToken),timeout=30).json()
    for l in response['results']:
        htmlLabels.append(l['name'])
    #htmlLabels = ",".join(htmlLabels)
    return(htmlLabels)

def dumpHtml(argHTML,argTitle,argPageID,argOutdir):
    soup = bs(argHTML, "html.parser")
    htmlFileName = str(argTitle) + '.html'
    htmlFilePath = os.path.join(argOutdir,htmlFileName)
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
        origEmbedPath = embed['src']
        origEmbedName = origEmbedPath.rsplit('/',1)[-1].rsplit('?')[0]
        myEmbedName = requests.utils.unquote(origEmbedName)
        #myEmbedName = origEmbedName.replace(":","-").replace(" ","_").replace("%20","_")        # replace offending characters from file name
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
        print(emoticon['src'])
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


#
# Define HTML page header
#
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
# Define RST file header
#
def setRstHeader(argLabels):
    myHeader = """.. tags:: """ + str(argLabels) + """

"""
    return(myHeader)
