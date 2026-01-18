# 🎭 TruthSnap Scenario Flows

**Detailed documentation of scenario-based user flows**

---

## 📋 Table of Contents

- [Overview](#overview)
- [Adult Blackmail Scenario](#-adult-blackmail-scenario)
- [Teenager SOS Scenario](#-teenager-sos-scenario)
- [Scenario Context Propagation](#scenario-context-propagation)
- [Implementation Details](#implementation-details)

---

## Overview

TruthSnap implements **two distinct scenario-based flows** to provide tailored support for different user groups facing deepfake blackmail and sextortion.

### Design Principles

1. **Empathy-Driven**: Tone and messaging match user's emotional state
2. **Context-Aware**: All features adapt to scenario (forensic vs. supportive)
3. **Action-Oriented**: Clear next steps at every stage
4. **Privacy-First**: No data shared between scenarios without consent

### Scenario Selection

Users choose their scenario after `/start`:

```
👋 Welcome to TruthSnap

Choose your scenario:

┌─────────────────────────────────┐
│ 👤 I'm being blackmailed        │  ← Adult Blackmail
├─────────────────────────────────┤
│ 🆘 I need help (Teenager)       │  ← Teenager SOS
├─────────────────────────────────┤
│ 📚 Knowledge Base               │  ← Educational resources
└─────────────────────────────────┘
```

---

## 👤 Adult Blackmail Scenario

**Target Audience**: Adults (18+) being blackmailed with alleged intimate photos

**Tone**: Cold, clinical, professional, legal-focused

**Goal**: Provide forensic evidence and counter-attack strategies

### Flow Diagram

```
/start
  ↓
Scenario Selection
  ↓
[User clicks "👤 I'm being blackmailed"]
  ↓
┌─────────────────────────────────────────┐
│ Step 1: Evidence Collection            │
│ ──────────────────────────────────────  │
│ Message: "Send the blackmail photo"    │
│ Tone: Professional, no emotion         │
│ State: AdultBlackmailStates.           │
│        waiting_for_evidence             │
└─────────────────────────────────────────┘
  ↓
[User sends photo]
  ↓
┌─────────────────────────────────────────┐
│ Step 2: Analysis with Forensic Context │
│ ──────────────────────────────────────  │
│ • Upload to S3                          │
│ • Enqueue with scenario="adult_blackmail"│
│ • Worker analyzes photo                 │
│ • Generate SHA-256 hash                 │
│ • Create Report ID: ANL-YYYYMMDD-hash   │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│ Step 3: Results with Legal Evidence    │
│ ──────────────────────────────────────  │
│ Message format:                         │
│                                         │
│ ✅ ANALYSIS COMPLETE                    │
│                                         │
│ Verdict: AI-GENERATED                   │
│ Confidence: 94%                         │
│                                         │
│ FORENSIC IDENTITY                       │
│ • Report ID: ANL-20260118-abc123        │
│ • SHA-256: a3f8...                      │
│ • Timestamp: 2026-01-18 14:32:15 UTC    │
│                                         │
│ This constitutes forensic evidence.     │
│                                         │
│ [📄 Get Forensic PDF]                   │
│ [🛡️ Counter-measures]                   │
│ [🔙 Back to Main Menu]                  │
└─────────────────────────────────────────┘
  ↓
[User clicks "🛡️ Counter-measures"]
  ↓
┌─────────────────────────────────────────┐
│ Step 4: Counter-Measures Menu          │
│ ──────────────────────────────────────  │
│ 🛡️ COUNTER-MEASURES                     │
│                                         │
│ Available strategies:                   │
│                                         │
│ 💬 Safe Response Generator              │
│    → AI-crafted responses citing        │
│      forensic evidence                  │
│                                         │
│ 🚫 StopNCII                             │
│    → Report to prevent online spread    │
│                                         │
│ 🚨 FBI IC3                              │
│    → Official Internet Crime Complaint  │
│                                         │
│ 📄 Forensic PDF                         │
│    → Legal-grade report with SHA-256    │
│                                         │
│ ⚠️ Never pay a blackmailer.             │
│                                         │
│ [💬 Generate Safe Response]             │
│ [🚫 Report to StopNCII] (link)          │
│ [🚨 Report to FBI IC3] (link)           │
│ [📄 Download PDF Report]                │
│ [🔙 Back]                               │
└─────────────────────────────────────────┘
  ↓
[User clicks "💬 Generate Safe Response"]
  ↓
┌─────────────────────────────────────────┐
│ Step 5: Safe Response Templates        │
│ ──────────────────────────────────────  │
│ 💬 SAFE RESPONSE TEMPLATES              │
│                                         │
│ Copy and customize:                     │
│                                         │
│ ──────────────────────────────────────  │
│                                         │
│ 1. Professional - Forensic Evidence     │
│                                         │
│ I have submitted your image to          │
│ professional forensic analysis. The     │
│ report confirms it is AI-generated      │
│ with a confidence score of [X]%.        │
│                                         │
│ I have documented this incident with:   │
│ • SHA-256 hash: [HASH]                  │
│ • Report ID: [ID]                       │
│ • Timestamp: [TIME]                     │
│                                         │
│ This has been reported to cybercrime    │
│ authorities. Any further contact will   │
│ be forwarded to law enforcement.        │
│                                         │
│ ──────────────────────────────────────  │
│                                         │
│ 2. Legal Notice                         │
│ [... additional templates ...]          │
│                                         │
│ ⚠️ Usage notes:                         │
│ • Replace [X], [HASH], [ID], [TIME]     │
│ • Send ONCE, then block                 │
│ • Do not engage in conversation         │
│                                         │
│ [🔙 Back to Counter-measures]           │
│ [🏠 Main Menu]                          │
└─────────────────────────────────────────┘
```

### Key Features

#### 1. Forensic Evidence
- **SHA-256 Hash**: Cryptographic proof of image identity
- **Report ID**: Unique identifier (ANL-YYYYMMDD-hash)
- **Timestamp**: UTC timestamp for legal documentation
- **PDF Report**: Legal-grade document with official disclaimer

#### 2. Safe Response Generator
Provides 4 templates:
1. **Professional - Forensic Evidence**: Cites analysis, hash, report ID
2. **Legal Notice**: References federal laws (18 U.S.C. § 875)
3. **Technical - AI Detection**: Lists detection methods
4. **Brief - No Negotiation**: Short, firm refusal

#### 3. Reporting Resources
- **StopNCII**: https://stopncii.org - Image removal service
- **FBI IC3**: https://ic3.gov - Internet Crime Complaint Center
- **Knowledge Base**: AI deepfake education

### Message Tone Examples

**Analysis Result (Adult)**:
```
✅ ANALYSIS COMPLETE

Verdict: AI-GENERATED
Confidence: 94%

━━━━━━━━━━━━━━━━━━━━━━

FORENSIC IDENTITY
• Report ID: ANL-20260118-abc123
• SHA-256: a3f8...
• Timestamp: 2026-01-18 14:32:15 UTC

━━━━━━━━━━━━━━━━━━━━━━

This analysis constitutes forensic evidence.
The report includes cryptographic proof of
the image's AI-generated nature.

Next steps:
1. Download PDF report
2. Use Safe Response templates
3. Report to authorities
```

**Counter-Measures (Adult)**:
```
🛡️ COUNTER-MEASURES

⚠️ Important: Never pay a blackmailer.
Payment increases demands and funds criminal networks.

Available strategies:

💬 Safe Response Generator
   → AI-crafted responses citing your forensic evidence

🚫 StopNCII
   → Report intimate images to prevent online spread

🚨 FBI IC3
   → Official Internet Crime Complaint Center
```

---

## 🆘 Teenager SOS Scenario

**Target Audience**: Teenagers (13-17) facing sextortion

**Tone**: Empathetic, supportive, educational

**Goal**: Calm victim, provide parental support, enable reporting

### Flow Diagram

```
/start
  ↓
Scenario Selection
  ↓
[User clicks "🆘 I need help (Teenager)"]
  ↓
┌─────────────────────────────────────────┐
│ Step 1: Psychological Stop Message     │
│ ──────────────────────────────────────  │
│ Message:                                │
│                                         │
│ 🆘 STOP. BREATHE.                       │
│                                         │
│ You are safe right now.                 │
│                                         │
│ What you're experiencing is called      │
│ "sextortion." It's a crime, and it's    │
│ NOT YOUR FAULT.                         │
│                                         │
│ Here's what we're going to do:          │
│ 1. Prove the photo is fake (AI-made)   │
│ 2. Give you a report to show parents   │
│ 3. Show you how to report this safely  │
│                                         │
│ You're not alone. Thousands of people   │
│ have been through this.                 │
│                                         │
│ Ready? Send me the photo they're        │
│ threatening you with.                   │
│                                         │
│ [📸 Send Photo]                         │
│ [🔙 Back to Main Menu]                  │
│                                         │
│ State: TeenagerSOSStates.               │
│        psychological_stop                │
└─────────────────────────────────────────┘
  ↓
[User sends photo]
  ↓
┌─────────────────────────────────────────┐
│ Step 2: Analysis with Empathetic Tone  │
│ ──────────────────────────────────────  │
│ • Upload to S3                          │
│ • Enqueue with scenario="teenager_sos"  │
│ • Worker analyzes photo                 │
│ • Generate PDF with simple language     │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│ Step 3: Results with Simple Language   │
│ ──────────────────────────────────────  │
│ Message format:                         │
│                                         │
│ ✅ GOOD NEWS                            │
│                                         │
│ This photo is AI-GENERATED.             │
│ (A computer made it, not a real camera) │
│                                         │
│ Confidence: 94%                         │
│ (That's really high!)                   │
│                                         │
│ What this means:                        │
│ • This is NOT a real photo of you       │
│ • You have PROOF it's fake              │
│ • The blackmailer is a scammer          │
│                                         │
│ What you should do next:                │
│                                         │
│ [📄 Get PDF Report]                     │
│    → Show this to your parents          │
│                                         │
│ [🤝 How to tell my parents]             │
│    → We'll help you explain             │
│                                         │
│ [🚫 Stop the Spread]                    │
│    → Prevent them from sharing it       │
│                                         │
│ [📚 What is sextortion?]                │
│    → Learn more (it's not your fault)   │
│                                         │
│ [🔙 Back to Main Menu]                  │
└─────────────────────────────────────────┘
  ↓
[User clicks "🤝 How to tell my parents"]
  ↓
┌─────────────────────────────────────────┐
│ Step 4: Parent Communication Helper    │
│ ──────────────────────────────────────  │
│ 🤝 HOW TO TELL YOUR PARENTS             │
│                                         │
│ Why tell them?                          │
│ • They can help you report this         │
│ • They can contact police if needed     │
│ • You don't have to handle this alone   │
│ • It's easier when you have proof       │
│                                         │
│ ──────────────────────────────────────  │
│                                         │
│ What to say:                            │
│                                         │
│ "I need to show you something serious.  │
│ Someone sent me a fake photo and is     │
│ trying to blackmail me with it. I got   │
│ it analyzed by TruthSnap, and here's    │
│ the proof it's AI-generated."           │
│                                         │
│ Then show them the PDF report.          │
│                                         │
│ ──────────────────────────────────────  │
│                                         │
│ What evidence to show:                  │
│                                         │
│ 1. PDF Report - This has:               │
│    • AI detection score                 │
│    • Technical analysis                 │
│    • Official disclaimer                │
│                                         │
│ 2. Screenshots of blackmail messages    │
│                                         │
│ ──────────────────────────────────────  │
│                                         │
│ What they'll probably ask:              │
│                                         │
│ ❓ "Are you sure it's fake?"            │
│ → "Yes, the report shows an AI score    │
│    of [X]%."                            │
│                                         │
│ ❓ "Did you send anyone photos?"        │
│ → Be honest. Even if you did,           │
│    blackmail is STILL illegal.          │
│                                         │
│ [📄 Get PDF Report (Show to parents)]   │
│ [💬 See conversation script]            │
│ [🔙 Back]                               │
└─────────────────────────────────────────┘
  ↓
[User clicks "💬 See conversation script"]
  ↓
┌─────────────────────────────────────────┐
│ Step 5: Detailed Conversation Script   │
│ ──────────────────────────────────────  │
│ 💬 CONVERSATION SCRIPT                  │
│                                         │
│ Step 1: Choose the right time           │
│ • When they're not busy or stressed     │
│ • In private (not in front of siblings) │
│ • When you feel calm enough to explain  │
│                                         │
│ ──────────────────────────────────────  │
│                                         │
│ Step 2: Opening line                    │
│                                         │
│ "Mom/Dad, I need to talk to you about   │
│ something serious. I'm okay, but I      │
│ need your help with something."         │
│                                         │
│ ──────────────────────────────────────  │
│                                         │
│ Step 3: Explain what happened           │
│                                         │
│ "Someone online created a fake photo    │
│ of me and is trying to blackmail me.    │
│ I didn't do anything wrong, but I'm     │
│ scared."                                │
│                                         │
│ ──────────────────────────────────────  │
│                                         │
│ Step 4: Show the evidence               │
│                                         │
│ "I used TruthSnap to analyze the photo. │
│ Here's the report - it proves the       │
│ photo is AI-generated."                 │
│                                         │
│ [Show PDF report]                       │
│                                         │
│ [... more steps ...]                    │
│                                         │
│ [🔙 Back]                               │
│ [🏠 Main Menu]                          │
└─────────────────────────────────────────┘
```

### Alternative Path: Stop the Spread

```
[User clicks "🚫 Stop the Spread"]
  ↓
┌─────────────────────────────────────────┐
│ Emergency Protection Resources          │
│ ──────────────────────────────────────  │
│ 🚫 STOP THE SPREAD                      │
│                                         │
│ What is Take It Down?                   │
│                                         │
│ Take It Down is a FREE service by NCMEC │
│ (National Center for Missing & Exploited│
│ Children).                              │
│                                         │
│ It helps remove intimate images from:   │
│ • Facebook                              │
│ • Instagram                             │
│ • TikTok                                │
│ • Snapchat                              │
│ • OnlyFans                              │
│ • And 20+ other platforms               │
│                                         │
│ ──────────────────────────────────────  │
│                                         │
│ How does it work?                       │
│                                         │
│ 1. You create a "hash" of the image     │
│    (a unique fingerprint)               │
│ 2. NCMEC shares that hash with platforms│
│ 3. Platforms automatically block it     │
│                                         │
│ Important: You DON'T upload the actual  │
│ photo! The hash is created on YOUR      │
│ device, privately.                      │
│                                         │
│ ──────────────────────────────────────  │
│                                         │
│ Is it anonymous?                        │
│                                         │
│ Yes! You can use it WITHOUT:            │
│ • Giving your name                      │
│ • Showing your face                     │
│ • Filing a police report                │
│                                         │
│ [🔗 Take It Down (Anonymous Removal)]   │
│    (https://takeitdown.ncmec.org/)      │
│                                         │
│ [📱 FBI Tips for Teens]                 │
│    (fbi.gov link)                       │
│                                         │
│ [🚨 Report to NCMEC]                    │
│    (https://report.cybertip.org)        │
│                                         │
│ [🔙 Back]                               │
│ [🏠 Main Menu]                          │
└─────────────────────────────────────────┘
```

### Key Features

#### 1. Psychological Stop Message
- **Calming tone**: "STOP. BREATHE."
- **Reassurance**: "You are safe right now."
- **Not your fault**: Explicitly stated multiple times
- **Clear next steps**: Numbered list of actions

#### 2. Parent Communication Helper
- **Conversation script**: Step-by-step guide
- **What to say**: Exact wording suggestions
- **What they'll ask**: Prepared answers to common questions
- **Evidence to show**: PDF report, screenshots

#### 3. Emergency Protection
- **Take It Down**: NCMEC anonymous image removal
- **FBI Tips for Teens**: Educational resources
- **CyberTipline**: Reporting mechanism

#### 4. Educational Content
- **What is sextortion?**: Definition and how it works
- **Statistics**: "1 in 7 teens experience sextortion"
- **Why you shouldn't feel ashamed**: Reassurance
- **How AI changed sextortion**: Technical explanation

### Message Tone Examples

**Analysis Result (Teenager)**:
```
✅ GOOD NEWS

This photo is AI-GENERATED.
(A computer made it, not a real camera)

Confidence: 94%
(That's really high!)

━━━━━━━━━━━━━━━━━━━━━━

What this means:
• This is NOT a real photo of you
• You have PROOF it's fake
• The blackmailer is a scammer

You're going to be okay. 💙

This happens to thousands of people.
With the right steps, this will be over soon.
```

**Parent Communication (Teenager)**:
```
🤝 HOW TO TELL YOUR PARENTS

Remember:
• Your parents will probably be shocked at first
• They might be angry at the blackmailer, not you
• Having the report makes this conversation much easier
• This happens to thousands of people - you're not alone

💡 Final tip: If you absolutely can't tell your
parents, talk to another trusted adult:
• School counselor
• Teacher
• Older sibling
• Coach or mentor

You don't have to do this alone.
```

---

## Scenario Context Propagation

Scenarios are propagated through the entire analysis pipeline:

### 1. User Selection → FSM State

```python
# bot/handlers/scenarios.py

@router.callback_query(F.data == "scenario:adult_blackmail")
async def scenario_adult_blackmail(callback: CallbackQuery, state: FSMContext):
    # Set FSM state
    await state.set_state(AdultBlackmailStates.waiting_for_evidence)

    # Store scenario in FSM context
    await state.update_data(scenario="adult_blackmail")
```

### 2. Photo Upload → Queue

```python
# bot/handlers/scenarios.py

@router.message(AdultBlackmailStates.waiting_for_evidence, F.photo)
async def adult_blackmail_photo(message: Message, state: FSMContext):
    # Get scenario from FSM context
    data = await state.get_data()
    scenario = data.get("scenario", "adult_blackmail")

    # Enqueue with scenario context
    job_id = queue_service.enqueue_analysis(
        user_id=user_id,
        chat_id=chat_id,
        message_id=message_id,
        photo_s3_key=s3_key,
        tier=tier,
        scenario=scenario  # ← Scenario passed to worker
    )
```

### 3. Queue → Worker

```python
# services/queue.py

def enqueue_analysis(
    self,
    user_id: int,
    chat_id: int,
    message_id: int,
    photo_s3_key: str,
    tier: str,
    priority: str = "default",
    scenario: str = None  # ← Scenario parameter
) -> str:
    job = self.queue.enqueue(
        'app.workers.tasks.analyze_photo_task',
        user_id,
        chat_id,
        message_id,
        photo_s3_key,
        tier,
        scenario  # ← Passed to worker
    )
    return job.id
```

### 4. Worker → Database

```python
# workers/tasks.py

def analyze_photo_task(
    user_id: int,
    chat_id: int,
    message_id: int,
    photo_s3_key: str,
    tier: str,
    scenario: str = None  # ← Scenario received
):
    # ... analysis code ...

    # Save to database with scenario
    analysis_repo.create_analysis(
        user_id=user_id,
        verdict=verdict,
        confidence=confidence,
        scenario=scenario,  # ← Stored in DB
        result_json=result
    )
```

### 5. Worker → Notification

```python
# workers/tasks.py

asyncio.run(
    notifier.send_analysis_result(
        chat_id=chat_id,
        message_id=message_id,
        result=result,
        tier=user_tier,
        analysis_id=analysis_id,
        scenario=scenario  # ← Passed to notifier
    )
)
```

### 6. Notification → Scenario-Specific Response

```python
# services/notifications.py

async def send_analysis_result(
    self,
    chat_id: int,
    message_id: int,
    result: dict,
    tier: str,
    analysis_id: str,
    scenario: str = None  # ← Scenario received
):
    if scenario == "adult_blackmail":
        # Clinical tone, forensic evidence
        keyboard = get_adult_blackmail_step1_keyboard()

    elif scenario == "teenager_sos":
        # Empathetic tone, simple language
        keyboard = get_teenager_step2_keyboard()

    else:
        # Legacy flow (no scenario)
        keyboard = get_default_keyboard()
```

### Data Flow Diagram

```
User Selection
     ↓
   scenario="adult_blackmail"
     ↓
FSM State.update_data(scenario)
     ↓
Photo Upload Handler
     ↓
queue.enqueue_analysis(..., scenario)
     ↓
Redis Queue Job
{
  "user_id": 123,
  "photo_s3_key": "...",
  "scenario": "adult_blackmail"  ← Persisted
}
     ↓
RQ Worker picks job
     ↓
analyze_photo_task(..., scenario)
     ↓
database.create_analysis(..., scenario)  ← Stored
     ↓
notifier.send_result(..., scenario)
     ↓
Scenario-specific keyboard + message
```

---

## Implementation Details

### File Structure

```
truthsnap-bot/app/bot/
├── handlers/
│   ├── scenarios.py          # Main scenario flows
│   ├── counter_measures.py   # Adult: Counter-measures
│   └── parent_support.py     # Teenager: Parent helper
├── keyboards/
│   └── scenarios.py          # Inline keyboards
└── states.py                 # FSM state definitions
```

### Key Handlers

#### 1. Scenario Selection (`scenarios.py`)

```python
@router.callback_query(F.data == "scenario:select")
async def scenario_back_to_selection(callback: CallbackQuery, state: FSMContext):
    """Return to scenario selection (delete old message)"""
    try:
        await callback.message.delete()
    except:
        pass

    await callback.message.answer(
        "👋 Welcome to TruthSnap\n\nChoose your scenario:",
        reply_markup=get_scenario_selection_keyboard()
    )

    await state.clear()
    await state.set_state(ScenarioStates.selecting_scenario)
```

#### 2. Adult Blackmail Entry (`scenarios.py`)

```python
@router.callback_query(F.data == "scenario:adult_blackmail")
async def scenario_adult_blackmail(callback: CallbackQuery, state: FSMContext):
    """Entry point for Adult Blackmail scenario"""
    await callback.message.edit_text(
        "👤 <b>Blackmail Evidence Analysis</b>\n\n"
        "Send the photo you're being blackmailed with.\n\n"
        "We will provide:\n"
        "• Forensic analysis\n"
        "• SHA-256 hash\n"
        "• Legal-grade PDF report\n\n"
        "This evidence can be used with authorities.",
        parse_mode="HTML"
    )

    await state.set_state(AdultBlackmailStates.waiting_for_evidence)
    await state.update_data(scenario="adult_blackmail")
    await callback.answer()
```

#### 3. Teenager SOS Entry (`scenarios.py`)

```python
@router.callback_query(F.data == "scenario:teenager_sos")
async def scenario_teenager_sos(callback: CallbackQuery, state: FSMContext):
    """Entry point for Teenager SOS scenario"""
    await callback.message.edit_text(
        "🆘 <b>STOP. BREATHE.</b>\n\n"
        "You are safe right now.\n\n"
        "What you're experiencing is called \"sextortion.\" "
        "It's a crime, and it's <b>NOT YOUR FAULT</b>.\n\n"
        "Here's what we're going to do:\n"
        "1. Prove the photo is fake (AI-made)\n"
        "2. Give you a report to show parents\n"
        "3. Show you how to report this safely\n\n"
        "You're not alone. Thousands of people have been through this.\n\n"
        "Ready? Send me the photo they're threatening you with.",
        parse_mode="HTML"
    )

    await state.set_state(TeenagerSOSStates.psychological_stop)
    await state.update_data(scenario="teenager_sos")
    await callback.answer()
```

#### 4. Counter-Measures (`counter_measures.py`)

```python
@router.callback_query(F.data == "counter:safe_response")
async def generate_safe_response(callback: CallbackQuery):
    """Generate safe response templates"""
    templates = [
        {
            "name": "Professional - Forensic Evidence",
            "text": "I have submitted your image to professional forensic analysis..."
        },
        {
            "name": "Legal Notice",
            "text": "This constitutes formal notice..."
        },
        # ... more templates
    ]

    # Format and send templates
    await callback.message.edit_text(response_text, parse_mode="HTML")
```

#### 5. Parent Support (`parent_support.py`)

```python
@router.callback_query(F.data == "teen:tell_parents")
async def show_tell_parents_guide(callback: CallbackQuery):
    """Show guide on how to tell parents"""
    await callback.message.edit_text(
        "🤝 <b>How to Tell Your Parents</b>\n\n"
        "Why tell them?\n"
        "• They can help you report this\n"
        "• You don't have to handle this alone\n\n"
        "What to say:\n"
        "\"I need to show you something serious...\"\n\n"
        "[📄 Get PDF Report (Show to parents)]\n"
        "[💬 See conversation script]",
        parse_mode="HTML",
        reply_markup=get_tell_parents_keyboard(analysis_id)
    )
```

### Database Schema

```sql
CREATE TABLE analyses (
    id SERIAL PRIMARY KEY,
    analysis_id VARCHAR(50) UNIQUE,
    user_id BIGINT REFERENCES users(user_id),
    scenario VARCHAR(20),  -- 'adult_blackmail', 'teenager_sos', NULL (legacy)
    verdict VARCHAR(20),
    confidence FLOAT,
    result_json JSONB,
    image_hash VARCHAR(64),  -- SHA-256
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_analyses_scenario ON analyses(scenario);
```

### PDF Report Differences

**Adult Blackmail PDF**:
- Section: "FORENSIC IDENTITY"
- Includes: Report ID, SHA-256 hash, timestamp
- Tone: Clinical, legal terminology
- Disclaimer: "Acceptable as supporting evidence in court"

**Teenager SOS PDF**:
- Section: "REPORT SUMMARY"
- Includes: Simple AI score, "What this means" section
- Tone: Simple language, reassuring
- Disclaimer: "Show this to a trusted adult"

---

## Testing Scenarios

### Test Adult Blackmail Flow

1. Start bot: `/start`
2. Click "👤 I'm being blackmailed"
3. Upload test photo
4. Verify:
   - Clinical tone in results
   - SHA-256 hash displayed
   - Report ID format: ANL-YYYYMMDD-hash
   - "Counter-measures" button appears
5. Click "🛡️ Counter-measures"
6. Verify:
   - Safe Response Generator option
   - StopNCII link
   - FBI IC3 link
7. Click "💬 Generate Safe Response"
8. Verify 4 templates displayed

### Test Teenager SOS Flow

1. Start bot: `/start`
2. Click "🆘 I need help (Teenager)"
3. Verify calming message: "STOP. BREATHE."
4. Upload test photo
5. Verify:
   - Empathetic tone in results
   - Simple language ("A computer made it")
   - Supportive keywords ("You're going to be okay")
   - "How to tell my parents" button appears
6. Click "🤝 How to tell my parents"
7. Verify conversation script displayed
8. Click "💬 See conversation script"
9. Verify step-by-step guide
10. Click "🚫 Stop the Spread"
11. Verify:
    - Take It Down explanation
    - NCMEC links
    - Anonymous process described

---

## Future Enhancements

### Planned Scenarios

1. **🏢 Corporate Fraud** (B2B)
   - Tone: Enterprise, compliance-focused
   - Features: Batch processing, API integration
   - Reporting: Compliance dashboard, audit logs

2. **👨‍⚖️ Legal Evidence** (Lawyers)
   - Tone: Legal professional, certified reports
   - Features: Chain of custody, notarized PDFs
   - Integration: Court evidence systems

3. **📱 Social Media Verification** (Influencers)
   - Tone: Casual, brand protection
   - Features: Bulk verification, brand monitoring
   - Integration: Platform APIs

### Feature Roadmap

- [ ] Multi-language support (Spanish, French, etc.)
- [ ] Video analysis for sextortion scenarios
- [ ] Live chat with counselors (Teenager SOS)
- [ ] Automated reporting to authorities
- [ ] Parent notification system (opt-in)
- [ ] Anonymous peer support groups

---

**Built with empathy to fight deepfake blackmail** 💙
