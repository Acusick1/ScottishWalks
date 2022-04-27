# Scottish Walks Database

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
Instructions do not contain info on webdriver (Chrome). Package should come with data and no need to scrape data, therefore "main" function not required. Either remove web scraping packages from poetry (or add to dev dependencies), or have development and product branches?

**Until decided... Download the necessary webdriver and ensure it is on the PATH**