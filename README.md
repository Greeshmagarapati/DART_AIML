# 🛡️ FSSAI DART — AI-Powered Food Adulteration Detection Website

An AI-integrated website based on the FSSAI DART (Detect Adulteration with Rapid Test) manual.
Helps users detect food adulteration using 44 official DART tests with AI-powered result analysis.

---

## 📁 Project Structure

```
fssai-dart/
├── frontend/               ← React + Vite + Tailwind CSS
│   ├── src/
│   │   ├── data/
│   │   │   └── dartTests.js       ← All 44 DART tests data
│   │   ├── pages/
│   │   │   ├── Home.jsx           ← Landing page
│   │   │   ├── Categories.jsx     ← 7 food categories
│   │   │   ├── TestList.jsx       ← Tests within a category
│   │   │   ├── TestDetail.jsx     ← Full test + AI analysis
│   │   │   ├── Chatbot.jsx        ← AI chat assistant
│   │   │   └── Awareness.jsx      ← Food safety education
│   │   ├── components/
│   │   │   └── Navbar.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── backend/                ← FastAPI + Python
│   ├── main.py             ← API routes (analyze + chat)
│   ├── static_responses.py ← Rule-based fallback responses
│   ├── requirements.txt
│   └── .env.example
│
└── README.md
```

---

## ⚡ Tech Stack

| Layer      | Technology              |
|------------|-------------------------|
| Frontend   | React 18 + Vite         |
| Styling    | Tailwind CSS            |
| Routing    | React Router v6         |
| HTTP       | Axios                   |
| Backend    | FastAPI (Python)        |
| AI         | Anthropic Claude API    |
| Fallback   | Static rule-based logic |

---

## 🚀 Setup Instructions

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and add your Anthropic API key (optional)
# If no API key → app uses static rule-based responses automatically

# Run backend
uvicorn main:app --reload --port 8000
```

Backend will run at: http://localhost:8000  
API docs at: http://localhost:8000/docs

---

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will run at: http://localhost:5173

---

## 🤖 AI Chatbot — Dual Mode

The chatbot works in **two modes automatically**:

### Mode 1: With Anthropic API Key (Full AI)
- Set `ANTHROPIC_API_KEY=sk-ant-...` in `backend/.env`
- Claude claude-sonnet-4-20250514 analyzes observations
- Detailed, context-aware responses
- Natural language Q&A

### Mode 2: Without API Key (Static Fallback)
- No API key needed
- Keyword-based rule matching
- Pre-trained responses for all major tests
- Works fully offline

The app **automatically detects** which mode to use — no code changes needed!

---

## 🧪 DART Tests Covered (All 44)

### 🥛 Milk & Dairy (4 tests)
- Water in milk
- Detergent in milk
- Starch in milk/khoya/paneer/chenna
- Starch in ghee/butter

### 🫙 Oils & Fats (3 tests)
- Other oils in coconut oil
- TOCP in oils (toxic industrial chemical)
- Winterization of salad oils

### 🍯 Sweets & Sugar (3 tests)
- Sugar solution in honey
- Chalk in sugar/jaggery
- Aluminium in silver leaves (vark)

### 🌾 Cereals & Pulses (9 tests)
- Extraneous matter in food grains
- Dhatura seeds in food grains (CRITICAL)
- Excess bran in wheat flour
- Khesari dal in pulses (causes paralysis)
- Artificial colour in food grains
- Turmeric in sella rice
- Rhodamine B in ragi (carcinogenic)
- Chakunda beans in pulses
- Sand/soil/insects in atta/maida/suji

### 🌶️ Spices (16 tests)
- Foreign resin in asafoetida (hing)
- Papaya seeds in black pepper
- Light berries in black pepper (2 methods)
- Soap stone in asafoetida
- Artificial colour in chilli powder
- Saw dust in chilli powder
- Starch in asafoetida
- Chalk in common salt
- Exhausted cloves in cloves
- Cassia bark in cinnamon
- Charcoal-coloured grass seeds in cumin
- Argemone seeds in mustard (CRITICAL)
- Lead chromate in turmeric (CRITICAL)
- Artificial colour in turmeric powder (CRITICAL)
- Sawdust/bran in powdered spices

### 🥦 Vegetables & Fruits (5 tests)
- Iodised vs common salt
- Coloured maize tendrils in saffron
- Malachite green in vegetables (CRITICAL)
- Artificial colour on green peas
- Rhodamine B in sweet potato (CRITICAL)

### ☕ Beverages (4 tests)
- Clay in coffee powder
- Chicory in coffee powder
- Exhausted tea / coal tar colour in tea
- Iron filings in tea leaves

---

## 🎨 Features

- ✅ Multi-page React app with React Router
- ✅ All 44 DART tests with full procedure text
- ✅ Risk levels (Safe / Low / Medium / High / Critical)
- ✅ AI-powered observation analysis (Claude)
- ✅ Static fallback when no API key
- ✅ Offline client-side fallback when backend is down
- ✅ Interactive AI chatbot with quick questions
- ✅ Food safety awareness page
- ✅ FSSAI contact integration
- ✅ Mobile-responsive design
- ✅ Color-coded results (Green = Safe, Red = Adulterated)

---

## 📞 FSSAI Contacts
- **Toll-Free:** 1800-11-2100
- **WhatsApp:** 98 6868 6868
- **Email:** compliance@fssai.gov.in
- **Website:** www.fssai.gov.in

---

## 🔑 Getting Anthropic API Key
1. Go to https://console.anthropic.com
2. Sign up / Log in
3. Create an API key
4. Add to `backend/.env` as `ANTHROPIC_API_KEY=sk-ant-...`

*Without API key, the app works perfectly using static responses!*
