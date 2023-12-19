import os
import re
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--folder', type=str, default='output',
                    help='Folder to handle', required=True)
parser.add_argument('--test', action='store_true', default=False,
                    help='Create copies of the original files', required=False)
args = parser.parse_args()

target_folder = args.folder

file_type = '.rst'
# dict with .rst files pageids and filenames
rst_pageids = {}
# filename for export file
rst_pageids_filename = "z_rst_pageids.txt"

## uncomment line to test with a single file
#my_single_rst_file = "PCI_DSS_Inventory.rst"

#
# ROUND 1
# get from all local RST files: page ID and filename
#
my_rst_files = []
for filename in os.listdir(target_folder):
    if filename.endswith(file_type) and not filename.startswith("zout"):
        my_rst_files.append(filename)

for filename in my_rst_files:
    path_and_name = os.path.join(target_folder, filename)
    with open(path_and_name, encoding='utf-8') as file:
        while line := file.readline():
            if ":confluencePageId:" in line:
                my_rsts_pageid = line.split(":confluencePageId: ")[1][:-1]
                rst_pageids.update({str(my_rsts_pageid)[:-1] : str(filename)})
                print(f"{str(my_rsts_pageid)[:-1]} : {str(filename)}")
                break

    # write the file out
    with open(rst_pageids_filename, 'w', encoding='utf-8') as file:
        for k,v in rst_pageids.items():
            file.write(f"{k}:{v}\n")

#
# ROUND 2
# go through all files again and replace confluence URLs with the local filenames
#

conf_pageids = []
conf_pageids_filename = "z_conf_pageids.txt"

if 'my_single_rst_file' in locals():
    my_rst_files = []
    my_rst_files.append(my_single_rst_file)


for filename in my_rst_files:
    all_sfile_lines = []
    all_tfile_lines = []
    # input file
    path_and_name = os.path.join(target_folder, filename)
    # output file
    if args.test is True:
        out_filename = f"zout_{filename}"
    else:
        out_filename = filename
    out_path_and_name = os.path.join(target_folder, out_filename)
    # open input file
    with open(path_and_name, 'r', encoding='utf-8') as sfile:     # sfile = source file
        all_sfile_lines = sfile.readlines()
    with open(out_path_and_name, 'w', encoding='utf-8') as tfile:     # tfile = target file
        for n,line in enumerate(all_sfile_lines):
            if ("<https://optile.atlassian.net/wiki/spaces/" in line or "</wiki/spaces/" in line) and "/pages/" in line and not line.startswith("Original URL:"):
                for find_match in re.findall(r'<?(https:\/\/\w+.*spaces\/\w+\/pages\/(\d+)?.*)>?|<(\/wiki\/spaces\/\w+\/pages\/(\d+)\/?.*)>',line):      # if there are >1 links in a line
                    # getting the pageID out of the confluence URL
                    if find_match[1]:       # for 0 and 1 of findall
                        link_pageid = find_match[1]
                        link_confluence = find_match[0]
                    if find_match[3]:       # for 2 and 3 of findall
                        link_pageid = find_match[3]
                        link_confluence = find_match[2]
                    if link_pageid in rst_pageids:
                        # using that pageID to match with the one in the "rst_pageids" dict
                        link_html_file = str(rst_pageids[link_pageid]).replace(".rst",".html")
                        line = line.replace(link_confluence,link_html_file)
                        #print(f"In line {n}, replaced {link_confluence} with {link_html_file}.")
                        #print(f"{find_match} will be replaced by {i}")
                    if link_pageid not in conf_pageids:
                        conf_pageids.append(link_pageid)
                all_tfile_lines.append(line)
            else:
                all_tfile_lines.append(line)
        tfile.writelines(all_tfile_lines)
        print(f"Created {out_filename}")
#    with open(path_and_name, 'w') as file:
#        file.writelines(all_file_lines)
    # write the file out
    with open(conf_pageids_filename, 'w', encoding='utf-8') as file:
        for n in conf_pageids:
            file.write(str(n) + '\n')

print(f"Created the file \"{conf_pageids_filename}\" with {len(conf_pageids)} entries")
# These are the Confluence links that I need to convert

# Now I need to collect every .rst file name, as each includes
