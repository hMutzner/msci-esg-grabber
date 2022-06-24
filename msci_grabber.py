import requests
from sys import stderr
from json import dumps
import os.path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.select import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

get_issuer_url = "https://www.msci.com/research-and-insights/esg-ratings-corporate-search-tool?p_p_id=esgratingsprofile&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=searchEsgRatingsProfiles&p_p_cacheability=cacheLevelPage&_esgratingsprofile_keywords={}"
get_info_url = "https://www.msci.com/research-and-insights/esg-ratings-corporate-search-tool/issuer/{}/{}"

companies = None

with open("msci_index", "r") as f:
    companies = f.readlines()

for company in companies:
    if os.path.isfile(company + ".json"):
        print("Found", company, end="")
        continue

    req = requests.get(get_issuer_url.format(company)).json()

    if len(req) == 0:
        print("Skipping")
        continue
    else:
        req = req[0]

    company_page_url = get_info_url.format(req["encodedTitle"], req["url"])

    opts = Options()
    opts.headless = True
    driver = webdriver.Firefox(options=opts)

    driver.get(company_page_url)

    try:
        WebDriverWait(driver, 5).until(lambda d: d.find_element(By.CLASS_NAME, 'highcharts-label'))
    except:
        print("Exception")
        continue

    name = req["title"]
    temp_rise = driver.find_element(By.CLASS_NAME, "implied-temp-rise-value").text[:-2]

    qa = {}
    for e in driver.find_elements(By.CLASS_NAME, "decarbonization-target-row"):
        f = e.text.split("\n")
        qa[" ".join(f[:-1])] = f[-1]

    history_graph = driver.find_element(By.ID, "_esgratingsprofile_esg-rating-history")

    date_labels = history_graph \
        .find_element(By.CLASS_NAME, "highcharts-xaxis-labels") \
        .find_elements(By.XPATH, ".//*")

    rating_labels = history_graph \
        .find_element(By.CLASS_NAME, "highcharts-data-labels") \
        .find_elements(By.CLASS_NAME, "highcharts-label")

    esg = driver.find_element(By.CLASS_NAME, "ratingdata-company-rating") \
        .get_attribute("class").split("esg-rating-circle-")[-1].lower()

    esg_hist = { \
        datetime.strptime(date.text, "%b-%y").strftime("%Y") : rating.text \
        for date, rating in zip(date_labels, rating_labels) \
    }

    def tocat(e):
        return e.find_element(By.XPATH, "./../..") \
                .find_element(By.CLASS_NAME, "comparison-header").text

    cats_with_ratings = {
            e.find_element(By.TAG_NAME, "span").text.lower(): tocat(e).lower()
            for e in driver.find_elements(By.CLASS_NAME, "comparison-value")
    }

    out = { "temp_rise": temp_rise, "qa": qa, "esg": esg, "esg_hist": esg_hist, "cats": cats_with_ratings }

    print(name, out)

    with open("{}.json".format(company), "w") as f:
        f.write(dumps(out))
