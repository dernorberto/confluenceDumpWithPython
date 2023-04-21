# Confluence Dump With Python

Dump Confluence pages using Python (requests) in HTML format, including embedded pictures and attachments.
It will updated all references to downloaded files to their local relative path.

## Description

Purpose of the files:
1. `confluenceExportHTMLrequestsByLabel.py`: download a set of pages based on one (or more) page Labels.
2. `confluenceExportHTMLrequestsSingle.py`: download a single page by supplying the page ID as an argument.
3. `confluenceExportHTMLrequestsPagePropertiesReport.py`: download page properties and all the pages in the report by supplying the page ID as an argument.

For CSS Styling, it uses the `site.css` from Confluence that can be obtained by using the Workaround described in: https://jira.atlassian.com/browse/CONFSERVER-40907
The 'site.css' file included with HTML exports is not as complete as the one above.

Folder and file structure:

* `output/<pageID>`
  * `output/<pageID>/attachments/`
  * `output/<pageID>/emoticons/`
  * `output/<pageID>/styles/`
  * Copies the file `styles/site.css` into `output/<pageID>/styles/`.

## What it does

* **getPagesByLabel**: use CQL with `.../rest/api/search?cql` to search by labels.
* **getIDs**: Gets `pageIDs` of all the found pages.
* **getTitles**: Gets page titles of all the found pages.
* FOR loop to cycle through the `pageIDs`.
  * **getBodyExportView**: download Export View for the page `.../rest/api/content/' + str(pageid) + '?expand=body.export_view`.
  * **getAttachments**: download all Attachments from the page `.../rest/api/content/' + str(pageID) + '?expand=children.attachment`.
  * get complete Export View in JSON: `myBodyExportView = getBodyExportView(pageID).json()`.
  * get page HTML from JSON: `myBodyExportViewHtml = myBodyExportView['body']['export_view']['value']`.
  * use BS to update HTML **dumpHtml(<Page HTML>,<Page Title>,<Page ID>)**.
    * prepend a page header containing a `<head>` as well as a link to the original page.
    * download emoticons (attachments were already downloaded previously).
    * replace `src` to local attachments/embeds.
    * replace `src` to local emoticons.

## Getting Started

* declare system variables:
  * `atlassianAPIToken`
  * `atlassianUserEmail`

### Dependencies

* python3
  * requests
  * beautifulsoup4

### Installing

* Clone repo.
  * It already includes `styles/site.css`
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

## Help

No special advice other than:
* make sure that your Atlassian API Token is valid.
* the username for Atlassian API is the e-mail address.


## Authors

Contributors names and contact info

@dernorberto

## Improvements

[ ] Create an index of the pages to use as a TOC.
[ ] Create a page layout to display TOC + articles.
[x] Copy `styles/site.css` into `output/styles/` if not present.

## Version History

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

