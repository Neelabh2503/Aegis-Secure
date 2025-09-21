### **Stakeholder Identification and Elicitation Techniques**

1. **Individual User**

   * **How Identified**: They are the primary end-users who will directly interact with the application.

   * **Elicitation Technique used**: *Survey and Interviews*  
        
   * **How Applied:** Conducted Survey by sharing the google form, conducted interviews 

2. **Email/SMS Service Providers**

   * **How Identified**: External service providers required for communication functionality within the system.

   * **Elicitation Technique used**: *Documentation Review* 

   * **How Applied:**  Reviewed technical documentation and developer guidelines to identify integration constraints, permissions, and compliance requirements.

   * **Citations:**   
   * [SMS Compliance Checklist for Businesses: Best Practices](https://www.textmagic.com/blog/sms-compliance-checklist/) (SMS)  
   * [https://knowledge.apollo.io/hc/en-us/articles/4409225311885-Email-Deliverability-Best-Practices](https://knowledge.apollo.io/hc/en-us/articles/4409225311885-Email-Deliverability-Best-Practices) (E-mail)

3. **Cloud Service Provider**

   * **How Identified**: Needed to host the application, databases, and ensure scalability.

   * **Elicitation Technique used**: *Documentation Review* 

   * **How Applied:** Reviewed CSP manuals and pricing to assess **scalability, security, and cost**, and performed a **comparative study** of AWS, Google Cloud, Microsoft Azure, and Salesforce to identify the best fit for our application.

   * **Citations :** [https://www.researchgate.net/profile/Ahmed-Youssef/publication/299551297\_Cloud\_Service\_Providers\_A\_Comparative\_Study/links/56fe9fe308aea6b77468cdb4/Cloud-Service-Providers-A-Comparative-Study.pdf](https://www.researchgate.net/profile/Ahmed-Youssef/publication/299551297_Cloud_Service_Providers_A_Comparative_Study/links/56fe9fe308aea6b77468cdb4/Cloud-Service-Providers-A-Comparative-Study.pdf)

4. **Dataset Providers**

   * **How Identified**: Essential for supplying real-time or static datasets for the application’s functioning.

   * **Elicitation Technique used**: *Documentation Review*

   * **How Applied:** We collected **metadata** (dataset names, sources, update frequency), **dataset structures** (formats like CSV, JSON, Parquet, structured vs unstructured), and **compliance policies** (GDPR, CCPA, copyright/licensing rules) from dataset provider documentation. This review helped us understand how datasets are organized, accessed, and legally used for analysis or application development.

   * **Citation:** [https://brightdata.com/blog/web-data/best-dataset-websites](https://brightdata.com/blog/web-data/best-dataset-websites?utm_source=chatgpt.com)

5. **Cybersecurity Experts**

   * **How Identified**: They provide domain knowledge about phishing tactics, scam patterns, and evolving threats

   * **Elicitation Technique used**: *Interviews/Surveys* 

   * **How Applied:** Conducted interviews to validate detection logic and confirm that identified scam indicators (e.g., suspicious links, urgency phrases) match real-world patterns.

6. **API Key Providers**

   * **How Identified**: Required for authentication, integration with third-party services, and enabling application functionalities.

   * **Elicitation Technique used**: *Documentation Review* 

   * **How Applied:** Reviewed API guidelines, authentication procedures, and integration manuals.

   * **Citations:** [https://www.helicone.ai/blog/llm-api-providers](https://www.helicone.ai/blog/llm-api-providers) [https://artificialanalysis.ai/leaderboards/providers](https://artificialanalysis.ai/leaderboards/providers)  
   * Documentation : [https://stoplight.io/api-documentation-guide](https://stoplight.io/api-documentation-guide?utm_source=chatgpt.com)  
   * Authentication :  [https://frontegg.com/guides/api-authentication-api-authorization](https://frontegg.com/guides/api-authentication-api-authorization?utm_source=chatgpt.com)  
   * Integration : [https://www.merge.dev/blog/api-integration-best-practices](https://www.merge.dev/blog/api-integration-best-practices)

7. **Government Agencies/Regulators**

   * **How Identified**: Required to comply with regulations such as data protection, privacy, and communication laws.

   * **Elicitation Technique used**: *Documentation Review* 

   * **How Applied:**  Referred to official guidelines, legal frameworks, and compliance documents.  
   * Citations : [TRAI releases Measures being taken by TRAI to Combat Spam Calls and SMS | Telecom Regulatory Authority of India](https://trai.gov.in/notifications/press-release/trai-releases-measures-being-taken-trai-combat-spam-calls-and-sms)

8. **Developer Team (Students \+ Mentor)**

   * **How Identified**: Core team responsible for design, development, and maintenance of the application.

   * **Elicitation Technique used**: *Brainstorming Sessions* 

   * **How Applied:** Conducted group discussions to define requirements, align goals, and explore implementation strategies.

       9\.  **Database Providers**

* **How Identified:** Identified as stakeholders due to their role in securely storing user preferences, logs, and anonymized feedback, ensuring data privacy, compliance, and system performance.

  * **Elicitation Technique used**: Documentation Analysis.

  * **How Applied:** Reviewed database provider documentation to gather metadata, features, performance, and security/compliance policies. This helped assess scalability, flexibility, cost, and suitability of different databases for our project.

  * **Citations:** [https://www.altexsoft.com/blog/comparing-database-management-systems-mysql-postgresql-mssql-server-mongodb-elasticsearch-and-others](https://www.altexsoft.com/blog/comparing-database-management-systems-mysql-postgresql-mssql-server-mongodb-elasticsearch-and-others)