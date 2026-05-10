---
title: "Methodology"
description: "How we analyze Weiss Schwarz booster sets."
date: 2026-05-10
---

## What we analyze

Each set analysis answers one question: **should you preorder, or wait for the dip?**

After a WS booster box releases, people who opened boxes often flood the market with singles, pushing box prices down for 30–90 days before they stabilize or recover. Whether to preorder or wait depends on the IP strength, historical behavior of that IP in WS, and the underlying value of the JP set.

## Analysis components

### 1. IP Strength

We check the IP's anime and manga rankings on MyAnimeList — rank, score, member count, and favorites. Stronger IPs sustain demand longer and recover faster after a post-release dip.

**Score tiers:**
- **Strong** — anime rank < 500 or member count > 500k
- **Moderate** — anime rank 500–2000
- **Niche** — rank > 2000 or no anime adaptation

### 2. Historical EN Performance

For every prior English WS set in the same IP, we track:
- Preorder price (sealed booster box)
- Pull rates for each rarity tier (SP, SSP, RRR, RR, R)
- Average value of high-rarity cards at release vs. now
- How long until the price recovered (if it dipped)

This tells us the pattern: does this IP tend to dip and recover, or does it steadily decline?

### 3. JP Set Analysis

Japanese sets release 12–18 months before their English equivalents. We pull all card prices from Yuyutei and compute:
- Box expected value (EV) per rarity slot
- Top-10 highest-value cards
- Whether the set has sustained JP value or collapsed

**Note:** We exclude AGR (autograph/signed) rarity from EV calculations — these never appear in English prints and would inflate the EV unfairly.

### 4. Competitive Standing

We note whether the IP has competitive presence in EN WS tournament play. Competitively relevant sets sustain demand even after the initial hype fades.

### 5. Recommendation

We synthesize the above into one of four signals:

| Signal | Meaning |
|--------|---------|
| **Strong Buy** | Preorder confidently — IP demand is high, EN trend is positive, JP EV justifies the price |
| **Buy** | Preorder is reasonable — positive signals but some uncertainty |
| **Wait for Dip** | Prior sets dipped 20%+ post-release and recovered; wait ~30 days for a better entry |
| **Pass** | IP is too niche or EN trend is declining; not worth the risk |

## Accuracy tracking

We publish analyses at preorder, then revisit at 30 days, 90 days, and 1 year post-release to measure how accurate our signals were. See each set's update posts.

## Data sources

- **MyAnimeList** (via Jikan API) — anime/manga rankings
- **Yuyutei** — Japanese card prices (scraped)
- **TCGPlayer** — English card prices (scraped)
- **Bushiroad EN product pages** — official pull rate sheets
- **WS community spreadsheets** — historical preorder prices

All price data is a point-in-time snapshot taken at analysis time. Treat recommendations as signals, not financial advice.
