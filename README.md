# Confluence Dump With Python

Dump Confluence pages using Python (requests) in HTML and RST format, including embedded pictures and attachments.
References to downloaded files will be updated to their local relative path.

## Description

Nonetheless, the refactoring will require only 2 files and accept command-line args:
* `myModules.py`: Contains all the required functions.
* `confluenceDumpWithPython.py`: Script to use with the following command line args:
  * `-m, --mode`: The export mode, `single`, `space`, `bylabel`, `pageprops` (required).
    * Note: Only `single`, `pageprops` and `space` have been implemented so far.
  * `-S, --site`: The Atlassian Site (required).
  * `-s, --space`: The Space Key (if needed).
  * `-p, --page`: The Page ID (if needed).
  * `-l, --label`: The Page label (if needed).
  * `-x, --sphinx`: The `_images` and `_static` folders are placed at the root of the export folder, instead of together with the exported HTML files.
  * `--notags`: Does not add the tags directives to the rst files (when the `sphinx-tags` addon is not used).
* `updatePageLinks.py`: Update online confluence links to the local files that have been downloaded so far.
  * `--folder`: Folder containing the files to update.
  * `--test`: Instead of overwriting the original .rst files, it will create updated ones with `zout_` as a prefix.
* `getPageEditorVersion.py`: Get the editor version from single pages or all pages in a space.
  * `--site`: The Atlassian Site (required).
  * `--page`: Page ID (either/or)
  * `--space`: Space Key (either/or)

For CSS Styling, it uses the `confluence.css` from Confluence that can be obtained by using the Workaround described in: https://jira.atlassian.com/browse/CONFSERVER-40907.
The `site.css` file included with Confluence UI HTML exports is not as complete as the one above.

### Folder and file structure:

* The default output folder is `output/` under the same path as the script.
* A folder with the Space name, Page Properties report page, single page name or Page Label name will be created under the output folder.
* By default, the `_images/` and `_static/` folders will be placed in the page|space|pageprops|label folder.
  * The `--sphinx` command line option will put those folder directly under the output folder
* The file `styles/confluence.css` will be copied into the defined `_static/`

## What it does

* Leverages the Confluence Cloud API
* Puts Confluence meta data like Page ID and Page Labels, in the HTML headers and RST fields.
* beautifulsoup is used to parse HTML to get and update content, ie. change remote links to local links.
* Download for every page, all attachments, emoticons and embedded files.

## Requirements

* declare system variables:
  * `atlassianAPIToken`
  * `atlassianUserEmail`

### Dependencies

* python3
  * requests
  * beautifulsoup4
  * Pillow (handle images)
  * pandoc & pypandoc (convert to RST)
  * re

### Installing

* Clone repo.
* Install dependencies.
* Declare system variables for Atlassian API Token.

### Executing program


* How to download a single page based on its ID.

```
confluenceDumpWithPython.py -m single -S <site Name> -p <ID of page to dump> [<output folder>] [--sphinx]
```

* How to download Page Properties and all the contained pages.

```
confluenceDumpWithPython.py -m pageprops -S <site Name> -p <ID of page properties report page> [<output folder>] [--sphinx]
```

* How to download a whole Space.

```
confluenceDumpWithPython.py -m space -S <site Name> -s <space KEY> [<output folder>]
```

## Help

No special advice other than:
* make sure that your Atlassian API Token is valid.
* the username for the Cloud Atlassian API is the e-mail address.

## Authors

Contributors names and contact info

@dernorberto

## Improvements

- [ ] Add export based on page label.
- [x] Add links to Downloads for the corresponding pages.
- [x] Update all links from downloaded pages to the local copies.
- [x] Add to headers the parent page and page labels.
- [ ] Create an index of the pages to use as a TOC.
- [ ] Create a page layout to display TOC + articles.
- [x] Copy `styles/site.css` into `output/styles/` if not present.
- [ ] Allow using with Confluence Server.

## Issues

* It does not like very long attachment files, you'll need to rename them in Confluence before the dump.
* Pages previously migrated from Confluence Server might have issues with old emoticons. The best is to convert the pages to the New Editor, which will replace the missing emoticons.

## Version History
* 1.4
  * Refactoring into a more simple file setup (`confluenceDumpWithPython.py` & `myModules.py`)
* 1.3
  * Added Space export (flat folder structure)
* 1.2
  * Added better HTML header and footer.
  * Added page labels to HTML headers.
  * Improved output folder argument logic.
* 1.1
  * Added Papge Properties dump and other smaller things
* 1.0
  * Initial Release

## legacy/ folder with previous version of scripts

Purpose of the files:
1. `confluenceExportHTMLrequestsByLabel.py`: download a set of pages based on one (or more) page Labels.
2. `confluenceExportHTMLrequestsSingle.py`: download a single page by supplying the page ID as an argument.
3. `confluenceExportHTMLrequestsPagePropertiesReport.py`: download page properties and all the pages in the report by supplying the page ID as an argument.
4. `confluenceExportHTMLrequestsPagesInSpace.py`: download all pages from a space.

## License

This project is licensed under the MIT License - see the LICENSE.txt file for details

## Acknowledgments

