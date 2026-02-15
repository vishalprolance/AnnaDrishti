# ANNA DRISHTI (अन्नदृष्टि) — Sell Smarter. Process Surplus. Farm With Dignity.

### *"Your farmer doesn't need another dashboard. They need someone who picks up the phone and gets them a better deal. We built that someone."*

**AI for Rural Innovation & Sustainable Systems — Complete Spec Sheet**

---

# THE THESIS

There are 120 million farming households in India. They produce ₹30 lakh crore worth of food every year. They capture less than 28% of the final retail value.

Not because the produce is bad. Not because demand is missing.

**Because nobody acts on their behalf.**

A rich farmer has agents, brokers, and mandi connections. They negotiate, time the market, divert surplus to processors, and access institutional credit.

A poor farmer has a mobile phone and last year's memory.

We call the gap between **knowing what to do** and **being able to do it** the **Agency Gap.**

The Tata-Cornell Institute's research on smallholder decision-making found that access to market price information alone changes farmer selling behavior in **less than 12% of cases.** The barrier is not knowledge. It is the logistical, bureaucratic, and negotiation burden of acting on that knowledge — while simultaneously running a farm.

| What the farmer needs to do | Why they can't do it today |
|-----------------------------|---------------------------|
| Sell at the best mandi in 100km | Can't check 8 mandis + call 5 buyers + compare transport costs — while harvesting |
| Divert surplus to processing before crash | No relationship with processors. No logistics. No quality standards knowledge |
| Time their sale for best price window | No price forecasting capability. Sell when harvested, not when optimal |
| Aggregate with neighbors for transport leverage | Coordination cost is too high without a broker |

### What This Costs — Conservatively

| Loss vector | Annual estimate | Basis |
|-------------|----------------|-------|
| Selling at the nearest (not best) mandi | ₹25,000-40,000 per farmer/year | Studies show 30-45% price dispersion across mandis within 100km radius |
| Crash-price selling during gluts | ₹50,000-90,000 crore total (All India Kisan Sabha, 2024-25) | Cobweb cycle: oversupply → crash → losses below production cost |
| Surplus left unharvested or sold at transport-loss prices | Unmeasured but widespread | Kolar 2024: tomato ₹2-5/kg, farmers abandoned crops |

> **Anna Drishti doesn't advise. It executes.**
>
> The farmer says: *"Bech do."* (Sell it.)
> The system handles the rest — with the farmer's explicit confirmation before any deal closes.

---

# WHAT ANNA DRISHTI ACTUALLY IS

Anna Drishti is an **AI-assisted selling and surplus management system** for Farmer Producer Organizations (FPOs). It operates via IVR (any phone) and WhatsApp.

**It does two things exceptionally well:**

### 1. SELL AGENT — Find the best buyer and negotiate the best price

When a farmer signals harvest readiness (voice call or WhatsApp message), the system:
- Scans live prices across nearby mandis (Agmarknet data)
- Estimates yield and matches with nearby demand (satellite-assisted)
- Aggregates with neighboring farmers for transport efficiency
- Contacts verified buyers on WhatsApp with a structured offer
- Conducts price negotiation within hard-coded guardrails
- Presents the best deal to the farmer for **explicit confirmation**
- Tracks pickup and payment post-sale

### 2. PROCESS AGENT — Divert surplus to processing before crash

When the system detects that the FPO's combined harvest volume will exceed what nearby mandis can absorb at stable prices:
- Calculates the optimal split between fresh market and processing
- Matches surplus volume with pre-onboarded micro-processing partners
- Routes produce to processing (paste, dried, powder) at contracted rates
- Ensures fresh market sellers get higher prices because supply pressure is reduced

**Everything else — insurance prefilling, scheme discovery, credit readiness scoring — exists as lightweight background features, not as autonomous agents.** They surface opportunities and prepare paperwork; the farmer or FPO coordinator makes the final decision.

---

# HOW A TRANSACTION ACTUALLY WORKS

A farmer in Nashik calls the Anna Drishti IVR number (toll-free, any phone):

**"Mere tamatar tayyar hain, bech do."**
*(My tomatoes are ready, sell them.)*

```
 ┌──────────────────────────────────────────────────────────────────┐
 │  STEP 1: UNDERSTAND INTENT                                      │
 │  Voice → Whisper STT → IndicBERT intent classifier               │
 │  Parsed: {intent: "sell", crop: "tomato", status: "harvest-ready"}│
 │  Farmer identified from registered FPO member list                │
 │  Plot: 2.1 acres, Sinnar block, Nashik                           │
 └───────────────────────────┬──────────────────────────────────────┘
                             │
 ┌───────────────────────────▼──────────────────────────────────────┐
 │  STEP 2: SATELLITE CONTEXT (Assistive, Not Definitive)           │
 │  Query Sentinel-2 (last pass: 3 days ago)                        │
 │  NDVI trajectory: declining from 0.68 → 0.52 (consistent with   │
 │  harvest-stage tomato in this region/season)                      │
 │                                                                   │
 │  Yield ESTIMATE: ~2.0-2.6 tonnes (based on plot area ×           │
 │  regional yield averages, NOT presented as precise measurement)   │
 │                                                                   │
 │  NOTE: Satellite data provides directional context only.          │
 │  Actual quantity confirmed by farmer during confirmation call.    │
 └───────────────────────────┬──────────────────────────────────────┘
                             │
 ┌───────────────────────────▼──────────────────────────────────────┐
 │  STEP 3: MARKET SCAN (Real Data, Real-Time)                      │
 │  Agmarknet scraper pulls last 24hr prices from mandis ≤100km:    │
 │                                                                   │
 │  Mandi          Avg Price  Arrivals   Est. Transport  Net to     │
 │                 (₹/kg)     (tonnes)   Cost (₹)        Farmer     │
 │  ──────────────────────────────────────────────────────────────── │
 │  Sinnar          ₹16        340        ₹800           ₹15.65/kg │
 │  Nashik APMC     ₹19        520        ₹1,400         ₹18.39/kg │
 │  Pune (Gultekdi) ₹28        890        ₹5,800         ₹25.48/kg │
 │  Mumbai APMC     ₹32        1,400      ₹8,200         ₹28.43/kg │
 │                                                                   │
 │  Price trend (LightGBM 48hr forecast): Pune likely stable/+₹1   │
 │  (weekend demand), Nashik likely -₹2 (rising arrivals)           │
 │                                                                   │
 │  >>> RECOMMENDATION: Target Pune/Mumbai buyers                   │
 └───────────────────────────┬──────────────────────────────────────┘
                             │
 ┌───────────────────────────▼──────────────────────────────────────┐
 │  STEP 4: SURPLUS CHECK — THE PROCESSING PIVOT                    │
 │                                                                   │
 │  FPO-level harvest data (from IVR calls received this week):      │
 │  • 14 farmers signaled tomato harvest-ready                       │
 │  • Reported combined volume: ~30T                                 │
 │  • Historical mandi absorption at current prices: ~18-22T/week   │
 │  • Risk signal: if >25T hits mandis, price likely drops 30-40%   │
 │                                                                   │
 │  >>> PROCESSING DIVERSION RECOMMENDED                            │
 │                                                                   │
 │  Pre-onboarded processor check:                                   │
 │  ┌─────────────────────────────────────────────────────────────┐ │
 │  │ Partner          Type           Avail    Contract Rate      │ │
 │  │ Sai Agro Foods   Tomato paste   5T/wk    ₹30-34/kg         │ │
 │  │ Krishi Proc.     Sun-dried      2T/wk    ₹35-40/kg         │ │
 │  │ (Pre-onboarded during pilot setup; LOIs signed)             │ │
 │  └─────────────────────────────────────────────────────────────┘ │
 │                                                                   │
 │  PROPOSED SPLIT (subject to farmer confirmation):                 │
 │  • ~22T → Fresh market (Pune/Mumbai buyers)                      │
 │  • ~5T → Sai Agro (paste) @ ₹32/kg                              │
 │  • ~2T → Krishi Proc. (sun-dried) @ ₹38/kg                      │
 │  • ~1T → Remaining to nearest mandi (overflow)                   │
 │                                                                   │
 │  By absorbing 7T into processing, mandi supply drops to ~22T     │
 │  → price holds at ~₹24-28/kg instead of crashing to ₹12-15/kg  │
 └───────────────────────────┬──────────────────────────────────────┘
                             │
 ┌───────────────────────────▼──────────────────────────────────────┐
 │  STEP 5: NEIGHBOR AGGREGATION                                    │
 │  System identifies 2 nearby farmers with compatible produce:      │
 │  • Ramesh Patil: ~2.3T (1.6T fresh, 0.7T processing)            │
 │  • Sunita Jadhav: ~1.8T (all fresh)                              │
 │  • Ganesh More: ~3.1T (2.2T fresh, 0.9T processing)             │
 │  Combined fresh load: ~5.6T → shared truck, 40% lower transport  │
 │  Each farmer called separately for confirmation                   │
 └───────────────────────────┬──────────────────────────────────────┘
                             │
 ┌───────────────────────────▼──────────────────────────────────────┐
 │  STEP 6: BUYER OUTREACH + NEGOTIATION (WhatsApp)                 │
 │                                                                   │
 │  System contacts 3-4 pre-verified buyers from FPO's network:     │
 │                                                                   │
 │  To Buyer (Pune):                                                 │
 │  "Namaste Sharma ji. Nashik FPO se 5.6 tonne tomato available    │
 │   hai, kal pickup ke liye. Grade details: season average quality. │
 │   Single load, aggregated. ₹26/kg minimum. Interested?"          │
 │                                                                   │
 │  Buyer: "₹23 dunga"                                              │
 │                                                                   │
 │  System (within guardrails):                                      │
 │  "₹23 market rate se neeche hai Sharma ji. Pune mein aaj ₹28    │
 │   chal raha hai. Single load mein 5.6T, aapka sorting cost       │
 │   bachega. ₹26 fair rate hai."                                    │
 │                                                                   │
 │  Buyer: "₹25 final, with pickup"                                 │
 │                                                                   │
 │  System: "₹25.50 with pickup, UPI same day. ₹26 without pickup. │
 │   Jo suit kare."                                                   │
 │                                                                   │
 │  Buyer: "₹25.50 done. Truck kal subah 6 baje."                  │
 │                                                                   │
 │  >>> TENTATIVE DEAL: ₹25.50/kg, 5.6T, pickup Thursday 6AM       │
 │                                                                   │
 │  HARD CONSTRAINTS (never overridden):                             │
 │  • Floor price = max(production cost estimate, lowest mandi net)  │
 │  • No commitment made without farmer confirmation call            │
 │  • All negotiation messages logged for audit                      │
 │  • System CANNOT finalize deal — only recommend and await "Haan"  │
 └───────────────────────────┬──────────────────────────────────────┘
                             │
 ┌───────────────────────────▼──────────────────────────────────────┐
 │  STEP 7: FARMER CONFIRMATION (IVR Callback — Mandatory)          │
 │                                                                   │
 │  "Ramesh bhai, aapke tamatar ke liye ek acchi deal mili hai.     │
 │                                                                   │
 │   Takriban 1,600 kilo fresh market — ₹25.50 per kilo.           │
 │   Truck kal subah 6 baje aayega.                                  │
 │   Takriban 700 kilo processing — ₹32 per kilo.                   │
 │   Sai Agro pickup kal 8 baje.                                     │
 │                                                                   │
 │   Total lagbhag: ₹63,200.                                        │
 │   Payment UPI se, pickup ke 4-6 ghante mein.                      │
 │                                                                   │
 │   YEH DEAL TABHI CONFIRM HOGI JAB AAP HAAN BOLENGE.              │
 │   Haan bolein toh confirm, naa bolein toh cancel."                │
 │                                                                   │
 │  Ramesh: "Haan."                                                  │
 │                                                                   │
 │  >>> CONFIRMED. Buyer notified. Processor notified. Timer set.    │
 └───────────────────────────┬──────────────────────────────────────┘
                             │
 ┌───────────────────────────▼──────────────────────────────────────┐
 │  STEP 8: POST-TRANSACTION TRACKING                               │
 │  • Payment tracked: ₹63,200 UPI — confirmed or escalated         │
 │  • SMS receipt sent to farmer                                     │
 │  • Transaction logged in farmer's digital ledger                  │
 │  • If payment delayed >6hrs → FPO coordinator alerted            │
 │  • If payment fails → dispute workflow triggered (human-managed) │
 └──────────────────────────────────────────────────────────────────┘
```

