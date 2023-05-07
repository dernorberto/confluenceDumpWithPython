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
attachDir = "_images/"
emoticonsDir = "_images/"
stylesDir = "_static/"

def setVariables():
    dictVars = {}
    dictVars['attachDir'] = "_images/"
    dictVars['emoticonsDir'] = "_images/"
    dictVars['stylesDir'] = "_static/"
    attachDir = "_images/"
    emoticonsDir = "_images/"
    stylesDir = "_static/"
    return(dictVars)
#
# Create the output folders, set to match Sphynx structure
#
def setDirs(argOutdir="output"):        # setting default to output
    myVars = setVariables()
    outdirAttach = os.path.join(argOutdir,myVars['attachDir'])
    outdirEmoticons = os.path.join(argOutdir,myVars['emoticonsDir'])
    outdirStyles = os.path.join(argOutdir,myVars['stylesDir'])
    return[outdirAttach, outdirEmoticons, outdirStyles]      # returns a list

def mkOutdirs(argOutdir="output"):       # setting default to output
    myVars = setVariables()
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

    if not os.path.exists(outdirStyles + '/confluence.css'):
        os.system('cp ' + scriptDir + '/styles/confluence.css "' + outdirStyles + '"')
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

def getPageParent(argSite,argPageId,argUsername,argApiToken):
    serverURL = 'https://' + argSite + '.atlassian.net/wiki/api/v2/pages/' + str(argPageId)
    response = requests.get(serverURL, auth=(argUsername, argApiToken),timeout=30)
    return(response.json()['parentId'])

def getAttachments(argSite,argPageId,argOutdirAttach,argUsername,argApiToken):
    myAttachmentsList = []
    serverURL = 'https://' + argSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageId) + '?expand=children.attachment'
    response = requests.get(serverURL, auth=(argUsername, argApiToken),timeout=30)
    myAttachments = response.json()['children']['attachment']['results']
    for attachment in myAttachments:
        attachmentTitle = requests.utils.unquote(attachment['title']).replace(" ","_").replace(":","-")         # I want attachments without spaces
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
    htmlLabels = ",".join(htmlLabels)
    return(htmlLabels)

def getPagePropertiesChildren(argSite,argHTML,argOutdir,argUserName,argApiToken):
    myPagePropertiesChildren = []
    myPagePropertiesChildrenDict = {}
    soup = bs(argHTML, "html.parser")
    myPagePropertiesItems = soup.findAll('td',class_="title")
    myPagePropertiesItemsCounter = 0
    for n in myPagePropertiesItems:
        myPageID = str(n['data-content-id'])
        myPagePropertiesChildren.append(str(n['data-content-id']))
        myPagePropertiesItemsCounter = myPagePropertiesItemsCounter + 1
        myPageName = getPageName(argSite,int(myPageID),argUserName,argApiToken).rsplit('_',1)[1].replace(":","-").replace(" ","_").replace("%20","_")          # replace offending characters from file name
        myPagePropertiesChildrenDict.update({ myPageID:{}})
        myPagePropertiesChildrenDict[myPageID].update({"ID": myPageID})
        myPagePropertiesChildrenDict[myPageID].update({"Name": myPageName})
    print(str(myPagePropertiesItemsCounter) + " Pages")
    print("Exporting to: " + argOutdir)
    return[myPagePropertiesChildren,myPagePropertiesChildrenDict]


