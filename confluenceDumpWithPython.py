import requests
import os.path
import json
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup as bs
import pypandoc
from PIL import Image
import re
import myModules
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--mode', '-m', dest='mode', choices=['single', 'space', 'bylabel', 'pageprops'],
                    help='Chose a download mode', required=True)
parser.add_argument('--site', '-S', type=str,
                    help='Atlassian Site', required=True)
parser.add_argument('--space', '-s', type=str,
                    help='Space Key')
parser.add_argument('--page', '-p', type=int,
                    help='Page ID')
parser.add_argument('--label', '-l', type=str,
                    help='Page label')
parser.add_argument('--outdir', '-o', type=str, default='output',
                    help='Folder for expoert', required=False)
args = parser.parse_args()
atlassianSite = args.site
myOutdir = args.outdir
if args.mode == 'single':
    print("Exporting a single page")
    pageId = args.page
elif args.mode == 'space':
    print("Exporting a whole space")
    spaceKey = args.space
elif args.mode == 'bylabel':
    print("Exporting all pages with a common label")
elif args.mode == 'pageprops':
    print("Exporting a Page Properties page with all its children")


#print('Site: ' + args.site +  args.mode, args.site, args.page, args.outdir)

myAttachments = []
myEmbeds = []
myEmbedsExternals = []
myEmoticons = []
myEmoticonsList = []

userName = os.environ["atlassianUserEmail"]
apiToken = os.environ["atlassianAPIToken"]

atlassianSite = args.site
myOutdir = args.outdir
print("myOutdir: " + myOutdir)
if args.mode == 'single':
    pageId = args.page
    pageName = myModules.getPageName(atlassianSite,pageId,userName,apiToken)

    myBodyExportView = myModules.getBodyExportView(atlassianSite,pageId,userName,apiToken).json()
    myBodyExportViewHtml = myBodyExportView['body']['export_view']['value']
    myBodyExportViewTitle = myBodyExportView['title'].replace("/","-").replace(",","").replace("&","And").replace(":","-")

    pageUrl = str(myBodyExportView['_links']['base']) + str(myBodyExportView['_links']['webui'])

    myOutdir = myOutdir
    myOutdir = os.path.join(myOutdir,str(pageId) + "-" + str(myBodyExportViewTitle))
    print("myOutdir: " + myOutdir)
    myOutdirs = []
    myOutdirs = myModules.mkOutdirs(myOutdir)               # attachments, embeds, scripts
    #myAttachments = myModules.getAttachments(atlassianSite,pageId,str(myOutdirs[0]),userName,apiToken)         # dumpHtml alreay runs getAttachments
    myPageLabels = myModules.getPageLabels(atlassianSite,pageId,userName,apiToken)

    myModules.dumpHtml(atlassianSite,myBodyExportViewHtml,myBodyExportViewTitle,pageId,myOutdir,myPageLabels,userName,apiToken)
elif args.mode == 'space':
    #
    # get list of spaces from site
    #
    allSpacesFull = myModules.getSpacesAll(atlassianSite,userName,apiToken)         # get a dump of all spaces
    print(str(len(allSpacesFull)))
    allSpacesShort = []                                                             # initialize list for less detailed list of spaces
    i = 0
    for n in allSpacesFull:
        i = i +1
        allSpacesShort.append({                                                     # append the list of spaces
            'spaceKey' : n['key'],
            'spaceId' : n['id'],
            'spaceName' : n['name'],
            'homepageId' : n['homepageId'],
            'spaceDescription' : n['description'],
            })
        if (n['key'] == spaceKey) or n['key'] == str.upper(spaceKey) or n['key'] == str.lower(spaceKey):
            print("Found space: " + n['key'])
            spaceId = n['id']
            spaceName = n['name']
            currentParent = n['homepageId']
    print("before: " + myOutdir)
    myOutdir = os.path.join(myOutdir,str(spaceId) + "-" + str(spaceName))           # set outdir to <outdir>/<Space ID>-<Space Name>
    print("after: " + myOutdir)
    #myOutdirs = myModules.mkOutdirs(myOutdir)                                       # attachments, embeds, scripts
    if spaceKey == "" or spaceKey == None:                                          # if the supplied space key can't be found
        print("Could not find Space Key in this site")
    else:
        spaceTitle = myModules.getSpaceTitle(atlassianSite,spaceId,userName,apiToken)
        #
        # get list of pages from space
        #
        allPagesFull = myModules.getPagesFromSpace(atlassianSite,spaceId,userName,apiToken)
        allPagesShort = []
        i = 0
        for n in allPagesFull:
            i = i + 1
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
        # put it all together
        print(str(len(allPagesShort)) + ' pages to export')
        pageCounter = 0
        for p in allPagesShort:
            pageCounter = pageCounter + 1
            myBodyExportView = myModules.getBodyExportView(atlassianSite,p['pageId'],userName,apiToken).json()
            myBodyExportViewHtml = myBodyExportView['body']['export_view']['value']
            myBodyExportViewName = p['pageTitle']
            myBodyExportViewTitle = p['pageTitle'].replace("/","-").replace(",","").replace("&","And")
            print()
            print("Getting page #" + str(pageCounter) + '/' + str(len(allPagesShort)) + ', ' + myBodyExportViewTitle + ', ' + str(p['pageId']))
            #myBodyExportViewLabels = myModules.getPageLabels(atlassianSite,p['pageId'],userName,apiToken)
            myBodyExportViewLabels = ",".join(myModules.getPageLabels(atlassianSite,p['pageId'],userName,apiToken))
            myPageURL = str(myBodyExportView['_links']['base']) + str(myBodyExportView['_links']['webui'])
            #htmlPageHeader = myModules.setHtmlHeader(myBodyExportViewTitle,myPageURL,myBodyExportViewLabels,myOutdirs[2])
            #myModules.dumpHtml(myBodyExportViewHtml,myBodyExportViewTitle,p['pageId'])
            myModules.dumpHtml(atlassianSite,myBodyExportViewHtml,myBodyExportViewTitle,p['pageId'],myOutdir,myBodyExportViewLabels,userName,apiToken)
else:
    print("No script mode defined in the command line")