### What This Illustrates (With Honest Caveats)

| Metric | In This Scenario | Assumptions |
|--------|-----------------|-------------|
| Farmer time spent | ~4 minutes (2 calls) | Farmer is reachable by phone |
| System actions between calls | 30+ (scan, match, aggregate, outreach, negotiate) | Buyer responds within 4-6 hours |
| Income: nearest mandi (₹16/kg) | ~₹36,800 | Selling full quantity at Sinnar |
| Income: Anna Drishti (blended ₹27.50/kg) | ~₹63,200 | Deal closes as illustrated |
| **Income difference** | **+₹26,400 in this scenario** | Actual results vary by crop, season, and market |
| What processing prevented | Mandi crash from ₹26 to ₹12-15/kg for ALL 14 FPO farmers | Based on historical glut events (Nashik 2024) |

> **We do not claim "+78% always."** We claim that systematic market scanning, aggregation, and surplus diversion produces materially better outcomes than nearest-mandi selling. The scenario above is modeled on real Nashik tomato price data from 2024.

---

# THE PROCESSING PIVOT — The Core Differentiator

This is the feature that separates Anna Drishti from every agri-marketplace, chatbot, or advisory platform.

## The Problem It Solves

Every year, Indian farmers destroy food because selling is worse than abandoning it:

| Year | Event | Loss |
|------|-------|------|
| 2024 | Kolar (Karnataka): tomato ₹2-5/kg — farmers left crops unharvested | Full season loss |
| 2025 | Maharashtra: onion ₹7/kg wholesale — below ₹10/kg production cost | ₹15,000+ crore farmer distress |
| 2024 | MP: soybean ₹50-150/quintal at mandi — below MSP | Triggered farmer suicides in Sehore |

Every advisory tool says: *"You should have planted something else."*

That's useless when the crop is ALREADY in the ground.

**Anna Drishti is the only system that works AFTER planting.** It doesn't prevent the glut. It prevents the CRASH by diverting surplus into value-added processing.

## Why Processing Diversion Works (The Math)

**SCENARIO A — No diversion (current reality):**
```
30T of tomato from one FPO all hits Nashik/Pune mandis in the same week
→ Arrivals spike 40% above normal
→ Price drops from ₹26/kg to ₹12-15/kg (mandi records confirm this pattern)
→ 14 farmers, avg ~2.1T each, earn: ~₹27,000 average
→ Production cost: ~₹12/kg = ₹25,200
→ Net: ₹1,800 — barely breaking even
```

**SCENARIO B — Anna Drishti diverts 7T to processing:**
```
23T → Fresh market (supply closer to demand → price holds at ~₹24-26/kg)
  Revenue at ₹25/kg: ₹5,75,000

5T → Sai Agro (tomato paste contract): ₹32/kg
  Revenue: ₹1,60,000

2T → Krishi Proc. (sun-dried): ₹38/kg
  Revenue: ₹76,000

Total FPO revenue: ₹8,11,000
Per farmer avg (14 farmers): ~₹57,900

Difference: ₹57,900 vs ₹27,000 = +₹30,900 per farmer
```

**Key insight: the processing diversion doesn't just recover value from surplus. It PROTECTS the fresh market price for everyone.** By absorbing 7T, the remaining 23T sells at ₹25/kg instead of ₹12/kg.

### What Makes This Feasible (Not Vaporware)

| Concern | Reality |
|---------|---------|
| "Where are the processors?" | India has **70,000+ registered micro-food-processing units** under the PMFME scheme. The government invested ₹10,000 crore specifically to build this capacity. Most run at 40-60% utilization because supply is unpredictable |
| "Why would they work with you?" | Their #1 problem is inconsistent raw material supply. We offer: aggregated, volume-predictable, quality-graded supply on a weekly schedule. This is exactly what they need |
| "For the hackathon?" | We pre-onboard 1-2 processor partners in Nashik district during prep week. Not theoretical — actual WhatsApp conversations establishing rate + capacity. For demo, we simulate the diversion flow with real data and real processor response |

### The Value Ladder (What Surplus Becomes)

| Raw (crash price) | Processed Form | Typical Processing Contract Rate | Shelf Life |
|-------------------|---------------|--------------------------------|------------|
| Tomato (₹10-15/kg) | Tomato paste / puree | ₹28-35/kg | 12 months |
| Tomato (₹10-15/kg) | Sun-dried tomatoes | ₹35-45/kg | 18 months |
| Onion (₹7-10/kg) | Dehydrated flakes | ₹80-120/kg | 24 months |
| Chili (₹15-20/kg) | Chili powder / flakes | ₹100-150/kg | 18 months |

**India processes only 7.7% of agricultural output. The US processes 65%. The gap is coordination, not infrastructure.**

---

