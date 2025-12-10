"""
Image Analysis Script using Ollama Qwen3-VL

Analyzes course images using local vision LLM to:
1. Extract text/diagrams from images
2. Generate educational context
3. Map images to course topics
4. Create searchable descriptions for RAG

Usage:
    python -m app.etl.image_analyzer

Output:
    data/processed/images.json - Analyzed images with context
"""

import json
import logging
import base64
import re
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import hashlib
import xml.etree.ElementTree as ET
import httpx
from PIL import Image
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
RAW_DIR = DATA_DIR / "raw" / "course-data" / "ExportFile_COMP237"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_FILE = PROCESSED_DIR / "images.json"

# Ollama configuration - Use smaller 4B models for faster processing
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_PRIMARY_MODEL = "gemma3:4b"          # Primary: Fast general vision model (works well)
OLLAMA_FALLBACK_MODEL = "qwen3-vl:4b"       # Fallback: Specialized vision model
OLLAMA_MODEL = OLLAMA_PRIMARY_MODEL         # Default to primary

# Image analysis prompt
ANALYSIS_PROMPT = """Analyze this educational image from an Introduction to AI (COMP237) course. 

Provide a structured analysis:

1. **Image Type**: What kind of image is this? (diagram, flowchart, graph, formula, code screenshot, photo, illustration, etc.)

2. **Content Description**: Describe what is shown in the image in detail. Include any text, formulas, or labels visible.

3. **AI/ML Concepts**: What AI or machine learning concepts does this image illustrate? List specific topics like:
   - Neural networks, perceptrons, layers
   - Search algorithms (BFS, DFS, A*, greedy)
   - Machine learning (regression, classification, clustering)
   - Agents and environments
   - Natural language processing
   - Computer vision

4. **Educational Context**: How would this image be used to teach students? What does it help explain?

5. **Key Terms**: List 3-5 key technical terms shown or implied in this image.

Format your response as JSON:
{
    "image_type": "...",
    "description": "...",
    "concepts": ["concept1", "concept2", ...],
    "educational_context": "...",
    "key_terms": ["term1", "term2", ...]
}

If the image is not educational (like a banner, logo, or decorative), respond with:
{
    "image_type": "non-educational",
    "description": "Brief description",
    "concepts": [],
    "educational_context": "N/A",
    "key_terms": []
}
"""


