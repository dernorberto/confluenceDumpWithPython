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
    spaceId = args.space
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

if args.mode == 'single':
    pageId = args.page
    pageName = myModules.getPageName(atlassianSite,pageId,userName,apiToken)

    myBodyExportView = myModules.getBodyExportView(atlassianSite,pageId,userName,apiToken).json()
    myBodyExportViewHtml = myBodyExportView['body']['export_view']['value']
    myBodyExportViewTitle = myBodyExportView['title'].replace("/","-").replace(",","")

    pageUrl = str(myBodyExportView['_links']['base']) + str(myBodyExportView['_links']['webui'])

    myOutdirs = []
    myOutdirs = myModules.mkOutdirs(myOutdir)               # attachments, embeds, scripts
    #myAttachments = myModules.getAttachments(atlassianSite,pageId,str(myOutdirs[0]),userName,apiToken)         # dumpHtml alreay runs getAttachments
    myPageLabels = myModules.getPageLabels(atlassianSite,pageId,userName,apiToken)

    myModules.dumpHtml(atlassianSite,myBodyExportViewHtml,myBodyExportViewTitle,pageId,myOutdir,myPageLabels,userName,apiToken)
else:
    print("No script mode defined in the command line")
