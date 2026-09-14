import os
from google import genai

title = "Anthropic เปิดตัว Claude 3.5 Sonnet โมเดลฉลาดล้ำ"
text = "Anthropic ประกาศเปิดตัว Claude 3.5 Sonnet ซึ่งมีความเร็วเพิ่มขึ้น 2 เท่า และสามารถเขียนโค้ดได้ดีกว่าเดิม พร้อมให้บริการแล้วตั้งแต่วันนี้"

def test_ai():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ ไม่พบ GEMINI_API_KEY")
        return

    try:
        print("⏳ กำลังเรียก Gemini API...")
        client = genai.Client(api_key=api_key)
        prompt = f"""
        วิเคราะห์ข่าวนี้:
        หัวข้อ: {title}
        เนื้อหา: {text}
        ให้ตอบกลับมาเป็น JSON format ตามรูปแบบนี้:
        {{
            "category": "หมวดหมู่ข่าวสั้นๆ พร้อมอีโมจิ",
            "summary": "สรุปสั้นๆ 1-2 บรรทัด"
        }}
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        print("✅ Gemini ตอบกลับมาว่า:\n", response.text)
    except Exception as e:
        print(f"❌ มี Error เกิดขึ้น: {e}")

if __name__ == "__main__":
    test_ai()
