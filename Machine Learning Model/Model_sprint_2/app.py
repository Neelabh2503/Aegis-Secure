import os
import re
import json
import time
import sys
import asyncio
from typing import List, Dict, Optional
from urllib.parse import urlparse
import socket
import httpx
import uvicorn
import joblib
import torch
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import AsyncGroq
from dotenv import load_dotenv
from bs4 import BeautifulSoup

import config
from models import get_ml_models, get_dl_models, FinetunedBERT
from feature_extraction import process_row

load_dotenv()
sys.path.append(os.path.join(config.BASE_DIR, 'Message_model'))
from predict import PhishingPredictor

app = FastAPI(
    title="Phishing Detection API",
    description="Advanced phishing detection system using multiple ML/DL models and Groq",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MessageInput(BaseModel):
    sender: Optional[str] = ""
    subject: Optional[str] = ""
    text: str
    metadata: Optional[Dict] = {}

class PredictionResponse(BaseModel):
    confidence: float
    reasoning: str
    highlighted_text: str
    final_decision: str
    suggestion: str

ml_models = {}
dl_models = {}
bert_model = None
semantic_model = None
groq_async_client = None

MODEL_BOUNDARIES = {
    'logistic': 0.5,
    'svm': 0.5,
    'xgboost': 0.5,
    'attention_blstm': 0.5,
    'rcnn': 0.5,
    'bert': 0.5,
    'semantic': 0.5
}

def load_models():
    global ml_models, dl_models, bert_model, semantic_model, groq_async_client
    
    print("Loading models...")
    
    models_dir = config.MODELS_DIR
    for model_name in ['logistic', 'svm', 'xgboost']:
        model_path = os.path.join(models_dir, f'{model_name}.joblib')
        if os.path.exists(model_path):
            ml_models[model_name] = joblib.load(model_path)
            print(f"✓ Loaded {model_name} model")
        else:
            print(f"⚠ Warning: {model_name} model not found at {model_path}")
    
    for model_name in ['attention_blstm', 'rcnn']:
        model_path = os.path.join(models_dir, f'{model_name}.pt')
        if os.path.exists(model_path):
            model_template = get_dl_models(input_dim=len(config.NUMERICAL_FEATURES))
            dl_models[model_name] = model_template[model_name]
            dl_models[model_name].load_state_dict(torch.load(model_path, map_location='cpu'))
            dl_models[model_name].eval()
            print(f"✓ Loaded {model_name} model")
        else:
            print(f"⚠ Warning: {model_name} model not found at {model_path}")
    
    bert_path = os.path.join(config.BASE_DIR, 'finetuned_bert')
    if os.path.exists(bert_path):
        try:
            bert_model = FinetunedBERT(bert_path)
            print("✓ Loaded BERT model")
        except Exception as e:
            print(f"⚠ Warning: Could not load BERT model: {e}")
    
    semantic_model_path = os.path.join(config.BASE_DIR, 'Message_model', 'final_semantic_model')
    if os.path.exists(semantic_model_path) and os.listdir(semantic_model_path):
        try:
            semantic_model = PhishingPredictor(model_path=semantic_model_path)
            print("✓ Loaded semantic model")
        except Exception as e:
            print(f"⚠ Warning: Could not load semantic model: {e}")
    else:
        checkpoint_path = os.path.join(config.BASE_DIR, 'Message_model', 'training_checkpoints', 'checkpoint-30')
        if os.path.exists(checkpoint_path):
            try:
                semantic_model = PhishingPredictor(model_path=checkpoint_path)
                print("✓ Loaded semantic model from checkpoint")
            except Exception as e:
                print(f"⚠ Warning: Could not load semantic model from checkpoint: {e}")
    
    groq_api_key = os.environ.get('GROQ_API_KEY')
    if groq_api_key:
        groq_async_client = AsyncGroq(api_key=groq_api_key)
        print("✓ Initialized Groq API Client")
    else:
        print("⚠ Warning: GROQ_API_KEY not set. Set it as environment variable.")
        print("   Example: export GROQ_API_KEY='your-api-key-here'")

def extract_visible_text(html_body: str) -> str:
    soup = BeautifulSoup(html_body, 'html.parser')

    for tag in soup(["script", "style", "nav", "header", "footer", "link", "meta"]):
        tag.decompose()

    text = soup.get_text(separator=' ', strip=True)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def parse_message(text: str) -> tuple:
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+|(?:www\.)?[a-zA-Z0-9-]+\.[a-z]{2,12}\b(?:/[^\s]*)?'
    urls = re.findall(url_pattern, text)
    cleaned_text = re.sub(url_pattern, '', text)
    cleaned_text = ' '.join(cleaned_text.lower().split())
    cleaned_text = re.sub(r'[^a-z0-9\s.,!?-]', '', cleaned_text)
    cleaned_text = re.sub(r'([.,!?])+', r'\1', cleaned_text)
    cleaned_text = ' '.join(cleaned_text.split())
    return urls, cleaned_text

async def extract_url_features(urls: List[str]) -> pd.DataFrame:
    if not urls:
        return pd.DataFrame()
    
    df = pd.DataFrame({'url': urls})
    whois_cache = {}
    ssl_cache = {}
    
    tasks = []
    for _, row in df.iterrows():
        tasks.append(asyncio.to_thread(process_row, row, whois_cache, ssl_cache))
    
    feature_list = await asyncio.gather(*tasks)
    features_df = pd.DataFrame(feature_list)
    result_df = pd.concat([df, features_df], axis=1)
    return result_df

def custom_boundary(raw_score: float, boundary: float) -> float:
    return (raw_score - boundary) * 100

def get_model_predictions(features_df: pd.DataFrame, message_text: str) -> Dict:
    predictions = {}
    
    numerical_features = config.NUMERICAL_FEATURES
    categorical_features = config.CATEGORICAL_FEATURES
    
    if not features_df.empty:
        try:
            X = features_df[numerical_features + categorical_features]

            X.loc[:, numerical_features] = X.loc[:, numerical_features].fillna(-1)
            X.loc[:, categorical_features] = X.loc[:, categorical_features].fillna('N/A')

            for model_name, model in ml_models.items():
                try:
                    all_probas = model.predict_proba(X)[:, 1]  
                    raw_score = np.max(all_probas)      
                    
                    scaled_score = custom_boundary(raw_score, MODEL_BOUNDARIES[model_name])
                    predictions[model_name] = {
                        'raw_score': float(raw_score),
                        'scaled_score': float(scaled_score)
                    }
                except Exception as e:
                    print(f"Error with {model_name} (Prediction Step): {e}") 
            
            X_numerical = X[numerical_features].values 
            
            for model_name, model in dl_models.items():
                try:
                    X_tensor = torch.tensor(X_numerical, dtype=torch.float32)
                    with torch.no_grad():
                        all_scores = model(X_tensor)
                        raw_score = torch.max(all_scores).item()
                        
                    scaled_score = custom_boundary(raw_score, MODEL_BOUNDARIES[model_name])
                    predictions[model_name] = {
                        'raw_score': float(raw_score),
                        'scaled_score': float(scaled_score)
                    }
                except Exception as e:
                    print(f"Error with {model_name}: {e}")
        
        except KeyError as e:
            print(f"Error: Missing columns in features_df. {e}")
            print(f"Available columns: {features_df.columns.tolist()}")

        if bert_model:
            try:
                urls = features_df['url'].tolist()
                raw_scores = bert_model.predict_proba(urls)
                avg_raw_score = np.mean([score[1] for score in raw_scores])
                scaled_score = custom_boundary(avg_raw_score, MODEL_BOUNDARIES['bert'])
                predictions['bert'] = {
                    'raw_score': float(avg_raw_score),
                    'scaled_score': float(scaled_score)
                }
            except Exception as e:
                print(f"Error with BERT: {e}")
    
    if semantic_model and message_text:
        try:
            result = semantic_model.predict(message_text)
            raw_score = result['phishing_probability']
            scaled_score = custom_boundary(raw_score, MODEL_BOUNDARIES['semantic'])
            predictions['semantic'] = {
                'raw_score': float(raw_score),
                'scaled_score': float(scaled_score),
                'confidence': result['confidence']
            }
        except Exception as e:
            print(f"Error with semantic model: {e}")
    
    return predictions

async def get_network_features_for_gemini(urls: List[str]) -> str:
    if not urls:
        return "No URLs to analyze for network features."
    
    results = []
    async with httpx.AsyncClient() as client:
        for i, url_str in enumerate(urls[:3]): 
            try:
                hostname = urlparse(url_str).hostname
                if not hostname:
                    results.append(f"\nURL {i+1} ({url_str}): Invalid URL, no hostname.")
                    continue
                
                try:
                    ip_address = await asyncio.to_thread(socket.gethostbyname, hostname)
                except socket.gaierror:
                    results.append(f"\nURL {i+1} ({hostname}): Could not resolve domain to IP.")
                    continue
                
                try:
                    geo_url = f"http://ip-api.com/json/{ip_address}?fields=status,message,country,city,isp,org,as"
                    response = await client.get(geo_url, timeout=3.0)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data.get('status') == 'success':
                        geo_info = (
                            f"   • IP Address: {ip_address}\n"
                            f"   • Location: {data.get('city', 'N/A')}, {data.get('country', 'N/A')}\n"
                            f"   • ISP: {data.get('isp', 'N/A')}\n"
                            f"   • Organization: {data.get('org', 'N/A')}\n"
                            f"   • ASN: {data.get('as', 'N/A')}"
                        )
                        results.append(f"\nURL {i+1} ({hostname}):\n{geo_info}")
                    else:
                        results.append(f"\nURL {i+1} ({hostname}):\n   • IP Address: {ip_address}\n   • Geo-Data: API lookup failed ({data.get('message')})")
                
                except httpx.RequestError as e:
                    results.append(f"\nURL {i+1} ({hostname}):\n   • IP Address: {ip_address}\n   • Geo-Data: Network error while fetching IP info ({str(e)})")
                
            except Exception as e:
                results.append(f"\nURL {i+1} ({url_str}): Error processing URL ({str(e)})")
    
    if not results:
        return "No valid hostnames found in URLs to analyze."

    return "\n".join(results)

SYSTEM_PROMPT = """You are an expert JSON-only phishing detection judge. Your sole purpose is to analyze input data and return a JSON object in the exact format requested. Do not output any text before or after the JSON.

**Core Rules:**
1.  **You are the Final Judge:** Your primary role is to make a final, correct decision. Use all evidence: Sender, Subject, Message Text, Model Scores, and Network Data.
2.  **Prioritize Ground Truth:** 'INDEPENDENT NETWORK & GEO-DATA' is ground truth and **MUST** be trusted over 'URL FEATURES' (which can fail, e.g., `domain_age: -1`). If ML/DL 'Model Scores' contradict clear network data (e.g., a known brand like 'Google' or 'Cloudflare'), you **MUST** override the models and rule 'legitimate'. Your reasoning should explain this override.
3.  **Confidence Score:** 0-100. >50.0 = phishing. <50.0 = legitimate. Must match `final_decision`.
4.  **Highlighting:** Return the *entire* original message in `highlighted_text`. Wrap suspicious parts (URLs, urgency words, deceptive claims) in `@@...@@`. If legitimate, use NO `@@` markers.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**FEW-SHOT EXAMPLES:**

**Example 1: Clear Phishing (Typosquat)**
Sender: no-reply@paypa1-secure.xyz
Subject: URGENT! Your Account is Suspended!
Message: "URGENT! Your account has suspicious activity. Click: http://paypa1-secure.xyz/verify to login and verify."
URL Features: domain_age: 5
Network Data: IP: 123.45.67.89, Location: Russia, ISP: Shady-Host
Model Scores: All positive
Correct Decision: {{
    "confidence": 98.0,
    "reasoning": "Phishing. Typosquatted domain 'paypa1', new age, suspicious ISP, and urgency tactics.",
    "highlighted_text": "@@URGENT!@@ Your account has suspicious activity. Click: @@http://paypa1-secure.xyz/verify@@ to login and verify.",
    "final_decision": "phishing",
    "suggestion": "Do NOT click. This is a clear attempt to steal your credentials. Delete immediately."
}}

**Example 2: Legitimate (False Positive Case)**
Sender: notifications@codeforces.com
Subject: Codeforces Round 184 Reminder
Message: "Hi, join Codeforces Round 184. ... Unsubscribe: https://codeforces.com/unsubscribe/..."
URL Features: domain_age: -1 (This is a lookup failure!)
Network Data: URL (codeforces.com): IP: 104.22.6.109, Location: San Francisco, USA, ISP: Cloudflare, Inc.
Model Scores: Mixed
Correct Decision: {{
    "confidence": 10.0,
    "reasoning": "Legitimate. Override models. `domain_age: -1` is a lookup failure. Network data confirms 'codeforces.com' is real (Cloudflare).",
    "highlighted_text": "Hi, join Codeforces Round 184. ... Unsubscribe: https://codeforces.com/unsubscribe/...",
    "final_decision": "legitimate",
    "suggestion": "This message is safe. It is a legitimate notification from Codeforces."
}}

**Example 3: Legitimate (Formal Text)**
Sender: investor.relations@tatamotors.com
Subject: TATA MOTORS GENERAL GUIDANCE NOTE
Message: "TATA MOTORS PASSENGER VEHICLES LIMITED... GENERAL GUIDANCE NOTE... [TRUNCATED]"
URL Features: domain_age: 8414
Network Data: URL (cars.tatamotors.com): IP: 23.209.113.12, Location: Boardman, USA, ISP: Akamai
Model Scores: All negative
Correct Decision: {{
    "confidence": 5.0,
    "reasoning": "Legitimate. Formal corporate text. Network data confirms 'tatamotors.com' on Akamai. Models are correct.",
    "highlighted_text": "TATA MOTORS PASSENGER VEHICLES LIMITED... GENERAL GUIDANCE NOTE... [TRUNCATED]",
    "final_decision": "legitimate",
    "suggestion": "This message is a legitimate corporate communication and appears safe."
}}

**Example 4: No URL Phishing (Scam)**
Sender: it-support@yourcompany.org
Subject: Employee Appreciation Reward
Message: "To thank you for your hard work, please reply with your personal email address and mobile phone number to receive your $500 gift card."
URL Features: No URLs detected
Network Data: No URLs detected
Model Scores: semantic: positive
Correct Decision: {{
    "confidence": 85.0,
    "reasoning": "Phishing. No URL. This is a data harvesting scam. The sender is suspicious and is requesting sensitive personal information.",
    "highlighted_text": "To thank you for your hard work, @@please reply with your personal email address and mobile phone number@@ to receive your $500 gift card.",
    "final_decision": "phishing",
    "suggestion": "Do not reply. This is a scam to steal your personal information. Report this email to your IT department."
}}

**Example 5: Legitimate Transaction (No URL)**
Sender: VM-SBIUPI
Subject: N/A
Message: "Dear UPI user A/C X1243 debited by 16.0 on date 16Nov25 trf to Kuldevi Caterers Refno 532032534589 If not u? call-1800111109 for other services-18001234-SBI"
URL Features: No URLs detected
Network Data: No URLs detected
Model Scores: semantic: negative
Correct Decision: {{
    "confidence": 10.0,
    "reasoning": "Legitimate. This is a standard, informational banking transaction alert (UPI debit). It contains no URLs and the phone numbers appear to be standard toll-free support lines.",
    "highlighted_text": "Dear UPI user A/C X1243 debited by 16.0 on date 16Nov25 trf to Kuldevi Caterers Refno 532032534589 If not u? call-1800111109 for other services-18001234-SBI",
    "final_decision": "legitimate",
    "suggestion": "This message is a legitimate transaction alert and appears safe. No action is needed unless you do not recognize this transaction."
}}

**Example 6: Clear Phishing (Prize Scam)**
Sender: meta-rewards@hacker-round.com
Subject: hooray you have won a prize!!!
Message: "You have won Rs 5000 for the meta hacker round 2 , for getting into top 2500 click here to claim you prize : https:// www.dghjdgf.com/paypal.co.uk/cycgi-bin/webscrcmd=_home-customer&nav=1/loading.php"
URL Features: domain_age: 1, count_dot: 4, count_special_chars: 12
Network Data: URL (dghjdgf.com): IP: 1.2.3.4, Location: Unknown, ISP: Random-Host-Provider
Model Scores: All positive
Correct Decision: {{
    "confidence": 99.0,
    "reasoning": "Phishing. This is a classic prize scam. The URL is highly suspicious, using a random domain ('dghjdgf.com') to impersonate PayPal. The lure of money and call to action are clear phishing tactics.",
    "highlighted_text": "@@You have won Rs 5000 for the meta hacker round 2@@ , for getting into top 2500 @@click here to claim you prize : https:// www.dghjdgf.com/paypal.co.uk/cycgi-bin/webscrcmd=_home-customer&nav=1/loading.php@@",
    "final_decision": "phishing",
    "suggestion": "Do NOT click this link. This is a scam to steal your information. Delete this email immediately."
}}

**Example 7: Legitimate University Event (Internal)**
Sender: AI Club <ai_club@dau.ac.in>
Subject: Invitation to iPrompt ’25 & AI Triathlon — 15th November at iFest’25
Message: "Dear Students, The AI Club, DA-IICT, is delighted to invite you... Register: https://ifest25.vercel.app ... Participants’ WhatsApp Group: https://chat.whatsapp.com/EeJ1XeNxcgM7w7gVBjKjox ... Warm regards, AI Club, DA-IICT"
URL Features: domain_age: -1 (vercel.app), domain_age: 7500 (whatsapp.com)
Network Data: URL (ifest25.vercel.app): IP: 76.76.21.21, Location: USA, ISP: Vercel Inc. URL (chat.whatsapp.com): IP: 157.240.22.60, Location: USA, ISP: Meta Platforms, Inc.
Model Scores: Mixed (semantic: negative, some URL models might flag vercel.app)
Correct Decision: {{
    "confidence": 5.0,
    "reasoning": "Legitimate. This is an internal university announcement from a trusted sender domain (@dau.ac.in). The links to Vercel (common for student projects) and WhatsApp are legitimate and verified by network data.",
    "highlighted_text": "Dear Students, The AI Club, DA-IICT, is delighted to invite you... Register: https://ifest25.vercel.app ... Participants’ WhatsApp Group: https://chat.whatsapp.com/EeJ1XeNxcgM7w7gVBjKjox ... Warm regards, AI Club, DA-IICT",
    "final_decision": "legitimate",
    "suggestion": "This email is a safe internal announcement about a university event."
}}

**Example 8: Legitimate Corporate Policy Update**
Sender: YouTube <no-reply@youtube.com>
Subject: Annual reminder about YouTube’s Terms of Service, Community Guidelines and Privacy Policy
Message: "This email is an annual reminder that your use of YouTube is subject to the Terms of Service, Community Guidelines and Google’s Privacy Policy... © 2025 Google LLC, 1600 Amphitheatre Parkway, Mountain View, CA, 94043"
URL Features: domain_age: 10000+ (youtube.com, google.com)
Network Data: URL (youtube.com): IP: 142.250.196.222, Location: USA, ISP: Google LLC
Model Scores: All negative
Correct Decision: {{
    "confidence": 1.0,
    "reasoning": "Legitimate. This is a standard, text-heavy legal/policy notification from a trusted sender (@youtube.com). Network data confirms the domain belongs to Google. There is no suspicious call to action.",
    "highlighted_text": "This email is an annual reminder that your use of YouTube is subject to the Terms of Service, Community Guidelines and Google’s Privacy Policy... © 2025 Google LLC, 1600 Amphitheatre Parkway, Mountain View, CA, 94043",
    "final_decision": "legitimate",
    "suggestion": "This is a standard policy update from YouTube. It is safe."
}}

**Example 9: Legitimate Service Notification (Google)**
Sender: 2022 01224 (Classroom) <no-reply@classroom.google.com>
Subject: Due tomorrow: "Lab 09"
Message: "Aaditya_CT303 Due tomorrow Lab 09 Follow these instructions... View assignment Google LLC 1600 Amphitheatre Parkway, Mountain View, CA 94043 USA"
URL Features: domain_age: 10000+ (classroom.google.com)
Network Data: URL (classroom.google.com): IP: 142.250.196.206, Location: USA, ISP: Google LLC
Model Scores: All negative
Correct Decision: {{
    "confidence": 2.0,
    "reasoning": "Legitimate. This is an automated notification from Google Classroom. The sender (@classroom.google.com) and network data confirm it's a real Google service. The 'urgency' (Due tomorrow) is part of the service's function.",
    "highlighted_text": "Aaditya_CT303 Due tomorrow Lab 09 Follow these instructions... View assignment Google LLC 1600 Amphitheatre Parkway, Mountain View, CA 94043 USA",
    "final_decision": "legitimate",
    "suggestion": "This is a safe and legitimate assignment reminder from Google Classroom."
}}

**Example 10: Legitimate Internal Announcement (No URL)**
Sender: iFest DAU <ifest@dau.ac.in>
Subject: Instruction for i.Fest' 25
Message: "Hello everyone, As we all know, i.Fest’ 25 begins today! Here are some important guidelines... Entry will be permitted only with a valid Student ID card... Best Regards, Team i.Fest"
URL Features: No URLs detected
Network Data: No URLs detected
Model Scores: semantic: negative
Correct Decision: {{
    "confidence": 5.0,
    "reasoning": "Legitimate. This is a text-only informational email from a trusted internal university domain (@dau.ac.in). It contains instructions, not suspicious links or requests.",
    "highlighted_text": "Hello everyone, As we all know, i.Fest’ 25 begins today! Here are some important guidelines... Entry will be permitted only with a valid Student ID card... Best Regards, Team i.Fest",
    "final_decision": "legitimate",
    "suggestion": "This is a safe internal announcement for university students."
}}

**Example 11: Legitimate Marketing (Clickbait Subject)**
Sender: Jia from Unstop <noreply@dare2compete.news>
Subject: [Congrats] Intern with Panasonic - Earn a stipend of ₹35,000!
Message: "Hi Akshat, here are some top opportunities curated just for you! ... Software Engineering Internship Panasonic... Explore more Internships... © 2025 Unstop. All rights reserved."
URL Features: domain_age: 3000+ (dare2compete.news)
Network Data: URL (dare2compete.news): IP: 104.26.10.168, Location: USA, ISP: Cloudflare, Inc.
Model Scores: Mixed (Subject line '[Congrats]' might trigger semantic model)
Correct Decision: {{
    "confidence": 15.0,
    "reasoning": "Legitimate. Although the subject line '[Congrats]' is clickbait, the sender domain ('dare2compete.news') is established and network data (Cloudflare) checks out. The content is a standard job/internship digest from a known platform.",
    "highlighted_text": "Hi Akshat, here are some top opportunities curated just for you! ... Software Engineering Internship Panasonic... Explore more Internships... © 2025 Unstop. All rights reserved.",
    "final_decision": "legitimate",
    "suggestion": "This is a legitimate promotional email from Unstop. It is safe."
}}

**Example 12: Legitimate Marketing (SaaS)**
Sender: Numerade <ace@email.numerade.com>
Subject: Your All-In-One Finals Prep Toolkit
Message: "Finals can be overwhelming. Numerade’s textbook solutions give you instant access to step-by-step explanations... Find Your Textbook Answers ... © 2025, Numerade, All rights reserved."
URL Features: domain_age: 2000+ (email.numerade.com)
Network Data: URL (email.numerade.com): IP: 149.72.215.153, Location: USA, ISP: SendGrid, Inc.
Model Scores: All negative
Correct Decision: {{
    "confidence": 8.0,
    "reasoning": "Legitimate. This is a standard marketing email from a known company (Numerade) sent via a reputable email service (SendGrid), as confirmed by network data. It has clear unsubscribe links and branding.",
    "highlighted_text": "Finals can be overwhelming. Numerade’s textbook solutions give you instant access to step-by-step explanations... Find Your Textbook Answers ... © 2025, Numerade, All rights reserved.",
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

async def get_groq_final_decision(urls: List[str], features_df: pd.DataFrame, 
                                  message_text: str, predictions: Dict, 
                                  original_text: str,
                                  sender: Optional[str] = "",
                                  subject: Optional[str] = "") -> Dict:
    
    if not groq_async_client:
        avg_scaled_score = np.mean([p['scaled_score'] for p in predictions.values()]) if predictions else 0
        confidence = min(100, max(0, 50 + avg_scaled_score))
        final_decision = "phishing" if confidence > 50 else "legitimate"
        
        return {
            "confidence": round(confidence, 2),
            "reasoning": f"Groq API not available. Using average model scores. (Avg Scaled Score: {avg_scaled_score:.2f})",
            "highlighted_text": original_text,
            "final_decision": final_decision,
            "suggestion": "Do not interact with this message. Delete it immediately and report it to your IT department." if final_decision == "phishing" else "This message appears safe, but remain cautious with any links or attachments."
        }
    
    url_features_summary = "No URLs detected in message"
    if not features_df.empty:
        feature_summary_parts = []
        for idx, row in features_df.iterrows():
            url = row.get('url', 'Unknown')
            feature_summary_parts.append(f"\nURL {idx+1}: {url}")
            feature_summary_parts.append(f"   • Length: {row.get('url_length', 'N/A')} chars")
            feature_summary_parts.append(f"   • Dots in URL: {row.get('count_dot', 'N/A')}")
            feature_summary_parts.append(f"   • Special characters: {row.get('count_special_chars', 'N/A')}")
            feature_summary_parts.append(f"   • Domain age: {row.get('domain_age_days', 'N/A')} days")
            feature_summary_parts.append(f"   • SSL certificate valid: {row.get('cert_has_valid_hostname', 'N/A')}")
            feature_summary_parts.append(f"   • Uses HTTPS: {row.get('https', 'N/A')}")
        url_features_summary = "\n".join(feature_summary_parts)

    network_features_summary = await get_network_features_for_gemini(urls)
    
    model_predictions_summary = []
    for model_name, pred_data in predictions.items():
        scaled = pred_data['scaled_score']
        raw = pred_data['raw_score']
        model_predictions_summary.append(
            f"   • {model_name.upper()}: scaled_score={scaled:.2f} (raw={raw:.3f})"
        )
    model_scores_text = "\n".join(model_predictions_summary)
    
    MAX_TEXT_LEN = 3000
    if len(original_text) > MAX_TEXT_LEN:
        truncated_original_text = original_text[:MAX_TEXT_LEN] + "\n... [TRUNCATED]"
    else:
        truncated_original_text = original_text

    if len(message_text) > MAX_TEXT_LEN:
        truncated_message_text = message_text[:MAX_TEXT_LEN] + "\n... [TRUNCATED]"
    else:
        truncated_message_text = message_text

    user_prompt = f"""MESSAGE DATA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sender: {sender if sender else 'N/A'}
Subject: {subject if subject else 'N/A'}

Original Message (Parsed from HTML):
{truncated_original_text}

Cleaned Text (for models):
{truncated_message_text}

URLs Found: {', '.join(urls) if urls else 'None'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

URL FEATURES (from ML models):
{url_features_summary}

INDEPENDENT NETWORK & GEO-DATA (for Gemini analysis only):
{network_features_summary}

MODEL PREDICTIONS:
(Positive scaled scores → phishing, Negative → legitimate. Range: -50 to +50)
{model_scores_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Please analyze this data and provide your JSON response."""
    
    try:
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                chat_completion = await groq_async_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT,
                        },
                        {
                            "role": "user",
                            "content": user_prompt,
                        }
                    ],
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    temperature=0.2,
                    max_tokens=4096, 
                    top_p=0.85,
                    response_format={"type": "json_object"},
                )
                
                response_text = chat_completion.choices[0].message.content
                break

            except Exception as retry_error:
                print(f"Groq API attempt {attempt + 1} failed: {retry_error}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay) 
                    retry_delay *= 2
                else:
                    raise retry_error

        result = json.loads(response_text)
        
        required_fields = ['confidence', 'reasoning', 'highlighted_text', 'final_decision', 'suggestion']
        if not all(field in result for field in required_fields):
            raise ValueError(f"Missing required fields. Got: {list(result.keys())}")
        
        result['confidence'] = float(result['confidence'])
        if not 0 <= result['confidence'] <= 100:
            result['confidence'] = max(0, min(100, result['confidence']))
        
        if result['final_decision'].lower() not in ['phishing', 'legitimate']:
            result['final_decision'] = 'phishing' if result['confidence'] > 50 else 'legitimate'
        else:
            result['final_decision'] = result['final_decision'].lower()
        
        if result['final_decision'] == 'phishing' and result['confidence'] < 50:
            print(f"Warning: Groq decision 'phishing' mismatches confidence {result['confidence']}. Adjusting confidence.")
            result['confidence'] = 51.0
        elif result['final_decision'] == 'legitimate' and result['confidence'] > 50:
            print(f"Warning: Groq decision 'legitimate' mismatches confidence {result['confidence']}. Adjusting confidence.")
            result['confidence'] = 49.0
            
        if not result['highlighted_text'].strip() or '...' in result['highlighted_text'] or 'TRUNCATED' in result['highlighted_text']:
            print("Warning: Groq returned empty or truncated 'highlighted_text'. Falling back to original_text.")
            result['highlighted_text'] = original_text
        
        if not result.get('suggestion', '').strip():
            if result['final_decision'] == 'phishing':
                result['suggestion'] = "Do not interact with this message. Delete it immediately and report it as phishing."
            else:
                result['suggestion'] = "This message appears safe, but always verify sender identity before taking any action."
        
        return result
    
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response text that failed parsing: {response_text[:500]}")
        
        avg_scaled_score = np.mean([p['scaled_score'] for p in predictions.values()]) if predictions else 0
        confidence = min(100, max(0, 50 + avg_scaled_score))
        final_decision = "phishing" if confidence > 50 else "legitimate"
        
        return {
            "confidence": round(confidence, 2),
            "reasoning": f"Groq response parsing failed. Fallback: Based on model average (directional score: {confidence:.2f}), message appears {'suspicious' if final_decision == 'phishing' else 'legitimate'}.",
            "highlighted_text": original_text,
            "final_decision": final_decision,
            "suggestion": "Do not interact with this message. Delete it immediately and be cautious." if final_decision == 'phishing' else "Exercise caution. Verify the sender before taking any action."
        }
    
    except Exception as e:
        print(f"Error with Groq API: {e}")
        
        avg_scaled_score = np.mean([p['scaled_score'] for p in predictions.values()]) if predictions else 0
        confidence = min(100, max(0, 50 + avg_scaled_score))
        final_decision = "phishing" if confidence > 50 else "legitimate"
        
        return {
            "confidence": round(confidence, 2),
            "reasoning": f"Groq API error: {str(e)}. Fallback decision based on {len(predictions)} model predictions (average directional score: {confidence:.2f}).",
            "highlighted_text": original_text,
            "final_decision": final_decision,
            "suggestion": "Treat this message with caution. Delete it if suspicious, or verify the sender through official channels before taking action." if final_decision == 'phishing' else "This message appears safe based on models, but always verify sender identity before clicking links or providing information."
        }

@app.on_event("startup")
async def startup_event():
    load_models()
    print("\n" + "="*60)
    print("Phishing Detection API is ready!")
    print("="*60)
    print("API Documentation: http://localhost:8000/docs")
    print("="*60 + "\n")

@app.get("/")
async def root():
    return {
        "message": "Phishing Detection API",
        "version": "1.0.0",
        "endpoints": {
            "predict": "/predict (POST)",
            "health": "/health (GET)",
            "docs": "/docs (GET)"
        }
    }

@app.get("/health")
async def health_check():
    models_loaded = {
        "ml_models": list(ml_models.keys()),
        "dl_models": list(dl_models.keys()),
        "bert_model": bert_model is not None,
        "semantic_model": semantic_model is not None,
        "groq_client": groq_async_client is not None
    }
    
    return {
        "status": "healthy",
        "models_loaded": models_loaded
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict(message_input: MessageInput):
    try:
        html_body = message_input.text
        sender = message_input.sender
        subject = message_input.subject
        
        original_text = extract_visible_text(html_body)
        
        if not original_text or not original_text.strip():
            raise HTTPException(status_code=400, detail="Message text (after HTML parsing) cannot be empty")
        
        urls, cleaned_text = parse_message(original_text)
        
        features_df = pd.DataFrame()
        if urls:
            features_df = await extract_url_features(urls)
        
        predictions = {}
        if not features_df.empty or (cleaned_text and semantic_model):
            predictions = await asyncio.to_thread(get_model_predictions, features_df, cleaned_text)
        
        if not predictions:
            if not urls and not cleaned_text:
                detail = "Message text is empty after cleaning."
            elif not urls and not semantic_model:
                detail = "No URLs provided and semantic model is not loaded."
            elif not any([ml_models, dl_models, bert_model, semantic_model]):
                    detail = "No models available for prediction. Please ensure models are trained and loaded."
            else:
                detail = "Could not generate predictions. Models may be missing or feature extraction failed."
            
            raise HTTPException(
                status_code=500, 
                detail=detail
            )
        
        final_result = await get_groq_final_decision(
            urls, features_df, cleaned_text, predictions, original_text,
            sender, subject
        )
        
        return PredictionResponse(**final_result)
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