# BACKGROUND FEATURES (Not Agents — Assistive Tools)

Beyond the core Sell + Process engines, Anna Drishti surfaces useful information to the farmer and FPO coordinator — but with **human decision gates**, not autonomous action:

## Insurance Assist

| What it does | What it does NOT do |
|-------------|-------------------|
| Detects possible crop distress via satellite NDVI anomalies | Does NOT auto-file claims on farmer's behalf |
| Alerts FPO coordinator: "3 farmers may have crop damage, may be eligible for PMFBY" | Does NOT interact with PMFBY portal autonomously |
| Pre-fills claim documentation (satellite screenshot, weather data, loss estimate) | Coordinator or farmer reviews, confirms, and submits |
| Tracks claim status if submission reference is entered | Does NOT follow up with insurer |

## Scheme Discovery

| What it does | What it does NOT do |
|-------------|-------------------|
| Maintains database of ~30 major national + state agriculture schemes | Does NOT auto-apply for any scheme |
| Matches farmer profile (from FPO records) against eligibility criteria | Does NOT access government portals |
| Alerts farmer/coordinator: "You may be eligible for PM-KISAN / KCC / soil subsidy" | Coordinator helps farmer apply using pre-filled form |
| Provides checklist of required documents | Does NOT guarantee eligibility or approval |

## Credit Readiness Signal

| What it does | What it does NOT do |
|-------------|-------------------|
| Maintains digital transaction ledger (every sale via platform) | Does NOT calculate credit score for banks |
| Can generate "farmer profile" summary: crops grown, revenue history, repayment record (if loan data available) | Does NOT apply for loans or interact with bank systems |
| Makes farmer "credit visible" — a portfolio a bank/NBFC can review | Does NOT act as Business Correspondent (requires separate licensing) |

> **Why this matters:** These features demonstrate platform completeness to judges without over-claiming autonomous capability. They show we UNDERSTAND the farmer's full lifecycle — but we're honest about what requires human oversight.

---

# SEASONAL PLANNING — THE GAME THEORY ENGINE

## What It Is

Before each sowing season, Anna Drishti provides FPO-level crop diversification recommendations using cooperative game theory. This is the **intellectual differentiator** — the math that no competing solution uses.

## How It Works

1. **Profile each plot**: soil type (from Soil Health Card database), water availability, past crop history, farmer's stated preferences
2. **Simulate 10,000 market scenarios**: Monte Carlo simulation using historical Agmarknet prices + TFT temporal model for demand-side factors (weather, festival calendar, macroeconomic indicators)
3. **Compute Shapley-optimal allocation**: cooperative game theory solver finds the crop plan across all FPO members that maximizes COLLECTIVE expected income, subject to:
   - Individual rationality: each farmer earns ≥ their solo expected income
   - Fairness: Gini coefficient across farmer incomes ≤ 0.15
   - Feasibility: soil/water/labor constraints per plot
4. **Deliver via IVR**: personalized voice recommendation to each farmer

### Example Output

```
"Ramesh bhai, agle season ke liye humara sujhav:
 1 acre tamatar, 1 acre moong.

 Agar poore FPO mein sab tamatar lagayenge toh bhav girne ka risk hai.
 Moong ki demand badhne ka signal hai — ₹7,800/quintal tak ja sakta hai.

 Agar aap yeh plan follow karein, aur FPO ke 60%+ kisan bhi karein —
 toh aapki estimated season income: ₹65,000-85,000.

 Yeh FPO coordinator Suresh bhai se baat karke confirm karein."
```

### Honest Caveats

| What this IS | What this is NOT |
|-------------|-----------------|
| A mathematically optimized recommendation | A guarantee of income |
| Based on historical price patterns and game theory | A crystal ball for future prices |
| Most valuable when 60%+ of FPO members participate | Effective for individual farmers acting alone |
| Demonstrated in hackathon as a pre-computed simulation | A real-time system processing 500 farmers in 48 hours |

### Why It Still Impresses Judges

The game theory engine is demonstrated as a **visualization**: show 500 farmer dots, press "uncoordinated" → all turn red (tomato) → price crashes → collective income: ₹2.1 crore. Press "Anna Drishti plan" → dots diversify → prices stable → collective income: ₹3.4 crore. **Same land, same farmers, +₹1.3 crore because they planned TOGETHER.**

This is pre-computed, not live. We're honest about that. But the MATH is real, the DATA is real, and the insight — coordination is more powerful than prediction — is genuinely novel.

---

# AI COMPONENTS — 6 Core Models for MVP

| # | Component | Model | Purpose | Honest Limitation |
|---|-----------|-------|---------|-------------------|
| 1 | **Voice Intent Parser** | Whisper (small) + fine-tuned IndicBERT | Parse farmer voice into structured intent (sell/buy/query) | Regional dialects may reduce accuracy; fallback to DTMF menu |
| 2 | **Market Scanner** | Agmarknet scraper + LightGBM price forecaster | Real-time mandi prices + 48hr trend prediction | Agmarknet data can be delayed 4-12hrs; we forecast from available data, not live feeds |
| 3 | **Surplus Detector** | Rule-based (FPO harvest signals vs. historical mandi absorption) | Flag when FPO volume exceeds safe mandi capacity | Relies on farmers signaling harvest via IVR; incomplete reporting = incomplete detection |
| 4 | **Processing Matcher** | Constraint optimizer (OR-Tools MILP) | Optimal split between fresh market and processors | Only works with pre-onboarded processor network; limited to pilot geography initially |
| 5 | **Negotiation Engine** | GPT-4o mini with hard constraints + template structure | Conduct buyer negotiation on WhatsApp within price guardrails | NOT free-form LLM generation; template-based with variable insertion. Floor price is hard-coded. All messages logged |
| 6 | **Satellite Context Provider** | NDVI temporal analysis on Sentinel-2 imagery | Crop stage confirmation + regional yield estimation | Resolution: 10m pixels. Accuracy: directional/regional, not plot-precise. Cloud cover creates 5-10 day gaps |

### Roadmap Models (Not Built for MVP, Mentioned in Pitch)

| # | Component | Purpose | Phase |
|---|-----------|---------|-------|
| 7 | Cooperative Game Solver (Shapley + MILP) | Pre-season crop optimization across FPO | Demonstrated as simulation in MVP; production in Phase 2 |
| 8 | Monte Carlo Market Simulator (TFT) | 10,000-scenario demand simulation | Pre-computed for demo; live system in Phase 2 |
| 9 | GNN Buyer Trust Scorer | Score buyer reliability from transaction history | Useful at scale (100+ buyers); manual trust scoring in pilot |
| 10 | NDVI Anomaly Detector (Isolation Forest) | Crop distress detection for insurance assist | Phase 2: requires 2+ seasons of baseline data |
| 11 | Scheme Eligibility Matcher + NER | Auto-parse government scheme documents for eligibility rules | Phase 2 |
| 12 | Credit Readiness Profiler | Generate farmer financial summary for bank partnership | Phase 3 |

---

# ARCHITECTURE

```
┌────────────────────────────────────────────────────────────────────┐
│                      FARMER INTERFACE                               │
│   ┌──────────┐  ┌────────────┐  ┌──────────┐  ┌──────────────┐   │
│   │ IVR Call  │  │ WhatsApp   │  │ SMS alerts│  │ FPO Manager  │   │
│   │ (any     │  │ (voice +   │  │ (receipts │  │ Web Dashboard│   │
│   │  phone)  │  │  text)     │  │ + alerts) │  │              │   │
│   └──────────┘  └────────────┘  └──────────┘  └──────────────┘   │
│             Exotel/Gupshup Voice Gateway                           │
│             Hindi (MVP) · Marathi (Phase 2)                        │
└──────────────────────────┬─────────────────────────────────────────┘
                           │
┌──────────────────────────┴─────────────────────────────────────────┐
│                 CORE ENGINE (FastAPI + LangGraph)                   │
│                                                                     │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐   │
│  │ SELL AGENT            │  │ PROCESS AGENT                    │   │
│  │ • Market scan         │  │ • Surplus detection              │   │
│  │ • Aggregation logic   │  │ • Processor matching (MILP)      │   │
│  │ • Buyer outreach      │  │ • Allocation optimization        │   │
│  │ • Negotiation engine  │  │ • Revenue blending               │   │
│  │ • Confirmation flow   │  │ • Processor communication        │   │
│  └──────────────────────┘  └──────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ TOOL REGISTRY                                                │  │
│  │ Agmarknet Scraper │ WhatsApp BA API │ IVR Engine │ UPI Track │  │
│  │ Sentinel-2 NDVI   │ Farmer Ledger DB │ Processor DB         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────┐  ┌──────────────────────────────────┐    │
│  │ SATELLITE CONTEXT    │  │ BACKGROUND FEATURES               │    │
│  │ • NDVI temporal      │  │ • Insurance assist (alert + form)│    │
│  │ • Regional yield est │  │ • Scheme discovery (match + list)│    │
│  │ • Crop stage confirm │  │ • Credit ledger (transaction log)│    │
│  └─────────────────────┘  └──────────────────────────────────┘    │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ DATA: PostgreSQL │ Redis (sessions) │ S3 (satellite + logs) │  │
│  └──────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬─────────────────────────────────────────┘
                           │
┌──────────────────────────┴─────────────────────────────────────────┐
│                    EXTERNAL                                         │
│  Agmarknet │ Sentinel-2 (Copernicus) │ Exotel/Twilio │ WhatsApp   │
│  Pre-onboarded buyers (3-5) │ Pre-onboarded processors (1-2)      │
└────────────────────────────────────────────────────────────────────┘
```

