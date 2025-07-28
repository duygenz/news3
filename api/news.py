from http.server import BaseHTTPRequestHandler
import json
import requests
import xml.etree.ElementTree as ET
from collections import Counter
import re
from urllib.parse import urlparse, parse_qs

# Danh sách các nguồn RSS của bạn
RSS_FEEDS = {
    "vietstock_cophieu": "https://vietstock.vn/830/chung-khoan/co-phieu.rss",
    "cafef": "https://cafef.vn/thi-truong-chung-khoan.rss",
    "vietstock_chuyengia": "https://vietstock.vn/145/chung-khoan/y-kien-chuyen-gia.rss",
    "vietstock_kinhdoanh": "https://vietstock.vn/737/doanh-nghiep/hoat-dong-kinh-doanh.rss",
    "dongduong": "https://vietstock.vn/1328/dong-duong/thi-truong-chung-khoan.rss"
}

def text_to_vector(text):
    """Hàm đơn giản để chuyển văn bản thành vector (Bag-of-Words)."""
    words = re.findall(r'\w+', text.lower())
    # Trả về một dictionary đếm số lần xuất hiện của mỗi từ
    return dict(Counter(words))

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Phân tích URL để lấy query parameter
        query_components = parse_qs(urlparse(self.path).query)
        feed_key = query_components.get("feed", [None])[0]

        # Mặc định trả về lỗi nếu không có feed key hoặc key không hợp lệ
        if not feed_key or feed_key not in RSS_FEEDS:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_data = {"error": "Vui lòng cung cấp một 'feed' hợp lệ trong query string.", "available_feeds": list(RSS_FEEDS.keys())}
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            return

        # Lấy URL từ feed key
        url = RSS_FEEDS[feed_key]
        news_items = []
        
        try:
            # Tải nội dung RSS
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Phân tích XML
            root = ET.fromstring(response.content)

            # Lấy 10 tin mới nhất
            for item in root.findall('.//item')[:10]:
                title = item.find('title').text
                link = item.find('link').text
                
                # Tạo vector từ tiêu đề
                vector = text_to_vector(title)
                
                news_items.append({
                    "title": title,
                    "link": link,
                    "vector": vector
                })

            # Chuẩn bị dữ liệu trả về
            final_response = {
                "feed": feed_key,
                "news": news_items
            }
            status_code = 200

        except Exception as e:
            status_code = 500
            final_response = {"error": str(e)}

        # Gửi phản hồi HTTP
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(final_response, ensure_ascii=False).encode('utf-8'))
