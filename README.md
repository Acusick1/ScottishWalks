# Scottish Walks
Webapp to view walk starting locations, routes, and allow filtering based on user preferences such as duration, total elevation, and number of Munros climbed. Data has been scraped from [walkhighlands.co.uk](https://www.walkhighlands.co.uk), and GPS routes are currently scraped on request when a user clicks on a given walk.

The motivation for this project is that no current website allows for multiple user filters at once. This is a simple, user-friendly approach that allows users to view walks across the country or a specific area, and filter based on any number of individual preferences.

Streamlit has been used for the initial webapp which can filter the data, but cannot display the routes as the simplified notebook can. The current mapping package is relatively immature (basic Python copy of a native JavaScript library), therefore building a full frontend will likely be required for full functionality.

![Map view](https://www.dropbox.com/s/2dje4ci5qfeeknm/dashboard_all.png?dl=0)

![Filtered walks based on multiple preferences](https://www.dropbox.com/s/crgnt7z5viq261d/dashboard_filtered.png?dl=0)

## Installation
The package has been made using Poetry, and can be installed via:

```
$ git clone https://github.com/Acusick1/ScottishWalks
$ poetry install
```
Or, without Poetry:
```
$ pip -m install .
```

To enable qgrid in Jupyter (used for DataFrame filtering):

```
$ jupyter nbextension enable --py --sys-prefix qgrid
$ jupyter nbextension enable --py --sys-prefix widgetsnbextension
```
## Notes

### Link names
Area data currently taken from stripping link, could be taken when traversing through links by a) getting page headings or b) using link titles when collecting them

### Webdriver
Instructions do not contain info on webdrivers. Package should come with data and no need to scrape data, therefore "main" function not required. Either remove web scraping packages from poetry (or add to dev dependencies), or have development and product branches?

**Until decided... Download the necessary webdriver and ensure it is on the PATH**