---

# AWS SERVICE MAPPING — Hackathon Implementation

Since this is an **AWS hackathon**, here's the complete mapping of Anna Drishti's architecture to AWS services. Every component below runs on AWS infrastructure.

## Core Infrastructure

| Component | AWS Service | Why This Service | Configuration |
|-----------|------------|-----------------|---------------|
| **Voice Interface (IVR)** | **Amazon Connect** | Native AWS telephony with Hindi language support, pay-per-minute pricing, built-in call recording | Connect flow with Lex bot integration for intent parsing |
| **Alternative: Voice Gateway** | **AWS Pinpoint** (SMS/Voice API) | If using external IVR (Exotel), Pinpoint handles SMS alerts and voice callbacks | SNS topic triggers for farmer confirmations |
| **WhatsApp Integration** | **API Gateway + Lambda** | Webhook receiver for WhatsApp Business API messages (via Gupshup/Twilio) | Lambda processes incoming/outgoing WhatsApp messages |
| **Agent Orchestration** | **AWS Step Functions** | Workflow orchestration for multi-step agent flows (market scan → surplus check → negotiation → confirmation) | State machine with parallel execution for market scanning |
| **LLM Negotiation** | **Amazon Bedrock** (Claude 3 Haiku or Llama 3) | Constrained message generation for buyer negotiation with hard-coded price floor guardrails | System prompt with JSON schema output constraint |
| **Web Dashboard** | **Amazon S3 + CloudFront** | Static React app hosted on S3, served via CloudFront CDN for low-latency access | CloudFront invalidation on deployment |
| **Backend API** | **AWS Lambda + API Gateway** OR **ECS Fargate** | Lambda for event-driven tools (scrapers, alerts); ECS for FastAPI long-running services | Lambda: Python 3.11 runtime. ECS: Fargate with auto-scaling |

## Data Layer

| Data Type | AWS Service | Why This Service | Schema |
|-----------|------------|-----------------|--------|
| **Farmer profiles + transactions** | **Amazon RDS (PostgreSQL)** | Relational data with ACID guarantees for financial transactions | Tables: farmers, plots, transactions, buyers, processors |
| **Time-series price data** | **Amazon Timestream** OR **RDS + TimescaleDB extension** | Efficient storage for mandi price history + forecasting training data | Partitioned by date, indexed by mandi+crop |
| **Session state + cache** | **Amazon ElastiCache (Redis)** | Low-latency session management for IVR flows + mandi price cache (TTL 1hr) | Redis Cluster mode for HA |
| **Satellite imagery** | **Amazon S3 (Standard tier)** | Cost-effective storage for Sentinel-2 GeoTIFF imagery (~100MB per plot per pass) | S3 bucket lifecycle: 30-day transition to Glacier for historical imagery |
| **Audit logs** | **Amazon CloudWatch Logs** | All negotiation messages, farmer confirmations, agent decisions logged with 7-year retention | Log groups per agent with metric filters for anomaly detection |
| **Analytical queries** | **AWS Glue + Athena** | Query transaction history and mandi price trends for FPO coordinator dashboard | Glue crawler on S3 transaction exports; Athena for SQL analytics |

## AI/ML Components

| Model | AWS Service | Why This Service | Deployment |
|-------|------------|-----------------|------------|
| **Voice-to-Text** | **Amazon Transcribe** (Hindi) | Native Hindi STT with custom vocabulary for agriculture terms (tamatar, moong, mandi) | Real-time streaming API via Connect integration |
| **Text-to-Speech** | **Amazon Polly** (Hindi: Aditi voice) | Natural-sounding Hindi voice for IVR callbacks | SSML for emphasis on price and confirmation prompts |
| **Intent Classification** | **Amazon Comprehend** OR **SageMaker endpoint (IndicBERT)** | Classify farmer intent (sell/buy/query) + extract entities (crop, quantity, urgency) | SageMaker inference endpoint if custom fine-tuned model; Comprehend for general NLU |
| **Price Forecasting** | **SageMaker (LightGBM)** | Train LightGBM on 3 years of Agmarknet data; deploy as real-time endpoint | Training job: ml.m5.xlarge. Inference: ml.t3.medium with auto-scaling |
| **Processing Optimizer** | **Lambda (OR-Tools MILP solver)** | Run constrained optimization for surplus allocation (fresh vs. processing split) | Lambda with 3GB memory, 2-minute timeout. Packaged as Lambda Layer |
| **Satellite NDVI Analysis** | **SageMaker (custom ViT model)** OR **Lambda (NumPy/Rasterio)** | ViT for crop classification; NumPy for NDVI calculation from Sentinel-2 bands | Batch transform job for weekly satellite passes |
| **Game Theory Solver** | **AWS Batch (Shapley + MILP)** | Compute-intensive Shapley value calculation for 500 farmers × 8 crops | Fargate Spot instances for cost optimization |

## Integration & Orchestration

| Function | AWS Service | Why This Service | Pattern |
|----------|------------|-----------------|---------|
| **Market Data Scraper** | **Lambda (scheduled)** | Scrape Agmarknet every 6 hours via EventBridge schedule | Lambda triggered by EventBridge rule; stores results in Timestream |
| **Satellite Data Ingestion** | **Lambda (S3 trigger)** | Download Sentinel-2 from Copernicus → process → store in S3 | S3 event notification triggers Lambda on new imagery upload |
| **Agent Workflow** | **Step Functions (Standard)** | Orchestrate: market scan ∥ satellite check → surplus detect → buyer match → negotiate → confirm | Express workflows for sub-1min flows; Standard for multi-hour negotiation cycles |
| **Payment Tracking** | **Lambda (UPI webhook)** | Receive payment confirmation from UPI gateway → update transaction status → alert farmer | API Gateway + Lambda; SNS for farmer SMS alert |
| **Dispute Escalation** | **EventBridge + SNS** | If payment delayed >6hrs, trigger SNS notification to FPO coordinator | CloudWatch alarm on transaction status |
| **WhatsApp Negotiation Bot** | **Lambda (Bedrock runtime)** | Stateless negotiation: receive buyer response → Bedrock generates counter-offer → send via WhatsApp API | Bedrock Converse API with response streaming disabled for deterministic output |

## Security & Compliance

| Requirement | AWS Service | Implementation |
|------------|------------|----------------|
| **Secrets Management** | **AWS Secrets Manager** | Store: Agmarknet credentials, WhatsApp API keys, UPI gateway secrets, RDS passwords |
| **Authentication** | **Amazon Cognito** | FPO coordinator dashboard login; OAuth2 for buyer/processor portals |
| **Encryption at Rest** | **AWS KMS** | Encrypt RDS, S3, EBS volumes with customer-managed keys |
| **Audit Trail** | **CloudWatch Logs + CloudTrail** | All agent actions logged; API calls tracked via CloudTrail |
| **Network Isolation** | **Amazon VPC** | RDS in private subnet; Lambda with VPC endpoint for S3 access |
| **DDoS Protection** | **AWS Shield Standard** | Automatic protection for CloudFront + API Gateway |

## Cost Optimization

| Strategy | AWS Service | Estimated Monthly Cost (1 FPO pilot) |
|---------|------------|-------------------------------------|
| **Compute** | Lambda (5M invocations/mo) + ECS Fargate (1 task, 0.5 vCPU) | ₹2,500 (Lambda) + ₹1,800 (Fargate) |
| **Storage** | S3 (50GB satellite) + RDS (db.t4g.micro) | ₹800 (S3) + ₹1,200 (RDS) |
| **ML Inference** | SageMaker endpoint (ml.t3.medium, 8hrs/day) + Bedrock (10K tokens/day) | ₹3,500 (SageMaker) + ₹600 (Bedrock) |
| **Voice** | Connect (500 minutes/mo) OR Pinpoint (1000 SMS) | ₹1,000 (Connect) OR ₹400 (Pinpoint) |
| **Data Transfer** | CloudFront (5GB/mo) + inter-AZ | ₹100 |
| **TOTAL** | | **~₹11,900/mo** (₹1,42,800/year) |

