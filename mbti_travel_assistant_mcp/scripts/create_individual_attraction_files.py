#!/usr/bin/env python3
"""
Create Individual Attraction Files for No-Chunking Strategy

This script creates one file per attraction with structured markdown format,
ensuring each file is small enough for no-chunking strategy.
"""

import boto3
import re
from typing import Dict, List

def create_individual_attraction_files():
    """Create individual files for each attraction."""
    
    print("📂 Creating individual attraction files...")
    
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
        return []
    
    # MBTI types to extract
    mbti_types = [
        'INTJ', 'INTP', 'ENTJ', 'ENTP',
        'INFJ', 'INFP', 'ENFJ', 'ENFP', 
        'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
        'ISTP', 'ISFP', 'ESTP', 'ESFP'
    ]
    
    all_files = []
    
    # Process each MBTI section
    for mbti_type in mbti_types:
        # Find section
        pattern = rf'^###\s*{mbti_type}\s*$'
        matches = list(re.finditer(pattern, content, re.MULTILINE))
        
        if matches:
            start_pos = matches[0].end()
            
            # Find next section
            next_pos = len(content)
            for other_mbti in mbti_types:
                if other_mbti != mbti_type:
                    other_pattern = rf'^###\s*{other_mbti}\s*$'
                    other_matches = list(re.finditer(other_pattern, content, re.MULTILINE))
                    for match in other_matches:
                        if match.start() > start_pos and match.start() < next_pos:
                            next_pos = match.start()
            
            section_content = content[start_pos:next_pos].strip()
            
            # Parse table rows more carefully
            lines = section_content.split('\n')
            
            # Find the table header to understand column structure
            header_line = None
            data_rows = []
            
            for i, line in enumerate(lines):
                line = line.strip()
                if '|' in line and 'Tourist Spot' in line:
                    header_line = line
                elif '|' in line and '---' in line:
                    # Skip separator
                    continue
                elif '|' in line and header_line and len(line.split('|')) >= 5:
                    data_rows.append(line)
            
            if header_line and data_rows:
                # Parse header
                headers = [h.strip() for h in header_line.split('|') if h.strip()]
                
                # Process each data row
                for row_idx, row in enumerate(data_rows, 1):
                    cells = [cell.strip() for cell in row.split('|')]
                    
                    # Skip empty rows
                    if len(cells) < 3:
                        continue
                    
                    # Extract data (skip first and last empty cells from markdown table format)
                    if cells[0] == '':
                        cells = cells[1:]
                    if cells and cells[-1] == '':
                        cells = cells[:-1]
                    
                    # Map cells to headers
                    attraction_data = {}
                    for i, header in enumerate(headers):
                        if i < len(cells):
                            attraction_data[header] = cells[i] if cells[i] else ""
                    
                    # Get attraction name (first column)
                    attraction_name = attraction_data.get('Tourist Spot', f'Attraction_{row_idx}')
                    
                    if not attraction_name or attraction_name == '':
                        continue
                    
                    # Create structured markdown content
                    file_content = f"""# {attraction_name}

## MBTI Personality Match
**Type:** {mbti_type}  
**Description:** {attraction_data.get('Description', 'Perfect match for this personality type')}

## Location Information
**Address:** {attraction_data.get('Address', 'Address not specified')}  
**District:** {attraction_data.get('District', 'District not specified')}  
**Area:** {attraction_data.get('Location', 'Location not specified')}

## Operating Hours
**Weekdays (Mon-Fri):** {attraction_data.get('Operating Hours (Mon-Fri)', 'Hours not specified')}  
**Weekends (Sat-Sun):** {attraction_data.get('Operating Hours (Sat-Sun)', 'Hours not specified')}  
**Public Holidays:** {attraction_data.get('Operating Hours (Public Holiday)', 'Hours not specified')}

## Additional Information
**Contact/Remarks:** {attraction_data.get('Remarks', 'No additional information')}  
**Full Day Info:** {attraction_data.get('Full Day', 'Not specified')}

## MBTI Suitability
This attraction is specifically recommended for **{mbti_type}** personality types because it aligns with their preferences and characteristics.

## Keywords
MBTI: {mbti_type}, Hong Kong, Tourist Attraction, {attraction_data.get('District', '')}, {attraction_data.get('Location', '')}, {attraction_name.replace(' ', ', ')}
"""
                    
                    # Create safe filename
                    safe_name = attraction_name.replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '').replace(',', '').replace('&', 'and')
                    filename = f"{mbti_type}_{safe_name}.md"
                    
                    all_files.append((filename, file_content))
                    
                print(f"   Processed {mbti_type}: {len(data_rows)} attractions")
    
    print(f"\n📊 Created {len(all_files)} individual attraction files")
    return all_files

def upload_individual_files(files: List[tuple], bucket_name: str):
    """Upload individual files to S3."""
    
    print(f"\n☁️ Uploading individual attraction files...")
    
    s3 = boto3.client('s3', region_name='us-east-1')
    uploaded_files = []
    
    for filename, content in files:
        s3_key = f"mbti_individual/{filename}"
        
        try:
            s3.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=content.encode('utf-8'),
                ContentType='text/markdown'
            )
            uploaded_files.append(s3_key)
            print(f"   ✅ {filename} ({len(content)} chars)")
        except Exception as e:
            print(f"   ❌ Error uploading {filename}: {e}")
    
    return uploaded_files

def update_data_source_for_individual_files():
    """Update the data source to use individual files."""
    
    print("\n🔄 Updating data source for individual files...")
    
    import subprocess
    
    cmd = [
        'aws', 'bedrock-agent', 'update-data-source',
        '--knowledge-base-id', 'RCWW86CLM9',
        '--data-source-id', 'JJSNBHN3VI',
        '--name', 'MBTI-Individual-Attractions',
        '--data-source-configuration', 
        '{"type": "S3","s3Configuration": {"bucketArn": "arn:aws:s3:::mbti-knowledgebase-209803798463-us-east-1","inclusionPrefixes": ["mbti_individual/"]}}',
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
    """Start ingestion job."""
    
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

def main():
    """Main process."""
    
    print("🎯 Individual MBTI Attraction Files Creator")
    print("=" * 50)
    
    # Create individual files
    files = create_individual_attraction_files()
    
    if not files:
        print("❌ No files created. Exiting.")
        return
    
    bucket_name = 'mbti-knowledgebase-209803798463-us-east-1'
    
    # Upload files
    uploaded = upload_individual_files(files, bucket_name)
    
    if uploaded:
        print(f"\n📊 Upload Summary:")
        print(f"   Files created: {len(files)}")
        print(f"   Files uploaded: {len(uploaded)}")
        print(f"   Average file size: {sum(len(content) for _, content in files) // len(files)} chars")
        
        # Update data source
        if update_data_source_for_individual_files():
            # Start ingestion
            job_id = start_ingestion_job()
            
            if job_id:
                print(f"\n🎉 Success! Individual attraction files created and ingestion started.")
                print(f"Monitor job: {job_id}")
                print("\nEach attraction is now a separate document for precise retrieval!")
            else:
                print("\n⚠️ Files uploaded but ingestion failed to start")
        else:
            print("\n⚠️ Files uploaded but data source update failed")
    else:
        print("\n❌ File upload failed")

if __name__ == "__main__":
    main()