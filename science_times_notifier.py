
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import os
import time

# --- 설정이 필요한 변수들 ---

# 1. 이메일(SMTP) 서버 정보 (사용하는 이메일 서비스에 맞게 수정)
# 예: Gmail -> smtp.gmail.com, Naver -> smtp.naver.com
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# 2. 보내는 사람 이메일 계정 정보
# 보안을 위해 앱 비밀번호 사용을 강력히 권장합니다.
# Gmail 앱 비밀번호 생성: https://support.google.com/accounts/answer/185833
# Naver 앱 비밀번호 생성: https://help.naver.com/support/contents/supportContents.help?serviceNo=2342&categoryNo=2289
SENDER_EMAIL = "dlehgus1687@mju.ac.kr"  # 보내는 사람 이메일 주소
SENDER_PASSWORD = "앱 비밀번호 입력"    # 보내는 사람 이메일 앱 비밀번호

# 3. 받는 사람 이메일 주소
RECIPIENT_EMAIL = "dlehgus1687@mju.ac.kr"

# --- 스크립트 주요 로직 (수정 필요 없음) ---

# 사이언스타임즈 카테고리 URL (생명과학/의학)
CATEGORY_URLS = {
    "생명과학/의학": "https://www.sciencetimes.co.kr/nscvrg/list/menu/251?searchCategory=223"
}

# 확인한 기사 링크를 저장할 파일
PROCESSED_ARTICLES_FILE = "processed_articles.txt"

def get_processed_articles():
    """이미 처리한 기사 링크 목록을 파일에서 불러옵니다."""
    if not os.path.exists(PROCESSED_ARTICLES_FILE):
        return set()
    with open(PROCESSED_ARTICLES_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)

def save_processed_article(article_link):
    """처리한 기사 링크를 파일에 저장합니다."""
    with open(PROCESSED_ARTICLES_FILE, "a", encoding="utf-8") as f:
        f.write(article_link + "\n")

def send_email(subject, body):
    """이메일을 발송합니다."""
    try:
        msg = MIMEText(body, "html", "utf-8")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECIPIENT_EMAIL

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # TLS 보안 연결 시작
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        server.quit()
        print(f"성공적으로 이메일을 발송했습니다: {subject}")
    except Exception as e:
        print(f"이메일 발송 중 오류가 발생했습니다: {e}")

def check_new_articles():
    """새로운 기사를 확인하고 이메일을 보냅니다."""
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - 새로운 기사 확인 시작...")
    processed_articles = get_processed_articles()
    
    for category_name, url in CATEGORY_URLS.items():
        try:
            response = requests.get(url)
            response.raise_for_status()  # HTTP 오류가 발생하면 예외를 발생시킴
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 기사 목록 선택 (웹사이트 구조에 따라 변경될 수 있음)
            articles = soup.select("div.nc_word")
            
            if not articles:
                print(f"'{category_name}' 카테고리에서 기사 목록을 찾을 수 없습니다. 사이트 구조가 변경되었을 수 있습니다.")
                continue

            for article_div in articles:
                link_tag = article_div.select_one("div.sub_txt a")
                title_tag = link_tag.select_one("b") if link_tag else None

                if not link_tag or not title_tag or not link_tag.has_attr('href'):
                    continue

                title = title_tag.get_text(strip=True)
                link = "https://www.sciencetimes.co.kr" + link_tag['href']

                if link not in processed_articles:
                    print(f"새 기사 발견: {title}")
                    
                    # 이메일 내용 구성
                    email_subject = f"[사이언스타임즈] 새로운 {category_name} 기사: {title}"
                    email_body = f"""
                    <html>
                    <body>
                        <h2>새로운 사이언스타임즈 기사가 업데이트되었습니다.</h2>
                        <p><strong>카테고리:</strong> {category_name}</p>
                        <p><strong>제목:</strong> {title}</p>
                        <p><strong>링크:</strong> <a href="{link}">{link}</a></p>
                    </body>
                    </html>
                    """
                    
                    send_email(email_subject, email_body)
                    save_processed_article(link)
                    processed_articles.add(link) # 메모리에도 추가하여 중복 발송 방지

        except requests.exceptions.RequestException as e:
            print(f"'{category_name}' 카테고리 페이지를 불러오는 중 오류 발생: {e}")
        except Exception as e:
            print(f"알 수 없는 오류 발생: {e}")

if __name__ == "__main__":
    check_new_articles()
