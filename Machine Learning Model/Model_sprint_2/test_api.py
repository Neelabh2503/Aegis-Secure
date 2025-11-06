from asyncio import sleep
import requests
import json
import textwrap

 
API_URL = "https://sharyl-liberalistic-procrastinatingly.ngrok-free.dev/predict" 

 
HEADERS = {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true'
}

 
messages_to_test = [
    """Dear Akshat Nitinkumar Bhatt of DAIICT
Become a Campus Manager at Unlox: Lead, Earn, and Grow with AI EdTech!
Join Unlox as a Campus Manager and be the face of India's top AI-powered EdTech revolution right on your campus! Unlox is a next-gen platform dedicated to revolutionising student learning and career preparation. We're looking for driven, tech-savvy student leaders to champion this movement at their colleges.
What You'll Gain:
Earn up to ₹21,000 in Stipends* (get ₹1,000 instantly for every 4 enrollments!).
Free Edulet after 15 enrollments (Tab with smartlab,blu, job bridge program)
Official Certificate of Completion & Appraisal Letter for your resume.
Invaluable Real Leadership & Management Experience.
FREE Access to PrepFree, our exclusive career platform, featuring:
AI Resume Builder
Mock Interviews
Smart Job Matching
Dedicated Career Assistance and Job Portals
Masterclasses and bootcamps
 Your Mission:
Lead a simple WhatsApp campaign to engage 50+ students from your college. Your goal is to grow the Unlox Student Community—all while gaining excellent real-world experience and significantly boosting your resume.

Ready to lead and make a tangible impact?
Application form - Apply by clicking this link

Regards
Aman K
Team Leader Unlox.
https://unlox.com/
https://in.linkedin.com/company/unloxacademy""",

    """You're invited to join the Internshala Student Partner program to develop professional skills while gaining valuable experience.
Ready to represent us
in DAIICT Gandhinagar?
Join the Internshala Student Partner Program
Program benefits include:
 Learning opportunity - Masterclasses by industry professionals
 Career development - Certificates and recommendation letters
 Skill building - Develop leadership and communication skills
Who can apply? B.Tech students at DAIICT Gandhinagar can learn more about the program by clicking below.
LEARN MOREInternshala (Scholiverse Educare Pvt. Ltd.)
901A and 901B, Iris Tech Park, Sector - 48, Sohna Road, Gurugram
Not interested? Unsubscribe""",

    """Hey Akshat,
While you may still be (or not be!) on the hunt for a full-time opportunity, I wanted to share that we are also starting to partner with organizations that have part-time roles and tasks that you can complete to earn some additional income while still looking for full-time work.

We’re currently collaborating with an AI research lab on a project to help train AI models to better understand how real people use computers in day-to-day tasks. As a part of this project, you will have a front-row seat into helping shape the way future AI systems interact with common software, making technology more accessible and useful for everyone.

What's involved?
You'll be asked to perform simple, everyday computer tasks—like creating a Word document, making a presentation slide, or organizing videos online.
Each task is quick (around 2–3 minutes) and you can do as many or as few as you’d like within a 24-hour period. (Note: Project expires on November 6th, 2025)

Requirements:
For verification, you'll need to install two small programs and allow temporary recording of your screen and keyboard activities, strictly for checking that tasks are completed as described. Your data is protected and only used for research purposes.

Compensation:
You'll earn $0.30 (or Rs. 30 if in India) for each correctly completed and verified task (minimum quality standard: 75% accuracy).
There are at least 1,000 tasks available—meaning you could earn a upto ~$350 in one day if you choose to finish all. The most active participants can take on up to 20,000 tasks.

Next Steps and How to Start:
Just fill out the form here to get started: https://tinyurl.com/lightning-puneet
You will receive onboarding instructions over email in 5-10 minutes after filling out the form.

You can also join our WhatsApp group for this project to discuss with other contributors - cheers (Link will be provided after registration)!

We appreciate your help building smarter, fairer AI systems. Happy to answer any questions!

Regards,
Puneet Kohli
careerflow.ai""",
    """Dear Akshat!
😎 Turn your Curiosity into Epic rewards with the TATA group*!

Yes, its true! Join the Tata Crucible Campus Quiz 2025  🎉 open to all in-college students from every stream and background.

✨  Here's what you can win:
A brand-new iPhone 17
Win cash prizes worth up to ₹2.5 Lakh*
Internships* with the TATA group
A Luxury holiday worth ₹50,000
Certificates & loads of other rewards (every quiz taker gets a reward)
👉  How to Participate? (follow 3 simple steps):

1️⃣ Click the button below to Register
2️⃣ Once logged in, click on continue and hit "Complete Details.”
3️⃣ Fill in your details, take the quiz, and DM your quiz completion screenshot to Tata Crucible’s official Instagram by following them.
⚠️ Important: Registration can only be completed once the basic details are filled in.

🔥 Thousands of students are already in. Don’t miss your chance to shine at India’s biggest campus quiz!
Register Now
 
 
internshala (scholiverse educare pvt. ltd.)
iris tech park, sohna road, gurugram 

view it in your browser.
unsubscribe me from this list
    """
]

def analyze_message(text):
    """
    Sends a message to the Phishing Detection API and prints the result.
    """
    payload = {"text": text}  
    
    try:
       
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=10)
        
       
        if response.status_code == 200:
            prediction = response.json()  
             
            print(json.dumps(prediction, indent=4))
            
           
            print("-" * 20)
            print(f"Decision:     {prediction.get('final_decision')}")
            print(f"Confidence:   {prediction.get('confidence')}%")
            print(f"Reasoning:    {prediction.get('reasoning')}")
            print(f"Suggestion:   {prediction.get('suggestion')}")
            print("-" * 20)

        else:
            
            print(f"Error: Received status code {response.status_code}")
            print(f"Response text: {response.text}")  

    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: Could not connect to {API_URL}.")
        print("Please ensure the ngrok tunnel is running and the URL is correct.")  
    except requests.exceptions.RequestException as e:
       
        print(f"An error occurred during the request: {e}")

 
if __name__ == "__main__":
    for i, message in enumerate(messages_to_test):
        print(f"================== TESTING MESSAGE {i+1} ==================")
        
        print(f"Message Snippet: {textwrap.shorten(message, width=70, placeholder='...')}\n")
        
        analyze_message(message)
        
        print(f"================END OF TEST FOR MESSAGE {i+1} ================\n\n")
        sleep(6.0)