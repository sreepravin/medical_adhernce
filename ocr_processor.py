"""
OCR and Prescription Image Processing
Uses Google Gemini AI (primary) with Tesseract OCR (fallback)
"""

import os
import re
import json
import time
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
    
    def _ensure_gemini(self):
        """Lazy-initialize Gemini if not already done but API key is available."""
        if self.gemini_available and self.gemini_client:
            return True
        api_key = os.environ.get('GEMINI_API_KEY', '')
        if GEMINI_AVAILABLE and api_key:
            try:
                self.gemini_client = genai.Client(api_key=api_key)
                self.gemini_available = True
                print("[OCR] ✓ Gemini AI (re)initialized successfully")
                return True
            except Exception as e:
                print(f"[OCR] ⚠ Gemini lazy-init failed: {e}")
        return False

    def _resize_image(self, image, max_dimension=1024):
        """Resize image to prevent OOM on free-tier hosting (512MB RAM)."""
        w, h = image.size
        if max(w, h) > max_dimension:
            ratio = max_dimension / max(w, h)
            new_size = (int(w * ratio), int(h * ratio))
            image = image.resize(new_size, Image.LANCZOS)
            print(f"[OCR] Resized image from {w}x{h} to {new_size[0]}x{new_size[1]}")
        # Convert RGBA to RGB if needed (JPEG compat)
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        return image

    def extract_from_image(self, image_path_or_bytes):
        """Extract ALL prescription data from image using Gemini AI (primary) or Tesseract (fallback).
        Returns a list of prescription dicts (one per medicine found)."""
        try:
            # Load image
            if isinstance(image_path_or_bytes, str):
                image = Image.open(image_path_or_bytes)
            elif isinstance(image_path_or_bytes, bytes):
                image = Image.open(BytesIO(image_path_or_bytes))
            else:
                image = Image.open(BytesIO(image_path_or_bytes))
            
            # Free raw bytes immediately to save memory
            image_path_or_bytes = None
            
            # Resize large images to prevent OOM on deployment
            image = self._resize_image(image)
            
            print(f"[OCR] Input image: size={image.size}, mode={image.mode}")
            
            # === PRIMARY: Try Gemini AI ===
            self._ensure_gemini()  # Re-check in case key was set after startup
            gemini_error = None
            if self.gemini_available:
                print("[OCR] Using Gemini AI for prescription analysis...")
                try:
                    results = self._extract_with_gemini(image)
                except Exception as gemini_err:
                    print(f"[OCR] Gemini exception: {gemini_err}")
                    gemini_error = str(gemini_err)
                    results = None
                
                if results and isinstance(results, list) and len(results) > 0:
                    for r in results:
                        r["ocr_engine"] = "gemini-ai"
                    names = [r.get('medicine_name', '?') for r in results]
                    print(f"[OCR] ✓ Gemini extracted {len(results)} medicine(s): {', '.join(names)}")
                    return results
                elif results and isinstance(results, dict) and results.get("medicine_name"):
                    # Legacy single-dict fallback
                    results["ocr_engine"] = "gemini-ai"
                    print(f"[OCR] ✓ Gemini extracted medicine: {results.get('medicine_name')}")
                    return [results]
                else:
                    gemini_error = gemini_error or "Could not read medicines from this image"
                    print(f"[OCR] Gemini returned no medicines: {gemini_error}")
            else:
                print(f"[OCR] Gemini not available (gemini_available={self.gemini_available})")
            
            # === FALLBACK: Tesseract OCR ===
            if self.tesseract_available:
                tesseract_results = self._extract_with_tesseract(image)
                return tesseract_results  # Already a list
            
            # Determine the real error message
            if self.gemini_available and gemini_error:
                # Gemini was configured but the API call failed
                err_msg = f"AI analysis failed: {gemini_error}. Please try again or fill the form manually."
                if '429' in gemini_error or 'RESOURCE_EXHAUSTED' in gemini_error or 'rate' in gemini_error.lower():
                    err_msg = "Gemini AI is rate-limited. Please wait a minute and try again, or fill the form manually."
            elif not self.gemini_available:
                err_msg = "No OCR engine available. Please set GEMINI_API_KEY in environment variables, or fill the form manually."
            else:
                err_msg = "Could not extract medicines from this image. Please try a clearer photo or fill the form manually."
            
            print(f"[OCR] ⚠ {err_msg}")
            return [{
                "error": err_msg,
                "ocr_confidence": 0,
                "requires_manual_confirmation": True
            }]
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return [{
                "error": str(e),
                "ocr_confidence": 0,
                "requires_manual_confirmation": True
            }]
    
    # ================================================================
    # GEMINI AI EXTRACTION
    # ================================================================
    def _extract_with_gemini(self, image):
        """Use Google Gemini AI to analyze prescription image and extract ALL medicines as a list"""
        try:
            prompt = """Analyze this prescription/medicine image carefully. Extract ALL medicines/drugs found in the image.

Return ONLY a valid JSON array (no markdown, no code blocks, no extra text). Each element is an object for one medicine:

[
  {
    "medicine_name": "exact medicine/drug name",
    "dosage": "numeric dosage value (e.g. 500)",
    "dosage_unit": "unit like mg, ml, g, mcg",
    "frequency": "how often to take (e.g. Once daily, Twice daily, Three times daily)",
    "duration": "number of days as integer",
    "route": "how to take it (e.g. oral, tablet, capsule, injection, syrup, cream)",
    "instructions": "any special instructions for THIS medicine",
    "raw_text": "all readable text from the image (include in first element only)"
  }
]

Rules:
- Extract EVERY medicine/drug listed in the prescription. Do NOT skip any.
- medicine_name is the MOST IMPORTANT field for each entry.
- If you see brand names, include them. If you see generic names, include those.
- For dosage, only include the number (e.g. "500" not "500mg").
- For duration, convert to days (e.g. "1 week" = 7, "1 month" = 30).
- If you cannot determine a field, use null.
- Even if there is only ONE medicine, return it as an array with one element.
- Return ONLY the JSON array, nothing else."""

            # Retry up to 2 times on rate limit (429) errors
            response_text = None
            for attempt in range(2):
                try:
                    response = self.gemini_client.models.generate_content(
                        model='gemini-2.0-flash',
                        contents=[prompt, image]
                    )
                    response_text = response.text.strip()
                    break  # Success
                except Exception as retry_err:
                    err_str = str(retry_err)
                    if '429' in err_str or 'RESOURCE_EXHAUSTED' in err_str:
                        wait = 3  # Fixed short wait
                        print(f"[OCR] Gemini rate limited (attempt {attempt+1}/2), retrying in {wait}s...")
                        time.sleep(wait)
                    else:
                        raise retry_err  # Non-rate-limit error, don't retry
            
            # Free image from memory after Gemini call
            image = None
            
            if response_text is None:
                print("[OCR] Gemini failed after 2 retries (rate limited)")
                return None
            
            print(f"[OCR] Gemini raw response: {response_text[:800]}")
            
            # Clean response - remove markdown code blocks if present
            response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
            response_text = response_text.strip()
            
            # Parse JSON
            data = json.loads(response_text)
            
            # Handle both array and single-object responses
            if isinstance(data, dict):
                data = [data]  # Wrap single object in array
            
            if not isinstance(data, list) or len(data) == 0:
                return None
            
            prescriptions = []
            for i, med in enumerate(data):
                prescription = {
                    "medicine_name": med.get("medicine_name"),
                    "dosage": str(med["dosage"]) if med.get("dosage") else None,
                    "dosage_unit": med.get("dosage_unit", "mg"),
                    "frequency": med.get("frequency", "Once daily"),
                    "duration": int(med["duration"]) if med.get("duration") else 30,
                    "route": med.get("route", "oral"),
                    "raw_text": med.get("raw_text", "") if i == 0 else "",
                    "extraction_notes": [],
                    "instructions": med.get("instructions"),
                    "special_instructions": med.get("special_instructions"),
                    "ocr_confidence": 0.9 if med.get("medicine_name") else 0.3,
                    "requires_manual_confirmation": not bool(med.get("medicine_name")),
                }
                
                if not prescription["medicine_name"]:
                    prescription["extraction_notes"].append("AI could not identify medicine name - please enter manually")
                if not prescription["dosage"]:
                    prescription["extraction_notes"].append("Dosage unclear - please confirm")
                if prescription["extraction_notes"]:
                    prescription["requires_manual_confirmation"] = True
                
                prescriptions.append(prescription)
            
            # Filter out entries with no medicine name (noise)
            valid = [p for p in prescriptions if p.get("medicine_name")]
            return valid if valid else prescriptions[:1]  # Return at least one entry
            
        except json.JSONDecodeError as e:
            print(f"[OCR] Gemini JSON parse error: {e}")
            result = self._parse_gemini_text_fallback(response_text)
            return [result] if result else None
        except Exception as e:
            print(f"[OCR] Gemini error: {e}")
            raise  # Re-raise so caller gets the actual error message
    
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
        """Use Tesseract OCR + regex parsing as fallback. Returns a LIST of prescription dicts."""
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
        
        # Extract ALL medicines from the text
        medicines = self._extract_all_medicines_from_text(text)
        confidence = self._calculate_confidence(text)
        engine = "tesseract" if self.tesseract_available else "fallback"
        for m in medicines:
            m["ocr_confidence"] = confidence
            m["ocr_engine"] = engine
        
        print(f"[OCR] Tesseract found {len(medicines)} medicine(s): {[m.get('medicine_name','?') for m in medicines]}")
        return medicines
    
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
    
    def _find_all_medicine_names(self, text):
        """Find ALL medicine names in OCR text using multiple strategies.
        Returns a list of (medicine_name, position_in_text) tuples."""
        if not text or len(text.strip()) < 2:
            return []
        
        text_lower = text.lower()
        text_cleaned = re.sub(r'[|{}\[\]~`]', '', text_lower)
        text_no_spaces = text_cleaned.replace(' ', '')
        found = []  # list of (name, position)
        found_lower = set()  # track what we've already found
        
        # Strategy 1: Exact match against known medicine database
        for med in KNOWN_MEDICINES:
            pos = text_cleaned.find(med)
            if pos >= 0 and med not in found_lower:
                found.append((med.capitalize(), pos))
                found_lower.add(med)
        
        # Strategy 2: No-spaces match (OCR often splits words like "Met formin")
        for med in KNOWN_MEDICINES:
            if med in found_lower:
                continue
            pos = text_no_spaces.find(med)
            if pos >= 0:
                found.append((med.capitalize(), pos))
                found_lower.add(med)
        
        # Strategy 3: Fuzzy match words and word-pairs against known medicines
        words = re.findall(r'[a-zA-Z]{2,}', text_cleaned)
        candidates = []
        for i, w in enumerate(words):
            candidates.append((w, i))
            if i < len(words) - 1:
                candidates.append((w + words[i+1], i))
        
        for candidate, word_idx in candidates:
            for med in KNOWN_MEDICINES:
                if med in found_lower:
                    continue
                ratio = difflib.SequenceMatcher(None, candidate.lower(), med).ratio()
                if ratio >= 0.80:
                    # Approximate position from word index
                    found.append((med.capitalize(), word_idx * 10))
                    found_lower.add(med)
        
        # Strategy 4: Medicine-suffix words (e.g. ending in -in, -ol, -ide, etc.)
        med_suffix_re = r'\b([A-Za-z]{3,}(?:in|ol|ne|ide|ate|ine|one|cin|lin|min|pril|tan|pine|fen|lol|vir|zole|mab|nib|lam|pam|done|phil|mide|oxin|tide|arin|ulin|zide|sone))\b'
        skip_words_lower = {'medicine', 'online', 'routine', 'determine', 'combine', 'examine',
                            'define', 'decline', 'information', 'prescription', 'substitution',
                            'permission', 'written'}
        for m in re.finditer(med_suffix_re, text, re.IGNORECASE):
            word = m.group(1)
            if word.lower() in skip_words_lower or word.lower() in found_lower or len(word) < 4:
                continue
            close = difflib.get_close_matches(word.lower(), KNOWN_MEDICINES, n=1, cutoff=0.6)
            name = close[0].capitalize() if close else word.capitalize()
            if name.lower() not in found_lower:
                found.append((name, m.start()))
                found_lower.add(name.lower())
        
        # Sort by position in text to maintain order
        found.sort(key=lambda x: x[1])
        return found
    
    def _extract_context_near(self, text, medicine_name, window=200):
        """Extract text near a medicine name for parsing dosage/frequency/etc."""
        text_lower = text.lower()
        med_lower = medicine_name.lower()
        pos = text_lower.find(med_lower)
        if pos < 0:
            # Try without spaces
            pos = text_lower.replace(' ', '').find(med_lower)
            if pos < 0:
                return text  # Fallback: use full text
        start = max(0, pos - 30)  # A little before
        end = min(len(text), pos + len(medicine_name) + window)
        return text[start:end]
    
    def _parse_dosage_freq_duration(self, context_text):
        """Parse dosage, frequency, duration, and route from a text snippet."""
        result = {"dosage": None, "dosage_unit": None, "frequency": None, "duration": None, "route": None}
        
        # Dosage
        dosage_match = re.search(
            r'(\d+(?:\.\d+)?)\s*(mg|ml|g|microgram|mcg|%|unit|IU)',
            context_text, re.IGNORECASE
        )
        if dosage_match:
            result["dosage"] = dosage_match.group(1)
            result["dosage_unit"] = dosage_match.group(2).lower()
        
        # Frequency
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
            match = re.search(pattern, context_text, re.IGNORECASE)
            if match:
                freq = replacement
                if '\\1' in freq and match.groups():
                    freq = freq.replace('\\1', match.group(1))
                result["frequency"] = freq
                break
        
        # Duration
        duration_match = re.search(
            r'(?:for|x|duration)?\s*(\d+)\s+(?:days?|weeks?|months?)',
            context_text, re.IGNORECASE
        )
        if duration_match:
            days = int(duration_match.group(1))
            if 'week' in duration_match.group(0).lower():
                days *= 7
            elif 'month' in duration_match.group(0).lower():
                days *= 30
            result["duration"] = days
        
        # Route
        route_match = re.search(
            r'\b(oral|tablet|tab|capsule|cap|injection|inj|intravenous|IV|topical|cream|ointment|drops|syrup|inhaler|patch|sublingual)\b',
            context_text, re.IGNORECASE
        )
        if route_match:
            route_map = {'tab': 'tablet', 'cap': 'capsule', 'inj': 'injection'}
            route = route_match.group(1).lower()
            result["route"] = route_map.get(route, route)
        
        return result
    
    def _extract_all_medicines_from_text(self, text):
        """Extract ALL medicines from OCR text, returning a list of prescription dicts."""
        if not text or len(text.strip()) < 2:
            return [{
                "medicine_name": None,
                "dosage": None,
                "dosage_unit": None,
                "frequency": None,
                "duration": 30,
                "route": None,
                "raw_text": text or "",
                "extraction_notes": ["No text could be extracted from image"],
                "requires_manual_confirmation": True,
            }]
        
        # Find all medicine names
        medicine_hits = self._find_all_medicine_names(text)
        print(f"[OCR] Found medicine candidates: {[m[0] for m in medicine_hits]}")
        
        if not medicine_hits:
            # No medicines found at all — return single empty entry
            return [{
                "medicine_name": None,
                "dosage": None,
                "dosage_unit": None,
                "frequency": None,
                "duration": 30,
                "route": None,
                "raw_text": text,
                "extraction_notes": ["No medicine names detected — please enter manually"],
                "requires_manual_confirmation": True,
            }]
        
        results = []
        for i, (med_name, _pos) in enumerate(medicine_hits):
            # Get text context near this medicine for parsing details
            context = self._extract_context_near(text, med_name)
            details = self._parse_dosage_freq_duration(context)
            
            notes = []
            if not details["dosage"]:
                notes.append("Dosage unclear - please confirm")
            if not details["frequency"]:
                notes.append("Frequency unclear - please confirm")
                details["frequency"] = "Once daily"
            if not details["duration"]:
                notes.append("Duration not found - defaulting to 30 days")
                details["duration"] = 30
            
            prescription = {
                "medicine_name": med_name,
                "dosage": details["dosage"],
                "dosage_unit": details.get("dosage_unit"),
                "frequency": details["frequency"],
                "duration": details["duration"],
                "route": details.get("route"),
                "raw_text": text if i == 0 else "",
                "extraction_notes": notes,
                "requires_manual_confirmation": len(notes) > 0,
            }
            results.append(prescription)
        
        return results
    
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
