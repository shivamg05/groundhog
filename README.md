# 🦫 Groundhog: Autonomous Web Agent

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/shivamg05/groundhog/blob/main/notebooks/demo.ipynb)
[![Hugging Face Model](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Model-blue)](https://huggingface.co/shivamg05/groundhog-v1)

Groundhog is a **local-first autonomous web agent** that navigates the internet to accomplish natural language goals. 

Unlike most agents that rely on expensive, closed-source APIs (like GPT-4o), Groundhog runs entirely on **open-source models** (Qwen2.5-VL) that you can run yourself.

## 🚀 Try it Now

You don't need a GPU to try this! I have prepared a Google Colab notebook that installs Chrome, loads the model, and launches a web interface for you to watch the agent work.

[**Click here to launch the Demo**](https://colab.research.google.com/github/shivamg05/groundhog/blob/main/notebooks/demo.ipynb)


## 🧠 How it Works

### 1. Fine-Tuned VLM
The core is **[groundhog-v1](https://huggingface.co/shivamg05/groundhog-v1)**, a model I fine-tuned using `Qwen2.5-VL-7B-Instruct` as the base model. It was trained using **QLoRA** on a preprocessed subset of the **Mind2Web** dataset to specialize in web navigation, turning visual UI elements into actionable JSON commands.

### 2. The Stamping Architecture
Raw HTML is too noisy for VLMs. Groundhog uses a custom inference pipeline:
1.  A custom JavaScript engine "stamps" every interactive element in the browser with a unique ID (`[1]`, `[2]`).
2.  It then extracts a simplified DOM tree containing only elements currently visible in the viewport.
3.  The model receives the Screenshot and the Distilled DOM. It correlates the visual location of a button with its stamped ID.
4.  The model outputs a JSON command (e.g., `{"action": "click", "element_id": "15"}`).

### 3. Deterministic Controller
Language models hallucinate. Groundhog wraps the model in a Python controller that validates predictions against the live browser state. If the model tries to click a non-existent ID, the controller catches it and triggers a retry or scroll sequence instead of crashing.


## 📦 Local Installation

To run Groundhog locally, you need a machine with an **NVIDIA GPU (8GB+ VRAM)** because the model uses 4-bit quantization (BitsAndBytes).

1. **Clone the repository**
   ```bash
   git clone https://github.com/shivamg05/groundhog.git
   cd groundhog


for more information on me visit https://shivamgarg.me!