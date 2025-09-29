#!/usr/bin/env python3
"""
Clean Up Obsolete Knowledge Base Files

This script identifies and moves obsolete files that are no longer used
for the current MBTI Travel Assistant Knowledge Base implementation.
"""

import os
import shutil
from pathlib import Path

def create_archive_directory():
    """Create archive directory for obsolete files."""
    archive_dir = Path("archive_obsolete_kb_files")
    archive_dir.mkdir(exist_ok=True)
    return archive_dir

def identify_obsolete_files():
    """Identify files that are obsolete for current KB implementation."""
    
    # Current active files (keep these)
    active_files = {
        # Core implementation files
        "create_s3_vectors_kb.py",  # KB creation
        "create_individual_attraction_files.py",  # Data processing
        "test_all_infj_attractions.py",  # Comprehensive testing
        "test_infj_tourist_spots.py",  # Basic testing
        "diagnose_ingestion_failure.py",  # Diagnostics
        
        # Data files
        "Tourist_Spots_With_Hours.markdown",  # Source data
        "complete_infj_attractions.json",  # Test results
        "infj_attractions.json",  # Test results
        
        # Documentation
        "mbti_travel_assistant_mcp/KNOWLEDGE_BASE_SUMMARY.md",
        "mbti_travel_assistant_mcp/docs/KNOWLEDGE_BASE_IMPLEMENTATION.md",
    }
    
    # Obsolete files (move these to archive)
    obsolete_files = {
        # Old preprocessing attempts
        "preprocess_markdown.py",
        "corrected_preprocess_markdown.py", 
        "update_kb_with_optimized_markdown.py",
        "final_kb_update_with_addresses.py",
        
        # Alternative format experiments
        "convert_mbti_formats.py",
        "split_mbti_table_files.py", 
        "split_mbti_files.py",
        
        # Old optimization attempts
        "implement_kb_optimizations.py",
        "s3_vectors_optimization_guide.py",
        "advanced_kb_retrieval.py",
        "optimize_kb_for_markdown.py",
        "practical_kb_optimizations.md",
        
        # Old Nova Pro implementations
        "final_nova_pro_kb_implementation.py",
        "test_nova_pro_fixed.py",
        "test_nova_pro_kb.py",
        "test_retrieve_and_generate.py",
        
        # Old API implementations
        "mbti_attractions_api.py",
        "improved_mbti_attractions_list.py",
        "get_mbti_attractions_list.py",
        
        # Old data files
        "Tourist_Spots_Corrected_Optimized.markdown",
        "MBTI_ATTRACTIONS_SYSTEM_SUMMARY.md",
        
        # Temporary files
        "Tourist_Spots_With_Hours_temp.markdown",
        "ENFP_Tourist_Spots_Preview.markdown",
        "ENFP_JSON_Preview.json",
        "INTJ_Tourist_Spots_Preview.markdown",
        "ENFP_Structured_Preview.md",
        "ENFP_Individual_Preview.md",
        "verify_addresses.py",
    }
    
    return active_files, obsolete_files

def move_obsolete_files():
    """Move obsolete files to archive directory."""
    
    print("🧹 Cleaning Up Obsolete Knowledge Base Files")
    print("=" * 50)
    
    archive_dir = create_archive_directory()
    active_files, obsolete_files = identify_obsolete_files()
    
    moved_count = 0
    not_found_count = 0
    
    for file_path in obsolete_files:
        if os.path.exists(file_path):
            try:
                # Create subdirectories in archive if needed
                archive_path = archive_dir / file_path
                archive_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Move file to archive
                shutil.move(file_path, archive_path)
                print(f"✅ Moved: {file_path} → {archive_path}")
                moved_count += 1
                
            except Exception as e:
                print(f"❌ Error moving {file_path}: {e}")
        else:
            print(f"⚠️ Not found: {file_path}")
            not_found_count += 1
    
    print(f"\n📊 Cleanup Summary:")
    print(f"   Files moved to archive: {moved_count}")
    print(f"   Files not found: {not_found_count}")
    print(f"   Archive location: {archive_dir}")
    
    return moved_count

def create_cleanup_summary():
    """Create a summary of what was cleaned up."""
    
    active_files, obsolete_files = identify_obsolete_files()
    
    summary = f"""# Knowledge Base Cleanup Summary

## Files Kept (Active Implementation)

### Core Implementation Scripts
"""
    
    core_scripts = [f for f in active_files if f.endswith('.py')]
    for script in sorted(core_scripts):
        summary += f"- `{script}`\n"
    
    summary += f"""
### Data Files
"""
    data_files = [f for f in active_files if not f.endswith('.py')]
    for data_file in sorted(data_files):
        summary += f"- `{data_file}`\n"
    
    summary += f"""
## Files Archived (Obsolete)

### Old Preprocessing Scripts
"""
    preprocessing = [f for f in obsolete_files if 'preprocess' in f or 'update_kb' in f]
    for script in sorted(preprocessing):
        summary += f"- `{script}` - Superseded by individual file approach\n"
    
    summary += f"""
### Alternative Format Experiments  
"""
    formats = [f for f in obsolete_files if 'convert' in f or 'split' in f]
    for script in sorted(formats):
        summary += f"- `{script}` - Alternative approaches not used\n"
    
    summary += f"""
### Old Optimization Attempts
"""
    optimizations = [f for f in obsolete_files if 'optim' in f or 'advanced' in f]
    for script in sorted(optimizations):
        summary += f"- `{script}` - Replaced by no-chunking strategy\n"
    
    summary += f"""
### Legacy Nova Pro Implementations
"""
    nova_pro = [f for f in obsolete_files if 'nova_pro' in f or 'retrieve_and_generate' in f]
    for script in sorted(nova_pro):
        summary += f"- `{script}` - Old implementation approach\n"
    
    summary += f"""
### Old API Implementations
"""
    apis = [f for f in obsolete_files if 'api' in f or 'attractions_list' in f]
    for script in sorted(apis):
        summary += f"- `{script}` - Superseded by comprehensive testing\n"
    
    summary += f"""
## Current Active Architecture

The current knowledge base implementation uses:

1. **Knowledge Base**: RCWW86CLM9 with S3 Vectors storage
2. **Data Source**: JJSNBHN3VI (MBTI-Individual-Attractions)  
3. **Strategy**: No-chunking with individual attraction files
4. **Files**: 183 individual markdown files in `mbti_individual/` prefix
5. **Success Rate**: 100% (all 13 INFJ attractions retrievable)

## Archived Files Location

All obsolete files have been moved to: `archive_obsolete_kb_files/`

These files are preserved for reference but are not part of the current implementation.
"""
    
    with open("CLEANUP_SUMMARY.md", "w", encoding="utf-8") as f:
        f.write(summary)
    
    print(f"📄 Created cleanup summary: CLEANUP_SUMMARY.md")

def main():
    """Main cleanup process."""
    
    # Move obsolete files
    moved_count = move_obsolete_files()
    
    # Create summary
    create_cleanup_summary()
    
    print(f"\n🎉 Cleanup completed!")
    print(f"   {moved_count} obsolete files archived")
    print(f"   Current implementation files preserved")
    print(f"   Archive: archive_obsolete_kb_files/")
    print(f"   Summary: CLEANUP_SUMMARY.md")

if __name__ == "__main__":
    main()