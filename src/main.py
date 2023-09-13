import json
import time
import re
import os
import platform
from typing import Iterable, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from settings import RAW_DATA_PATH, PROJECT_PATH

BASE_URL = "https://www.walkhighlands.co.uk"
AREA_LINKS = {}
WALK_LINKS = set()
AREA_LINKS_FILE = PROJECT_PATH / "arealinks.json"
DELAY = 0.5


def get_walk_data(driver, walk_link):

    location = get_area_from_link(walk_link)

    driver.get(walk_link)

    try:
        test = driver.find_element(by=By.ID, value="col")
    except NoSuchElementException:
        return None

    key = test.find_elements(by=By.CSS_SELECTOR, value="dt")
    val = test.find_elements(by=By.CSS_SELECTOR, value="dd")

    data = {}
    for k, v in zip(key, val):
        if k.text in data:
            data[k.text] = ', '.join([data[k.text], v.text])
        else:
            data[k.text] = v.text

    test = driver.find_element(by=By.ID, value="wrapper")
    name = test.find_element(by=By.CSS_SELECTOR, value="h1")
    votes = test.find_element(by=By.CLASS_NAME, value="votes")
    vote_value = votes.find_element(by=By.XPATH, value='//span[@itemprop="ratingValue"]').get_attribute("innerHTML")
    vote_count = votes.find_element(by=By.XPATH, value='//span[@itemprop="ratingCount"]').get_attribute("innerHTML")

    grade = test.find_element(by=By.CLASS_NAME, value="grade")
    grade = len(grade.find_elements(by=By.CSS_SELECTOR, value="img"))

    bog = test.find_element(by=By.CLASS_NAME, value="bog")
    bog = len(bog.find_elements(by=By.CSS_SELECTOR, value="img"))

    # Find all links
    all_links = driver.find_elements_by_tag_name('a')

    # Loop through all found links to find Google Maps link
    start_point_url = None
    for link in all_links:
        start_point_url = link.get_attribute('href')
        if 'www.google.com/maps' in start_point_url:
            break

    print(f"URL: {start_point_url}")

    data = data | location

    data['Name'] = name.text
    data['Rating'] = vote_value
    data['Votes'] = vote_count
    data['Grade'] = grade
    data['Bog'] = bog
    data["Link"] = walk_link
    data["Start Point"] = start_point_url
    data["GPX"] = get_route_link(driver)

    return data


def get_route_link(driver):

    hrefs = driver.find_element(by=By.CSS_SELECTOR, value="ul.box").find_elements(by=By.TAG_NAME, value="a")

    link = None
    for h in hrefs:

        link = h.get_attribute("href")

        if "download.php" in link or link.endswith("GPX"):
            break

    if link is not None:
        driver.get(link)
        time.sleep(DELAY)
        button = driver.find_element(by=By.ID, value="walk_info").find_element(by=By.CLASS_NAME, value="button2")
        return button.get_attribute("href")
    else:
        Exception("GPX link not found")


def get_unique_links(element):

    return {link.get_attribute("href") for link in element.find_elements(by=By.TAG_NAME, value="a")}


def get_links(element):

    return [link.get_attribute("href") for link in element.find_elements(by=By.TAG_NAME, value="a")]


def link_filter(links: Iterable[str]) -> List[str]:

    return [link for link in links if link is not None and not link.endswith('#') and not link.endswith('php')]


def get_area_from_link(link: str) -> dict:

    # Remove base url
    link = re.sub(f".*{BASE_URL}/", "", link)
    # Split link by forward slashes, keep everything after website name
    split = link.split(r'/')
    # Remove anything after period in final split (.shtml)
    split[-1] = split[-1].split('.')[0]

    return {f"Area{i}": area for i, area in enumerate(split)}


def recursive(driver, hrefs):

    for h in hrefs:
        driver.get(h)
        time.sleep(DELAY)
        try:
            area_table = driver.find_element(by=By.ID, value="arealist")
            hrefs = link_filter(get_unique_links(area_table))
            area = {h: hrefs}

        except NoSuchElementException:

            area = {h: ""}

        AREA_LINKS.update(area)


def search_areas(driver):

    for area_link, sub_link in AREA_LINKS.items():

        name = area_link.rstrip("/").split("/")[-1]
        print(f"Searching walks within area: {area_link}")

        walks = []
        for sub in sub_link:
            driver.get(sub)
            time.sleep(DELAY)
            walk_table = driver.find_element(by=By.CLASS_NAME, value="table1")
            walk_links = link_filter(get_unique_links(walk_table))

            for walk in walk_links:

                walk_data = get_walk_data(driver, walk)

                if walk_data is not None:
                    walks.append(walk_data)

        with open(f"{RAW_DATA_PATH}{os.sep}{name}walks.json", 'w') as fout:
            json.dump(walks, fout)


def main():

    if platform.system() == "Windows":
        driver = webdriver.Chrome()
    elif platform.system() == "Linux":
        driver = webdriver.Firefox()
    else:
        Exception(f"No webdriver setup for {platform.system()} system")

    driver.get(BASE_URL)

    nav_bar = WebDriverWait(driver, 10).until(lambda d: d.find_element(by=By.ID, value="nav"))
    lists = nav_bar.find_element(by=By.TAG_NAME, value="li")

    area_links_path = PROJECT_PATH / AREA_LINKS_FILE
    if area_links_path.is_file():
        with open(area_links_path, 'r') as fin:
            AREA_LINKS.update(json.load(fin))
    else:
        recursive(driver, link_filter(get_unique_links(lists)))
        with open(area_links_path, 'w') as fout:
            json.dump(AREA_LINKS, fout)

    search_areas(driver)

    driver.quit()


def tester(link):

    driver = webdriver.Chrome()
    driver.get(link)
    get_route_link(driver)


if __name__ == "__main__":

    # link = r"https://www.walkhighlands.co.uk/fortwilliam/beinn-iaruinn.shtml"
    # tester(link)

    main()

