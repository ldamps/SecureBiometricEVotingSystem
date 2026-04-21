# Voter Guide

## Secure Biometric E-Voting System

This guide walks you through using the voting platform as a voter, from creating your account through casting your ballot and managing your registration after.

---

## Table of Contents

1. [Before You Start](#1-before-you-start)
2. [Landing Page](#2-landing-page)
3. [Registering to Vote](#3-registering-to-vote)
4. [Installing the Authenticator App](#4-installing-the-authenticator-app)
5. [Biometric Enrolment](#5-biometric-enrolment)
6. [Casting Your Vote](#6-casting-your-vote)
7. [Managing Your Registration](#7-managing-your-registration)
8. [Troubleshooting](#8-troubleshooting)
9. [Privacy and Security: What You Should Know](#9-privacy-and-security-what-you-should-know)

---

## 1. Before You Start

To register and vote you will need:

- A **computer or tablet** with a modern browser (Chrome, Edge, Safari, Firefox) to use the voting website.
- A **smartphone** (iPhone or Android) with a front-facing camera. This becomes your personal authenticator — it stores your biometrics and signs in to the voting system on your behalf.
- A **valid photo ID** — a UK passport, driving licence, or national identity card — for identity verification.
- A **proof of address** document (utility bill, bank statement, council tax letter) issued within the last three months.
- Your **National Insurance number** (if you have one) or passport details.
- A working **email address**. All confirmations, verification codes, and receipts are sent here.

You should only need to register once. After that, you use the same account for every election you are eligible to vote in.

---

## 2. Landing Page

When you open the voting website you see three options:

- **Vote** — opens the ballot flow for an election that is currently running.
- **Register to vote** — starts first-time registration.
- **Manage vote registration details** — lets you view or update your existing registration (new address, change of name, re-enrol biometrics, etc.).

A link to **About** explains in plain language how the system protects your privacy and your ballot. If you are unsure what the platform does, read that page first.

---

## 3. Registering to Vote

Click **Register to vote** on the landing page. Registration is a five-step form. You can move back and forth between steps until you submit at the end.

### Step 1 — Where you live

Choose whether you live in England / Northern Ireland, Scotland, or Wales. This determines the minimum voting age that applies to you (16 in England and Northern Ireland, 14 in Scotland and Wales for local and devolved elections).

### Step 2 — Your details

Enter:

- First and last name (legal name exactly as it appears on your ID).
- Previous name, if you have changed it (optional).
- Email address.
- Date of birth.
- Nationality — British, Irish, a qualifying Commonwealth citizen, or EU.
- Either your **National Insurance number** or your **passport details** (number, issuing country, expiry). You only need to provide one of these.

You will be asked to verify your email with a **six-digit code** sent to the address you entered. Enter it when prompted. If the code does not arrive within a minute, check your spam folder and use the **Resend code** button.

### Step 3 — Your address

Enter your full UK address, including postcode. The system looks your postcode up automatically and assigns you to the correct parliamentary constituency (using the 2025 boundaries).

You will then be asked to complete **identity verification** through Stripe Identity, which is embedded in the page:

1. Photograph the front and back of your photo ID.
2. Take a selfie so your face can be matched to the photo on the document.
3. Upload a recent proof-of-address document.

The checks take a minute or two. You do not need to leave the page; Stripe will show a green tick when each step is accepted.

### Step 4 — Biometric enrolment

Now you link a **personal authenticator** — your phone — to your account. This is the device that will confirm it is really you every time you vote. See [Section 4](#4-installing-the-authenticator-app) and [Section 5](#5-biometric-enrolment) for the full walk-through. You cannot skip this step.

### Step 5 — Confirm and submit

Review the summary of everything you have entered. When you click **Submit**, you receive:

- A confirmation email with a summary of your registration.
- A notice that you are eligible to vote in any election currently open in your constituency.

You are now on the electoral roll on this platform.

---

## 4. Installing the Authenticator App

The authenticator is a Progressive Web App (PWA). You do not install it from the App Store or Google Play — you add it directly from the voting website.

### On iPhone (Safari)

1. Open the voting website on your iPhone.
2. Tap the **Share** button in the toolbar.
3. Scroll down and tap **Add to Home Screen**.
4. Tap **Add**.
5. Open the new icon from your home screen.

### On Android (Chrome)

1. Open the voting website on your Android phone.
2. Open the browser menu (three dots).
3. Tap **Install app** (or **Add to Home screen**).
4. Tap **Install**.
5. Open the new icon from your home screen.

When you open the installed app for the first time it goes straight to a **QR code scanner**. That is the only thing it does — it is single-purpose by design. Grant it access to the camera when prompted.

---

## 5. Biometric Enrolment

Enrolment teaches your phone what you look like so that only you can approve votes from it.

1. On the voting website, at the biometric step of registration, a **QR code** appears on screen.
2. Open the authenticator app on your phone and point the camera at the QR code. The app recognises it and opens the enrolment screen.
3. Read the short privacy notice. Tap **Start enrolment**.
4. Hold the phone at arm's length. Follow the on-screen prompts:
   - Face the camera straight on.
   - Blink when asked (liveness check).
   - Turn your head slightly so each ear can be captured.
5. The app then shows a progress message — "Generating biometric-bound encryption keys…" — followed by "Registering your device with the voting platform…".
6. When you see **"Enrolment complete"**, go back to the voting website on your computer. The registration form advances automatically.

**What is stored where:** Your face and ear data never leave your phone. Only a public cryptographic key (which cannot be reversed into your face) is sent to the voting system. If your phone is lost or stolen, no biometric information can be extracted from the server.

---

## 6. Casting Your Vote

### 6.1 Starting the flow

Click **Vote** on the landing page. Voting happens in five stages. A progress indicator at the top shows which one you are on.

### 6.2 Confirm your identity

Enter your full name and address as they appear on your registration. The system checks your entries against the electoral roll. If something does not match, you will be asked to correct it or open **Manage registration** to update your details first.

### 6.3 Biometric verification

A new QR code appears. Open the authenticator on your phone and scan it.

- The app says "Verify your identity". Tap **Verify identity**.
- Hold the phone so the camera can see your face and ears, as in enrolment.
- You will see progress messages: "Fetching your enrolment data…", "Verifying your biometrics…", "Submitting cryptographic proof…".
- When you see **"Identity verified"**, return to the voting website.

If the app shows "Biometric verification failed", move to better lighting, make sure your ears are not covered by hair, hats, or earphones, and tap **Try again**.

### 6.4 Choose the election

Pick the election or referendum you want to vote in from the list. Only contests you are eligible for (based on your constituency) are shown.

### 6.5 Mark your ballot — the 10-minute window

As soon as the ballot opens, a countdown at the top reads **"Time remaining: 10:00"**. You have ten minutes to complete and submit your vote. The timer turns red in the final minute.

The ballot looks different depending on the election:

- **First Past the Post** (general elections, most local elections, mayoral): select **one** candidate.
- **Alternative Vote** (some specialist elections): rank candidates 1, 2, 3… in your order of preference. You do not have to rank all of them.
- **Single Transferable Vote** (Northern Ireland Assembly, some local councils): rank candidates 1, 2, 3… across the multiple seats available.
- **Additional Member System** (Scottish Parliament, London Assembly): make **two** choices — one constituency candidate and one regional party.
- **Referendum**: choose **Yes** or **No** to the question shown.

### 6.6 Review and submit

Before submitting you see a summary of your selection. Tick **"Email me a confirmation of participation"** if you want a receipt. The receipt confirms that you voted; it does **not** record what you voted for.

Click **Submit vote**. You will see a success screen and the browser back button is disabled so you cannot accidentally return to the ballot. You are done.

If the ten-minute timer runs out before you submit, the session ends and you are returned to the landing page. You can start again — your vote has not been recorded, and you will not be shown as having voted.

---

## 7. Managing Your Registration

Click **Manage vote registration details** on the landing page. You will be asked to:

1. Re-enter your name and address so we can find your record.
2. Verify your identity — either through the authenticator app (preferred) or by requesting a **six-digit email code** as a backup if you no longer have access to your enrolled phone.

Once you are in, you can edit three sections:

- **Identity details** — name, date of birth, email, nationality, ID method.
- **Current address** — move to a new address (you will be asked to upload a new proof of address; this may change your constituency).
- **Biometric details** — re-enrol on a new phone, or refresh an existing enrolment. Re-enrolling automatically deactivates your previous device.

Edited sections are marked **(draft)**. When you click **Save changes**, all draft changes are submitted together. You will get an email confirming the changes; most edits are live immediately, but some identity changes take up to 24 hours to process.

---

## 8. Troubleshooting

**The email verification code never arrived.**
Check your spam folder. Use the **Resend code** button. If it still does not arrive, the email address you entered may have a typo — go back to Step 2 and correct it.

**Stripe Identity rejected my document.**
Retake the photo in brighter, even lighting with no glare. Make sure all four corners are visible and the text is in focus. Your document must be valid (not expired).

**The authenticator will not scan the QR code.**
Hold the phone about 20 cm from the screen, square-on, and make sure your screen brightness is high. Clean the phone's camera lens.

**Biometric verification keeps failing.**
Face the camera squarely in good lighting. Remove hats, headphones, or hair covering your ears. If it still fails, open **Manage registration** from a computer, verify with an email code, and re-enrol on your phone.

**I lost my phone.**
Go to **Manage registration**, verify with an email code, and re-enrol on a new phone. Your old device is automatically deactivated.

**The 10-minute timer ran out.**
Your vote was not submitted and your eligibility is unchanged. Click **Vote** and start again — you can vote in the same election as long as it is still open.

**The system says I have already voted.**
Each voter can only vote once per election. If you believe this is wrong, contact your election official at the address on the About page.

---

## 9. Privacy and Security: What You Should Know

- **Your vote is anonymous.** Vote records are not linked to your name, address, or any identifier. The system records separately that you took part, and separately what the totals are. No official — not even an administrator — can look up how you voted.
- **Your biometrics stay on your phone.** The server never sees your face or ear data. Only a cryptographic public key is stored.
- **Personal data is encrypted at rest.** Your name, address, ID number, and passport details are encrypted field-by-field in the database. Nothing is visible to anyone reading the raw database.
- **Every ballot token is single-use.** Once you submit your vote, the token that let you cast it is burned. It cannot be reused even if someone intercepted it.
- **The voting window is strictly enforced.** Votes are only accepted between the official opening and closing times of each election.
- **Rate limiting protects your account.** After several failed login or verification attempts, your session is temporarily locked to prevent brute-force attacks.

If you spot anything that looks wrong — a candidate missing, an election you should be eligible for that is not shown, or unexpected behaviour — report it to your election official. They can open a formal investigation into the issue.
