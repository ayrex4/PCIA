<h1 align="center">🧠 PCIA — Programmable Cognitive Intelligent Agent</h1>

<p align="center">
  <a href="https://github.com/ayrex4/PCIA">
    <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3200&pause=1200&color=22C55E&center=true&vCenter=true&width=700&lines=Programmable+Cognitive+Intelligent+Agent;Autonomous+Desktop+Research+Agent;Built+with+Gemini+AI;Adaptive+Planning+%7C+Visual+Automation" alt="Typing Animation"/>
  </a>
</p>

<p align="center">
  <em>An experimental autonomous AI that doesn't just chat—it controls your PC.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Version-0.2-22C55E?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Python-3.10+-1E3A8A?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Gemini_AI-0EA5E9?style=for-the-badge&logo=google&logoColor=white"/>
  <img src="https://img.shields.io/badge/Windows_11-0078D4?style=for-the-badge&logo=windows&logoColor=white"/>
</p>

---

## 💡 About the Project

**PCIA** is a cutting-edge **autonomous desktop agent**. Unlike traditional automation tools or chatbots, PCIA acts like a true digital assistant. It bridges the gap between human intent and system execution by combining **Chain-of-Thought Planning**, **Visual UI Verification**, and **Real-Time System Observation**.

Give PCIA a complex task, and it will autonomously use your keyboard, mouse, terminal, and browser to get it done.

---

## 🚀 Quickstart: How to Use PCIA

Ready to let PCIA take the wheel? Follow these steps to get started:

### 1. Clone & Install
```bash
# Clone the repository
git clone https://github.com/ayrex4/PCIA.git
cd PCIA

# Install required dependencies
pip install -r requirements.txt
```

### 2. Environment Setup
Create a `.env` file in the root directory and add your Gemini API key, plus the path to your Tesseract OCR installation:

```env
GEMINI_API_KEY=your_gemini_api_key_here
TESSERACT_CMD_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```
*(Note: You must have [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) installed on your Windows machine).*

### 3. Run the Agent
Start the cognitive engine by running:
```bash
python main.py
```
Type your prompt (e.g., *"Send a high-quality photo of a Porsche 911 to my best friend on WhatsApp"*), hit Enter, and take your hands off the keyboard!

---

## ✨ What's New in Version 0.2?

We've massively upgraded PCIA to be more capable, persistent, and powerful. 

<details>
<summary><b>🖼️ Image Scraping & Delivery</b></summary>
<blockquote>
PCIA can now intelligently search the web, download high-quality images, and physically copy them directly into your chats. <i>(Example: "Send my friend a photo of a car.")</i>
</blockquote>
</details>

<details>
<summary><b>🎵 Spotify Music Control</b></summary>
<blockquote>
Fully integrated ability to search for and play music directly on your desktop Spotify app.
</blockquote>
</details>

<details>
<summary><b>🧠 Persistent Memory</b></summary>
<blockquote>
A new JSON-based memory function allows the agent to learn and remember important details about you and your preferences across sessions.
</blockquote>
</details>

<details>
<summary><b>💻 Direct Terminal Control</b></summary>
<blockquote>
The agent can now safely execute Terminal/CMD commands directly. It can create complex folder structures, manipulate files, or even shut down your laptop upon request!
</blockquote>
</details>

---

## 🧠 How It Works: The Architecture

PCIA uses a multi-layered cognitive architecture to handle unpredictability in desktop environments.

```mermaid
graph TD
    A[Human Request] -->|Parsed via main.py| B(Task Planner - Gemini AI)
    B -->|Generates JSON| C[Execution Pipeline]
    
    C --> D{Dynamic UI Encountered?}
    D -- Yes --> E[Spawn Tactical Mini-Brain]
    E -->|Analyze Screen & Adjust| C
    
    D -- No --> F[Physical Execution]
    F -->|Mouse/Keyboard/Terminal| G[Visual & OCR Verification]
    
    G --> H{Execution Success?}
    H -- Yes --> I((Task Complete))
    H -- No --> J[Log to learning_log.json]
    J -->|Self-Heal| B
```

---

## ⚙️ Core Capabilities

- **Self-Healing Execution**: Mistakes happen, but PCIA learns. Execution errors are automatically recorded and injected into the planner so it **never repeats a failure**.
- **Physical Scraping**: Bypassing most anti-bot protections, PCIA uses physical hotkeys (`Ctrl + A`, `Ctrl + C`) to ingest webpage content directly from the browser, exactly like a human would.
- **Context Awareness**: The agent continuously monitors your OS environment (CPU load, RAM usage, open windows) to dynamically adjust its execution timing and maintain stability.

---

## 🛣️ Roadmap: Version 0.3

The next frontier for PCIA is breaking the text barrier. **Version 0.3 will introduce Real-Time Conversation!** 
- **STT & TTS Integration**: You will be able to speak to PCIA directly (Speech-to-Text) and it will reply to you audibly (Text-to-Speech), making it a truly interactive voice assistant for your desktop.

---

## 📊 Project Progress

<div align="center">
  <img src="https://github-readme-activity-graph.vercel.app/graph?username=ayrex4&bg_color=0d1117&color=22c55e&line=3b82f6&point=ffffff&hide_border=true"/>
</div>

Explore the detailed development history in the repository: 👉 **[Insights Tab](https://github.com/ayrex4/PCIA/pulse)**  

---

## 🌐 Connect With Me

<p align="center">
  <a href="mailto:aissaoui.aymane.24@ump.ac.ma">
    <img src="https://img.shields.io/badge/Email-0284C7?style=for-the-badge&logo=gmail&logoColor=white"/>
  </a>
  <a href="https://linkedin.com/in/aymane-aissaoui">
    <img src="https://img.shields.io/badge/LinkedIn-0369A1?style=for-the-badge&logo=linkedin&logoColor=white"/>
  </a>
  <a href="https://discord.com/users/phan_tom_7">
    <img src="https://img.shields.io/badge/Discord-22C55E?style=for-the-badge&logo=discord&logoColor=white"/>
  </a>
</p>

---

<p align="center">
  ☕ **Turning coffee into code**
</p>
