import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go # Daha gelişmiş grafikler için

# --- 1. AYARLAR ---
st.set_page_config(page_title="StokSezgisi AI", layout="wide")
st.title("🔮 StokSezgisi: AI Destekli Talep Tahmini")

# --- 2. VERİ YÜKLEME ---
@st.cache_data
def veri_yukle():
    try:
        df = pd.read_csv('satis_verisi_2024.csv')
        df['Tarih'] = pd.to_datetime(df['Tarih'])
        return df
    except FileNotFoundError:
        return None

df = veri_yukle()

if df is None:
    st.error("Lütfen önce veri üretme kodunu çalıştırın.")
    st.stop()

# --- 3. SEKMELİ YAPI (TABS) ---
# Siteyi iki ana bölüme ayırıyoruz: Mevcut Durum vs Gelecek Tahmini
tab1, tab2 = st.tabs(["📊 Mevcut Durum Raporu", "🚀 Gelecek Tahmini (Forecast)"])

# ==========================================
# SEKME 1: MEVCUT DURUM (Eski Kodlarımız)
# ==========================================
with tab1:
    st.header("Genel Bakış")
    
    # Filtreler (Sadece bu sekme için)
    col_filtre1, col_filtre2 = st.columns(2)
    secilen_urun = col_filtre1.selectbox("Analiz Edilecek Ürün", df['Urun_Adi'].unique())
    
    # Veriyi Süz
    df_urun = df[df['Urun_Adi'] == secilen_urun].copy() # .copy() uyarısı almamak için
    
    # KPI Kartları
    toplam_satis = df_urun['Satis_Adedi'].sum()
    ortalama_satis = df_urun['Satis_Adedi'].mean()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Satış", f"{toplam_satis} Adet")
    c2.metric("Günlük Ortalama", f"{ortalama_satis:.1f} Adet")
    
    # Ham Grafik
    fig_raw = px.line(df_urun, x='Tarih', y='Satis_Adedi', title=f"{secilen_urun} - Günlük Satışlar")
    st.plotly_chart(fig_raw, use_container_width=True)

# ==========================================
# SEKME 2: GELECEK TAHMİNİ (YENİ ÖZELLİK)
# ==========================================
with tab2:
    st.header("📈 Trend Analizi ve Tahmin")
    st.info("Bu modül, 'Hareketli Ortalama' (Moving Average) tekniği ile gürültüyü temizler ve trendi gösterir.")
    
    # Kullanıcıdan Parametre Alalım (İnteraktiflik)
    window_size = st.slider("Hareketli Ortalama Penceresi (Gün)", min_value=3, max_value=30, value=7)
    
    # --- MÜHENDİSLİK HESABI ---
    # Pandas ile Hareketli Ortalama Hesabı (Rolling Window)
    # Bu satır, son 'window_size' kadar günün ortalamasını alır.
    df_urun['Trend'] = df_urun['Satis_Adedi'].rolling(window=window_size).mean()
    
    # Grafik Oluşturma (Plotly Graph Objects ile daha detaylı çizim)
    fig_forecast = go.Figure()
    
    # 1. Gerçek Veriyi Çiz (Silik bir şekilde)
    fig_forecast.add_trace(go.Scatter(
        x=df_urun['Tarih'], 
        y=df_urun['Satis_Adedi'],
        mode='lines',
        name='Gerçek Satışlar',
        line=dict(color='lightgray', width=1) # Gürültü olduğu için silik yapıyoruz
    ))
    
    # 2. Trend Çizgisini Çiz (Belirgin)
    fig_forecast.add_trace(go.Scatter(
        x=df_urun['Tarih'], 
        y=df_urun['Trend'],
        mode='lines',
        name=f'{window_size} Günlük Trend',
        line=dict(color='blue', width=3)
    ))
    
    fig_forecast.update_layout(title=f"{secilen_urun} Satış Trendi Analizi", xaxis_title="Tarih", yaxis_title="Adet")
    st.plotly_chart(fig_forecast, use_container_width=True)
    
    # --- GELECEK TAHMİNİ SİMÜLASYONU ---
    st.subheader("🔮 Gelecek Hafta Tahmini")
    
    # Son hesaplanan trend değeri bizim için en güçlü tahmin verisidir
    son_trend_degeri = df_urun['Trend'].iloc[-1]
    
    if pd.notna(son_trend_degeri): # Eğer değer boş değilse
        gelecek_hafta_tahmini = son_trend_degeri * 7
        st.success(f"Son trendlere göre, önümüzdeki 7 gün içinde **{int(gelecek_hafta_tahmini)} adet** {secilen_urun} satılması bekleniyor.")
        
        # Stok Durumu Kontrolü
        mevcut_stok = st.number_input("Depodaki Mevcut Stok Adediniz:", min_value=0, value=50)
        
        if mevcut_stok < gelecek_hafta_tahmini:
            eksik = int(gelecek_hafta_tahmini - mevcut_stok)
            st.error(f"⚠️ DİKKAT: Stok yetersiz kalabilir! Tahmini talebi karşılamak için **{eksik} adet** daha sipariş vermelisiniz.")
        else:
            st.balloons() # Stok yetiyorsa konfeti patlat
            st.success("✅ Stok seviyesi güvenli. Önümüzdeki haftayı çıkarır.")
            
    else:
        st.warning("Trend hesaplamak için yeterli veri yok. Lütfen gün sayısını azaltın.")
