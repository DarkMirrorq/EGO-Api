from flask import Flask, jsonify, request, Response
import sqlite3
from functools import wraps
import requests
from bs4 import BeautifulSoup
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from chromedriver_py import binary_path

app = Flask(__name__)

# Veritabanı bağlantısı ve işlemleri için context manager
class Database:
    def __init__(self, db_name):
        self.db_name = db_name

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_name)
        return self.conn.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.conn.close()

def create_users_table():
    with Database('kullanicilar.db') as c:
        c.execute('''CREATE TABLE IF NOT EXISTS api_usage
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      hourly_limit INTEGER,
                      hourly_usage INTEGER DEFAULT 0,
                      monthly_limit INTEGER,
                      monthly_usage INTEGER DEFAULT 0,
                      last_reset DATETIME DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY (user_id) REFERENCES users (id))''')

def fetch_one(query, params):
    with Database('kullanicilar.db') as c:
        c.execute(query, params)
        return c.fetchone()

def check_auth(username, password):
    user = fetch_one('SELECT * FROM kullanicilar WHERE username=? AND password=?', (username, password))
    return bool(user)

def check_api_limits(user_id):
    result = fetch_one("SELECT hourly_limit, hourly_usage, monthly_limit, monthly_usage FROM api_usage WHERE user_id = ?", (user_id,))
    if not result:
        with Database('kullanicilar.db') as c:
            c.execute("INSERT INTO api_usage (user_id, hourly_limit, monthly_limit) VALUES (?, ?, ?)", (user_id, 100, 1000))
            return True
    else:
        hourly_limit, hourly_usage, monthly_limit, monthly_usage = result
        if hourly_usage + 1 > hourly_limit or monthly_usage + 1 > monthly_limit:
            return False
        else:
            return True

def web_scrape_table(url, table_id):
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table', {'id': table_id})
    if not table:
        return []
    rows = table.find_all('tr')
    headers = [header.text for header in rows[0].find_all('th')]
    data = []
    for row in rows[1:]:
        cells = row.find_all('td')
        card_data = {headers[i]: cells[i].text for i in range(len(headers))}
        data.append(card_data)
    return data

def otobus_dakika(durak_no, hat_no):
    url = f'https://www.ego.gov.tr/tr/otobusnerede?durak_no={durak_no}&hat_no={hat_no}'
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    service = ChromeService(executable_path=binary_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(url)
    driver.execute_script(f"OtobusNerede({durak_no}, {hat_no})")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    table = soup.find('table', {'class': 'list'})
    if not table:
        return []
    headers = [header.text for header in table.find('tr').find_all('th')]
    rows = table.find_all('tr')[1:]
    data = []
    for row in rows:
        cells = row.find_all('td')
        if len(cells) == 0:
            continue
        row_data = {headers[i]: cells[i].text.strip() for i in range(len(cells))}
        additional_info_row = row.find_next_sibling('tr')
        additional_info = additional_info_row.find('td').text.strip() if additional_info_row else None
        if additional_info:
            row_data['Detay'] = additional_info
        data.append(row_data)
    return data

def update_api_usage(user_id):
    with Database('kullanicilar.db') as c:
        c.execute("UPDATE api_usage SET hourly_usage = hourly_usage + 1 WHERE user_id = ?", (user_id,))
        c.execute("UPDATE api_usage SET monthly_usage = monthly_usage + 1 WHERE user_id = ?", (user_id,))
        c.execute("UPDATE api_usage SET monthly_usage = 0, last_reset = CURRENT_TIMESTAMP WHERE user_id = ? AND strftime('%m', last_reset) != strftime('%m', CURRENT_TIMESTAMP)", (user_id,))


def requires_auth_and_limit(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if check_auth(auth.username, auth.password) or not check_api_limits(auth.username):
            return jsonify({'message': 'Unauthorized access or API limit exceeded'}), 401
        update_api_usage(auth.username)
        return f(*args, **kwargs)
    return decorated

@app.route('/api/kayipkartlar', methods=['GET'])
@requires_auth_and_limit
def get_kayipkartlar():
    data = web_scrape_table("https://www.ego.gov.tr/tr/kayip/Ankarakart", "kayipkarttablosu")
    return Response(json.dumps(data, ensure_ascii=False), content_type='application/json; charset=utf-8')

@app.route('/api/bayiler', methods=['GET'])
@requires_auth_and_limit
def get_bayiler():
    data = web_scrape_table("https://www.ankarakart.com.tr/islem-merkezi", "satisbayiler")
    return Response(json.dumps(data, ensure_ascii=False), content_type='application/json; charset=utf-8')

@app.route('/api/otobus_dakika', methods=['GET'])
@requires_auth_and_limit
def get_otobus_dakika():
    durak_no = request.args.get('durak_no')
    hat_no = request.args.get('hat_no')
    if not durak_no or not hat_no:
        return Response(json.dumps({'Hata': 'Durak No ve Hat No gönderilmesi zorunludur.'}, ensure_ascii=False), content_type='application/json; charset=utf-8'), 400
    data = otobus_dakika(durak_no, hat_no)
    if not data:
        return Response(json.dumps({'Mesaj': 'Sefer yok'}, ensure_ascii=False), content_type='application/json; charset=utf-8'), 200
    return Response(json.dumps(data, ensure_ascii=False), content_type='application/json; charset=utf-8')

if __name__ == '__main__':
    create_users_table()
    app.run(debug=True)
