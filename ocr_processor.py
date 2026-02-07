"""
OCR and Prescription Image Processing
Uses Google Gemini AI (primary) with Tesseract OCR (fallback)
"""

import os
import re
import json
import base64
import difflib
from io import BytesIO

try:
    import pytesseract
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

# Google Gemini AI (new google-genai package)
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    try:
        import google.generativeai as genai_legacy
        GEMINI_AVAILABLE = True
    except ImportError:
        GEMINI_AVAILABLE = False

from PIL import Image, ImageFilter
from dotenv import load_dotenv
load_dotenv()

# Common medicine names for matching against OCR text (extensive list)
KNOWN_MEDICINES = [
    # Analgesics / Anti-inflammatory
    "aspirin", "ibuprofen", "acetaminophen", "paracetamol", "naproxen", "diclofenac",
    "tramadol", "morphine", "codeine", "celecoxib", "meloxicam", "piroxicam",
    "indomethacin", "ketorolac", "mefenamic",
    # Diabetes
    "metformin", "glimepiride", "pioglitazone", "glipizide", "glyburide", "insulin",
    "sitagliptin", "empagliflozin", "dapagliflozin", "canagliflozin", "liraglutide",
    "semaglutide", "vildagliptin", "saxagliptin", "linagliptin",
    # Antibiotics
    "amoxicillin", "azithromycin", "ciprofloxacin", "doxycycline", "cephalexin",
    "clindamycin", "ceftriaxone", "levofloxacin", "moxifloxacin", "clarithromycin",
    "erythromycin", "metronidazole", "nitrofurantoin", "trimethoprim", "sulfamethoxazole",
    "penicillin", "ampicillin", "cefixime", "cefuroxime", "cefpodoxime", "ofloxacin",
    "norfloxacin", "gentamicin", "vancomycin", "linezolid", "rifampicin", "isoniazid",
    # Cardiovascular
    "lisinopril", "atorvastatin", "amlodipine", "metoprolol", "losartan", "simvastatin",
    "clopidogrel", "warfarin", "bisoprolol", "carvedilol", "valsartan", "ramipril",
    "diltiazem", "nifedipine", "telmisartan", "enalapril", "furosemide", "spironolactone",
    "hydrochlorothiazide", "rosuvastatin", "pravastatin", "propranolol", "atenolol",
    "nebivolol", "candesartan", "irbesartan", "olmesartan", "indapamide", "digoxin",
    "apixaban", "rivaroxaban", "dabigatran", "heparin", "enoxaparin", "nitroglycerin",
    # GI / Antacids
    "omeprazole", "pantoprazole", "esomeprazole", "rabeprazole", "lansoprazole",
    "ranitidine", "famotidine", "domperidone", "ondansetron", "metoclopramide",
    "loperamide", "sucralfate", "mesalamine", "lactulose",
    # Respiratory
    "salbutamol", "albuterol", "budesonide", "fluticasone", "montelukast",
    "cetirizine", "loratadine", "fexofenadine", "levocetirizine", "desloratadine",
    "diphenhydramine", "chlorpheniramine", "theophylline", "ipratropium", "tiotropium",
    "dextromethorphan", "guaifenesin", "ambroxol", "bromhexine",
    # Thyroid
    "levothyroxine", "methimazole", "propylthiouracil",
    # Neurological / Psychiatric
    "gabapentin", "sertraline", "phenytoin", "carbamazepine", "valproate", "levetiracetam",
    "topiramate", "duloxetine", "venlafaxine", "escitalopram", "fluoxetine", "paroxetine",
    "alprazolam", "lorazepam", "diazepam", "clonazepam", "zolpidem", "pregabalin",
    "amitriptyline", "nortriptyline", "citalopram", "mirtazapine", "bupropion",
    "quetiapine", "olanzapine", "risperidone", "aripiprazole", "haloperidol",
    "lithium", "lamotrigine", "oxcarbazepine", "donepezil", "memantine",
    # Steroids
    "prednisone", "prednisolone", "dexamethasone", "methylprednisolone", "hydrocortisone",
    "betamethasone", "triamcinolone", "fludrocortisone",
    # Antifungal / Antiviral
    "fluconazole", "acyclovir", "valacyclovir", "oseltamivir", "itraconazole",
    "ketoconazole", "clotrimazole", "terbinafine", "nystatin",
    # Other common
    "hydroxychloroquine", "colchicine", "allopurinol", "febuxostat", "methotrexate",
    "cyclosporine", "tacrolimus", "azathioprine", "mycophenolate",
    "sildenafil", "tadalafil", "tamsulosin", "finasteride", "dutasteride",
    "oxybutynin", "tolterodine", "desmopressin",
    "ferrous", "folic", "calcium", "vitamin", "multivitamin",
    "melatonin", "biotin", "zinc", "magnesium",
]

