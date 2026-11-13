# Algions AI Labs — School Management System
## 3 to 5-Minute Video Walkthrough Script & Demo Checklist

This script is designed for your 3–5 minute submission recording and your 15-minute technical walkthrough interview.

---

### Segment 1: Introduction & Architecture (0:00 - 0:45)
* **Goal:** Present the problem statement and technical architecture.
* **Talking Points:**
  > "Hello, I am presenting the School Management System built for Algions AI Labs. This system implements a clean, modular monolith architecture using Django 6.x. It separates concerns across six core domain modules: Accounts, Academics, Attendance, Examinations, Finance, and Audit. All critical actions enforce server-side RBAC, database transactions, and database-level unique constraints to guarantee data integrity."

---

### Segment 2: Admin Operations & Academics Setup (0:45 - 1:30)
* **Goal:** Demonstrate administrator oversight and academic catalog.
* **Actions on Screen:**
  1. Navigate to `/accounts/login/` and sign in as `admin` / `admin123`.
  2. Point out the **Admin Command Center**: Total students, attendance rate, total collected fees, and the live Audit Trail.
  3. Click **Classes & Sections** and **Subjects** under Academics to show class allocations.
  4. Show the **Audit Trail** (`/audit/logs/`) to show that every operation is logged.

---

### Segment 3: Teacher Journey & Attendance Duplicate Prevention (1:30 - 2:30)
* **Goal:** Demonstrate Acceptance Criteria 1 & 2.
* **Actions on Screen:**
  1. Sign out and sign in as `teacher1` / `teacher123` (Sarah Jenkins).
  2. Notice the **Teacher Workspace**: Only Sarah's assigned classes (Grade 10 Section A) are accessible.
  3. Click **Record Attendance**:
     * Demonstrate that Sarah cannot record attendance for unassigned classes (server-side authorization blocks unauthorized IDs).
     * Mark attendance for Grade 10 Section A: click **Mark All Present**, toggle one student to **Late**, and click **Save**.
     * Resubmit/edit to demonstrate safe upsert: the database unique constraint prevents duplicate rows for the same student/date/session.
  4. Navigate to **Marks Entry**: Select Mid-Term Test, enter marks for students, and demonstrate that letter grades (A+, A, B, etc.) are computed automatically based on configured grading rules.

---

### Segment 4: Guardian Privacy & Report Card (2:30 - 3:30)
* **Goal:** Demonstrate Acceptance Criteria 3 & 4.
* **Actions on Screen:**
  1. Sign out and sign in as `guardian1` / `guardian123` (Robert Taylor).
  2. Point out the **Parent Portal**: Robert can only see his daughter, Alice Taylor. Leo and Sofia Garcia are completely inaccessible.
  3. Click **Official Report Card**:
     * Show Alice's computed grades, overall percentage, and attendance statistics.
     * Click **Print Report Card** to show the `@media print` optimized transcript.

---

### Segment 5: Fee Management & Ledger Reconciliation (3:30 - 4:30)
* **Goal:** Demonstrate Acceptance Criterion 5.
* **Actions on Screen:**
  1. On the Guardian dashboard, locate Alice's or Leo's fee invoice.
  2. Click **Pay Now**: Make a simulated payment of the outstanding balance.
  3. Sign back in as `admin` and open the **Fee Ledger Reconciliation Report** (`/finance/ledger/`).
  4. Highlight the reconciliation banner:
     $$\text{Total Invoiced} = \text{Total Collected} + \text{Outstanding Balance}$$
     Show that every payment is recorded in the immutable payment ledger.

---

### Segment 6: API Documentation & Automated Tests (4:30 - 5:00)
* **Goal:** Showcase OpenAPI docs and test evidence.
* **Actions on Screen:**
  1. Open `/api/docs/` to show interactive Swagger UI with all documented endpoints.
  2. In the terminal, run `python manage.py test` to show all 7 acceptance tests passing with `OK`.
  3. Conclude the demonstration.

