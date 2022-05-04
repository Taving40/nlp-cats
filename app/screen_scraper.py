import json
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#NOTE:  #each video's info is stored in a <ytd-grid-video-renderer> -> <div id="dismissible"> -> <div id="details"> -> <div id="meta"> 
        #things to look for in the "meta" div: 
        # 1) <h3> -> <a id="video-title">
        # 2) <div id="metadata-container"> -> <div id="metadata"> -> <div id="metadata-line"> -> two <span>s with the view number and date

#NOTE:  #to see how many videos the channel has query: https://www.youtube.com/results?search_query=channel_name
        #then look for this span
        # <span id="video-count" class="style-scope ytd-channel-renderer"> NUMBER_OF_VIDEOS videos </span>

#NOTE:  #to get video links, each is contained in an "a" tag with an id of "thumbnail"

#NOTE:  #useful script for getting all of an elements attributes:
        #attrs = browser.execute_script('var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index) { items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; return items;', 
        #                               element) #where elemnt is the element we wish to get the attributes for

class VideoInfo():

    def __init__(self, title=None, length=None, views=None, likes=None, date=None, link=None, desc=None):
        self.title = title
        self.length = length
        self.views = views
        self.likes = likes
        self.date = date
        self.link = link
        self.desc = desc

    def __repr__(self):
        return f"\n Title:{self.title}, Len:{self.length}, Views:{self.views}, Likes:{self.likes}, Date:{self.date}, Link:{self.link}\n"

    def __str__(self):
        return f"\n Title:{self.title}, Len:{self.length}, Views:{self.views}, Likes:{self.likes}, Date:{self.date}, Link:{self.link}\n"

    def to_dict(self):
        return {
                "title": self.title,
                "length": self.length, 
                "views": self.views,
                "likes": self.likes, 
                "date": self.date,
                "link": self.link,
                "description": self.desc,
                }
    
    def to_json(self):
        return json.dumps(self.to_dict())

def get_number_of_videos_and_subscribers(channel_name):
    browser = webdriver.Edge()
    browser.set_page_load_timeout(10)
    browser.implicitly_wait(10)
    browser.get(f'https://www.youtube.com/results?search_query={channel_name}')
    submit_form(browser)
    number_of_vids = browser.find_element(by=By.CSS_SELECTOR, value="#video-count").text
    number_of_subs = browser.find_element(by=By.CSS_SELECTOR, value="span#subscribers").text
    browser.close()
    temp_index = number_of_vids.find(" ")
    if temp_index == -1:
        raise Exception("Number of videos has unexpected format")
    
    number_of_vids = int(number_of_vids[0:temp_index].replace(",", ""))
    return number_of_vids, number_of_subs

def submit_form(browser: webdriver.Edge):
    element = browser.find_element(by=By.CSS_SELECTOR, value="form")
    element.submit()

def write_video_info(videos: list, file: str, number_of_subs:str=None, channel_name:str=None, number_of_vids:int=None)->None:
    with open(file, "w", encoding="utf-8") as f:
        videos = [x.to_dict() for x in videos]
        result = {
            "channel name": channel_name,
            "number of subscribers": number_of_subs,
            "number of videos": number_of_vids,
            "videos": videos
        }
        f.write(json.dumps(result, indent=3))

def write_video_info_100(videos:list, file:str, index):
    slice_of_vids = [vid.to_dict() for vid in videos[index-100:index]]
    with open(file, "a", encoding="utf-8") as f:
        f.write(json.dumps(slice_of_vids, indent=3))

def parse_description(parent_element: WebElement) -> str:
    res = []
    children = parent_element.find_elements(by=By.CSS_SELECTOR, value="*")
    for child in children:
        res.append(child.text + "\n")
    return ' '.join(res)


