#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.firefox.options import Options

options = Options()
options.set_preference("browser.download.folderList",2)
options.set_preference("browser.download.manager.showWhenStarting", False)
options.set_preference("browser.download.dir","/tmp")
options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream,application/vnd.ms-excel")

url = "https://www.degreedays.net/"
weather_station = "KMABROOK44"
base_temp = "68"  # using drop down value!
period_covered = "1"  # 1mon, using drop down value
driver = webdriver.Firefox(firefox_options=options)  # type: WebDriver
driver.get(url)

# weather station
station_input = driver.find_element_by_css_selector('input.gwt-TextBox')
station_input.clear()
station_input.send_keys(weather_station)


# select an option, by value, from a GWT drop down
def select_gwt_dropdown(option_count, desired_option_value):
    candidates = driver.find_elements_by_css_selector('select.gwt-ListBox')
    found_selects = [input for input in candidates if
                     input.is_displayed() and option_count == len(input.find_elements_by_css_selector('option'))]
    temperature_select = found_selects[0]  # there should be 1
    options = Select(temperature_select)
    options.select_by_value(desired_option_value)


# base temperature
select_gwt_dropdown(129, base_temp)
select_gwt_dropdown(37, period_covered)

# click the non-submit button
btn = driver.find_element_by_css_selector('button.submitButton')
btn.click()

# wait for data to be ready
label = (By.CSS_SELECTOR, 'table.dataStatusPanel div.gwt-Label')
WebDriverWait(driver, 30).until(ec.text_to_be_present_in_element(label, 'Your degree days are ready'))

download_btn = driver.find_element_by_css_selector('table.dataStatusPanel div.downloadPanel button.gwt-Button')
download_btn.click()
with driver.download_file() as filename:
    File.copy(filename, final_dest) # start here & fix this call

# gwt is google web toolkit

# Wait for element on a page to go stale to know you have transitioned properly.

driver.quit()
print('Done')
