# Confluence Dump With Python

Dump Confluence pages using Python (requests) in HTML and RST format, including embedded pictures and attachments.
References to downloaded files will be updated to their local relative path.

## Refactoring in Progress

The steps in the Description section are still valid.

Nonetheless, the refactoring will require only 2 files and accept command-line args:
* `myModules.py`: Contains all the required functions.
* `confluenceDumpWithPython.py`: Script to use with the following command line args:
  * `-m, --mode`: The export mode, `single`, `space`, `bylabel`, `pageprops` (required).
    * Note: Only `single`, `pageprops` and `space` have been implemented so far.
  * `-S, --site`: The Atlassian Site (required).
  * `-s, --space`: The Space Key (if needed).
  * `-p, --page`: The Page ID (if needed).
  * `-l, --label`: The Page label (if needed).
  * `-x, --sphinx`: The `_images` and `_static` folder are placed at the root of the export folder, instead of together with the exported HTML files.

## Description

Purpose of the files:
1. `confluenceExportHTMLrequestsByLabel.py`: download a set of pages based on one (or more) page Labels.
2. `confluenceExportHTMLrequestsSingle.py`: download a single page by supplying the page ID as an argument.
3. `confluenceExportHTMLrequestsPagePropertiesReport.py`: download page properties and all the pages in the report by supplying the page ID as an argument.
4. `confluenceExportHTMLrequestsPagesInSpace.py`: download all pages from a space.

For CSS Styling, it uses the `site.css` from Confluence that can be obtained by using the Workaround described in: https://jira.atlassian.com/browse/CONFSERVER-40907
The 'site.css' file included with HTML exports is not as complete as the one above.

Folder and file structure:

* `<output folder>/<page|space|label>`
  * `<output folder>/<page|space|label>/_images/`
  * `<output folder>/<page|space|label>/_static/`
  * Copies the file `styles/site.css` into `<output folder>/<page|space|label>/_static/`

Note: `<output folder>` will be in the script path if no argument is defined.

## What it does

* leverages the Confluence Cloud API
  * uses CQL with `.../rest/api/search?cql` to search by labels
  * gets **Export View** from pages (`.../rest/api/content/' + str(pageid) + '?expand=body.export_view`)
  * download all Attachments from the page `.../rest/api/content/' + str(pageID) + '?expand=children.attachment`.
  * get page HTML from JSON: `myBodyExportViewHtml = myBodyExportView['body']['export_view']['value']`.
  * use BS to update HTML **dumpHtml(<Page HTML>,<Page Title>,<Page ID>)**.
    * prepend a page header containing a `<head>` as well as a link to the original page.
    * download emoticons (attachments were already downloaded previously).
    * replace `src` to local attachments/embeds/emoticons

## Getting Started

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

* How to download based on a page label.

```
confluenceExportHTMLrequestsByLabel.py <site Name> <page Label of all pages to download> [<output folder>]
```

* How to download a single page based on its ID.

```
confluenceExportHTMLrequestsSingle.py <site Name> <ID of page to dump> [<output folder>]
```

* How to download Page Properties and all the contained pages.

```
confluenceExportHTMLrequestsPagePropertiesReport.py <site Name> <ID of page properties report page> [<output folder>]
```

* How to download a whole Space.

```
confluenceExportHTMLrequestsPagesInSpace.py <site Name> <space KEY> [<output folder>]
```

## Help

No special advice other than:
* make sure that your Atlassian API Token is valid.
* the username for Atlassian API is the e-mail address.


## Authors

Contributors names and contact info

@dernorberto

## Improvements

- [x] Add links to Downloads for the corresponding pages.
- [ ] Update all links from downloaded pages to the local copies.
- [x] Add to headers the parent page and page labels.
- [ ] Create an index of the pages to use as a TOC.
- [ ] Create a page layout to display TOC + articles.
- [x] Copy `styles/site.css` into `output/styles/` if not present.

## Issues

* It does not like very long attachment files, you'll need to rename them before the dump.
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

## License

This project is licensed under the MIT License - see the LICENSE.txt file for details

## Acknowledgments

