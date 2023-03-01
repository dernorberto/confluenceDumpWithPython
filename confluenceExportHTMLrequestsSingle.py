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

## Diagrams that were NOT downloaded
"""
attachments/page-0.png
attachments/page-0.png
attachments/page-2.png
attachments/page-1.png
"""

"""
URL: https://atlassian-lucidchart-com.s3.amazonaws.com/Confluence%3A0569361781/73399e28-8d60-47d5-b428-95a3b7220ca3/page-0.png?X-Amz-Security-Token=IQoJb3JpZ2luX2VjEOP%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJHMEUCIHWxg%2FSxjidv7uyfGflOUTjOguLBaRvh0BwrxbOsDPhQAiEAokI35U0ikYqTmm%2B4Q2nYJnY%2Ffe08RJkD52WeKlHj294qugUIjP%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FARAAGgw5MzU2MDY5MjYxODIiDOKYNTKWpheTZgaUMiqOBbs5huZ29RbttM5BZx1uaM337Yze5Y3kmpbKhiq7Ppd%2F32Hy39DG68CNNrunhasMGL3kJVJNjRc4%2FBEruQFuHwPjh5kBvaVar%2B%2FBf3UNqznIyvRMx9JftqtvCan2UJfvT206%2BBAFQmksUqfGT%2BjrEoV3CoOdc3MoZ4cB1aqKcbuKasnx1TklAh4jxTq%2FijvPckR6TSSKEDAA%2BB3cnAz%2FrwEYaj1oLcULgcfF0OMXPKs9k72VAyWGi96R7aXBT2t5jUMWcmvbNwpfPYFNB6jLfzgKhHHk4UzLUTLVsZrUzEfJQFtNm6MvVMjqaCLgL%2BDc5Hd%2FDKgYo0NoxcGVA8HNhlOw3KCLur9Bk5mgvOLLIXGL%2BQiMRHdTq7HRnE7rmaytMVulZvvbYhsdQh9uYwHCHo25B7PBnQO%2FGvk%2F8gV%2FL6oR%2Bvp08GpXn4%2BuAzhJzSBAq0MyS12rxF4QZkLgG1QLfnlZ4GusDK9ig%2Ba90dXm%2BoOWCLFnbSphst0rmSJxil3CXKH9mltNq295tkIy2O%2BlhdC3d2RqOpYSW25DdgJ5AJKn5kRavzZ7mW5BZ0pCe1WYKrnXEcEFwKoO1C9AoHnvZR26OQl8UDxVstayKSm3YWLi8kY2gR2Q86hYUlazImtS%2B%2FLqAwxkeMeeJkj5gcvCxQwzD5aCp55bS7KLZEtOFgysMREb7yJoTyl3voiYtlikbvqJyxw9YU4B6S37YLjhJxp7hUVhtjGPGl7Bl5%2B5gnDdm7sciqjBC4tPeQvMiHzK5YK8rvKrRcYkGadCwfGEmCFCzRhDzYCiaIaDsGAtyLd5m%2F1TU39Dm1bHJpGbi8l0X5Es5QkeeenbBavUbWQlsbktTfuwZ5fE2d1RMYbh7DCg2vyfBjqxAU5sG6S7TQpHmetL2lhyqbP9%2B6ODxfoHxOGTzFbaLDKmy8iDJRgWIiY1iJJ0iy5Xvgd%2FWMwrqm4OIM%2FV3mFKLmkRJhvtb95F57NYPwyjX2cCGsouJ5OUfkqkrGpZiX3oGOvaEDjGhYbvkndCjH8emAMTBYmkBACWkt6AqW55xqogZTaNBA0NaZTdrIpnoUvjeyZF8UwawBZGtCmkLZk3eO6jVKusH%2BVg7sAV1Cb3L76heg%3D%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20230301T111801Z&X-Amz-SignedHeaders=host&X-Amz-Expires=299&X-Amz-Credential=ASIA5TVUEXNTE2LPUI7B%2F20230301%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=e359e2681645d1b2e715c5118cbf103e9e25b9a89bd38cce6e26624d63f96271

<div style="display: inline-block;max-width: 100.0%;width: 1702.0px;height: auto;">
  <span class="confluence-embedded-file-wrapper">
   <img class="confluence-embedded-image confluence-external-resource" data-image-src="https://atlassian-lucidchart-com.s3.amazonaws.com/Confluence%3A0569361781/73399e28-8d60-47d5-b428-95a3b7220ca3/page-0.png?X-Amz-Security-Token=IQoJb3JpZ2luX2VjEOP%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJHMEUCIHWxg%2FSxjidv7uyfGflOUTjOguLBaRvh0BwrxbOsDPhQAiEAokI35U0ikYqTmm%2B4Q2nYJnY%2Ffe08RJkD52WeKlHj294qugUIjP%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FARAAGgw5MzU2MDY5MjYxODIiDOKYNTKWpheTZgaUMiqOBbs5huZ29RbttM5BZx1uaM337Yze5Y3kmpbKhiq7Ppd%2F32Hy39DG68CNNrunhasMGL3kJVJNjRc4%2FBEruQFuHwPjh5kBvaVar%2B%2FBf3UNqznIyvRMx9JftqtvCan2UJfvT206%2BBAFQmksUqfGT%2BjrEoV3CoOdc3MoZ4cB1aqKcbuKasnx1TklAh4jxTq%2FijvPckR6TSSKEDAA%2BB3cnAz%2FrwEYaj1oLcULgcfF0OMXPKs9k72VAyWGi96R7aXBT2t5jUMWcmvbNwpfPYFNB6jLfzgKhHHk4UzLUTLVsZrUzEfJQFtNm6MvVMjqaCLgL%2BDc5Hd%2FDKgYo0NoxcGVA8HNhlOw3KCLur9Bk5mgvOLLIXGL%2BQiMRHdTq7HRnE7rmaytMVulZvvbYhsdQh9uYwHCHo25B7PBnQO%2FGvk%2F8gV%2FL6oR%2Bvp08GpXn4%2BuAzhJzSBAq0MyS12rxF4QZkLgG1QLfnlZ4GusDK9ig%2Ba90dXm%2BoOWCLFnbSphst0rmSJxil3CXKH9mltNq295tkIy2O%2BlhdC3d2RqOpYSW25DdgJ5AJKn5kRavzZ7mW5BZ0pCe1WYKrnXEcEFwKoO1C9AoHnvZR26OQl8UDxVstayKSm3YWLi8kY2gR2Q86hYUlazImtS%2B%2FLqAwxkeMeeJkj5gcvCxQwzD5aCp55bS7KLZEtOFgysMREb7yJoTyl3voiYtlikbvqJyxw9YU4B6S37YLjhJxp7hUVhtjGPGl7Bl5%2B5gnDdm7sciqjBC4tPeQvMiHzK5YK8rvKrRcYkGadCwfGEmCFCzRhDzYCiaIaDsGAtyLd5m%2F1TU39Dm1bHJpGbi8l0X5Es5QkeeenbBavUbWQlsbktTfuwZ5fE2d1RMYbh7DCg2vyfBjqxAU5sG6S7TQpHmetL2lhyqbP9%2B6ODxfoHxOGTzFbaLDKmy8iDJRgWIiY1iJJ0iy5Xvgd%2FWMwrqm4OIM%2FV3mFKLmkRJhvtb95F57NYPwyjX2cCGsouJ5OUfkqkrGpZiX3oGOvaEDjGhYbvkndCjH8emAMTBYmkBACWkt6AqW55xqogZTaNBA0NaZTdrIpnoUvjeyZF8UwawBZGtCmkLZk3eO6jVKusH%2BVg7sAV1Cb3L76heg%3D%3D&amp;X-Amz-Algorithm=AWS4-HMAC-SHA256&amp;X-Amz-Date=20230301T111801Z&amp;X-Amz-SignedHeaders=host&amp;X-Amz-Expires=299&amp;X-Amz-Credential=ASIA5TVUEXNTE2LPUI7B%2F20230301%2Fus-east-1%2Fs3%2Faws4_request&amp;X-Amz-Signature=e359e2681645d1b2e715c5118cbf103e9e25b9a89bd38cce6e26624d63f96271" loading="lazy" src="attachments/page-0.png">
  </span>
 </div>

 SAVING JSON TO FILE

f = open("output2.json",'w')
f.write(json.dumps(response.json(),indent=4))
f.close


"""


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
