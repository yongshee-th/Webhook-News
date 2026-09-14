import os
import json
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

WEBHOOK_URL = "https://discord.com/api/webhooks/1549121441721753662/fZgMp6em_sJWaftCBRjupJ8KVO1aTPXjrFm8SWB-izx2TjYL3IZzPx-T2UeLGj1so-DB"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

SOURCES = [
    {"name": "Anthropic News", "url": "https://www.anthropic.com/news", "filter": "/news/"},
    {"name": "Claude Blog", "url": "https://claude.com/blog", "filter": "/blog/"}
]

SEEN_FILE = "seen.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f, indent=4)

def clean_title(title, url):
    if title.lower() in ["read more", "learn more", ""] or len(title) < 5 or len(title) > 80:
        return url.strip("/").split("/")[-1].replace("-", " ").title()
    return title

def analyze_news_with_ai(title, url):
    if not GEMINI_API_KEY:
        return "📌 บทความใหม่", "ไม่ได้ใส่ API Key ของ Gemini ไว้ที่ GitHub Secrets"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        text = " ".join([p.get_text() for p in soup.find_all("p")])[:1500] 

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        วิเคราะห์ข่าวนี้จาก Anthropic/Claude:
        หัวข้อ: {title}
        เนื้อหา: {text}
        
        ให้ตอบกลับมาเป็น JSON format ตามรูปแบบนี้เท่านั้น:
        {{
            "category": "หมวดหมู่ข่าวสั้นๆ พร้อมอีโมจิ (เช่น 🚀 อัปเดตฟีเจอร์, 🔬 งานวิจัย, 📢 ประกาศ, 🏢 ธุรกิจ)",
            "summary": "สรุปเนื้อหาข่าวเป็นภาษาไทยสั้นๆ เข้าใจง่าย ประมาณ 2-3 บรรทัด"
        }}
        """
        
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "", 1).replace("```", "", 1).strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text.replace("```", "", 2).strip()

        data = json.loads(raw_text)
        return data.get("category", "📌 ข่าวทั่วไป"), data.get("summary", "")
    except Exception as e:
        print(f"AI Analysis Failed: {e}")
        return "📌 บทความ", "ดึงเนื้อหาไม่สำเร็จ หรือ AI ขัดข้อง"

def scrape_links(source):
    try:
        response = requests.get(source["url"], headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        link_dict = {}
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if source["filter"] in href and not href.endswith(source["filter"]):
                full_url = href if href.startswith("http") else f"{source['url'].split('/')[0]}//{source['url'].split('/')[2]}{href}"
                heading = a.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                raw_title = heading.get_text(strip=True) if heading else a.get_text(strip=True)
                title = clean_title(raw_title, full_url)
                
                if full_url not in link_dict or (len(link_dict[full_url]) < len(title) and title.lower() != "read more"):
                    link_dict[full_url] = title
                    
        return [(title, link) for link, title in link_dict.items()]
    except Exception as e:
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
        print(f"Processing & AI Analyzing: {title}")
        category, summary = analyze_news_with_ai(title, link)
        
        color = 14392237 if "Anthropic" in name else 15129532 
        msg = {
            "embeds": [
                {
                    "title": f"[{category}] {title}",
                    "description": summary + f"\n\n👉 **[อ่านรายละเอียดเต็มๆ ได้ที่นี่]({link})**",
                    "url": link,
                    "color": color,
                    "author": {
                        "name": f"🤖 ข่าวใหม่จาก {name}"
                    },
                    "footer": {
                        "text": "Summarized by AI • Automated by GitHub Actions"
                    }
                }
            ]
        }
        requests.post(WEBHOOK_URL, json=msg)

    if new_articles:
        save_seen(seen)
    else:
        print("No new articles found.")

if __name__ == "__main__":
    main()
