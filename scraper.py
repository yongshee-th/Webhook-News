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

def scrape_links(source):
    try:
        response = requests.get(source["url"], headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        
        # หาแท็ก <a> ทั้งหมดที่มี href
        for a in soup.find_all("a", href=True):
            href = a["href"]
            # กรองเอาเฉพาะลิงก์ที่เป็นบทความจริงๆ
            if source["filter"] in href and not href.endswith(source["filter"]):
                # แปลงเป็น Full URL
                full_url = href if href.startswith("http") else f"{source['url'].split('/')[0]}//{source['url'].split('/')[2]}{href}"
                title = a.get_text(strip=True)
                if title and len(title) > 5: # ตัดพวกลิงก์เปล่าๆ หรือปุ่มสั้นๆ ทิ้ง
                    links.append((title, full_url))
        return links
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
        
        # กำหนดสี Embed ตามแหล่งที่มา (Anthropic = สีส้มอ่อน, Claude = สีครีม/เทา)
        color = 14392237 if "Anthropic" in name else 15129532 
        
        # สร้างกล่องข้อความแบบ Embed
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