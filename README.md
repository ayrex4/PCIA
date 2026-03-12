# 🧠 PCIA – Programmable Cognitive Intelligent Agent

PCIA is an **experimental agentic AI desktop automation system**.  
Unlike traditional automation tools, PCIA behaves like a **cognitive agent** that can perceive its environment, reason about tasks, and execute complex workflows autonomously on Windows.

The goal of PCIA is to overcome the brittleness of traditional scripts by combining **deterministic OS interaction** with **LLM-based reasoning and planning**.

---

# 🧠 Architecture – The Cognitive Loop

PCIA operates using a **closed-loop cognitive architecture** that mimics a simplified reasoning system.

## 1️⃣ Main Brain (Gemini 2.5 / 3.1)

The **Main Brain** translates natural language instructions into a structured **JSON Task Chain**.

It performs **chain-of-thought reasoning** to break a complex goal into smaller tactical steps.

Example workflow:

```
User Prompt → Reasoning → Task Chain → Execution
```

---

## 2️⃣ Tactical Mini-Brain

When the Main Brain encounters a **dynamic interface** (such as search results or unpredictable UI elements), it triggers a **Replan process**.

The **Mini-Brain**:

- analyzes a **live screenshot**
- detects UI elements
- executes precise actions like:
  - clicking links
  - scrolling
  - selecting results

This allows the system to adapt to **dynamic interfaces in real time**.

---

## 3️⃣ Execution & Verification Layer

PCIA interacts directly with the operating system while continuously verifying results.

### Physical Scraper

Uses keyboard interaction:

```
Ctrl + A
Ctrl + C
```

to capture webpage content without relying on APIs or bypassing bot restrictions.

---

### Visual Wait System

Instead of using static delays, PCIA:

- monitors **pixel stability**
- waits for the interface to finish loading
- executes actions only when the UI is stable

This greatly improves reliability.

---

### Self-Healing Mechanism

Execution failures are automatically logged inside:

```
learning_log.json
```

These logs are injected back into the planning system so the agent can **avoid repeating the same mistakes**.

---

# 🚀 Progress Log (Phase 1 – Phase 6)

## ✅ Cognitive Foundation

- **System Awareness**

  The agent detects:
  - OS
  - CPU load
  - RAM usage

  and dynamically adjusts execution speed and wait times.

---

- **Error Recovery**

  A **Learning Journal** records execution failures so the system can learn from past mistakes.

---

- **Recursive Planning**

  The system can spawn **Mini-Brain subprocesses** to solve UI problems such as:

  - scrolling
  - clicking dynamic elements
  - navigating search results

---

## ✅ Navigation & Data Acquisition

### Universal Launch System

Applications are opened using **Windows Search (`Win` key)** instead of icon templates, making launching much more reliable.

---

### Physical Scraping

Clipboard-based scraping allows PCIA to ingest data from webpages while bypassing most anti-bot restrictions.

---

### Vision + OCR Hybrid

PCIA combines:

- **Vision AI** for object detection
- **Local OCR** for pixel-precise text targeting

This enables accurate UI interaction.

---

# 🔮 Future Roadmap

### 🧠 Long-Term Memory

Integration of a **vector database (RAG)** so the agent can remember:

- user preferences
- previous tasks
- context between sessions

---

### 🎤 Voice Interface

Speech-to-text integration allowing users to trigger task chains **hands-free**.

---

### 🔁 Self-Correction Loop

The agent will analyze its own crash logs and automatically:

```
Detect Error → Replan → Retry Execution
```

---

### 🖥️ Local Vision Models

Migrating from cloud vision services to **local models** for:

- improved privacy
- lower latency
- offline capability

---

# 🛠️ Project Status

**Status:** 🧪 Experimental / Active Development  

**Current Focus:**

- Recursive planning
- Sub-goal decomposition
- Physical UI interaction

---

# 👤 Developer

Developed and maintained by:

**GitHub:**  
[@ayrex4](https://github.com/ayrex4)

**Social:**  
@ayrex4

---

# ⚙️ Philosophy

PCIA is built on the idea that a **modular, decision-driven agent** can outperform traditional automation.

Instead of rigid scripts, the system combines:

- deterministic system interaction
- reasoning from large language models
- adaptive planning

to create a **flexible cognitive automation agent**.
