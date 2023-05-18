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
parser.add_argument('--notags', action='store_true', default=False,
                    help='Do not add tags to export', required=False)
args = parser.parse_args()
atlassian_site = args.site
if args.mode == 'single':
    print("Exporting a single page (Sphinx set to " + str(args.sphinx) + ")")
    page_id = args.page
elif args.mode == 'space':
    print("Exporting a whole space (Sphinx set to " + str(args.sphinx) + ")")
    space_key = args.space
elif args.mode == 'bylabel':
    print("Exporting all pages with a common label (Sphinx set to " + str(args.sphinx) + ")")
elif args.mode == 'pageprops':
    print("Exporting a Page Properties page with all its children (Sphinx set to " + str(args.sphinx) + ")")

my_attachments = []
my_embeds = []
my_embeds_externals = []
my_emoticons = []
my_emoticons_list = []

user_name = os.environ["atlassianUserEmail"]
api_token = os.environ["atlassianAPIToken"]

sphinx_compatible = args.sphinx
sphinx_notags = args.notags
print("Sphinx set to " + str(sphinx_compatible))
atlassian_site = args.site
my_outdir_base = args.outdir
if args.mode == 'single':
    ############
    ## SINGLE ##
    ############
    page_id = args.page
    page_name = myModules.get_page_name(atlassian_site,page_id,user_name,api_token)

    my_body_export_view = myModules.get_body_export_view(atlassian_site,page_id,user_name,api_token).json()
    my_body_export_view_html = my_body_export_view['body']['export_view']['value']
    my_body_export_view_title = my_body_export_view['title'].replace("/","-").replace(",","").replace("&","And").replace(":","-")

    page_url = str(my_body_export_view['_links']['base']) + str(my_body_export_view['_links']['webui'])
    page_parent = myModules.get_page_parent(atlassian_site,page_id,user_name,api_token)

    if args.sphinx == False:
        my_outdir_base = os.path.join(my_outdir_base,str(page_id) + "-" + str(my_body_export_view_title))        # sets outdir to path under page_name
    my_outdir_content = os.path.join(my_outdir_base,str(page_id) + "-" + str(my_body_export_view_title))         # name of the folder for the page content
    #print("my_outdir_base: " + my_outdir_base)
    #print("my_outdir_content: " + my_outdir_content)
    my_outdirs = []
    my_outdirs = myModules.mk_outdirs(my_outdir_base)               # attachments, embeds, scripts
    my_page_labels = myModules.get_page_labels(atlassian_site,page_id,user_name,api_token)
    myModules.dump_html(atlassian_site,my_body_export_view_html,my_body_export_view_title,page_id,my_outdir_base, my_outdir_content,my_page_labels,page_parent,user_name,api_token,sphinx_compatible,sphinx_notags)
    print("Done!")
elif args.mode == 'space':
    ###########
    ## SPACE ##
    ###########
    all_spaces_full = myModules.get_spaces_all(atlassian_site,user_name,api_token)         # get a dump of all spaces
    all_spaces_short = []                                                             # initialize list for less detailed list of spaces
    i = 0
    for n in all_spaces_full:
        i = i +1
        all_spaces_short.append({                                                     # append the list of spaces
            'space_key' : n['key'],
            'space_id' : n['id'],
            'space_name' : n['name'],
            'homepage_id' : n['homepage_id'],
            'spaceDescription' : n['description'],
            })
        if (n['key'] == space_key) or n['key'] == str.upper(space_key) or n['key'] == str.lower(space_key):
            print("Found space: " + n['key'])
            space_id = n['id']
            space_name = n['name']
            current_parent = n['homepage_id']
    my_outdir_content = os.path.join(my_outdir_base,str(space_id) + "-" + str(space_name))
    if not os.path.exists(my_outdir_content):
        os.mkdir(my_outdir_content)
    if args.sphinx == False:
        my_outdir_base = my_outdir_content

    #print("my_outdir_base: " + my_outdir_base)
    #print("my_outdir_content: " + my_outdir_content)

    if space_key == "" or space_key == None:                                          # if the supplied space key can't be found
        print("Could not find Space Key in this site")
    else:
        space_title = myModules.get_space_title(atlassian_site,space_id,user_name,api_token)
        #
        # get list of pages from space
        #
        all_pages_full = myModules.get_pages_from_space(atlassian_site,space_id,user_name,api_token)
        all_pages_short = []
        i = 0
        for n in all_pages_full:
            i = i + 1
            all_pages_short.append({
                'page_id' : n['id'],
                'pageTitle' : n['title'],
                'parentId' : n['parentId'],
                'space_id' : n['space_id'],
                }
            )
        # put it all together
        print(str(len(all_pages_short)) + ' pages to export')
        page_counter = 0
        for p in all_pages_short:
            page_counter = page_counter + 1
            my_body_export_view = myModules.get_body_export_view(atlassian_site,p['page_id'],user_name,api_token).json()
            my_body_export_view_html = my_body_export_view['body']['export_view']['value']
            my_body_export_view_name = p['pageTitle']
            my_body_export_view_title = p['pageTitle'].replace("/","-").replace(",","").replace("&","And")
            print()
            print("Getting page #" + str(page_counter) + '/' + str(len(all_pages_short)) + ', ' + my_body_export_view_title + ', ' + str(p['page_id']))
            my_body_export_view_labels = ",".join(myModules.get_page_labels(atlassian_site,p['page_id'],user_name,api_token))
            mypage_url = str(my_body_export_view['_links']['base']) + str(my_body_export_view['_links']['webui'])
            print("dump_html arg sphinx_compatible = " + str(sphinx_compatible))
            myModules.dump_html(atlassian_site,my_body_export_view_html,my_body_export_view_title,p['page_id'],my_outdir_base,my_outdir_content,my_body_export_view_labels,p['parentId'],user_name,api_token,sphinx_compatible,sphinx_notags)
    print("Done!")
