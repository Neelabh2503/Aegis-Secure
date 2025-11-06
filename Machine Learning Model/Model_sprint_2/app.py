import os
import re
import json
import time
import sys
import asyncio
from urllib.parse import urlparse
from typing import List, Dict, Optional

import joblib
import torch
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

import config
from models import get_ml_models, get_dl_models, FinetunedBERT
from feature_extraction import process_row

load_dotenv()
sys.path.append(os.path.join(config.BASE_DIR, 'Message_model'))
from predict import PhishingPredictor

app = FastAPI(
    title="Phishing Detection API",
    description="Advanced phishing detection system using multiple ML/DL models and Gemini AI",
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
gemini_model = None

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
    global ml_models, dl_models, bert_model, semantic_model, gemini_model
    
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
    
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        print("✓ Initialized Gemini API")
    else:
        print("⚠ Warning: GEMINI_API_KEY not set. Set it as environment variable.")
        print("   Example: export GEMINI_API_KEY='your-api-key-here'")

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
    
    try:
        X = features_df[numerical_features + categorical_features]
    except KeyError as e:
        print(f"Error: Missing columns in features_df. {e}")
        print(f"Available columns: {features_df.columns.tolist()}")
        return {}
    
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
    
    if bert_model and len(features_df) > 0:
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

async def get_gemini_final_decision(urls: List[str], features_df: pd.DataFrame, 
                                    message_text: str, predictions: Dict, 
                                    original_text: str) -> Dict:
    
    if not gemini_model:
        avg_scaled_score = np.mean([p['scaled_score'] for p in predictions.values()])
        confidence = min(100, max(0, 50 + abs(avg_scaled_score)))
        
        return {
            "confidence": round(confidence, 2),
            "reasoning": "Gemini API not available. Using average model scores.",
            "highlighted_text": original_text,
            "final_decision": "phishing" if avg_scaled_score > 0 else "legitimate",
            "suggestion": "Do not interact with this message. Delete it immediately and report it to your IT department." if avg_scaled_score > 0 else "This message appears safe, but remain cautious with any links or attachments."
        }
    
    url_features_summary = "No URLs detected in message"
    has_urls = len(features_df) > 0
    
    if has_urls:
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
    
    model_predictions_summary = []
    for model_name, pred_data in predictions.items():
        scaled = pred_data['scaled_score']
        raw = pred_data['raw_score']
        model_predictions_summary.append(
            f"   • {model_name.upper()}: scaled_score={scaled:.2f} (raw={raw:.3f})"
        )
    model_scores_text = "\n".join(model_predictions_summary)
    
    analysis_focus = ""
    if has_urls:
        analysis_focus = """
PRIORITY: URL-BASED ANALYSIS
Since URLs are present, focus heavily on URL features and characteristics:
- Examine domain reputation, age, SSL certificates
- Look for suspicious URL patterns (IP addresses, unusual TLDs, excessive special chars)
- Check for URL obfuscation techniques or shortened links
- Consider the ML model scores for URL-based features
- Then supplement with message content analysis
"""
    else:
        analysis_focus = """
PRIORITY: SEMANTIC/CONTENT ANALYSIS
No URLs detected. Focus entirely on message content and semantics:
- Analyze language patterns, urgency tactics, and social engineering techniques
- Look for credential requests, financial solicitations, or threats
- Check for impersonation attempts, spelling errors, or grammatical issues
- Evaluate the semantic model's assessment heavily
- Consider overall message intent and context
"""

    context = f"""You are the FINAL JUDGE in a phishing detection system. Your role is critical: analyze ALL available evidence and make the ultimate decision.

IMPORTANT INSTRUCTIONS:
1. You have FULL AUTHORITY to override model predictions if evidence suggests they're wrong
2. If models predict phishing but message appears legitimate, YOU CAN classify it as legitimate
3. If models predict legitimate but you detect phishing indicators, YOU CAN classify it as phishing
4. Your confidence score (0-100) should reflect certainty:
   - 0-30: Very likely legitimate
   - 30-50: Probably legitimate but some concerns
   - 50-70: Suspicious, possibly phishing
   - 70-90: Likely phishing
   - 90-100: Definitely phishing
5. BE WARY OF FALSE POSITIVES. Legitimate messages (especially from banks or marketing) can mimic phishing tactics.
   - **Bank Alerts:** Often use URGENT language ("Not you? Call...") as a REAL security feature. This is not phishing if it directs to a known number and doesn't ask for credentials via a link.
   - **Marketing Links:** Often use link shorteners (e.g., bit.ly, t.co, mnge.co). A new or "unknown" domain (like age -1) for a link shortener is not, by itself, proof of phishing. Evaluate the *context* of the message (is it a known brand? is it just an offer?).

{analysis_focus}

MESSAGE DATA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Original Message:
{original_text}

Cleaned Text:
{message_text}

URLs Found: {', '.join(urls) if urls else 'None'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

URL FEATURES & ANALYSIS:
{url_features_summary}

MODEL PREDICTIONS:
(Positive scaled scores → phishing, Negative → legitimate)
{model_scores_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FEW-SHOT EXAMPLES FOR GUIDANCE:

Example 1 - Clear Phishing:
Message: "URGENT! Your account will be suspended. Click here immediately: http://paypa1-secure.xyz/verify"
URL Features: New domain (5 days old), no SSL, misspelled brand, excessive urgency
Model Scores: All positive (phishing indicators)
Correct Decision: {{
  "confidence": 95.0,
  "reasoning": "Classic phishing attempt. Domain mimics PayPal with character substitution (1 for l), newly registered domain with no SSL certificate, and urgent language designed to bypass critical thinking. All models correctly identified threat.",
  "highlighted_text": "$$URGENT$$! Your account will be suspended. Click here immediately: $$http://paypa1-secure.xyz/verify$$",
  "final_decision": "phishing",
  "suggestion": "Do NOT click any links. Delete this message immediately. If you have a PayPal account, log in directly through the official PayPal website or app (not through this link) to check your account status. Report this phishing attempt to PayPal's security team."
}}

Example 2 - Legitimate Message:
Message: "Hi John, here's the meeting notes from today: https://docs.google.com/document/d/abc123"
URL Features: Established domain (8000+ days), valid SSL, legitimate Google domain
Model Scores: Mixed or slightly negative (legitimate indicators)
Correct Decision: {{
  "confidence": 15.0,
  "reasoning": "Legitimate message sharing Google Docs link. Domain is authentic Google property with proper SSL, no urgency tactics, normal conversational tone, and context suggests genuine communication.",
  "highlighted_text": "Hi John, here's the meeting notes from today: https://docs.google.com/document/d/abc123",
  "final_decision": "legitimate",
  "suggestion": "This message appears safe. You can click the link if you're expecting meeting notes from this sender. Verify the sender's identity if you have any doubts."
}}

Example 3 - Overriding Models (Models Wrong - Actually Legitimate):
Message: "Congratulations! You've been selected for our customer appreciation program. Reply to claim your reward."
URL Features: No URLs present
Model Scores: Some positive scores (false phishing detection)
Correct Decision: {{
  "confidence": 35.0,
  "reasoning": "While models flagged this due to words like 'congratulations' and 'reward', there are NO URLs, no credential requests, no pressure tactics, and no suspicious links. This appears to be a standard marketing message. OVERRIDING models - classifying as legitimate with low confidence due to marketing language.",
  "final_decision": "legitimate",
  "suggestion": "While this appears to be a legitimate marketing message, be cautious about replying or sharing personal information. If interested, research the company independently before responding."
}}

Example 4 - Overriding Models (Models Wrong - Actually Phishing):
Message: "Hello, we noticed unusual activity. Please confirm your details at our secure portal."
URL Features: URL present but models scored negative (missed it)
Model Scores: Mostly negative (missed the threat)
Correct Decision: {{
  "confidence": 78.0,
  "reasoning": "OVERRIDING models. Despite negative scores, this exhibits classic phishing: vague 'unusual activity' claim, requests personal details, creates false urgency. Models likely missed subtle social engineering. The phrase 'confirm your details' is a red flag.",
  "highlighted_text": "Hello, we noticed $$unusual activity$$. Please $$confirm your details$$ at our secure portal.",
  "final_decision": "phishing",
  "suggestion": "Do NOT click any links or provide any information. Delete this message immediately. If you're concerned about your account security, contact the company directly using official contact information from their verified website (not from this message)."
}}

Example 5 - No URLs, Pure Semantic Analysis:
Message: "Hey! Just wanted to share that I found a great deal on those shoes you wanted!"
URL Features: No URLs
Model Scores: Semantic model shows negative (legitimate)
Correct Decision: {{
  "confidence": 10.0,
  "reasoning": "Casual, friendly message with no URLs, no requests for information, no urgency, no threats. Semantic analysis confirms natural conversational language. This is normal personal communication.",
  "highlighted_text": "Hey! Just wanted to share that I found a great deal on those shoes you wanted!",
  "final_decision": "legitimate",
  "suggestion": "This appears to be a safe personal message. You can respond normally if you recognize the sender."
}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

YOUR ANALYSIS TASK:
Analyze the message data above following these steps:
1. Review all model predictions but DON'T blindly trust them
2. Examine URL features if present (domain age, SSL, suspicious patterns)
3. Analyze message content (urgency, threats, requests, impersonation)
4. Look for phishing indicators: urgency, fear, promises, credential harvesting
5. Make YOUR OWN independent judgment
6. Calculate confidence score (0-100 float)
7. Provide clear reasoning for your decision
8. Highlight suspicious parts with $$text$$ markers
9. Give final decision: "phishing" or "legitimate"
10. Provide actionable suggestion for the user based on your decision

OUTPUT FORMAT (respond with ONLY this JSON, no markdown, no explanation):
{{
  "confidence": <float 0-100>,
  "reasoning": "<your detailed analysis explaining why this is/isn't phishing>",
  "highlighted_text": "<original message with suspicious parts marked as $$suspicious text$$>",
  "final_decision": "phishing" or "legitimate",
  "suggestion": "<specific, actionable advice for the user on how to handle this message - what to do or not do>"
}}"""

    try:
        generation_config = {
            'temperature': 0.2,
            'top_p': 0.85,
            'top_k': 40,
            'max_output_tokens': 1024,
        }
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = await gemini_model.generate_content_async(
                    context,
                    generation_config=generation_config
                )
                break
            except Exception as retry_error:
                if attempt < max_retries - 1:
                    print(f"Gemini API attempt {attempt + 1} failed: {retry_error}. Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay) 
                    retry_delay *= 2
                else:
                    raise retry_error
        
        response_text = response.text.strip()
        
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        if not response_text.startswith('{'):
            import re
            json_match = re.search(r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
            else:
                raise ValueError(f"Could not find JSON in Gemini response: {response_text[:200]}")
        
        result = json.loads(response_text)
        
        required_fields = ['confidence', 'reasoning', 'highlighted_text', 'final_decision', 'suggestion']
        if not all(field in result for field in required_fields):
            raise ValueError(f"Missing required fields. Got: {list(result.keys())}")
        
        result['confidence'] = float(result['confidence'])
        if not 0 <= result['confidence'] <= 100:
            result['confidence'] = max(0, min(100, result['confidence']))
        
        if result['final_decision'].lower() not in ['phishing', 'legitimate']:
            result['final_decision'] = 'phishing' if result['confidence'] >= 50 else 'legitimate'
        else:
            result['final_decision'] = result['final_decision'].lower()
        
        if not result['highlighted_text'].strip():
            result['highlighted_text'] = original_text
        
        if not result.get('suggestion', '').strip():
            if result['final_decision'] == 'phishing':
                result['suggestion'] = "Do not interact with this message. Delete it immediately and report it as phishing."
            else:
                result['suggestion'] = "This message appears safe, but always verify sender identity before taking any action."
        
        return result
    
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response text: {response_text[:500]}")
        avg_scaled_score = np.mean([p['scaled_score'] for p in predictions.values()]) if predictions else 0
        confidence = min(100, max(0, 50 + abs(avg_scaled_score)))
        
        return {
            "confidence": round(confidence, 2),
            "reasoning": f"Gemini response parsing failed. Fallback: Based on model average (score: {avg_scaled_score:.2f}), message appears {'suspicious' if avg_scaled_score > 0 else 'legitimate'}.",
            "highlighted_text": original_text,
            "final_decision": "phishing" if avg_scaled_score > 0 else "legitimate",
            "suggestion": "Do not interact with this message. Delete it immediately and be cautious." if avg_scaled_score > 0 else "Exercise caution. Verify the sender before taking any action."
        }
    
    except Exception as e:
        print(f"Error with Gemini API: {e}")
        avg_scaled_score = np.mean([p['scaled_score'] for p in predictions.values()]) if predictions else 0
        confidence = min(100, max(0, 50 + abs(avg_scaled_score)))
        
        return {
            "confidence": round(confidence, 2),
            "reasoning": f"Gemini API error: {str(e)}. Fallback decision based on {len(predictions)} model predictions (average score: {avg_scaled_score:.2f}).",
            "highlighted_text": original_text,
            "final_decision": "phishing" if avg_scaled_score > 0 else "legitimate",
            "suggestion": "Treat this message with caution. Delete it if suspicious, or verify the sender through official channels before taking action." if avg_scaled_score > 0 else "This message appears safe based on models, but always verify sender identity before clicking links or providing information."
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
        "gemini_model": gemini_model is not None
    }
    
    return {
        "status": "healthy",
        "models_loaded": models_loaded
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict(message_input: MessageInput):
    try:
        original_text = message_input.text
        
        if not original_text or not original_text.strip():
            raise HTTPException(status_code=400, detail="Message text cannot be empty")
        
        urls, cleaned_text = parse_message(original_text)
        
        features_df = pd.DataFrame()
        if urls:
            features_df = await extract_url_features(urls)
        
        predictions = {}
        if len(features_df) > 0:
            predictions = await asyncio.to_thread(get_model_predictions, features_df, cleaned_text)
        elif cleaned_text:
            if semantic_model:
                result = await asyncio.to_thread(semantic_model.predict, cleaned_text)
                raw_score = result['phishing_probability']
                scaled_score = custom_boundary(raw_score, MODEL_BOUNDARIES['semantic'])
                predictions['semantic'] = {
                    'raw_score': float(raw_score),
                    'scaled_score': float(scaled_score),
                    'confidence': result['confidence']
                }
        
        if not predictions:
            if cleaned_text and not semantic_model:
                detail = "No URLs provided and semantic model is not loaded."
            else:
                detail = "No models available for prediction. Please ensure models are trained and loaded."
            
            raise HTTPException(
                status_code=500, 
                detail=detail
            )
        
        final_result = await get_gemini_final_decision(
            urls, features_df, cleaned_text, predictions, original_text
        )
        
        return PredictionResponse(**final_result)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)