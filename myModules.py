import shutil
import requests
import os.path
import json
import time
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException
from bs4 import BeautifulSoup as bs
import sys
import pypandoc
from PIL import Image
import re

"""
Arguments needed to run these functions centrally:
* outdirs: outdir, attach_dir, emoticonDir, styles_dir
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
script_dir = os.path.dirname(os.path.abspath(__file__))
attach_dir = "_images/"
emoticons_dir = "_images/"
styles_dir = "_static/"


def request_get_with_retry(url, retries=5, backoff_factor=1.5, timeout=30, **kwargs):
    """Execute GET request with exponential backoff for transient network errors."""
    last_error = None
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
        except RequestException as error:
            last_error = error
            if attempt == retries - 1:
                break
            sleep_time = backoff_factor ** attempt
            print(
                f"WARNING: request failed ({error}). Retrying in {sleep_time:.1f}s "
                f"[{attempt + 1}/{retries}] for URL: {url}"
            )
            time.sleep(sleep_time)
    raise last_error

def set_variables():
    """Set variables for export folders"""
    dict_vars = {}
    dict_vars['attach_dir'] = "_images/"
    dict_vars['emoticons_dir'] = "_images/"
    dict_vars['styles_dir'] = "_static/"
    attach_dir = "_images/"
    emoticons_dir = "_images/"
    styles_dir = "_static/"
    return(dict_vars)
#
# Create the output folders, set to match Sphynx structure
#
def set_dirs(arg_outdir="output"):        # setting default to output
    """Set output folders paths for attachments, emoticons and styles"""
    my_vars = set_variables()
    outdir_attach = os.path.join(arg_outdir,my_vars['attach_dir'])
    outdir_emoticons = os.path.join(arg_outdir,my_vars['emoticons_dir'])
    outdir_styles = os.path.join(arg_outdir,my_vars['styles_dir'])
    return[outdir_attach, outdir_emoticons, outdir_styles]      # returns a list

def mk_outdirs(arg_outdir="output"):       # setting default to output
    """Create the output folders"""
    my_vars = set_variables()
    outdir_list = set_dirs(arg_outdir)
    outdir_attach = outdir_list[0]
    outdir_emoticons = outdir_list[1]
    outdir_styles = outdir_list[2]

    if not os.path.exists(arg_outdir):
        os.mkdir(arg_outdir)

    if not os.path.exists(outdir_attach):
        os.mkdir(outdir_attach)

    if not os.path.exists(outdir_emoticons):
        os.mkdir(outdir_emoticons)

    if not os.path.exists(outdir_styles):
        os.mkdir(outdir_styles)

    if not os.path.exists(outdir_styles + '/confluence.css'):
        shutil.copy(f"{script_dir}/styles/confluence.css", f"{outdir_styles}confluence.css")
    return(outdir_list)

def get_space_title(arg_site,arg_space_id,arg_username,arg_api_token):
    """Get Title of a space

    Args:
        arg_site: The site name
        arg_space_id: ID of the space
        arg_username: Username for auth
        arg_api_token: API token for auth

    Returns:
        response (string): The title of the space
    """
    server_url = (f"https://{arg_site}.atlassian.net/wiki/api/v2/spaces/{arg_space_id}")

    response = request_get_with_retry(server_url, auth=(arg_username, arg_api_token), timeout=30).json()['name']
    return(response)

def get_spaces_all(arg_site,arg_username,arg_api_token):
    server_url = f"https://{arg_site}.atlassian.net/wiki/api/v2/spaces/?limit=250"
    response = request_get_with_retry(server_url, auth=(arg_username,arg_api_token), timeout=30)
    response.raise_for_status()  # raises exception when not a 2xx response
    space_list = response.json()['results']
    while 'next' in response.json()['_links'].keys():
        cursorserver_url = f"{server_url}&cursor{response.json()['_links']['next'].split('cursor')[1]}"
        response = request_get_with_retry(cursorserver_url, auth=(arg_username,arg_api_token), timeout=30)
        space_list = space_list + response.json()['results']
    return(space_list)

def get_pages_from_space(arg_site,arg_space_id,arg_username,arg_api_token):
    page_list = []
    server_url = f"https://{arg_site}.atlassian.net/wiki/api/v2/spaces/{arg_space_id}/pages?status=current&limit=250"
    response = request_get_with_retry(server_url, auth=(arg_username,arg_api_token), timeout=30)
    page_list = response.json()['results']
    while 'next' in response.json()['_links'].keys():
        cursorserver_url = f"{server_url}&cursor{response.json()['_links']['next'].split('cursor')[1]}"
        response = request_get_with_retry(cursorserver_url, auth=(arg_username,arg_api_token), timeout=30)
        page_list = page_list + response.json()['results']
    return(page_list)

def get_body_export_view(arg_site,arg_page_id,arg_username,arg_api_token):
    server_url = f"https://{arg_site}.atlassian.net/wiki/rest/api/content/{arg_page_id}?expand=body.export_view"
    response = request_get_with_retry(server_url, auth=(arg_username, arg_api_token), timeout=30)
    return(response)

def get_page_name(arg_site,arg_page_id,arg_username,arg_api_token):
    server_url = f"https://{arg_site}.atlassian.net/wiki/rest/api/content/{arg_page_id}"
    r_pagetree = request_get_with_retry(server_url, auth=(arg_username, arg_api_token), timeout=30)
    return(r_pagetree.json()['id'] + "_" + r_pagetree.json()['title'])

def get_page_parent(arg_site,arg_page_id,arg_username,arg_api_token):
    server_url = f"https://{arg_site}.atlassian.net/wiki/api/v2/pages/{arg_page_id}"
    response = request_get_with_retry(server_url, auth=(arg_username, arg_api_token), timeout=30)
    return(response.json()['parentId'])

def remove_illegal_characters(input):
    return re.sub(r'[^\w_\.\- ]+', '_', input)

def windows_safe_filename(name, max_len=180):
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'[\x00-\x1f]', '_', name)
    name = re.sub(r'[\s\.]+$', '', name)
    name = name.strip()
    if len(name) > max_len:
        name = name[:max_len]
    if not name:
        name = "untitled"
    return name

def get_attachments(arg_site,arg_page_id,arg_outdir_attach,arg_username,arg_api_token):
    my_attachments_list = []
    server_url = f"https://{arg_site}.atlassian.net/wiki/rest/api/content/{arg_page_id}?expand=children.attachment"
    response = request_get_with_retry(server_url, auth=(arg_username, arg_api_token), timeout=30)
    my_attachments = response.json()['children']['attachment']['results']
    for attachment in my_attachments:
        attachment_title = remove_illegal_characters(requests.utils.unquote(attachment['title']).replace(" ","_").replace(":","-"))         # I want attachments without spaces
        attachment_file_path = os.path.join(arg_outdir_attach,attachment_title)
        if not os.path.exists(attachment_file_path):
            print(f"Downloading: {attachment_title}")
            try:
                attachment_url = f"https://{arg_site}.atlassian.net/wiki{attachment['_links']['download']}"
                request_attachment = request_get_with_retry(attachment_url, auth=(arg_username, arg_api_token), allow_redirects=True, timeout=30)
                open(attachment_file_path, 'wb').write(request_attachment.content)
            except:
                print(f"WARNING: Skipping attachment file {attachment_file_path} due to issues. url: {attachment_url}")
        my_attachments_list.append(attachment_title)
    return(my_attachments_list)

# get page labels
def get_page_labels(arg_site,arg_page_id,arg_username,arg_api_token):
    html_labels = []
    server_url = f"https://{arg_site}.atlassian.net/wiki/api/v2/pages/{arg_page_id}/labels"
    response = request_get_with_retry(server_url, auth=(arg_username,arg_api_token), timeout=30).json()
    for l in response['results']:
        html_labels.append(l['name'])
        print(f"Label: {l['name']}")
    html_labels = ", ".join(html_labels)
    print(f"Page labels: {html_labels}")
    return(html_labels)

def get_page_properties_children(arg_site,arg_html,arg_outdir,arg_username,arg_api_token):
    my_page_properties_children = []
    my_page_properties_children_dict = {}
    soup = bs(arg_html, "html.parser")
    my_page_properties_items = soup.findAll('td',class_="title")
    my_page_properties_items_counter = 0
    for n in my_page_properties_items:
        my_page_id = str(n['data-content-id'])
        my_page_properties_children.append(str(n['data-content-id']))
        my_page_properties_items_counter = my_page_properties_items_counter + 1
        my_page_name = get_page_name(arg_site,int(my_page_id),arg_username,arg_api_token).rsplit('_',1)[1].replace(":","-").replace(" ","_").replace("%20","_")          # replace offending characters from file name
        my_page_properties_children_dict.update({ my_page_id:{}})
        my_page_properties_children_dict[my_page_id].update({"ID": my_page_id})
        my_page_properties_children_dict[my_page_id].update({"Name": my_page_name})
    print( f"{my_page_properties_items_counter} Page Properties Children Pages")
    return[my_page_properties_children,my_page_properties_children_dict]

def get_editor_version(arg_site,arg_page_id,arg_username,arg_api_token):
    server_url = f"https://{arg_site}.atlassian.net/wiki/rest/api/content/{arg_page_id}?expand=metadata.properties.editor"
    response = request_get_with_retry(server_url, auth=(arg_username, arg_api_token), timeout=30)
    return(response)

def dump_html(
    arg_site,
    arg_html,
    arg_title,
    arg_page_id,
    arg_outdir_base,
    arg_outdir_content,
    arg_page_labels,
    arg_page_parent,
    arg_username,
    arg_api_token,
    arg_sphinx_compatible=True,
    arg_sphinx_tags=False,
    arg_type="",
    arg_html_output=False,
    arg_rst_output=True,
    arg_show_labels=False
    ):
    """Create HTML and RST files

    Args:
        arg_site: Name of the Confluence Site
        arg_html: HTML Content to use for page
        arg_title: Title of the page
        arg_page_id: Page ID
        arg_outdir_base: Base output folder
        arg_outdir_content: Output folder for Content
        arg_page_labels: Labels of the page
        arg_page_parent: Parent of the page
        arg_username: Username for authentication
        arg_api_token: API Token for authentication
        arg_sphinx_compatible: Place _static and _images folder at root of output folder
        arg_sphinx_tags: Add tags to output RST
        arg_type: For Page Properties, the type of page: "report", "child" or "common" if it's not for Page Properties

    Returns:
        HTML, RST and all attachments, embeds and emoticons
    """
    my_vars = set_variables()
    my_emoticons_list = []
    my_outdir_content = arg_outdir_content
    #my_outdir_content = os.path.join(arg_outdir_base,str(arg_page_id) + "-" + str(arg_title))      # this is for html and rst files
    if not os.path.exists(my_outdir_content):
        os.mkdir(my_outdir_content)
    #myOutdir = os.path.join(arg_outdir,str(arg_page_id) + "-" + str(arg_title))
    my_outdirs = mk_outdirs(arg_outdir_base)        # this is for everything for _images and _static
    my_vars = set_variables()     # create a dict with the 3 folder paths: attach, emoticons, styles

    soup = bs(arg_html, "html.parser")

    #
    # removing elements we don't need like
    # * <div class="expand-control"...
    # * <pre class="syntaxhighlighter-pre"...
    #
    my_undesirables = soup.findAll('div',class_="expand-control")
    for div in my_undesirables:
        div.decompose()

    # Find all pre tags
    pre_tags = soup.find_all('pre')
    # Remove the class 'syntaxhighlighter-pre' from each pre tag
    for pre in pre_tags:
        pre['class'] = [c for c in pre.get('class', []) if c != 'syntaxhighlighter-pre']

    # continuing
    safe_title = windows_safe_filename(arg_title.replace(" ", "_").replace(":", "-").replace("/", "-"))
    html_file_name = f"{safe_title}.html"
    html_file_path = os.path.join(my_outdir_content,html_file_name)
    my_attachments = get_attachments(arg_site,arg_page_id,str(my_outdirs[0]),arg_username,arg_api_token)
    #
    # used for pageprops mode
    #
    #if (arg_type == "child"):
        #my_report_children_dict = get_page_properties_children(arg_site,arg_html,arg_outdir,arg_username,arg_api_token)[1]              # get list of all page properties children
        #my_report_children_dict[arg_page_id].update({"Filename": arg_html_file_name})
    if (arg_type == "report"):
        my_report_children_dict= get_page_properties_children(arg_site,arg_html,my_outdir_content,arg_username,arg_api_token)[1]      # dict
        my_page_properties_items = soup.findAll('td',class_="title")       # list
        for item in my_page_properties_items:
            id = item['data-content-id']
            item.a['href'] = (f"{my_report_children_dict[id]['Name']}.html")
    #
    # dealing with "confluence-embedded-image confluence-external-resource"
    #
    my_embeds_externals = soup.findAll('img',class_="confluence-embedded-image confluence-external-resource")
    my_embeds_externals_counter = 0
    for embed_ext in my_embeds_externals:
        orig_embed_external_path = embed_ext['src']     # online link to file
        orig_embed_external_name = orig_embed_external_path.rsplit('/',1)[-1].rsplit('?')[0]      # just the file name
        my_embed_external_name = remove_illegal_characters((f"{arg_page_id}-{my_embeds_externals_counter}-{requests.utils.unquote(orig_embed_external_name)}").replace(" ", "_").replace(":","-"))    # local filename
        my_embed_external_path = os.path.join(my_outdirs[0],my_embed_external_name)        # local filename and path
        if arg_sphinx_compatible == True:
            my_embed_external_path_relative = os.path.join(str('../' + my_vars['attach_dir']),my_embed_external_name)
        else:
            my_embed_external_path_relative = os.path.join(my_vars['attach_dir'],my_embed_external_name)
        try:
            if not os.path.exists(my_embed_external_path):
                to_download = request_get_with_retry(orig_embed_external_path, allow_redirects=True, timeout=30)
                open(my_embed_external_path,'wb').write(to_download.content)
            img = Image.open(my_embed_external_path)
        except:
            print(f"WARNING: Skipping embed file {my_embed_external_path} due to issues. url: {orig_embed_external_path}")
        else:
            if img is not None:
                if img.width < 600:
                    embed_ext['width'] = img.width
                else:
                    embed_ext['width'] = 600
                img.close
                embed_ext['height'] = "auto"
                embed_ext['onclick'] = f"window.open(\"{my_embed_external_path_relative}\")"
                embed_ext['src'] = str(my_embed_external_path_relative)
                embed_ext['data-image-src'] = str(my_embed_external_path_relative)
                my_embeds_externals_counter = my_embeds_externals_counter + 1

    #
    # dealing with "confluence-embedded-image"
    #
    my_embeds = soup.findAll('img',class_=re.compile("^confluence-embedded-image"))
    print(str(len(my_embeds)) + " embedded images.")
    for embed in my_embeds:
        orig_embed_path = embed['src']        # online link to file
        orig_embed_name = orig_embed_path.rsplit('/',1)[-1].rsplit('?')[0]      # online file name
        my_embed_name = remove_illegal_characters(requests.utils.unquote(orig_embed_name).replace(" ", "_"))    # local file name
        my_embed_path = my_outdirs[0] + my_embed_name                            # local file path
        if arg_sphinx_compatible == True:
            my_embed_path_relative = f"../{my_vars['attach_dir']}{my_embed_name}"
        else:
            my_embed_path_relative = f"{my_vars['attach_dir']}{my_embed_name}"
        img = None
        try:
            if not os.path.exists(my_embed_path):
                to_download = request_get_with_retry(orig_embed_path, allow_redirects=True, auth=(arg_username, arg_api_token), timeout=30)
                open(my_embed_path,'wb').write(to_download.content)
            img = Image.open(my_embed_path)
        except:
            print(f"WARNING: Skipping embed file {my_embed_path} due to issues. url: {orig_embed_path}")
        else:
            if img is not None:
                if img.width < 600:
                    embed['width'] = img.width
                else:
                    embed['width'] = 600
                img.close
                embed['height'] = "auto"
                embed['onclick'] = f"window.open(\"{my_embed_path_relative}\")"
            embed['src'] = my_embed_path_relative
    #
    # dealing with "emoticon" and expands' "grey_arrow_down.png"
    #
    my_emoticons = soup.findAll('img',class_=re.compile("emoticon|expand-control-image"))
    print(f"{len(my_emoticons)} emoticons.")
    for emoticon in my_emoticons:
        my_emoticon_title = emoticon['src'].rsplit('/',1)[-1]     # just filename
        if arg_sphinx_compatible == True:
            my_emoticon_path = f"../{my_vars['emoticons_dir']}{my_emoticon_title}"
        else:
            my_emoticon_path = f"{my_vars['emoticons_dir']}{my_emoticon_title}"
        if my_emoticon_title not in my_emoticons_list:
            my_emoticons_list.append(my_emoticon_title)
            print(f"Getting emoticon: {my_emoticon_title}")
            file_path = os.path.join(my_outdirs[1],remove_illegal_characters(my_emoticon_title))
            if not os.path.exists(file_path):
                emoticon_src = emoticon['src']
                try:
                    request_emoticons = request_get_with_retry(emoticon_src, auth=(arg_username, arg_api_token), timeout=30)
                    open(file_path, 'wb').write(request_emoticons.content)
                except:
                    print(f"WARNING: Skipping emoticon file {file_path} due to issues. url: {emoticon_src}")
        emoticon['src'] = my_emoticon_path

    my_body_export_view = get_body_export_view(arg_site,arg_page_id,arg_username,arg_api_token).json()
    page_url = f"{my_body_export_view['_links']['base']}{my_body_export_view['_links']['webui']}"
    if arg_sphinx_compatible == True:
        styles_dir_relative = f"../{my_vars['styles_dir']}"
    else:
        styles_dir_relative = my_vars['styles_dir']

    my_header = (f"<html>\n"
                f"<head>\n"
                f"<title>{arg_title}</title>\n"
                f"<link rel=\"stylesheet\" href=\"{styles_dir_relative}confluence.css\" type=\"text/css\" />\n"
                f"<meta name=\"generator\" content=\"confluenceExportHTML\" />\n"
                f"<META http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\">\n"
                f"<meta name=\"ConfluencePageLabels\" content=\"{arg_page_labels}\">\n"
                f"<meta name=\"ConfluencePageID\" content=\"{arg_page_id}\">\n"
                f"<meta name=\"ConfluencePageParent\" content=\"{arg_page_parent}\">\n"
                f"</head>\n"
                f"<body>\n"
                f"<h2>{arg_title}</h2>\n"
                f"<p>Original URL: <a href=\"{page_url}\"> {arg_title}</a><hr>\n"
    )


    myFooter = (f"</body>\n"
                f"</html>"
    )
    #
    # At the end of the page, put a link to all attachments.
    #
    if arg_sphinx_compatible == True:
        attach_dir = "../" + my_vars['attach_dir']
    else:
        attach_dir = my_vars['attach_dir']
    if len(my_attachments) > 0:
        my_pre_footer = "<h2>Attachments</h2><ol>"
        for attachment in my_attachments:
            my_pre_footer += (f"<li><a href=\"{os.path.join(attach_dir,attachment)}\">{attachment}</a></li>")
        my_pre_footer += "</ol></br>"

    #
    # Putting HTML together
    #
    pretty_html = soup.prettify()
    html_file = open(html_file_path, 'w', encoding='utf-8')
    html_file.write(my_header)
    html_file.write(pretty_html)
    if len(my_attachments) > 0:
        html_file.write(my_pre_footer)
    html_file.write(myFooter)
    html_file.close()
    if arg_html_output == True:
        print(f"Exported HTML file {html_file_path}")
    #
    # convert html to rst
    #
    if not arg_rst_output:
        return

    rst_file_name = html_file_name.replace(".html", ".rst")
    rst_file_path = os.path.join(my_outdir_content,rst_file_name)
    try:
        output_rst = pypandoc.convert_file(str(html_file_path), 'rst', format='html',extra_args=['--standalone','--wrap=none','--list-tables'])
    except:
        print("There was an issue generating an RST file from the page.")
    else:
        ##
        ## RST Header with Page Metadata
        ##
        if (arg_sphinx_compatible == True):
            rst_page_header = (f":conf_pagetype: {arg_type}\n"
                f":conf_pageid: {arg_page_id}\n"
                f":conf_parent: {arg_page_parent}\n"
                f":conf_labels: {arg_page_labels}\n"
                f":doc_title: {arg_title}\n"
                f"\n"
            )
        else:
            rst_page_header = (f".. meta::\n"
                f"    :confluencePageId: {arg_page_id} \n"
                f"    :confluencePageLabels: {arg_page_labels} \n"
                f"    :confluencePageParent: {arg_page_parent} \n"
                f"\n"
            )
        ## Footer with list of page labels
        if arg_show_labels == True:
            footer_rst = (f"...."
                f"\n"
                f"\n**Page labels**: {arg_page_labels} \n")
        else:
            footer_rst = ""

        rst_file = open(rst_file_path, 'w', encoding='utf-8')
        rst_file.write(rst_page_header)
        rst_file.write(output_rst)
        rst_file.write(footer_rst)
        rst_file.close()
        print(f"Exported RST file: {rst_file_path}")
        if arg_html_output == False:
            os.remove(html_file_path)
