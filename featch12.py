import requests, csv
from bs4 import BeautifulSoup
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4887.87 Safari/537.36'
}

f = open("before fetching first website.csv", "a", encoding="utf-8", newline="")
writer = csv.writer(f)

def fetch_and_parse(url):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return BeautifulSoup(response.content, 'html.parser')
    else:
        print("Failed to fetch URL: (111)", url)
        exit()

def fetch_report_urls(url):
    report_urls = []
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        # Find report links under <div class="body-post clear">
        div_body_posts = soup.find_all('div', class_='body-post clear')
        for div_body_post in div_body_posts:
            report_links = div_body_post.find_all('a', class_='story-link')
            for link in report_links:
                report_urls.append(link['href'])
    else:
        print("Failed to fetch URL:", url)
    return report_urls

def fetch_article_content(url):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        content_div = soup.find('div', class_='articlebody clear cf')
        if content_div:
            content_elements = content_div.find_all(['p', 'ul'])
            content_text = '\n'.join(element.get_text(strip=True) for element in content_elements)
            return content_text
        else:
            print("Content not found on the page:", url)
            return None
    else:
        print("Failed to fetch URL:", url)
        return None

def fetch_article_titles_and_content_recursively(url, max_articles, current_articles=0, visited=None , i=1):
    if visited is None:
        visited = set()

    if current_articles >= max_articles:
        print(f"{current_articles} articles were fetched")
        return

    if url in visited:
        return

    visited.add(url)
    print("Scraping:", url, f"{i} were fetched!")
    soup = fetch_and_parse(url)
    if soup:
        article_links = fetch_report_urls(url)
        for link in article_links:
            article_content = fetch_article_content(link)
            if article_content:
                writer.writerow([i, link, article_content])
                i = i + 1
                current_articles += 1

                if current_articles >= max_articles:
                    print(f"{current_articles} articles were fetched")
                    return

        next_page_link = soup.find('a', {'class': 'blog-pager-older-link-mobile'})
        if next_page_link:
            next_page_url = next_page_link['href']
            fetch_article_titles_and_content_recursively(next_page_url, max_articles, current_articles, visited, i=i)
        else:
            print('No more pages')
    else:
        print('Failed to fetch URL:', url)

# Example usage
if __name__ == "__main__":
  start_url = 'https://thehackernews.com/'
  fetch_article_titles_and_content_recursively(start_url,max)