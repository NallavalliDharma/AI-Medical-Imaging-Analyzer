# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
import google.generativeai as genai
from PIL import Image
import json
import os
from pathlib import Path
from datetime import datetime
import uuid
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT


app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['REPORTS_FOLDER'] = 'reports'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'dcm', 'gif'}

# Create necessary folders
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)


SSH_API_KEY = "AIzaSyApAapjt8UNHKtnonmZIVQCLpLsYA3NMi0"  # Replace with your API key
genai.configure(api_key=SSH_API_KEY)

# ============================================================================
# MEDICAL ANALYZER (Simplified for Web)
# ============================================================================

class WebMedicalAnalyzer:
    """Optimized analyzer for web interface"""
    
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.5-flash")
    
    def analyze_medical_image(self, image_path: str, clinical_context: str = "") -> dict:
        """Analyze medical image and generate report"""
        
        # Load image
        image = Image.open(image_path)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if needed
        max_size = 2048
        if max(image.size) > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Detect modality
        modality_info = self._detect_modality(image)
        
        # Perform analysis
        analysis = self._analyze_image(image, modality_info, clinical_context)
        
        # Generate report
        report = self._generate_report(image, modality_info, analysis, clinical_context)
        
        return {
            "modality": modality_info,
            "analysis": analysis,
            "report": report,
            "timestamp": datetime.now().isoformat()
        }
    
    def _detect_modality(self, image: Image.Image) -> dict:
        """Detect imaging modality"""
        
        prompt = """
        Identify this medical image quickly:
        
        Return ONLY JSON:
        {
            "type": "X-ray|MRI|CT|Ultrasound|Other",
            "body_region": "Chest|Brain|Abdomen|etc",
            "view": "PA|AP|Axial|Sagittal|etc",
            "quality": "Excellent|Good|Fair|Poor",
            "suitable": true/false
        }
        """
        
        response = self.model.generate_content([prompt, image])
        return self._parse_json(response.text)
    
    def _analyze_image(self, image: Image.Image, modality: dict, context: str) -> dict:
        """Perform medical analysis"""
        
        prompt = f"""
        Analyze this {modality.get('type', 'medical')} image of {modality.get('body_region', 'unknown region')}.
        
        Clinical Context: {context if context else "Routine examination"}
        
        Provide comprehensive analysis:
        
        1. Key findings (list 3-5 most important)
        2. Pathologies detected (if any)
        3. Severity assessment
        4. Recommendations
        
        Return JSON:
        {{
            "findings": [
                {{"finding": "description", "severity": "normal|mild|moderate|severe", "location": "where"}}
            ],
            "pathologies": ["list of detected conditions"],
            "overall_assessment": "summary",
            "urgency": "routine|urgent|emergent",
            "recommendations": ["recommendation 1", "recommendation 2"]
        }}
        """
        
        response = self.model.generate_content([prompt, image])
        return self._parse_json(response.text)
    
    def _generate_report(self, image: Image.Image, modality: dict, analysis: dict, context: str) -> str:
        """Generate formatted medical report"""
        
        prompt = f"""
        Generate a professional radiology report.
        
        STUDY TYPE: {modality.get('type', 'Unknown')} - {modality.get('body_region', 'Unknown')}
        
        CLINICAL INDICATION: {context if context else "Routine examination"}
        
        ANALYSIS:
        {json.dumps(analysis, indent=2)}
        
        Create a structured report with:
        
        RADIOLOGY REPORT
        ================
        
        CLINICAL INDICATION:
        [Brief statement]
        
        TECHNIQUE:
        [Imaging details]
        
        FINDINGS:
        [Detailed findings - normal structures brief, abnormalities detailed]
        
        IMPRESSION:
        1. [Most important finding]
        2. [Second finding]
        ...
        
        RECOMMENDATIONS:
        [Specific recommendations]
        
        Use professional medical language. Be clear and concise.
        """
        
        response = self.model.generate_content([prompt, image])
        return response.text
    
    def _parse_json(self, text: str) -> dict:
        """Parse JSON from response"""
        try:
            text = text.strip()
            if '```' in text:
                parts = text.split('```')
                for part in parts:
                    if part.strip().startswith('json'):
                        part = part.strip()[4:]
                    if part.strip().startswith('{'):
                        text = part.strip()
                        break
            
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
            
            return {"error": "Failed to parse", "raw": text[:200]}
        except Exception as e:
            return {"error": str(e)}

