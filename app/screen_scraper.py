import json
import sys
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

#TODO: for number of likes per video we would probably need to save all the video links and run a loop over them either with selenium or requests lib

if __name__ == "__main__":
    
    # browser = webdriver.Firefox()
    browser = webdriver.Chrome()
    browser.get('http://www.youtube.com/user/jimmydiresta/videos')

    #hit the I agree button 
    element = browser.find_element(by=By.CSS_SELECTOR, value="form")
    # print(browser.page_source)
    element.submit()

    #each video's info is stored in a <ytd-grid-video-renderer> -> <div id="dismissible"> -> <div id="details"> -> <div id="meta"> 
    #things to look for in the "meta" div: 
    # 1) <h3> -> <a id="video-title">
    # 2) <div id="metadata-container"> -> <div id="metadata"> -> <div id="metadata-line"> -> two <span>s with the view number and date
    
    video_titles = browser.find_elements(by=By.CSS_SELECTOR, value="#video-title")
    video_titles = [x.text for x in video_titles]
    print(len(video_titles))

    #scroll until you reach the bottom of the page
    #TODO: edit the js script to remember the previous scroll value and stop once the scroll value no longer changes from one iteration to the next
    for _ in range(100):
        time.sleep(0.5)
        browser.execute_script("window.scrollTo(0, document.querySelector('#content').scrollHeight);")

    #get all the video titles
    video_titles = browser.find_elements(by=By.CSS_SELECTOR, value="#video-title")
    video_titles = [x.text for x in video_titles]
    print(len(video_titles))

    #TODO: to get all the metadata: first select all the <div id="metadata-line"> and split each of them into the two spans (with further selecting)
    
    #sleep forever for debugging the browser (it closes once the script finishes executing)
    while True:
        time.sleep(3)   

    # with open("page.html", "w", encoding='utf-8') as file:
    #     file.write(browser.page_source)
