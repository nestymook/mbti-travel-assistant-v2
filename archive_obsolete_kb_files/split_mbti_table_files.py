#!/usr/bin/env python3
"""
Split MBTI Tourist Spots Table Files

This script splits Tourist_Spots_With_Hours.markdown by MBTI headers,
creating individual files with markdown table format for no-chunking strategy.
"""

import boto3
import re
from pathlib import Path

def split_mbti_table_files():
    """Split the markdown file by MBTI headers, preserving table format."""
    
    print("📂 Splitting MBTI Tourist Spots table files...")
    
    # Download the original file
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
    
    # Find all MBTI sections using the actual format: ### MBTI_TYPE
    for mbti_type in mbti_types:
        # Look for section headers like "### INTJ"
        pattern = rf'^###\s*{mbti_type}\s*$'
        matches = list(re.finditer(pattern, content, re.MULTILINE))
        
        if matches:
            start_pos = matches[0].end()  # Start after the header
            
            # Find the next MBTI section or end of file
            next_pos = len(content)
            for other_mbti in mbti_types:
                if other_mbti != mbti_type:
                    other_pattern = rf'^###\s*{other_mbti}\s*$'
                    other_matches = list(re.finditer(other_pattern, content, re.MULTILINE))
                    for match in other_matches:
                        if match.start() > start_pos and match.start() < next_pos:
                            next_pos = match.start()
            
            # Extract the section content (everything after the header)
            section_content = content[start_pos:next_pos].strip()
            
            if section_content:
                sections[mbti_type] = section_content
                print(f"   Found {mbti_type}: {len(section_content)} characters")
    
    if not sections:
        print("❌ No MBTI sections found.")
        return []
    
    # Create individual files and upload to S3
    uploaded_files = []
    
    for mbti_type, section_content in sections.items():
        # Create a complete markdown file with header and table
        file_content = f"""# {mbti_type} Personality Type - Hong Kong Tourist Attractions

{section_content}
"""
        
        # Save locally first
        local_filename = f"{mbti_type}_Tourist_Spots.markdown"
        with open(local_filename, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        # Upload to S3 in mbti_split/ folder
        s3_key = f"mbti_split/{local_filename}"
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
    print(f"   Prefix: mbti_split/")
    
    return uploaded_files

def update_data_source_for_split_files():
    """Update the data source to include all MBTI split files."""
    
    print("\n🔄 Updating data source configuration...")
    
    # Update data source to include the mbti_split/ prefix
    import subprocess
    
    cmd = [
        'aws', 'bedrock-agent', 'update-data-source',
        '--knowledge-base-id', 'RCWW86CLM9',
        '--data-source-id', 'JJSNBHN3VI',
        '--name', 'MBTI-Split-Table-Files',
        '--data-source-configuration', 
        '{"type": "S3","s3Configuration": {"bucketArn": "arn:aws:s3:::mbti-knowledgebase-209803798463-us-east-1","inclusionPrefixes": ["mbti_split/"]}}',
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

def monitor_ingestion_job(job_id):
    """Monitor the ingestion job progress."""
    
    if not job_id:
        return
    
    print(f"\n⏳ Monitoring ingestion job: {job_id}")
    
    import subprocess
    import time
    import json
    
    while True:
        cmd = [
            'aws', 'bedrock-agent', 'get-ingestion-job',
            '--knowledge-base-id', 'RCWW86CLM9',
            '--data-source-id', 'JJSNBHN3VI',
            '--ingestion-job-id', job_id,
            '--region', 'us-east-1'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                response = json.loads(result.stdout)
                status = response['ingestionJob']['status']
                stats = response['ingestionJob'].get('statistics', {})
                
                print(f"   Status: {status}")
                if stats:
                    print(f"   Documents scanned: {stats.get('numberOfDocumentsScanned', 0)}")
                    print(f"   Documents indexed: {stats.get('numberOfNewDocumentsIndexed', 0)}")
                    print(f"   Documents failed: {stats.get('numberOfDocumentsFailed', 0)}")
                
                if status in ['COMPLETE', 'FAILED']:
                    if status == 'COMPLETE':
                        print("✅ Ingestion completed successfully!")
                    else:
                        failure_reasons = response['ingestionJob'].get('failureReasons', [])
                        print(f"❌ Ingestion failed: {failure_reasons}")
                    break
                
                print("   Waiting 30 seconds...")
                time.sleep(30)
            else:
                print(f"❌ Error checking job status: {result.stderr}")
                break
        except Exception as e:
            print(f"❌ Error monitoring job: {e}")
            break

def list_uploaded_files():
    """List the files that were uploaded."""
    
    print("\n📋 Listing uploaded files:")
    
    import subprocess
    
    cmd = [
        'aws', 's3', 'ls', 
        's3://mbti-knowledgebase-209803798463-us-east-1/mbti_split/',
        '--region', 'us-east-1'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"❌ Error listing files: {result.stderr}")
    except Exception as e:
        print(f"❌ Error running command: {e}")

if __name__ == "__main__":
    print("🎯 MBTI Table File Splitter for No-Chunking Strategy")
    print("=" * 60)
    
    # Step 1: Split the files
    uploaded_files = split_mbti_table_files()
    
    if uploaded_files:
        # Step 2: List uploaded files
        list_uploaded_files()
        
        # Step 3: Update data source
        if update_data_source_for_split_files():
            # Step 4: Start ingestion
            job_id = start_ingestion_job()
            
            if job_id:
                # Step 5: Monitor ingestion
                monitor_ingestion_job(job_id)
                
                print(f"\n🎉 Process Complete!")
                print("\nNext steps:")
                print("1. Test your improved_mbti_attractions_list.py script")
                print("2. Each MBTI type is now a separate document with table format")
                print("3. No chunking strategy preserves table structure")
            else:
                print("\n⚠️ Files uploaded but ingestion job failed to start")
        else:
            print("\n⚠️ Files uploaded but data source update failed")
    else:
        print("\n❌ File splitting failed")