def get_video_info(browser: webdriver.Edge, file:str) -> tuple:

    videos = []

    time.sleep(1)

    video_titles = browser.find_elements(by=By.CSS_SELECTOR, value="#video-title")
    video_links = browser.find_elements(by=By.CSS_SELECTOR, value="#thumbnail")

    for x in list(video_links):
        if not x.get_attribute("href"):
            video_links.remove(x)

    for i in range(len(video_titles)):
        videos.append(VideoInfo(
            title=video_titles[i].text,
            length=video_links[i].text,
            link=video_links[i].get_attribute("href"),
        ))

    for video in list(videos):
        if video.link.find("shorts") != -1:
            videos.remove(video)

    print("Initial length of videos: ", len(videos))

    for video in list(videos):
        print("Now trying for video ", videos.index(video))

        if videos.index(video) % 100 == 0: #save periodically to avoid data loss on crash
            write_video_info_100(videos, file, videos.index(video))

        print("Opening new window...")

        browser.execute_script("window.open();")            #open new tab
        browser.switch_to.window(browser.window_handles[1]) #switch to new tab

        #Sometimes process hangs on this get
        try:
            browser.get(f'{video.link}')
        except Exception:
            print("Page failed to load...continuing to next video")
            browser.execute_script("window.close();")
            browser.switch_to.window(browser.window_handles[0]) #switch to new tab
            time.sleep(3)
            browser.close()
            browser = webdriver.Edge()
            browser.set_page_load_timeout(10)
            browser.implicitly_wait(10)
            videos.remove(video)
            print("After re-opening browser, length of videos is ", len(videos))
            continue
        print("Done opening new window!")


        view_count = None
        print("Getting view_count...")
        try:
            view_count = browser.find_element(by=By.CSS_SELECTOR, value=".view-count")
        except Exception:
            pass
        print("Done getting view_count!")

        likes = None
        print("Getting likes...")
        try:
            likes = browser.find_element(by=By.CSS_SELECTOR, value="yt-formatted-string.style-scope.ytd-toggle-button-renderer.style-text")
        except Exception:
            pass
        print("Done getting likes!")

        date = None
        print("Getting date...")
        try:
            date = browser.find_element(by=By.CSS_SELECTOR, value="#info-strings yt-formatted-string.style-scope.ytd-video-primary-info-renderer")
        except Exception:
            pass
            print("Done getting date! ", date.text)

        desc = None
        print("Getting description...")
        try:
            desc = browser.find_element(by=By.CSS_SELECTOR, value="div#description yt-formatted-string")
        except Exception:
            pass
            print("Done getting description!")

        print("Storing information in video object...")
        if view_count:
            video.views = view_count.text
        if likes and likes.get_attribute("aria-label"):
            video.likes = likes.get_attribute("aria-label")
        if likes and not video.likes:
            video.likes = likes.text
        if date:
            video.date = date.text
        if desc:
            video.desc = parse_description(desc)
        print("Done storing information in video object!\n")

        browser.execute_script("window.close();")
        browser.switch_to.window(browser.window_handles[0]) #switch to new tab

    return videos, browser

def get_number_of_rendered_vids(browser: webdriver.Edge)-> int:
    return len(browser.find_elements(by=By.CSS_SELECTOR, value="ytd-grid-video-renderer.style-scope.ytd-grid-renderer"))

def scroll_to_bottom(browser: webdriver.Edge, number_of_videos: int, hard_cap:int=3000) -> None:
    """This function scrolls to the bottom of the window to allow render of next batch of 30 videos.
    It does this for number_of_videos/30 + 1 to reach the bottom of the page."""

    number_of_repeated_loops = 0
    while get_number_of_rendered_vids(browser) < number_of_videos \
        and get_number_of_rendered_vids(browser) < hard_cap \
        and number_of_repeated_loops < 50:

        previous_nr_of_vids = get_number_of_rendered_vids(browser)
        new_nr_of_vids = -1
        number_of_repeated_loops = 0
        browser.execute_script("window.scrollTo(0, document.querySelector('#content').scrollHeight);")
        while new_nr_of_vids <= previous_nr_of_vids \
            and number_of_repeated_loops < 50:
            time.sleep(0.3)
            number_of_repeated_loops += 1
            # print(number_of_repeated_loops)
            new_nr_of_vids = get_number_of_rendered_vids(browser)


def get_channel_name_from_link(link:str) -> str:
    browser = webdriver.Edge()
    browser.set_page_load_timeout(10)
    browser.implicitly_wait(10)
    browser.get(link)
    submit_form(browser)
    channel_name = browser.find_element(by=By.CSS_SELECTOR, value="yt-formatted-string.ytd-channel-name").text
    browser.close()
    return channel_name

    # alternative hard coded way of getting channel name (might fail on some link formats)
    # temp_index_start = link.find("user")
    # if temp_index_start == -1:
    #     temp_index_start = link.find("channel")
    # temp_index_end = link.find("/videos")
    # return link[temp_index_start+5:temp_index_end]

if __name__ == "__main__":

    #defaults if none were provided from cli
    LINKS = ['http://www.youtube.com/user/jimmydiresta/videos']
    CHANNEL_NAMES = ['jimmydiresta']
    RESULT_FILE_NAMES = ["result.json"]
    
    if len(sys.argv) >= 2:
        LINKS = list(sys.argv[1:])
        CHANNEL_NAMES = [get_channel_name_from_link(link) for link in LINKS]
        RESULT_FILE_NAMES = [f"{name}.json" for name in CHANNEL_NAMES]

    for i in range(len(LINKS)):

        if LINKS[i].find('videos') == -1:
            raise Exception("Bad link format, link should end with /videos")
        
        print("Getting channel's number of videos...")
        number_of_videos, number_of_subscribers = get_number_of_videos_and_subscribers(CHANNEL_NAMES[i])
        

        browser = webdriver.Edge()
        browser.set_page_load_timeout(10)
        browser.implicitly_wait(10)
        browser.get(LINKS[i])

        #hit the "I agree" button
        submit_form(browser)

        print("Scrolling to render all of the channel's videos...")
        scroll_to_bottom(browser, number_of_videos)

        print("Getting videos info...")
        VIDEOS_INFO, browser = get_video_info(browser, RESULT_FILE_NAMES[i])
        
        print("Writing videos info to file...")
        write_video_info(VIDEOS_INFO, RESULT_FILE_NAMES[i], number_of_subscribers, CHANNEL_NAMES[i], number_of_videos)

        browser.close()
        
    print("All done! :D")

