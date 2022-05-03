import json
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def submit_form(browser: webdriver.Chrome):
    element = browser.find_element(by=By.CSS_SELECTOR, value="form")
    element.submit()


browser = webdriver.Chrome()
browser.get('https://www.youtube.com/c/StudyMD/videos')
submit_form(browser)
print(len(browser.find_elements(by=By.CSS_SELECTOR, value="#video-title")))