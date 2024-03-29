from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from time import sleep
from tqdm import tqdm
import os
import json
import datetime

# only edit these if you're having problems
delay = 1  # time to wait on each page load before reading the page
driver = webdriver.Safari()  # options are Chrome() Firefox() Safari()

# edit this
START_FROM_BEGINNING = True
DELETE_OLD = False

# don't mess with this stuff
candidate_jsonlist = "../../data/tweets/2014_us_gubernatorial_election_candidates_with_twitter.jsonlist"
candidate_left = "../../data/tweets/handle_left.jsonlist"
twitter_ids_filename = '../../data/tweets/all_tweet_ids.json'
# days = (end - start).days + 1
id_selector = '.time a.tweet-timestamp'
tweet_selector = 'li.js-stream-item'
# user = user.lower()
ids = []


def format_day(date):
    day = '0' + str(date.day) if len(str(date.day)) == 1 else str(date.day)
    month = '0' + str(date.month) if len(str(date.month)) == 1 else str(date.month)
    year = str(date.year)
    return '-'.join([year, month, day])


def form_url(since, until, user):
    p1 = 'https://twitter.com/search?f=tweets&vertical=default&q=from%3A'
    p2 = user + '%20since%3A' + since + '%20until%3A' + until + 'include%3Aretweets&src=typd'
    return p1 + p2


def increment_day(date, i):
    return date + datetime.timedelta(days=i)


if __name__ == "__main__":
    if START_FROM_BEGINNING:
        with open(candidate_jsonlist, 'r') as f:
            candidates = [json.loads(line) for line in f]
        if DELETE_OLD:
            try:
                os.remove(os.path.join(os.getcwd(), twitter_ids_filename))
                os.remove(os.path.join(os.getcwd(), candidate_left))
            except:
                pass
    else:
        with open(candidate_left, 'r') as f:
            candidates = [json.loads(line) for line in f]

    for i, c in tqdm(enumerate(candidates), total=len(candidates)):
        if not c["twitter"]:
            continue

        # edit these three variables
        start = datetime.datetime(2014, 8, 3)  # year, month, day
        end = datetime.datetime(2014, 11, 3)  # year, month, day

        user = c["twitter"]
        user = user.lower()
        ids = []

        for _ in range((end - start).days + 1):
            d1 = format_day(increment_day(start, 0))
            d2 = format_day(increment_day(start, 1))
            url = form_url(d1, d2, user)
            # print(url)
            # print(d1)
            driver.get(url)
            sleep(delay)

            try:
                found_tweets = driver.find_elements_by_css_selector(tweet_selector)
                increment = 10

                while len(found_tweets) >= increment:
                    # print('scrolling down to load more tweets')
                    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                    sleep(delay)
                    found_tweets = driver.find_elements_by_css_selector(tweet_selector)
                    increment += 10

                # print('{} tweets found, {} total'.format(len(found_tweets), len(ids)))

                for tweet in found_tweets:
                    try:
                        id = tweet.find_element_by_css_selector(id_selector).get_attribute('href').split('/')[-1]
                        ids.append(id)
                    except StaleElementReferenceException as e:
                        print('lost element reference', tweet)

            except NoSuchElementException:
                print('no tweets on this day')

            start = increment_day(start, 1)

        try:
            with open(twitter_ids_filename) as f:
                all_ids = ids + json.load(f)
                data_to_write = list(set(all_ids))
                print('tweets found on this scrape: ', len(ids))
                print('total tweet count: ', len(data_to_write))
        except FileNotFoundError:
            with open(twitter_ids_filename, 'w') as f:
                all_ids = ids
                data_to_write = list(set(all_ids))
                print('tweets found on this scrape: ', len(ids))
                print('total tweet count: ', len(data_to_write))

        # save the progress
        with open(candidate_left, 'w') as f:
            for j in candidates[i + 1:]:
                f.write(json.dumps(j))
                f.write("\n")

        with open(twitter_ids_filename, 'w') as outfile:
            json.dump(data_to_write, outfile)

    print('all done here')
    driver.close()
