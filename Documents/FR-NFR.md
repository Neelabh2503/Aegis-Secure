  
**Functional Requirements (FR)**

### **FR-001 — Scam Detection**

* Description: Analyze input (URLs / message text) and classify as *Safe* or *Scam*, returning a confidence score (0–100) and a one-line plain-language explanation.

* Elicitation techniques used: Interviews, Surveys, Brainstorming.

* How the techniques produced the requirement: Interviews gave real scam examples and user demand for clear explanations; surveys confirmed broad need for automated detection and confidence scores; brainstorming translated these into a concrete output format (label, confidence, explanation).

### **FR-002 — Result Dashboard**

* Description: Provide a dashboard listing recent scans with timestamp, risk category (Low/Med/High), confidence score, and brief explanation; support basic sorting and filtering.

* Elicitation techniques used: Interviews, Surveys, Brainstorming.

* How the techniques produced the requirement: Interviews showed users want an at-a-glance summary; surveys validated which fields are important; brainstorming defined the dashboard columns and filter/sort behavior.

### **FR-003 — Manual Input (Ad-hoc Scan)**

* Description: Allow users to paste or type suspicious text/URLs and trigger an immediate scan; validate input (reject empty submissions).

* Elicitation techniques used: Interviews, Surveys, Brainstorming.

* How the techniques produced the requirement: Interviews revealed copy-paste scanning is common; surveys confirmed it as a priority; brainstorming specified validation rules and UI placement.

### **FR-004 — SMS / Email Integration (Permissioned)**

* Description: Integrate with user SMS/email only after explicit consent; enable reading of incoming messages for scanning when permission is granted; allow revoke and log access.

* Elicitation techniques used: Interviews, Surveys, Brainstorming.

* How the techniques produced the requirement: Interviews emphasised privacy and consent; surveys showed conditional acceptance; brainstorming produced the grant/revoke workflow and audit logging requirement.

### **FR-005 — Auto Scanning Service (Background)**

* Description: Run a background service that automatically scans new messages and triggers alerts/notifications for suspicious content.

* Elicitation techniques used: Interviews, Surveys, Brainstorming.

* How the techniques produced the requirement: Interviews captured the desire to avoid manual scans; surveys supported background automation if privacy is respected; brainstorming converted this into a background-job design and notification policy.

### **FR-006 — User Feedback Loop**

* Description: Allow users to mark flagged items as *Scam* or *Safe* (with optional comment); store feedback linked to the original scan for model improvement.

* Elicitation techniques used: Interviews, Brainstorming.

* How the techniques produced the requirement: Interviews showed users want correction ability; brainstorming specified linkage to scan records and an exportable feedback format for retraining.

### **FR-007 — Push Notifications**

* Description: Deliver push notifications for flagged threats that include the label, confidence score, and a visual severity cue (color); allow deep-link to the detailed view.

* Elicitation techniques used: Interviews, Surveys, Brainstorming.

* How the techniques produced the requirement: Interviews defined useful notification content; surveys confirmed the need for immediate alerts; brainstorming specified payload structure and deep-link behavior.

### **FR-008 — Secure User Registration & Verification**

* Description: Provide signup/login via email (phone optional); enforce password strength (min. 8 chars, mixed types); verify accounts via email/SMS; prevent duplicate registrations.

* Elicitation techniques used: Brainstorming.

* How the techniques produced the requirement: Brainstorming defined enforceable password and verification rules plus duplicate checks.

### **FR-009 — Settings & Account Preferences**

* Description: Provide user-configurable settings for notifications, language, and scanning behavior; persist preferences per account.

* Elicitation techniques used: Interviews, Surveys, Brainstorming.

* How the techniques produced the requirement: Interviews identified which preferences users need; surveys confirmed expectation of persistence; brainstorming defined storage and UI placement.

### **FR-010 — Multilingual Analysis (Detection)**

* Description: Detect and classify messages in multiple languages (initial set based on user need); if unsupported, present clear “unsupported language” feedback.

* Elicitation techniques used: Interviews, Surveys, Brainstorming.

* How the techniques produced the requirement: Interviews with multilingual users showed the need; surveys identified priority languages; brainstorming set initial scope and fallback messaging.

### **FR-011 — Summary Screen & History**

* Description: Maintain a timestamped history of scans and present a summary visualization (pie chart) of classification distribution over selectable time ranges.

* Elicitation techniques used: Interviews, Surveys, Brainstorming.

* How the techniques produced the requirement: Interviews expressed need to audit past alerts; surveys supported visualization; brainstorming defined history schema and chart requirements.

### **FR-012 — Multilingual App UI**

* Description: Localize UI text and notifications to the user’s selected language and detect preferred language on first-run where feasible.

* Elicitation techniques used: Interviews, Surveys, Brainstorming.

* How the techniques produced the requirement: Interviews emphasised full UI localization; surveys reinforced expectation for localized notifications/explanations; brainstorming defined detection and runtime translation strategy.

# **Non-Functional Requirements (NFR)**

### **NFR-001 — Privacy & Data Minimization (Anonymous)**

* Description: By default do not store raw message bodies; store only analysis metadata (label, confidence, explanation, timestamp). Raw messages may be stored only with explicit user opt-in and an auditable flag.

* Elicitation techniques used: Interviews, Surveys, Brainstorming.

* How the techniques produced the requirement: Interviews surfaced strong privacy concerns; surveys confirmed privacy as a priority; brainstorming produced the default-minimization policy and opt-in mechanism.

### **NFR-002 — Secure Connections & Encryption**

* Description: Enforce TLS (HTTPS) for all network traffic; store credentials with strong hashing (bcrypt/argon2); use a secrets manager for keys.

* Elicitation techniques used: Interviews, Surveys, Brainstorming.

* How the techniques produced the requirement: Security-focused interviews demanded encrypted transport/storage; surveys indicated trust benefits from explicit security measures; brainstorming specified TLS enforcement, hashing, and secrets management**.**

### **NFR-003 — Accuracy (Model Performance)**

* Description: The detection model should meet project precision/recall targets (team to set numeric goals) and present confidence scores so users can interpret results.

* Elicitation techniques used: Interviews, Brainstorming.

* How the techniques produced the requirement: Interviews clarified acceptable false-positive/false-negative tradeoffs; brainstorming converted tolerance into measurable model targets and a UI confidence display.

### **NFR-004 — Performance (Latency)**

* Description: Manual scans should return results within a few seconds.

* Elicitation techniques used: Interviews, Brainstorming.

* How the techniques produced the requirement: Interviews specified acceptable wait times; brainstorming defined testable latency metrics and monitoring approach.

### **NFR-005 — Simplicity & Accessibility (Usability)**

* Description: UI and explanations must be simple and accessible to non-technical users (plain language, minimal steps, basic accessibility checks).

* Elicitation techniques used: Interviews, Surveys, Brainstorming.

* How the techniques produced the requirement: Interviews with non-technical users revealed pain points with jargon; surveys confirmed broad need for plain-language explanations; brainstorming translated findings into style guidelines and minimal-step flows.

