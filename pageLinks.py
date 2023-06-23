import os
import re
import sys


if len(sys.argv) > 1:
    try:
        target_folder = sys.argv[1]
    except IndexError:        
        raise SystemExit(f"ERROR, Target folder is not correct")
else:
    target_folder = os.path.join(os.getcwd(),"output/679313542-Move to UK")

file_type = '.rst'
# dict with .rst files pageids and filenames
rst_pageids = {}
# filename for export file
rst_pageids_filename = "z_rst_pageids.txt"

#
# ROUND 1
# get from all local RST files: page ID and filename
#
for filename in os.listdir(target_folder):
    if filename.endswith(file_type):
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
    else:
        continue

#
# ROUND 2
# go through all files again and replace confluence URLs with the local filenames
#

conf_pageids = []
conf_pageids_filename = "z_conf_pageids.txt"

for filename in os.listdir(target_folder):
    if filename.endswith(file_type):
        path_and_name = os.path.join(target_folder, filename)
#####################
        with open(path_and_name) as file:
            contents = file.read()
            while line := file.readline():
                if "<https://optile.atlassian.net/wiki/spaces/" in line and "/pages/" in line and not line.startswith("Original URL:"):
                    for find_match in re.findall(r'<(.*?)>',line):
        #                    for find_match in re.findall("<https://optile.atlassian.net(.+?)>",line):      # commenting to try the one above
                        try:
                            # getting the pageID out of the confluence URL
                            link_pageid = find_match.split("/pages/")[1].split("/")[0].split("#")[0]
                            # using that pageID to match with the one in the "rst_pageids" dict
                            link_rst_file = rst_pageids[link_pageid]
                            # This is where I am stuck
                            # TODO
                            # I need to replace the text between < > with the local target file
                            re.sub(r'<(.*?)>',link_rst_file,find_match)
                            print(line)
                            print(find_match)
                        except:
                            print(f"The match {find_match} in file {filename} does not work")
                        if link_pageid not in conf_pageids:
                            conf_pageids.append(link_pageid)

        # write the file out
        with open(conf_pageids_filename, 'w') as file:
            for n in conf_pageids:
                file.write(str(n) + '\n')

print(f"Created the file \"{conf_pageids_filename}\" with {len(conf_pageids)} entries")
# These are the Confluence links that I need to convert

# Now I need to collect every .rst file name, as each includes