**At scale (100 FPOs):** ₹8,50,000/year (↓40% via Reserved Instances + Savings Plans)

## Deployment Architecture Diagram (AWS-Specific)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER LAYER                                   │
│  ┌──────────────┐  ┌────────────────┐  ┌───────────────────────┐  │
│  │ Amazon       │  │ WhatsApp via   │  │ S3 + CloudFront       │  │
│  │ Connect      │  │ API Gateway +  │  │ (React Dashboard)     │  │
│  │ (IVR Hindi)  │  │ Lambda webhook │  │                       │  │
│  └──────────────┘  └────────────────┘  └───────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────────┐
│                    ORCHESTRATION LAYER                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ AWS Step Functions (Agent Workflow State Machine)            │  │
│  │ ┌────────────┐  ┌────────────┐  ┌──────────┐  ┌──────────┐ │  │
│  │ │ Market Scan│  │ Surplus    │  │ Processor│  │ Negotiate│ │  │
│  │ │ (parallel) │→ │ Detect     │→ │ Match    │→ │ + Confirm│ │  │
│  │ └────────────┘  └────────────┘  └──────────┘  └──────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ EventBridge Rules (Scheduled Triggers)                        │ │
│  │ • Agmarknet scraper: every 6 hours                            │ │
│  │ • Sentinel-2 download: daily at 3 AM                          │ │
│  │ • Payment timeout check: every 30 minutes                     │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────────┐
│                      COMPUTE LAYER                                   │
│  ┌──────────────────────┐  ┌────────────────────────────────────┐  │
│  │ Lambda Functions     │  │ ECS Fargate (if using FastAPI)     │  │
│  │ • Agmarknet scraper  │  │ • LangGraph runtime (optional)     │  │
│  │ • NDVI calculator    │  │ • Game theory batch jobs           │  │
│  │ • WhatsApp handler   │  │                                    │  │
│  │ • Payment tracker    │  │                                    │  │
│  │ • MILP optimizer     │  │                                    │  │
│  └──────────────────────┘  └────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Amazon Bedrock (LLM)                                         │  │
│  │ Model: Claude 3 Haiku OR Meta Llama 3 8B                     │  │
│  │ Use: Constrained negotiation message generation              │  │
│  │ Guardrails: Price floor, template structure, audit logging   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ SageMaker Endpoints                                          │  │
│  │ • LightGBM price forecaster (ml.t3.medium, auto-scale)       │  │
│  │ • ViT crop classifier (batch transform, weekly)              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────────┐
│                       DATA LAYER                                     │
│  ┌─────────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ RDS PostgreSQL      │  │ Timestream      │  │ ElastiCache     │ │
│  │ (farmers, txns,     │  │ (mandi prices,  │  │ Redis (sessions,│ │
│  │  buyers, processors)│  │  time-series)   │  │  price cache)   │ │
│  └─────────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ S3 Buckets                                                  │   │
│  │ • satellite-imagery/ (Sentinel-2 GeoTIFFs)                  │   │
│  │ • transaction-exports/ (daily Parquet snapshots)            │   │
│  │ • audit-logs/ (negotiation transcripts, agent decisions)    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ AWS Glue + Athena (Analytics)                               │   │
│  │ Query FPO performance, farmer income trends, buyer patterns │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────────┐
│                    MONITORING & SECURITY                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ CloudWatch Logs + Metrics + Alarms                           │  │
│  │ • Agent execution traces                                     │  │
│  │ • Payment timeout alerts                                     │  │
│  │ • LLM negotiation anomaly detection                          │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ AWS Secrets Manager + KMS                                    │  │
│  │ Encrypted storage for API keys, DB credentials, certificates │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ VPC (Private Subnets for RDS, Lambda VPC endpoints for S3)  │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Why This AWS Stack Wins

| Judge Concern | AWS Answer |
|--------------|-----------|
| **"Can you scale?"** | Step Functions handles 25,000 executions/sec. Lambda auto-scales to millions of invocations. RDS read replicas for analytics load |
| **"What about voice in vernacular languages?"** | Amazon Connect + Transcribe support Hindi natively. Polly has Aditi (female Hindi voice). Custom vocabulary for agriculture terms |
| **"LLM cost concerns?"** | Bedrock's pay-per-token model is ₹0.0003/1K tokens (Haiku). 10K negotiation messages/mo = ₹600. Cheaper than GPT-4 API |
| **"Satellite data storage?"** | S3 Intelligent-Tiering: frequently accessed NDVI stays in Standard; historical imagery auto-migrates to Glacier (90% cost reduction) |
| **"Audit trail for disputes?"** | CloudWatch Logs with 7-year retention. Every negotiation message, farmer confirmation, and payment status change is immutable and timestamped |
| **"Production readiness?"** | AWS Well-Architected Framework compliance: HA via multi-AZ RDS, fault tolerance via Lambda retries, security via KMS + Secrets Manager |

## Demo-Specific Implementation (48-Hour Hackathon)

For the hackathon MVP, we'll use:

| Component | AWS Service | Why (for DEMO) |
|-----------|------------|----------------|
| **Voice demo** | **Pre-recorded audio + manual trigger** (Skip Connect setup; show UX flow) | Connect setup requires 2-3 days for Hindi config. Demo with pre-recorded farmer audio |
| **LLM negotiation** | **Bedrock Claude 3 Haiku** (LIVE, not mocked) | Provisioned throughput not needed; on-demand is fast enough for demo (<2s latency) |
| **Backend** | **Lambda + API Gateway** (NOT ECS; faster deployment) | Lambda deployment via SAM/CDK in <10 minutes. ECS requires container registry + task definitions |
| **ML models** | **SageMaker batch transform** (pre-run before demo) + **cached results** | Train LightGBM on SageMaker training job Fri-Sat; inference results cached in S3 for demo speed |
| **Database** | **RDS PostgreSQL (db.t4g.micro)** | Provision Saturday morning; load with 500 simulated farmers + 3 years mandi price data |
| **Frontend** | **S3 + CloudFront** | Deploy React build to S3; CloudFront for HTTPS + low-latency |
| **Orchestration** | **Step Functions (pre-built state machine)** | Define state machine in CDK; deploy Sat evening; test Sunday morning |

**What's LIVE in demo:**
- ✅ Bedrock LLM negotiation (actual API call)
- ✅ Step Functions workflow execution (audience sees state transitions)
- ✅ Lambda functions (Agmarknet scraper runs LIVE on stage)
- ✅ RDS queries (real farmer data)
- ✅ WhatsApp message sending (to team phone)

**What's pre-computed:**
- 🔄 Satellite NDVI (pre-downloaded from Copernicus; analysis run Saturday)
- 🔄 Game theory simulation (pre-computed; visualization is interactive)
- 🔄 Price forecast training (model trained Sat; inference cached)

---

# REVENUE MODEL

| Stream | Mechanism | Per FPO (500 farmers) / year | When |
|--------|-----------|---------------------------|------|
| **Transaction commission** | 1.5% of sale value facilitated through platform | ₹4,00,000 - ₹6,00,000 | From first transaction |
| **Processing facilitation** | 2% of processing volume arranged | ₹1,00,000 - ₹2,00,000 | When processing is active |
| **FPO SaaS** | Dashboard + analytics subscription | ₹1,00,000 - ₹2,00,000 | Phase 2 |
| **Total per FPO/year** | | **₹6,00,000 - ₹10,00,000** | |
| **Cost to serve per FPO/year** | IVR (₹80K) + cloud (₹40K) + WhatsApp API (₹20K) + human coordinator (₹60K) | **₹2,00,000 - ₹2,50,000** | |
| **Contribution margin** | | **60-75%** (improves with scale) | |

**Farmer cost: ₹0.** Revenue comes from commission on sales the platform facilitates — sales that wouldn't have happened at that price without Anna Drishti.

**Honest note on pilot economics:** At 1-2 FPOs, revenue will NOT cover costs. The pilot is funded as an investment in proving the model. Break-even requires ~15-20 FPOs. This is typical for marketplace businesses and we won't pretend otherwise.

---

# RISK DISCLOSURE

