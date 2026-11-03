"""
EGO-Api - Ankara EGO Genel Müdürlüğü Otobüs ve Ulaşım API Servisi
Tersine mühendislik ile resmi mobil servisler üzerinden yüksek hızlı REST API.
"""

from functools import wraps
import json
import os
import sqlite3
from flask import Flask, Response, jsonify, request
import requests

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

EGO_BASE_URL = "https://egocptsrvand.ego.gov.tr"
TIMEOUT = 8

# Kimlik doğrulama ayarı: Varsayılan olarak kapalıdır (False).
# Ortam değişkeni REQUIRE_AUTH=true yapılarak aktif edilebilir.
AUTH_REQUIRED = os.environ.get("REQUIRE_AUTH", "false").lower() in ("true", "1")
DB_NAME = "kullanicilar.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS kullanicilar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )"""
    )
    conn.commit()
    conn.close()


def check_auth(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT id FROM kullanicilar WHERE username=? AND password=?",
        (username, password),
    )
    user = c.fetchone()
    conn.close()
    return user is not None


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not AUTH_REQUIRED:
            return f(*args, **kwargs)

        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return (
                jsonify(
                    {"hata": "Yetkisiz erişim. Geçerli Basic Auth bilgileri gereklidir."}
                ),
                401,
            )
        return f(*args, **kwargs)

    return decorated


def make_response(data, status=200):
    return Response(
        json.dumps(data, ensure_ascii=False),
        status=status,
        content_type="application/json; charset=utf-8",
    )


def ego_request(path, params=None):
    url = f"{EGO_BASE_URL}{path}"
    headers = {
        "User-Agent": "okhttp/4.9.2",
        "Accept": "application/json",
    }
    try:
        res = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.Timeout:
        return {"hata": "EGO sunucu yanıt zaman aşımına uğradı."}
    except requests.exceptions.RequestException as e:
        return {"hata": f"EGO servisine bağlanırken bir hata oluştu: {str(e)}"}
    except json.JSONDecodeError:
        return {"hata": "EGO servisinden geçersiz yanıt alındı."}


@app.route("/", methods=["GET"])
def index():
    return make_response(
        {
            "servis": "EGO REST API",
            "durum": "aktif",
            "surum": "2.0.0",
            "dokumantasyon": "https://github.com/DarkMirrorq/EGO-Api",
            "endpointler": {
                "otobus_dakika": "/api/otobus_dakika?durak_no=10001[&hat_no=415]",
                "durak_hatlar": "/api/durak_hatlar?durak_no=10001",
                "hat_ara": "/api/hat_ara?hat_no=185",
                "hat_duraklar": "/api/hat_duraklar?hat_kod=185",
                "bayiler": "/api/bayiler",
                "duyurular": "/api/duyurular",
                "bakiye": "/api/bakiye?kart_no=12345678901",
            },
        }
    )


@app.route("/api/otobus_dakika", methods=["GET"])
@requires_auth
def get_otobus_dakika():
    """Belirtilen duraktaki otobüs varış sürelerini getirir."""
    durak_no = request.args.get("durak_no")
    hat_no = request.args.get("hat_no")

    if not durak_no:
        return make_response(
            {"hata": "'durak_no' parametresi zorunludur."}, status=400
        )

    data = ego_request(f"/hibrit/srv.asp?&LAN=tr&FNC=Otobusler&DURAK={durak_no}")

    if isinstance(data, dict) and "hata" in data:
        return make_response(data, status=502)

    if not isinstance(data, list):
        return make_response([], status=200)

    # İsteğe bağlı hat_no filtrelemesi
    if hat_no:
        hat_str = str(hat_no).strip()
        filtered = [
            bus
            for bus in data
            if str(bus.get("hat_no", "")).strip() == hat_str
            or str(bus.get("hat_kod", "")).strip() == hat_str
        ]
        if not filtered:
            return make_response(
                {"mesaj": f"{hat_no} numaralı hat için yaklaşan sefer bulunamadı."},
                status=200,
            )
        return make_response(filtered)

    return make_response(data)


@app.route("/api/durak_hatlar", methods=["GET"])
@requires_auth
def get_durak_hatlar():
    """Belirtilen duraktan geçen tüm hatların listesini döner."""
    durak_no = request.args.get("durak_no")
    if not durak_no:
        return make_response(
            {"hata": "'durak_no' parametresi zorunludur."}, status=400
        )

    data = ego_request(f"/hibrit/action.asp?FNC=DuraktanGecenHatlar&KOD={durak_no}")
    return make_response(data)


@app.route("/api/hat_ara", methods=["GET"])
@requires_auth
def get_hat_ara():
    """Hat numarasına veya adına göre arama yapar."""
    hat_no = request.args.get("hat_no") or request.args.get("query")
    if not hat_no:
        return make_response({"hata": "'hat_no' parametresi zorunludur."}, status=400)

    data = ego_request(f"/hibrit/action.asp?FNC=HatAra&QUERY={hat_no}")
    return make_response(data)


@app.route("/api/hat_duraklar", methods=["GET"])
@requires_auth
def get_hat_duraklar():
    """Bir hattın güzergahındaki tüm durakları döner."""
    hat_kod = request.args.get("hat_kod") or request.args.get("hat_no")
    if not hat_kod:
        return make_response(
            {"hata": "'hat_kod' parametresi zorunludur."}, status=400
        )

    data = ego_request(f"/hibrit/action.asp?FNC=HatDuraklar&KOD={hat_kod}")
    return make_response(data)


@app.route("/api/bayiler", methods=["GET"])
@requires_auth
def get_bayiler():
    """Tüm Ankarakart bayilerini ve koordinatlarını listeler."""
    data = ego_request("/hibrit/action.asp?FNC=AnkaraKartBayiler")
    return make_response(data)


@app.route("/api/duyurular", methods=["GET"])
@requires_auth
def get_duyurular():
    """EGO resmi duyuru ve haber akışını döner."""
    data = ego_request("/hibrit/action.asp?FNC=Duyurular")
    return make_response(data)


@app.route("/api/bakiye", methods=["GET"])
@requires_auth
def get_bakiye():
    """Ankarakart bakiye sorgulama."""
    kart_no = request.args.get("kart_no")
    if not kart_no:
        return make_response({"hata": "'kart_no' parametresi zorunludur."}, status=400)

    data = ego_request(f"/hibrit/action.asp?FNC=AnkaraKartBakiye&KART={kart_no}")
    return make_response(data)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
