# Reading Note: Palantir & ICE — Platform-State Violence Case Study

## Source Information

**Primary Source:** LabourNet Germany  
**Title:** "Palantir & Co.: Die digitalen Abschiebe-helfer der US-Einwanderungsbehörde ICE"  
**Date:** February 3, 2026  
**URL:** https://www.labournet.de/internationales/usa/wirtschaft-usa/palantir-co-die-digitalen-abschiebe-helfer-der-us-einwanderungsbehoerde-ice/  
**Language:** German (with English sources cited)  

**Additional Sources Referenced:**
- Electronic Frontier Foundation (EFF) — legal challenges to ICE data use
- 404 Media — investigative reporting on ICE surveillance tools
- Netzpolitik.org / heise — German tech policy coverage
- The Nation — boycott campaign analysis
- Wired, NYTimes, Washington Post — mainstream coverage

---

## Summary

Comprehensive dossier documenting how Palantir Technologies provides the technical infrastructure for US Immigration and Customs Enforcement (ICE) deportation operations. Reveals a $30+ million contract for "ImmigrationOS" — a platform integrating data from Medicaid, IRS, DMV, social media, and commercial surveillance to create deportation targets, dossiers, and "trust scores" for individuals.

The article documents worker resistance (Capgemini divestment, Palantir employee dissent), boycott campaigns ("Resist and Unsubscribe"), and notes similar Palantir deployments in German police forces (Hessen, Bayern, NRW).

---

## Key Technical Systems

| System | Provider | Function | Data Sources |
|--------|----------|----------|--------------|
| **ImmigrationOS** | Palantir ($30M contract) | Central integration platform | All ICE databases |
| **ELITE** | Palantir | Maps deportation targets, creates dossiers, assigns "trust scores" | Medicaid, USCIS, Thomson Reuters |
| **Tangles/Webloc** | Penlink ($1B potential contract) | Phone location tracking | Advertising industry (hundreds of millions of devices) |
| **Clearview AI** | Clearview | Facial recognition | Social media scraping |
| **Mobile Fortify** | ICE internal | Facial recognition | Field-deployable |
| **Graphite** | Paragon | Spyware (hacks phones, accesses Signal/WhatsApp) | Device-level surveillance |

---

## Data Integration Map

### Government Sources
- **Medicaid** — health data, addresses
- **IRS** — tax records, employment
- **DMV** — driver records, vehicle registration
- **USCIS** — immigration status
- **Social Security Administration**
- **State voter registries**

### Commercial Sources
- **ISO ClaimSearch** — 1.8 billion insurance claims, 58 million medical bills
- **Advertising industry** — location data from apps ("real-time bidding")
- **Thomson Reuters** — commercial databases
- **Data brokers** — aggregated consumer data

### Surveillance Sources
- Social media monitoring
- Facial recognition databases
- Phone location tracking
- License plate readers
- Body cameras (GoPro, Meta Smart Glasses)

---

## Theoretical Framework: Platform-State Violence

### 1. "Cloud Capital" as Repressive Infrastructure

Varoufakis's concept applied:
> "The 'cloud capitalists' control digital infrastructure that enables extraction without production. In the ICE case, this extraction is literal — extracting people from territory."

- **Cloud rent:** $30M+ contract for infrastructure access
- **Digital fiefdom:** ICE as captured client within Palantir's ecosystem
- **Algorithmic Gosplan:** Central planning of deportation logistics

### 2. Data Colonialism Extended

Couldry/Mejias's framework:
- **Traditional:** Data extracted from Global South for Northern platform profits
- **Extension:** Data extracted from marginalized populations (migrants, poor) for state violence
- **Same mechanism:** Appropriation of life resources (data) without consent or compensation

### 3. Platform-State Nexus

New theoretical category:
| Traditional State | Platform-State Nexus |
|-------------------|---------------------|
| Owns infrastructure | Rents infrastructure from platforms |
| Employs bureaucrats | Uses platform algorithms |
| Public accountability | Private, opaque systems |
| Legal process | Algorithmic prediction |

**Critical insight:** The state doesn't just *use* platforms — it becomes *dependent* on them. Palantir's "institutional knowledge" (per contract) makes ICE functionally inseparable from Palantir.

### 4. "Techno-Feudalism" in Practice

Varoufakis's thesis verified:
- Palantir extracts rent without producing deportations (ICE agents do the work)
- "Cloud lords" (Palantir) provide infrastructure to "vassals" (ICE)
- Non-market coordination: algorithmic allocation of deportation targets

**But:** Unlike Varoufakis's "40% cloud rent" claim, here the rent is paid by taxpayers to a private corporation for state violence.

---

## Worker Resistance

### Capgemini Divestment (February 2026)
- **Context:** Capgemini (French tech giant) received ICE contract for "skip-tracing" (tracking hard-to-find immigrants)
- **Pressure:** French CGT union, government officials (including Economy Minister Roland Lescure)
- **Outcome:** Capgemini announced sale of US subsidiary "Capgemini Government Solutions"
- **Significance:** First major tech divestment from ICE contracts due to worker/public pressure

