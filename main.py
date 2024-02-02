import argparse
from .src.scrape import Scrape
from dotenv import load_dotenv
import os

def main():
    parser = argparse.ArgumentParser(description='Your script description')    
    # Add flag arguments
    parser.add_argument('-t', '--type', action='store_true', help='Type of post')
    parser.add_argument('-u', '--until', action='store_true', help='Until date')
    parser.add_argument('-f', '--since', action='store_true', help='From date')
    parser.add_argument('-ua', '--until_account', action='store_true', help='Until account')
    parser.add_argument('-a', '--from_account', action='store_true', help='From account')
    parser.add_argument('-w', '--words', action='store_true', help='Word filter')
     
    args = parser.parse_args()
    
    #Specify account details from env
    load_dotenv()
    account =  {'username' : os.getenv('USERNAME'), 'password' : os.getenv('PASSWORD'), 'email' : os.getenv('EMAIL')}
    
    # Access parsed arguments using dot notation
    if args.flag:
        print('Flag is set')
    session = Scrape()
    data = session.scrape(tweet_type = args.type, words= args.words, from_account= args.from_account, interval=1,
              headless=False, save_images=False, lang="en",
              resume=False, filter_replies=True, proximity=False,account = account)

if __name__ == '__main__':
    main()

