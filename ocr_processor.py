"""
OCR and Prescription Image Processing
"""

try:
    import pytesseract
    # Configure Tesseract path for Windows
    import os
    tesseract_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        os.path.expanduser(r'~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'),
    ]
    for path in tesseract_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

from PIL import Image
import re
from io import BytesIO
import base64

# Common medicine names for matching against OCR text
KNOWN_MEDICINES = [
    "aspirin", "metformin", "amoxicillin", "lisinopril", "ibuprofen", "atorvastatin",
    "omeprazole", "amlodipine", "metoprolol", "losartan", "simvastatin", "levothyroxine",
    "azithromycin", "hydrochlorothiazide", "gabapentin", "sertraline", "tramadol",
    "acetaminophen", "paracetamol", "ciprofloxacin", "prednisone", "cetirizine",
    "montelukast", "pantoprazole", "ranitidine", "diclofenac", "naproxen",
    "clopidogrel", "warfarin", "insulin", "glimepiride", "pioglitazone",
    "rosuvastatin", "telmisartan", "enalapril", "furosemide", "spironolactone",
    "doxycycline", "cephalexin", "clindamycin", "fluconazole", "acyclovir",
    "salbutamol", "albuterol", "budesonide", "fluticasone", "prednisolone",
    "hydroxychloroquine", "esomeprazole", "rabeprazole", "domperidone",
    "ondansetron", "metoclopramide", "loperamide", "bisoprolol", "carvedilol",
    "valsartan", "ramipril", "diltiazem", "nifedipine", "ceftriaxone",
    "levofloxacin", "moxifloxacin", "clarithromycin", "erythromycin",
    "phenytoin", "carbamazepine", "valproate", "levetiracetam", "topiramate",
    "duloxetine", "venlafaxine", "escitalopram", "fluoxetine", "paroxetine",
    "alprazolam", "lorazepam", "diazepam", "clonazepam", "zolpidem",
]