### Palantir Employee Dissent
- **Internal Slack messages** (per Wired/404 Media):
  - "Our involvement with ICE is being swept under the rug internally"
  - "Can Palantir exert any pressure on ICE?"
  - "Are we helping people get detained even when they have no reason to be?"
- **Company response:** Prepared FAQs for employees to send to concerned family/friends

### "Resist and Unsubscribe" Boycott
- **Organizers:** Scott Galloway (NYU professor), tech workers
- **Target:** 10 subscription-based tech companies: Amazon, Apple, Google, Microsoft, Paramount+, Uber, Netflix, X, Meta, OpenAI
- **Duration:** February 2026 (one month)
- **Tactics:** Cancel subscriptions, delete apps, don't click ads
- **Rationale:** "The most radical action in a capitalist society is non-participation"

---

## German/European Dimensions

### Palantir in Germany
- **Hessen:** State police use Palantir for "Gefährder" (threat) tracking
- **Bayern:** Similar deployments
- **Nordrhein-Westfalen:** Police use confirmed
- **Federal level:** Bundesregierung (federal government) uses Palantir products

### EU-US Data Sharing
- US demands access to EU police databases (INPOL in Germany) through Visa Waiver Program
- EU Commission negotiating "framework agreement"
- **Critical concern:** European migrant data accessible to ICE/Palantir systems?

### Capgemini Context
- European company profiting from US deportation machine
- Divestment shows potential for transnational worker solidarity

---

## Critical Assessment

### Strengths of Coverage
- **Multi-source verification:** LabourNet aggregates EFF, 404 Media, mainstream outlets
- **Technical specificity:** Names specific systems, contracts, data flows
- **Worker agency:** Documents resistance, not just victimization
- **Transnational scope:** Connects US ICE to European police use

### Gaps
- **Financial opacity:** Exact contract values unclear
- **Legal analysis:** Could use deeper analysis of constitutional/privacy law
- **Comparative context:** How does ICE-Palantir compare to other state-platform collaborations (China, UK)?
- **Longitudinal data:** When did these contracts start? Escalation timeline?

### Methodological Notes
- **Investigative journalism:** 404 Media, EFF doing original FOIA/sourcing work
- **Activist-academic collaboration:** LabourNet as aggregator/curator
- **Whistleblower reliance:** Internal Palantir docs via leaks

---

## Connections to Research Project

### Direct Relevance

| Chapter | Application |
|---------|-------------|
| **Theoretical Framework** | Tests "techno-feudalism" thesis; extends "data colonialism" |
| **Platform-State Nexus** | New section — this is the flagship case study |
| **Labor Resistance** | Tech worker organizing, union divestment campaigns |
| **EU Regulation** | DMA vs. reality of police-platform collaboration |
| **Global South** | Deportation targets often from Global South; data extraction mirrors colonial patterns |

### Empirical Richness
- **Concrete systems:** Named platforms, costs, data sources
- **Worker voices:** Palantir employees, Capgemini response
- **Legal battles:** EFF lawsuits, EU negotiations
- **Social movements:** Boycotts, protests

### Theoretical Contribution
This case study helps answer:
1. Is Varoufakis's "techno-feudalism" accurate or overstated?
2. How does platform-state collaboration differ from traditional state contracting?
3. What forms of resistance are effective against platform-state violence?
4. How transnational is platform-state infrastructure?

---

## Quotable Passages

> "Palantir arbeitet an einem Tool für die Einwanderungs- und Zollbehörde (ICE), das eine Karte mit potenziellen Abschiebungszielen erstellt, ein Dossier zu jeder Person anzeigt und einen 'Vertrauenswert' für die aktuelle Adresse der Person angibt."

> "Die radikalste Aktion in einer kapitalistischen Gesellschaft ist Nichtteilnahme." — Scott Galloway

> "Unsere Beteiligung bei ICE unter Trump2 wird intern unter dem Teppich gekehrt – zu sehr. Wir brauchen Informationen darüber, wie wir hier involviert sind." — Palantir employee (internal Slack)

> "Wir haben eine nette kleine Datenbank, und jetzt gelten Sie als inländischer Terrorist." — Masked federal agent to protester

---

## Action Items for Project

- [ ] **Compare to European practices:** Research German police Palantir use (INPOL integration)
- [ ] **Legal framework:** Analyze GDPR applicability to police use of Palantir
- [ ] **Worker organizing:** Document tech worker resistance movements (Tech Workers Coalition, etc.)
- [ ] **Financial analysis:** Trace Palantir revenue from government contracts
- [ ] **Historical comparison:** Compare to IBM-Holocaust collaboration (Hollerith machines)
- [ ] **Theoretical refinement:** Does this support or challenge "techno-feudalism"?

---

## Tags

#platform_state_violence #palantir #ice #surveillance #deportation #data_colonialism #techno_feudalism #worker_resistance #boycott #germany #eu_data_policy #case_study

---

*Created: 2026-02-03*  
*Added by: Rook (AI Assistant) for Marcus (PI)*  
*Source: LabourNet Germany dossier with multi-source verification*
