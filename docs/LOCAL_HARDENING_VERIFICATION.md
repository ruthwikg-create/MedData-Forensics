# Local security and research-integrity verification (14 November 2026)

This branch contains hardening changes to the uploaded MedData Forensics research prototype. It is **not clinically validated or production-ready**.

## Executed locally

- Python regression suite: **52 passed** on the repaired local ZIP, including 10 new tests for security, data integrity and exact reference metrics.
- Node frontend test suite: **67 passed**.
- Python compile check and JavaScript syntax check: **passed**.
- Live FastAPI synthetic-workflow smoke: **16 passing checks** for startup, demo dataset, forensic audit, CPU baseline, metric ranges, dataset integrity, records, four report formats, counterfactual study and image serving.
- Separate live HTTP session smoke: **passed** for missing/wrong token rejection, opaque cookie issuance, protected API requests and logout revocation.
- Chromium browser navigation: **blocked by this test environment's managed URLBlocklist** (ERR_BLOCKED_BY_ADMINISTRATOR). This is not an app test failure or a browser pass. Run the GitHub Actions Playwright browser smoke on this PR.

## Repairs

1. Browser no longer stores the master access secret; the server issues eight-hour process-local revocable HttpOnly SameSite-Strict cookies. Secure cookies apply over HTTPS.
2. Without an access token, remote peers and wildcard-bound configurations cannot access research APIs.
3. Train/validation/test leakage screening now follows transitive group/hash/decoded-pixel links and deduplicates identical held-out images.
4. Forensic audit no longer overwrites import-time SHA-256; modified files yield recorded integrity findings.
5. ZIP CSV/image entry reads now impose bounds before decompression.
6. Explicit patient IDs take precedence over lesion and generic group metadata where available.
7. CSV exported findings neutralize spreadsheet formula prefixes.
8. Invalid non-finite scenario rates are rejected.
9. The web app adds an explicit content security policy.

## Unverified release conditions

Independent medical data, clinical label truth, patient independence where identifiers are unavailable, real-dataset generalization, Windows installation, penetration testing, and multi-user identity/RBAC remain unverified. A synthetic 100% accuracy score is not evidence of medical predictive accuracy.

Keep the host on `127.0.0.1` and review CI before merging. No redundant research features were deleted simply on speculation. The complete locally tested ZIP and detailed report are available in the corresponding ChatGPT conversation.
