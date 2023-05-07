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
                    help='Folder for export', required=False)
parser.add_argument('--sphinx', '-x', action='store_true', default=False,
                    help='Sphinx compatible folder structure', required=False)
args = parser.parse_args()
atlassianSite = args.site
if args.mode == 'single':
    print("Exporting a single page (Sphinx set to " + str(args.sphinx) + ")")
    pageId = args.page
elif args.mode == 'space':
    print("Exporting a whole space (Sphinx set to " + str(args.sphinx) + ")")
    spaceKey = args.space
elif args.mode == 'bylabel':
    print("Exporting all pages with a common label (Sphinx set to " + str(args.sphinx) + ")")
elif args.mode == 'pageprops':
    print("Exporting a Page Properties page with all its children (Sphinx set to " + str(args.sphinx) + ")")

myAttachments = []
myEmbeds = []
myEmbedsExternals = []
myEmoticons = []
myEmoticonsList = []

userName = os.environ["atlassianUserEmail"]
apiToken = os.environ["atlassianAPIToken"]

sphinxCompatible = args.sphinx
print("Sphinx set to " + str(sphinxCompatible))
atlassianSite = args.site
myOutdirBase = args.outdir
if args.mode == 'single':
    ############
    ## SINGLE ##
    ############
    pageId = args.page
    pageName = myModules.getPageName(atlassianSite,pageId,userName,apiToken)

    myBodyExportView = myModules.getBodyExportView(atlassianSite,pageId,userName,apiToken).json()
    myBodyExportViewHtml = myBodyExportView['body']['export_view']['value']
    myBodyExportViewTitle = myBodyExportView['title'].replace("/","-").replace(",","").replace("&","And").replace(":","-")

    pageUrl = str(myBodyExportView['_links']['base']) + str(myBodyExportView['_links']['webui'])
    pageParent = myModules.getPageParent(atlassianSite,pageId,userName,apiToken)

    if args.sphinx == False:
        myOutdirBase = os.path.join(myOutdirBase,str(pageId) + "-" + str(myBodyExportViewTitle))        # sets outdir to path under pagename
    myOutdirContent = os.path.join(myOutdirBase,str(pageId) + "-" + str(myBodyExportViewTitle))         # name of the folder for the page content
    #print("myOutdirBase: " + myOutdirBase)
    #print("myOutdirContent: " + myOutdirContent)
    myOutdirs = []
    myOutdirs = myModules.mkOutdirs(myOutdirBase)               # attachments, embeds, scripts
    myPageLabels = myModules.getPageLabels(atlassianSite,pageId,userName,apiToken)
    myModules.dumpHtml(atlassianSite,myBodyExportViewHtml,myBodyExportViewTitle,pageId,myOutdirBase, myOutdirContent,myPageLabels,pageParent,userName,apiToken,sphinxCompatible)
    print("Done!")
elif args.mode == 'space':
    ###########
    ## SPACE ##
    ###########
    allSpacesFull = myModules.getSpacesAll(atlassianSite,userName,apiToken)         # get a dump of all spaces
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
    myOutdirContent = os.path.join(myOutdirBase,str(spaceId) + "-" + str(spaceName))
    if not os.path.exists(myOutdirContent):
        os.mkdir(myOutdirContent)
    if args.sphinx == False:
        myOutdirBase = myOutdirContent

    #print("myOutdirBase: " + myOutdirBase)
    #print("myOutdirContent: " + myOutdirContent)

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
            myBodyExportViewLabels = ",".join(myModules.getPageLabels(atlassianSite,p['pageId'],userName,apiToken))
            myPageURL = str(myBodyExportView['_links']['base']) + str(myBodyExportView['_links']['webui'])
            print("dumpHtml arg sphinxCompatible = " + str(sphinxCompatible))
            myModules.dumpHtml(atlassianSite,myBodyExportViewHtml,myBodyExportViewTitle,p['pageId'],myOutdirBase,myOutdirContent,myBodyExportViewLabels,p['parentId'],userName,apiToken,sphinxCompatible)
    print("Done!")