elif args.mode == 'pageprops':
    ###############
    ## PAGEPROPS ##
    ###############
    my_page_properties_children = []
    my_page_properties_children_dict = {}

    page_id = args.page
    #
    # Get Page Properties REPORT
    #
    print("Getting Page Properties Report Details")
    my_report_export_view = myModules.get_body_export_view(atlassian_site,page_id,user_name,api_token).json()
    my_report_export_view_title = my_report_export_view['title'].replace("/","-").replace(",","").replace("&","And").replace(":","-")
    my_report_export_view_html = my_report_export_view['body']['export_view']['value']
    my_report_export_viewName = myModules.get_page_name(atlassian_site,page_id,user_name,api_token)
    my_report_export_view_labels = myModules.get_page_labels(atlassian_site,page_id,user_name,api_token)
    my_report_export_page_url = str(my_report_export_view['_links']['base']) + str(my_report_export_view['_links']['webui'])
    my_report_export_page_parent = myModules.get_page_parent(atlassian_site,page_id,user_name,api_token)
    my_report_export_html_filename = str(my_report_export_view_title) + '.html'
    # my outdirs
    my_outdir_content = os.path.join(my_outdir_base,str(page_id) + "-" + str(my_report_export_view_title))
    #print("my_outdir_base: " + my_outdir_base)
    #print("my_outdir_content: " + my_outdir_content)
    if args.sphinx == False:
        my_outdir_base = my_outdir_content

    my_outdirs = []
    my_outdirs = myModules.mk_outdirs(my_outdir_base)               # attachments, embeds, scripts
    # get info abbout children
    #my_page_properties_children = myModules.get_page_properties_children(atlassian_site,my_report_export_view_html,my_outdir_content,user_name,api_token)[0]          # list
    #my_page_properties_children_dict = myModules.get_page_properties_children(atlassian_site,my_report_export_view_html,my_outdir_content,user_name,api_token)[1]      # dict
    (my_page_properties_children,my_page_properties_children_dict) = myModules.get_page_properties_children(atlassian_site,my_report_export_view_html,my_outdir_content,user_name,api_token)
    #
    # Get Page Properties CHILDREN
    #
    page_counter = 0
    for p in my_page_properties_children:
        page_counter = page_counter + 1
        #print("Handling child: " + p)
        my_child_export_view = myModules.get_body_export_view(atlassian_site,p,user_name,api_token).json()
        my_child_export_view_html = my_child_export_view['body']['export_view']['value']
        my_child_export_view_name = my_page_properties_children_dict[p]['Name']
        my_child_export_view_labels = myModules.get_page_labels(atlassian_site,p,user_name,api_token)
        my_child_export_view_title = my_child_export_view['title'].replace("/","-").replace(":","-").replace(" ","_")
        print("Getting Child page #" + str(page_counter) + '/' + str(len(my_page_properties_children)) + ', ' + my_child_export_view_title + ', ' + my_page_properties_children_dict[str(p)]['ID'])
        my_child_export_page_url = str(my_child_export_view['_links']['base']) + str(my_child_export_view['_links']['webui'])
        my_child_export_page_parent = myModules.get_page_parent(atlassian_site,p,user_name,api_token)
        html_file_name = my_page_properties_children_dict[p]['Name'].replace(":","-").replace(" ","_") + '.html'
        my_page_properties_children_dict[str(p)].update({"Filename": html_file_name})

        myModules.dump_html(atlassian_site,my_child_export_view_html,my_child_export_view_title,p,my_outdir_base,my_outdir_content,my_child_export_view_labels,my_child_export_page_parent,user_name,api_token,sphinx_compatible,sphinx_notags,"child")                  # creates html files for every child
    myModules.dump_html(atlassian_site,my_report_export_view_html,my_report_export_view_title,page_id,my_outdir_base,my_outdir_content,my_report_export_view_labels, my_report_export_page_parent, user_name, api_token ,sphinx_compatible,sphinx_notags,"report")         # finally creating the HTML for the report page
    print("Done!")
else:
    print("No script mode defined in the command line")
