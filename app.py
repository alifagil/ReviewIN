import os
import joblib
import numpy as np
import re  # Dipakai untuk metode Regex-based Text Segmentation & Filtering
from flask import Flask, render_template, request, jsonify
try:
    from scraper import scrape_reviews
except Exception as e:
    print(f"Scraper disabled: {e}")

    def scrape_reviews(url):
        return []

app = Flask(__name__)

# --- CONFIG LOAD MODEL MACHINE LEARNING ---
base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, 'model_fraud.pkl')
vectorizer_path = os.path.join(base_dir, 'tfidf_vectorizer.pkl')

try:
    model = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)
    print("✅ MANTAP: Model & Vectorizer berhasil ke-load!")
except Exception as e:
    print(f"❌ ERROR: File .pkl gak ketemu! {e}")

def get_indications(text):
    """Mencari kata kunci yang memiliki pengaruh besar terhadap prediksi BOT berdasarkan koefisien model"""
    feature_names = vectorizer.get_feature_names_out()
    coefs = model.coef_[0]
    words = text.lower().split()
    found_indications = []
    
    for word in words:
        if word in feature_names:
            indices = np.where(feature_names == word)[0]
            if len(indices) > 0:
                index = indices[0]
                if coefs[index] > 1.2: 
                    found_indications.append(word)
    
    return list(set(found_indications))

def clean_and_extract_review_body(chunk_text):
    """
    METODE: Advanced Regex Metadata Stripping
    Membersihkan sisa-sisa teks metadata Amazon yang menempel di awal ulasan
    akibat salin-tempel segaris (single-line paste / berantakan).
    """
    # 1. Hapus teks rating seperti "5.0 out of 5 stars", "4 out of 5 stars", dll.
    cleaned = re.sub(r'\d+(\.\d+)?\s+out\s+of\s+5\s+stars', '', chunk_text, flags=re.IGNORECASE)
    
    # 2. Hapus data lokasi & tanggal (Reviewed in... on Month DD, YYYY)
    cleaned = re.sub(r'Reviewed\s+in\s+.*?\s+on\s+[A-Za-z]+\s+\d+,\s+\d+', '', cleaned, flags=re.IGNORECASE)
    
    # 3. Hapus teks varian produk & metadata transaksi
    cleaned = re.sub(r'Size:\s+\S+', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Color:\s+\S+', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Verified\s+Purchase', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Amazon\s+Vine\s+Customer\s+Review\s+of\s+Free\s+Product.*?\)', '', cleaned, flags=re.IGNORECASE)
    
    # 4. Hapus teks lampiran gambar dan tombol helpful di bagian bawah ulasan
    cleaned = re.sub(r'Customer\s+image', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\d+\s+peop[le]*\s+found\s+this\s+helpful', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'One\s+person\s+found\s+this\s+helpful', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b(helpful|report)\b', '', cleaned, flags=re.IGNORECASE)
    
    # Kembalikan teks komentar murni yang sudah rapi dan bersih dari spasi berlebih
    return " ".join(cleaned.split()).strip()

def split_manual_reviews(text):
    """
    METODE: Pattern-based Text Splitting (Robust Version)
    Memotong teks massal menjadi ulasan terpisah meskipun format barisnya menyatu hancur ke samping.
    """
    # Menggunakan penanda akhir 'Helpful Report' sebagai basis pemotongan utama
    pattern = r'Helpful\s+Report'
    raw_chunks = re.split(pattern, text, flags=re.IGNORECASE)
    
    cleaned_reviews = []
    for chunk in raw_chunks:
        if not chunk.strip():
            continue
            
        # Bersihkan potongan ulasan dari metadata sampah secara menyeluruh
        pure_comment = clean_and_extract_review_body(chunk)
        
        # Validasi: Masukkan ke list jika lolos sensor dan bukan teks kosong / terlalu pendek
        if pure_comment and len(pure_comment) > 10:
            cleaned_reviews.append(pure_comment)
            
    return cleaned_reviews

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    input_type = request.form.get('input_type', 'link')
    input_data = request.form.get('url', '').strip() 
    
    scraped_data = []
    
    # --- LOGIKA SELEKSI INPUT METODE ---
    if input_type == 'link':
        if not input_data or ("amazon" not in input_data.lower() and "a.co" not in input_data.lower()):
            return "⚠️ Bro, masukin link Amazon yang bener ya! (Bisa link dari aplikasi mobile a.co atau web amazon.com)", 400
        print(f"🕵️ Memulai proses scraping live untuk link: {input_data}")
        scraped_data = scrape_reviews(input_data) 
    else:
        if not input_data:
            return "⚠️ Bro, teks ulasannya jangan kosong ya!", 400
        print(f"📝 Menerapkan Advanced Pattern Segmentation & Filtering pada teks manual...")
        scraped_data = split_manual_reviews(input_data)
        print(f"📊 Berhasil mengekstrak {len(scraped_data)} komentar murni untuk diuji.")
    
    results = []
    bot_count = 0

    if isinstance(scraped_data, list) and len(scraped_data) > 0:
        for rev in scraped_data:
            # Transform teks murni yang sudah steril ke TF-IDF
            vec = vectorizer.transform([rev.lower()])
            prediction = model.predict(vec)[0]
            
            indications = []
            if prediction == 1:
                bot_count += 1
                indications = get_indications(rev)
                
            results.append({
                'text': rev,
                'label': 'BOT' if prediction == 1 else 'MANUSIA',
                'indications': ", ".join(indications) if indications else "-"
            })

        percentage = (bot_count / len(scraped_data)) * 100
        human_percentage = 100 - percentage
    else:
        # Fallback jika user memasukkan pola teks yang merusak struktur segmentasi
        percentage = 0
        human_percentage = 100
        results.append({
            'text': "Gagal memproses data. Pastikan teks ulasan yang Anda salin menyertakan struktur pembatas ulasan Amazon (Helpful Report).",
            'label': "ERROR",
            'indications': "-"
        })
    
    return render_template('index.html', 
                           url=input_data, 
                           percentage=round(percentage, 1), 
                           human_percentage=round(human_percentage, 1),
                           results=results,
                           input_type=input_type,
                           total_reviews=len(scraped_data) if isinstance(scraped_data, list) else 0)

if __name__ == '__main__':
    app.run(debug=True)