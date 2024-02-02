from newutils import init_driver, get_last_date_from_csv, log_search_page, keep_scroling, dowload_images, log_in, get_data, init_driverNew
import csv
import os
import datetime
import argparse
from time import sleep
import random
import pandas as pd
from selenium.webdriver.edge.service import Service
import platform
from selenium.webdriver.common.keys import Keys
# import pathlib
import sys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import urllib


def get_user(driver,acc,path,tweet_ids,writer,data,last_position,scroll,text_value,scrolling=True,tweet_parsed=0,limit=float("inf"),wait=5,save_images=False):
    save_images_dir = "/images"

    if save_images == True:
        if not os.path.exists(save_images_dir):
            os.mkdir(save_images_dir)

    while scrolling and tweet_parsed < limit:
        sleep(random.uniform(0.5, 1.5))
        # get the card of tweets
        sleep(3)
        page_cards = driver.find_elements("xpath",'//article[@data-testid="tweet"]')  # changed div by article
        for card in page_cards:
            tweet= get_data(card, save_images, save_images_dir,text_value=text_value)
            if tweet:
                # check if the tweet is unique
                tweet_id = ''.join(tweet[:-3])
                if tweet_id not in tweet_ids:
                    tweet_ids.add(tweet_id)
                    data.append(tweet)
                    last_date = str(tweet[2])
                    print("Tweet made at: " + str(last_date) + " is found.")
                    print(tweet)
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
            #page_height = driver.execute_script("return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight);")
            # Set the scroll step size
            # Scroll slowly to the bottom of the page
            '''
            for i in range(0, page_height, scroll_step):
                driver.execute_script(f"window.scrollTo(0, {i});")
                sleep(0.1)
            '''
            curr_position = driver.execute_script("return window.pageYOffset;")
            if last_position == curr_position:
                scroll_attempt += 1
                # end of scroll region
                if scroll_attempt >= 3:
                    try:
                        show_ogcensor = driver.find_element("xpath",'//div[@role="button" and @class="css-1rynq56 r-bcqeeo r-qvutc0 r-37j5jr r-q4m81j r-a023e6 r-rjixqe r-b88u0q r-1awozwy r-6koalj r-18u37iz r-16y2uox r-1777fci"]')
                        show_ogcensor.click()
                        sleep(random.uniform(0.5, 1.5)) 
                    except:
                        try:
                            show_more = driver.find_element("xpath",'//div[@role="button" and @class="css-175oi2r r-1777fci r-1pl7oy7 r-13qz1uu r-1loqt21 r-o7ynqc r-6416eg r-1ny4l3l"]')
                            show_more.click()
                            sleep(random.uniform(0.5, 1.5)) 
                            try :
                                show_censor = driver.find_element("xpath",'//div[@role="button" and @class="css-1rynq56 r-bcqeeo r-qvutc0 r-37j5jr r-q4m81j r-a023e6 r-rjixqe r-b88u0q r-1awozwy r-6koalj r-18u37iz r-16y2uox r-1777fci"]')
                                show_censor.click()
                                sleep(random.uniform(0.5, 1.5))
                                break
                            except:
                                sleep(random.uniform(0.5, 1.5))
                        except :
                            print("Cannot find show more replies")
                            scrolling = False
                            break
                else:
                    sleep(random.uniform(0.5, 1.5))  # attempt another scroll
            else:
                last_position = curr_position
                break
    return driver, data, writer, tweet_ids, scrolling, tweet_parsed, scroll, last_position
        
