import os.path
import json
import myModules
import argparse

user_name = os.environ["atlassianUserEmail"]
api_token = os.environ["atlassianAPIToken"]

parser = argparse.ArgumentParser()
parser.add_argument('--site', '-S', type=str,
                    help='Atlassian Site', required=True)
parser.add_argument('--space', '-s', type=str,
                    help='Space Key')
parser.add_argument('--page', '-p', type=int,
                    help='Page ID')
args = parser.parse_args()
atlassian_site = args.site

if args.page:
    page_editor_version = myModules.get_editor_version(atlassian_site,args.page,user_name,api_token).json()
    try:
        page_editor_version['metadata']['properties']['editor']['value'] == "v2"
    except KeyError:
        editor_version = "v1"
    else:
        editor_version = "v2"
    print(f"Page: {args.page} using Editor: {editor_version}")
elif args.space:
    space_key = args.space
    ## get all spaces in order to find the space ID based on the key
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

    if space_key == "" or space_key is None:    # if the supplied space key can't be found
        print("Could not find Space Key in this site")
    else:
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
    # go through all pages and update short dict
    count_v1 = 0
    count_v2 = 0
    for my_page in all_pages_short:
        try:
            print(f"Checking page {my_page['pageTitle']} ({my_page['page_id']})")
            page_editor_version = myModules.get_editor_version(atlassian_site,my_page['page_id'],user_name,api_token).json()
        except KeyError:
            print(f"Key Error with {my_page}")
            break
        else:
            print(f"OK with {my_page['page_id']}")

        try:
            page_editor_version['metadata']['properties']['editor']['value'] == "v2"
        except KeyError:
            editor_version = "v1"
            my_page.update({"editor_version" : editor_version})
            count_v1 = count_v1 + 1
        else:
            editor_version = "v2"
            my_page.update({"editor_version" : editor_version})
            count_v2 = count_v2 + 1

    json_file_name = f"{space_key}.json"
    with open(json_file_name,'wt') as file:
        file.write(str(all_pages_short))
    print(f"Created the file {json_file_name}, {count_v1}/{count_v2} (v1/v2) pages")
else:
    print(f"No space or page supplied.")