| Risk | Likelihood | Impact | Mitigation | Residual |
|------|-----------|--------|-----------|----------|
| **Negotiation misfire** — LLM says something inappropriate to buyer | Low (template-based) | High (damages FPO relationship) | Hard constraints: price floor, no commitment without confirmation, all messages logged and auditable. Buyer receives structured template, not free-form text | Coordinator reviews flagged conversations weekly |
| **Payment default** — Buyer doesn't pay after pickup | Medium | High | Only verified buyers (FPO's existing network + platform history). UPI tracking with 6hr alert. Dispute escalation to FPO coordinator. Persistent defaulters removed from buyer network | Cannot eliminate fully; FPO bears commercial risk as in any trade |
| **Misclassification** — System routes produce to processor but quality doesn't meet processing standards | Medium | Medium | Processor acceptance is confirmed AFTER physical inspection at pickup. Platform does not guarantee quality grade — only facilitates connection | Pre-season: establish grade definitions with each processor partner |
| **Farmer over-reliance** — Farmer trusts system blindly, doesn't verify | Low-Medium | Medium | EVERY deal requires explicit farmer voice confirmation ("Haan"). SMS receipt with full details. FPO coordinator has oversight dashboard | Trust-building transparency: full transaction history accessible via voice query |
| **Surplus miscalculation** — System underestimates surplus, crash still occurs | Medium | Medium | System errs conservative: triggers processing diversion at 70% mandi capacity (not 100%). If processors are full, falls back to multi-mandi distribution | Cannot prevent all crashes; aim to reduce severity and frequency |
| **Satellite data gaps** — Cloud cover prevents NDVI reading | Medium | Low | Graceful degradation: if satellite data unavailable, system proceeds with market scan + farmer-reported harvest data only. Satellite context is assistive, not blocking | System works without satellite; satellite makes it better |

---

# THE DEMO — 12 MINUTES

## Minute 0-2: "THE GAP" — Setting the Stage

*"10,786 farmers took their own lives in 2023."*
*"We researched why. The answer isn't drought. It isn't pests."*
*"It's that nobody acts on their behalf."*

*"A rich farmer has an agent, a broker, a CA, and connections."*
*"A poor farmer walks to the nearest mandi and takes whatever price he gets."*

*"We asked: what if AI didn't just TELL farmers what to do — but DID the work for them?"*
*"Not autonomously — with their permission, in their language, on any phone."*

---

## Minute 2-7: "THE LIVE SELL" — The Proof

**[LIVE on stage: call the IVR number]**

*"Mere tamatar tayyar hain, bech do."*

**Split screen activates:**
- LEFT: Farmer's simple voice experience (audio playing)
- RIGHT: System workflow (real-time dashboard)

1. 🛰️ **Satellite check** — show Sentinel-2 NDVI image of Nashik farmland
2. 📊 **4 mandis scanned** — real Agmarknet data populating: Sinnar ₹16, Nashik ₹19, Pune ₹28, Mumbai ₹32
3. ⚠️ **SURPLUS DETECTED** — "FPO total this week: ~30T. Mandi safe capacity: ~22T."
4. 🏭 **Processing match** — "Sai Agro: 5T available at ₹32/kg. Krishi Proc: 2T at ₹38/kg."
5. 👥 **3 farmers aggregated** — "Combined fresh load: 5.6T. Shared truck."
6. 📱 **WhatsApp negotiation** — audience watches actual messages appear:
   - System: *"5.6T tomato, Nashik, kal pickup. ₹26 minimum."*
   - Buyer (team member backstage): *"₹23 dunga"*
   - System: *"Pune mein ₹28 chal raha. ₹26 fair rate hai."*
   - Buyer: *"₹25.50 done."*
7. ✅ **DEAL — pending farmer confirmation**

**Farmer callback plays on speaker:**
*"Ramesh bhai, ₹25.50/kg fresh market, ₹32/kg processing. Total lagbhag ₹63,000. Haan bolein toh confirm."*

**[Beat]**

*"4 minutes of farmer time."*
*"30+ system actions."*
*"In this scenario: ₹63,000 vs. ₹37,000 at the nearest mandi."*

---

## Minute 7-9: "THE PROCESSING PIVOT" — The Aha Moment

**Counter-factual visualization:**

**Screen A: "WITHOUT Anna Drishti"**
- Graph: 30T hits mandis → price line crashes from ₹26 to ₹12
- 14 farmer income bars: all short, red, barely above production cost

**Screen B: "WITH Anna Drishti"**
- 7T diverted to processing → supply drops to 23T → price holds at ₹25
- 14 farmer income bars: all taller, green, well above cost

*"There's nothing left to crash. The system moved the surplus into tomato paste before the first truck reached the mandi."*

*"India processes 7.7% of its agriculture. The US processes 65%. The processors exist — 70,000 registered units under PMFME. They run at half capacity because they can't get predictable supply."*

*"We don't build processing plants. We connect the supply they've been waiting for."*

---

## Minute 9-10: "THE PLANNING BRAIN" — The Intellectual Punch

**Pre-computed simulation:**

*"What if farmers could plan TOGETHER before the season even starts?"*

Dashboard: 500 farmer dots on map.
- Press "Every farmer picks independently" → 80% turn red (tomato) → price crash → collective income: ₹2.1 crore
- Press "Anna Drishti coordination" → dots diversify (40% tomato, 25% moong, 20% chili, 15% greens) → stable prices → collective income: ₹3.4 crore

*"Same farmers. Same land. Same weather. ₹1.3 crore more. Because they planned together."*

*"This is cooperative game theory — Shapley values, Nash Bargaining. Nobel Prize mathematics. We bring it to farmers through a phone call."*

*"This is a pre-season planning tool. We demonstrate the simulation today. The production version launches in Phase 2."*

---

## Minute 10-11: "THE PLATFORM" — Quick Hits

**Insurance Assist:** *"Satellite detects crop stress. System alerts FPO coordinator. Pre-fills claim documentation. But the farmer confirms and submits — not the AI."*

**Scheme Discovery:** *"System finds 4 government schemes this farmer qualifies for but hasn't enrolled in. Pre-fills the forms. FPO coordinator helps submit."*

*"We're not an autonomous government interface. We're a preparation engine that makes the coordinator's job 10x easier."*

---

## Minute 11-12: "THE ROAD AHEAD" — Ambition Without Overreach

*"Today you've seen Phase 1: sell smarter, process surplus."*

*"Phase 2: direct-to-consumer channels — same tomato, ₹52/kg to the consumer instead of ₹25 to the trader."*

*"Phase 3: carbon credits — the crop rotation our game theory engine recommends generates verified carbon income. ₹4,800/year per farmer. For practices they're already doing."*

*"This is not a product roadmap. It's a compounding wealth architecture."*

*"But today, we start where it matters: the next harvest."*

---

## The Close (30 seconds)

*"We get asked: 'Who is your competitor?'"*

*"The answer is: the nearest mandi. The ₹16/kg that a farmer settles for because they have no other option."*

*"Anna Drishti doesn't replace the mandi. It gives the farmer a better option — and the power to say no to a bad deal."*

*"If UPI gave every Indian a bank — Anna Drishti gives every farmer a negotiator."*

*"They just farm. We handle the deal."*

*"Thank you."*

---

# DEPLOYMENT PLAN

| Phase | Timeline | Scale | What's Built | What's Measured |
|-------|----------|-------|-------------|----------------|
| **Hackathon MVP** | 48 hours | Simulated FPO | Sell Agent (live IVR + WhatsApp) + Processing simulation + Game theory visualization | Judge response + demo reliability |
| **Field Pilot** | Months 1-4 | 1 FPO, 500 farmers, Nashik (tomato/onion) | Sell Agent + Process Agent with 2 real processor partners, 3-5 verified buyers | Avg selling price uplift vs. control. Processing utilization rate. Farmer re-use rate |
| **Regional** | Months 5-12 | 10-20 FPOs, MH + Telangana | Full Sell + Process. Insurance Assist + Scheme Discovery activated. Multi-language (Marathi, Telugu) | Revenue per FPO. Contribution margin. Farmer NPS. Processor partner retention |
| **Scale** | Year 2-3 | 200+ FPOs, 5+ states | D2C pilot. Carbon credit pilot. Open API for bank/insurer integration | Path to ₹100 crore revenue. Policy impact evidence |

---

# HACKATHON MVP — 48-HOUR BUILD