class PrescriptionOCR:
    """Handle prescription image extraction using AI (Gemini) + Tesseract fallback"""
    
    def __init__(self):
        """Initialize OCR engine"""
        self.tesseract_available = TESSERACT_AVAILABLE
        if self.tesseract_available:
            try:
                pytesseract.get_tesseract_version()
            except Exception:
                self.tesseract_available = False
        
        # Initialize Gemini
        self.gemini_available = False
        self.gemini_client = None
        api_key = os.environ.get('GEMINI_API_KEY', '')
        if GEMINI_AVAILABLE and api_key:
            try:
                self.gemini_client = genai.Client(api_key=api_key)
                self.gemini_available = True
                print("[OCR] ✓ Gemini AI initialized successfully")
            except Exception as e:
                print(f"[OCR] ⚠ Gemini init failed: {e}")
        else:
            if not GEMINI_AVAILABLE:
                print("[OCR] ⚠ google-genai package not installed")
            if not api_key:
                print("[OCR] ⚠ GEMINI_API_KEY not set in environment")
    
    def extract_from_image(self, image_path_or_bytes):
        """Extract prescription data from image using Gemini AI (primary) or Tesseract (fallback)"""
        try:
            # Load image
            if isinstance(image_path_or_bytes, str):
                image = Image.open(image_path_or_bytes)
                with open(image_path_or_bytes, 'rb') as f:
                    image_bytes = f.read()
            elif isinstance(image_path_or_bytes, bytes):
                image = Image.open(BytesIO(image_path_or_bytes))
                image_bytes = image_path_or_bytes
            else:
                image = Image.open(BytesIO(image_path_or_bytes))
                image_bytes = image_path_or_bytes
            
            print(f"[OCR] Input image: size={image.size}, mode={image.mode}")
            
            # === PRIMARY: Try Gemini AI ===
            if self.gemini_available:
                print("[OCR] Using Gemini AI for prescription analysis...")
                result = self._extract_with_gemini(image)
                if result and result.get("medicine_name"):
                    result["ocr_engine"] = "gemini-ai"
                    print(f"[OCR] ✓ Gemini extracted medicine: {result.get('medicine_name')}")
                    return result
                else:
                    print("[OCR] Gemini couldn't extract medicine, falling back to Tesseract...")
            
            # === FALLBACK: Tesseract OCR ===
            return self._extract_with_tesseract(image)
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "error": str(e),
                "ocr_confidence": 0,
                "requires_manual_confirmation": True
            }
    
    # ================================================================
    # GEMINI AI EXTRACTION
    # ================================================================
    def _extract_with_gemini(self, image):
        """Use Google Gemini AI to analyze prescription image and extract structured data"""
        try:
            prompt = """Analyze this prescription/medicine image carefully. Extract the following information and return ONLY a valid JSON object (no markdown, no code blocks, no extra text):

{
  "medicine_name": "exact medicine/drug name found in the image",
  "dosage": "numeric dosage value (e.g. 500)",
  "dosage_unit": "unit like mg, ml, g, mcg",
  "frequency": "how often to take (e.g. Once daily, Twice daily, Three times daily)",
  "duration": "number of days as integer",
  "route": "how to take it (e.g. oral, tablet, capsule, injection, syrup, cream)",
  "instructions": "any special instructions like take after food, avoid alcohol etc",
  "raw_text": "all readable text from the image"
}

Rules:
- medicine_name is the MOST IMPORTANT field. Look for drug/medicine names carefully.
- If you see brand names, include them. If you see generic names, include those.
- If multiple medicines are listed, use the first/primary one.
- For dosage, only include the number (e.g. "500" not "500mg").
- For duration, convert to days (e.g. "1 week" = 7, "1 month" = 30).
- If you cannot determine a field, use null.
- Return ONLY the JSON object, nothing else."""

            response = self.gemini_client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[prompt, image]
            )
            response_text = response.text.strip()
            print(f"[OCR] Gemini raw response: {response_text[:500]}")
            
            # Clean response - remove markdown code blocks if present
            response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
            response_text = response_text.strip()
            
            # Parse JSON
            data = json.loads(response_text)
            
            # Build standard prescription dict
            prescription = {
                "medicine_name": data.get("medicine_name"),
                "dosage": str(data["dosage"]) if data.get("dosage") else None,
                "dosage_unit": data.get("dosage_unit", "mg"),
                "frequency": data.get("frequency", "Once daily"),
                "duration": int(data["duration"]) if data.get("duration") else 30,
                "route": data.get("route", "oral"),
                "raw_text": data.get("raw_text", ""),
                "extraction_notes": [],
                "instructions": data.get("instructions"),
                "ocr_confidence": 0.9 if data.get("medicine_name") else 0.3,
                "requires_manual_confirmation": not bool(data.get("medicine_name")),
            }
            
            if not prescription["medicine_name"]:
                prescription["extraction_notes"].append("AI could not identify medicine name - please enter manually")
            if not prescription["dosage"]:
                prescription["extraction_notes"].append("Dosage unclear - please confirm")
            if prescription["extraction_notes"]:
                prescription["requires_manual_confirmation"] = True
            
            return prescription
            
        except json.JSONDecodeError as e:
            print(f"[OCR] Gemini JSON parse error: {e}")
            # Try to extract medicine name from raw text response
            return self._parse_gemini_text_fallback(response_text)
        except Exception as e:
            print(f"[OCR] Gemini error: {e}")
            return None
    
    def _parse_gemini_text_fallback(self, text):
        """If Gemini returns non-JSON text, try to extract medicine name from it"""
        if not text:
            return None
        
        # Look for medicine_name in the text
        med_match = re.search(r'medicine[_ ]?name["\s:]*["\']?([A-Za-z][A-Za-z\s]*?)["\'}\s,]', text, re.IGNORECASE)
        if med_match:
            name = med_match.group(1).strip()
            if name.lower() != 'null' and len(name) >= 3:
                return {
                    "medicine_name": name,
                    "dosage": None,
                    "dosage_unit": "mg",
                    "frequency": "Once daily",
                    "duration": 30,
                    "route": "oral",
                    "raw_text": text,
                    "extraction_notes": ["AI response was partially parsed - please review all fields"],
                    "ocr_confidence": 0.6,
                    "requires_manual_confirmation": True,
                }
        return None
    
    # ================================================================
    # TESSERACT OCR EXTRACTION (Fallback)
    # ================================================================
    def _extract_with_tesseract(self, image):
        """Use Tesseract OCR + regex parsing as fallback"""
        text = ""
        if self.tesseract_available:
            variants = self._get_image_variants(image)
            configs = [
                '--psm 6 --oem 3',
                '--psm 4 --oem 3',
                '--psm 3 --oem 3',
            ]
            best_text = ""
            best_score = -1
            best_label = ""
            for label, img_variant in variants:
                for cfg in configs:
                    try:
                        t = pytesseract.image_to_string(img_variant, config=cfg)
                        score = self._text_quality_score(t)
                        if score > best_score:
                            best_score = score
                            best_text = t
                            best_label = f"{label}+{cfg}"
                    except Exception:
                        continue
            text = best_text if best_text else ""
            print(f"[OCR] Tesseract best variant: {best_label} (score={best_score})")
            print(f"[OCR] Raw text ({len(text)} chars): {repr(text[:300])}")
        
        prescription_data = self._parse_prescription_text(text)
        prescription_data["ocr_confidence"] = self._calculate_confidence(text)
        prescription_data["ocr_engine"] = "tesseract" if self.tesseract_available else "fallback"
        return prescription_data
    
    # ================================================================
    # HELPER METHODS
    # ================================================================
    def _text_quality_score(self, text):
        """Score OCR text quality — prefer text with more medicine-related keywords."""
        if not text:
            return 0
        text_lower = text.lower()
        score = len(text.strip())
        keywords = ['mg', 'ml', 'tablet', 'tab', 'capsule', 'cap', 'daily', 'twice',
                    'once', 'oral', 'take', 'dose', 'rx', 'morning', 'evening', 'night',
                    'days', 'weeks', 'after', 'before', 'food', 'medicine', 'prescription']
        for kw in keywords:
            if kw in text_lower:
                score += 50
        for med in KNOWN_MEDICINES:
            if med in text_lower:
                score += 200
        return score

    def _get_image_variants(self, image):
        """Generate multiple preprocessed variants of the image for OCR.
        Different images respond better to different preprocessing.
        Returns list of (label, image) tuples."""
        from PIL import ImageEnhance, ImageOps
        
        variants = []
        
        # Convert to RGB first if necessary (handles RGBA, palette, etc.)
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        
        # Upscale small images — Tesseract works best at 300+ DPI
        width, height = image.size
        if width < 1500 or height < 1500:
            scale = max(1500 / width, 1500 / height, 2.0)
            scale = min(scale, 4.0)  # Don't upscale more than 4x
            new_size = (int(width * scale), int(height * scale))
            image = image.resize(new_size, Image.LANCZOS)
        
        # === Variant 1: Grayscale with moderate contrast (gentle) ===
        gray = image.convert('L')
        enhanced = ImageEnhance.Contrast(gray).enhance(1.5)
        enhanced = ImageEnhance.Sharpness(enhanced).enhance(2.0)
        variants.append(('gentle', enhanced))
        
        # === Variant 2: High-contrast grayscale with autocontrast ===
        gray2 = image.convert('L')
        gray2 = ImageOps.autocontrast(gray2, cutoff=1)
        gray2 = ImageEnhance.Contrast(gray2).enhance(2.0)
        gray2 = ImageEnhance.Sharpness(gray2).enhance(2.0)
        variants.append(('high_contrast', gray2))
        
        # === Variant 3: Adaptive binarization (for clean printed text) ===
        gray3 = image.convert('L')
        gray3 = ImageOps.autocontrast(gray3, cutoff=2)
        gray3 = ImageEnhance.Contrast(gray3).enhance(2.5)
        # Use Otsu-style: compute mean pixel and use as threshold
        import statistics
        pixels = list(gray3.getdata())
        try:
            mean_val = statistics.mean(pixels)
        except Exception:
            mean_val = 128
        threshold = int(mean_val * 0.85)  # Slightly below mean for dark text on light bg
        gray3 = gray3.point(lambda x: 255 if x > threshold else 0, '1')
        gray3 = gray3.convert('L')
        gray3 = gray3.filter(ImageFilter.MedianFilter(size=3))
        variants.append(('binarized', gray3))
        
        # === Variant 4: Inverted (for light text on dark background) ===
        gray4 = image.convert('L')
        gray4 = ImageOps.autocontrast(gray4, cutoff=2)
        # Check if image is mostly dark (inverted prescription)
        avg_pixel = statistics.mean(list(gray4.getdata()))
        if avg_pixel < 128:  # Mostly dark — invert it
            gray4 = ImageOps.invert(gray4)
            gray4 = ImageEnhance.Contrast(gray4).enhance(2.0)
            variants.append(('inverted', gray4))
        
        # === Variant 5: Aggressive sharpen + denoise ===
        gray5 = image.convert('L')
        gray5 = gray5.filter(ImageFilter.SHARPEN)
        gray5 = gray5.filter(ImageFilter.SHARPEN)
        gray5 = ImageEnhance.Contrast(gray5).enhance(2.0)
        gray5 = ImageEnhance.Brightness(gray5).enhance(1.1)
        gray5 = ImageOps.autocontrast(gray5, cutoff=3)
        variants.append(('sharp', gray5))
        
        return variants
    
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
        
        text_lower = clean_text.lower()
        # Remove common OCR noise characters
        text_cleaned = re.sub(r'[|{}\[\]~`]', '', text_lower)
        
        # Strategy 1: Exact match against known medicine database
        for med in KNOWN_MEDICINES:
            if med in text_cleaned:
                prescription["medicine_name"] = med.capitalize()
                break
        
        # Strategy 2: Fuzzy match against known medicines
        # OCR often introduces spaces/typos, e.g. "Amox icillin" or "Parace tamol"
        if not prescription["medicine_name"]:
            # First try: remove all spaces and match
            text_no_spaces = text_cleaned.replace(' ', '')
            for med in KNOWN_MEDICINES:
                if med in text_no_spaces:
                    prescription["medicine_name"] = med.capitalize()
                    break
        
        if not prescription["medicine_name"]:
            # Second try: fuzzy match each word and word-pairs against known medicines
            words = re.findall(r'[a-zA-Z]{2,}', text_cleaned)
            best_match = None
            best_ratio = 0.0
            # Check individual words and adjacent word-pairs
            candidates = list(words)
            for i in range(len(words) - 1):
                candidates.append(words[i] + words[i + 1])  # join adjacent words
            for candidate in candidates:
                for med in KNOWN_MEDICINES:
                    ratio = difflib.SequenceMatcher(None, candidate.lower(), med).ratio()
                    if ratio > best_ratio and ratio >= 0.75:  # 75% similarity threshold
                        best_ratio = ratio
                        best_match = med
            if best_match:
                prescription["medicine_name"] = best_match.capitalize()
                prescription["extraction_notes"].append(
                    f"Medicine name matched via fuzzy matching ({int(best_ratio*100)}% confidence)"
                )
        
        # Strategy 3: Look for medicine name after common labels
        if not prescription["medicine_name"]:
            label_patterns = [
                r'(?:Rx|R[/x]|medicine|tablet|tab|cap|capsule|drug|med|name|medication)[\s.:=/-]*([A-Za-z]{3,}(?:\s?[A-Za-z]+)?)',
                r'(?:prescribed?|take|Sig)[\s.:=/-]*([A-Za-z]{3,})',
                r'(?:Drug\s*Name|Med\s*Name|Medication)[\s.:=/-]*([A-Za-z]{3,}(?:\s?[A-Za-z]+)?)',
            ]
            for pattern in label_patterns:
                match = re.search(pattern, clean_text, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    # Filter out common non-medicine words
                    skip_words = {'the', 'for', 'take', 'with', 'food', 'water', 'daily', 'twice',
                                  'once', 'oral', 'patient', 'doctor', 'date', 'name', 'this',
                                  'that', 'your', 'from', 'have', 'been', 'will', 'should'}
                    if name.lower() not in skip_words and len(name) >= 3:
                        # Check if this label-extracted name fuzzy-matches a known medicine
                        close = difflib.get_close_matches(name.lower(), KNOWN_MEDICINES, n=1, cutoff=0.6)
                        if close:
                            prescription["medicine_name"] = close[0].capitalize()
                        else:
                            prescription["medicine_name"] = name.capitalize()
                        break
        
        # Strategy 4: Find words that look like medicine names (common suffixes)
        if not prescription["medicine_name"]:
            med_suffix_re = r'\b([A-Za-z]{3,}(?:in|ol|ne|ide|ate|ine|one|cin|lin|min|pril|tan|pine|fen|lol|vir|zole|mab|nib|lam|pam|done|phil|mide|oxin|tide|arin|ulin|zide|sone))\b'
            suffix_matches = re.findall(med_suffix_re, clean_text, re.IGNORECASE)
            skip_words_lower = {'medicine', 'online', 'routine', 'determine', 'combine', 'examine',
                                'define', 'decline', 'antine', 'antine', 'antine'}
            for word in suffix_matches:
                if word.lower() not in skip_words_lower and len(word) >= 4:
                    # Verify against known medicines with fuzzy match
                    close = difflib.get_close_matches(word.lower(), KNOWN_MEDICINES, n=1, cutoff=0.6)
                    if close:
                        prescription["medicine_name"] = close[0].capitalize()
                    else:
                        prescription["medicine_name"] = word.capitalize()
                    break
        
        # Strategy 5: Find any long capitalized word (last resort)
        if not prescription["medicine_name"]:
            cap_words = re.findall(r'\b([A-Z][a-zA-Z]{4,})\b', clean_text)
            skip_words = {'Patient', 'Doctor', 'Hospital', 'Clinic', 'Medical', 'Prescription', 'Pharmacy', 
                         'Address', 'Phone', 'Email', 'Date', 'Signature', 'Name', 'License', 'Number',
                         'India', 'Health', 'Report', 'Order', 'Department', 'Center', 'Centre',
                         'Treatment', 'Diagnosis', 'Insurance', 'Register'}
            for word in cap_words:
                if word not in skip_words:
                    # Try fuzzy matching as final attempt
                    close = difflib.get_close_matches(word.lower(), KNOWN_MEDICINES, n=1, cutoff=0.6)
                    if close:
                        prescription["medicine_name"] = close[0].capitalize()
                    else:
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
            (r'once\s+(?:a\s+)?(?:day|daily)', 'Once daily'),
            (r'twice\s+(?:a\s+)?(?:day|daily)', 'Twice daily'),
            (r'three\s+times\s+(?:a\s+)?(?:day|daily)', 'Three times daily'),
            (r'(?:1|one)\s*(?:x|time)\s*(?:a\s+)?(?:day|daily)', 'Once daily'),
            (r'(?:2|two)\s*(?:x|times?)\s*(?:a\s+)?(?:day|daily)', 'Twice daily'),
            (r'(?:3|three)\s*(?:x|times?)\s*(?:a\s+)?(?:day|daily)', 'Three times daily'),
            (r'every\s+(\d+)\s+hours?', 'Every \\1 hours'),
            (r'morning\s+(?:and|&)\s+evening', 'Twice daily'),
            (r'morning\s+(?:and|&)\s+night', 'Twice daily'),
            (r'at\s+bedtime', 'At bedtime'),
            (r'(\d+)\s+times\s+(?:a\s+)?(?:day|daily)', '\\1 times daily'),
            (r'\b(?:bd|bid|b\.?\s*d\.?)\b', 'Twice daily'),
            (r'\b(?:tds|tid|t\.?\s*d\.?\s*s\.?)\b', 'Three times daily'),
            (r'\b(?:od|o\.?\s*d\.?)\b', 'Once daily'),
            (r'\b(?:qid|q\.?\s*i\.?\s*d\.?)\b', 'Every 6 hours'),
            (r'\b(?:qhs|h\.?\s*s\.?)\b', 'At bedtime'),
            (r'\b(?:prn|p\.?\s*r\.?\s*n\.?)\b', 'As needed'),
            (r'\btwice\b', 'Twice daily'),
            (r'\bdaily\b', 'Once daily'),
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