def dumpHtml(argSite,argHTML,argTitle,argPageId,argOutdirBase,argOutdirContent,argPageLabels,argPageParent,argUserName,argApiToken,argSphinxCompatible=True,argType="common"):
    myVars = setVariables()
    print("myModules.py receiving arg argSphinxCompatible = " + str(argSphinxCompatible))
    myEmoticonsList = []
    myOutdirContent = argOutdirContent
    #myOutdirContent = os.path.join(argOutdirBase,str(argPageId) + "-" + str(argTitle))      # this is for html and rst files
    if not os.path.exists(myOutdirContent):
        os.mkdir(myOutdirContent)
    #myOutdir = os.path.join(argOutdir,str(argPageId) + "-" + str(argTitle))
    myOutdirs = mkOutdirs(argOutdirBase)        # this is for everything for _images and _static
    myVars = setVariables()     # create a dict with the 3 folder paths: attach, emoticons, styles

    soup = bs(argHTML, "html.parser")
    htmlFileName = str(argTitle) + '.html'
    htmlFilePath = os.path.join(myOutdirContent,htmlFileName)
    myAttachments = getAttachments(argSite,argPageId,str(myOutdirs[0]),argUserName,argApiToken)
    #
    # used for pageprops mode
    #
    #if (argType == "child"):
        #myReportChildrenDict = getPagePropertiesChildren(argSite,argHTML,argOutdir,argUserName,argApiToken)[1]              # get list of all page properties children
        #myReportChildrenDict[argPageId].update({"Filename": argHtmlFileName})
    if (argType == "report"):
        myReportChildrenDict= getPagePropertiesChildren(argSite,argHTML,myOutdirContent,argUserName,argApiToken)[1]      # dict
        myPagePropertiesItems = soup.findAll('td',class_="title")       # list
        for item in myPagePropertiesItems:
            id = item['data-content-id']
            item.a['href'] = (myReportChildrenDict[id]['Name'] + '.html')
    #
    # dealing with "confluence-embedded-image confluence-external-resource"
    #
    myEmbedsExternals = soup.findAll('img',class_="confluence-embedded-image confluence-external-resource")
    myEmbedsExternalsCounter = 0
    for embedExt in myEmbedsExternals:
        origEmbedExternalPath = embedExt['src']     # online link to file
        origEmbedExternalName = origEmbedExternalPath.rsplit('/',1)[-1].rsplit('?')[0]      # just the file name
        myEmbedExternalName = str(argPageId) + "-" + str(myEmbedsExternalsCounter) + "-" + requests.utils.unquote(origEmbedExternalName).replace(" ", "_").replace(":","-")    # local filename
        myEmbedExternalPath = os.path.join(myOutdirs[0],myEmbedExternalName)        # local filename and path
        if argSphinxCompatible == True:
            myEmbedExternalPathRelative = os.path.join(str('../' + myVars['attachDir']),myEmbedExternalName)
        else:
            myEmbedExternalPathRelative = os.path.join(myVars['attachDir'],myEmbedExternalName)
        toDownload = requests.get(origEmbedExternalPath, allow_redirects=True)
        try:
            open(myEmbedExternalPath,'wb').write(toDownload.content)
        except:
            print(origEmbedExternalPath)
        img = Image.open(myEmbedExternalPath)
        if img.width < 600:
            embedExt['width'] = img.width
        else:
            embedExt['width'] = 600
        img.close
        embedExt['height'] = "auto"
        embedExt['onclick'] = "window.open(\"" + str(myEmbedExternalPathRelative) + "\")"
        embedExt['src'] = str(myEmbedExternalPathRelative)
        embedExt['data-image-src'] = str(myEmbedExternalPathRelative)
        myEmbedsExternalsCounter = myEmbedsExternalsCounter + 1

    #
    # dealing with "confluence-embedded-image"
    #
    myEmbeds = soup.findAll('img',class_=re.compile("^confluence-embedded-image"))
    print(str(len(myEmbeds)) + " embedded images.")
    for embed in myEmbeds:
        origEmbedPath = embed['src']        # online link to file
        origEmbedName = origEmbedPath.rsplit('/',1)[-1].rsplit('?')[0]      # online file name
        myEmbedName = requests.utils.unquote(origEmbedName).replace(" ", "_")    # local file name
        myEmbedPath = myOutdirs[0] + myEmbedName                            # local file path
        if argSphinxCompatible == True:
            myEmbedPathRelative = '../' + myVars['attachDir'] + myEmbedName
        else:
            myEmbedPathRelative = myVars['attachDir'] + myEmbedName
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
            embed['onclick'] = "window.open(\"" + myEmbedPathRelative + "\")"
            embed['src'] = myEmbedPathRelative

    #
    # dealing with "emoticon"
    #
    myEmoticons = soup.findAll('img',class_=re.compile("emoticon"))     # atlassian-check_mark, or
    print(str(len(myEmoticons)) + " emoticons.")
    for emoticon in myEmoticons:
        requestEmoticons = requests.get(emoticon['src'], auth=(argUserName, argApiToken))
        myEmoticonTitle = emoticon['src'].rsplit('/',1)[-1]     # just filename
        if argSphinxCompatible == True:
            myEmoticonPath = '../' + myVars['emoticonsDir'] + myEmoticonTitle
        else:
            myEmoticonPath = myVars['emoticonsDir'] + myEmoticonTitle
        if myEmoticonTitle not in myEmoticonsList:
            myEmoticonsList.append(myEmoticonTitle)
            print("Getting emoticon: " + myEmoticonTitle)
            filePath = os.path.join(myOutdirs[1],myEmoticonTitle)
            open(filePath, 'wb').write(requestEmoticons.content)
        emoticon['src'] = myEmoticonPath

    myBodyExportView = getBodyExportView(argSite,argPageId,argUserName,argApiToken).json()
    pageUrl = str(myBodyExportView['_links']['base']) + str(myBodyExportView['_links']['webui'])
    if argSphinxCompatible == True:
        stylesDirRelative = str("../" + myVars['stylesDir'])
    else:
        stylesDirRelative = myVars['stylesDir']
    myHeader = """<html>
<head>
<title>""" + argTitle + """</title>
<link rel="stylesheet" href=\"""" + stylesDirRelative + """confluence.css" type="text/css" />
<meta name="generator" content="confluenceExportHTML" />
<META http-equiv="Content-Type" content="text/html; charset=UTF-8">
<meta name="ConfluencePageLabels" content=\"""" + str(argPageLabels) + """\">
<meta name="ConfluencePageID" content=\"""" + str(argPageId) + """\">
<meta name="ConfluencePageParent" content=\"""" + str(argPageParent) + """\">
</head>
<body>
<h2>""" + argTitle + """</h2>
<p>Original URL: <a href=\"""" + pageUrl + """\"> """+argTitle+"""</a><hr>"""

    myFooter = """</body>
</html>"""
    #
    # At the end of the page, put a link to all attachments.
    #
    if argSphinxCompatible == True:
        attachDir = "../" + myVars['attachDir']
    else:
        attachDir = myVars['attachDir']
    if len(myAttachments) > 0:
        myPreFooter = "<h2>Attachments</h2><ol>"
        for attachment in myAttachments:
            myPreFooter += ("""<li><a href=\"""" + os.path.join(attachDir,attachment) + """\"> """ + attachment + """</a></li>""")
        myPreFooter +=  "</ol></br>"
    #
    # Putting HTML together
    #
    prettyHTML = soup.prettify()
    htmlFile = open(htmlFilePath, 'w')
    htmlFile.write(myHeader)
    htmlFile.write(prettyHTML)
    if len(myAttachments) > 0:
        htmlFile.write(myPreFooter)
    htmlFile.write(myFooter)
    htmlFile.close()
    print("Exported HTML file " + htmlFilePath)
    #
    # convert html to rst
    #
    rstFileName = str(argTitle) + '.rst'
    rstFilePath = os.path.join(myOutdirContent,rstFileName)
    try:
        outputRST = pypandoc.convert_file(str(htmlFilePath), 'rst', format='html',extra_args=['--standalone','--wrap=none','--list-tables'])
    except:
        print("There was an issue generating an RST file from the page.")
    else:
        ##
        ## RST Header with Page Metadata
        ##
        rstPageHeader = """.. tags:: """ + str(argPageLabels) + """

.. meta::
    :confluencePageId: """ + str(argPageId) + """
    :confluencePageLabels: """ + str(argPageLabels) + """
    :confluencePageParent: """ + str(argPageParent) + """

"""
        rstFile = open(rstFilePath, 'w')
        rstFile.write(rstPageHeader)            # assing .. tags:: to rst file for future reference
        rstFile.write(outputRST)
        rstFile.close()
        print("Exported RST file: " + rstFilePath)
