import os
import json
import requests
from bs4 import BeautifulSoup

# Webhook URL ของ Discord
WEBHOOK_URL = "https://discord.com/api/webhooks/1549121441721753662/fZgMp6em_sJWaftCBRjupJ8KVO1aTPXjrFm8SWB-izx2TjYL3IZzPx-T2UeLGj1so-DB"

SOURCES = [
    {"name": "Anthropic News", "url": "https://www.anthropic.com/news", "filter": "/news/"},
    {"name": "Claude Blog", "url": "https://claude.com/blog", "filter": "/blog/"}
]

SEEN_FILE = "seen.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r") as f:
                return set(json.load(f))
        except json.JSONDecodeError:
            return set()
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f, indent=4)

def clean_title(title, url):
    # กรณีเจอปุ่ม Read more หรือข้อความว่าง
    if title.lower() in ["read more", "learn more", ""] or len(title) < 5:
        basename = url.strip("/").split("/")[-1]
        return basename.replace("-", " ").title()
    
    # กรณีเว็บ Anthropic ดูดเนื้อหากับวันที่มาติดกันจนยาวเกินไป
    if len(title) > 80:
        basename = url.strip("/").split("/")[-1]
        return basename.replace("-", " ").title()

    return title

def scrape_links(source):
    try:
        response = requests.get(source["url"], headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # ใช้ Dictionary ดักลิงก์ซ้ำในหน้าเดียวกัน
        link_dict = {}
        
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if source["filter"] in href and not href.endswith(source["filter"]):
                full_url = href if href.startswith("http") else f"{source['url'].split('/')[0]}//{source['url'].split('/')[2]}{href}"
                
                # พยายามหา Tag H (Heading) ก่อนเผื่อมีหัวข้อชัดเจน
                heading = a.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                raw_title = heading.get_text(strip=True) if heading else a.get_text(strip=True)
                
                title = clean_title(raw_title, full_url)
                
                # ถ้าเคยดึงลิงก์นี้มาแล้วในลูป ให้เลือกใช้ชื่อข่าวที่ดูดีกว่า
                if full_url in link_dict:
                    if len(link_dict[full_url]) < len(title) and title.lower() != "read more":
                         link_dict[full_url] = title
                else:
                    link_dict[full_url] = title
                    
        return [(title, link) for link, title in link_dict.items()]
    except Exception as e:
        print(f"Error scraping {source['name']}: {e}")
        return []

def main():
    seen = load_seen()
    new_articles = []

    for source in SOURCES:
        print(f"Scraping {source['name']}...")
        articles = scrape_links(source)
        for title, link in articles:
            if link not in seen:
                new_articles.append((source["name"], title, link))
                seen.add(link)

    for name, title, link in new_articles:
        print(f"Found new article: {title}")
        color = 14392237 if "Anthropic" in name else 15129532 
        
        msg = {
            "embeds": [
                {
                    "title": title,
                    "url": link,
                    "color": color,
                    "author": {
                        "name": f"🚀 ข่าวใหม่จาก {name}"
                    },
                    "footer": {
                        "text": "Automated by GitHub Actions"
                    }
                }
            ]
        }
        requests.post(WEBHOOK_URL, json=msg)

    if new_articles:
        save_seen(seen)
        print(f"Successfully saved {len(new_articles)} new articles to seen.json")
    else:
        print("No new articles found.")

if __name__ == "__main__":
    main()