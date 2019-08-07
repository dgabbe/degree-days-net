#!/usr/bin/env python3


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

from os import path # finish adding individual classes
import os
import time


class lambda_succeeds(object):
    """
    WebDriverWait class for lambda that takes a WebDriver - waits until lambda returns non-falsey or timeout

    custom_lambda - lambda that takes a WebDriver as argument
    returns non-falsey that the custom_lambda returned
    """

    def __init__(self, custom_lambda):
        self.custom_lambda = custom_lambda

    def __call__(self, driver):
        return self.custom_lambda(driver)


GWT_LIST_BOX_CSS = "select.gwt-ListBox"
GWT_SUBMIT_BUTTON_CSS = "button.submitButton"
WEATHER_STATION_CSS = "input.gwt-TextBox"


# select an option, by value, from a GWT drop down
def select_gwt_dropdown(driver, option_count, desired_option_value):
    """
    Select an option in an anonymous GWT dropdown. Because there are multiple GWT dropdowns, use the one that has
    `option_count` number of options. Then select the option that has `desirec_option_value`.
    :param WebDriver driver:
    :param int option_count: exact number of options for the dropdown
    :param str desired_option_value: value of the dropdown list to select
    :return: None
    :rtype: NoneType
    """
    candidates = driver.find_elements_by_css_selector(GWT_LIST_BOX_CSS)
    found_selects = [
        input
        for input in candidates
        if input.is_displayed()
        and option_count == len(input.find_elements_by_css_selector("option"))
    ]
    temperature_select = found_selects[0]  # there should be 1
    options = Select(temperature_select)
    options.select_by_value(desired_option_value)


def get_latest_file(directory, time_to_wait=60):
    """
    Return full pathname of the newest file in a directory. Based on https://stackoverflow.com/a/40518772
    :param str directory:
    :param int time_to_wait:
    :return: complete path of newest file
    """

    def fn_by_ctime(fname):
        try:
            return path.getctime(path.join(directory, fname))
        except FileNotFoundError:
            return -1.0  # in case file is sym link

    fn_newest_file = lambda: max([f for f in os.listdir(directory)], key=fn_by_ctime)

    filename = fn_newest_file()
    time_counter = 0
    while ".part" in filename or ".crdownload" in filename:  # firefox, chrome
        time.sleep(1)
        time_counter += 1
        if time_counter > time_to_wait:
            raise Exception("Waited too long for file to download")

    return path.join(directory, fn_newest_file())


def scrape(url, weather_station, base_temp, period_covered, download_directory="/tmp"):
    """

    :param str url:
    :param str weather_station:
    :param str base_temp:
    :param str period_covered:
    :param str download_directory: where to put the downloaded file
    :return: complete pathname of downloaded CSV
    :rtype: str
    """
    # options to skip download dialog - http://allselenium.info/file-downloads-python-selenium-webdriver/
    options = Options()
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)

    options.set_preference("browser.download.dir", download_directory)

    downloadable_mimetypes = ", ".join(
        [
            "application/csv",
            "application/pdf",
            "application/zip",
            "text/csv",
            "text/plain",
        ]
    )
    options.set_preference(
        "browser.helperApps.neverAsk.saveToDisk", downloadable_mimetypes
    )

    driver = webdriver.Firefox(options=options)  # type: WebDriver
    driver.get(url)

    # GWT takes forever to appear on page
    wait_for_gwt_panel(driver)

    # enter desired weather station
    station_input = driver.find_element_by_css_selector(WEATHER_STATION_CSS)
    station_input.clear()
    station_input.send_keys(weather_station)

    # base temperature & period
    select_gwt_dropdown(driver, 129, base_temp)
    select_gwt_dropdown(driver, 37, period_covered)

    # click the non-submit button (not a true submit button)
    btn = driver.find_element_by_css_selector(GWT_SUBMIT_BUTTON_CSS)
    btn.click()

    # wait for data to be ready
    label = (By.CSS_SELECTOR, "table.dataStatusPanel div.gwt-Label")
    WebDriverWait(driver, 30).until(
        ec.text_to_be_present_in_element(label, "Your degree days are ready")
    )
    download_btn = driver.find_element_by_css_selector(
        "table.dataStatusPanel div.downloadPanel button.gwt-Button"
    )
    download_btn.click()

    time.sleep(1)  # hack to give browser time to save file
    downloaded_file = get_latest_file(download_directory)
    driver.quit()

    return downloaded_file


def all_displayed_dropdowns_loaded(driver):
    """
    Determine whether all displayed GWT dropdowns have be loaded properly. Pass this to lambda_succeeds to execute as
    the lambda condition

    :param WebDriver driver: driver to which to query
    :rtype: NoneType
    """
    dropdowns = driver.find_elements_by_css_selector(GWT_LIST_BOX_CSS)
    displayed_dropdowns = [select for select in dropdowns if select.is_displayed()]
    options_loaded = [
        len(select.find_elements_by_css_selector("option")) > 0
        for select in displayed_dropdowns
    ]
    all_options_loaded = all(options_loaded)
    return all_options_loaded


def wait_for_gwt_panel(driver):
    timeout = 30
    WebDriverWait(driver, timeout).until(
        ec.presence_of_element_located((By.CSS_SELECTOR, WEATHER_STATION_CSS))
    )
    WebDriverWait(driver, timeout).until(
        lambda_succeeds(all_displayed_dropdowns_loaded)
    )
    WebDriverWait(driver, timeout).until(
        ec.presence_of_element_located((By.CSS_SELECTOR, GWT_SUBMIT_BUTTON_CSS))
    )


if __name__ == "__main__":
    URL = "https://www.degreedays.net/"
    WEATHER_STATION = "KMABROOK44"
    BASE_TEMPERATURE = "68"  # using drop down value!
    PERIOD_COVERED = "1"  # 1mon, using drop down value

    csv_filename = scrape(URL, WEATHER_STATION, BASE_TEMPERATURE, PERIOD_COVERED)
    print(csv_filename)
