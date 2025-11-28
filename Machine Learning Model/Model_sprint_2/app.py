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
import email
from email.policy import default
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse
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
import config
from models import get_ml_models, get_dl_models, FinetunedBERT
from feature_extraction import process_row
load_dotenv()
sys.path.append(os.path.join(config.BASE_DIR, 'Message_model'))
try:
    from predict import PhishingPredictor
except ImportError:
    PhishingPredictor = None

class UltraColorFormatter(logging.Formatter):
    GREY = "\x1b[38;5;240m"
    CYAN = "\x1b[36m"
    NEON_BLUE = "\x1b[38;5;39m"
    NEON_GREEN = "\x1b[38;5;82m"
    NEON_PURPLE = "\x1b[38;5;129m"
    YELLOW = "\x1b[33m"
    ORANGE = "\x1b[38;5;208m"
    RED = "\x1b[31m"
    BOLD_RED = "\x1b[31;1m"
    WHITE_BOLD = "\x1b[37;1m"
    RESET = "\x1b[0m"
    FORMATS = {
        logging.DEBUG: GREY + "   [DEBUG] %(message)s" + RESET,
        logging.INFO: "%(message)s" + RESET,
        logging.WARNING: ORANGE + "   [WARNING] %(message)s" + RESET,
        logging.ERROR: RED + "   [ERROR] %(message)s" + RESET,
        logging.CRITICAL: BOLD_RED + "\n [CRITICAL] %(message)s\n" + RESET
    }
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
logger = logging.getLogger("PhishingAPI")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(UltraColorFormatter())
if logger.hasHandlers():
    logger.handlers.clear()
logger.addHandler(ch)

def log_section(title):
    logger.info(f"\n{UltraColorFormatter.NEON_PURPLE}┌{'─'*70}┐")
    logger.info(f"{UltraColorFormatter.NEON_PURPLE}│ {UltraColorFormatter.WHITE_BOLD}{title.center(68)}{UltraColorFormatter.NEON_PURPLE} │")
    logger.info(f"{UltraColorFormatter.NEON_PURPLE}└{'─'*70}┘{UltraColorFormatter.RESET}")
def log_step(icon, text):
    logger.info(f"{UltraColorFormatter.CYAN} {icon} {text}{UltraColorFormatter.RESET}")
def log_substep(text, value=""):
    val_str = f": {UltraColorFormatter.NEON_GREEN}{value}{UltraColorFormatter.RESET}" if value else ""
    logger.info(f"{UltraColorFormatter.GREY}    ├─ {text}{val_str}")
def log_success(text):
    logger.info(f"{UltraColorFormatter.NEON_GREEN}  {text}{UltraColorFormatter.RESET}")
def log_metric(label, value, warning=False):
    color = UltraColorFormatter.ORANGE if warning else UltraColorFormatter.NEON_BLUE
    logger.info(f"    {color} {label}: {UltraColorFormatter.WHITE_BOLD}{value}{UltraColorFormatter.RESET}")

MAX_INPUT_CHARS = 4000
MAX_CONCURRENT_REQUESTS = 5
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
            log_substep("API Key Rotator", f"Initialized with {len(self.keys)} keys")
        
        self.clients = [AsyncGroq(api_key=k) for k in self.keys]
        self.num_keys = len(self.clients)
        self.current_index = 0
    def get_client_and_rotate(self):
        if not self.clients:
            return None
        client = self.clients[self.current_index]
        self.current_index = (self.current_index + 1) % self.num_keys
        return client