elif args.mode == 'pageprops':
    ###############
    ## PAGEPROPS ##
    ###############
    myPagePropertiesChildren = []
    myPagePropertiesChildrenDict = {}

    pageId = args.page
    #
    # Get Page Properties REPORT
    #
    print("Getting Page Properties Report Details")
    myReportExportView = myModules.getBodyExportView(atlassianSite,pageId,userName,apiToken).json()
    myReportExportViewTitle = myReportExportView['title'].replace("/","-").replace(",","").replace("&","And").replace(":","-")
    myReportExportViewHtml = myReportExportView['body']['export_view']['value']
    myReportExportViewName = myModules.getPageName(atlassianSite,pageId,userName,apiToken)
    myReportExportViewLabels = myModules.getPageLabels(atlassianSite,pageId,userName,apiToken)
    myReportExportPageURL = str(myReportExportView['_links']['base']) + str(myReportExportView['_links']['webui'])
    myReportExportPageParent = myModules.getPageParent(atlassianSite,pageId,userName,apiToken)
    myReportExportHtmlFilename = str(myReportExportViewTitle) + '.html'
    # my outdirs
    myOutdirContent = os.path.join(myOutdirBase,str(pageId) + "-" + str(myReportExportViewTitle))
    #print("myOutdirBase: " + myOutdirBase)
    #print("myOutdirContent: " + myOutdirContent)
    if args.sphinx == False:
        myOutdirBase = myOutdirContent

    myOutdirs = []
    myOutdirs = myModules.mkOutdirs(myOutdirBase)               # attachments, embeds, scripts
    # get info abbout children
    #myPagePropertiesChildren = myModules.getPagePropertiesChildren(atlassianSite,myReportExportViewHtml,myOutdirContent,userName,apiToken)[0]          # list
    #myPagePropertiesChildrenDict = myModules.getPagePropertiesChildren(atlassianSite,myReportExportViewHtml,myOutdirContent,userName,apiToken)[1]      # dict
    (myPagePropertiesChildren,myPagePropertiesChildrenDict) = myModules.getPagePropertiesChildren(atlassianSite,myReportExportViewHtml,myOutdirContent,userName,apiToken)
    #
    # Get Page Properties CHILDREN
    #
    pageCounter = 0
    for p in myPagePropertiesChildren:
        pageCounter = pageCounter + 1
        #print("Handling child: " + p)
        myChildExportView = myModules.getBodyExportView(atlassianSite,p,userName,apiToken).json()
        myChildExportViewHtml = myChildExportView['body']['export_view']['value']
        myChildExportViewName = myPagePropertiesChildrenDict[p]['Name']
        myChildExportViewLabels = myModules.getPageLabels(atlassianSite,p,userName,apiToken)
        myChildExportViewTitle = myChildExportView['title'].replace("/","-").replace(":","-").replace(" ","_")
        print("Getting Child page #" + str(pageCounter) + '/' + str(len(myPagePropertiesChildren)) + ', ' + myChildExportViewTitle + ', ' + myPagePropertiesChildrenDict[str(p)]['ID'])
        myChildExportPageURL = str(myChildExportView['_links']['base']) + str(myChildExportView['_links']['webui'])
        myChildExportPageParent = myModules.getPageParent(atlassianSite,p,userName,apiToken)
        htmlFileName = myPagePropertiesChildrenDict[p]['Name'].replace(":","-").replace(" ","_") + '.html'
        myPagePropertiesChildrenDict[str(p)].update({"Filename": htmlFileName})

        myModules.dumpHtml(atlassianSite,myChildExportViewHtml,myChildExportViewTitle,p,myOutdirBase,myOutdirContent,myChildExportViewLabels,myChildExportPageParent,userName,apiToken,sphinxCompatible,"child")                  # creates html files for every child
    myModules.dumpHtml(atlassianSite,myReportExportViewHtml,myReportExportViewTitle,pageId,myOutdirBase,myOutdirContent,myReportExportViewLabels, myReportExportPageParent, userName, apiToken ,sphinxCompatible,"report")         # finally creating the HTML for the report page
    print("Done!")
else:
    print("No script mode defined in the command line")