class PrescriptionOCR:
    """Handle prescription image extraction"""
    
    def __init__(self):
        """Initialize OCR engine"""
        self.tesseract_available = TESSERACT_AVAILABLE
        if self.tesseract_available:
            try:
                # Test if tesseract binary is accessible
                pytesseract.get_tesseract_version()
            except Exception:
                self.tesseract_available = False
    
    def extract_from_image(self, image_path_or_bytes):
        """
        Extract prescription data from image
        Args:
            image_path_or_bytes: Path to image file or image bytes
        Returns:
            dict with extracted prescription data
        """
        try:
            # Load image
            if isinstance(image_path_or_bytes, str):
                image = Image.open(image_path_or_bytes)
            else:
                image = Image.open(BytesIO(image_path_or_bytes))
            
            # Enhance image for better OCR
            image = self._enhance_image(image)
            
            text = ""
            if self.tesseract_available:
                # Extract text using Tesseract
                text = pytesseract.image_to_string(image)
            else:
                # Fallback: try using Pillow's basic image info + pixel analysis
                text = self._fallback_text_extraction(image)
            
            # Parse prescription data
            prescription_data = self._parse_prescription_text(text)
            prescription_data["ocr_confidence"] = self._calculate_confidence(text)
            prescription_data["ocr_engine"] = "tesseract" if self.tesseract_available else "fallback"
            
            return prescription_data
        
        except Exception as e:
            return {
                "error": str(e),
                "ocr_confidence": 0,
                "requires_manual_confirmation": True
            }
    
    def _fallback_text_extraction(self, image):
        """Fallback text extraction when Tesseract is not available.
        Uses basic image analysis heuristics."""
        # Without Tesseract, we can't do real OCR
        # Return empty text so the parser can flag all fields as needing confirmation
        return ""
    
    def _enhance_image(self, image):
        """Enhance image quality for better OCR"""
        from PIL import ImageEnhance
        
        # Convert to grayscale
        image = image.convert('L')
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2)
        
        # Increase brightness if needed
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.2)
        
        return image
    
    def _parse_prescription_text(self, text):
        """Parse raw OCR text into structured prescription data"""
        prescription = {
            "medicine_name": None,
            "dosage": None,
            "dosage_unit": None,
            "frequency": None,
            "duration": None,
            "route": None,
            "raw_text": text,
            "extraction_notes": []
        }
        
        if not text or len(text.strip()) < 2:
            prescription["extraction_notes"].append("No text could be extracted from image")
            prescription["extraction_notes"].append("Medicine name unclear - please enter manually")
            prescription["extraction_notes"].append("Dosage unclear - please enter manually")
            prescription["extraction_notes"].append("Frequency unclear - please enter manually")
            prescription["requires_manual_confirmation"] = True
            return prescription
        
        # Clean text - keep newlines for line-based parsing
        original_lines = [line.strip() for line in text.split('\n') if line.strip()]
        clean_text = text.replace('\n', ' ')
        
        # === MEDICINE NAME EXTRACTION (multi-strategy) ===
        
        # Strategy 1: Match against known medicine database (highest priority)
        text_lower = clean_text.lower()
        for med in KNOWN_MEDICINES:
            if med in text_lower:
                prescription["medicine_name"] = med.capitalize()
                break
        
        # Strategy 2: Look for medicine name after common labels
        if not prescription["medicine_name"]:
            label_patterns = [
                r'(?:Rx|R/|medicine|tablet|tab|cap|capsule|drug|med|name|medication)[\s.:/-]*([A-Za-z]{3,})',
                r'(?:prescribed?|take)[\s.:/-]*([A-Za-z]{3,})',
            ]
            for pattern in label_patterns:
                match = re.search(pattern, clean_text, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    # Filter out common non-medicine words
                    skip_words = {'the', 'for', 'take', 'with', 'food', 'water', 'daily', 'twice', 'once', 'oral', 'patient', 'doctor', 'date', 'name'}
                    if name.lower() not in skip_words and len(name) >= 3:
                        prescription["medicine_name"] = name.capitalize()
                        break
        
        # Strategy 3: Find capitalized words that look like medicine names
        if not prescription["medicine_name"]:
            # Look for words with capital letters that are >= 4 chars (typical medicine names)
            cap_words = re.findall(r'\b([A-Z][a-z]{3,}(?:in|ol|ne|ide|ate|ine|one|cin|lin|min|pril|tan|pine|fen|lol|vir|zole|mab|nib)\b)', clean_text)
            if cap_words:
                prescription["medicine_name"] = cap_words[0]
        
        # Strategy 4: Find any long capitalized word (likely a medicine)
        if not prescription["medicine_name"]:
            cap_words = re.findall(r'\b([A-Z][a-zA-Z]{4,})\b', clean_text)
            skip_words = {'Patient', 'Doctor', 'Hospital', 'Clinic', 'Medical', 'Prescription', 'Pharmacy', 
                         'Address', 'Phone', 'Email', 'Date', 'Signature', 'Name', 'License', 'Number'}
            for word in cap_words:
                if word not in skip_words:
                    prescription["medicine_name"] = word
                    break
        
        # === DOSAGE EXTRACTION ===
        dosage_match = re.search(
            r'(\d+(?:\.\d+)?)\s*(mg|ml|g|microgram|mcg|%|unit|IU|mcg)',
            clean_text,
            re.IGNORECASE
        )
        if dosage_match:
            prescription["dosage"] = dosage_match.group(1)
            prescription["dosage_unit"] = dosage_match.group(2).lower()
        
        # === FREQUENCY EXTRACTION ===
        frequency_patterns = [
            (r'once\s+(?:a\s+)?day', 'Once daily'),
            (r'twice\s+(?:a\s+)?day', 'Twice daily'),
            (r'three\s+times\s+(?:a\s+)?day', 'Three times daily'),
            (r'(?:1|one)\s*x\s*(?:a\s+)?day', 'Once daily'),
            (r'(?:2|two)\s*x\s*(?:a\s+)?day', 'Twice daily'),
            (r'(?:3|three)\s*x\s*(?:a\s+)?day', 'Three times daily'),
            (r'every\s+(\d+)\s+hours?', 'Every \\1 hours'),
            (r'morning\s+and\s+evening', 'Twice daily'),
            (r'morning\s+and\s+night', 'Twice daily'),
            (r'at\s+bedtime', 'At bedtime'),
            (r'(\d+)\s+times\s+(?:a\s+)?day', '\\1 times daily'),
            (r'(?:bd|bid|b\.d\.)', 'Twice daily'),
            (r'(?:tds|tid|t\.d\.s\.)', 'Three times daily'),
            (r'(?:od|o\.d\.)', 'Once daily'),
            (r'(?:qid|q\.i\.d\.)', 'Every 6 hours'),
            (r'(?:qhs|h\.s\.)', 'At bedtime'),
            (r'(?:prn|p\.r\.n\.)', 'As needed'),
        ]
        
        for pattern, replacement in frequency_patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                freq = replacement
                # Handle backreferences
                if '\\1' in freq and match.groups():
                    freq = freq.replace('\\1', match.group(1))
                prescription["frequency"] = freq
                break
        
        # === DURATION EXTRACTION ===
        duration_match = re.search(
            r'(?:for|x|duration)?\s*(\d+)\s+(?:days?|weeks?|months?)',
            clean_text,
            re.IGNORECASE
        )
        if duration_match:
            days = int(duration_match.group(1))
            if 'week' in duration_match.group(0).lower():
                days *= 7
            elif 'month' in duration_match.group(0).lower():
                days *= 30
            prescription["duration"] = days
        
        # === ROUTE EXTRACTION ===
        route_match = re.search(
            r'\b(oral|tablet|tab|capsule|cap|injection|inj|intravenous|IV|topical|cream|ointment|drops|syrup|inhaler|patch|sublingual)\b',
            clean_text,
            re.IGNORECASE
        )
        if route_match:
            route_map = {'tab': 'tablet', 'cap': 'capsule', 'inj': 'injection'}
            route = route_match.group(1).lower()
            prescription["route"] = route_map.get(route, route)
        
        # === EXTRACTION NOTES ===
        if not prescription["medicine_name"]:
            prescription["extraction_notes"].append("Medicine name unclear - please confirm")
        if not prescription["dosage"]:
            prescription["extraction_notes"].append("Dosage unclear - please confirm")
        if not prescription["frequency"]:
            prescription["extraction_notes"].append("Frequency unclear - please confirm")
            prescription["frequency"] = "Once daily"  # Default
        if not prescription["duration"]:
            prescription["extraction_notes"].append("Duration not found - defaulting to 30 days")
            prescription["duration"] = 30
        
        prescription["requires_manual_confirmation"] = len(prescription["extraction_notes"]) > 0
        
        return prescription
    
    def _calculate_confidence(self, text):
        """Calculate OCR confidence score"""
        # Simple confidence calculation based on text length and structure
        if not text or len(text) < 10:
            return 0.3
        
        # Check for common prescription keywords
        keywords = [
            'medicine', 'tablet', 'take', 'daily', 'mg', 'ml',
            'frequency', 'dose', 'morning', 'evening', 'twice'
        ]
        
        text_lower = text.lower()
        keyword_count = sum(1 for kw in keywords if kw in text_lower)
        
        confidence = min(0.9, 0.5 + (keyword_count * 0.05))
        return round(confidence, 2)

def validate_prescription_input(prescription_data):
    """
    Validate manually entered prescription data
    Returns list of errors if any
    """
    errors = []
    
    if not prescription_data.get("medicine_name"):
        errors.append("Medicine name is required")
    
    if not prescription_data.get("dosage"):
        errors.append("Dosage is required")
    
    if not prescription_data.get("frequency"):
        errors.append("Frequency is required")
    
    # Validate dosage format
    if prescription_data.get("dosage"):
        try:
            float(prescription_data["dosage"])
        except ValueError:
            errors.append("Dosage must be a number")
    
    # Validate duration if provided
    if prescription_data.get("duration"):
        try:
            int(prescription_data["duration"])
        except ValueError:
            errors.append("Duration must be a number of days")
    
    return errors
