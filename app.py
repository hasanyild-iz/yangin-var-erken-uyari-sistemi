import streamlit as st
import pandas as pd
import plotly.express as px
from veri_motoru import turkiye_yanginlarini_cek, gercek_hava_durumu_al, ruzgar_yonu_metin, risk_skoru_hesapla

# Sayfa Genişlik Ayarı ve Başlık
st.set_page_config(page_title="YangınVar! Erken Uyarı Sistemi", layout="wide")

st.title("🔥 YangınVar! | Uydu Tabanlı Canlı Erken Uyarı Paneli")
st.markdown("NASA FIRMS uydularından alınan son 24 saatlik anomali verileri ve canlı meteoroloji entegrasyonu.")

# Sol Menü (Sidebar) Kontrolleri
st.sidebar.header("Sistem Ayarları")
filtre_durumu = st.sidebar.multiselect(
    "Risk Seviyesine Göre Filtrele",
    ["YÜKSEK TEHLİKE 🚨", "ORTA TEHLİKE ⚠️", "DÜŞÜK RİSK 🟢"],
    default=["YÜKSEK TEHLİKE 🚨", "ORTA TEHLİKE ⚠️", "DÜŞÜK RİSK 🟢"]
)

# Yenileme Butonu
if st.sidebar.button("Verileri Yenile 🔄"):
    st.rerun()

# Veriyi Çekme Aşaması
with st.spinner("NASA uydularından canlı veriler analiz ediliyor..."):
    yangin_df = turkiye_yanginlarini_cek()

if yangin_df is not None and not yangin_df.empty:
    
    # Tüm noktalar için hava durumu ve risk analizi yapıp listeye ekliyoruz
    analiz_sonuclari = []
    
    # Performans için şimdilik ilk 10 noktayı haritada detaylı analiz edelim
    # (Hava durumu API limitini doldurmamak için)
    for index, row in yangin_df.head(10).iterrows():
        enlem = row['latitude']
        boylam = row['longitude']
        sicaklik = round(row['bright_ti4'] - 273.15, 1)
        
        hava = gercek_hava_durumu_al(enlem, boylam)
        yon = ruzgar_yonu_metin(hava["ruzgar_yonu_derece"])
        durum = risk_skoru_hesapla(sicaklik, hava["nem"], hava["ruzgar_hizi"])

        # 🚨 GERÇEK MOD: Sadece ORTA ve YÜKSEK tehlike durumlarında Telegram'a mesaj gider
        if "YÜKSEK" in durum or "ORTA" in durum: 
            from veri_motoru import telegram_uyari_gonder
            telegram_uyari_gonder(enlem, boylam, sicaklik, hava["nem"], hava["ruzgar_hizi"], yon, durum)
        
        analiz_sonuclari.append({
            "Enlem": enlem,
            "Boylam": boylam,
            "Uydu Sıcaklığı (°C)": sicaklik,
            "Nem (%)": hava["nem"],
            "Rüzgar Hızı (km/s)": round(hava["ruzgar_hizi"], 1),
            "Rüzgar Yönü": yon,
            "Sistem Durumu": durum
        })
        
    analiz_df = pd.DataFrame(analiz_sonuclari)
    
    # Kullanıcının sol menüden seçtiği risk durumuna göre tabloyu filtrele
    analiz_df = analiz_df[analiz_df["Sistem Durumu"].isin(filtre_durumu)]
    
    if not analiz_df.empty:
        # İSTATİSTİKLER (METRICS)
        col1, col2, col3 = st.columns(3)
        col1.metric("Toplam Analiz Edilen Nokta", len(analiz_df))
        col2.metric("Kritik Alarm Sayısı 🚨", len(analiz_df[analiz_df["Sistem Durumu"] == "YÜKSEK TEHLİKE 🚨"]))
        col3.metric("En Yüksek Uydu Sıcaklığı", f"{analiz_df['Uydu Sıcaklığı (°C)'].max()} °C")
        
        st.markdown("---")
        
        # 🗺️ CANLI HARİTA (Plotly Mapbox)
        st.subheader("🌍 Türkiye Canlı Yangın Risk Haritası")
        
        # Harita renk skalası tanımlama
        renk_haritasi = {
            "YÜKSEK TEHLİKE 🚨": "red",
            "ORTA TEHLİKE ⚠️": "orange",
            "DÜŞÜK RİSK 🟢": "green"
        }
        
        fig = px.scatter_mapbox(
            analiz_df, 
            lat="Enlem", 
            lon="Boylam", 
            color="Sistem Durumu",
            color_discrete_map=renk_haritasi,
            size="Uydu Sıcaklığı (°C)",
            hover_name="Sistem Durumu",
            hover_data=["Uydu Sıcaklığı (°C)", "Nem (%)", "Rüzgar Hızı (km/s)", "Rüzgar Yönü"],
            zoom=5, 
            center={"lat": 38.9637, "lon": 35.2433}, # Türkiye Merkezli
            mapbox_style="carto-positron",
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # 📊 VERİ TABLOSU
        st.subheader("📋 Detaylı Koordinat ve Meteoroloji Listesi")
        st.dataframe(analiz_df, use_container_width=True)
        
    else:
        st.info("Seçtiğiniz risk kategorisinde eşleşen anomali bulunamadı.")
else:
    st.error("NASA verileri şu an çekilemiyor veya Türkiye sınırlarında aktif anomali yok.")