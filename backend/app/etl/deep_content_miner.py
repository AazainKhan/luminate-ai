import os
import re
import json
import argparse
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeepContentMiner:
    def __init__(self, export_dir: str, mappings_path: str, syllabus_path: str = None):
        self.export_dir = export_dir
        self.mappings = self._load_json(mappings_path)
        # Handle mapping structure if it's nested
        if "resource_to_title" in self.mappings:
            self.mappings = self.mappings["resource_to_title"]
            
        self.syllabus = self._load_json(syllabus_path) if syllabus_path else {}
        self.embedded_items = []

    def _load_json(self, path: str) -> Dict:
        if not path or not os.path.exists(path):
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _clean_context_text(self, text: str) -> str:
        noise_patterns = [
            r"Watch this (short )?video( to learn more)?( about)?",
            r"Click the (following )?link",
            r"then continue reading",
            r"Ref::?",
            r"https?://\S+"
        ]
        cleaned = text
        for pattern in noise_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip(" :-,")

    def _enrich_from_syllabus(self, title: str) -> Dict:
        """
        Matches a generic title (e.g., 'Topic 5.2') to the Syllabus Map.
        Returns enriched title and keywords.
        """
        if not self.syllabus or 'weeks' not in self.syllabus:
            return {"module": "General", "keywords": []}

        # Extract number from "Topic 5.2" or "Week 5"
        match = re.search(r'(Topic|Week|Module)\s+(\d+)', title, re.IGNORECASE)
        if match:
            week_num = int(match.group(2))
            
            # Find matching week in syllabus
            for week in self.syllabus['weeks']:
                # Handle cases where syllabus might use string "1" or int 1
                if int(week.get('week_number', -1)) == week_num:
                    return {
                        "module": f"Week {week_num}: {week['title']}",
                        "keywords": week.get('topics', []) + week.get('keywords', [])
                    }
        
        return {"module": "General Resources", "keywords": []}

    def _extract_title_from_html(self, soup: BeautifulSoup) -> Optional[str]:
        for tag in ['h1', 'h2', 'h3', 'h4']:
            header = soup.find(tag)
            if header:
                text = header.get_text(strip=True)
                if len(text) > 5:
                    return text
        return None

    def scan(self):
        logger.info(f"Scanning directory: {self.export_dir}")
        for root, _, files in os.walk(self.export_dir):
            for file in files:
                if file.endswith(('.dat', '.xml')):
                    self._process_file(os.path.join(root, file), file)

    def _process_file(self, filepath: str, filename: str):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Handle XML parsing with fallback
            try:
                xml_soup = BeautifulSoup(content, 'xml')
                text_tag = xml_soup.find('TEXT')
                if not text_tag:
                    # Try parsing as HTML directly if XML structure is missing/broken
                    soup = BeautifulSoup(content, 'html.parser')
                else:
                    html_content = text_tag.get_text()
                    soup = BeautifulSoup(html_content, 'html.parser')
            except Exception:
                soup = BeautifulSoup(content, 'html.parser')

            resource_id = filename.replace('.dat', '').replace('.xml', '')
            
            # Get mapping info
            # If mappings is a simple dict of id->title
            if isinstance(self.mappings.get(resource_id), str):
                title = self.mappings.get(resource_id)
                parent = "Unknown Module"
            else:
                mapping_info = self.mappings.get(resource_id, {})
                title = mapping_info.get('title', 'Unknown Title') if isinstance(mapping_info, dict) else 'Unknown Title'
            
            # 1. Rescue Title from HTML
            if title in ["ultraDocumentBody", "Content", "Unknown Title", "ROOT", "--TOP--"]:
                rescued_title = self._extract_title_from_html(soup)
                if rescued_title:
                    title = rescued_title

            # 2. Enrich with Syllabus Data
            syllabus_info = self._enrich_from_syllabus(title)
            parent_module = syllabus_info['module']
            keywords = syllabus_info['keywords']

            links = []
            for a in soup.find_all('a', href=True):
                links.append(self._extract_link_info(a, soup, keywords))
            
            for iframe in soup.find_all('iframe', src=True):
                links.append(self._extract_link_info(iframe, soup, keywords, is_iframe=True))

            valid_links = [l for l in links if l and not self._is_internal(l['url'])]

            if valid_links:
                self.embedded_items.append({
                    "source_file": filename,
                    "associated_resource_id": resource_id,
                    "course_location": {
                        "parent": parent_module,
                        "title": title,
                        "syllabus_keywords": keywords
                    },
                    "extracted_links": valid_links
                })

        except Exception as e:
            logger.warning(f"Error processing {filename}: {e}")

    def _is_internal(self, url: str) -> bool:
        return url.startswith(('/', '#', 'mailto:')) or 'bbcswebdav' in url or '@X@' in url

    def _extract_link_info(self, tag, soup, keywords, is_iframe=False):
        url = tag.get('src') if is_iframe else tag.get('href')
        
        if not url:
            return None

        link_type = "generic_url"
        if "mediasite" in url: link_type = "mediasite"
        elif "youtube" in url or "youtu.be" in url: link_type = "youtube"
        elif "panopto" in url: link_type = "panopto"
        elif "zoom" in url: link_type = "zoom"

        context = ""
        parent_p = tag.find_parent('p')
        if parent_p:
            context = parent_p.get_text(strip=True)
        
        if not context or len(context) < 10:
            prev_header = tag.find_previous(['h1', 'h2', 'h3', 'h4'])
            if prev_header:
                context = f"{prev_header.get_text(strip=True)}: {context}"

        # Append syllabus keywords to context for better embedding retrieval
        enriched_context = self._clean_context_text(context)
        if keywords:
            enriched_context += f"\nRelated Topics: {', '.join(keywords[:5])}"

        return {
            "type": link_type,
            "url": url,
            "context_text": enriched_context
        }

    def save(self, output_path: str):
        with open(output_path, 'w') as f:
            json.dump({"embedded_items": self.embedded_items}, f, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-dir", required=True)
    parser.add_argument("--mappings", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--syllabus", help="Path to syllabus_map.json")
    args = parser.parse_args()

    miner = DeepContentMiner(args.export_dir, args.mappings, args.syllabus)
    miner.scan()
    miner.save(args.output)
    logger.info(f"Mining complete. Saved to {args.output}")
