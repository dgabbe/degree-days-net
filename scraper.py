#!/usr/bin/env python3


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait


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


GWT_LIST_BOX_CSS = 'select.gwt-ListBox'
GWT_SUBMIT_BUTTON_CSS = 'button.submitButton'
WEATHER_STATION_CSS = 'input.gwt-TextBox'


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
    found_selects = [input for input in candidates if
                     input.is_displayed() and option_count == len(input.find_elements_by_css_selector('option'))]
    temperature_select = found_selects[0]  # there should be 1
    options = Select(temperature_select)
    options.select_by_value(desired_option_value)


def scrape(url, weather_station, base_temp, period_covered):
    # set options to bypass download dialog
    options = Options()
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.download.dir", "/tmp")
    options.set_preference("browser.helperApps.neverAsk.saveToDisk",
                           "application/octet-stream, application/vnd.ms-excel, text/csv")

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
    label = (By.CSS_SELECTOR, 'table.dataStatusPanel div.gwt-Label')
    WebDriverWait(driver, 30).until(ec.text_to_be_present_in_element(label, 'Your degree days are ready'))
    download_btn = driver.find_element_by_css_selector('table.dataStatusPanel div.downloadPanel button.gwt-Button')
    download_btn.click()

    # with driver.download_file() as filename:
    #     File.copy(filename, final_dest) # start here & fix this call
    # gwt is google web toolkit
    # Wait for element on a page to go stale to know you have transitioned properly.

    driver.quit()


def all_displayed_dropdowns_loaded(driver):
    """
    Determine whether all displayed GWT dropdowns have be loaded properly. Pass this to lambda_succeeds to execute as
    the lambda condition

    :param WebDriver driver: driver to which to query
    :rtype: NoneType
    """
    dropdowns = driver.find_elements_by_css_selector(GWT_LIST_BOX_CSS)
    displayed_dropdowns = [select for select in dropdowns if select.is_displayed()]
    options_loaded = [len(select.find_elements_by_css_selector('option')) > 0 for select in displayed_dropdowns]
    all_options_loaded = all(options_loaded)
    return all_options_loaded


def wait_for_gwt_panel(driver):
    timeout = 30
    WebDriverWait(driver, timeout).until(ec.presence_of_element_located((By.CSS_SELECTOR, WEATHER_STATION_CSS)))
    WebDriverWait(driver, timeout).until(lambda_succeeds(all_displayed_dropdowns_loaded))
    WebDriverWait(driver, timeout).until(ec.presence_of_element_located((By.CSS_SELECTOR, GWT_SUBMIT_BUTTON_CSS)))


if __name__ == "__main__":
    url = "https://www.degreedays.net/"
    weather_station = "KMABROOK44"
    base_temp = "68"  # using drop down value!
    period_covered = "1"  # 1mon, using drop down value

    scrape(url, weather_station, base_temp, period_covered)
