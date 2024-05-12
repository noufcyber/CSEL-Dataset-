# ------------------------------------ Scrabing https://www.bleepingcomputer.com/ ----------------------------

import requests, re, csv
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4887.87 Safari/537.36'
}
f = open("before fetching second website.csv", "a", encoding="utf-8", newline="")
writer = csv.writer(f)

def fetch_and_parse(url):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return BeautifulSoup(response.content, 'html.parser')
    else:
        print("Failed to fetch URL:", url)
        f.close()
        exit()

def fetch_report_urls(url):
    report_links = set()
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        # Find report links under <ul id="bc-home-news-main-wrap">
        a_tags=soup.find_all('a', href=True)
        for a_tag in a_tags:
            href = a_tag['href']
            if re.match(r'^https:\/\/www\.bleepingcomputer\.com\/news\/\w+\/.+\/$', href):
                report_links.add(href)
            if (len(report_links) == 20):
                return report_links
    else:
        print("Failed to fetch URL:", url)
    return report_links

def fetch_article_content(url):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        article_tag = soup.find('section', class_='bc_main_content')
        if article_tag:
            article_div= soup.find('div', class_='container')
            if article_div:
                article_body = soup.find('div', class_='article_section')
                if article_body:
                    content_elements = article_body.find_all(['p', 'ul'])
                    content_text = '\n'.join(element.get_text(strip=True) for element in content_elements)
                    #print(f"Fetching this report {url}")
                    return delete_last_five_lines(content_text)
                else:
                    print("Content not found on the page:", url)
                    return None
            else:
                print("No <div> clss: container tag found.")
                return None
        else:
            print("No <section> tag found.")
            return None
    else:
        print("Failed to fetch URL:", url)
        return None

def delete_last_five_lines(text):
    lines = text.split('\n')
    if len(lines) > 5:
        return '\n'.join(lines[:-5])
    else:
        return ''

def fetch_article_titles_recursively(url, max_articles=4, current_articles=0, visited=None, c=0):
    if visited is None:
        visited = set()

    if current_articles >= max_articles:
        print(f"{current_articles} were fetched")
        return

    if url in visited:
        return

    visited.add(url)
    print("Scraping:", url)
    soup = fetch_and_parse(url)
    if soup is not None:
        article_links = fetch_report_urls(url)
        for link in article_links:
            article_content = fetch_article_content(link)
            if article_content:
                print(f"Report {c}")
                writer.writerow([c, link, article_content])
                c = c + 1
                current_articles += 1

                if (current_articles >= max_articles):
                    print(f"{current_articles} articles were fetched")
                    return
        print(f"{current_articles} were fetched", "\n")

        # Extract link to the next page
        if current_articles <= max_articles:
            for i in range(2,917):
                next_page_url = f"https://www.bleepingcomputer.com/news/page/{i}/"
                fetch_article_titles_recursively(next_page_url, max_articles, current_articles, visited, c=c)
        else:
            f.close()
            exit()

if __name__ == "__main__":
    start_url = 'https://www.bleepingcomputer.com/news/'
    fetch_article_titles_recursively(start_url)