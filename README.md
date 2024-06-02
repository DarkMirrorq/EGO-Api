# EGO-Api

Bu apide ego verilerini çekiyoruz tamamen yasal sayfa üzerinden veri alıyoruz. Aşağıdaki endpointleri get request yaparak kullanabilirsiniz. Gerekli paketler requirements.txt'de.


## API Kullanımı

#### Otobüs Dakika Alma
```http
  GET /api/otobus_dakika
```

| Parametre | Tip     | Açıklama                |
| :-------- | :------- | :------------------------- |
| `durak_no` | `string` | **Zorunlu**. Bulunduğunuz Durak. 
| `hat_no` | `string` | **Zorunlu** Sorgulamak İstediğiniz Hat.  


| Auth | Response     | Response Süresi(Ortalama)                |
| :-------- | :------- | :------------------------- |
| `Basic Authentication` | `Json` | 10 Second |

#### EGO'ya Bildirilen Kayıp Kartları Çekme

```http
  GET /api/kayipkartlar
```

| Auth | Response     | Response Süresi(Ortalama)                |
| :-------- | :------- | :------------------------- |
| `Basic Authentication` | `Json` | 1,5 Second |

#### Kart Satış ve Dolum Bayileri Listesi

```http
  GET /api/bayiler
```

| Auth | Response     | Response Süresi(Ortalama)                |
| :-------- | :------- | :------------------------- |
| `Basic Authentication` | `Json` | 700 MS |






  
## Kurulum

Projeyi klonlayın

```bash
  git clone https://github.com/DarkMirrorq/EGO-Api
```

Proje dizinine gidin

```bash
  cd EGO-Api
```

Gerekli paketleri yükleyin

```bash
  pip install -r requirements.txt
```

Programı çalıştırın

```bash
  python main.py
```

  