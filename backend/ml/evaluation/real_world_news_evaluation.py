import csv
import json
import logging
import os
import sys
from pathlib import Path

import requests

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base API URL
API_URL = "http://localhost:8000/api/articles/analyze"

CSV_PATH = Path(__file__).resolve().parent / "real_world_news_evaluation.csv"

# The 20 real-world articles
ARTICLES = [
    # Politik
    {"url": "https://www.cnnindonesia.com/nasional/20240801123456-12-1111111/prabowo-dan-jokowi-bertemu-di-istana-bahas-transisi-pemerintahan", "expected_category": "Politik", "expected_sentiment": "Neutral"},
    {"url": "https://www.detik.com/pemilu/d-1234567/kpu-tetapkan-hasil-rekapitulasi-pemilu-2024-ini-rinciannya", "expected_category": "Politik", "expected_sentiment": "Neutral"},
    {"url": "https://nasional.kompas.com/read/2024/05/20/09000011/dpr-sahkan-revisi-uu-kementerian-negara-jadi-usul-inisiatif", "expected_category": "Politik", "expected_sentiment": "Neutral"},
    # Ekonomi
    {"url": "https://www.cnbcindonesia.com/market/20240722080000-17-555555/ihsg-ditutup-hijau-saham-bank-kakap-jadi-motor-penggerak", "expected_category": "Ekonomi", "expected_sentiment": "Positive"},
    {"url": "https://ekonomi.bisnis.com/read/20240810/9/1789012/pertumbuhan-ekonomi-kuartal-ii-2024-capai-505-persen-bps-ungkap-pendorongnya", "expected_category": "Ekonomi", "expected_sentiment": "Positive"},
    {"url": "https://finance.detik.com/berita-ekonomi-bisnis/d-7489012/rupiah-melemah-ke-rp-16-200-us-ini-kata-gubernur-bi", "expected_category": "Ekonomi", "expected_sentiment": "Negative"},
    {"url": "https://www.antaranews.com/berita/4123456/menteri-keuangan-sebut-inflasi-terjaga-di-kisaran-25-persen", "expected_category": "Ekonomi", "expected_sentiment": "Positive"},
    # Hukum / Kriminal
    {"url": "https://news.detik.com/berita/d-7300000/kpk-tetapkan-bupati-x-sebagai-tersangka-kasus-suap-proyek-jalan", "expected_category": "Hukum", "expected_sentiment": "Negative"},
    {"url": "https://nasional.tempo.co/read/1890000/polisi-tangkap-sindikat-narkoba-jaringan-internasional-sita-100-kg-sabu", "expected_category": "Hukum", "expected_sentiment": "Negative"},
    {"url": "https://www.cnnindonesia.com/nasional/20240615100000-12-1110000/hakim-vonis-bebas-terdakwa-kasus-korupsi-timah-jaksa-ajukan-kasasi", "expected_category": "Hukum", "expected_sentiment": "Neutral"},
    # Teknologi
    {"url": "https://inet.detik.com/consumer/d-7411111/apple-resmi-rilis-ios-18-ini-daftar-iphone-yang-kebagian", "expected_category": "Teknologi", "expected_sentiment": "Positive"},
    {"url": "https://tekno.kompas.com/read/2024/07/20/12000000/openai-rilis-gpt-4o-mini-model-ai-baru-yang-lebih-murah-dan-pintar", "expected_category": "Teknologi", "expected_sentiment": "Positive"},
    {"url": "https://www.cnbcindonesia.com/tech/20240801090000-37-567890/kominfo-blokir-ribuan-situs-judi-online-sepanjang-2024", "expected_category": "Teknologi", "expected_sentiment": "Negative"},
    # Olahraga
    {"url": "https://sport.detik.com/sepakbola/liga-inggris/d-7422222/manchester-city-juara-liga-inggris-4-kali-beruntun-ukir-sejarah", "expected_category": "Olahraga", "expected_sentiment": "Positive"},
    {"url": "https://www.cnnindonesia.com/olahraga/20240805150000-178-1234567/gregoria-mariska-raih-perunggu-olimpiade-paris-2024-cetak-sejarah", "expected_category": "Olahraga", "expected_sentiment": "Positive"},
    {"url": "https://www.antaranews.com/berita/4234567/timnas-indonesia-tumbang-dari-irak-0-2-di-kualifikasi-piala-dunia", "expected_category": "Olahraga", "expected_sentiment": "Negative"},
    # Bencana / Kecelakaan
    {"url": "https://news.detik.com/berita/d-7433333/gempa-m-6-5-guncang-garut-terasa-kuat-hingga-bandung-dan-jakarta", "expected_category": "Bencana", "expected_sentiment": "Negative"},
    {"url": "https://www.cnnindonesia.com/nasional/20240511200000-20-1111111/banjir-bandang-terjang-sumatera-barat-belasan-orang-meninggal-dunia", "expected_category": "Bencana", "expected_sentiment": "Negative"},
    {"url": "https://regional.kompas.com/read/2024/06/10/14000000/kecelakaan-maut-bus-rombongan-siswa-smk-di-subang-11-tewas", "expected_category": "Bencana", "expected_sentiment": "Negative"},
    # Hiburan
    {"url": "https://hot.detik.com/music/d-7444444/konser-taylor-swift-di-singapura-sukses-besar-dihadiri-ribuan-fans", "expected_category": "Hiburan", "expected_sentiment": "Positive"},
]

