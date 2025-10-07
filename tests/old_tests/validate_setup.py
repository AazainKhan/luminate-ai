#!/usr/bin/env python3
"""
Validation Script for Luminate AI Ingestion Pipeline
====================================================

This script validates the setup and runs basic checks before ingestion.
"""

import sys
from pathlib import Path


def check_python_version():
    """Check Python version."""
    print("Checking Python version...", end=" ")
    if sys.version_info < (3, 8):
        print("❌")
        print(f"  Error: Python 3.8+ required, found {sys.version_info.major}.{sys.version_info.minor}")
        return False
    print(f"✅ ({sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro})")
    return True


def check_dependencies():
    """Check if all required dependencies are installed."""
    print("\nChecking dependencies...")
    
    required = {
        'bs4': 'beautifulsoup4',
        'pypdf': 'pypdf',
        'docx': 'python-docx',
        'pptx': 'python-pptx',
        'chardet': 'chardet',
        'tqdm': 'tqdm'
    }
    
    missing = []
    
    for import_name, package_name in required.items():
        try:
            __import__(import_name)
            print(f"  ✅ {package_name}")
        except ImportError:
            print(f"  ❌ {package_name}")
            missing.append(package_name)
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print(f"   Install with: pip install {' '.join(missing)}")
        return False
    
    return True


def check_source_directory():
    """Check if source directory exists and has content."""
    print("\nChecking source directory...")
    
    source_dir = Path('extracted/ExportFile_COMP237_INP')
    
    if not source_dir.exists():
        print(f"  ❌ Source directory not found: {source_dir}")
        print(f"     Create it or specify a different path with --source")
        return False
    
    print(f"  ✅ Directory exists: {source_dir}")
    
    # Check for manifest
    manifest = source_dir / 'imsmanifest.xml'
    if manifest.exists():
        print(f"  ✅ Found imsmanifest.xml")
    else:
        print(f"  ⚠️  imsmanifest.xml not found (optional)")
    
    # Count files
    dat_files = list(source_dir.glob('*.dat'))
    print(f"  ℹ️  Found {len(dat_files)} .dat files")
    
    if len(dat_files) == 0:
        print(f"  ⚠️  No .dat files found - is this the correct export?")
    
    return True


def check_write_permissions():
    """Check if we can write to output directories."""
    print("\nChecking write permissions...")
    
    test_dirs = ['cleaned', 'graph_seed', 'logs']
    
    all_ok = True
    for dir_name in test_dirs:
        dir_path = Path(dir_name)
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            test_file = dir_path / '.test'
            test_file.touch()
            test_file.unlink()
            print(f"  ✅ Can write to {dir_name}/")
        except Exception as e:
            print(f"  ❌ Cannot write to {dir_name}/: {e}")
            all_ok = False
    
    return all_ok


def check_disk_space():
    """Check available disk space."""
    print("\nChecking disk space...")
    
    try:
        import shutil
        stat = shutil.disk_usage('.')
        
        gb_free = stat.free / (1024**3)
        print(f"  ℹ️  Available space: {gb_free:.2f} GB")
        
        if gb_free < 1:
            print(f"  ⚠️  Low disk space (< 1 GB)")
            return False
        
        print(f"  ✅ Sufficient disk space")
        return True
    except Exception as e:
        print(f"  ⚠️  Could not check disk space: {e}")
        return True


def estimate_processing_time():
    """Estimate processing time based on file count."""
    print("\nEstimating processing time...")
    
    source_dir = Path('extracted/ExportFile_COMP237_INP')
    
    if not source_dir.exists():
        print("  ⚠️  Cannot estimate (source not found)")
        return
    
    # Count all supported files
    supported = ['.dat', '.html', '.htm', '.pdf', '.docx', '.pptx', '.txt', '.xml', '.md']
    total_files = 0
    
    for ext in supported:
        total_files += len(list(source_dir.rglob(f'*{ext}')))
    
    # Rough estimate: 15 files/second
    estimated_seconds = total_files / 15
    
    print(f"  ℹ️  Total files to process: {total_files}")
    
    if estimated_seconds < 60:
        print(f"  ℹ️  Estimated time: ~{estimated_seconds:.0f} seconds")
    else:
        print(f"  ℹ️  Estimated time: ~{estimated_seconds/60:.1f} minutes")


def run_sample_test():
    """Run a quick test on a sample file."""
    print("\nRunning sample test...")
    
    source_dir = Path('extracted/ExportFile_COMP237_INP')
    
    if not source_dir.exists():
        print("  ⚠️  Cannot run test (source not found)")
        return False
    
    # Find a .dat file
    dat_files = list(source_dir.glob('*.dat'))[:1]
    
    if not dat_files:
        print("  ⚠️  No .dat files to test")
        return True
    
    try:
        from ingest_clean_luminate import Config, DatFileParser, IngestionLogger
        
        config = Config()
        logger = IngestionLogger(Path('logs'))
        parser = DatFileParser(config, logger)
        
        test_file = dat_files[0]
        text, metadata = parser.parse(test_file)
        
        if text:
            print(f"  ✅ Successfully parsed sample file")
            print(f"     File: {test_file.name}")
            print(f"     Extracted {len(text)} characters")
            if metadata.get('bb_doc_id'):
                print(f"     Found BB ID: {metadata['bb_doc_id']}")
        else:
            print(f"  ⚠️  Sample file parsed but no text extracted")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Sample test failed: {e}")
        return False


def main():
    """Run all validation checks."""
    print("=" * 80)
    print("LUMINATE AI INGESTION PIPELINE - VALIDATION")
    print("=" * 80)
    
    results = []
    
    # Run checks
    results.append(("Python Version", check_python_version()))
    results.append(("Dependencies", check_dependencies()))
    results.append(("Source Directory", check_source_directory()))
    results.append(("Write Permissions", check_write_permissions()))
    results.append(("Disk Space", check_disk_space()))
    
    estimate_processing_time()
    
    results.append(("Sample Test", run_sample_test()))
    
    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check_name:.<40} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 80)
    
    if all_passed:
        print("\n✅ All checks passed! Ready to run ingestion pipeline.")
        print("\nRun the pipeline with:")
        print("  python ingest_clean_luminate.py")
        print("\nOr use the interactive quick start:")
        print("  python quick_start.py")
        return 0
    else:
        print("\n❌ Some checks failed. Please fix the issues above before running.")
        print("\nFor help, see README.md or check the error messages above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
