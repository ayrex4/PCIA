# PCIA – Programmable Cognitive Intelligent Agent

PCIA is an **experimental agentic AI desktop automation system** designed to understand natural language user requests, analyze the screen environment, intelligently select the best detection strategy, and execute multi-step actions on a Windows PC.

Moving beyond simple automation scripts, PCIA combines multiple perception methods with a central **decision-planning layer**.

---

# 🧠 Core Concept: Perception → Decision → Execution

The system operates as a **closed-loop agent**.

### Planner (Gemini 2.5 Flash)

Translates an English prompt into a structured **JSON task chain**.

### Decision Engine

Evaluates each task and chooses the most reliable detection method:

* OCR
* Template Matching
* Vision AI

### Execution & Verification

Performs the action and verifies whether the screen state changed using **Visual Memory**.

---

# 🚀 Current Progress (Phase 1–6 Complete)

## ✅ Rock-Solid Foundation

**Fast Perception**

Sub-100ms screen capture with optimized:

* OCR (**Pytesseract**)
* Template Matching (**OpenCV**)

**Universal Navigation**

Uses the **Windows Start Menu strategy** to open any application without needing pre-saved icons.

**Smart Logic**

A **decision matrix** that prioritizes fast local methods (OCR) and falls back to advanced cloud AI (**Gemini**) only when necessary.

---

## ✅ Advanced Cognitive Features

### Visual Settle (Smart Wait)

Instead of static `sleep` timers, PCIA watches the screen and proceeds only when the UI **stops moving** (loading complete).

### Vision Extraction & Memory

The agent can **read specific information** (like an address) from a website, store it in **short-term memory**, and **inject it into another application** (for example WhatsApp).

### Action Verification

After every click, the agent compares **before and after screenshots** to mathematically confirm that the action was effective.

---

# 🔍 Perception & Control Methods

### Vision-Based AI

**Gemini 2.5 Flash** for general object detection and coordinate prediction.

### OpenCV – Template Matching

Pixel-perfect detection of **static UI elements**.

### OCR (Optical Character Recognition)

Reliable **text-based interaction**.

### PyAutoGUI & OS Shortcuts

High-speed **keyboard and mouse execution**.

---

# 🔮 Future Roadmap

### Phase 7 – Self-Healing

Implement a **retry & re-evaluate loop** where the agent asks Vision AI for help if it becomes stuck.

### Local Vision Models

Integrate **lightweight local models** to reduce API latency and costs.

### Context Memory

Maintain a **long-term database** of user preferences and recurring tasks.

### Voice Integration

Add a **hands-free voice interface** to trigger task chains through speech.

---

# 🛠️ Project Status

**Status:** Experimental / Active Development
**Focus:** Hybrid perception systems and autonomous task planning.

---

# 👤 Developer

Developed and maintained by:

**GitHub:** @aymane4
**Social Media:** @ayrex4 (AKA @aymane4)

PCIA is built on the philosophy that a **modular, decision-driven agent can outperform traditional automation by combining deterministic logic with LLM-based reasoning.**
