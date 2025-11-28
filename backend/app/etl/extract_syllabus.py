import os
import json
import re
import argparse
from langchain_community.document_loaders import PyPDFLoader
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def extract_syllabus_structure(pdf_path: str, output_path: str):
    print(f"📄 Parsing Course Outline: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return

    # 1. Load PDF Text
    try:
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        full_text = "\n".join([p.page_content for p in pages])
    except Exception as e:
        print(f"Error loading PDF: {e}")
        return

    # 2. Try Regex Extraction (Fallback/Primary since LLM is flaky)
    print("🧠 Analyzing structure with Regex Parser...")
    syllabus_data = parse_syllabus_regex(full_text)
    
    if not syllabus_data['weeks']:
        print("⚠️ Regex parsing failed to find weeks. Please check the PDF format.")
    
    # 3. Save to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(syllabus_data, f, indent=2)
    print(f"✅ Syllabus map saved to {output_path}")

def parse_syllabus_regex(text: str) -> dict:
    weeks = []
    current_week = None
    buffer = []
    
    # Split into lines and iterate
    lines = text.split('\n')
    
    # Regex to find "Week X" or just "X" on a line
    # Based on the text dump, weeks appear as single numbers on a line
    week_start_pattern = re.compile(r'^\s*(\d{1,2})\s*$')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        match = week_start_pattern.match(line)
        if match:
            # Save previous week
            if current_week:
                current_week['topics'] = clean_topics(buffer)
                weeks.append(current_week)
            
            # Start new week
            week_num = int(match.group(1))
            # Filter out likely page numbers or noise (weeks are usually 1-15)
            if 1 <= week_num <= 15:
                current_week = {
                    "week_number": week_num,
                    "title": f"Week {week_num}", # Placeholder title
                    "topics": []
                }
                buffer = []
            else:
                # If it's a page number like "4", just append to buffer if we are in a week
                if current_week:
                    buffer.append(line)
        else:
            if current_week:
                buffer.append(line)
    
    # Append last week
    if current_week:
        current_week['topics'] = clean_topics(buffer)
        weeks.append(current_week)
        
    return {
        "course_code": "COMP237",
        "course_title": "Introduction to AI",
        "weeks": weeks
    }

def clean_topics(lines: list) -> list:
    # Join lines and split by common delimiters or just return meaningful lines
    text = " ".join(lines)
    # Remove common noise
    text = re.sub(r'Chapter \d+.*', '', text) # Remove reading assignments often mixed in
    text = re.sub(r'Lecture videos.*', '', text)
    text = re.sub(r'On-line lab tutorial.*', '', text)
    text = re.sub(r'Discussion boards.*', '', text)
    text = re.sub(r'N/A', '', text)
    
    # Extract potential topics (this is heuristic)
    # We'll just return the raw text as keywords for now, maybe split by period
    keywords = [s.strip() for s in text.split('.') if len(s.strip()) > 5]
    return keywords[:10] # Limit to top 10 phrases

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    extract_syllabus_structure(args.pdf, args.output)