def scrape(words=None, to_account=None, from_account=None, mention_account=None, interval=5, lang=None,
          headless=True, limit=float("inf"), display_type="Top", resume=False, proxy=None, hashtag=None, 
          show_images=False, save_images=False, save_dir="comments", filter_replies=False, proximity=False, minreplies=None, minlikes=None, minretweets=None,account=0):
    """
    scrape data from twitter using requests, starting from <since> until <until>. The program make a search between each <since> and <until_local>
    until it reaches the <until> date if it's given, else it stops at the actual date.

    return:
    data : df containing all tweets scraped with the associated features.
    save a csv file containing all tweets scraped with the associated features.
    """

    # ------------------------- Variables : 
    # header of csv
    header = ['UserScreenName', 'UserName', 'Timestamp', 'Text', 'Embedded_text', 'Emojis', 'Comments', 'Likes', 'Retweets',
                  'Image link', 'Tweet URL','From_Tweet']
    # list that contains all data 
    data = []
    # unique tweet ids
    tweet_ids = set()
    # write mode 
    write_mode = 'w'
    # start scraping from <since> until <until>
    # add the <interval> to <since> to get <until_local> for the first refresh
    #until_local = datetime.datetime.strptime(since, '%Y-%m-%d') + datetime.timedelta(days=interval)
    # if <until>=None, set it to the actual date
    '''
    if until is None:
        until = datetime.date.today().strftime("%Y-%m-%d")
    # set refresh at 0. we refresh the page for each <interval> of time.
    '''
    refresh = 0

    # ------------------------- settings :
    # file path
    if words:
        if type(words) == str : 
            words = words.split("//")
        path = save_dir + "/" + '_'.join(words) + '_' + str(since).split(' ')[0] + '_' + \
               str(until).split(' ')[0] + '.csv'
    elif from_account:
        path = save_dir + "/" + from_account + "/" + from_account + '_' + sys.argv[4] + '_quotes' + '(' + str(sys.argv[3]) + ')' + '.csv'
    elif to_account:
        path = save_dir + "/" + to_account + '_' + str(since).split(' ')[0] + '_' + str(until).split(' ')[
            0] + '.csv'
    elif mention_account:
        path = save_dir + "/" + mention_account + '_' + str(since).split(' ')[0] + '_' + str(until).split(' ')[
            0] + '.csv'
    elif hashtag:
        path = save_dir + "/" + hashtag + '_' + str(since).split(' ')[0] + '_' + str(until).split(' ')[
            0] + '.csv'
    # create the <save_dir>
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    # show images during scraping (for saving purpose)
    if save_images == True:
        show_images = True
    # initiate the driver
    driver = init_driver(headless, proxy, show_images)
    #driver = init_driverNew(headless, proxy, show_images,firefox=True)
    # resume scraping from previous work
    if resume:
        since = str(get_last_date_from_csv(path))[:10]
        write_mode = 'a'

    #------------------------- start scraping : keep searching until until
    # open the file
    with open(path, write_mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_mode == 'w':
            # write the csv header
            writer.writerow(header)
        # log search page for a specific <interval> of time and keep scrolling unltil scrolling stops or reach the <until>
        log_in(driver=driver,account=account) 
        DIR =  os.path.dirname(os.path.abspath(__file__)) + f'/{from_account}_' + sys.argv[4] + '_2018-2023.csv'
        df = pd.read_csv(DIR)[int(sys.argv[5]):]
        for index, row in df.iterrows():
                url_value = row['Tweet URL'] + "/quotes"
                text_value = row['Embedded_text']
                driver.get(url_value)
                sleep(5)
                print("Index :" + str(index))
                last_position = driver.execute_script("return window.pageYOffset;")
                scroll = 0
                driver, data, writer, tweet_ids, scrolling, tweet_parsed, scroll, last_position = get_user(
                    driver=driver,acc=None,path = path,data = data, tweet_ids=tweet_ids,writer = writer,last_position=last_position,scroll=scroll,text_value=text_value)
                    
    data = pd.DataFrame(data, columns = ['UserScreenName', 'UserName', 'Timestamp', 'Text', 'Embedded_text', 'Emojis', 
                              'Comments', 'Likes', 'Retweets','Image link', 'Tweet URL','From_Tweet'])

    # save images
    if save_images==True:
        print("Saving images ...")
        save_images_dir = "images"
        if not os.path.exists(save_images_dir):
            os.makedirs(save_images_dir)

        dowload_images(data["Image link"], save_images_dir)

    # close the web driver
    driver.close()

    return data

if __name__ == '__main__':
    if sys.argv[2] == '0' :
        from_account = '@benandjerrys'
    elif sys.argv[2] == '1' :
        from_account = '@Nike'
    elif sys.argv[2] == '2' :
        from_account = '@patagonia'
    elif sys.argv[2] == '3' :
        from_account = '@hm'
    elif sys.argv[2] == '4' :
        from_account = '@Starbucks'
    elif sys.argv[2] == '5' :
        from_account = '@mcdonalds'
    elif sys.argv[2] == '6' :
        from_account = '@dominos'
    data = scrape(words=None, from_account=from_account, interval=1,
              headless=False, display_type="Top", save_images=False, lang="en",
              resume=False, filter_replies=True, proximity=False,account = sys.argv[1])