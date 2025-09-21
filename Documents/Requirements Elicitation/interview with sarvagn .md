**Interviewee : Sarvagn Pathak (masters in Cybersecurity from New Jersey Institute of Technology)**

**Q — In your experience, what types of phishing or scam messages are hardest to detect for average users?**

**Answer:**  
The ones that come from executives — for example, messages that contain offers are easy to spot. But messages that appear to come from a CEO or CFO, asking you to do something (like transfer funds) urgently, are harder. People’s instinct is to act immediately, so they don’t fact-check and end up falling for the scam. Those types of scams are pretty hard to identify.

---

**Q — What risks do you see in automating scam detection with AI/ML?**

**Answer:**  
The risks I can see are false negatives and false positives. Sometimes AI/ML models are not trained properly, or the necessary pre-checks aren’t implemented. If those checks aren’t done correctly, a legitimate email might be flagged. So there should be other mechanisms in place.

---

**Q — What features would you consider essential in a scam-detection app to make it genuinely effective?**

**Answer:**  
URL parameter checks and domain obfuscation detection are important — that is, determining whether the URL is legitimate and whether it comes from the original domain. If there’s any image, there should be a security check before it renders to see if it contains malware. Those are pretty important features.

---

**Q — From a security/privacy perspective, what data should absolutely not be stored or transmitted?**  
**Answer:**  
Malicious payloads should not be stored — nowadays people store hashes instead of the original malware. Never store malware directly. Also, do not store any personal data. Images could contain malware too, so don’t store those either.

---

**Q — How would you balance false positives (safe messages flagged as scam) vs false negatives (scams not detected)? Which is worse from a user-trust standpoint?**

**Answer:**  
Do proper training and A/B testing so you understand what works and what doesn’t. Keep documentation of all flagged items. For example, if you get 100 flags out of 1000 messages, you can analyze that 10% and generalize. Maintain optimized AI/ML models and conventional hardcoded checks. Both false positives and false negatives are bad — it’s not just about user preference, but also about how SOC teams act on the data. That’s how IT teams typically handle it.

---

**Q — What would you suggest as acceptable accuracy/performance benchmarks for such an app (e.g., precision, recall, latency)?**

**Answer:**  
It depends on the benchmark — there are many tools available like KB4 with different benchmarks. Take multiple benchmarks, test on different parameters, and get their evaluations.

---

**Q — What strategies can help explain results to non-technical users without oversimplifying?**

**Answer:**  
This is a good question because non-technical users will see alerts before the IT team or SOC. Users should be made aware if they are likely to receive phishing mail and be alerted to be cautious about untrustworthy senders. They should check URLs carefully, avoid clicking suspicious buttons, and verify redirects. They should also search the URL themselves to check if it’s safe. Doing these things will reduce the chance of being scammed.

---

**Q — In your opinion, how feasible is multilingual scam detection within a 2-month project scope? What approach would you recommend (e.g., translation vs language-specific models)?**

**Answer:**  
This isn’t his strong area, but it requires a lot of data and effort. Multilingual detection is not feasible in a short timeframe because interpreters may not work properly; it’s very extensive to implement.

---

**Q — What potential cyber risks could emerge if such an app itself is targeted (e.g., adversarial attacks, fake inputs)? How can we mitigate them?**

**Answer:**  
That’s a good question. But the app isn’t usually targeted through the user because the attack vector increases significantly. An entire app can’t be hacked just through phishing — there are many other security measures to place that are outside the phishing domain.

---

**Q — If you were advising the team, what one technical safeguard would you insist on implementing first?**

**Answer:**  
Parameter recognition is the most important feature.

