# Algions AI Labs — School Management System
## Submission Form Ready-to-Copy Data & Answers

Use the text below to fill in your official Algions AI Labs submission form:

---

### Section 1: Candidate Identification
* **Internship Role:** Full-Stack Web Development
* **Assigned Project Title:** School Management System
* **Student Name:** *(Enter your full name)*
* **Registration Number:** *(Enter your registration number)*
* **University Email:** *(Enter your university email address)*

---

### Section 2: Code and Version
* **Repository URL:** *(Enter your Git repository URL, e.g. GitHub/GitLab)*
* **Primary Branch:** `main` (or `master`)
* **Reviewer Access:** Ensure repository is set to Public or reviewer access is granted.

---

### Section 3: Demonstration
* **3–5 Minute Video Link:** *(Paste your Loom, YouTube Unlisted, or Google Drive link)*
* **Live Web Demo URL:** Declare Local-Only Demo (or host link if deployed on Render/Railway free-tier):
  > "Local-Only Demo: The project is verified to run deterministically with zero paid external services using `python manage.py runserver`. A complete 3-5 minute video demonstrating all 5 acceptance workflows is provided."

---

### Section 4: Documentation Links
* **Technical Report / Architecture:** Link to `TECHNICAL_REPORT.md` and `README.md` in repository.
* **Database & ER Schema Diagram:** Embedded Mermaid diagram in `README.md` and OpenAPI schema at `/api/docs/`.
* **API Documentation Link:** `http://127.0.0.1:8000/api/docs/` (Interactive Swagger UI via `drf-spectacular`).

---

### Section 5: Technology & Limitations
* **Technology Stack:**
  * **Backend Framework:** Django 6.1 (Python 3.14) — Modular Monolith architecture.
  * **Database & ORM:** Relational persistence with Django ORM, utilizing Foreign Keys, `UniqueConstraint` indices, and `django.db.transaction.atomic()` for financial and attendance operations.
  * **API & Documentation:** Django REST Framework 3.15 + drf-spectacular (OpenAPI 3.0 / Swagger UI).
  * **Frontend & UI:** Django Template Language (DTL) + Bootstrap 5.3 CDN + responsive `@media print` CSS for official student transcripts and fee receipts.
  * **Security & Auth:** Custom user model (`CustomUser`) with server-side Role-Based Access Control (RBAC) decorators and query-level guardian data isolation.
* **Setup Notes:**
  1. `python -m venv .venv`
  2. `pip install -r requirements.txt`
  3. `python manage.py migrate`
  4. `python manage.py seed_sms_data`
  5. `python manage.py test`
  6. `python manage.py runserver`
* **Assumptions & Known Limitations:**
  1. Simulated payment processing uses internally generated transaction vouchers (`SIM-XXXXX`) without live payment gateway credentials, as explicitly mandated by the assessment rules.
  2. The system is designed for single-campus institution management; multi-campus tenancy would require schema-based tenant routing.

---

### Section 6: AI & Attribution
* **AI Tools Used:** Google Antigravity / Gemini.
* **Purpose of Use:** Architectural consultation, boilerplate scaffolding of modular apps, test case formulation for database constraints, and documentation generation.
* **Library & Source Attribution:**
  * Django Project ([djangoproject.com](https://www.djangoproject.com/))
  * Django REST Framework ([django-rest-framework.org](https://www.django-rest-framework.org/))
  * drf-spectacular ([drf-spectacular.readthedocs.io](https://drf-spectacular.readthedocs.io/))
  * Bootstrap 5 ([getbootstrap.com](https://getbootstrap.com/))

---

### Section 7: Declarations & Interview Preparedness
* **Originality & Ownership Declaration:**
  > "I confirm that I understand the complete codebase, data schema, and security architecture of this School Management System. I am fully prepared to explain the design decisions in the 15-minute technical walkthrough and execute the 10-minute live coding/debugging task."
* **Secrets Declaration:**
  > "Confirmed: No real passwords, active payment tokens, personal identifiable information, or live API secrets exist in the repository. Environment variables use `.env.example`."
