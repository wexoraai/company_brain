# Security Policy & Privacy Guidelines (Soil Systems)

This document outlines the security, data privacy, and Multi-Factor Authentication (MFA/2FA) requirements for **The Company Brain**.

---

## 1. Mandatory 2-Factor Authentication (2FA / MFA)
To prevent unauthorized access, all systems must enforce 2FA. **SMS-based 2FA is prohibited**; use Authenticator apps (e.g. Google Authenticator, Aegis) or hardware security keys (e.g. YubiKey).

| System / Provider | Role | 2FA Policy |
| :--- | :--- | :--- |
| **Google Workspace** | Corporate Identity | Mandatory for all logins. Admin must enforce globally. |
| **GitHub Organization** | Code Repository | "Enforce two-factor authentication for everyone in your organization" must be enabled. |
| **Supabase** | Core Database & Storage | MFA must be enabled for all administrator and developer logins. |
| **Bitwarden / 1Password** | Credentials Vault | Master account must have 2FA enabled. Shared vault contains TOTP keys for shared accounts. |
| **Zoho (CRM/Books)** | CRM & Accounting API | All operator logins must have Zoho OneAuth / MFA active. |

---

## 2. API Credentials & Shared Vault Policy
- **Zero Credentials in Code**: API keys, database passwords, and secrets must **never** be committed to Git. Commit only `.env.example`.
- **Vault-Only Storage**: Store all production configurations, API tokens, and credentials in the company's shared Bitwarden vault.
- **Environment Isolation**:
  - Development databases must use local credentials or separated staging databases.
  - Production database connection strings should only be accessible to the host runner (e.g. Docker environment on VPS).

---

## 3. Data Privacy & Isolation
- **Subsidiary Separation**:
  - Each document and meeting note must link to a specific `project_id` and `company_id`.
  - The Q&A search query endpoint allows scoping queries to a single project to prevent leaking information across sister entities (e.g., Windflower records should not bleed into Woods & Spices).
- **Personal Account Prohibition**:
  - No developer or employee is allowed to register cloud accounts (Supabase, OpenAI, Anthropic, AWS) using personal Gmail accounts for Soil Systems operations. All sign-ups must use company-owned emails (e.g., `tech@soilsystems.in`).
- **Data Transmission**:
  - All communication between the API, database, and clients must use TLS/HTTPS.
  - Set `sslmode=require` in Postgres connection strings when deploying to production.