# ============================================================================
# PDF GENERATOR
# ============================================================================

class PDFReportGenerator:
    """Generate professional PDF reports"""
    
    @staticmethod
    def generate_pdf(report_data: dict, output_path: str):
        """Create PDF report"""
        
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title
        story.append(Paragraph("MEDICAL IMAGING REPORT", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Metadata table
        modality = report_data.get('modality', {})
        metadata = [
            ['Study Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Modality:', modality.get('type', 'Unknown')],
            ['Body Region:', modality.get('body_region', 'Unknown')],
            ['View:', modality.get('view', 'Unknown')],
            ['Image Quality:', modality.get('quality', 'Unknown')]
        ]
        
        t = Table(metadata, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0fe')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3*inch))
        
        # Report content
        report_text = report_data.get('report', 'No report generated')
        
        # Split report into sections
        sections = report_text.split('\n\n')
        for section in sections:
            if section.strip():
                # Check if it's a heading (all caps or starts with number)
                if section.strip().isupper() or section.strip()[0].isdigit():
                    story.append(Paragraph(section.strip(), heading_style))
                else:
                    story.append(Paragraph(section.strip(), styles['BodyText']))
                story.append(Spacer(1, 0.1*inch))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_text = f"Generated by AI Medical Imaging System v2.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(footer_text, styles['Italic']))
        
        # Build PDF
        doc.build(story)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def generate_report_id():
    """Generate unique report ID"""
    return f"RPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8].upper()}"

# Initialize analyzer
analyzer = WebMedicalAnalyzer()

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and analysis"""
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    clinical_context = request.form.get('clinical_context', '')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, DCM'}), 400
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        # Analyze image
        result = analyzer.analyze_medical_image(filepath, clinical_context)
        
        # Generate report ID
        report_id = generate_report_id()
        
        # Save report
        report_path = os.path.join(app.config['REPORTS_FOLDER'], f"{report_id}.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                'report_id': report_id,
                'filename': filename,
                'clinical_context': clinical_context,
                **result
            }, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'report_id': report_id,
            'modality': result['modality'],
            'analysis': result['analysis'],
            'report': result['report']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<report_id>/<format>')
def download_report(report_id, format):
    """Download report in specified format"""
    
    try:
        # Load report data
        report_path = os.path.join(app.config['REPORTS_FOLDER'], f"{report_id}.json")
        
        if not os.path.exists(report_path):
            return jsonify({'error': 'Report not found'}), 404
        
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        if format == 'pdf':
            # Generate PDF
            pdf_path = os.path.join(app.config['REPORTS_FOLDER'], f"{report_id}.pdf")
            PDFReportGenerator.generate_pdf(report_data, pdf_path)
            return send_file(pdf_path, as_attachment=True, download_name=f"{report_id}.pdf")
        
        elif format == 'txt':
            # Generate TXT
            txt_content = f"""MEDICAL IMAGING REPORT
{'='*60}

Report ID: {report_data.get('report_id', 'N/A')}
Generated: {report_data.get('timestamp', 'N/A')}

STUDY INFORMATION
{'='*60}
Modality: {report_data.get('modality', {}).get('type', 'N/A')}
Body Region: {report_data.get('modality', {}).get('body_region', 'N/A')}
View: {report_data.get('modality', {}).get('view', 'N/A')}
Quality: {report_data.get('modality', {}).get('quality', 'N/A')}

CLINICAL INDICATION
{'='*60}
{report_data.get('clinical_context', 'Not provided')}

{'='*60}
{report_data.get('report', 'No report generated')}
{'='*60}

Generated by AI Medical Imaging System v2.0
"""
            
            txt_buffer = io.BytesIO()
            txt_buffer.write(txt_content.encode('utf-8'))
            txt_buffer.seek(0)
            
            return send_file(
                txt_buffer,
                as_attachment=True,
                download_name=f"{report_id}.txt",
                mimetype='text/plain'
            )
        
        elif format == 'json':
            # Return JSON
            return send_file(
                report_path,
                as_attachment=True,
                download_name=f"{report_id}.json"
            )
        
        else:
            return jsonify({'error': 'Invalid format'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/history')
def get_history():
    """Get list of all reports"""
    
    try:
        reports = []
        for filename in os.listdir(app.config['REPORTS_FOLDER']):
            if filename.endswith('.json'):
                filepath = os.path.join(app.config['REPORTS_FOLDER'], filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    reports.append({
                        'report_id': data.get('report_id'),
                        'timestamp': data.get('timestamp'),
                        'modality': data.get('modality', {}).get('type'),
                        'body_region': data.get('modality', {}).get('body_region')
                    })
        
        # Sort by timestamp (newest first)
        reports.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify({'reports': reports})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# HTML TEMPLATE (Save as templates/index.html)
# ============================================================================

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Medical Imaging Analysis</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .main-card {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        
        .upload-section {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 60px 20px;
            text-align: center;
            background: #f8f9ff;
            transition: all 0.3s;
            cursor: pointer;
        }
        
        .upload-section:hover {
            border-color: #764ba2;
            background: #f0f2ff;
        }
        
        .upload-section.dragover {
            border-color: #4caf50;
            background: #e8f5e9;
        }
        
        .upload-icon {
            font-size: 4em;
            margin-bottom: 20px;
            color: #667eea;
        }
        
        .file-input {
            display: none;
        }
        
        .upload-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 40px;
            border: none;
            border-radius: 30px;
            font-size: 1.1em;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .upload-button:hover {
            transform: scale(1.05);
        }
        
        .clinical-context {
            margin-top: 30px;
        }
        
        .clinical-context textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-size: 1em;
            font-family: inherit;
            resize: vertical;
            min-height: 100px;
        }
        
        .clinical-context textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .analyze-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 50px;
            border: none;
            border-radius: 30px;
            font-size: 1.2em;
            cursor: pointer;
            margin-top: 20px;
            transition: transform 0.2s;
        }
        
        .analyze-button:hover:not(:disabled) {
            transform: scale(1.05);
        }
        
        .analyze-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .loading {
            display: none;
            text-align: center;
            margin-top: 30px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .result-section {
            display: none;
            margin-top: 40px;
        }
        
        .modality-info {
            background: #f8f9ff;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .modality-info h3 {
            color: #667eea;
            margin-bottom: 15px;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .info-item {
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .info-label {
            font-weight: bold;
            color: #666;
            font-size: 0.9em;
        }
        
        .info-value {
            color: #333;
            font-size: 1.1em;
            margin-top: 5px;
        }
        
        .report-content {
            background: white;
            padding: 30px;
            border-radius: 10px;
            border: 2px solid #e0e0e0;
            margin-top: 20px;
            white-space: pre-wrap;
            line-height: 1.8;
            font-size: 0.95em;
        }
        
        .download-buttons {
            margin-top: 30px;
            text-align: center;
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .download-btn {
            background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 25px;
            font-size: 1em;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: transform 0.2s;
        }
        
        .download-btn:hover {
            transform: scale(1.05);
        }
        
        .download-btn.pdf {
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        }
        
        .download-btn.txt {
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
        }
        
        .error-message {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            display: none;
        }
        
        .success-badge {
            background: #4caf50;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            display: inline-block;
            margin-left: 10px;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2em;
            }
            
            .main-card {
                padding: 20px;
            }
            
            .download-buttons {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏥 AI Medical Imaging Analysis</h1>
            <p>Professional Radiology Report Generation Platform</p>
        </div>
        
        <div class="main-card">
            <div class="upload-section" id="uploadSection">
                <div class="upload-icon">📁</div>
                <h2>Drag & Drop Medical Image</h2>
                <p>or click to browse</p>
                <input type="file" id="fileInput" class="file-input" accept=".png,.jpg,.jpeg,.dcm">
                <p style="margin-top: 20px; color: #666;">Supported: PNG, JPG, JPEG, DICOM</p>
            </div>
            
            <div class="clinical-context">
                <h3>Clinical Context (Optional)</h3>
                <textarea id="clinicalContext" placeholder="Enter patient history, symptoms, indication for imaging, etc.
                
Example:
- Patient: 65-year-old male
- Chief complaint: Chest pain, shortness of breath
- History: Hypertension, diabetes
- Indication: Assess for cardiomegaly, pulmonary edema"></textarea>
            </div>
            
            <div style="text-align: center;">
                <button class="analyze-button" id="analyzeBtn" disabled>🔬 Analyze Image</button>
            </div>
            
            <div class="loading" id="loadingSection">
                <div class="spinner"></div>
                <p>Analyzing medical image... This may take 30-60 seconds.</p>
            </div>
            
            <div class="error-message" id="errorMessage"></div>
            
            <div class="result-section" id="resultSection">
                <h2>Analysis Results <span class="success-badge" id="successBadge">✓ Complete</span></h2>
                
                <div class="modality-info">
                    <h3>Study Information</h3>
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Modality</div>
                            <div class="info-value" id="modalityType">-</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Body Region</div>
                            <div class="info-value" id="bodyRegion">-</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">View</div>
                            <div class="info-value" id="view">-</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Quality</div>
                            <div class="info-value" id="quality">-</div>
                        </div>
                    </div>
                </div>
                
                <h3>Radiology Report</h3>
                <div class="report-content" id="reportContent"></div>
                
                <div class="download-buttons">
                    <a href="#" class="download-btn pdf" id="downloadPDF">📄 Download PDF</a>
                    <a href="#" class="download-btn txt" id="downloadTXT">📝 Download TXT</a>
                    <a href="#" class="download-btn" id="downloadJSON">💾 Download JSON</a>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let selectedFile = null;
        let currentReportId = null;
        
        const uploadSection = document.getElementById('uploadSection');
        const fileInput = document.getElementById('fileInput');
        const analyzeBtn = document.getElementById('analyzeBtn');
        const loadingSection = document.getElementById('loadingSection');
        const resultSection = document.getElementById('resultSection');
        const errorMessage = document.getElementById('errorMessage');
        
        // Click to upload
        uploadSection.addEventListener('click', () => fileInput.click());
        
        // Drag and drop
        uploadSection.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadSection.classList.add('dragover');
        });
        
        uploadSection.addEventListener('dragleave', () => {
            uploadSection.classList.remove('dragover');
        });
        
        uploadSection.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadSection.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFile(files[0]);
            }
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFile(e.target.files[0]);
            }
        });
        
        function handleFile(file) {
            selectedFile = file;
            uploadSection.innerHTML = `
                <div class="upload-icon">✅</div>
                <h3>${file.name}</h3>
                <p>${(file.size / 1024 / 1024).toFixed(2)} MB</p>
                <p style="color: #4caf50; margin-top: 10px;">Ready to analyze!</p>
            `;
            analyzeBtn.disabled = false;
        }
        
        analyzeBtn.addEventListener('click', async () => {
            if (!selectedFile) return;
            
            const formData = new FormData();
            formData.append('file', selectedFile);
            formData.append('clinical_context', document.getElementById('clinicalContext').value);
            
            // Show loading
            loadingSection.style.display = 'block';
            resultSection.style.display = 'none';
            errorMessage.style.display = 'none';
            analyzeBtn.disabled = true;
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    currentReportId = data.report_id;
                    displayResults(data);
                } else {
                    showError(data.error || 'Analysis failed');
                }
            } catch (error) {
                showError('Network error: ' + error.message);
            } finally {
                loadingSection.style.display = 'none';
                analyzeBtn.disabled = false;
            }
        });
        
        function displayResults(data) {
            // Update modality info
            document.getElementById('modalityType').textContent = data.modality.type || 'Unknown';
            document.getElementById('bodyRegion').textContent = data.modality.body_region || 'Unknown';
            document.getElementById('view').textContent = data.modality.view || 'Unknown';
            document.getElementById('quality').textContent = data.modality.quality || 'Unknown';
            
            // Update report content
            document.getElementById('reportContent').textContent = data.report;
            
            // Setup download links
            document.getElementById('downloadPDF').href = `/download/${currentReportId}/pdf`;
            document.getElementById('downloadTXT').href = `/download/${currentReportId}/txt`;
            document.getElementById('downloadJSON').href = `/download/${currentReportId}/json`;
            
            // Show results
            resultSection.style.display = 'block';
            
            // Scroll to results
            resultSection.scrollIntoView({ behavior: 'smooth' });
        }
        
        function showError(message) {
            errorMessage.textContent = '❌ Error: ' + message;
            errorMessage.style.display = 'block';
        }
    </script>
</body>
</html>"""

if __name__ == '__main__':
    # Force UTF-8 output for Windows console
    import sys
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    # Create templates folder and save HTML
    os.makedirs('templates', exist_ok=True)
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(HTML_TEMPLATE)
    
    print("="*80)
    print("  MEDICAL IMAGING WEB APPLICATION")
    print("="*80)
    print("\nStarting Flask server...")
    print("[+] Open your browser and go to: http://localhost:5000")
    print("\n[*] Features:")
    print("   - Drag & drop image upload")
    print("   - Real-time analysis")
    print("   - Download reports as PDF/TXT/JSON")
    print("   - Beautiful modern UI")
    print("\n" + "="*80 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)