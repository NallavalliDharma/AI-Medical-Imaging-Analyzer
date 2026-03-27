import google.generativeai as genai
from PIL import Image
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple
import base64
from io import BytesIO

class Config:
    """Configuration for the Medical Report Generator"""
    SSH_API_KEY = "AIzaSyApAapjt8UNHKtnonmZIVQCLpLsYA3NMi0"  
    MODEL_NAME = "gemini-2.5-flash" 

    # Organ categories to analyze
    ORGANS = [
        "heart",
        "left_lung",
        "right_lung",
        "pleura",
        "mediastinum",
        "bones",
        "diaphragm"
    ]
    
    # Pathologies to detect
    PATHOLOGIES = [
        "cardiomegaly",
        "pleural_effusion",
        "pneumonia",
        "atelectasis",
        "pulmonary_edema",
        "pneumothorax",
        "lung_nodule",
        "consolidation"
    ]

class MedicalReportGenerator:
    
    
    def __init__(self, api_key: str):
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(Config.MODEL_NAME)
        
    def load_image(self, image_path: str) -> Image.Image:
        """Load and preprocess medical image"""
        img = Image.open(image_path)
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize if too large (optional)
        max_size = 2048
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        return img
    
    def analyze_organs(self, image: Image.Image) -> Dict:
        """
        Task Distillation Module: Analyze organ-level information
        """
        prompt = f"""
        You are an expert radiologist AI analyzing a chest X-ray image.
        
        Perform organ-level analysis for the following structures:
        {', '.join(Config.ORGANS)}
        
        For EACH organ, provide:
        1. Status: "normal" or "abnormal"
        2. If abnormal, describe the findings
        3. Confidence level (high/medium/low)
        
        Format your response as JSON:
        {{
            "organ_analysis": {{
                "heart": {{
                    "status": "normal/abnormal",
                    "findings": "description",
                    "confidence": "high/medium/low"
                }},
                ...
            }}
        }}
        
        Be thorough and medically accurate.
        """
        
        response = self.model.generate_content([prompt, image])
        
        try:
            # Extract JSON from response
            text = response.text
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            json_str = text[json_start:json_end]
            return json.loads(json_str)
        except:
            return {"error": "Failed to parse organ analysis", "raw": response.text}
    
    def detect_pathologies(self, image: Image.Image) -> Dict:
        """
        Classification Module: Detect specific pathologies
        """
        prompt = f"""
        You are an expert radiologist AI. Analyze this chest X-ray for the following pathologies:
        {', '.join(Config.PATHOLOGIES)}
        
        For EACH pathology, determine:
        1. Present: yes/no
        2. Severity: mild/moderate/severe (if present)
        3. Location: specific area affected
        4. Confidence: high/medium/low
        
        Format as JSON:
        {{
            "pathology_detection": {{
                "cardiomegaly": {{
                    "present": true/false,
                    "severity": "mild/moderate/severe",
                    "location": "description",
                    "confidence": "high/medium/low"
                }},
                ...
            }}
        }}
        
        IMPORTANT: For dialysis patients, pay special attention to:
        - Cardiomegaly (enlarged heart)
        - Pleural effusion (fluid around lungs)
        - Pulmonary edema (fluid in lungs)
        - Signs of volume overload
        """
        
        response = self.model.generate_content([prompt, image])
        
        try:
            text = response.text
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            json_str = text[json_start:json_end]
            return json.loads(json_str)
        except:
            return {"error": "Failed to parse pathology detection", "raw": response.text}
    
    def generate_organ_aware_report(
        self, 
        image: Image.Image, 
        organ_analysis: Dict, 
        pathology_detection: Dict,
        patient_context: str = ""
    ) -> str:
        """
        Organ-Aware Report Generation Module
        Generates structured, organ-specific diagnostic reports
        """
        prompt = f"""
        You are an expert radiologist writing a formal diagnostic report for a chest X-ray.
        
        PATIENT CONTEXT:
        {patient_context if patient_context else "No additional patient information provided"}
        
        ORGAN-LEVEL ANALYSIS:
        {json.dumps(organ_analysis, indent=2)}
        
        PATHOLOGY DETECTION:
        {json.dumps(pathology_detection, indent=2)}
        
        Generate a comprehensive radiology report with the following structure:
        
        1. CLINICAL INDICATION:
           - Brief statement of why imaging was performed
        
        2. TECHNIQUE:
           - "Frontal chest radiograph"
        
        3. COMPARISON:
           - State if prior studies available (assume none if not mentioned)
        
        4. FINDINGS (ORGAN-AWARE):
           - For NORMAL organs: Brief, template-based description (1 sentence)
           - For ABNORMAL organs: Detailed, specific findings (2-3 sentences)
           - Use this order: Heart, Lungs, Pleura, Mediastinum, Bones, Soft tissues
        
        5. IMPRESSION:
           - Numbered list of key findings
           - Prioritize abnormal/urgent findings
           - For dialysis patients, specifically mention volume status if relevant
        
        6. RECOMMENDATIONS (if applicable):
           - Follow-up imaging
           - Clinical correlation
           - Urgent findings requiring immediate attention
        
        STYLE GUIDELINES:
        - Professional medical terminology
        - Clear and concise
        - Prioritize clinically significant findings
        - Use standard radiology report format
        - Be definitive where confidence is high, cautious where uncertain
        
        Write the complete report now:
        """
        
        response = self.model.generate_content([prompt, image])
        return response.text
    
    def generate_complete_report(
        self, 
        image_path: str, 
        patient_context: str = "",
        save_output: bool = True
    ) -> Dict:
        """
        Complete end-to-end report generation pipeline
        """
        print(f"Loading image: {image_path}")
        image = self.load_image(image_path)
        
        print("Analyzing organs...")
        organ_analysis = self.analyze_organs(image)
        
        print("Detecting pathologies...")
        pathology_detection = self.detect_pathologies(image)
        
        print("Generating report...")
        report = self.generate_organ_aware_report(
            image, 
            organ_analysis, 
            pathology_detection,
            patient_context
        )
        
        result = {
            "image_path": image_path,
            "organ_analysis": organ_analysis,
            "pathology_detection": pathology_detection,
            "radiology_report": report,
            "patient_context": patient_context
        }
        
        if save_output:
            output_path = Path(image_path).stem + "_report.json"
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Report saved to: {output_path}")
        
        return result
    
    def batch_process(self, image_folder: str, output_folder: str = "reports"):
        """
        Process multiple X-ray images in batch
        """
        os.makedirs(output_folder, exist_ok=True)
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.dcm']
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(Path(image_folder).glob(f'*{ext}'))
        
        results = []
        for i, image_path in enumerate(image_files, 1):
            print(f"\n{'='*60}")
            print(f"Processing {i}/{len(image_files)}: {image_path.name}")
            print(f"{'='*60}")
            
            try:
                result = self.generate_complete_report(str(image_path), save_output=False)
                
                # Save individual report
                output_path = os.path.join(
                    output_folder, 
                    f"{image_path.stem}_report.json"
                )
                with open(output_path, 'w') as f:
                    json.dump(result, f, indent=2)
                
                results.append(result)
                print(f"✓ Success: Report saved to {output_path}")
                
            except Exception as e:
                print(f"✗ Error processing {image_path.name}: {str(e)}")
        
        # Save summary
        summary_path = os.path.join(output_folder, "batch_summary.json")
        with open(summary_path, 'w') as f:
            json.dump({
                "total_processed": len(results),
                "total_images": len(image_files),
                "reports": results
            }, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"Batch processing complete!")
        print(f"Processed: {len(results)}/{len(image_files)} images")
        print(f"Summary saved to: {summary_path}")
        print(f"{'='*60}")
        
        return results