ml_models = {}
dl_models = {}
bert_model = None
semantic_model = None
key_rotator: Optional[SmartAPIKeyRotator] = None
ip_cache = {}
def clean_and_parse_json(text: str) -> Dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    text = re.sub(r"json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"", "", text)
    
    try:
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            json_str = text[start:end+1]
            return json.loads(json_str)
    except Exception:
        pass
    logger.error(f"Failed to parse JSON from LLM response: {text[:50]}...")
    return {}
class EnsembleScorer:
    WEIGHTS = {'ml': 0.30, 'dl': 0.20, 'bert': 0.20, 'semantic': 0.10, 'network': 0.20}
    @staticmethod
    def calculate_technical_score(predictions: Dict, network_data: List[Dict], urls: List[str]) -> Dict:
        score_accum = 0.0
        weight_accum = 0.0
        details = []
        
        log_step("", "Calculating Ensemble Weights")
        
        ml_scores = [p['raw_score'] for k, p in predictions.items() if k in ['logistic', 'svm', 'xgboost']]
        if ml_scores:
            avg_ml = np.mean(ml_scores)
            score_accum += avg_ml * EnsembleScorer.WEIGHTS['ml'] * 100
            weight_accum += EnsembleScorer.WEIGHTS['ml']
            details.append(f"ML Consensus: {avg_ml:.2f}")
            log_substep("ML Models Consensus", f"{avg_ml:.4f} (Weight: {EnsembleScorer.WEIGHTS['ml']})")
        
        dl_scores = [p['raw_score'] for k, p in predictions.items() if k in ['attention_blstm', 'rcnn']]
        if dl_scores:
            avg_dl = np.mean(dl_scores)
            score_accum += avg_dl * EnsembleScorer.WEIGHTS['dl'] * 100
            weight_accum += EnsembleScorer.WEIGHTS['dl']
            details.append(f"DL Consensus: {avg_dl:.2f}")
            log_substep("Deep Learning Consensus", f"{avg_dl:.4f} (Weight: {EnsembleScorer.WEIGHTS['dl']})")
        
        if 'bert' in predictions:
            bert_s = predictions['bert']['raw_score']
            score_accum += bert_s * EnsembleScorer.WEIGHTS['bert'] * 100
            weight_accum += EnsembleScorer.WEIGHTS['bert']
            details.append(f"BERT Score: {bert_s:.2f}")
            log_substep("BERT Finetuned", f"{bert_s:.4f} (Weight: {EnsembleScorer.WEIGHTS['bert']})")
        
        if 'semantic' in predictions:
            sem_s = predictions['semantic']['raw_score']
            score_accum += sem_s * EnsembleScorer.WEIGHTS['semantic'] * 100
            weight_accum += EnsembleScorer.WEIGHTS['semantic']
            log_substep("Semantic Analysis", f"{sem_s:.4f} (Weight: {EnsembleScorer.WEIGHTS['semantic']})")
        
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
        
        log_substep("Network Risk Calculated", f"{net_risk:.2f} (Weight: {EnsembleScorer.WEIGHTS['network']})")
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
    log_section("SYSTEM STARTUP: LOADING ASSETS")
    
    models_dir = config.MODELS_DIR
    
    for model_name in ['logistic', 'svm', 'xgboost']:
        try:
            path = os.path.join(models_dir, f'{model_name}.joblib')
            if os.path.exists(path):
                ml_models[model_name] = joblib.load(path)
                log_substep(f"ML Model Loaded", model_name)
        except Exception:
            pass
    
    for model_name in ['attention_blstm', 'rcnn']:
        try:
            path = os.path.join(models_dir, f'{model_name}.pt')
            if os.path.exists(path):
                template = get_dl_models(input_dim=len(config.NUMERICAL_FEATURES))
                model = template[model_name]
                model.load_state_dict(torch.load(path, map_location='cpu'))
                model.eval()
                dl_models[model_name] = model
                log_substep(f"DL Model Loaded", model_name)
        except Exception:
            pass
    
    bert_path = os.path.join(config.BASE_DIR, 'finetuned_bert')
    if os.path.exists(bert_path):
        try:
            bert_model = FinetunedBERT(bert_path)
            log_substep("BERT Model", "Loaded Successfully")
        except Exception:
            pass
    
    sem_path = os.path.join(config.BASE_DIR, 'Message_model', 'final_semantic_model')
    if os.path.exists(sem_path) and PhishingPredictor:
        try:
            semantic_model = PhishingPredictor(model_path=sem_path)
            log_substep("Semantic Model", "Loaded Successfully")
        except Exception:
            pass
    key_rotator = SmartAPIKeyRotator()

def extract_visible_text_and_links(raw_email: str) -> tuple:
    log_step("", "Parsing Email MIME Structure")
    if not raw_email:
        logger.warning("Parsing received empty email input")
        return "", []
    extracted_text_parts = []
    links = set()
    
    try:
        msg = email.message_from_string(raw_email, policy=default)
        
        metadata = {
            "from": msg.get("From", ""),
            "to": msg.get("To", ""),
            "subject": msg.get("Subject", "")
        }
        for k, v in metadata.items():
            if v:
                extracted_text_parts.append(f"{k.capitalize()}: {v}")
                log_substep(f"Metadata [{k}]", v[:50] + "..." if len(v) > 50 else v)
        part_count = 0
        for part in msg.walk():
            part_count += 1
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition") or "")
            try:
                if content_type == "text/plain":
                    text_data = part.get_payload(decode=True)
                    if text_data:
                        text_str = text_data.decode(part.get_content_charset() or "utf-8", errors="ignore")
                        extracted_text_parts.append(text_str)
                        links.update(re.findall(r'https?://\S+', text_str))
                
                elif content_type == "text/html":
                    html_data = part.get_payload(decode=True)
                    if html_data:
                        html_str = html_data.decode(part.get_content_charset() or "utf-8", errors="ignore")
                        soup = BeautifulSoup(html_str, "html.parser")
                        extracted_text_parts.append(soup.get_text(separator="\n"))
                        for a in soup.find_all("a", href=True):
                            links.add(a["href"])
                        for img in soup.find_all("img", src=True):
                            links.add(img["src"])
                
                elif "attachment" in content_disposition.lower() or "inline" in content_disposition.lower():
                    filename = part.get_filename()
                    if filename:
                        extracted_text_parts.append(f"[Attachment found: {filename}]")
                        log_substep("Attachment", filename)
            except Exception as e:
                logger.warning(f"Error parsing email part: {e}")
    except Exception as e:
        logger.error(f"Email Parsing Failed: {e}")
    
    extracted_text = "\n".join(extracted_text_parts).strip()
    
    if not extracted_text:
        if "<html" in raw_email.lower() or "<body" in raw_email.lower() or "<div" in raw_email.lower():
            log_substep("Fallback", "Input appears to be Raw HTML, stripping tags...")
            try:
                soup = BeautifulSoup(raw_email, "html.parser")
                extracted_text = soup.get_text(separator="\n")
                
                for a in soup.find_all("a", href=True):
                    links.add(a["href"])
                for img in soup.find_all("img", src=True):
                    links.add(img["src"])
            except Exception:
                extracted_text = raw_email
        else:
            extracted_text = raw_email
            
    links.update(re.findall(r'https?://\S+', raw_email))
    cleaned_links = []
    for link in links:
        link = link.strip().strip("<>").replace('"', "")
        if link.startswith("http://") or link.startswith("https://"):
            cleaned_links.append(link)
    log_success(f"Parsed Content. Extracted {len(cleaned_links)} unique URLs.")
    return extracted_text, cleaned_links
async def extract_url_features(urls: List[str]) -> pd.DataFrame:
    if not urls:
        return pd.DataFrame()
    
    log_step("", f"Extracting Features for {len(urls)} URLs")
    df = pd.DataFrame({'url': urls})
    whois_cache, ssl_cache = {}, {}
    tasks = [asyncio.to_thread(process_row, row, whois_cache, ssl_cache) for _, row in df.iterrows()]
    feature_list_raw = await asyncio.gather(*tasks, return_exceptions=True)
    feature_list = []
    for i, f in enumerate(feature_list_raw):
        if isinstance(f, Exception):
            logger.error(f"Feature extraction error on {urls[i]}: {f}")
            feature_list.append({})
        else:
            feature_list.append(f)
    
    log_substep("Feature Extraction", "Complete")
    return pd.concat([df, pd.DataFrame(feature_list)], axis=1)
def get_model_predictions(features_df: pd.DataFrame, message_text: str) -> Dict:
    predictions = {}
    num_feats = config.NUMERICAL_FEATURES
    cat_feats = config.CATEGORICAL_FEATURES
    
    if not features_df.empty:
        try:
            log_step("", "Running Machine Learning Inference")
            X = features_df[num_feats + cat_feats].copy()
            X[num_feats] = X[num_feats].fillna(-1)
            X[cat_feats] = X[cat_feats].fillna('N/A')
            
            for name, model in ml_models.items():
                try:
                    probas = model.predict_proba(X)[:, 1]
                    raw_score = float(np.max(probas))
                    predictions[name] = {'raw_score': raw_score}
                    log_substep(f"ML: {name.ljust(10)}", f"{raw_score:.4f}")
                except:
                    predictions[name] = {'raw_score': 0.5}
            
            if dl_models:
                X_num = torch.tensor(X[num_feats].values.astype(np.float32))
                with torch.no_grad():
                    for name, model in dl_models.items():
                        try:
                            out = model(X_num)
                            raw_score = float(torch.max(out).item())
                            predictions[name] = {'raw_score': raw_score}
                            log_substep(f"DL: {name.ljust(10)}", f"{raw_score:.4f}")
                        except:
                            predictions[name] = {'raw_score': 0.5}
            
            if bert_model:
                try:
                    scores = bert_model.predict_proba(features_df['url'].tolist())
                    avg_score = float(np.mean([s[1] for s in scores]))
                    predictions['bert'] = {'raw_score': avg_score}
                    log_substep("BERT Inference", f"{avg_score:.4f}")
                except:
                    pass
        except Exception as e:
            logger.error(f"Feature Pipeline Error: {e}")
    if semantic_model and message_text:
        try:
            log_step("", "Running Semantic Text Analysis")
            res = semantic_model.predict(message_text)
            predictions['semantic'] = {'raw_score': float(res['phishing_probability'])}
            log_substep("Semantic Prob", f"{res['phishing_probability']:.4f}")
        except:
            pass
    return predictions
async def get_network_data_raw(urls: List[str]) -> List[Dict]:
    data = []
    unique_hosts = set()
    
    for url_str in urls:
        try:
            parsed = urlparse(url_str if url_str.startswith(('http', 'https')) else f"http://{url_str}")
            if parsed.hostname:
                unique_hosts.add(parsed.hostname)
        except:
            pass
    target_hosts = list(unique_hosts)[:5]
    log_step("", f"Geo-Locating Hosts: {target_hosts}")
    async with httpx.AsyncClient(timeout=3.0) as client:
        for host in target_hosts:
            if host in ip_cache:
                data.append(ip_cache[host])
                log_substep(f"Cache Hit", host)
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
                        ip_cache[host] = geo
                        log_substep(f"Resolved {host}", f"{geo.get('org', 'Unknown')} [{geo.get('country', 'UNK')}]")
            except Exception:
                log_substep(f"Failed to resolve", host)
            
            await asyncio.sleep(0.2)
    return data
async def scrape_landing_page(urls: list[str]) -> dict:
      
    urls = urls[:10]
    results = {}
    async def scrape_single(url: str):
        nonlocal results
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                try:
                    target_url = url if url.startswith(("http", "https")) else f"http://{url}"
                    await page.goto(target_url, timeout=10000, wait_until="domcontentloaded")
                    content = await page.content()
                    soup = BeautifulSoup(content, "html.parser")
                    for tag in soup(["script", "style", "nav", "footer", "svg", "noscript"]):
                        tag.decompose()
                    text = soup.get_text(separator=" ", strip=True)
                    text = unicodedata.normalize("NFKC", text)
                    results[url] = text[:300]
                except Exception as e:
                    results[url] = f"Error accessing page: {str(e)}"
                finally:
                    await browser.close()
        except Exception as e:
            results[url] = f"Scraping failed: {str(e)}"
    tasks = [scrape_single(u) for u in urls]
    await asyncio.gather(*tasks)
    return results

SYSTEM_PROMPT = """You are the 'Maverick', an elite, autonomous Cybersecurity Judge. Your sole purpose is to analyze the provided Evidence Dossier and return a JSON object.
**Core Rules:**
1. **The "One Bad Link" Rule:** If the email contains **ANY** suspicious or malicious URL, the Final Decision MUST be "phishing" (100% Confidence), even if other links are legitimate.
2. **Prioritize Ground Truth:** You must prioritize **Scraped Content** (e.g., a page asking for credentials) and **Network Data** (e.g., a Bank hosted on DigitalOcean) over the Technical Score.
3. **Override Authority:** Even if the 'Technical Ensemble Score' is low (e.g., 20/100), if you find a Critical Threat in the Scraped Data or Forensic Scan, you MUST override with a High Score (90-100).
4. **Suspicious Indicators:**
    - **Scraped Data:** Login forms on non-official domains, "Verify Identity" text, urgency.
    - **Network:** Mismatch between Sender Domain and Hosting (e.g., Microsoft email hosted on Namecheap).
    - **Forensics:** Hidden H1 tags, Typosquatting (paypa1.com), Mismatched hrefs.
**8 ROBUST FEW-SHOT EXAMPLES:**
**Example 1: Phishing (Credential Harvesting - Scraped Data Override)**
**Input:**
Sender: security-alert@microsoft-online-verify.com
Subject: Action Required: Unusual Sign-in Activity Detected
Technical Score: 35 / 100
Network Intelligence: Host: 162.241.2.1 | Org: Unified Layer (Cheap Hosting) | ISP: Bluehost | Proxy: False
Scraped Content: "Microsoft 365. Sign in to your account. Email, phone, or Skype. No account? Create one. Can't access your account? Sign-in options. Terms of Use Privacy & Cookies. © Microsoft 2025. NOTE: This page is for authorized users only."
Forensic Scan: Link: http://microsoft-online-verify.com/login.php
Message: "Microsoft Security Alert
We detected a sign-in attempt from a new device or location.
**Account:** user@example.com
**Date:** Fri, Nov 28, 2025 10:23 AM GMT
**Location:** Moscow, Russia
**IP Address:** 103.22.14.2
**Browser:** Firefox on Windows 10
If this wasn't you, your account may have been compromised. Please **verify your identity immediately** to secure your account and avoid permanent suspension.
[Secure My Account]
Thanks,
The Microsoft Account Team"
**Correct Decision:**
{{
  "confidence": 99.0,
  "reasoning": "CRITICAL OVERRIDE. The Scraped Data mimics a Microsoft 365 Login portal ('Sign in to your account'), but the Network Data confirms the site is hosted on 'Unified Layer/Bluehost', NOT Microsoft's official Azure infrastructure. This is a classic credential harvesting attack using a fake security alert.",
  "highlighted_text": "Please @@verify your identity immediately@@ to secure your account and avoid permanent suspension. @@[Secure My Account]@@",
  "final_decision": "phishing",
  "suggestion": "Do not enter credentials. This is a fake login page hosted on non-Microsoft servers."
}}
**Example 2: Phishing (Hidden Malicious URL - Forensic Override)**
**Input:**
Sender: hr-updates@wipro.com
Subject: MANDATORY: Updated Employee Handbook & Compliance Policy 2025
Technical Score: 45 / 100
Network Intelligence: Host: docs.google.com (Google LLC)
Scraped Content: "Google Docs. Sign in. Employee Handbook 2025.pdf. You need permission. Request access. Switch accounts. Google Workspace."
Forensic Scan: CRITICAL: Found hidden URL in H1 tag: 'http://bit.ly/malware-redirect-payload'
Message: "Dear Team,
As part of our annual compliance audit (ISO 27001), all employees are required to review and sign the updated Employee Handbook for the fiscal year 2025.
Please access the document via the secure Google Docs link below:
[docs.google.com/handbook-2025](Link)
Failure to acknowledge this document by Friday may result in a temporary suspension of network access.
Regards,
HR Compliance Team
Wipro Limited"
**Correct Decision:**
{{
  "confidence": 98.0,
  "reasoning": "Phishing. While the visible body text points to a legitimate Google Docs URL, the email contains a hidden malicious URL ('bit.ly/malware-redirect-payload') embedded in the HTML header tags. This is a sophisticated evasion tactic designed to bypass filters while tricking the user.",
  "highlighted_text": "Please access the document via the secure Google Docs link below: [docs.google.com/handbook-2025] @@(Hidden Header URL Detected)@@",
  "final_decision": "phishing",
  "suggestion": "Do not click. A hidden malicious payload was detected in the email structure."
}}
**Example 3: Phishing (Typosquatting & Urgency)**
**Input:**
Sender: support@paypa1-resolution.com
Subject: URGENT: Wallet Suspended - Case ID #99283-AX
Technical Score: 88 / 100
Network Intelligence: Host: paypa1-resolution.com | Org: Namecheap Inc | ISP: Namecheap
Scraped Content: "PayPal. Security Challenge. Enter your credit card number to verify ownership. Expiration Date. CVV. Billing Address. Submit. Copyright 1999-2025 PayPal. All rights reserved."
Forensic Scan: Link: https://paypa1-resolution.com/verify-identity
Message: "Hello Customer,
Your PayPal wallet has been temporarily suspended due to suspicious transactions totaling $400.00 USD to 'Global-Tech-Solutions Ltd'.
To restore full access to your funds, you must **verify your payment method immediately**. Failure to do so within 24 hours will result in the permanent closure of your account and forfeiture of remaining balance.
[Resolve Issue Now]
Thank you for being a valued customer."
**Correct Decision:**
{{
  "confidence": 99.0,
  "reasoning": "Phishing. Typosquatting detected ('paypa1' instead of 'paypal'). The Scraped Data confirms the landing page asks for credit card details (CVV/Expiry), and the domain is registered via Namecheap, not PayPal's official infrastructure. High urgency and threat of 'forfeiture' are clear indicators.",
  "highlighted_text": "Your PayPal wallet has been temporarily @@suspended@@. To restore full access, you must @@verify your payment method immediately@@. Failure to do so within 24 hours will result in @@permanent closure@@.",
  "final_decision": "phishing",
  "suggestion": "Delete immediately. This is an impersonation attack stealing financial data."
}}
**Example 4: Legitimate (Internal Corporate Email)**
**Input:**
Sender: admin@internal.daiict.ac.in
Subject: Scheduled Maintenance - Server Room B - Sunday Nov 30
Technical Score: 15 / 100
Network Intelligence: Host: internal.daiict.ac.in | Org: DA-IICT | ISP: NKN (National Knowledge Network) | Proxy: False
Scraped Content: "DA-IICT Intranet Login. Authorized Personnel Only. User ID. Password. Forgot Password? IT Helpdesk Extension: 4444."
Forensic Scan: Link: https://internal.daiict.ac.in/wiki/maintenance-schedule
Message: "Dear Faculty and Staff,
The central server room (Room B) will be undergoing scheduled maintenance on Sunday, Nov 30, from 2:00 AM to 4:00 AM IST.
**Services affected:**
1. Moodle (LMS)
2. Faculty Webmail
3. Student Portal
Please ensure all work is saved before this time. For the full maintenance schedule and alternative access points, please check the wiki:
https://internal.daiict.ac.in/wiki/maintenance-schedule
Regards,
IT Services"
**Correct Decision:**
{{
  "confidence": 5.0,
  "reasoning": "Legitimate. The sender domain, link domain, and network infrastructure (DA-IICT/NKN) all align perfectly. The scraped content matches an internal login page. The content is informational with specific details and lacks suspicious urgency or external hosting.",
  "highlighted_text": "The central server room (Room B) will be undergoing scheduled maintenance on Sunday. Please check the wiki: https://internal.daiict.ac.in/wiki/maintenance-schedule",
  "final_decision": "legitimate",
  "suggestion": "Safe internal communication regarding maintenance."
}}
**Example 5: Phishing (Legitimate Cloud Abuse - Google Forms)**
**Input:**
Sender: recruitment-officer.john.doe@gmail.com
Subject: Job Offer: Senior Python Developer - Document Upload
Technical Score: 60 / 100
Network Intelligence: Host: forms.gle (Google LLC)
Scraped Content: "Untitled Form. Job Application - Senior Dev. Upload your Passport Front and Back. Upload SSN Card. Upload Drivers License. Submit. Never submit passwords through Google Forms."
Forensic Scan: Link: https://forms.gle/xyz123abc
Message: "Dear Candidate,
Congratulations! We are pleased to offer you the Senior Python Developer position at TechSolutions Inc.
To proceed with your background check and contract generation, we need you to upload the following documents immediately:
1. Scanned Copy of Passport
2. Social Security Number (SSN) Card
3. Driver's License
Please upload them to our secure portal here:
[Link to Google Form]
We need this by EOD today."
**Correct Decision:**
{{
  "confidence": 92.0,
  "reasoning": "Phishing. Although the domain is legitimate (Google Forms), the Scraped Content reveals it is soliciting highly sensitive PII (Passport/SSN). Legitimate companies do not collect SSNs via public Google Forms. The use of a generic Gmail address for a 'Recruitment Officer' is also a red flag.",
  "highlighted_text": "To proceed with your background check... please @@upload the following documents immediately@@: 1. Scanned Copy of Passport 2. Social Security Number (SSN) Card. Please upload them to our secure portal here: @@[Link to Google Form]@@",
  "final_decision": "phishing",
  "suggestion": "Do not upload sensitive ID documents to public forms. This is likely identity theft."
}}
**Example 6: Legitimate (Transactional Alert)**
**Input:**
Sender: alerts@hdfcbank.net
Subject: Transaction Alert: INR 5,000.00 Debited
Technical Score: 8 / 100
Network Intelligence: Host: hdfcbank.net | Org: HDFC Bank Ltd | ISP: Sify Technologies
Scraped Content: N/A (No Links)
Forensic Scan: No URLs found.
Message: "Dear Customer,
INR 5,000.00 was debited from your A/c XX1234 on 28-Nov-2025.
**Info:** UPI-12345-AmazonPay
**Available Bal:** INR 42,000.00
If this transaction was not done by you, please call our 24x7 PhoneBanking number 1800-202-6161 immediately to block your card/account.
Warm Regards,
HDFC Bank"
**Correct Decision:**
{{
  "confidence": 2.0,
  "reasoning": "Legitimate. This is a standard text-only transactional alert. The sender domain matches HDFC Bank's official domain, and the network data confirms it. The phone number is a standard support line. There are no suspicious links.",
  "highlighted_text": "INR 5,000.00 was debited from your A/c XX1234 on 28-Nov-2025. Info: UPI-12345-AmazonPay.",
  "final_decision": "legitimate",
  "suggestion": "Safe transactional alert. No action needed unless the transaction is unrecognized."
}}
**Example 7: Phishing (CEO Fraud / BEC - No Links)**
**Input:**
Sender: ceo.work.private@gmail.com (Spoofed Name: "Elon Musk")
Subject: Urgent Task - Confidential - DO NOT IGNORE
Technical Score: 75 / 100
Network Intelligence: Host: mail.google.com (Google LLC)
Scraped Content: N/A
Forensic Scan: No URLs found.
Message: "Akshat,
I am currently in a closed-door meeting with the board of investors and cannot talk on the phone. I need a favor.
I need you to purchase 5 Apple Gift Cards ($100 each) for a client gift. It is urgent and needs to be done in the next 30 minutes. I will reimburse you personally by this evening.
Do not mention this to anyone else yet. Reply with the codes here as soon as you have them.
Elon."
**Correct Decision:**
{{
  "confidence": 90.0,
  "reasoning": "Phishing (BEC). Classic Business Email Compromise. The Sender is using a generic Gmail address to impersonate a C-level executive. The request involves financial urgency (Gift Cards), secrecy ('closed-door meeting', 'do not mention'), and bypasses standard procurement channels.",
  "highlighted_text": "I need you to @@purchase 5 Apple Gift Cards@@ ($100 each) for a client gift. It is urgent... @@Reply with the codes here@@ as soon as you have them.",
  "final_decision": "phishing",
  "suggestion": "Do not reply. Verify this request with the CEO via a different, verified channel (Slack/Phone/Corporate Email)."
}}
**Example 8: Legitimate (Marketing with Trackers)**
**Input:**
Sender: newsletter@coursera.org
Subject: Recommended for you: Python for Everybody Specialization
Technical Score: 20 / 100
Network Intelligence: Host: links.coursera.org | Org: Coursera Inc | ISP: Amazon.com
Scraped Content: "Coursera. Master Python. Enroll for Free. Starts Nov 29. Financial Aid available. Top Instructors. University of Michigan. 4.8 Stars (120k ratings)."
Forensic Scan: Link: https://links.coursera.org/track/click?id=12345&user=akshat
Message: "Hi Student,
Based on your interest in Data Science, we found a course you might like:
**Python for Everybody Specialization**
Offered by University of Michigan.
Start learning today and build job-ready skills.
[Enroll Now]
See you in class,
The Coursera Team
381 E. Evelyn Ave, Mountain View, CA 94041"
**Correct Decision:**
{{
  "confidence": 10.0,
  "reasoning": "Legitimate. Standard marketing email from a known education platform. Network data confirms the link tracking domain belongs to Coursera (hosted on AWS). Scraped content is consistent with the offer. Address matches public records.",
  "highlighted_text": "Based on your interest in Data Science, we found a course you might like: Python for Everybody Specialization. [Enroll Now]",
  "final_decision": "legitimate",
  "suggestion": "Safe marketing email."
}}"""
async def get_groq_decision(ensemble_result: Dict, network_data: List[Dict], landing_page_text: str, cleaned_text: str, original_raw_html: str, readable_display_text: str, sender: str, subject: str):
    net_str = "No Network Data"
    if network_data:
        net_str = "\n".join([
            f"- Host: {d.get('host')} | IP: {d.get('ip')} | Org: {d.get('org')} | ISP: {d.get('isp')} | Hosting/Proxy: {d.get('hosting') or d.get('proxy')}"
            for d in network_data
        ])
    log_step("", "Starting Forensic HTML Scan")
    forensic_report = []
    try:
        soup = BeautifulSoup(original_raw_html, 'html.parser')
        
        for form in soup.find_all('form'):
            action = form.get('action')
            if action:
                forensic_report.append(f"CRITICAL: Found URL in <form action>: {action}")
        
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                forensic_report.append(f"Found URL in <img src>: {src}")
                
        for a in soup.find_all('a'):
            href = a.get('href')
            if href:
                forensic_report.append(f"Found URL in <a href>: {href}")
        url_pattern = r'(?:https?://|ftp://|www\.)[\w\-\.]+\.[a-zA-Z]{2,}(?:/[\w\-\._~:/?#[\]@!$&\'()*+,;=]*)?'
        all_text_urls = set(re.findall(url_pattern, original_raw_html))
        if all_text_urls:
            forensic_report.append(f"All URLs detected in raw text: {', '.join(all_text_urls)}")
            
    except Exception as e:
        logger.warning(f"Forensic Scan Error: {e}")
        forensic_report.append("Forensic scan failed to parse HTML structure.")
    forensic_str = "\n".join(forensic_report) if forensic_report else "No URLs found in forensic scan."
    log_substep("Forensic Scan", f"Found {len(forensic_report)} potential indicators")
    prompt_display_text = readable_display_text[:MAX_INPUT_CHARS]
    
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
"{prompt_display_text}"
**TASK:**
Analyze the "FORENSIC URL SCAN" findings.
- If ANY URL in the forensic scan is NSFW/Adult or malicious, flag as PHISHING.
- If a URL looks like a generated subdomain (e.g. 643646.me) or is unrelated to the sender, FLAG AS PHISHING immediately.
- IMPORTANT: For the 'highlighted_text' field in your JSON response, use the **MESSAGE CONTENT (READABLE VERSION)** provided above. Do NOT output raw HTML tags. Just mark suspicious parts in the readable text with @@...@@.
"""

    attempts = 0
    while attempts < LLM_MAX_RETRIES:
        try:
            client = key_rotator.get_client_and_rotate()
            if not client:
                raise Exception("No Keys")
            
            log_step("", f"Sending LLM Request (Attempt {attempts+1}/{LLM_MAX_RETRIES})")
            
            completion = await client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                temperature=0.1,
                max_tokens=4096,
                response_format={"type": "json_object"}
            )
            raw_content = completion.choices[0].message.content
            log_substep("LLM Response Received", f"Length: {len(raw_content)} chars")
            
            parsed_json = clean_and_parse_json(raw_content)
            
            if parsed_json:
                log_success("LLM Response Parsed Successfully")
                return parsed_json
            else:
                raise ValueError("Empty or Invalid JSON from LLM")
        except RateLimitError as e:
            wait_time = 2 ** (attempts + 1) + random.uniform(0, 1)
            if hasattr(e, 'headers') and 'retry-after' in e.headers:
                try:
                    wait_time = float(e.headers['retry-after']) + 1
                except:
                    pass
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
        "highlighted_text": readable_display_text,
        "final_decision": "phishing" if is_phishing else "legitimate",
        "suggestion": "Exercise caution. Automated analysis detected risks." if is_phishing else "Appears safe."
    }
@app.on_event("startup")
async def startup():
    logger.info(f"\n{UltraColorFormatter.NEON_BLUE}{'='*70}")
    logger.info(f"{UltraColorFormatter.WHITE_BOLD}        PHISHING DETECTION API v2.6.0 - SYSTEM STARTUP        ".center(80))
    logger.info(f"{UltraColorFormatter.NEON_BLUE}{'='*70}{UltraColorFormatter.RESET}")
    load_models()
    logger.info(f"\n{UltraColorFormatter.NEON_GREEN} SYSTEM READY AND LISTENING ON PORT 8000{UltraColorFormatter.RESET}\n")
@app.post("/predict", response_model=PredictionResponse)
async def predict(input_data: MessageInput):
    log_section(f"NEW REQUEST: {input_data.sender}")
    
    if not input_data.text or not input_data.text.strip():
        logger.warning("Received empty input text.")
        return PredictionResponse(
            confidence=0.0,
            reasoning="Empty input.",
            highlighted_text="",
            final_decision="legitimate",
            suggestion="None"
        )
    async with request_semaphore:
        try:
            start_time = time.time()
            
            extracted_text, all_urls = extract_visible_text_and_links(input_data.text)
            
            url_pattern_for_cleaning = r'(?:https?://|ftp://|www\.)[\w\-\.]+\.[a-zA-Z]{2,}(?:/[\w\-\._~:/?#[\]@!$&\'()*+,;=]*)?'
            cleaned_text_for_models = re.sub(url_pattern_for_cleaning, '', extracted_text)
            cleaned_text_for_models = ' '.join(cleaned_text_for_models.lower().split())
            all_urls = all_urls[:MAX_URLS_TO_ANALYZE]
            if all_urls:
                log_step("", f"Proceeding with {len(all_urls)} URLs")
            else:
                log_step("", "No URLs Detected - Skipping Feature Extraction")
            features_df = pd.DataFrame()
            network_data_raw = []
            landing_page_text = ""
            if all_urls:
                log_step("", "Initiating Parallel Async Tasks")
                results = await asyncio.gather(
                    extract_url_features(all_urls),
                    get_network_data_raw(all_urls),
                    scrape_landing_page(all_urls)
                )
                features_df, network_data_raw, landing_page_text = results
            if isinstance(landing_page_text, dict):
                landing_page_text = "\n".join(f"{u}: {txt}" for u, txt in landing_page_text.items())
            else:
                landing_page_text = str(landing_page_text)
            
            predictions = await asyncio.to_thread(get_model_predictions, features_df, cleaned_text_for_models)
            ensemble_result = EnsembleScorer.calculate_technical_score(predictions, network_data_raw, all_urls)
            
            log_metric("Ensemble Technical Score", f"{ensemble_result['score']:.2f}/100", warning=ensemble_result['score']>50)
            llm_result = await get_groq_decision(
                ensemble_result,
                network_data_raw,
                landing_page_text,
                cleaned_text_for_models,
                input_data.text, 
                extracted_text,  
                input_data.sender,
                input_data.subject
            )
            final_dec = llm_result.get('final_decision', 'legitimate').lower()
            if final_dec not in ['phishing', 'legitimate']:
                final_dec = 'legitimate'
            
            elapsed = time.time() - start_time
            
            log_section("REQUEST COMPLETE")
            log_metric("Execution Time", f"{elapsed:.2f}s")
            log_metric("Technical Score", f"{ensemble_result['score']:.0f}")
            
            decision_color = UltraColorFormatter.BOLD_RED if final_dec == "phishing" else UltraColorFormatter.NEON_GREEN
            logger.info(f"     FINAL VERDICT: {decision_color}{final_dec.upper()}{UltraColorFormatter.RESET}")
            return PredictionResponse(
                confidence=float(llm_result.get('confidence', ensemble_result['score'])),
                reasoning=llm_result.get('reasoning', ensemble_result['details']),
                highlighted_text=llm_result.get('highlighted_text', extracted_text),
                final_decision=final_dec,
                suggestion=llm_result.get('suggestion', 'Check details carefully.')
            )
        except Exception as e:
            logger.error(f"CRITICAL FAILURE in Prediction Pipeline: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
