# Confluence Dump With Python

Dump Confluence pages using Python (requests) in HTML format, including embedded pictures and attachments.
It will updated all references to downloaded files to their local relative path.

## Description

Purpose of the files:
1. `confluenceExportHTMLrequestsByLabel.py`: download a set of pages based on one (or more) page Labels.
2. `confluenceExportHTMLrequestsSingle.py`: download a single page by supplying the page ID as an argument.

For CSS Styling, it uses the `site.css` file that Confluence gnerates when exporting in HTML.

It will create the folder structure
* `output/`
  * `output/attachments/`
  * `output/emoticons/`

You will need to manually copy the file `styles/site.css` into `output/styles/`.

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
* manually copy the file `styles/site.css` into `output/styles/`.

### Dependencies

* python3
  * requests
  * beautifulsoup4

### Installing

* Clone repo.
  * It includes `styles/site.css`
* Install dependencies.
* Declare system variables for Atlassian API Token.

### Executing program

* How to download based on a page label.

```
confluenceExportHTMLrequestsByLabel.py <site Name> <page Label of all pages to download>
```

* How to download a single page based on its ID.
 
```
confluenceExportHTMLrequestsSingle.py <site Name> <ID of page to dump>
```

## Help

No special advice other than:
* make sure that your Atlassian API Token is valid.
* the username for Atlassian API is the e-mail address.


## Authors

Contributors names and contact info

@dernorberto

## Improvements

* Create an index of the pages to use as a TOC.
* Create a page layout to display TOC + articles.
* Copy `styles/site.css` into `output/styles/` if not present.

## Version History

* 1.0
    * Initial Release

## License

This project is licensed under the MIT License - see the LICENSE.txt file for details

## Acknowledgments