| Person | Builds | What's Real vs. Simulated |
|--------|--------|--------------------------|
| **P1: ML** | LightGBM price model on 3yr Agmarknet data + NDVI analysis on pre-downloaded Nashik imagery + OR-Tools MILP for processing allocation | **Real**: price model trained on actual mandi data. **Simulated**: satellite imagery is pre-downloaded, not live API |
| **P2: Backend** | FastAPI + LangGraph Sell Agent (market scan → surplus check → buyer outreach → confirmation flow) | **Real**: end-to-end agent flow with actual tool calls. **Simulated**: processor capacity is pre-configured |
| **P3: Frontend** | React dashboard: real-time agent action stream, mandi price map, processing diversion visualization, farmer profile | **Real**: functional UI. Priority: this IS the demo. 60% of their time |
| **P4: Integrations** | Twilio WhatsApp sandbox (negotiation) + Exotel IVR (voice intake) + Agmarknet scraper | **Real**: actual WhatsApp messages to actual phone. Team members act as buyer/processor. Pre-recorded Hindi IVR prompts |
| **P5: Story** | Slides, demo script, Nashik data prep, game theory pre-computation, rehearsal | Source real farmer data. Prepare counter-factual visualizations. Time every beat |

### What Judges See That's Real
- ✅ Live IVR call → voice parsed → intent extracted
- ✅ Real Agmarknet price data populating dashboard
- ✅ WhatsApp negotiation with human "buyer" in Hindi (actual messages)
- ✅ Processing diversion calculation with real surplus math
- ✅ Game theory simulation with real crop-price data
- ✅ Farmer confirmation call with deal details

### What's Explicitly Simulated (And We Say So)
- 🔄 Satellite imagery is pre-downloaded (mention: "production system pulls from Copernicus every 5 days")
- 🔄 Processor capacity is pre-configured (mention: "pilot will have LOIs with 2 Nashik-area processors")
- 🔄 Game theory is pre-computed (mention: "production version runs pre-season for each FPO")
- 🔄 Insurance/scheme features shown as UI mockups (mention: "Phase 2 activation")

---

# Q&A SURVIVAL KIT

**Q: "Isn't this just a marketplace?"**
> A marketplace lists prices. We NEGOTIATE on behalf of the farmer, DETECT surpluses before they crash the market, and DIVERT to processing. A marketplace is infrastructure. We're an agent — with a confirmed diversion strategy that protects the entire FPO, not just one seller.

**Q: "What if the AI negotiation says something wrong?"**
> The negotiation is template-based with variable insertion (price, quantity, location), not free-form generation. Hard-coded floor price that the system CANNOT go below. Every message is logged and auditable. And critically — no deal closes without the farmer saying "Haan" on a confirmation call. The system RECOMMENDS deals; the farmer DECIDES.

**Q: "Where are your processor partners?"**
> For the hackathon, we simulate the processor interaction with pre-configured capacity data. For the field pilot, we will sign LOIs with 1-2 PMFME-registered processing units in Nashik district. The pitch to them is straightforward: we guarantee aggregated, predictable supply — their #1 problem.

**Q: "How do you handle disputes — bad produce, late payment, buyer no-show?"**
> Every transaction has: (1) SMS receipt to farmer with deal terms, (2) FPO coordinator real-time visibility on dashboard, (3) Payment tracking with 6-hour escalation alert, (4) Buyer reliability score that degrades on defaults — persistent defaulters removed from network. We don't eliminate commercial risk; we make it visible and manageable.

**Q: "The game theory engine — does it actually work?"**
> The simulation you see runs on actual Nashik mandi data from 2022-2024. The Shapley value calculation and MILP optimization are mathematically sound — published game theory. The HARD PART is farmer adoption (getting 60%+ to follow coordinated plans). That's a trust problem we solve through demonstrated results: show coordination outcomes vs. actual outcomes from previous seasons, and build participation over time.

**Q: "Cost ₹0 to farmer — how is that sustainable?"**
> We take 1.5% of the sale value we facilitate. That commission ONLY exists because the transaction happened at a better price than the farmer's alternative. At pilot scale, we're subsidized. At 15-20 FPOs, the model breaks even. At 100+ FPOs, contribution margins reach 65-75%. This is standard marketplace economics — Uber and UPI both subsidized early.

---

# WHY THIS WINS

| Judge Criterion | Anna Drishti's Answer |
|----------------|----------------------|
| **Novel insight** | "The problem isn't information, it's agency" — reframes every competing solution as insufficient |
| **Sharp wedge** | Sell + Process. Two capabilities, deeply built. Not 8 industries |
| **Technical depth** | Cooperative game theory + MILP processing optimizer + LLM negotiation with hard constraints + satellite context. The stack is deep WITHIN the wedge |
| **Demo power** | LIVE WhatsApp negotiation in Hindi with a real buyer + processing crash-prevention visualization. Nobody else will show AI actually doing a deal |
| **Honest scope** | "This is what's built. This is what's simulated. This is Phase 2." Credibility through transparency |
| **Feasibility proof** | Uses existing infrastructure: WhatsApp, UPI, Agmarknet, Sentinel-2, PMFME processors. No new hardware. No regulatory sidestep |
| **Emotional resonance** | "₹10,786 farmers died in 2023. Not from drought. From having no one in their corner." |
| **Business credibility** | Transaction commission model. Honest about pilot economics. Clear break-even path. Not "₹0 cost + 83% margins" fairytale |
| **Roadmap credibility** | D2C, carbon credits, and forward contracts as Phase 2/3 — shows vision without triggering "too much" alarm |

---

# THE LINE

> *"Anna Drishti gives every farmer a negotiator.*
>
> *Not an advisor. Not a dashboard. Not a chatbot that says 'tomato price is ₹28.'*
>
> *A negotiator who calls the buyer, fights for ₹25.50 instead of ₹16, diverts surplus to processing before the crash, and calls the farmer back to say: 'Deal mil gaya. Haan bolein toh confirm.'*
>
> *They farm. We handle the deal."*

---

# PHASE 2-3 ROADMAP — The Wealth Stack

> **Phase 1 makes farmers earn more. Phase 2 makes farmers sell smarter. Phase 3 makes farming compound like an asset.**

Now we move from **"win hackathon"** to **"design rural financial infrastructure."**

Phase 3 is not about adding features. It is about adding **compounding income layers** that:
- Do NOT break regulatory walls
- Do NOT increase farmer complexity
- Do NOT depend on speculative forecasting
- Strengthen the core Sell + Process wedge
- Create permanent adoption

---

## PHASE 2: Stabilization & Automation

| Capability | Why It Compounds | AWS Implementation | Dependency |
|-----------|-----------------|-------------------|------------|
| **Direct-to-consumer channel** | Farmer gets ₹52/kg instead of ₹25/kg for premium produce | S3 static site + API Gateway for order management | Requires consumer demand validation + last-mile logistics partner |
| **Insurance Assist → full automation** | Auto-detect + auto-file PMFBY claims with satellite evidence | Lambda triggers on NDVI anomaly detection → pre-fill forms via Textract | Requires insurer API partnership + regulatory clarity on digital filing |
| **Real-time Game Theory Engine** | Pre-season crop coordination goes from simulation to production | AWS Batch for Shapley solver; SageMaker for Monte Carlo demand simulation | Requires 60%+ FPO adoption to demonstrate coordination benefits |

---

## PHASE 3: THE WEALTH STACK

### 🧠 Core Philosophy

Sell smarter → Stabilize income → Capture surplus → **Now convert farming from seasonal survival into a structured asset system.**

We build **4 tightly connected layers**.

---

### 1️⃣ FORWARD PRICE LOCK (Harvest Income Stability Engine)

#### Why This Matters

The current system:
- Improves selling price
- Prevents crashes via processing

But income is still **uncertain until harvest week**.

We now introduce: **Micro Forward Contracts — FPO-backed, not speculative.**

#### How It Works (Realistic Version)

60 days before harvest, system computes:
- Yield estimate range (satellite + historical)
- 60-day mandi forward probability band
- FPO-wide exposure
- Processor absorption capacity

Then farmer gets IVR call:

*"Aap ₹24/kg ka minimum lock karna chahte hain?*
*Agar market ₹30 gaya, aapko ₹30 milega.*
*Agar ₹15 gaya, aapko ₹24 milega."*

#### Mechanism (Regulatory-Safe Version)

**NOT futures trading.**

Instead:
- FPO creates **Minimum Income Pool**
- Backed by:
  - Diversified crop base
  - Processing contracts
  - Small NBFC credit line
- Structured as:
  - Price protection agreement (FPO internal risk-sharing)
  - Not commodity derivative (no SEBI/FMC regulatory burden)

#### AI Engine Behind It (AWS Implementation)

| Component | AWS Service | Purpose |
|-----------|------------|---------|
| Monte Carlo yield simulation | SageMaker training job (PyTorch/TensorFlow) | 10,000-scenario crop outcome simulation |
| Bayesian price probability band | SageMaker endpoint (Prophet model) | 60-day forward price distribution |
| CVaR exposure monitoring | Lambda + Timestream | Real-time FPO risk dashboard (value-at-risk calculation) |
| Contract management | DynamoDB + Step Functions | Track forward locks, trigger settlement on harvest |