class ImageAnalyzer:
    """Analyzes course images using Ollama vision model with fallback support"""
    
    def __init__(self, ollama_host: str = OLLAMA_HOST, model: str = OLLAMA_MODEL):
        self.ollama_host = ollama_host
        self.primary_model = OLLAMA_PRIMARY_MODEL
        self.fallback_model = OLLAMA_FALLBACK_MODEL
        self.current_model = model
        self.results = {
            "generated_at": datetime.now().isoformat(),
            "model": model,
            "summary": {
                "total_images": 0,
                "analyzed_images": 0,
                "educational_images": 0,
                "non_educational_images": 0,
                "failed_analysis": 0,
                "skipped_too_small": 0,
                "used_fallback": 0,
            },
            "images": [],
            "by_concept": {},  # Index by AI concept
        }
    
    async def check_ollama_available(self) -> bool:
        """Check if Ollama is running and at least one model is available"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.ollama_host}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [m.get("name", "") for m in models]
                    
                    # Check primary model
                    primary_available = any(self.primary_model in name for name in model_names)
                    fallback_available = any(self.fallback_model in name for name in model_names)
                    
                    if primary_available:
                        logger.info(f"✅ Primary model {self.primary_model} is available")
                        self.current_model = self.primary_model
                        return True
                    elif fallback_available:
                        logger.warning(f"⚠️ Primary {self.primary_model} not found, using fallback {self.fallback_model}")
                        self.current_model = self.fallback_model
                        return True
                    else:
                        logger.error(f"❌ Neither {self.primary_model} nor {self.fallback_model} found. Available: {model_names}")
                        return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to Ollama at {self.ollama_host}: {e}")
            return False
    
    def find_all_images(self) -> List[Path]:
        """Find all image files in the raw course data"""
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
        images = []
        
        for ext in image_extensions:
            images.extend(RAW_DIR.glob(f"**/*{ext}"))
        
        # Filter out very small images (likely icons/bullets)
        filtered = []
        for img_path in images:
            try:
                if img_path.stat().st_size > 2000:  # > 2KB
                    filtered.append(img_path)
                else:
                    self.results["summary"]["skipped_too_small"] += 1
            except Exception:
                pass
        
        logger.info(f"Found {len(filtered)} images (skipped {self.results['summary']['skipped_too_small']} small files)")
        return filtered
    
    def extract_context_from_path(self, image_path: Path) -> Dict:
        """Extract context from image path and nearby XML metadata files"""
        context = {
            "original_path": str(image_path.relative_to(RAW_DIR)),
            "filename": image_path.name,
            "parent_folder": image_path.parent.name,
        }
        
        # Try to find XML metadata file
        xml_path = image_path.with_suffix(f"{image_path.suffix}.xml")
        if xml_path.exists():
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
                # Extract identifier from XML
                for identifier in root.iter():
                    if "identifier" in identifier.tag.lower() and identifier.text:
                        context["blackboard_identifier"] = identifier.text
                        # Parse course context from identifier
                        # Example: 1693010_1#/courses/COMP237_INP.DEV/PastedImage...
                        if "#" in identifier.text:
                            context["course_path"] = identifier.text.split("#")[-1]
            except Exception as e:
                logger.debug(f"Could not parse XML for {xml_path}: {e}")
        
        # Try to infer module/week from path
        path_str = str(image_path)
        
        # Look for module patterns
        module_match = re.search(r"Module[_\s]?(\d+)", path_str, re.IGNORECASE)
        if module_match:
            context["module"] = int(module_match.group(1))
        
        week_match = re.search(r"Week[_\s]?(\d+)", path_str, re.IGNORECASE)
        if week_match:
            context["week"] = int(week_match.group(1))
        
        topic_match = re.search(r"Topic[_\s]?(\d+[\.\d]*)", path_str, re.IGNORECASE)
        if topic_match:
            context["topic"] = topic_match.group(1)
        
        return context
    
    def image_to_base64(self, image_path: Path, max_size: int = 1024) -> Optional[str]:
        """Convert image to base64, resizing if necessary"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Resize if too large
                if max(img.size) > max_size:
                    ratio = max_size / max(img.size)
                    new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Convert to base64
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=85)
                return base64.b64encode(buffer.getvalue()).decode("utf-8")
        except Exception as e:
            logger.warning(f"Could not process image {image_path}: {e}")
            return None
    
    async def analyze_image(self, image_path: Path) -> Optional[Dict]:
        """Analyze a single image using Ollama vision model with fallback"""
        # Convert image to base64
        image_b64 = self.image_to_base64(image_path)
        if not image_b64:
            return None
        
        # Extract context from path
        context = self.extract_context_from_path(image_path)
        
        # Try primary model first, then fallback
        models_to_try = [self.current_model]
        if self.current_model == self.primary_model and self.fallback_model:
            models_to_try.append(self.fallback_model)
        
        for model in models_to_try:
            try:
                # Use reasonable timeout for 4B models (much faster than 8B)
                async with httpx.AsyncClient(timeout=120.0) as client:
                    # Call Ollama API with vision model
                    response = await client.post(
                        f"{self.ollama_host}/api/generate",
                        json={
                            "model": model,
                            "prompt": ANALYSIS_PROMPT,
                            "images": [image_b64],
                            "stream": False,
                            "options": {
                                "temperature": 0.3,
                                "num_predict": 1024,
                            }
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        response_text = result.get("response", "")
                        
                        # Parse JSON from response
                        analysis = self._parse_analysis_response(response_text)
                        
                        if analysis:
                            # Track if we used fallback
                            if model != self.primary_model:
                                self.results["summary"]["used_fallback"] += 1
                            
                            return {
                                "id": hashlib.md5(str(image_path).encode()).hexdigest()[:16],
                                "path": context["original_path"],
                                "filename": context["filename"],
                                "context": context,
                                "analysis": analysis,
                                "is_educational": analysis.get("image_type") != "non-educational",
                                "analyzed_by": model,
                            }
                    else:
                        logger.warning(f"Ollama returned {response.status_code} for {image_path.name} with {model}")
                        
            except httpx.TimeoutException:
                logger.warning(f"Timeout analyzing {image_path.name} with {model}, trying next...")
                continue
            except Exception as e:
                logger.warning(f"Error analyzing {image_path.name} with {model}: {e}")
                continue
        
        return None
    
    def _parse_analysis_response(self, response_text: str) -> Optional[Dict]:
        """Parse JSON from LLM response"""
        try:
            # Remove any markdown code blocks
            clean = re.sub(r"```json\s*", "", response_text)
            clean = re.sub(r"```\s*", "", clean)
            clean = clean.strip()
            
            # Try to find JSON object in response
            json_match = re.search(r"\{[\s\S]*\}", clean)
            if json_match:
                return json.loads(json_match.group())
            
            return None
        except json.JSONDecodeError as e:
            logger.debug(f"Could not parse JSON from response: {e}")
            return None
    
    async def analyze_batch(self, images: List[Path], batch_size: int = 5) -> List[Dict]:
        """Analyze images in batches with concurrency limit"""
        results = []
        
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            logger.info(f"Analyzing batch {i//batch_size + 1}/{(len(images) + batch_size - 1)//batch_size} ({len(batch)} images)...")
            
            # Process batch sequentially (Ollama handles one request at a time well)
            for img_path in batch:
                result = await self.analyze_image(img_path)
                if result:
                    results.append(result)
                    self.results["summary"]["analyzed_images"] += 1
                    
                    if result["is_educational"]:
                        self.results["summary"]["educational_images"] += 1
                    else:
                        self.results["summary"]["non_educational_images"] += 1
                else:
                    self.results["summary"]["failed_analysis"] += 1
            
            # Small delay between batches
            await asyncio.sleep(0.5)
        
        return results
    
    def build_concept_index(self, images: List[Dict]):
        """Build an index of images by AI/ML concept"""
        concept_index = {}
        
        for img in images:
            if not img.get("is_educational"):
                continue
            
            concepts = img.get("analysis", {}).get("concepts", [])
            for concept in concepts:
                concept_key = concept.lower().replace(" ", "_")
                if concept_key not in concept_index:
                    concept_index[concept_key] = []
                concept_index[concept_key].append({
                    "id": img["id"],
                    "path": img["path"],
                    "description": img["analysis"].get("description", "")[:200],
                })
        
        return concept_index
    
    async def run(self, limit: Optional[int] = None):
        """Run the full image analysis pipeline"""
        logger.info("Starting image analysis pipeline...")
        
        # Check Ollama availability
        if not await self.check_ollama_available():
            logger.error("Ollama is not available. Please start Ollama and pull the model:")
            logger.error(f"  ollama pull {self.model}")
            return
        
        # Find all images
        images = self.find_all_images()
        self.results["summary"]["total_images"] = len(images)
        
        if limit:
            images = images[:limit]
            logger.info(f"Limited to {limit} images for testing")
        
        # Analyze images
        analyzed = await self.analyze_batch(images)
        self.results["images"] = analyzed
        
        # Build concept index
        self.results["by_concept"] = self.build_concept_index(analyzed)
        
        # Save results
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w") as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Results saved to {OUTPUT_FILE}")
        self._print_summary()
    
    def _print_summary(self):
        """Print analysis summary"""
        s = self.results["summary"]
        print("\n" + "="*60)
        print("IMAGE ANALYSIS SUMMARY")
        print("="*60)
        print(f"Model (primary):     {self.primary_model}")
        print(f"Model (fallback):    {self.fallback_model}")
        print(f"Total Images:        {s['total_images']}")
        print(f"Analyzed:            {s['analyzed_images']}")
        print(f"Educational:         {s['educational_images']}")
        print(f"Non-Educational:     {s['non_educational_images']}")
        print(f"Failed:              {s['failed_analysis']}")
        print(f"Skipped (too small): {s['skipped_too_small']}")
        print(f"Used Fallback:       {s.get('used_fallback', 0)}")
        print("-"*40)
        print(f"Concepts indexed:    {len(self.results.get('by_concept', {}))}")
        
        if self.results.get("by_concept"):
            print("\nTop concepts by image count:")
            sorted_concepts = sorted(
                self.results["by_concept"].items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:10]
            for concept, images in sorted_concepts:
                print(f"  {concept}: {len(images)} images")
        
        print("="*60 + "\n")


def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description="Analyze course images with Ollama vision model")
    parser.add_argument("--limit", type=int, help="Limit number of images to analyze (for testing)")
    args = parser.parse_args()
    
    analyzer = ImageAnalyzer()
    asyncio.run(analyzer.run(limit=args.limit))


if __name__ == "__main__":
    main()