# ============================================================================
# DIALYSIS-SPECIFIC ANALYZER
# ============================================================================

class DialysisPatientAnalyzer(MedicalReportGenerator):
    """
    Specialized analyzer for dialysis patients
    Focuses on complications: cardiomegaly, pleural effusion, edema, vascular issues
    """
    
    def analyze_dialysis_complications(self, image: Image.Image) -> Dict:
        """
        Focused analysis for dialysis-specific complications
        """
        prompt = """
        You are analyzing a chest X-ray for a DIALYSIS PATIENT.
        
        Focus specifically on dialysis-related complications:
        
        1. VOLUME STATUS:
           - Cardiomegaly (heart size - measure cardiothoracic ratio if possible)
           - Pulmonary vascular congestion
           - Pulmonary edema (interstitial or alveolar)
           - Pleural effusions
        
        2. VASCULAR ACCESS COMPLICATIONS:
           - Central venous catheter position (if visible)
           - Pneumothorax (post-catheter insertion)
           - Hemothorax
        
        3. INFECTIOUS COMPLICATIONS:
           - Pneumonia
           - Signs of line infection
        
        4. OTHER COMPLICATIONS:
           - Pericardial effusion
           - Calcifications
        
        Provide assessment as JSON:
        {
            "volume_status": "overloaded/normal/depleted",
            "urgent_findings": [],
            "dialysis_complications": {
                "cardiomegaly": {...},
                "pleural_effusion": {...},
                "pulmonary_edema": {...},
                "vascular_issues": {...}
            },
            "recommendations": []
        }
        """
        
        response = self.model.generate_content([prompt, image])
        
        try:
            text = response.text
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            json_str = text[json_start:json_end]
            return json.loads(json_str)
        except:
            return {"error": "Failed to parse dialysis analysis", "raw": response.text}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main execution function with examples
    """
    
    # Initialize the generator
    generator = MedicalReportGenerator(api_key=Config.SSH_API_KEY)
    
    print("=" * 65)
    print("  AI-Powered Medical Imaging Report Generator")
    print("=" * 65)
    
    # Example 1: Single image analysis
    print("\n[Example 1] Single X-ray Analysis")
    print("-" * 60)
    
    # Replace with your actual image path
    image_path = "chest_image.png"
    
    if os.path.exists(image_path):
        patient_context = """
        Patient: 65-year-old male
        History: End-stage renal disease on hemodialysis
        Indication: Routine dialysis imaging, assess for fluid overload
        """
        
        result = generator.generate_complete_report(
            image_path, 
            patient_context=patient_context
        )
        
        print("\n" + "="*60)
        print("GENERATED RADIOLOGY REPORT")
        print("="*60)
        print(result['radiology_report'])
    else:
        print(f"Image not found: {image_path}")
        print("Please provide a valid chest X-ray image path")
    
    # Example 2: Batch processing
    print("\n\n[Example 2] Batch Processing")
    print("-" * 60)
    print("To process multiple images, use:")
    print("generator.batch_process('path/to/xray/folder', 'output_reports')")
    
    # Example 3: Dialysis-specific analysis
    print("\n\n[Example 3] Dialysis Patient Analysis")
    print("-" * 60)
    print("For dialysis-specific analysis:")
    print("dialysis_analyzer.generate_complete_report('dialysis_patient_xray.jpg')")

if __name__ == "__main__":
    main()