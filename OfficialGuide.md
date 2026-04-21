# Election Official Guide

## Secure Biometric E-Voting System

This guide explains how to use the platform as an election official — from your first login through running elections, reviewing results, handling incidents, and generating the formal audit report.

---

## Table of Contents

1. [Roles and Responsibilities](#1-roles-and-responsibilities)
2. [First-Time Login and Onboarding](#2-first-time-login-and-onboarding)
3. [Your Dashboard Home](#3-your-dashboard-home)
4. [Managing Elections](#4-managing-elections)
5. [Managing Referendums](#5-managing-referendums)
6. [Reviewing Results](#6-reviewing-results)
7. [Investigations and Incident Reports](#7-investigations-and-incident-reports)
8. [Generating the Audit Report](#8-generating-the-audit-report)
9. [Managing Fellow Officials](#9-managing-fellow-officials)
10. [Profile and Session Management](#10-profile-and-session-management)
11. [Good Practice and Escalation](#11-good-practice-and-escalation)

---

## 1. Roles and Responsibilities

Officials on the platform have one of two roles:

| Role | What they can do |
|------|------------------|
| **Election Officer** | View all dashboards, results, investigations. Create, edit, publish, close, and cancel elections and referendums. Report and triage incidents. |
| **Administrator** | Everything an Election Officer can do, plus: invite, deactivate, and reactivate officials; generate formal PDF audit reports. |

Your role is shown as a badge on your profile. If you need your role changed, contact another administrator.

Every action you take — creating an election, closing voting, resolving an investigation — is recorded in the audit log under your official ID. Work carefully; your work is attributable.

---

## 2. First-Time Login and Onboarding

### 2.1 Getting your account

You cannot create your own account. An existing administrator invites you. You will receive an email containing:

- Your **username** (derived from your email address).
- A **temporary password**.
- A link to the official login page.

### 2.2 First login

1. Open the official login page (`/official/landing`).
2. Enter your username and the temporary password from the invitation email.
3. Click **Sign in**.

Because `must_reset_password` is set on new accounts, you are redirected automatically to the **onboarding page**.

### 2.3 Setting your password

On the onboarding page:

1. Re-enter your temporary password.
2. Enter a new password (minimum 8 characters, and must differ from the temporary one).
3. Confirm the new password.
4. Click **Continue**.

You are now signed in and taken to the home dashboard. This password is the one you use from now on.

### 2.4 Forgotten password

If you forget your password there is no self-service reset. Email the system administrator at the contact address shown on the login page — they can issue a new temporary password and the onboarding flow will run again.

---

## 3. Your Dashboard Home

The home page (`/official/home`) is the central view. At the top is an **election / referendum selector** — a dropdown that lists every contest on the system, sorted by status (open first, then closed, then drafts and cancelled). Select the contest you want to work with; the rest of the page updates to match.

Three tabs sit below the selector:

- **Overview** — live or final results for the selected contest.
- **Audit logs** — PDF audit report (administrators only).
- **Investigations** — incident reports and their status (elections only).

See [Section 6](#6-reviewing-results) for what each part of the Overview tab shows and [Section 8](#8-generating-the-audit-report) for the audit report.

The left-hand navigation takes you to the four management areas: **Manage elections**, **Manage referendums**, **Manage officials**, and **Profile**.

---

## 4. Managing Elections

Open **Manage elections** from the navigation. You see a table of every election with columns for title, type, voting system, scope, status, opening and closing dates, constituency count, and action buttons.

### 4.1 Election statuses and what you can do in each

| Status | What it means | Actions available |
|--------|---------------|-------------------|
| **DRAFT** | Created but not yet live. Voters cannot see it. | Edit · Publish · Cancel |
| **OPEN** | Voting is live and accepting ballots. | Close · Revert to draft · Cancel |
| **CLOSED** | Voting has ended and results are final. | Reopen · Cancel |
| **CANCELLED** | Election was withdrawn and has no results. | (none — terminal state) |

### 4.2 Creating a new election

Click **+ New election**. In the dialog, fill in:

| Field | Notes |
|-------|-------|
| **Title** | Public-facing name, e.g. "2026 UK General Election". |
| **Election type** | Choose from the predefined types: General, Local (England/Wales), Local (NI/Scotland), Scottish Parliament, London Assembly, NI Assembly, Mayoral, Police & Crime Commissioner, Scottish National Park, Scottish Crofting Commission, House of Lords Hereditary. |
| **Scope** | National, Regional, or Local. |
| **Voting opens** | dd/mm/yyyy. Required before you can publish. |
| **Voting closes** | dd/mm/yyyy. Must be after "Voting opens". |
| **Constituencies** | Multi-select list. Search by name or country; use **Select all**, **Select filtered**, or **Clear all** to speed selection. |

The **voting system** (FPTP, AMS, STV, or Alternative Vote) is set automatically based on the election type you chose — see the table in [Section 4.4](#44-voting-systems-and-when-they-apply).

You can either:

- **Save as draft** without dates, and come back later to fill them in and publish, or
- Enter dates and click **Publish** to move the election straight to OPEN.

### 4.3 Publishing, closing, reopening, cancelling

- **Publish** moves a DRAFT to OPEN. Once open, the election appears to eligible voters and they can begin casting ballots.
- **Close** moves an OPEN election to CLOSED and produces final results. Use this at the scheduled close time if the automatic close has not yet fired.
- **Revert to draft** takes an OPEN election back to DRAFT. Use sparingly — only before any real votes have been cast.
- **Reopen** moves a CLOSED election back to OPEN. Use only to extend voting after an incident, and document the reason in an investigation.
- **Cancel** marks the election as CANCELLED. This is final. Votes are not counted and results are not published. Cancel only when there is a genuine integrity problem with the election.

### 4.4 Voting systems and when they apply

| System | Ballot experience | Applied automatically to |
|--------|-------------------|--------------------------|
| **First Past the Post (FPTP)** | Voter picks one candidate. | General, Local (England/Wales), Mayoral, Police & Crime Commissioner, Scottish National Park |
| **Alternative Vote (AV)** | Voter ranks candidates in order of preference. | House of Lords Hereditary, Scottish Crofting Commission |
| **Single Transferable Vote (STV)** | Voter ranks candidates; surplus votes transfer until seats are filled. | NI Assembly, Local (NI/Scotland) |
| **Additional Member System (AMS)** | Voter picks one constituency candidate and one regional party. | Scottish Parliament, London Assembly |

### 4.5 Editing an election

Edit is only available while the election is in DRAFT. Once published, the only structural changes you can make are close, cancel, or revert to draft. Candidates, constituencies, and dates are fixed for an open election to guarantee integrity.

---

## 5. Managing Referendums

Open **Manage referendums**. The table and workflow mirror elections, with one extra field.

### 5.1 Creating a new referendum

Click **+ New referendum** and fill in:

| Field | Notes |
|-------|-------|
| **Title** | Short name, e.g. "2026 Devolution Referendum". |
| **Question** | The actual question voters see on the ballot. Write it clearly and neutrally. |
| **Scope** | National, Regional, or Local. |
| **Voting opens / closes** | dd/mm/yyyy. Same rules as elections. |
| **Constituencies** | Which constituencies are eligible to take part. |

Referendums have the same four statuses as elections — DRAFT, OPEN, CLOSED, CANCELLED — with the same action buttons. The ballot shows a simple **Yes / No** choice.

---

## 6. Reviewing Results

Select the election or referendum in the home page dropdown and open the **Overview** tab.

### 6.1 For an election

**Summary cards** at the top show:

- Total votes cast.
- Total seats available.
- Majority threshold.
- Number of constituencies that have reported.
- Winning party (when a majority is secured).
- Overall status (open, closed).

**Charts:**

- Top 20 constituencies by vote count (bar chart).
- Seat allocation by party (bar chart).

**Seat allocation table** — each party with the seats they have won and the percentage of the total.

**Constituency results table** — paginated 20 per page. Each row shows the constituency name, the winner, the winning party, total votes, and how many candidates stood. Next to every row is a **Report error** button. Use this if you see something that does not look right (see [Section 7](#7-investigations-and-incident-reports)).

While an election is still open, the results are interim. They are marked accordingly and update as more ballots arrive.

### 6.2 For a referendum

Summary cards show total votes, Yes count, No count, Yes %, No %, and the outcome (Yes / No / Pending). A bar chart compares Yes against No.

---

## 7. Investigations and Incident Reports

Investigations are the formal record of anything that went wrong (or might have gone wrong) during an election. They feed directly into the audit report.

### 7.1 Raising an incident

On the Overview tab, click **Report error** next to a constituency row, or **Report error** at the top of the page for a general issue.

A modal opens. Fill in:

- **Severity** — LOW, MEDIUM, HIGH, or CRITICAL.
- **Summary** — a short title (minimum 3 characters). The constituency name is prepended automatically when you report from a row.
- **Description** — optional, but recommended. Include what you saw, when, and anything that might help another official investigate.

Click **Submit**. An investigation is created with status **OPEN**. You are recorded as the raiser.

### 7.2 Triaging investigations

Open the **Investigations** tab. Each investigation card shows:

- Title, severity, and the date it was raised.
- Category (BALLOT_IRREGULARITY, SYSTEM_ERROR, VOTER_FRAUD, TALLY_DISCREPANCY, PROCESS_VIOLATION, OTHER).
- Status (OPEN, IN_PROGRESS, RESOLVED, CLOSED).
- The description and any notes added since.
- The assigned official's name, if one has been assigned.
- A resolution summary and resolved date, when applicable.

Click **Manage** on any investigation to:

- Change the **status**. Moving to RESOLVED or CLOSED requires a **resolution summary** — a short explanation of what was found and what was done.
- **Assign** it to a specific official (so there is a clear owner).
- Update the **category** if the original classification was wrong.
- Add **notes** as the investigation progresses.

When you save a resolution, your official ID is recorded as `resolved_by` and the resolved date is timestamped. These details appear in the audit report.

### 7.3 When to escalate

Raise severity to HIGH or CRITICAL and, where appropriate, revert or cancel the election if any of the following are observed:

- Evidence that votes have been miscounted or missed.
- Reports of voters unable to vote despite being eligible.
- Evidence of biometric bypass, replay of ballot tokens, or duplicate votes.
- Any signal of tampering with the database or audit log.

Do not mark such investigations as RESOLVED without a clear written remedy and sign-off from an administrator.

---

## 8. Generating the Audit Report

> Administrators only.

1. On the home page, select the election or referendum in the dropdown.
2. Open the **Audit logs** tab.
3. Click **Download audit report (PDF)**.

The generated PDF is a complete, defensible record containing:

- **Election metadata** — title, type, allocation system, scope, status, dates.
- **Turnout summary** — total votes, number of constituencies reporting.
- **Ballot reconciliation** — tokens issued, tokens used, votes recorded, per-constituency breakdown. These numbers must match.
- **Voting-period integrity** — the official voting window, the earliest and latest recorded vote, and confirmation that all votes fell inside the window.
- **Biometric verification summary** — challenges issued, challenges completed, challenges expired.
- **Result summary** — total seats, majority threshold, winning party (for elections) or yes/no outcome (for referendums).
- **Seat allocation table** by party.
- **System event timeline** and **official activity log**.
- **Investigation summaries** — every incident raised against this contest, with its resolution.

The report deliberately contains **no voter-identifiable information**. It is safe to share with auditors, the Electoral Commission, or the public when the election has closed.

Save each generated report in your organisation's records. The filename includes the election title and the timestamp.

---

## 9. Managing Fellow Officials

> Administrators only.

Open **Manage officials**. The table lists every official (active and inactive) with name, username, email, role, and status.

### 9.1 Inviting a new official

Click **+ New official** and fill in:

- **First name**, **Last name**.
- **Email** — their work email; the invitation is sent here.
- **Role** — Election Officer or Administrator.

Click **Save**. The system:

1. Generates a username from the email (the portion before the `@`).
2. Generates a temporary password.
3. Emails the new official their credentials and the onboarding link.
4. Records you as the `created_by` of this account.

The new official will be prompted through onboarding on their first login (see [Section 2](#2-first-time-login-and-onboarding)).

### 9.2 Deactivating and reactivating

- **Deactivate** an active official when they no longer need access (left the role, left the organisation, moved to a different function). The account is preserved — deactivation only blocks login and disables their tokens. Inactive rows appear greyed out.
- **Reactivate** restores access with the existing credentials.

Prefer deactivation over deletion. A deactivated account keeps the person's history tied to the audit log.

### 9.3 Changing roles

Role changes are not edited from this table. Contact the system administrator or — in this system — have another administrator deactivate and re-invite with the correct role.

---

## 10. Profile and Session Management

The **Profile** page shows your name, email, username, and role badge.

- Your avatar is derived from your initials.
- Contact details are read-only here. If they need to change, contact an administrator.
- There is no "change password" option on the profile — passwords are only set during onboarding. To rotate your password, ask an administrator to issue a new temporary password; you will then run onboarding again.

Your access token refreshes automatically while you are working. If you are idle for long enough your session expires and you are returned to the login page.

After several failed login attempts the account is temporarily locked. If this happens to you, wait for the lockout window to expire or contact another administrator.

---

## 11. Good Practice and Escalation

- **Publish elections only when all checks are done.** Once an election is OPEN and voters are casting ballots, structural edits are no longer possible for integrity reasons.
- **Be specific when reporting an incident.** A precise description (what, where, when, who reported it) makes the investigation resolvable.
- **Always add a resolution summary when closing an investigation.** The audit report depends on it.
- **Download and archive the audit report** as soon as an election closes. It is your formal record.
- **Do not share credentials.** Every action is attributable to an individual official; sharing an account destroys that property.
- **Report suspected system tampering immediately.** Open a CRITICAL investigation and notify another administrator out-of-band. Do not rely only on the platform to flag the issue.

If you are unsure how to proceed — whether to close an election early, whether to cancel, how to resolve an ambiguous investigation — ask another administrator before acting. Reversible decisions (draft, close) are always safer than destructive ones (cancel).
