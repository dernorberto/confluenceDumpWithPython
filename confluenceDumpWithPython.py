import os.path
import json
import argparse
import myModules

"""Dump Confluence content using Python

Args:
    mode: Download mode
    site: Site to export from
    space: Space to export from
    page: Page to export
    outdir: Folder to export to (optional)
    sphinx: Sphinx compatible folder structure (optional)
    notags: Do not add tags to rst files (optional)


Returns:
    HTML and RST files inside the default or custom output folder

"""


parser = argparse.ArgumentParser()
parser.add_argument('--mode', '-m', dest='mode',
                    choices=['single', 'space', 'bylabel', 'pageprops'],
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
parser.add_argument('--tags', action='store_true', default=False,
                    help='Add labels as .. tags::', required=False)
parser.add_argument('--html', action='store_true', default=False,
                    help='Include .html file in export (default is only .rst)', required=False)
parser.add_argument('--no-rst', action='store_false', dest="rst", default=True,
                    help='Disable .rst file in export', required=False)
parser.add_argument('--showlabels', action='store_true', default=False,
                    help='Export .rst files with the page labels at the bottom', required=False)

args = parser.parse_args()
atlassian_site = args.site
if args.mode == 'single':
    print(f"Exporting a single page (Sphinx set to {args.sphinx})")
    page_id = args.page
elif args.mode == 'space':
    print(f"Exporting a whole space (Sphinx set to {args.sphinx})")
    space_key = args.space
elif args.mode == 'bylabel':
    print(f"Exporting all pages with a common label (Sphinx set to {args.sphinx})")
elif args.mode == 'pageprops':
    print(f"Exporting a Page Properties page with all its children (Sphinx set to {args.sphinx})")

my_attachments = []
my_embeds = []
my_embeds_externals = []
my_emoticons = []
my_emoticons_list = []

user_name = os.environ["atlassianUserEmail"]
api_token = os.environ["atlassianAPIToken"]

sphinx_compatible = args.sphinx
sphinx_tags = args.tags
print("Sphinx set to " + str(sphinx_compatible))
atlassian_site = args.site
my_outdir_base = args.outdir
if args.mode == 'single':
    ############
    ## SINGLE ##
    ############
    page_id = args.page
    page_name = myModules.get_page_name(atlassian_site,page_id,user_name,api_token)

    my_body_export_view = myModules.get_body_export_view(atlassian_site,page_id,
        user_name,api_token).json()
    my_body_export_view_html = my_body_export_view['body']['export_view']['value']
    my_body_export_view_title = my_body_export_view['title'].replace("/","-")\
        .replace(",","").replace("&","And").replace(":","-")

    server_url = f"https://{atlassian_site}.atlassian.net/wiki/api/v2/spaces/?limit=250"

    page_url = f"{my_body_export_view['_links']['base']}{my_body_export_view['_links']['webui']}"
    page_parent = myModules.get_page_parent(atlassian_site,page_id,user_name,api_token)

    my_outdir_base = os.path.join(my_outdir_base,f"{page_id}-{my_body_export_view_title}")        # sets outdir to path under page_name
    my_outdir_content = my_outdir_base

#    if args.sphinx is False:
#        my_outdir_base = os.path.join(my_outdir_base,f"{page_id}-{my_body_export_view_title}")        # sets outdir to path under page_name
#        my_outdir_content = my_outdir_base
#    else:
#        my_outdir_content = my_outdir_base
    my_outdirs = []
    my_outdirs = myModules.mk_outdirs(my_outdir_base)               # attachments, embeds, scripts
    my_page_labels = myModules.get_page_labels(atlassian_site,page_id,user_name,api_token)
    print(f"Base export folder is \"{my_outdir_base}\" and the Content goes to \"{my_outdir_content}\"")
    myModules.dump_html(atlassian_site,my_body_export_view_html,my_body_export_view_title,page_id,my_outdir_base, my_outdir_content,my_page_labels,page_parent,user_name,api_token,sphinx_compatible,sphinx_tags,arg_html_output=args.html,arg_rst_output=args.rst)
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
            'homepage_id' : n['homepageId'],
            'spaceDescription' : n['description'],
            })
        if (n['key'] == space_key) or n['key'] == str.upper(space_key) or n['key'] == str.lower(space_key):
            print("Found space: " + n['key'])
            space_id = n['id']
            space_name = n['name']
            current_parent = n['homepageId']
    my_outdir_content = os.path.join(my_outdir_base,f"{space_id}-{space_name}")
    if not os.path.exists(my_outdir_content):
        os.mkdir(my_outdir_content)
    if args.sphinx is False:
        my_outdir_base = my_outdir_content

    #print("my_outdir_base: " + my_outdir_base)
    #print("my_outdir_content: " + my_outdir_content)

    if space_key == "" or space_key is None:                                          # if the supplied space key can't be found
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
                'space_id' : n['spaceId'],
                }
            )
        # put it all together
        print(f"{len(all_pages_short)} pages to export")

        progress_file = os.path.join(my_outdir_content, ".space_export_progress.json")
        exported_page_ids = set()
        if os.path.exists(progress_file):
            try:
                with open(progress_file, "r", encoding="utf-8") as f:
                    progress_data = json.load(f)
                    exported_page_ids = set(progress_data.get("exported_page_ids", []))
                print(f"Loaded progress file with {len(exported_page_ids)} exported pages")
            except (json.JSONDecodeError, OSError) as error:
                print(f"WARNING: Could not read progress file {progress_file}: {error}")
        else:
            print("Progress file not found. Scanning output folder for already exported pages...")
            for page_item in all_pages_short:
                raw_title = page_item['pageTitle'].replace("/","-").replace(",","").replace("&","And").replace(" ","_")
                safe_title = myModules.windows_safe_filename(raw_title.replace(" ", "_").replace(":", "-").replace("/", "-"))
                expected_rst_path = os.path.join(my_outdir_content, f"{safe_title}.rst")
                expected_html_path = os.path.join(my_outdir_content, f"{safe_title}.html")

                if args.rst and args.html:
                    is_complete = os.path.exists(expected_rst_path) and os.path.exists(expected_html_path)
                elif args.rst:
                    is_complete = os.path.exists(expected_rst_path)
                elif args.html:
                    is_complete = os.path.exists(expected_html_path)
                else:
                    is_complete = False

                if is_complete:
                    exported_page_ids.add(str(page_item['page_id']))

            print(f"Recovered {len(exported_page_ids)} exported pages by scanning existing output files")

        pages_to_export = [p for p in all_pages_short if str(p['page_id']) not in exported_page_ids]
        print(f"{len(pages_to_export)} pages remaining to export")

        page_counter = 0
        for p in pages_to_export:
            page_counter = page_counter + 1
            my_body_export_view = myModules.get_body_export_view(atlassian_site,p['page_id'],user_name,api_token).json()
            my_body_export_view_html = my_body_export_view['body']['export_view']['value']
            my_body_export_view_name = p['pageTitle']
            my_body_export_view_title = p['pageTitle'].replace("/","-").replace(",","").replace("&","And").replace(" ","_")     # added .replace(" ","_") so that filenames have _ as a separator
            print()
            print(f"Getting page #{page_counter}/{len(pages_to_export)}, {my_body_export_view_title}, {p['page_id']}")
            my_body_export_view_labels = myModules.get_page_labels(atlassian_site,p['page_id'],user_name,api_token)
            #my_body_export_view_labels = ",".join(myModules.get_page_labels(atlassian_site,p['page_id'],user_name,api_token))
            mypage_url = f"{my_body_export_view['_links']['base']}{my_body_export_view['_links']['webui']}"
            print(f"dump_html arg sphinx_compatible = {sphinx_compatible}")
            myModules.dump_html(atlassian_site,my_body_export_view_html,my_body_export_view_title,p['page_id'],my_outdir_base,my_outdir_content,my_body_export_view_labels,p['parentId'],user_name,api_token,sphinx_compatible,sphinx_tags,arg_html_output=args.html,arg_rst_output=args.rst)

            exported_page_ids.add(str(p['page_id']))
            with open(progress_file, "w", encoding="utf-8") as f:
                json.dump({"exported_page_ids": sorted(exported_page_ids)}, f, indent=2)
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
    my_report_export_page_url = f"{my_report_export_view['_links']['base']}{my_report_export_view['_links']['webui']}"
    my_report_export_page_parent = myModules.get_page_parent(atlassian_site,page_id,user_name,api_token)
    my_report_export_html_filename = f"{my_report_export_view_title}.html"
        # str(my_report_export_view_title) + '.html'
    # my outdirs
    my_outdir_content = os.path.join(my_outdir_base,str(page_id) + "-" + str(my_report_export_view_title))
    #print("my_outdir_base: " + my_outdir_base)
    #print("my_outdir_content: " + my_outdir_content)
    if args.sphinx is False:
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
        my_child_export_view_title = my_child_export_view['title']      ##.replace("/","-").replace(":","-").replace(" ","_")
        print(f"Getting Child page #{page_counter}/{len(my_page_properties_children)}, {my_child_export_view_title}, {my_page_properties_children_dict[str(p)]['ID']}")
        #print("Getting Child page #" + str(page_counter) + '/' + str(len(my_page_properties_children)) + ', ' + my_child_export_view_title + ', ' + my_page_properties_children_dict[str(p)]['ID'])
        my_child_export_page_url = f"{my_child_export_view['_links']['base']}{my_child_export_view['_links']['webui']}"
        #my_child_export_page_url = str(my_child_export_view['_links']['base']) + str(my_child_export_view['_links']['webui'])
        my_child_export_page_parent = myModules.get_page_parent(atlassian_site,p,user_name,api_token)
        html_file_name = (f"{my_page_properties_children_dict[p]['Name']}.html").replace(":","-").replace(" ","_")
        #html_file_name = my_page_properties_children_dict[p]['Name'].replace(":","-").replace(" ","_") + '.html'
        my_page_properties_children_dict[str(p)].update({"Filename": html_file_name})

        myModules.dump_html(
                arg_site=atlassian_site,
                arg_html=my_child_export_view_html,
                arg_title=my_child_export_view_title,
                arg_page_id=p,
                arg_outdir_base=my_outdir_base,
                arg_outdir_content=my_outdir_content,
                arg_page_labels=my_child_export_view_labels,
                arg_page_parent=my_child_export_page_parent,
                arg_username=user_name,
                arg_api_token=api_token,
                arg_sphinx_compatible=sphinx_compatible,
                arg_sphinx_tags=sphinx_tags,
                arg_type="reportchild",
                arg_html_output=args.html,
                arg_rst_output=args.rst,
                arg_show_labels=args.showlabels
            )                  # creates html files for every child
    myModules.dump_html(
            arg_site=atlassian_site,
            arg_html=my_report_export_view_html,
            arg_title=my_report_export_view_title,
            arg_page_id=page_id,
            arg_outdir_base=my_outdir_base,
            arg_outdir_content=my_outdir_content,
            arg_page_labels=my_report_export_view_labels,
            arg_page_parent=my_report_export_page_parent,
            arg_username=user_name,
            arg_api_token=api_token,
            arg_sphinx_compatible=sphinx_compatible,
            arg_sphinx_tags=sphinx_tags,
            arg_type="report",
            arg_html_output=args.html,
            arg_rst_output=args.rst,
            arg_show_labels=args.showlabels
        )         # finally creating the HTML for the report page
    print("Done!")
else:
    print("No script mode defined in the command line")
