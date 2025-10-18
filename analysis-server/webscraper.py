import requests
from bs4 import BeautifulSoup
import re


class BaseScraper:
    """Base class that handles fetching and parsing HTML pages."""
    
    def __init__(self, base_url):
        self.base_url = base_url
        self.html = self.get_page(base_url)
        self.soup = self.parse_html(self.html) if self.html else None

    def get_page(self, url):
        """Fetch the HTML content of a URL."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Request failed for {url}: {e}")
            return None

    def parse_html(self, html):
        """Parse HTML into a BeautifulSoup object."""
        return BeautifulSoup(html, "html.parser")


class Article:
    """Data class for storing article details."""
    
    def __init__(self, title, link, text=None):
        self.title = title
        self.link = link
        self.text = text

    def __repr__(self):
        return f"<Article title='{self.title}' link='{self.link}'>"


class BBCBusinessScraper(BaseScraper):
    """Scraper for BBC Business section."""
    
    def __init__(self, base_url="https://www.bbc.co.uk/news/business"):
        super().__init__(base_url)
        self.headlines = []
        self.related_articles = []

    def fetch_headlines(self):
        """Scrape headlines and links from the BBC Business page."""
        html = self.get_page(self.base_url)
        if not html:
            return []
        
        soup = self.parse_html(html)

        # BBC structure (may change; verify selectors)
        headline_elements = soup.find_all("a",class_=re.compile(r"PromoLink"))
        for tag in headline_elements:
            title = tag.get_text(strip=True)
            link = tag.get("href")
            if link and not link.startswith("http"):
                link = f"https://www.bbc.co.uk{link}"
            if title and link:
                self.headlines.append(Article(title, link))
        return self.headlines

    def fetch_article_text(self, article):
        """Fetch the full text from a given article page."""
        html = self.get_page(article.link)
        if not html:
            return None
        
        soup = self.parse_html(html)
        
        # Typical BBC article paragraphs
        paragraphs = soup.select("main p")
        text = " ".join(p.get_text(strip=True) for p in paragraphs)
        article.text = text
        return text
    
    def get_journalist(self,article):
        html = self.get_page(article.link)
        if not html:
            return None
        soup = self.parse_html(html)

        journalist = soup.find("span",class_="ssrcss-vd0pba-TextContributorName epw3ir01")

        if not journalist:
            return -1
        journalist_name = journalist.get_text(strip=True)
        if not journalist_name:
            return -1
        formatted_name = journalist_name.replace(" ", "+")
        url = f"https://www.bbc.co.uk/search?q={formatted_name}&d=NEWS_PS"
        journalist_page = requests.get(url)
        journalist_soup = BeautifulSoup(journalist_page.text,'html.parser')
        last_text = journalist_soup.select_one('ol[role="list"] li:last-child div').get_text(strip=True)
        return (journalist_name,int(last_text))
        

    def get_all_articles(self, limit=None):
        """Fetch all article data including full text (optionally limit count)."""
        if not self.headlines:
            self.fetch_headlines()
        articles = self.headlines[:limit] if limit else self.headlines
        for article in articles:
            self.fetch_article_text(article)
            self.get_journalist(article)
        return articles


class BBCArticleScraper(BaseScraper):
    def get_heading(self):
        # the heading container has an id of 'main-heading'
        # a span inside the container has the text
        heading = self.soup.find("h1", id="main-heading")
        return heading.get_text(strip=True) if heading else None
    
    def get_text_content(self):
        """Fetch the full text from a given article page."""
        # Typical BBC article paragraphs
        paragraphs = self.soup.select("main p")
        text = " ".join(p.get_text(strip=True) for p in paragraphs)
        return text
    
    def get_journalist(self):
        journalist = self.soup.find("span",class_="ssrcss-vd0pba-TextContributorName epw3ir01")
        if not journalist:
            return None
        journalist_name = journalist.get_text(strip=True)
        if not journalist_name:
            return None
        formatted_name = journalist_name.replace(" ", "+")
        url = f"https://www.bbc.co.uk/search?q={formatted_name}&d=NEWS_PS"
        journalist_page = requests.get(url)
        journalist_soup = BeautifulSoup(journalist_page.text, 'html.parser')
        last_text = journalist_soup.select_one('ol[role="list"] li:last-child div').get_text(strip=True)
        return (journalist_name, int(last_text))
    
if __name__ == "__main__":
    scraper = BBCArticleScraper('https://www.bbc.co.uk/news/articles/cq502xl53xqo')
    print(scraper.get_heading())
    print(scraper.get_text_content())
    print(scraper.get_journalist())