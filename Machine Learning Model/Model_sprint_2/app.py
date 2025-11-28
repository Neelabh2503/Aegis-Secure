import os
import re
import json
import time
import sys
import asyncio
import socket
import random
import logging
import warnings
import unicodedata
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse

# Third-party imports
import httpx
import uvicorn
import joblib
import torch
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import AsyncGroq, RateLimitError, APIError
from dotenv import load_dotenv
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from playwright.async_api import async_playwright

# Local imports
import config
from models import get_ml_models, get_dl_models, FinetunedBERT
from feature_extraction import process_row

load_dotenv()
sys.path.append(os.path.join(config.BASE_DIR, 'Message_model'))

# Attempt to import the local semantic model
try:
    from predict import PhishingPredictor
except ImportError:
    PhishingPredictor = None

# --- CONFIGURATION & LOGGING ---

# Configure Structured Logging (Standard Python Logging)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PhishingAPI")

MAX_INPUT_CHARS = 4000
MAX_CONCURRENT_REQUESTS = 5
# CRITICAL FIX: Reduced from 1000 to 15 to prevent self-DoS and API bans
MAX_URLS_TO_ANALYZE = 15
LLM_MAX_RETRIES = 3

app = FastAPI(
    title="Phishing Detection API (Robust Ensemble)",
    description="Multilingual phishing detection using Weighted Ensemble (ML/DL) + LLM Semantic Analysis + Live Scraping",
    version="2.6.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

request_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

# --- DATA MODELS ---

class MessageInput(BaseModel):
    sender: Optional[str] = ""
    subject: Optional[str] = ""
    text: Optional[str] = ""
    metadata: Optional[Dict] = {}

class PredictionResponse(BaseModel):
    confidence: float
    reasoning: str
    highlighted_text: str
    final_decision: str
    suggestion: str

# --- UTILITIES ---

class SmartAPIKeyRotator:
    def __init__(self):
        keys_str = os.environ.get('GROQ_API_KEYS', '')
        self.keys = [k.strip() for k in keys_str.split(',') if k.strip()]
        if not self.keys:
            single_key = os.environ.get('GROQ_API_KEY')
            if single_key:
                self.keys = [single_key]
        
        if not self.keys:
            logger.critical("CRITICAL: No GROQ_API_KEYS found in environment variables!")
        else:
            logger.info(f"API Key Rotator initialized with {len(self.keys)} keys.")
            
        self.clients = [AsyncGroq(api_key=k) for k in self.keys]
        self.num_keys = len(self.clients)
        self.current_index = 0

    def get_client_and_rotate(self):
        if not self.clients:
            return None
        client = self.clients[self.current_index]
        self.current_index = (self.current_index + 1) % self.num_keys
        return client

# Global Model Placeholders
ml_models = {}
dl_models = {}
bert_model = None
semantic_model = None
key_rotator: Optional[SmartAPIKeyRotator] = None
# Simple in-memory cache for IP lookups
ip_cache = {}

def clean_and_parse_json(text: str) -> Dict:
    """
    Robustly extracts JSON from text, handling markdown blocks and conversational filler.
    Fixes Error 400 issues.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Remove Markdown Code Blocks
    text = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)

    # Attempt to find the first '{' and last '}'
    try:
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            json_str = text[start:end+1]
            return json.loads(json_str)
    except Exception:
        pass
    
    logger.error(f"Failed to parse JSON from LLM response: {text[:100]}...")
    return {}

class EnsembleScorer:
    WEIGHTS = {
        'ml': 0.30,
        'dl': 0.20,
        'bert': 0.20,
        'semantic': 0.10,
        'network': 0.20
    }
    
    @staticmethod
    def calculate_technical_score(predictions: Dict, network_data: List[Dict], urls: List[str]) -> Dict:
        score_accum = 0.0
        weight_accum = 0.0
        details = []
        
        # ML Scores
        ml_scores = [p['raw_score'] for k, p in predictions.items() if k in ['logistic', 'svm', 'xgboost']]
        if ml_scores:
            avg_ml = np.mean(ml_scores)
            score_accum += avg_ml * EnsembleScorer.WEIGHTS['ml'] * 100
            weight_accum += EnsembleScorer.WEIGHTS['ml']
            details.append(f"ML Consensus: {avg_ml:.2f}")

        # DL Scores
        dl_scores = [p['raw_score'] for k, p in predictions.items() if k in ['attention_blstm', 'rcnn']]
        if dl_scores:
            avg_dl = np.mean(dl_scores)
            score_accum += avg_dl * EnsembleScorer.WEIGHTS['dl'] * 100
            weight_accum += EnsembleScorer.WEIGHTS['dl']
            details.append(f"DL Consensus: {avg_dl:.2f}")

        # BERT Score
        if 'bert' in predictions:
            bert_s = predictions['bert']['raw_score']
            score_accum += bert_s * EnsembleScorer.WEIGHTS['bert'] * 100
            weight_accum += EnsembleScorer.WEIGHTS['bert']
            details.append(f"BERT Score: {bert_s:.2f}")

        # Semantic Score
        if 'semantic' in predictions:
            sem_s = predictions['semantic']['raw_score']
            score_accum += sem_s * EnsembleScorer.WEIGHTS['semantic'] * 100
            weight_accum += EnsembleScorer.WEIGHTS['semantic']

        # Network Risk Logic
        net_risk = 0.0
        net_reasons = []
        for net_info in network_data:
            if net_info.get('proxy') or net_info.get('hosting'):
                net_risk += 40
                net_reasons.append("Hosted/Proxy IP")
            
            org = str(net_info.get('org', '')).lower()
            isp = str(net_info.get('isp', '')).lower()
            suspicious_hosts = ['hostinger', 'namecheap', 'digitalocean', 'hetzner', 'ovh', 'flokinet']
            if any(x in org or x in isp for x in suspicious_hosts):
                net_risk += 20
                net_reasons.append(f"Cheap Cloud Provider ({org[:15]}...)")
        
        net_risk = min(net_risk, 100)
        score_accum += net_risk * EnsembleScorer.WEIGHTS['network']
        weight_accum += EnsembleScorer.WEIGHTS['network']
        
        if net_reasons:
            details.append(f"Network Penalties: {', '.join(list(set(net_reasons)))}")

        if weight_accum == 0:
            final_score = 50.0
        else:
            final_score = score_accum / weight_accum

        return {
            "score": min(max(final_score, 0), 100),
            "details": "; ".join(details),
            "network_risk": net_risk
        }

def load_models():
    global ml_models, dl_models, bert_model, semantic_model, key_rotator
    logger.info("Initializing System & Loading Models...")
    
    models_dir = config.MODELS_DIR
    
    # Load ML Models
    for model_name in ['logistic', 'svm', 'xgboost']:
        try:
            path = os.path.join(models_dir, f'{model_name}.joblib')
            if os.path.exists(path):
                ml_models[model_name] = joblib.load(path)
                logger.info(f"Loaded ML: {model_name}")
        except Exception: pass

    # Load DL Models
    for model_name in ['attention_blstm', 'rcnn']:
        try:
            path = os.path.join(models_dir, f'{model_name}.pt')
            if os.path.exists(path):
                template = get_dl_models(input_dim=len(config.NUMERICAL_FEATURES))
                model = template[model_name]
                model.load_state_dict(torch.load(path, map_location='cpu'))
                model.eval()
                dl_models[model_name] = model
                logger.info(f"Loaded DL: {model_name}")
        except Exception: pass

    # Load BERT
    bert_path = os.path.join(config.BASE_DIR, 'finetuned_bert')
    if os.path.exists(bert_path):
        try:
            bert_model = FinetunedBERT(bert_path)
            logger.info("Loaded BERT")
        except Exception: pass

    # Load Semantic
    sem_path = os.path.join(config.BASE_DIR, 'Message_model', 'final_semantic_model')
    if os.path.exists(sem_path) and PhishingPredictor:
        try:
            semantic_model = PhishingPredictor(model_path=sem_path)
            logger.info("Loaded Semantic Model")
        except Exception: pass
        
    key_rotator = SmartAPIKeyRotator()

# --- FIXED & ROBUST URL EXTRACTION ---

def extract_visible_text_and_links(html_body: str) -> tuple:
    if not html_body: 
        return "", []

    extracted_urls = set()
    
    # --- 1. Regex Extraction (Run on RAW input first) ---
    url_pattern = r'(?:https?://|ftp://|www\.)[\w\-\.]+\.[a-zA-Z]{2,}(?:/[\w\-\._~:/?#[\]@!$&\'()*+,;=]*)?'
    
    try:
        raw_matches = re.findall(url_pattern, html_body)
        for url in raw_matches:
            cleaned_url = url.rstrip('.,;:"\')>]')
            extracted_urls.add(cleaned_url)
    except Exception as e:
        logger.warning(f"Regex extraction warning: {e}")

    # --- 2. HTML Attribute Extraction ---
    try:
        warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
        soup = BeautifulSoup(html_body, 'html.parser')

        url_tags = {
            'a': 'href', 'link': 'href', 'img': 'src', 'iframe': 'src',
            'form': 'action', 'source': 'src', 'script': 'src', 'area': 'href', 'embed': 'src'
        }

        for tag_name, attr_name in url_tags.items():
            for tag in soup.find_all(tag_name):
                url = tag.get(attr_name)
                if url:
                    url = url.strip()
                    if url.startswith('//'):
                        url = 'https:' + url
                    if re.match(url_pattern, url):
                        extracted_urls.add(url)

        # --- 3. Text Extraction ---
        for tag in soup(["script", "style", "nav", "header", "footer", "meta", "noscript", "svg"]):
            tag.decompose()

        text = soup.get_text(separator=' ', strip=True)
        text = unicodedata.normalize('NFKC', text)
        text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C" or ch == "\n")
        
        return text.strip(), list(extracted_urls)

    except Exception as e:
        logger.error(f"Parser Error: {e}")
        return html_body, list(extracted_urls)

async def extract_url_features(urls: List[str]) -> pd.DataFrame:
    if not urls: return pd.DataFrame()
    df = pd.DataFrame({'url': urls})
    whois_cache, ssl_cache = {}, {}
    
    # Concurrency limiter inside feature extraction if needed
    tasks = [asyncio.to_thread(process_row, row, whois_cache, ssl_cache) for _, row in df.iterrows()]
    
    # Use gather with return_exceptions=True to prevent one bad URL crashing the batch
    feature_list_raw = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions
    feature_list = []
    for f in feature_list_raw:
        if isinstance(f, Exception):
            logger.error(f"Feature extraction error: {f}")
            # Return empty feature set/defaults on error to keep DF alignment
            feature_list.append({}) 
        else:
            feature_list.append(f)

    return pd.concat([df, pd.DataFrame(feature_list)], axis=1)

def get_model_predictions(features_df: pd.DataFrame, message_text: str) -> Dict:
    predictions = {}
    num_feats = config.NUMERICAL_FEATURES
    cat_feats = config.CATEGORICAL_FEATURES
    
    if not features_df.empty:
        try:
            X = features_df[num_feats + cat_feats].copy()
            X[num_feats] = X[num_feats].fillna(-1)
            X[cat_feats] = X[cat_feats].fillna('N/A')
            
            # ML Prediction
            for name, model in ml_models.items():
                try:
                    probas = model.predict_proba(X)[:, 1]
                    predictions[name] = {'raw_score': float(np.max(probas))}
                except: predictions[name] = {'raw_score': 0.5}
            
            # DL Prediction
            if dl_models:
                X_num = torch.tensor(X[num_feats].values.astype(np.float32))
                with torch.no_grad():
                    for name, model in dl_models.items():
                        try:
                            out = model(X_num)
                            predictions[name] = {'raw_score': float(torch.max(out).item())}
                        except: predictions[name] = {'raw_score': 0.5}
            
            # BERT Prediction
            if bert_model:
                try:
                    scores = bert_model.predict_proba(features_df['url'].tolist())
                    predictions['bert'] = {'raw_score': float(np.mean([s[1] for s in scores]))}
                except: pass
        except Exception as e:
            logger.error(f"Feature Pipeline Error: {e}")
            
    # Semantic Prediction
    if semantic_model and message_text:
        try:
            res = semantic_model.predict(message_text)
            predictions['semantic'] = {'raw_score': float(res['phishing_probability'])}
        except: pass
        
    return predictions

async def get_network_data_raw(urls: List[str]) -> List[Dict]:
    """
    Fetches network data with caching and concurrency limits to avoid API bans.
    """
    data = []
    unique_hosts = set()
    
    # Filter to unique hosts to avoid redundant calls
    for url_str in urls:
        try:
            parsed = urlparse(url_str if url_str.startswith(('http', 'https')) else f"http://{url_str}")
            if parsed.hostname:
                unique_hosts.add(parsed.hostname)
        except: pass
    
    # Limit to top 5 unique hosts to save API quota
    target_hosts = list(unique_hosts)[:5]

    async with httpx.AsyncClient(timeout=3.0) as client:
        for host in target_hosts:
            # Check Cache
            if host in ip_cache:
                data.append(ip_cache[host])
                continue

            try:
                ip = await asyncio.to_thread(socket.gethostbyname, host)
                resp = await client.get(f"http://ip-api.com/json/{ip}?fields=status,message,country,isp,org,as,proxy,hosting")
                if resp.status_code == 200:
                    geo = resp.json()
                    if geo.get('status') == 'success':
                        geo['ip'] = ip
                        geo['host'] = host
                        data.append(geo)
                        ip_cache[host] = geo # Cache result
            except Exception:
                pass
            
            # Polite delay to respect rate limits
            await asyncio.sleep(0.2)
            
    return data

async def scrape_landing_page(url: str) -> str:
    if not url: return ""
    try:
        async with async_playwright() as p:
            # Launch chromium in headless mode
            browser = await p.chromium.launch(headless=True)
            
            # Create context with realistic User-Agent
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
            )
            
            page = await context.new_page()
            
            try:
                target_url = url if url.startswith(('http', 'https')) else f"http://{url}"
                # Wait for DOM to load, timeout after 10s to keep API fast
                await page.goto(target_url, timeout=10000, wait_until="domcontentloaded")
                
                # Extract content
                content = await page.content()
                
                # Process with BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                for tag in soup(["script", "style", "nav", "footer", "svg", "noscript"]):
                    tag.decompose()
                
                text = soup.get_text(separator=' ', strip=True)
                text = unicodedata.normalize('NFKC', text)
                return text[:2000]
                
            except Exception as e:
                # Return partial error info but don't crash
                return f"Error accessing page: {str(e)}"
            finally:
                await browser.close()
                
    except Exception as e:
        logger.warning(f"Scraping failed for {url}: {e}")
        return "Could not access landing page."

# --- UPDATED SYSTEM PROMPT WITH 14 EXAMPLES (2 NEW + 12 ORIGINAL) ---

SYSTEM_PROMPT = """You are an expert JSON-only phishing detection judge. Your sole purpose is to analyze input data and return a JSON object in the exact format requested. Do not output any text before or after the JSON.
**Core Rules:**
1.  **The "One Bad Link" Rule:** If the email contains **ANY** suspicious or malicious URL, the Final Decision MUST be "phishing" (100% Confidence), even if other links are legitimate (like Google Forms).
2.  **Suspicious URL Definition:** A URL is suspicious if:
    - It is NSFW/Adult.
    - It uses a "generated" or "random" domain (e.g., `643646.me`, `xyz123.top`) unrelated to the sender.
    - It is a mismatch (e.g., email says "Wipro" but URL is `allegrolokalnie.me`).
    - It is **HIDDEN** in a Header (H1) or Image tag but is not the main call-to-action.
3.  **Respect Technical Score:** If 'Calculated Ensemble Score' is > 60, you MUST lean towards 'phishing'.
4.  **Prioritize Ground Truth:** Trust Network Data, but remember: Cloudflare/AWS host both good and bad sites. A Cloudflare IP does NOT guarantee safety if the domain name itself (`643646.me`) looks fraudulent.
5.  **Highlighting:** Return the *entire* message. Wrap suspicious parts in `@@...@@`.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**14 FEW-SHOT EXAMPLES:**
**Example 1: Mixed Links (Phishing - Hidden Header)**
Sender: hr@wipro.com
Message: "Apply here: [docs.google.com](Legit)" (Hidden in H1: `suspicious-site.net`)
Correct Decision: {{
    "confidence": 99.0,
    "reasoning": "Phishing. Although the Google Form link is valid, the email contains a hidden URL ('suspicious-site.net') in the header. This is a common evasion tactic.",
    "highlighted_text": "Apply here: [docs.google.com] @@(Hidden Header URL Detected)@@",
    "final_decision": "phishing",
    "suggestion": "Do not click. A hidden malicious link was detected."
}}
**Example 2: Random Domain (Phishing)**
Sender: support@amazon.com
Message: "Verify account: [amazon-verify.643646.me]"
Correct Decision: {{
    "confidence": 95.0,
    "reasoning": "Phishing. The domain '643646.me' is a random/generated alphanumeric domain unrelated to Amazon.",
    "highlighted_text": "Verify account: @@[amazon-verify.643646.me]@@",
    "final_decision": "phishing",
    "suggestion": "This is a fake Amazon link."
}}
**Example 3: Clear Phishing (Typosquat)**
Sender: no-reply@paypa1-secure.xyz
Subject: URGENT! Your Account is Suspended!
Message: "URGENT! Your account has suspicious activity. Click: [http://paypa1-secure.xyz/verify](http://paypa1-secure.xyz/verify) to login and verify."
Correct Decision: {{
    "confidence": 98.0,
    "reasoning": "Phishing. Typosquatted domain 'paypa1', new age, suspicious ISP, and urgency tactics.",
    "highlighted_text": "@@URGENT!@@ Your account has suspicious activity. Click: @@[http://paypa1-secure.xyz/verify](http://paypa1-secure.xyz/verify)@@ to login and verify.",
    "final_decision": "phishing",
    "suggestion": "Do NOT click. This is a clear attempt to steal your credentials. Delete immediately."
}}
**Example 4: Legitimate (False Positive Case)**
Sender: notifications@codeforces.com
Subject: Codeforces Round 184 Reminder
Message: "Hi, join Codeforces Round 184. ... Unsubscribe: [https://codeforces.com/unsubscribe/](https://codeforces.com/unsubscribe/)..."
Correct Decision: {{
    "confidence": 10.0,
    "reasoning": "Legitimate. Override models. `domain_age: -1` is a lookup failure. Network data confirms 'codeforces.com' is real (Cloudflare).",
    "highlighted_text": "Hi, join Codeforces Round 184. ... Unsubscribe: [https://codeforces.com/unsubscribe/](https://codeforces.com/unsubscribe/)...",
    "final_decision": "legitimate",
    "suggestion": "This message is safe. It is a legitimate notification from Codeforces."
}}
**Example 5: Legitimate (Formal Text)**
Sender: investor.relations@tatamotors.com
Subject: TATA MOTORS GENERAL GUIDANCE NOTE
Message: "TATA MOTORS PASSENGER VEHICLES LIMITED... GENERAL GUIDANCE NOTE... [TRUNCATED]"
Correct Decision: {{
    "confidence": 5.0,
    "reasoning": "Legitimate. Formal corporate text. Network data confirms 'tatamotors.com' on Akamai. Models are correct.",
    "highlighted_text": "TATA MOTORS PASSENGER VEHICLES LIMITED... GENERAL GUIDANCE NOTE... [TRUNCATED]",
    "final_decision": "legitimate",
    "suggestion": "This message is a legitimate corporate communication and appears safe."
}}
**Example 6: No URL Phishing (Scam)**
Sender: it-support@yourcompany.org
Subject: Employee Appreciation Reward
Message: "To thank you for your hard work, please reply with your personal email address and mobile phone number to receive your $500 gift card."
Correct Decision: {{
    "confidence": 85.0,
    "reasoning": "Phishing. No URL. This is a data harvesting scam. The sender is suspicious and is requesting sensitive personal information.",
    "highlighted_text": "To thank you for your hard work, @@please reply with your personal email address and mobile phone number@@ to receive your $500 gift card.",
    "final_decision": "phishing",
    "suggestion": "Do not reply. This is a scam to steal your personal information. Report this email to your IT department."
}}
**Example 7: Legitimate Transaction (No URL)**
Sender: VM-SBIUPI
Subject: N/A
Message: "Dear UPI user A/C X1243 debited by 16.0 on date 16Nov25 trf to Kuldevi Caterers Refno 532032534589 If not u? call-1800111109 for other services-18001234-SBI"
Correct Decision: {{
    "confidence": 10.0,
    "reasoning": "Legitimate. This is a standard, informational banking transaction alert (UPI debit). It contains no URLs and the phone numbers appear to be standard toll-free support lines.",
    "highlighted_text": "Dear UPI user A/C X1243 debited by 16.0 on date 16Nov25 trf to Kuldevi Caterers Refno 532032534589 If not u? call-1800111109 for other services-18001234-SBI",
    "final_decision": "legitimate",
    "suggestion": "This message is a legitimate transaction alert and appears safe. No action is needed unless you do not recognize this transaction."
}}
**Example 8: Clear Phishing (Prize Scam)**
Sender: meta-rewards@hacker-round.com
Subject: hooray you have won a prize!!!
Message: "You have won Rs 5000 for the meta hacker round 2 , for getting into top 2500 click here to claim you prize : https:// [www.dghjdgf.com/paypal.co.uk/cycgi-bin/webscrcmd=_home-customer&nav=1/loading.php](https://www.dghjdgf.com/paypal.co.uk/cycgi-bin/webscrcmd=_home-customer&nav=1/loading.php)"
Correct Decision: {{
    "confidence": 99.0,
    "reasoning": "Phishing. This is a classic prize scam. The URL is highly suspicious, using a random domain ('dghjdgf.com') to impersonate PayPal. The lure of money and call to action are clear phishing tactics.",
    "highlighted_text": "@@You have won Rs 5000 for the meta hacker round 2@@ , for getting into top 2500 @@click here to claim you prize : https:// [www.dghjdgf.com/paypal.co.uk/cycgi-bin/webscrcmd=_home-customer&nav=1/loading.php](https://www.dghjdgf.com/paypal.co.uk/cycgi-bin/webscrcmd=_home-customer&nav=1/loading.php)@@",
    "final_decision": "phishing",
    "suggestion": "Do NOT click this link. This is a scam to steal your information. Delete this email immediately."
}}
**Example 9: Legitimate University Event (Internal)**
Sender: AI Club <ai_club@dau.ac.in>
Subject: Invitation to iPrompt ’25 & AI Triathlon — 15th November at iFest’25
Message: "Dear Students, The AI Club, DA-IICT, is delighted to invite you... Register: [https://ifest25.vercel.app](https://ifest25.vercel.app)    ... Participants' WhatsApp Group: [https://chat.whatsapp.com/EeJ1XeNxcgM7w7gVBjKjox](https://chat.whatsapp.com/EeJ1XeNxcgM7w7gVBjKjox)    ... Warm regards, AI Club, DA-IICT"
Correct Decision: {{
    "confidence": 5.0,
    "reasoning": "Legitimate. This is an internal university announcement from a trusted sender domain (@dau.ac.in). The links to Vercel (common for student projects) and WhatsApp are legitimate and verified by network data.",
    "highlighted_text": "Dear Students, The AI Club, DA-IICT, is delighted to invite you... Register: [https://ifest25.vercel.app](https://ifest25.vercel.app)    ... Participants' WhatsApp Group: [https://chat.whatsapp.com/EeJ1XeNxcgM7w7gVBjKjox](https://chat.whatsapp.com/EeJ1XeNxcgM7w7gVBjKjox)    ... Warm regards, AI Club, DA-IICT",
    "final_decision": "legitimate",
    "suggestion": "This email is a safe internal announcement about a university event."
}}
**Example 10: Legitimate Corporate Policy Update**
Sender: YouTube <no-reply@youtube.com>
Subject: Annual reminder about YouTube's Terms of Service, Community Guidelines and Privacy Policy
Message: "This email is an annual reminder that your use of YouTube is subject to the Terms of Service, Community Guidelines and Google's Privacy Policy... © 2025 Google LLC, 1600 Amphitheatre Parkway, Mountain View, CA, 94043"
Correct Decision: {{
    "confidence": 1.0,
    "reasoning": "Legitimate. This is a standard, text-heavy legal/policy notification from a trusted sender (@youtube.com). Network data confirms the domain belongs to Google. There is no suspicious call to action.",
    "highlighted_text": "This email is an annual reminder that your use of YouTube is subject to the Terms of Service, Community Guidelines and Google's Privacy Policy... © 2025 Google LLC, 1600 Amphitheatre Parkway, Mountain View, CA, 94043",
    "final_decision": "legitimate",
    "suggestion": "This is a standard policy update from YouTube. It is safe."
}}
**Example 11: Legitimate Service Notification (Google)**
Sender: 2022 01224 (Classroom) <no-reply@classroom.google.com>
Subject: Due tomorrow: "Lab 09"
Message: "Aaditya_CT303 Due tomorrow Lab 09 Follow these instructions... View assignment Google LLC 1600 Amphitheatre Parkway, Mountain View, CA 94043 USA"
Correct Decision: {{
    "confidence": 2.0,
    "reasoning": "Legitimate. This is an automated notification from Google Classroom. The sender (@classroom.google.com) and network data confirm it's a real Google service. The 'urgency' (Due tomorrow) is part of the service's function.",
    "highlighted_text": "Aaditya_CT303 Due tomorrow Lab 09 Follow these instructions... View assignment Google LLC 1600 Amphitheatre Parkway, Mountain View, CA 94043 USA",
    "final_decision": "legitimate",
    "suggestion": "This is a safe and legitimate assignment reminder from Google Classroom."
}}
**Example 12: Legitimate Internal Announcement (No URL)**
Sender: iFest DAU <ifest@dau.ac.in>
Subject: Instruction for i.Fest' 25
Message: "Hello everyone, As we all know, i.Fest' 25 begins today! Here are some important guidelines... Entry will be permitted only with a valid Student ID card... Best Regards, Team i.Fest"
Correct Decision: {{
    "confidence": 5.0,
    "reasoning": "Legitimate. This is a text-only informational email from a trusted internal university domain (@dau.ac.in). It contains instructions, not suspicious links or requests.",
    "highlighted_text": "Hello everyone, As we all know, i.Fest' 25 begins today! Here are some important guidelines... Entry will be permitted only with a valid Student ID card... Best Regards, Team i.Fest",
    "final_decision": "legitimate",
    "suggestion": "This is a safe internal announcement for university students."
}}
**Example 13: Legitimate Marketing (Clickbait Subject)**
Sender: Jia from Unstop <noreply@dare2compete.news>
Subject: [Congrats] Intern with Panasonic - Earn a stipend of ₹35,000!
Message: "Hi Akshat, here are some top opportunities curated just for you! ... Software Engineering Internship Panasonic... Explore more Internships... © 2025 Unstop. All rights reserved."
Correct Decision: {{
    "confidence": 15.0,
    "reasoning": "Legitimate. Although the subject line '[Congrats]' is clickbait, the sender domain ('dare2compete.news') is established and network data (Cloudflare) checks out. The content is a standard job/internship digest from a known platform.",
    "highlighted_text": "Hi Akshat, here are some top opportunities curated just for you! ... Software Engineering Internship Panasonic... Explore more Internships... © 2025 Unstop. All rights reserved.",
    "final_decision": "legitimate",
    "suggestion": "This is a legitimate promotional email from Unstop. It is safe."
}}
**Example 14: Legitimate Marketing (SaaS)**
Sender: Numerade <ace@email.numerade.com>
Subject: Your All-In-One Finals Prep Toolkit
Message: "Finals can be overwhelming. Numerade's textbook solutions give you instant access to step-by-step explanations... Find Your Textbook Answers ... © 2025, Numerade, All rights reserved."
Correct Decision: {{
    "confidence": 8.0,
    "reasoning": "Legitimate. This is a standard marketing email from a known company (Numerade) sent via a reputable email service (SendGrid), as confirmed by network data. It has clear unsubscribe links and branding.",
    "highlighted_text": "Finals can be overwhelming. Numerade's textbook solutions give you instant access to step-by-step explanations... Find Your Textbook Answers ... © 2025, Numerade, All rights reserved.",
    "final_decision": "legitimate",
    "suggestion": "This is a safe marketing email from Numerade."
}}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**YOUR ANALYSIS TASK:**
Analyze the message data provided by the user (in the 'user' message) following all rules. Respond ONLY with the JSON object.
**OUTPUT FORMAT (JSON ONLY):**
{{
    "confidence": <float (0-100, directional score where >50 is phishing)>,
    "reasoning": "<your brief analysis explaining why this is/isn't phishing, mentioning key evidence>",
    "highlighted_text": "<THE FULL, ENTIRE original message with suspicious parts marked as @@suspicious text@@>",
    "final_decision": "phishing" or "legitimate",
    "suggestion": "<specific, actionable advice for the user on how to handle this message>"
}}"""

# --- UPDATED FUNCTION TO HANDLE RAW HTML SCANNING & CLEAN TEXT DISPLAY ---
async def get_groq_decision(ensemble_result: Dict, network_data: List[Dict], landing_page_text: str, cleaned_text: str, original_raw_html: str, readable_display_text: str, sender: str, subject: str):
    # 1. Format Network Data
    net_str = "No Network Data"
    if network_data:
        net_str = "\n".join([
            f"- Host: {d.get('host')} | IP: {d.get('ip')} | Org: {d.get('org')} | ISP: {d.get('isp')} | Hosting/Proxy: {d.get('hosting') or d.get('proxy')}"
            for d in network_data
        ])
    
    # --- FORENSIC URL SCAN (Scanning Raw HTML) ---
    forensic_report = []
    try:
        soup = BeautifulSoup(original_raw_html, 'html.parser')
        
        # A. Scan Forms
        for form in soup.find_all('form'):
            action = form.get('action')
            if action: forensic_report.append(f"CRITICAL: Found URL in <form action>: {action}")

        # B. Scan Images
        for img in soup.find_all('img'):
            src = img.get('src')
            if src: forensic_report.append(f"Found URL in <img src>: {src}")
            
        # C. Scan Links
        for a in soup.find_all('a'):
            href = a.get('href')
            if href: forensic_report.append(f"Found URL in <a href>: {href}")
            
        # D. Scan Raw Text (Catches the H1 Case)
        url_pattern = r'(?:https?://|ftp://|www\.)[\w\-\.]+\.[a-zA-Z]{2,}(?:/[\w\-\._~:/?#[\]@!$&\'()*+,;=]*)?'
        all_text_urls = set(re.findall(url_pattern, original_raw_html))
        if all_text_urls:
            forensic_report.append(f"All URLs detected in raw text: {', '.join(all_text_urls)}")

    except Exception as e:
        logger.warning(f"Forensic Scan Error: {e}")
        forensic_report.append("Forensic scan failed to parse HTML structure.")

    forensic_str = "\n".join(forensic_report) if forensic_report else "No URLs found in forensic scan."

    # --- PROMPT CONSTRUCTION ---
    # NOTE: We pass 'readable_display_text' as the Message Content so LLM highlights CLEAN text, not HTML.
    prompt = f"""
    **ANALYSIS CONTEXT**
    Sender: {sender}
    Subject: {subject}
    
    **FORENSIC URL SCAN (INTERNAL HTML ANALYSIS)**
    The system scanned the raw HTML and found these URLs (hidden in tags):
    {forensic_str}
    
    **TECHNICAL INDICATORS**
    Calculated Ensemble Score: {ensemble_result['score']:.2f} / 100
    Key Factors: {ensemble_result['details']}
    
    **NETWORK GROUND TRUTH**
    {net_str}
    
    **LANDING PAGE PREVIEW (Scraped Text)**
    "{landing_page_text}"
    
    **MESSAGE CONTENT (READABLE VERSION)**
    "{readable_display_text[:MAX_INPUT_CHARS]}"
    
    **TASK:**
    Analyze the "FORENSIC URL SCAN" findings.
    - If ANY URL in the forensic scan is NSFW/Adult or malicious, flag as PHISHING.
    - If a URL looks like a generated subdomain (e.g. `643646.me`) or is unrelated to the sender, FLAG AS PHISHING immediately.
    - IMPORTANT: For the 'highlighted_text' field in your JSON response, use the **MESSAGE CONTENT (READABLE VERSION)** provided above. Do NOT output raw HTML tags. Just mark suspicious parts in the readable text with @@...@@.
    """
    
    attempts = 0
    while attempts < LLM_MAX_RETRIES:
        try:
            client = key_rotator.get_client_and_rotate()
            if not client: raise Exception("No Keys")
            
            completion = await client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                max_tokens=4096,
                response_format={"type": "json_object"}
            )
            
            raw_content = completion.choices[0].message.content
            parsed_json = clean_and_parse_json(raw_content)
            if parsed_json:
                return parsed_json
            else:
                raise ValueError("Empty or Invalid JSON from LLM")

        except RateLimitError as e:
            wait_time = 2 ** (attempts + 1) + random.uniform(0, 1)
            if hasattr(e, 'headers') and 'retry-after' in e.headers:
                try:
                    wait_time = float(e.headers['retry-after']) + 1
                except: pass
            
            logger.warning(f"LLM Rate Limit (429). Retrying in {wait_time:.2f}s...")
            await asyncio.sleep(wait_time)
            attempts += 1

        except Exception as e:
            logger.warning(f"LLM Attempt {attempts+1} failed: {e}")
            attempts += 1
            await asyncio.sleep(1)
            
    is_phishing = ensemble_result['score'] > 50
    return {
        "confidence": ensemble_result['score'],
        "reasoning": f"LLM Unavailable after retries. Decision based purely on Technical Score ({ensemble_result['score']:.2f}).",
        "highlighted_text": readable_display_text, # Fallback to readable text
        "final_decision": "phishing" if is_phishing else "legitimate",
        "suggestion": "Exercise caution. Automated analysis detected risks." if is_phishing else "Appears safe."
    }

@app.on_event("startup")
async def startup():
    logger.info("Starting Robust Phishing API v2.6.0")
    load_models()
    logger.info("Ensemble Scorer & Models Ready")

# --- PREDICT ENDPOINT ---

@app.post("/predict", response_model=PredictionResponse)
async def predict(input_data: MessageInput):
    if not input_data.text or not input_data.text.strip():
        return PredictionResponse(
            confidence=0.0, reasoning="Empty input.", highlighted_text="",
            final_decision="legitimate", suggestion="None"
        )
        
    async with request_semaphore:
        try:
            start_time = time.time()
            
            # 1. Unified Extraction
            # 'extracted_text' = Clean, readable text (No HTML tags)
            # 'all_urls' = List of URLs found
            extracted_text, all_urls = extract_visible_text_and_links(input_data.text)
            
            # 2. Clean Text for Models (Lowercased, no URLs)
            url_pattern_for_cleaning = r'(?:https?://|ftp://|www\.)[\w\-\.]+\.[a-zA-Z]{2,}(?:/[\w\-\._~:/?#[\]@!$&\'()*+,;=]*)?'
            cleaned_text_for_models = re.sub(url_pattern_for_cleaning, '', extracted_text)
            cleaned_text_for_models = ' '.join(cleaned_text_for_models.lower().split())

            # LIMIT URLs to avoid 429s / DoS
            all_urls = all_urls[:MAX_URLS_TO_ANALYZE]

            if all_urls:
                logger.info(f"🔍 Analyzing {len(all_urls)} URLs.")
            else:
                logger.info("ℹ️ No URLs detected.")

            # 3. Feature Extraction & Scraping
            features_df = pd.DataFrame()
            network_data_raw = []
            landing_page_text = ""
            
            if all_urls:
                results = await asyncio.gather(
                    extract_url_features(all_urls),
                    get_network_data_raw(all_urls),
                    scrape_landing_page(all_urls[0]) if all_urls else asyncio.to_thread(lambda: "")
                )
                features_df, network_data_raw, landing_page_text = results
                if landing_page_text:
                    logger.info(f"Scraped {len(landing_page_text)} chars from landing page.")
            
            # 4. Model Predictions
            predictions = await asyncio.to_thread(get_model_predictions, features_df, cleaned_text_for_models)
            
            # 5. Ensemble Scoring
            ensemble_result = EnsembleScorer.calculate_technical_score(predictions, network_data_raw, all_urls)
            logger.info(f"Ensemble Technical Score: {ensemble_result['score']:.2f}")
            
            # 6. LLM Final Decision
            # CRITICAL UPDATE: Pass both Raw HTML (for forensics) AND Extracted Text (for highlighting)
            llm_result = await get_groq_decision(
                ensemble_result, 
                network_data_raw, 
                landing_page_text, 
                cleaned_text_for_models, 
                input_data.text,   # Original Raw HTML (for forensic scan)
                extracted_text,    # Readable Text (for LLM display output)
                input_data.sender, 
                input_data.subject
            )
            
            final_dec = llm_result.get('final_decision', 'legitimate').lower()
            if final_dec not in ['phishing', 'legitimate']: final_dec = 'legitimate'
            
            elapsed = time.time() - start_time
            logger.info(f"✅ Processed in {elapsed:.2f}s | TechScore: {ensemble_result['score']:.0f} | Final: {final_dec.upper()}")
            
            return PredictionResponse(
                confidence=float(llm_result.get('confidence', ensemble_result['score'])),
                reasoning=llm_result.get('reasoning', ensemble_result['details']),
                highlighted_text=llm_result.get('highlighted_text', extracted_text),
                final_decision=final_dec,
                suggestion=llm_result.get('suggestion', 'Check details carefully.')
            )
            
        except Exception as e:
            logger.error(f"Prediction Failed: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
