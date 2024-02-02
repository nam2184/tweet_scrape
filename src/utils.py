import os
import re
from time import sleep
import random
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FireService
import datetime
import pandas as pd
from selenium.webdriver.common.keys import Keys
# import pathlib
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

import urllib


# current_dir = pathlib.Path(__file__).parent.absolute()
def get_data(card,all_links,post_url,save_images=False,type='post',text_value=None):
    """Extract data from tweet card"""
    image_links = []
    #print(card)
    try:
        username = card.find_element("xpath", './/span').text
    except:
        #print("No username found")
        return

    try:
        handle = card.find_element("xpath", './/span[contains(text(), "@")]').text
    except:
        #print("No handle found")
        return

    try:
        postdate = card.find_element("xpath",'.//time').get_attribute('datetime')
    except:
        #print("No postdate found")
        return

    try:
        text = card.find_element("xpath",'.//div[2]/div[2]/div[1]').text
    except:
        text = ""

    try:
        embedded = card.find_element("xpath",'.//div[2]/div[2]/div[2]').text
    except:
        embedded = ""

    # text = comment + embedded

    try:
        reply_cnt = card.find_element("xpath",'.//div[@data-testid="reply"]').text
    except:
        reply_cnt = 0

    try:
        retweet_cnt = card.find_element("xpath",'.//div[@data-testid="retweet"]').text
    except:
        retweet_cnt = 0

    try:
        like_cnt = card.find_element("xpath",'.//div[@data-testid="like"]').text
    except:
        like_cnt = 0

    try:
        elements = card.find_elements("xpath",'.//div[2]/div[2]//img[contains(@src, "https://pbs.twimg.com/")]')
        for element in elements:
            image_links.append(element.get_attribute('src'))
    except:
        image_links = []

    # if save_images == True:
    #	for image_url in image_links:
    #		save_image(image_url, image_url, save_dir)
    # handle promoted tweets

    try:
        promoted = card.find_elements("xpath",'.//div[2]/div[2]/[last()]//span').text == "Promoted"
    except:
        promoted = False
    if promoted:
        print("Promoted")
        return 

    # get a string of all emojis contained in the tweet
    try:
        emoji_tags = card.find_elements("xpath",'.//img[contains(@src, "emoji")]')
    except:
        #print("Emoji list not found")
        return
    emoji_list = []
    for tag in emoji_tags:
        try:
            filename = tag.get_attribute('src')
            emoji = chr(int(re.search(r'svg\/([a-z0-9]+)\.svg', filename).group(1), base=16))
        except AttributeError:
            continue
        if emoji:
            emoji_list.append(emoji)
    emojis = ' '.join(emoji_list)

    # tweet url
    try:
        element = card.find_element("xpath",'.//a[contains(@href, "/status/")]')
        tweet_url = element.get_attribute('href')
        if type == 'comment':
            match = re.search(r'/(\d+)', tweet_url)
            if match:
                numeric_id = match.group(1)
            else:
                print("Numeric ID not found in the URL.")
            match = re.search(r'/(\d+)', post_url)
            if match:
                post_numeric = match.group(1)
            else:
                print("Numeric ID not found in the URL.")
            try :
                if int(reply_cnt) > 0 and numeric_id != post_numeric:
                    all_links.append(tweet_url)
            except:
                pass
    except:
        tweet_url='' 
    if text_value == None and type != 'comment' :
        data_dict = {'tweet' : (username, handle, postdate, text, embedded, emojis, reply_cnt, retweet_cnt, like_cnt, image_links, tweet_url), 'links' : None}
        return data_dict
    data_dict = {'tweet' : (username, handle, postdate, text, embedded, emojis, reply_cnt, retweet_cnt, like_cnt, image_links, tweet_url, text_value), 'links' : None}
    return data_dict


