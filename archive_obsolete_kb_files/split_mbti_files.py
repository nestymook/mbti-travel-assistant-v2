#!/usr/bin/env python3
"""
Split MBTI Tourist Spots into Individual Files for No-Chunking Strategy

This script splits the large markdown file into 16 smaller files,
one for each MBTI personality type, to work with no-chunking strategy.
"""

import boto3
import re
from pathlib import Path

def split_mbti_markdown():
    """Split the large markdown file by MBTI types."""
    
    print("📂 Splitting MBTI Tourist Spots into individual files...")
    
    # Download the original file with hours
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'mbti-knowledgebase-209803798463-us-east-1'
    source_file = 'Tourist_Spots_With_Hours.markdown'
    
    try:
        response = s3.get_object(Bucket=bucket_name, Key=source_file)
        content = response['Body'].read().decode('utf-8')
        print(f"✅ Downloaded {len(content)} characters from {source_file}")
    except Exception as e:
        print(f"❌ Error downloading file: {e}")
        return
    
    # MBTI types to extract
    mbti_types = [
        'INTJ', 'INTP', 'ENTJ', 'ENTP',
        'INFJ', 'INFP', 'ENFJ', 'ENFP', 
        'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
        'ISTP', 'ISFP', 'ESTP', 'ESFP'
    ]
    
    # Split content by MBTI sections
    sections = {}
    
    # Find all MBTI sections using the actual format
    for mbti_type in mbti_types:
        # Look for section headers like "## ENFJ Personality Type"
        pattern = rf'^##\s*{mbti_type}\s+Personality\s+Type'
        matches = list(re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE))
        
        if matches:
            start_pos = matches[0].start()
            
            # Find the next MBTI section or end of file
            next_pos = len(content)
            for other_mbti in mbti_types:
                if other_mbti != mbti_type:
                    other_pattern = rf'^##\s*{other_mbti}\s+Personality\s+Type'
                    other_matches = list(re.finditer(other_pattern, content, re.MULTILINE | re.IGNORECASE))
                    for match in other_matches:
                        if match.start() > start_pos and match.start() < next_pos:
                            next_pos = match.start()
            
            # Extract the section
            section_content = content[start_pos:next_pos].strip()
            sections[mbti_type] = section_content
            
            print(f"   Found {mbti_type}: {len(section_content)} characters")
    
    if not sections:
        print("❌ No MBTI sections found. Trying alternative parsing...")
        return
    
    # Create individual files and upload to S3
    uploaded_files = []
    
    for mbti_type, section_content in sections.items():
        # Create a complete markdown file for this MBTI type
        file_content = f"""# Hong Kong Tourist Attractions for {mbti_type} Personality Type

{section_content}

---
*Generated from MBTI Travel Assistant Knowledge Base*
*MBTI Type: {mbti_type}*
"""
        
        # Save locally first
        local_filename = f"Tourist_Spots_{mbti_type}.markdown"
        with open(local_filename, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        # Upload to S3
        s3_key = f"mbti_types/{local_filename}"
        try:
            s3.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=file_content.encode('utf-8'),
                ContentType='text/markdown'
            )
            uploaded_files.append(s3_key)
            print(f"✅ Uploaded {s3_key} ({len(file_content)} characters)")
        except Exception as e:
            print(f"❌ Error uploading {s3_key}: {e}")
    
    print(f"\n📊 Summary:")
    print(f"   Total MBTI types processed: {len(sections)}")
    print(f"   Files uploaded to S3: {len(uploaded_files)}")
    print(f"   S3 bucket: {bucket_name}")
    print(f"   Prefix: mbti_types/")
    
    return uploaded_files

def update_data_source_for_split_files():
    """Update the data source to include all MBTI type files."""
    
    print("\n🔄 Updating data source configuration...")
    
    # Update data source to include the mbti_types/ prefix
    import subprocess
    
    cmd = [
        'aws', 'bedrock-agent', 'update-data-source',
        '--knowledge-base-id', 'RCWW86CLM9',
        '--data-source-id', 'JJSNBHN3VI',
        '--name', 'MBTI-Split-Files-Source',
        '--data-source-configuration', 
        '{"type": "S3","s3Configuration": {"bucketArn": "arn:aws:s3:::mbti-knowledgebase-209803798463-us-east-1","inclusionPrefixes": ["mbti_types/"]}}',
        '--vector-ingestion-configuration',
        '{"chunkingConfiguration": {"chunkingStrategy": "NONE"}}',
        '--region', 'us-east-1'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Data source updated successfully")
            return True
        else:
            print(f"❌ Error updating data source: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error running AWS command: {e}")
        return False

def start_ingestion_job():
    """Start a new ingestion job."""
    
    print("\n🚀 Starting ingestion job...")
    
    import subprocess
    
    cmd = [
        'aws', 'bedrock-agent', 'start-ingestion-job',
        '--knowledge-base-id', 'RCWW86CLM9',
        '--data-source-id', 'JJSNBHN3VI',
        '--region', 'us-east-1'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            import json
            response = json.loads(result.stdout)
            job_id = response['ingestionJob']['ingestionJobId']
            print(f"✅ Ingestion job started: {job_id}")
            return job_id
        else:
            print(f"❌ Error starting ingestion job: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ Error running AWS command: {e}")
        return None

if __name__ == "__main__":
    print("🎯 MBTI File Splitter for No-Chunking Strategy")
    print("=" * 50)
    
    # Step 1: Split the files
    uploaded_files = split_mbti_markdown()
    
    if uploaded_files:
        # Step 2: Update data source
        if update_data_source_for_split_files():
            # Step 3: Start ingestion
            job_id = start_ingestion_job()
            
            if job_id:
                print(f"\n🎉 Success! Monitor ingestion job: {job_id}")
                print("\nNext steps:")
                print("1. Wait for ingestion to complete")
                print("2. Test your improved_mbti_attractions_list.py script")
                print("3. Each MBTI type is now a separate document")
            else:
                print("\n⚠️ Files uploaded but ingestion job failed to start")
        else:
            print("\n⚠️ Files uploaded but data source update failed")
    else:
        print("\n❌ File splitting failed")