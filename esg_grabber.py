import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
import csv
from sys import stdout

ratings_url = "https://www.sustainalytics.com/sustapi/companyratings/getcompanyratings"
company_page_url = "https://www.sustainalytics.com/esg-rating"

ratings_payload = {
    "industry": "Textiles & Apparel",
    "rating": "",
    "filter": "",
    "page": 1,
    "pageSize": 160,
    "resourcePackage": "Sustainalytics"
}

ratings_req = requests.post(ratings_url, ratings_payload)
soup = BeautifulSoup(ratings_req.text, 'html.parser')

out = []

for company in soup.find_all('div', class_="company-row"):
    hdr = company.find("div", class_="w-50")

    name = hdr.a.string

    ticker = hdr.small.string.split(":")

    if len(ticker) == 1:
        ticker_exchange, ticker_num = "", ""
    else:
        ticker_exchange, ticker_num = ticker[0], ticker[1]

    url = hdr.a.attrs["data-href"]

    esg = float(company.find("div", class_="company-score").div.div.string)

    company_page_html = requests.get(company_page_url + url).text
    company_soup = BeautifulSoup(company_page_html, "html.parser")

    update_time = company_soup.find("div", class_="last-update").div.strong.string
    update_time = datetime.strptime(update_time, "%b %d, %Y").date()

    if update_time <= date(2021, 12, 31):
        out.append({"name": name, "ticker_exchange": ticker_exchange,
            "ticker_num": ticker_num, "esg": esg, "date": update_time})

hdrs = ["name", "ticker_exchange", "ticker_num", "esg", "date"]
writer = csv.DictWriter(stdout, fieldnames = hdrs)
writer.writerows(out)
