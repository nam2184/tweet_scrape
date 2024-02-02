from newutils import init_driver, get_last_date_from_csv, log_search_page, keep_scroling, dowload_images, log_in, get_data, init_driverNew, get_data_comment
import csv
import os
import datetime
from time import sleep
import random
import pandas as pd
import pathlib
import sys

class Scrape(object):
    def __init__(self):
        pass

    def scroll(self,driver,path,tweet_ids,writer,data,last_position,scroll,text_value,scrolling=True,tweet_parsed=0,limit=float("inf"),wait=5,save_images=False,all_links=[],post_url=None):
        save_images_dir = "/images"
        all_links = []
        if save_images == True:
            if not os.path.exists(save_images_dir):
                os.mkdir(save_images_dir)

        while scrolling and tweet_parsed < limit:
            sleep(random.uniform(0.5, 1.5))
            # get the card of tweets
            sleep(3)
            page_cards = driver.find_elements("xpath",'//article[@data-testid="tweet"]')  # changed div by article
            for card in page_cards:
                try :
                    tweet, all_links = get_data_comment(card,all_links,post_url,save_images,save_images_dir,text_value=text_value)
                except :
                    tweet = get_data_comment(card,all_links,post_url,save_images,save_images_dir,text_value=text_value)
                    print("Something missing")
                if tweet:
                    # check if the tweet is unique
                    tweet_id = ''.join(tweet[:-3])
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
                    if scroll_attempt >= 3:
                        try: 
                            show_ogcensor = driver.find_element("xpath",'//div[@role="button" and @class="css-175oi2r r-sdzlij r-1phboty r-rs99b7 r-lrvibr r-j2kj52 r-f727ji r-15ysp7h r-4wgw6l r-ymttw5 r-1loqt21 r-o7ynqc r-6416eg r-1ny4l3l"]')
                            show_ogcensor.click()
                            sleep(random.uniform(0.5, 1.5)) 
                        except:
                            try:
                                show_more = driver.find_element("xpath",'//div[@role="button" and @class="css-175oi2r r-1777fci r-1pl7oy7 r-13qz1uu r-1loqt21 r-o7ynqc r-6416eg r-1ny4l3l"]')
                                show_more.click()
                                sleep(random.uniform(0.5, 1.5)) 
                                try :
                                    show_censor = driver.find_element("xpath",'//div[@role="button" and @class="css-175oi2r r-sdzlij r-1phboty r-rs99b7 r-lrvibr r-j2kj52 r-f727ji r-15ysp7h r-4wgw6l r-ymttw5 r-1loqt21 r-o7ynqc r-6416eg r-1ny4l3l"]')
                                    show_censor.click()
                                    sleep(random.uniform(0.5, 1.5))
                                    break
                                except:
                                    sleep(random.uniform(0.5, 1.5))
                            except :
                                print("Cannot find show more replies")
                                scrolling = False
                                if len(all_links) > 0 :
                                    for link in all_links:
                                        driver.get(link)
                                        sleep(5)
                                        last_position = driver.execute_script("return window.pageYOffset;")
                                        scroll = 0
                                        driver, data, writer, tweet_ids, scrolling, tweet_parsed, scroll, last_position = self.scroll(
                                        driver=driver,path = path,data = data, tweet_ids=tweet_ids,writer = writer,last_position=last_position,scroll=scroll,text_value=text_value,all_links=all_links)
                                    break
                                else:
                                    break
                    else:
                        sleep(random.uniform(0.5, 1.5))  # attempt another scroll
                else:
                    last_position = curr_position
                    break
        return driver, data, writer, tweet_ids, scrolling, tweet_parsed, scroll, last_position
            
    def scrape(self, tweet_type = 'post', since = None, until = None, words=None, to_account=None, from_account=None, mention_account=None, interval=5, lang=None,
            headless=True, limit=float("inf"), resume=False, proxy=None, hashtag=None, display_type="Top",
            show_images=False, save_images=False, save_dir="comments", filter_replies=False, proximity=False, minreplies=None, minlikes=None, minretweets=None,account=None):
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
        if until is None:
            until = datetime.date.today().strftime("%Y-%m-%d")
        # set refresh at 0. we refresh the page for each <interval> of time.
        refresh = 0 

        # ------------------------- settings :
        # file path
        if words:
            if type(words) == str : 
                words = words.split("//")
            path = save_dir + "/" + '_'.join(words) + '_' + str(since).split(' ')[0] + '_' + \
                   str(until).split(' ')[0] + '.csv'
        elif from_account:
            path = f"{save_dir}/{from_account}/{from_account}_{sys.argv[4]}_{tweet_type}({str(sys.argv[3])}).csv"
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
            if type == 'comment':
                DIR =  os.path.dirname(os.path.abspath(__file__)) + f'/{from_account}_{from}-{until}.csv'
                df = pd.read_csv(DIR)[int(sys.argv[5]):int(sys.argv[6])]
                for index, row in df.iterrows():
                        url_value = row['Tweet URL']
                        text_value = row['Embedded_text']
                        all_links = []
                        driver.get(url_value)
                        sleep(5)
                        print(f'Index of {from_account}: {str(index)}')
                        last_position = driver.execute_script("return window.pageYOffset;")
                        scroll = 0
                        driver, data, writer, tweet_ids, scroll, last_position = self.scroll(
                        driver=driver,acc=None,path = path,data = data, tweet_ids=tweet_ids,writer = writer,last_position=last_position,scroll=scroll,text_value=text_value,all_links=all_links,post_url=url_value)
            else :    
                while until_local <= datetime.datetime.strptime(until, '%Y-%m-%d'):
                    # number of scrolls
                    scroll = 0
                    # convert <since> and <until_local> to str
                    if type(since) != str :
                        since = datetime.datetime.strftime(since, '%Y-%m-%d')
                    if type(until_local) != str :
                        until_local = datetime.datetime.strftime(until_local, '%Y-%m-%d')
                    #log_in(driver=driver)
                    # log search page between <since> and <until_local>
                
                    path = log_search_page(driver=driver, words=words, since=since,
                                    until_local=until_local, to_account=to_account,
                                    from_account=from_account, mention_account=mention_account, hashtag=hashtag, lang=lang, 
                                    display_type=display_type, filter_replies=filter_replies, proximity=proximity,
                                    minreplies=minreplies, minlikes=minlikes, minretweets=minretweets)
                    
                    # number of logged pages (refresh each <interval>)
                    refresh += 1
                    # number of days crossed
                    #days_passed = refresh * interval
                    # last position of the page : the purpose for this is to know if we reached the end of the page or not so
                    # that we refresh for another <since> and <until_local>
                    last_position = driver.execute_script("return window.pageYOffset;")
                    # should we keep scrolling ?
                    scrolling = True
                    print("looking for tweets between " + str(since) + " and " + str(until_local) + " ...")
                    print(" path : {}".format(path))
                    # number of tweets parsed
                    tweet_parsed = 0
                    # sleep 
                    sleep(random.uniform(0.5, 1.5))
                    # start scrolling and get tweets
                    driver, data, writer, tweet_ids, scrolling, tweet_parsed, scroll, last_position = \
                        keep_scroling(driver, data, writer, tweet_ids, scrolling, tweet_parsed, limit, scroll, last_position)

                    # keep updating <start date> and <end date> for every search
                    if type(since) == str:
                        since = datetime.datetime.strptime(since, '%Y-%m-%d') + datetime.timedelta(days=interval)
                    else:
                        since = since + datetime.timedelta(days=interval)
                    if type(since) != str:
                        until_local = datetime.datetime.strptime(until_local, '%Y-%m-%d') + datetime.timedelta(days=interval)
                    else:
                        until_local = until_local + datetime.timedelta(days=interval)
         
        data = pd.DataFrame(data, columns = ['From_Tweet', 'UserScreenName', 'UserName', 'Timestamp', 'Text', 'Embedded_text', 'Emojis', 'Comments', 'Likes', 'Retweets','Image link', 'Tweet URL','From_Tweet'])

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


