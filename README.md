# 🚌 EGO-Api (v2.0)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-REST_API-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/Response_Time-~150ms-brightgreen?style=for-the-badge" alt="Speed">
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License">
</p>

Ankara EGO Genel Müdürlüğü toplu taşıma verilerini (otobüs varış süreleri, duraktan geçen hatlar, hat güzergahları, Ankarakart bayileri, duyurular vb.) sunan yüksek hızlı, modern REST API.

> [!NOTE]
> **v2.0 Güncellemesi:** Selenium / Chrome web kazıma bağımlılıkları tamamen kaldırılmış, doğrudan resmi mobil uç noktalarına (REST JSON) geçilmiştir. Yanıt süreleri **~15 saniyeden ~150 milisaniyeye** düşürülmüş, bellek tüketimi 10 kat azaltılmıştır.

---

## ⚡ Özellikler

- **Yüksek Hız:** Web kazıma ve tarayıcı simülasyonu yok. Doğrudan EGO mobil JSON servislerine erişir (~150ms).
- **Hafif Bağımlılık:** Sadece `Flask` ve `requests`.
- **Durağa Yaklaşan Otobüsler:** Belirli bir duraktaki tüm araçları veya istenilen hatta ait araçların dakika cinsinden kalan süresi.
- **Ankarakart Bayi Ağı:** Ankara genelindeki tüm bakiye dolum ve satış noktaları (enlem/boylam koordinatları ve açık adresleri ile).
- **Hat & Durak Sorguları:** Bir duraktan geçen hatlar, hat arama ve güzergah üzerindeki durak listesi.
- **Duyurular & Kart Bakiye:** EGO'nun anlık sefer değişiklik duyuruları ve Ankarakart bakiye sorgusu.
- **İsteğe Bağlı Yetkilendirme:** İsteğe göre Basic Auth (SQLite) desteği veya doğrudan açık kullanım.

---

## 🚀 Hızlı Başlangıç

### 1. Kurulum

```bash
git clone https://github.com/DarkMirrorq/EGO-Api.git
cd EGO-Api
pip install -r requirements.txt
```

### 2. Çalıştırma

```bash
python main.py
```
Servis varsayılan olarak `http://localhost:5000` portunda ayağa kalkar.

> [!TIP]
> Basic Auth yetkilendirmesini aktif etmek isterseniz:
> ```bash
> export REQUIRE_AUTH=true
> python main.py
> ```

---

## 📡 API Uç Noktaları

### 1. Durağa Yaklaşan Otobüsler (Dakika Bilgisi)
Belirtilen durağa yaklaşan araçların hat numarası, kalan süresi ve araç numarasını getirir.

```http
GET /api/otobus_dakika?durak_no=10001
GET /api/otobus_dakika?durak_no=10001&hat_no=415
```

| Parametre | Tip | Zorunlu mu? | Açıklama |
| :--- | :--- | :--- | :--- |
| `durak_no` | `string` | **Evet** | 5 haneli durak kodu (Örn: `10001`) |
| `hat_no` | `string` | Hayır | Belirli bir hatta göre filtrelemek için (Örn: `415`) |

**Örnek Yanıt:**
```json
[
  {
    "arac_no": "19-158",
    "sure": "4",
    "hat_kod": "415",
    "hat_no": "415",
    "hat_kisa_kod": "YESILTEPE-SIHHIYE-15 TEMMUZ KIZILAY MILLI IRADE MEYDANI",
    "aciklama": "Araç Durağa Yaklaşıyor"
  }
]
```

---

### 2. Duraktan Geçen Hatlar
Bir duraktan geçen tüm otobüs hatlarını listeler.

```http
GET /api/durak_hatlar?durak_no=10001
```

---

### 3. Hat Arama
Hat numarası veya adına göre hat bilgilerini sorgular.

```http
GET /api/hat_ara?hat_no=185
```

---

### 4. Hattın Durakları
Belirli bir hattın gidiş veya dönüş istikametindeki tüm durak listesini döner.

```http
GET /api/hat_duraklar?hat_kod=185
```

---

### 5. Ankarakart Bayileri & Dolum Noktaları
Ankara genelindeki tüm fiziksel satış ve dolum noktalarının GPS koordinatlarını ve adreslerini listeler.

```http
GET /api/bayiler
```

**Örnek Yanıt:**
```json
[
  {
    "id": "1",
    "ad": "KIZILAY METRO İSTASYONU",
    "lat": "39.92083",
    "lng": "32.85417",
    "adres": "Kızılay Metro İstasyonu İçi Çankaya/ANKARA"
  }
]
```

---

### 6. EGO Resmi Duyuruları
EGO Genel Müdürlüğü tarafından yayımlanan güncel duyuruları ve güzergah değişikliklerini çeker.

```http
GET /api/duyurular
```

---

### 7. Ankarakart Bakiye Sorgulama
Ankarakart numaranızı girerek mevcut bakiyeyi sorgular.

```http
GET /api/bakiye?kart_no=12345678901
```

---

## 📊 Karşılaştırma (v1.0 vs v2.0)

| Metrik | v1.0 (Selenium Scraping) | v2.0 (Native REST) | Fark |
| :--- | :--- | :--- | :--- |
| **Ortalama Yanıt Süresi** | ~12 - 15 saniye | **~150 ms** | ⚡ **100x daha hızlı** |
| **RAM Tüketimi** | ~500 MB (Headless Chrome) | **~30 MB** | 🚀 **%94 tasarruf** |
| **Kararlılık** | ChromeDriver sürüm hataları | Standart HTTP/JSON | 🛡️ **Sıfır çökme** |
| **Kurulum Zorluğu** | Chrome & Driver bağımlılığı | Sadece `pip install` | 📦 **Hafif ve taşınabilir** |

---

## 📜 Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır. Veriler Ankara Büyükşehir Belediyesi EGO Genel Müdürlüğü açık altyapısından sağlanmaktadır.
