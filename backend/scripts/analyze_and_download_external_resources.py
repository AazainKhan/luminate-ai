#!/usr/bin/env python3
"""
Analyze Blackboard export for external resources and download them
Generates a report of all media, links, and downloadable content
"""

import sys
import re
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse, unquote
from typing import Dict, List, Set
import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BlackboardResourceAnalyzer:
    """Analyzes Blackboard exports for external resources"""
    
    def __init__(self, export_dir: Path):
        """Initialize analyzer with export directory"""
        self.export_dir = export_dir
        self.manifest_path = export_dir / "imsmanifest.xml"
        
        # Track all resources
        self.images: Set[str] = set()
        self.videos: Set[str] = set()
        self.audio: Set[str] = set()
        self.documents: Set[str] = set()
        self.external_links: Set[str] = set()
        self.mediasite_links: Set[str] = set()
        self.youtube_links: Set[str] = set()
        self.inaccessible_links: Set[str] = set()
        
    def analyze(self):
        """Run full analysis"""
        logger.info(f"🔍 Analyzing Blackboard export: {self.export_dir}")
        
        # Parse manifest
        self.parse_manifest()
        
        # Scan all files
        self.scan_html_files()
        self.scan_xml_files()
        self.scan_media_files()
        
        # Generate report
        self.generate_report()
        
    def parse_manifest(self):
        """Parse imsmanifest.xml"""
        if not self.manifest_path.exists():
            logger.warning("⚠️ imsmanifest.xml not found")
            return
        
        try:
            tree = ET.parse(self.manifest_path)
            root = tree.getroot()
            
            # Extract resource references
            for resource in root.findall('.//{*}resource'):
                href = resource.get('href')
                if href:
                    file_path = self.export_dir / href
                    if file_path.exists():
                        self._categorize_file(file_path)
            
            logger.info(f"✅ Parsed manifest: found {len(root.findall('.//{*}resource'))} resources")
        except Exception as e:
            logger.error(f"❌ Error parsing manifest: {e}")
    
    def scan_html_files(self):
        """Scan HTML files for external links"""
        html_files = list(self.export_dir.rglob("*.html"))
        logger.info(f"📄 Scanning {len(html_files)} HTML files...")
        
        for html_file in html_files:
            try:
                with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Find all links
                    for link in soup.find_all(['a', 'img', 'video', 'audio', 'source', 'iframe']):
                        href = link.get('href') or link.get('src')
                        if href and (href.startswith('http') or href.startswith('www')):
                            self._categorize_url(href)
            except Exception as e:
                logger.debug(f"Error reading {html_file}: {e}")
    
    def scan_xml_files(self):
        """Scan XML files for resource references"""
        xml_files = list(self.export_dir.rglob("*.xml"))
        logger.info(f"📄 Scanning {len(xml_files)} XML files...")
        
        for xml_file in xml_files:
            if xml_file.name == "imsmanifest.xml":
                continue
            try:
                with open(xml_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Find URLs in XML
                    urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', content)
                    for url in urls:
                        self._categorize_url(url)
            except Exception as e:
                logger.debug(f"Error reading {xml_file}: {e}")
    
    def scan_media_files(self):
        """Scan for local media files"""
        logger.info("🎬 Scanning for local media files...")
        
        # Images
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.svg', '*.webp']:
            self.images.update(str(p.relative_to(self.export_dir)) for p in self.export_dir.rglob(ext))
        
        # Videos
        for ext in ['*.mp4', '*.avi', '*.mov', '*.wmv', '*.flv', '*.webm']:
            self.videos.update(str(p.relative_to(self.export_dir)) for p in self.export_dir.rglob(ext))
        
        # Audio
        for ext in ['*.mp3', '*.wav', '*.ogg', '*.m4a']:
            self.audio.update(str(p.relative_to(self.export_dir)) for p in self.export_dir.rglob(ext))
        
        # Documents
        for ext in ['*.pdf', '*.docx', '*.pptx', '*.xlsx', '*.doc', '*.ppt', '*.xls']:
            self.documents.update(str(p.relative_to(self.export_dir)) for p in self.export_dir.rglob(ext))
    
    def _categorize_file(self, file_path: Path):
        """Categorize a file by extension"""
        ext = file_path.suffix.lower()
        rel_path = str(file_path.relative_to(self.export_dir))
        
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp']:
            self.images.add(rel_path)
        elif ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']:
            self.videos.add(rel_path)
        elif ext in ['.mp3', '.wav', '.ogg', '.m4a']:
            self.audio.add(rel_path)
        elif ext in ['.pdf', '.docx', '.pptx', '.xlsx', '.doc', '.ppt', '.xls']:
            self.documents.add(rel_path)
    
    def _categorize_url(self, url: str):
        """Categorize a URL"""
        url_lower = url.lower()
        
        if 'mediasite' in url_lower:
            self.mediasite_links.add(url)
        elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            self.youtube_links.add(url)
        elif url_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg')):
            self.images.add(url)
        elif url_lower.endswith(('.mp4', '.avi', '.mov', '.webm')):
            self.videos.add(url)
        elif url_lower.endswith(('.mp3', '.wav', '.ogg')):
            self.audio.add(url)
        elif url_lower.endswith(('.pdf', '.docx', '.pptx', '.xlsx')):
            self.documents.add(url)
        else:
            self.external_links.add(url)
    
    def generate_report(self):
        """Generate analysis report"""
        logger.info("\n" + "="*80)
        logger.info("📊 BLACKBOARD EXPORT ANALYSIS REPORT")
        logger.info("="*80)
        
        logger.info(f"\n📁 LOCAL RESOURCES:")
        logger.info(f"   Images: {len([i for i in self.images if not i.startswith('http')])}")
        logger.info(f"   Videos: {len([v for v in self.videos if not v.startswith('http')])}")
        logger.info(f"   Audio: {len([a for a in self.audio if not a.startswith('http')])}")
        logger.info(f"   Documents: {len([d for d in self.documents if not d.startswith('http')])}")
        
        logger.info(f"\n🌐 EXTERNAL RESOURCES:")
        logger.info(f"   External Links: {len(self.external_links)}")
        logger.info(f"   YouTube Videos: {len(self.youtube_links)}")
        logger.info(f"   Mediasite Videos: {len(self.mediasite_links)}")
        logger.info(f"   External Images: {len([i for i in self.images if i.startswith('http')])}")
        logger.info(f"   External Videos: {len([v for v in self.videos if v.startswith('http')])}")
        
        # Save detailed report
        report_path = self.export_dir.parent / "resource_analysis_report.json"
        report = {
            "local_resources": {
                "images": sorted([i for i in self.images if not i.startswith('http')]),
                "videos": sorted([v for v in self.videos if not v.startswith('http')]),
                "audio": sorted([a for a in self.audio if not a.startswith('http')]),
                "documents": sorted([d for d in self.documents if not d.startswith('http')]),
            },
            "external_resources": {
                "links": sorted(list(self.external_links)),
                "youtube": sorted(list(self.youtube_links)),
                "mediasite": sorted(list(self.mediasite_links)),
                "images": sorted([i for i in self.images if i.startswith('http')]),
                "videos": sorted([v for v in self.videos if v.startswith('http')]),
                "audio": sorted([a for a in self.audio if a.startswith('http')]),
                "documents": sorted([d for d in self.documents if d.startswith('http')]),
            }
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n💾 Detailed report saved to: {report_path}")
        
        # Generate manual download list
        self.generate_manual_download_list()
    
    def generate_manual_download_list(self):
        """Generate list of resources that need manual download"""
        manual_list_path = self.export_dir.parent / "MANUAL_DOWNLOAD_LIST.md"
        
        with open(manual_list_path, 'w') as f:
            f.write("# Manual Download Required\n\n")
            f.write("The following resources cannot be automatically downloaded and require manual action:\n\n")
            
            if self.mediasite_links:
                f.write("## 🎥 Mediasite Videos (Requires Login)\n\n")
                f.write("These videos are hosted on Mediasite and require institutional login:\n\n")
                for link in sorted(self.mediasite_links):
                    f.write(f"- [ ] {link}\n")
                f.write("\n**Action Required:** Log into Mediasite, download videos, and place in `raw_data/mediasite_videos/`\n\n")
            
            if self.youtube_links:
                f.write("## 📺 YouTube Videos\n\n")
                f.write("These can be downloaded using youtube-dl or yt-dlp:\n\n")
                f.write("```bash\n")
                f.write("# Install yt-dlp: pip install yt-dlp\n")
                for link in sorted(self.youtube_links):
                    f.write(f"yt-dlp '{link}'\n")
                f.write("```\n\n")
            
            if self.external_links:
                f.write("## 🔗 External Links (Check Accessibility)\n\n")
                f.write("These links should be checked for accessibility:\n\n")
                for link in sorted(self.external_links)[:50]:  # Limit to first 50
                    f.write(f"- [ ] {link}\n")
                if len(self.external_links) > 50:
                    f.write(f"\n... and {len(self.external_links) - 50} more (see JSON report)\n")
                f.write("\n")
        
        logger.info(f"📝 Manual download list saved to: {manual_list_path}")


def download_accessible_resources(report_path: Path, output_dir: Path):
    """Download resources that are publicly accessible"""
    logger.info("\n" + "="*80)
    logger.info("⬇️  DOWNLOADING ACCESSIBLE RESOURCES")
    logger.info("="*80)
    
    with open(report_path) as f:
        report = json.load(f)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Download external images
    external_images = report['external_resources']['images']
    if external_images:
        logger.info(f"\n📸 Downloading {len(external_images)} external images...")
        img_dir = output_dir / "images"
        img_dir.mkdir(exist_ok=True)
        
        for i, url in enumerate(external_images, 1):
            try:
                filename = Path(urlparse(url).path).name or f"image_{i}.jpg"
                output_path = img_dir / filename
                
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"  ✅ [{i}/{len(external_images)}] {filename}")
            except Exception as e:
                logger.warning(f"  ❌ [{i}/{len(external_images)}] Failed: {url} - {e}")
    
    # Download external documents
    external_docs = report['external_resources']['documents']
    if external_docs:
        logger.info(f"\n📄 Downloading {len(external_docs)} external documents...")
        docs_dir = output_dir / "documents"
        docs_dir.mkdir(exist_ok=True)
        
        for i, url in enumerate(external_docs, 1):
            try:
                filename = Path(urlparse(url).path).name or f"document_{i}.pdf"
                output_path = docs_dir / filename
                
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"  ✅ [{i}/{len(external_docs)}] {filename}")
            except Exception as e:
                logger.warning(f"  ❌ [{i}/{len(external_docs)}] Failed: {url} - {e}")
    
    logger.info(f"\n✅ Downloaded resources saved to: {output_dir}")


def main():
    """Main execution"""
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    export_dir = project_root / "raw_data" / "ExportFile_COMP237"
    
    if not export_dir.exists():
        logger.error(f"❌ Export directory not found: {export_dir}")
        return 1
    
    # Run analysis
    analyzer = BlackboardResourceAnalyzer(export_dir)
    analyzer.analyze()
    
    # Download accessible resources
    report_path = project_root / "raw_data" / "resource_analysis_report.json"
    output_dir = project_root / "raw_data" / "downloaded_external_resources"
    
    try:
        download_accessible_resources(report_path, output_dir)
    except Exception as e:
        logger.error(f"❌ Error downloading resources: {e}")
    
    logger.info("\n" + "="*80)
    logger.info("✅ ANALYSIS COMPLETE")
    logger.info("="*80)
    logger.info("\n📋 Next Steps:")
    logger.info("1. Review MANUAL_DOWNLOAD_LIST.md for resources requiring manual download")
    logger.info("2. Check downloaded_external_resources/ for automatically downloaded files")
    logger.info("3. Re-run ETL pipeline to ingest all resources into ChromaDB")
    
    return 0


if __name__ == "__main__":
    exit(main())