def run_evaluation():
    results = []
    
    for item in ARTICLES:
        url = item["url"]
        logger.info(f"Evaluating URL: {url}")
        
        try:
            resp = requests.post(API_URL, json={"url": url, "top_keywords": 10}, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if "status" in data and data["status"] == "unsupported_language":
                    logger.warning(f"Unsupported language for {url}")
                    continue
                    
                analysis = data["analysis"]
                
                # Check metrics
                predicted_category = analysis["category"]
                category_conf = analysis["category_confidence"]
                predicted_sentiment = analysis["sentiment"]
                sentiment_conf = analysis["sentiment_confidence"]
                
                # Format keywords for CSV
                keywords_list = [k["keyword"] for k in analysis["keywords"]]
                keywords_str = ", ".join(keywords_list)
                
                # Format entities for CSV
                entities_list = [f"{e['text']} ({e['label']})" for e in analysis["entities"]]
                entities_str = " | ".join(entities_list)
                
                # Basic assessment note
                cat_match = "MATCH" if predicted_category.lower() == item["expected_category"].lower() else "MISMATCH"
                sent_match = "MATCH" if predicted_sentiment.lower() == item["expected_sentiment"].lower() else "MISMATCH"
                notes = f"Cat: {cat_match}, Sent: {sent_match}"
                
                results.append({
                    "url": url,
                    "expected_category": item["expected_category"],
                    "predicted_category": predicted_category,
                    "category_confidence": round(category_conf, 4) if category_conf else 0.0,
                    "expected_sentiment": item["expected_sentiment"],
                    "predicted_sentiment": predicted_sentiment,
                    "sentiment_confidence": round(sentiment_conf, 4) if sentiment_conf else 0.0,
                    "keywords": keywords_str,
                    "entities": entities_str,
                    "notes": notes
                })
                logger.info(f"Success! Cat: {predicted_category}, Sent: {predicted_sentiment}")
            else:
                logger.error(f"Failed to fetch {url}: {resp.status_code} - {resp.text}")
                results.append({
                    "url": url,
                    "expected_category": item["expected_category"],
                    "predicted_category": f"ERROR {resp.status_code}",
                    "category_confidence": 0.0,
                    "expected_sentiment": item["expected_sentiment"],
                    "predicted_sentiment": "ERROR",
                    "sentiment_confidence": 0.0,
                    "keywords": "",
                    "entities": "",
                    "notes": "Failed extraction"
                })
        except Exception as e:
            logger.error(f"Exception for {url}: {e}")
            
    # Write CSV
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["url", "expected_category", "predicted_category", "category_confidence", 
                     "expected_sentiment", "predicted_sentiment", "sentiment_confidence", 
                     "keywords", "entities", "notes"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)
            
    logger.info(f"Wrote evaluation results to {CSV_PATH}")

if __name__ == "__main__":
    run_evaluation()
