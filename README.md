# 🏥 AI-Powered Medical Imaging Analysis System

An advanced **AI diagnostic platform** that leverages **Google Gemini 2.5 Flash** to perform organ-level analysis and pathology detection from medical images such as **X-rays, MRI, CT, and Ultrasound scans**.
The system generates **professional structured radiology reports** and includes specialized modules for complex cases like **dialysis patients**.

---

# 🌟 Key Features

## 🔍 Automated Modality Detection

* Automatically identifies image types:

  * X-ray
  * MRI
  * CT Scan
  * Ultrasound
* Detects body regions for accurate analysis.

## 🫀 Organ-Aware Analysis

Evaluates important anatomical structures including:

* Heart
* Lungs
* Pleura
* Mediastinum
* Bones
* Diaphragm

## 🧠 Pathology Classification

Detects major medical conditions such as:

* Cardiomegaly
* Pleural Effusion
* Pneumonia
* Atelectasis
* Pulmonary Edema

## 💉 Specialized Dialysis Module

Dedicated analysis for **ESRD (End-Stage Renal Disease)** patients:

* Volume status assessment
* Fluid overload detection
* Vascular access complications
* Dialysis related abnormalities

## 📄 Multi-Format Export

Generate professional reports in multiple formats:

* PDF
* TXT
* JSON

## 🖥️ Modern Web Interface

Features include:

* Responsive dashboard
* Drag & drop image upload
* Real-time analysis progress
* Clean modern UI

---

# 🛠️ Tech Stack

## Backend

* Python 3.9+
* Flask

## AI Engine

* Google Generative AI
* Gemini 2.5 Flash

## Image Processing

* Pillow (PIL)

## Document Generation

* ReportLab (PDF generation)

## Frontend

* HTML5
* CSS3 (Modern Gradient UI)
* JavaScript

---

# 📋 Project Structure

```
AI-Medical-Imaging/
│
├── app.py                # Main Flask application & Web Analyzer logic
├── main.py               # Medical Report Generator & Dialysis Analyzer
├── main1.py              # CLI batch processing version
│
├── templates/
│   └── index.html        # Web dashboard UI
│
├── uploads/              # Temporary uploaded images
├── reports/              # Generated PDF & JSON reports
│
└── requirements.txt      # Dependencies
```

---

# 🚀 Getting Started

## 1️⃣ Installation

Clone the repository:

```
git clone https://github.com/NallavalliDharma/AI-Medical-Imaging.git
cd AI-Medical-Imaging
```

Install dependencies:

```
pip install -r requirements.txt
```

---

## 2️⃣ Configuration

This project requires a **Google Gemini API Key**.

Update the API key inside:

**app.py** or **main.py**

```
SSH_API_KEY = "YOUR_API_KEY_HERE"
```

---

## 3️⃣ Running the Application

## Run Web Application

```
python app.py
```

Open browser:

```
http://localhost:5000
```

## Run CLI Batch Processing

```
python main1.py
```

---

# 🔍 Analysis Pipeline

The system follows a **multi-stage AI analysis pipeline**:

## 1. Modality Detection

* Validates image type
* Checks image quality
* Identifies anatomical region

## 2. Organ Level Analysis

Evaluates:

* Heart condition
* Lung clarity
* Pleural abnormalities
* Bone structures
* Diaphragm condition

## 3. Pathology Detection

Classification system checks:

* High risk conditions
* Severity levels
* Abnormal patterns

## 4. Report Generation

Creates structured radiology reports including:

* Clinical Indication
* Technique
* Findings
* Impression
* Recommendations

---

# ⚠️ Medical Disclaimer

**Important Notice:**

This project is developed for:

* Educational purposes
* Research purposes
* AI experimentation

This system **does NOT replace professional medical diagnosis**.

Always consult:

* Certified Radiologist
* Doctor
* Healthcare professional

for medical decisions.

---

# 👨‍💻 Author

**Nallavalli Dharma**

---

# 📜 License

This project is intended for educational use.

---

# ⭐ Support

If you like this project:

Give a ⭐ on GitHub

---

# 🔮 Future Improvements

Possible enhancements:

* DICOM support
* Multi-image comparison
* Patient history integration
* Model fine-tuning
* Cloud deployment
* User authentication

---

# 🤝 Contributions

Contributions are welcome.

You can:

* Fork the repository
* Create a feature branch
* Submit a pull request

---

# 📬 Contact

For queries or collaboration:

GitHub:
https://github.com/NallavalliDharma

---
