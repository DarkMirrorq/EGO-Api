from flask import Flask, jsonify, request, Response
import sqlite3
from functools import wraps
import requests
from bs4 import BeautifulSoup
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from chromedriver_py import binary_path

app = Flask(__name__)

def create_users_table():
    conn = sqlite3.connect('kullanicilar.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS kullanicilar
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  password TEXT)''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('kullanicilar.db')
    conn.row_factory = sqlite3.Row
    return conn

def close_db_connection(conn):
    conn.close()

def execute_query(query, args=()):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(query, args)
    conn.commit()
    conn.close()

def fetch_one(query, args=()):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(query, args)
    result = c.fetchone()
    conn.close()
    return result

def register_user(username, password):
    execute_query('INSERT INTO kullanicilar (username, password) VALUES (?, ?)', (username, password))

def check_auth(username, password):
    user = fetch_one('SELECT * FROM kullanicilar WHERE username=? AND password=?', (username, password))
    if user:
        return True
    else:
        return False

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return jsonify({'message': 'Unauthorized access'}), 401
        return f(*args, **kwargs)
    return decorated

def kayipkartlar():
    url = "https://www.ego.gov.tr/tr/kayip/Ankarakart"
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.content, 'html.parser')

    table = soup.find('table', {'id': 'kayipkarttablosu'})
    if not table:
        return []

    rows = table.find_all('tr')
    headers = [header.text for header in rows[0].find_all('th')]
    kayipkartlar = []

    for row in rows[1:]:
        cells = row.find_all('td')
        card_data = {headers[i]: cells[i].text for i in range(len(headers))}
        kayipkartlar.append(card_data)

    return kayipkartlar


def bayiler():
    url = "https://www.ankarakart.com.tr/islem-merkezi"
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.content, 'html.parser')

    table = soup.find('table', {'id': 'satisbayiler'})
    if not table:
        return []

    rows = table.find_all('tr')
    headers = [header.text for header in rows[0].find_all('th')]
    bayiler = []

    for row in rows[1:]:
        cells = row.find_all('td')
        card_data = {headers[i]: cells[i].text for i in range(len(headers))}
        bayiler.append(card_data)

    return bayiler

def otobus_dakika(durak_no, hat_no):
    url = f'https://www.ego.gov.tr/tr/otobusnerede?durak_no={durak_no}&hat_no={hat_no}'
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Headless mod
    service = ChromeService(executable_path=binary_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(url)

    # time.sleep(2)  
    driver.execute_script(f"OtobusNerede({durak_no}, {hat_no})")

    # time.sleep(5)

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

@app.route('/api/kayipkartlar', methods=['GET'])
@requires_auth
def get_kayipkartlar():
    data = kayipkartlar()
    return Response(json.dumps(data, ensure_ascii=False), content_type='application/json; charset=utf-8')


@app.route('/api/bayiler', methods=['GET'])
@requires_auth
def get_bayiler():
    data = bayiler()
    return Response(json.dumps(data, ensure_ascii=False), content_type='application/json; charset=utf-8')


@app.route('/api/otobus_dakika', methods=['GET'])
@requires_auth
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
