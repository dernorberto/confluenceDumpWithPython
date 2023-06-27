import os
import re
import sys


if len(sys.argv) > 1:
    try:
        target_folder = sys.argv[1]
    except IndexError:
        raise SystemExit("ERROR, Target folder is not correct")
else:
    target_folder = os.path.join(os.getcwd(),"output/TestMe")

file_type = '.rst'
# dict with .rst files pageids and filenames
rst_pageids = {}
# filename for export file
rst_pageids_filename = "z_rst_pageids.txt"

#
# ROUND 1
# get from all local RST files: page ID and filename
#
my_rst_files = []
for filename in os.listdir(target_folder):
    if filename.endswith(file_type):
        my_rst_files.append(filename)

for filename in my_rst_files:
    path_and_name = os.path.join(target_folder, filename)
    with open(path_and_name) as file:
        while line := file.readline():
            if ":confluencePageId:" in line:
                my_rsts_pageid = line.split(":confluencePageId: ")[1][:-1]
                rst_pageids.update({str(my_rsts_pageid)[:-1] : str(filename)})
                print(f"{str(my_rsts_pageid)[:-1]} : {str(filename)}")
                break
            else:
                print(f"Breaking on {filename}")

    # write the file out
    with open(rst_pageids_filename, 'w') as file:
        for k,v in rst_pageids.items():
            file.write(f"{k}:{v}\n")

#
# ROUND 2
# go through all files again and replace confluence URLs with the local filenames
#

conf_pageids = []
conf_pageids_filename = "z_conf_pageids.txt"

for filename in my_rst_files:
    # input file
    path_and_name = os.path.join(target_folder, filename)
    # output file
    out_filename = f"zout_{filename}"
    out_path_and_name = os.path.join(target_folder, out_filename)
    # open input file
    with open(path_and_name, 'r') as sfile:
        all_sfile_lines = sfile.readlines()
        with open(out_path_and_name, 'w') as tfile:
            for n,line in enumerate(all_sfile_lines):
                if "<https://optile.atlassian.net/wiki/spaces/" in line and "/pages/" in line and not line.startswith("Original URL:"):
                    for find_match in re.findall(r'<(https:\/\/\w+.*spaces\/\w+\/pages\/(\d+)\/.*)>',line): # if there are >1 links in a line
                    #for find_match in re.findall(r'<(.*?)>',line):      # if there are >1 links in a line
                        # getting the pageID out of the confluence URL
                        link_pageid = find_match[1]
                        #link_pageid = find_match.split("/pages/")[1].split("/")[0].split("#")[0]
                        if link_pageid in rst_pageids:
                            # using that pageID to match with the one in the "rst_pageids" dict
                            link_html_file = str(rst_pageids[link_pageid]).replace(".rst",".html")
                            # This is where I am stuck
                            # I need to replace the text between < > with the local target file
                            line = line.replace((r'<(https:\/\/\w+.*spaces\/\w+\/pages\/(\d+)\/.*)>'),link_html_file)
                            ##i = re.sub(r'<(.*?)>',link_html_file,line)
                            print("Replaced " + str(find_match[0]) + " with " + str(link_html_file))
                            #print(f"{find_match} will be replaced by {i}")
                        if link_pageid not in conf_pageids:
                            conf_pageids.append(link_pageid)
#    with open(path_and_name, 'w') as file:
#        file.writelines(all_file_lines)
    # write the file out
    with open(conf_pageids_filename, 'w') as file:
        for n in conf_pageids:
            file.write(str(n) + '\n')

print(f"Created the file \"{conf_pageids_filename}\" with {len(conf_pageids)} entries")
# These are the Confluence links that I need to convert

# Now I need to collect every .rst file name, as each includes
