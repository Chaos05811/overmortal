import os
import re
import pytesseract
import cv2
from PIL import Image
from datetime import datetime
from typing import Dict, Optional, List
import json

class OvermortalOCR:
    """Improved OCR extractor for Overmortal game screenshots"""
    
    def __init__(self, image_dir: str, output_dir: str = "output"):
        self.image_dir = image_dir
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Tesseract configuration optimized for game UI
        self.tesseract_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.%:() '
    
    def preprocess_image(self, image_path: str) -> Image:
        """Preprocess image for better OCR accuracy"""
        # Read image
        img = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding for better text extraction
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
        
        # Increase contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        return Image.fromarray(enhanced)
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using OCR"""
        try:
            processed_img = self.preprocess_image(image_path)
            text = pytesseract.image_to_string(processed_img, config=self.tesseract_config)
            return text
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            return ""
    
    def extract_datetime_from_filename(self, filename: str) -> Dict[str, str]:
        """Extract date and time from screenshot filename"""
        # Pattern: Screenshot_2025-09-22-18-50-36-81_xxxxx.jpg
        name = os.path.splitext(filename)[0]
        
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})', name)
        
        if not match:
            return {'date': None, 'time': None, 'datetime': None}
        
        year, month, day, hour, minute = map(int, match.groups())
        
        try:
            dt = datetime(year, month, day, hour, minute)
            return {
                'date': dt.strftime("%B %d").lstrip("0"),
                'time': dt.strftime("%I:%M %p").lstrip("0"),
                'datetime': dt
            }
        except:
            return {'date': None, 'time': None, 'datetime': None}
    
    def parse_game_data(self, text: str) -> Dict:
        """Parse game data from OCR text"""
        data = {}
        
        # Normalize whitespace
        clean = " ".join(text.split())
        
        # Extract realm/stage (Celestial/Eternal + Early/Middle/Late)
        realm_match = re.search(
            r'(Celestial|Eternal)\s*(Early|Middle|Late)\s*(\d+\.?\d*)\s*%',
            clean,
            re.IGNORECASE
        )
        if realm_match:
            data['stage_name'] = f"{realm_match.group(1)} {realm_match.group(2)}"
            data['stage_percent'] = float(realm_match.group(3))
        
        # Alternative realm pattern
        if 'stage_name' not in data:
            realm_match2 = re.search(
                r'(Celestial|Eternal)\s*(Early|Middle|Late)',
                clean,
                re.IGNORECASE
            )
            if realm_match2:
                data['stage_name'] = f"{realm_match2.group(1)} {realm_match2.group(2)}"
                
                pct_match = re.search(r'(\d+\.?\d*)\s*%', clean)
                if pct_match:
                    data['stage_percent'] = float(pct_match.group(1))
        
        # Extract G level
        g_patterns = [
            r'(\d+)\s*G',  # 2G
            r'G\s*(\d+)',  # G2
            r'Middle\s+(\d+)\s*G',  # Middle 2G
        ]
        
        for pattern in g_patterns:
            g_match = re.search(pattern, clean, re.IGNORECASE)
            if g_match:
                data['g_level'] = int(g_match.group(1))
                break
        
        # Extract G progress percentage
        gprog_patterns = [
            r'Progress\s*:?\s*(\d+\.?\d*)\s*%',
            r'(\d+\.?\d*)\s*%.*?complete',
        ]
        
        for pattern in gprog_patterns:
            gprog_match = re.search(pattern, clean, re.IGNORECASE)
            if gprog_match:
                data['g_percent'] = float(gprog_match.group(1))
                break
        
        # Extract next breakthrough time
        next_patterns = [
            r'Next\s+Breakthrough.*?(\d+\.?\d*)\s*Year',
            r'(\d+\.?\d*)\s*Year.*?to.*?(?:G\d+|Breakthrough)',
            r'(\d+\.?\d*)\s*Yrs',
        ]
        
        for pattern in next_patterns:
            next_match = re.search(pattern, clean, re.IGNORECASE)
            if next_match:
                years = float(next_match.group(1))
                hours = int(years * 0.25)  # Game conversion: 1 year = 0.25 hours
                minutes = int(((years * 0.25) - hours) * 60)
                
                data['years_to_next'] = years
                data['hours_to_next'] = hours
                data['minutes_to_next'] = minutes
                break
        
        # Extract next G level target
        if 'g_level' in data:
            data['next_g'] = data['g_level'] + 1
        
        # Look for breakthrough indicator
        if re.search(r'breakthrough|break\s*through', clean, re.IGNORECASE):
            data['is_breakthrough'] = True
        
        return data
    
    def format_log_entry(self, filename: str, data: Dict) -> str:
        """Format data as a log entry"""
        lines = []
        
        # Extract datetime from filename
        dt_info = self.extract_datetime_from_filename(filename)
        
        # Header line
        if data.get('stage_name') and data.get('stage_percent') is not None:
            header = f"{dt_info['date']}, {dt_info['time']} - {data['stage_name']} ({data['stage_percent']}%)"
        else:
            header = f"{dt_info['date']}, {dt_info['time']} - [Stage Unknown]"
        
        lines.append(header)
        
        # G level and progress
        if data.get('g_level') and data.get('g_percent') is not None:
            lines.append(f"G{data['g_level']} at {data['g_percent']}%")
        elif data.get('g_level'):
            lines.append(f"G{data['g_level']}")
        
        # Time to next milestone
        if data.get('years_to_next') and data.get('next_g'):
            lines.append(
                f"{data['years_to_next']:.3f} Yrs or {data['hours_to_next']} Hrs "
                f"{data['minutes_to_next']} Min to G{data['next_g']}"
            )
        
        # Breakthrough indicator
        if data.get('is_breakthrough'):
            lines.append("[BREAKTHROUGH]")
        
        return "\n".join(lines)
    
    def process_directory(self) -> List[Dict]:
        """Process all images in directory"""
        results = []
        
        # Get all image files
        image_files = []
        for file in os.listdir(self.image_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_files.append(file)
        
        # Sort by filename (which should have timestamp)
        image_files.sort()
        
        print(f"Found {len(image_files)} images to process...")
        
        for idx, filename in enumerate(image_files, 1):
            print(f"Processing {idx}/{len(image_files)}: {filename}")
            
            path = os.path.join(self.image_dir, filename)
            
            # Extract text
            text = self.extract_text_from_image(path)
            
            # Parse data
            data = self.parse_game_data(text)
            
            # Add metadata
            dt_info = self.extract_datetime_from_filename(filename)
            data['filename'] = filename
            data['datetime'] = dt_info['datetime'].isoformat() if dt_info['datetime'] else None
            data['ocr_text'] = text
            
            results.append(data)
        
        return results
    
    def export_to_text(self, results: List[Dict], output_file: str = "progression_log.txt"):
        """Export results to formatted text log"""
        output_path = os.path.join(self.output_dir, output_file)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for result in results:
                log_entry = self.format_log_entry(result['filename'], result)
                f.write(log_entry + "\n\n")
        
        print(f"\nLog exported to: {output_path}")
    
    def export_to_json(self, results: List[Dict], output_file: str = "ocr_results.json"):
        """Export raw results to JSON"""
        output_path = os.path.join(self.output_dir, output_file)
        
        # Remove OCR text from JSON export (too verbose)
        clean_results = []
        for result in results:
            clean_result = {k: v for k, v in result.items() if k != 'ocr_text'}
            clean_results.append(clean_result)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(clean_results, f, indent=2)
        
        print(f"JSON data exported to: {output_path}")
    
    def run(self):
        """Run the complete OCR extraction pipeline"""
        print("=" * 60)
        print("OVERMORTAL OCR EXTRACTOR")
        print("=" * 60)
        print()
        
        # Process images
        results = self.process_directory()
        
        # Export results
        self.export_to_text(results)
        self.export_to_json(results)
        
        # Print summary
        print()
        print("=" * 60)
        print("EXTRACTION SUMMARY")
        print("=" * 60)
        print(f"Images processed: {len(results)}")
        print(f"Successful extractions: {sum(1 for r in results if r.get('stage_name'))}")
        print(f"Output directory: {self.output_dir}")
        print()


def main():
    """Main entry point"""
    # Configuration
    IMAGE_DIR = "/Users/jaypalsinhchavda/Downloads/images"  # Update this path
    OUTPUT_DIR = "output"
    
    # Check if image directory exists
    if not os.path.exists(IMAGE_DIR):
        print(f"Error: Image directory '{IMAGE_DIR}' not found!")
        print("Please update IMAGE_DIR in the script to point to your screenshots folder.")
        return
    
    # Run OCR extractor
    extractor = OvermortalOCR(IMAGE_DIR, OUTPUT_DIR)
    extractor.run()


if __name__ == "__main__":
    main()
