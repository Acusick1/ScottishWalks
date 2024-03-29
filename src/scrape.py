import json
import pandas as pd
import time
import re
import os
from typing import Iterable
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from config import settings

BASE_URL = "https://www.walkhighlands.co.uk"
AREA_LINKS = {}
WALK_LINKS = set()
AREA_LINKS_FILE = settings.root_path / "arealinks.json"
DELAY = 0.5


def get_walk_data(driver, walk_link: str) -> pd.DataFrame:

    location = get_area_from_link(walk_link)

    driver.get(walk_link)

    try:
        column = driver.find_element(by=By.ID, value="col")
    except NoSuchElementException:
        return None

    key = column.find_elements(by=By.CSS_SELECTOR, value="dt")
    val = column.find_elements(by=By.CSS_SELECTOR, value="dd")

    data = {}
    for k, v in zip(key, val):
        if k.text in data:
            data[k.text] = ', '.join([data[k.text], v.text])
        else:
            data[k.text] = v.text

    wrapper = driver.find_element(by=By.ID, value="wrapper")
    name = wrapper.find_element(by=By.CSS_SELECTOR, value="h1")
    votes = wrapper.find_element(by=By.CLASS_NAME, value="votes")
    vote_value = votes.find_elements(by=By.CSS_SELECTOR, value="span")[0].get_attribute("innerHTML")
    vote_count = votes.find_elements(by=By.CSS_SELECTOR, value="span")[-1].get_attribute("innerHTML")

    grade = wrapper.find_element(by=By.CLASS_NAME, value="grade")
    grade = len(grade.find_elements(by=By.CSS_SELECTOR, value="img"))

    bog = wrapper.find_element(by=By.CLASS_NAME, value="bog")
    bog = len(bog.find_elements(by=By.CSS_SELECTOR, value="img"))

    # Loop through all found links to find Google Maps link
    all_links = wrapper.find_elements(by=By.TAG_NAME, value="a")

    start_point_url = None
    for link in all_links:
        start_point_url = link.get_attribute('href')
        if 'www.google.com/maps' in start_point_url:
            break

    print(f"URL: {start_point_url}")

    data = data | location

    data["Name"] = name.text
    data["Rating"] = vote_value
    data["Votes"] = vote_count
    data["Grade"] = grade
    data["Bog"] = bog
    data["Link"] = walk_link
    data["StartPoint"] = start_point_url
    data["GPX"] = get_route_link(driver)

    return data


def get_route_link(driver) -> str:

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


def get_unique_links(element) -> set[str]:

    return {link.get_attribute("href") for link in element.find_elements(by=By.TAG_NAME, value="a")}


def get_links(element) -> set[str]:

    return [link.get_attribute("href") for link in element.find_elements(by=By.TAG_NAME, value="a")]


def link_filter(links: Iterable[str]) -> list[str]:

    return [link for link in links if link is not None and not link.endswith('#') and not link.endswith('php')]


def get_area_from_link(link: str) -> dict:

    # Remove base url
    link = re.sub(f".*{BASE_URL}/", "", link)
    # Split link by forward slashes, keep everything after website name
    split = link.split(r'/')
    # Remove anything after period in final split (.shtml)
    split[-1] = split[-1].split('.')[0]

    return {f"Area{i}": area for i, area in enumerate(split)}


def recursive(driver, hrefs: Iterable[str]) -> None:

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

        with open(f"{settings.raw_data_path}{os.sep}{name}walks.json", 'w') as fout:
            json.dump(walks, fout)


def main():

    try:
        driver = webdriver.Firefox()
    except Exception as e:
        print("Firefox webdriver failed, trying Chrome ...")
        driver = webdriver.Chrome()

    driver.get(BASE_URL)

    nav_bar = WebDriverWait(driver, 10).until(lambda d: d.find_element(by=By.ID, value="nav"))
    lists = nav_bar.find_element(by=By.TAG_NAME, value="li")

    area_links_path = settings.root_path / AREA_LINKS_FILE
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