def init_driver(headless=True, proxy=None, show_images=False, option=None,user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'):
    """ initiate a chromedriver or edgedriver instance 
        --option : other option to add (str)
    """
    path = os.path.join(os.getcwd(), 'chromedriver.exe')
    chrome_service = ChromeService(path)
    options = ChromeOptions()
    if headless is True:
        print("Scraping on headless mode.")
        options.add_argument('--disable-gpu')
        options.headless = True
    else:
        options.headless = False
    options.add_argument('log-level=3')
    if proxy is not None:
        options.add_argument('--proxy-server=%s' % proxy)
        print("using proxy : ", proxy)
    if show_images == False:
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
    if option is not None:
        options.add_argument(option)
    options.add_argument(f'user-agent={user_agent}')
    driver = webdriver.Chrome(service = chrome_service ,options=options)
    driver.set_page_load_timeout(100)
    return driver


def log_search_page(driver, since, until_local, lang, display_type, words, to_account, from_account, mention_account,
                    hashtag, filter_replies, proximity, minreplies, minlikes, minretweets):
    """ Search for this query between since and until_local"""
    # format the <from_account>, <to_account> and <hash_tags>
    from_account = "(from%3A" + from_account + ")%20" if from_account is not None else ""
    to_account = "(to%3A" + to_account + ")%20" if to_account is not None else ""
    mention_account = "(%40" + mention_account + ")%20" if mention_account is not None else ""
    hash_tags = "(%23" + hashtag + ")%20" if hashtag is not None else ""

    if words is not None:
        if len(words) == 1:
            words = "(" + str(''.join(words)) + ")%20"
        else:
            words = "(" + str('%20OR%20'.join(words)) + ")%20"
    else:
        words = ""

    if lang is not None:
        lang = 'lang%3A' + lang
    else:
        lang = ""

    until_local = "until%3A" + until_local + "%20"
    since = "since%3A" + since + "%20"

    if display_type == "Latest" or display_type == "latest":
        display_type = "&f=live"
    elif display_type == "Image" or display_type == "image":
        display_type = "&f=image"
    else:
        display_type = ""

    # filter replies 
    if filter_replies == True:
        filter_replies = "%20-filter%3Areplies"
    else:
        filter_replies = ""
    # geo
    # min number of replies
    if minreplies is not None:
        minreplies = "%20min_replies%3A" + str(minreplies)
    else:
        minreplies = ""
    # min number of likes
    if minlikes is not None:
        minlikes = "%20min_faves%3A" + str(minlikes)
    else:
        minlikes = ""
    # min number of retweets
    if minretweets is not None:
        minretweets = "%20min_retweets%3A" + str(minretweets)
    else:
        minretweets = ""

    # proximity
    if proximity == True:
        proximity = "&lf=on"  # at the end
    else:
        proximity = ""

    path = 'https://twitter.com/search?q=' + words + from_account + to_account + mention_account + hash_tags + until_local + since + lang + filter_replies + minreplies + minlikes + minretweets + '&src=typed_query' + display_type + proximity
    driver.get(path)
    return path


def get_last_date_from_csv(path):
    df = pd.read_csv(path)
    return datetime.datetime.strftime(max(pd.to_datetime(df["Timestamp"])), '%Y-%m-%dT%H:%M:%S.000Z')


def log_in(driver,account, wait=4):
    driver.get('https://twitter.com/i/flow/login')
    sleep(random.uniform(wait, wait + 1))
    sleep(random.uniform(wait, wait + 1))
    email_xpath = '//input[@autocomplete="username"]'
    password_xpath = '//input[@autocomplete="current-password"]'
    username_xpath = '//input[@data-testid="ocfEnterTextTextInput"]'

    sleep(random.uniform(wait, wait + 1))

    # enter email
    email_el = driver.find_element("xpath",email_xpath)
    sleep(random.uniform(wait, wait + 1))
    email_el.send_keys(account['email'])
    sleep(random.uniform(wait, wait + 1))
    email_el.send_keys(Keys.RETURN)
    sleep(random.uniform(wait, wait + 1))
    # in case twitter spotted unusual login activity : enter your username
    if check_exists_by_xpath(username_xpath, driver):
        username_el = driver.find_element("xpath",username_xpath)
        sleep(random.uniform(wait, wait + 1))
        username_el.send_keys(account['username'])
        sleep(random.uniform(wait, wait + 1))
        username_el.send_keys(Keys.RETURN)
        sleep(random.uniform(wait, wait + 1))
    # enter password
    password_el = driver.find_element("xpath",password_xpath)
    password_el.send_keys(account['password'])
    sleep(random.uniform(wait, wait + 1))
    password_el.send_keys(Keys.RETURN)
    sleep(random.uniform(wait, wait + 1))


def keep_scroling(driver, data, writer, tweet_ids, scrolling, tweet_parsed, limit, scroll, last_position,
                  save_images=False):
    """ scrolling function for tweets crawling"""

    save_images_dir = "/images"

    if save_images == True:
        if not os.path.exists(save_images_dir):
            os.mkdir(save_images_dir)

    while scrolling and tweet_parsed < limit:
        sleep(random.uniform(0.5, 1.5))
        # get the card of tweets
        page_cards = driver.find_elements("xpath",'//article[@data-testid="tweet"]')  # changed div by article
        for card in page_cards:
            tweet = get_data(card, save_images, save_images_dir)
            if tweet:
                # check if the tweet is unique
                tweet_id = ''.join(tweet[:-2])
                if tweet_id not in tweet_ids:
                    tweet_ids.add(tweet_id)
                    data.append(tweet)
                    last_date = str(tweet[2])
                    print("Tweet made at: " + str(last_date) + " is found.")
                    writer.writerow(tweet)
                    tweet_parsed += 1
                    if tweet_parsed >= limit:
                        break
        scroll_attempt = 0
        while tweet_parsed < limit:
            # check scroll position
            scroll += 1
            print("scroll ", scroll)
            sleep(random.uniform(0.5, 1.5))
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            curr_position = driver.execute_script("return window.pageYOffset;")
            if last_position == curr_position:
                scroll_attempt += 1
                # end of scroll region
                if scroll_attempt >= 2:
                    scrolling = False
                    break
                else:
                    sleep(random.uniform(0.5, 1.5))  # attempt another scroll
            else:
                last_position = curr_position
                break
    return driver, data, writer, tweet_ids, scrolling, tweet_parsed, scroll, last_position


def check_exists_by_xpath(xpath, driver):
    try:
        driver.find_element("xpath",xpath)
    except NoSuchElementException:
        return False
    return True


def dowload_images(urls, save_dir):
    for i, url_v in enumerate(urls):
        for j, url in enumerate(url_v):
            urllib.request.urlretrieve(url, save_dir + '/' + str(i + 1) + '_' + str(j + 1) + ".jpg")


    
 
