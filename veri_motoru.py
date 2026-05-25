import os
import json
import pandas as pd
import requests
from io import StringIO
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yüklüyoruz
load_dotenv()

# Şifreleri güvenli bir şekilde işletim sisteminden çağırıyoruz
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") 

def turkiye_yanginlarini_cek():
    print("🔄 NASA FIRMS uydularından son 24 saatlik veriler çekiliyor...")
    url = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_Global_24h.csv"
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return None
            
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)
        
        # Türkiye coğrafi sınır filtresi
        turkiye_yanginlari = df[
            (df['latitude'] >= 36.0) & (df['latitude'] <= 42.0) &
            (df['longitude'] >= 26.0) & (df['longitude'] <= 45.0)
        ].copy()
        
        return turkiye_yanginlari
    except Exception as e:
        print(f"❌ Veri çekme hatası: {e}")
        return None

def gercek_hava_durumu_al(enlem, boylam):
    """OpenWeatherMap API kullanarak anlık rüzgar ve nem verisi çeker."""
    if OPENWEATHER_API_KEY == "BURAYA_API_ANAHTARINI_YAZ":
        return {"ruzgar_hizi": 15.0, "ruzgar_yonu_derece": 45, "nem": 40}
        
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={enlem}&lon={boylam}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url)
        res = response.json()
        
        if response.status_code == 200 and res.get("cod") == 200:
            print(f"🌍 OpenWeather'dan CANLI veri başarıyla çekildi! Nem: %{res['main']['humidity']}")
            return {
                "ruzgar_hizi": res["wind"]["speed"] * 3.6, # m/s'yi km/s'ye çeviriyoruz
                "ruzgar_yonu_derece": res["wind"].get("deg", 0),
                "nem": res["main"]["humidity"]
            }
        else:
            print(f"⚠️ OpenWeather Sunucu Yanıtı Hatası! HTTP Kodu: {response.status_code} | Detay: {res.get('message')}")
            
    except Exception as e:
        print(f"❌ Hava durumu çekilirken bağlantı hatası oluştu: {e}")
        
    # API'de sorun olursa sistemin kilitlenmemesi için yedek veri
    return {"ruzgar_hizi": 15.0, "ruzgar_yonu_derece": 45, "nem": 40}

def telegram_uyari_gonder(enlem, boylam, sicaklik, nem, ruzgar_hizi, ruzgar_yonu, durum):
    """Aynı nokta için birden fazla Telegram uyarısı gitmesini (spam) engeller."""
    BOT_TOKEN = BOT_TOKEN
    KANAL_KULLANICI_ADI = "@yangin_ihbar_turkiye" 
    
    # 📝 Hafıza Dosyası Adı
    HAFIZA_DOSYASI = "bildirilen_yanginlar.json"
    
    # Uydunun küçük kaymalarını yakalamak için koordinatları ~1.1 km hassasiyete yuvarlıyoruz
    yangin_id = f"{round(enlem, 2)}_{round(boylam, 2)}"
    
    # Hafıza dosyasını yükle
    if os.path.exists(HAFIZA_DOSYASI):
        with open(HAFIZA_DOSYASI, "r") as f:
            try:
                bildirilenler = json.load(f)
            except:
                bildirilenler = []
    else:
        bildirilenler = []
        
    # Eğer bu bölge zaten yakın zamanda bildirildiyse işlemi iptal et (Spam Filtresi)
    if yangin_id in bildirilenler:
        print(f"🤫 {enlem}, {boylam} konumu yakın zamanda zaten bildirilmiş. Tekrar mesaj atılmadı.")
        return

    # Google Haritalar yönlendirme linki
    harita_linki = f"https://www.google.com/maps?q={enlem},{boylam}"
    
    mesaj = f"""
🚨 *ACİL YANGIN/TERMAL ANOMALİ BİLDİRİMİ!* 🚨
----------------------------------------
📊 *SİSTEM DURUMU:* {durum}
📍 *KONUM:* {enlem}, {boylam}
🔥 *UYDU PARLAKLIK ISISI:* {sicaklik}°C

💨 *RÜZGAR:* {ruzgar_yonu} ({round(ruzgar_hizi, 1)} km/s)
💧 *NEM:* %{nem}

🗺️ [Yangın Bölgesini Haritada Gör]({harita_linki})
----------------------------------------
📡 _YangınVar! Uydu Erken Uyarı Sistemi tarafından otomatik üretilmiştir._
"""
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": KANAL_KULLANICI_ADI,
        "text": mesaj,
        "parse_mode": "Markdown"
    }
    
    try:
        res = requests.post(url, json=payload)
        if res.status_code == 200:
            print(f"📢 Telegram kanalına uyarı başarıyla gönderildi! (Konum: {enlem}, {boylam})")
            
            # Gönderim başarılıysa hafızaya kaydet ki bir daha atmasın
            bildirilenler.append(yangin_id)
            with open(HAFIZA_DOSYASI, "w") as f:
                json.dump(bildirilenler, f)
        else:
            print(f"❌ Telegram mesajı gönderilemedi. Hata Kodu: {res.status_code}")
    except Exception as e:
        print(f"❌ Telegram bağlantı hatası: {e}")