#### Why This Is Powerful

Farmers now:
- Know **minimum harvest income 60 days early**
- Can plan school fees, debt repayment
- Reduce psychological stress

This creates **behavioral stickiness** — farmers stay on the platform because of income certainty, not just better prices.

---

### 2️⃣ SOIL WEALTH COMPOUNDING ENGINE

This is where Anna Drishti differentiates from every agri marketplace.

Most platforms optimize: **This season's price.**

Anna Drishti optimizes: **3-year soil asset growth.**

#### Mechanism

Add multi-season constraints to planning engine:

**Maximize:**
```
Σ(t=1 to 3) [ExpectedIncome(t) - InputCost(t)]
```

**Subject to:**
- Soil organic carbon ≥ baseline
- Nitrogen balance positive
- Crop diversity index ≥ threshold

#### What This Unlocks

- **20–30% fertilizer reduction** over 3 years (reduced input costs)
- **Yield stability increase** (resilient soil performs better in drought/flood)
- Better pest resilience
- **Carbon credit eligibility** (baseline established for Phase 3)

Now farming becomes: **Asset compounding, not extraction.**

#### AI Required (AWS Implementation)

| Component | AWS Service | Purpose |
|-----------|------------|---------|
| Temporal NDVI modeling | SageMaker (LSTM on Sentinel-2 time-series) | Track soil health trajectory over 3 years |
| Soil Health Card ingestion | Textract + Comprehend | Extract NPK, organic carbon from SHC PDFs |
| Crop rotation optimization MILP | Lambda (OR-Tools) | Find 3-year rotation plan maximizing soil + income |
| Long-horizon reinforcement learning | SageMaker RL (Ray RLlib) | Learn optimal multi-season policies from FPO historical data |

---

### 3️⃣ CARBON + REGENERATIVE INCOME LAYER

Now we **monetize what soil compounding creates**.

#### Realistic Model (No Hype)

We do **NOT**:
- Directly list credits internationally in Year 1
- Promise ₹50K/farmer from Day 1

**Instead:**

**Phase 3A:**
- Partner with verified carbon aggregator (e.g., Varaha, CarbonCred)
- FPO enrolled as grouped project
- Satellite + crop plan data exported to aggregator for MRV (Monitoring, Reporting, Verification)

**Phase 3B:**
- 2-season historical baseline established
- Verified carbon issuance (Verra/Gold Standard)
- Income distributed via FPO ledger

#### AI Role (AWS Implementation)

| Component | AWS Service | Purpose |
|-----------|------------|---------|
| MRV estimation | SageMaker (biomass regression model) | Estimate carbon sequestration from NDVI + crop rotation data |
| Farm clustering | SageMaker (geospatial clustering) | Group farms meeting min area requirement (e.g., 500 acres) |
| Leakage detection modeling | Lambda (anomaly detection) | Detect if carbon gains in one area cause emissions elsewhere |
| Additionality scoring | SageMaker endpoint (XGBoost) | Prove carbon gains are beyond business-as-usual practices |

#### Income

**₹4,000–10,000 per farmer annually**
- Pure upside
- Zero additional labor
- Monetizes regenerative practices farmers already do (when following game theory crop rotation)

---

### 4️⃣ WORKING CAPITAL FLYWHEEL (The Silent Multiplier)

Now that:
- Transactions are digitized
- Income stabilized (forward lock)
- Yield predicted
- Soil improving

You introduce: **Invoice-backed micro credit.**

#### How It Works

After a forward lock is set:
- Farmer eligible for **30% pre-harvest credit**
- Backed by locked contract (not unsecured lending)
- Repayment auto-deducted from sale proceeds

This is **NOT risky unsecured lending.**
It is **income-collateralized working capital.**

#### AI Component (AWS Implementation)

| Component | AWS Service | Purpose |
|-----------|------------|---------|
| Risk scoring | SageMaker (LightGBM) | Score based on: historical yield accuracy, crop diversification compliance, FPO participation |
| Dynamic credit ceiling | Lambda + DynamoDB | Adjust credit limit based on real-time harvest signals + forward lock value |
| Repayment tracking | Step Functions + SNS | Auto-deduct from sale proceeds; alert if shortfall |
| NBFC integration | API Gateway | Connect to partner NBFC for actual fund disbursement |

#### Why This Matters

Farmers currently:
- Borrow from moneylender at **36-60% APR** for seed/fertilizer
- Lose 15-20% of harvest income to interest

With invoice-backed credit:
- **12-18% APR** (bank-grade pricing)
- **10–15% working capital efficiency gain**
- No debt trap — repayment guaranteed by harvest proceeds

---

## 🔥 THE COMPLETE PHASE 3 STACK

| Layer | Purpose | Income Effect | Risk Level | AWS Core Services |
|-------|---------|--------------|-----------|------------------|
| **Forward Lock** | Stability | Removes downside volatility | Medium | SageMaker (Prophet), DynamoDB, Step Functions |
| **Soil Compounding** | Cost reduction + yield growth | 15–25% net gain over 3 yrs | Low | SageMaker (LSTM, RL), Textract, Lambda (MILP) |
| **Carbon Layer** | New income stream | ₹4–10k/year | Medium | SageMaker (biomass model), Glue (MRV export) |
| **Invoice Credit** | Liquidity | 10–15% working capital efficiency | Medium | SageMaker (credit scoring), API Gateway (NBFC) |

---

## 🧠 What This Creates

Not an app. Not a marketplace. Not advisory.

It creates: **A rural asset management system.**

Farmers become:
- Predictable
- Creditworthy
- Diversified
- Regenerative
- **Financially legible**

That changes everything.

---

## 🏗 Clean Architecture Integration

Phase 3 adds:

```
ANNA DRISHTI CORE (Phase 1)
├── SELL AGENT
├── PROCESS AGENT
└── Farmer Ledger

      ↓

COLLECTIVE BRAIN++ (Phase 2 + 3)
├── Game Theory Engine (real-time)
├── Forward Risk Engine (price lock)
├── Soil Temporal Optimizer (3-year MILP)
├── Carbon MRV Engine (biomass estimation)
└── Credit Scoring Layer (invoice-backed)

Connected to:
├── Revenue Pool (FPO risk-sharing)
├── Transaction Ledger (digital repayment)
└── NBFC API (working capital disbursement)
```

**All layers feed each other.** Forward locks enable credit. Credit enables better input purchasing. Better inputs improve soil. Better soil generates carbon income. Carbon income strengthens FPO balance sheet. Stronger FPO can underwrite larger forward locks.

**This is a flywheel, not a feature list.**

---

## 🧠 Why This Is The Perfect Phase 3

Because it:

✅ Compounds income
✅ Reduces volatility
✅ Improves soil
✅ Creates new markets (carbon, credit)
✅ Builds financial identity
✅ Does NOT overwhelm farmer (IVR stays simple: "Haan" or "Naa")
✅ Uses infrastructure you already built (ledger, satellite, game theory, FPO network)

---

## 🚨 What We Avoid (On Purpose)

❌ Running your own carbon registry
❌ Becoming an NBFC (we integrate, not compete)
❌ Commodity speculation (no NCDEX trading)
❌ Managing D2C logistics fleet
❌ Building processing plants

You stay:

> **The intelligence layer.**
> **The execution layer.**
> **The wealth coordination layer.**

Not the capital-heavy infrastructure layer.

---

## 📈 The 5-Year Trajectory

| Year | Focus | Outcome |
|------|-------|---------|
| **Year 1 (Phase 1)** | Sell + Process → Income uplift | ₹25K-40K additional income per farmer per season |
| **Year 2 (Phase 2)** | Coordination adoption → Reduced crashes | 60%+ FPO participation in game theory planning; mandi crash events ↓40% |
| **Year 3 (Phase 3A)** | Forward lock + Soil compounding | Income volatility ↓50%; fertilizer costs ↓20% |
| **Year 4 (Phase 3B)** | Carbon income + credit scaling | ₹8K carbon income/farmer; 40% farmers accessing invoice credit |
| **Year 5** | FPO becomes financially stable micro-economy | FPO can self-finance forward locks; NBFC partnership scaled to 100+ FPOs |

---

## 🏆 The Positioning Line

> *\"Phase 1 makes farmers earn more.*
> *Phase 2 makes farmers sell smarter.*
> *Phase 3 makes farming compound like an asset.\"*

---

> *"Today, we start where it matters: the next harvest.*
> *Tomorrow, we build the wealth engine.*
> *But the first step is giving a farmer a better deal — right now, this season."*