def ruzgar_yonu_metin(derece):
    """Derece cinsinden gelen rüzgar yönünü Türkçe denizcilik terimlerine çevirir."""
    if (derece >= 337.5) or (derece < 22.5): return "Kuzey (Yıldız)"
    if (22.5 <= derece < 67.5): return "Kuzeydoğu (Poyraz)"
    if (67.5 <= derece < 112.5): return "Doğu (Gündoğusu)"
    if (112.5 <= derece < 157.5): return "Güneydoğu (Keşişleme)"
    if (157.5 <= derece < 202.5): return "Güney (Kıble)"
    if (202.5 <= derece < 247.5): return "Güneybatı (Lodos)"
    if (247.5 <= derece < 292.5): return "Batı (Günbatısı)"
    if (292.5 <= derece < 337.5): return "Kuzeybatı (Karayel)"
    return "Bilinmiyor"

def risk_skoru_hesapla(uydu_sicakligi, nem, ruzgar_hizi):
    """Gelişmiş meteorolojik erken uyarı algoritması."""
    nem_carpani = 2.0 if nem < 30 else (0.5 if nem > 70 else 1.0)
    ruzgar_carpani = 1.5 if ruzgar_hizi > 20 else 1.0
    ham_skor = uydu_sicakligi * nem_carpani * ruzgar_carpani
    
    if ham_skor > 150: return "YÜKSEK TEHLİKE 🚨"
    if ham_skor > 80: return "ORTA TEHLİKE ⚠️"
    return "DÜŞÜK RİSK 🟢"

if __name__ == "__main__":
    yangin_df = turkiye_yanginlarini_cek()
    
    if yangin_df is not None and not yangin_df.empty:
        print("\n--- Analiz Edilen Canlı Yangın Noktaları ---")
        
        for index, row in yangin_df.head(3).iterrows():
            enlem = row['latitude']
            boylam = row['longitude']
            sicaklik_celcius = round(row['bright_ti4'] - 273.15, 1) 
            
            hava = gercek_hava_durumu_al(enlem, boylam)
            yon_metin = ruzgar_yonu_metin(hava["ruzgar_yonu_derece"])
            durum = risk_skoru_hesapla(sicaklik_celcius, hava["nem"], hava["ruzgar_hizi"])
            
            print(f"\n📍 Nokta #{index} | Konum: {enlem}, {boylam}")
            print(f"📊 SİSTEM DURUMU: {durum}")
            
            # Gerçek Mod: Sadece ORTA veya YÜKSEK risklerde bildirim gönderir
            if "YÜKSEK" in durum or "ORTA" in durum:
                telegram_uyari_gonder(
                    enlem, boylam, sicaklik_celcius, 
                    hava["nem"], hava["ruzgar_hizi"], yon_metin, durum
                )