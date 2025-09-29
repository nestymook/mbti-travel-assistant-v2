#!/usr/bin/env python3
"""
Convert MBTI Tourist Spots to Alternative Formats

This script converts the table data to different formats that work better
with no-chunking strategy while preserving all structured information.
"""

import boto3
import json
import csv
import re
from pathlib import Path
from typing import Dict, List, Any

def parse_table_data():
    """Parse the original markdown table data."""
    
    print("📂 Parsing original table data...")
    
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
        return {}
    
    # MBTI types to extract
    mbti_types = [
        'INTJ', 'INTP', 'ENTJ', 'ENTP',
        'INFJ', 'INFP', 'ENFJ', 'ENFP', 
        'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
        'ISTP', 'ISFP', 'ESTP', 'ESFP'
    ]
    
    all_data = {}
    
    # Parse each MBTI section
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
            
            # Parse table rows
            attractions = []
            lines = section_content.split('\n')
            
            # Find table header and data rows
            in_table = False
            headers = []
            
            for line in lines:
                line = line.strip()
                if '|' in line and 'Tourist Spot' in line:
                    # This is the header row
                    headers = [h.strip() for h in line.split('|') if h.strip()]
                    in_table = True
                elif '|' in line and '---' in line:
                    # Skip separator row
                    continue
                elif '|' in line and in_table and len(line.split('|')) >= 5:
                    # This is a data row
                    row_data = [cell.strip() for cell in line.split('|') if cell.strip() or cell == '']
                    
                    if len(row_data) >= len(headers):
                        attraction = {}
                        for i, header in enumerate(headers):
                            if i < len(row_data):
                                attraction[header] = row_data[i] if row_data[i] else ""
                        
                        # Add MBTI type
                        attraction['MBTI_Type'] = mbti_type
                        attractions.append(attraction)
            
            all_data[mbti_type] = attractions
            print(f"   Parsed {mbti_type}: {len(attractions)} attractions")
    
    return all_data

def create_structured_markdown_format(data: Dict[str, List[Dict]]) -> List[tuple]:
    """Create structured markdown format - one attraction per file."""
    
    print("\n📝 Creating structured markdown format...")
    
    files = []
    
    for mbti_type, attractions in data.items():
        for i, attraction in enumerate(attractions, 1):
            # Create a structured markdown document for each attraction
            content = f"""# {attraction.get('Tourist Spot', 'Unknown Attraction')}

## MBTI Personality Match
**Type:** {mbti_type}  
**Suitability:** {attraction.get('Description', 'Perfect match for this personality type')}

## Location Information
**Address:** {attraction.get('Address', 'Address not specified')}  
**District:** {attraction.get('District', 'District not specified')}  
**Area:** {attraction.get('Location', 'Location not specified')}

## Operating Hours
**Weekdays (Mon-Fri):** {attraction.get('Operating Hours (Mon-Fri)', 'Hours not specified')}  
**Weekends (Sat-Sun):** {attraction.get('Operating Hours (Sat-Sun)', 'Hours not specified')}  
**Public Holidays:** {attraction.get('Operating Hours (Public Holiday)', 'Hours not specified')}

## Additional Information
**Contact/Remarks:** {attraction.get('Remarks', 'No additional information')}  
**Full Day Info:** {attraction.get('Full Day', 'Not specified')}

## Keywords
MBTI: {mbti_type}, Hong Kong, Tourist Attraction, {attraction.get('District', '')}, {attraction.get('Location', '')}
"""
            
            filename = f"{mbti_type}_{i:02d}_{attraction.get('Tourist Spot', 'Unknown').replace(' ', '_').replace('/', '_')}.md"
            files.append((filename, content))
    
    print(f"   Created {len(files)} structured markdown files")
    return files

def create_json_format(data: Dict[str, List[Dict]]) -> List[tuple]:
    """Create JSON format - one MBTI type per file."""
    
    print("\n📊 Creating JSON format...")
    
    files = []
    
    for mbti_type, attractions in data.items():
        # Create comprehensive JSON structure
        json_data = {
            "mbti_type": mbti_type,
            "personality_description": f"{mbti_type} personality type attractions in Hong Kong",
            "total_attractions": len(attractions),
            "attractions": []
        }
        
        for attraction in attractions:
            structured_attraction = {
                "name": attraction.get('Tourist Spot', ''),
                "mbti_match": mbti_type,
                "description": attraction.get('Description', ''),
                "location": {
                    "address": attraction.get('Address', ''),
                    "district": attraction.get('District', ''),
                    "area": attraction.get('Location', '')
                },
                "operating_hours": {
                    "weekdays": attraction.get('Operating Hours (Mon-Fri)', ''),
                    "weekends": attraction.get('Operating Hours (Sat-Sun)', ''),
                    "holidays": attraction.get('Operating Hours (Public Holiday)', '')
                },
                "contact_info": attraction.get('Remarks', ''),
                "additional_info": attraction.get('Full Day', ''),
                "keywords": [mbti_type, "Hong Kong", "Tourist Attraction", attraction.get('District', '')]
            }
            json_data["attractions"].append(structured_attraction)
        
        content = json.dumps(json_data, indent=2, ensure_ascii=False)
        filename = f"{mbti_type}_attractions.json"
        files.append((filename, content))
    
    print(f"   Created {len(files)} JSON files")
    return files

def create_yaml_format(data: Dict[str, List[Dict]]) -> List[tuple]:
    """Create YAML format - one MBTI type per file."""
    
    print("\n📋 Creating YAML format...")
    
    files = []
    
    for mbti_type, attractions in data.items():
        # Create YAML content
        yaml_content = f"""# {mbti_type} Personality Type - Hong Kong Tourist Attractions

mbti_type: {mbti_type}
personality_description: "{mbti_type} personality type attractions in Hong Kong"
total_attractions: {len(attractions)}

attractions:
"""
        
        for attraction in attractions:
            yaml_content += f"""  - name: "{attraction.get('Tourist Spot', '')}"
    mbti_match: {mbti_type}
    description: "{attraction.get('Description', '')}"
    location:
      address: "{attraction.get('Address', '')}"
      district: "{attraction.get('District', '')}"
      area: "{attraction.get('Location', '')}"
    operating_hours:
      weekdays: "{attraction.get('Operating Hours (Mon-Fri)', '')}"
      weekends: "{attraction.get('Operating Hours (Sat-Sun)', '')}"
      holidays: "{attraction.get('Operating Hours (Public Holiday)', '')}"
    contact_info: "{attraction.get('Remarks', '')}"
    additional_info: "{attraction.get('Full Day', '')}"
    keywords: [{mbti_type}, "Hong Kong", "Tourist Attraction", "{attraction.get('District', '')}"]

"""
        
        filename = f"{mbti_type}_attractions.yaml"
        files.append((filename, yaml_content))
    
    print(f"   Created {len(files)} YAML files")
    return files

def create_csv_format(data: Dict[str, List[Dict]]) -> List[tuple]:
    """Create CSV format - one MBTI type per file."""
    
    print("\n📈 Creating CSV format...")
    
    files = []
    
    for mbti_type, attractions in data.items():
        if not attractions:
            continue
        
        # Create CSV content
        import io
        output = io.StringIO()
        
        # Get all possible fieldnames
        fieldnames = set()
        for attraction in attractions:
            fieldnames.update(attraction.keys())
        fieldnames = sorted(list(fieldnames))
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for attraction in attractions:
            writer.writerow(attraction)
        
        content = output.getvalue()
        filename = f"{mbti_type}_attractions.csv"
        files.append((filename, content))
    
    print(f"   Created {len(files)} CSV files")
    return files

def upload_files_to_s3(files: List[tuple], format_name: str, bucket_name: str):
    """Upload files to S3."""
    
    print(f"\n☁️ Uploading {format_name} files to S3...")
    
    s3 = boto3.client('s3', region_name='us-east-1')
    uploaded_files = []
    
    for filename, content in files:
        s3_key = f"mbti_{format_name.lower()}/{filename}"
        
        try:
            s3.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=content.encode('utf-8'),
                ContentType='text/plain'
            )
            uploaded_files.append(s3_key)
            print(f"   ✅ {s3_key} ({len(content)} chars)")
        except Exception as e:
            print(f"   ❌ Error uploading {s3_key}: {e}")
    
    return uploaded_files

def main():
    """Main conversion process."""
    
    print("🎯 MBTI Tourist Spots Format Converter")
    print("=" * 50)
    
    # Parse original data
    data = parse_table_data()
    
    if not data:
        print("❌ No data parsed. Exiting.")
        return
    
    bucket_name = 'mbti-knowledgebase-209803798463-us-east-1'
    
    # Create different formats
    formats = {
        "Structured_Markdown": create_structured_markdown_format(data),
        "JSON": create_json_format(data),
        "YAML": create_yaml_format(data),
        "CSV": create_csv_format(data)
    }
    
    # Upload each format
    all_uploaded = {}
    
    for format_name, files in formats.items():
        uploaded = upload_files_to_s3(files, format_name, bucket_name)
        all_uploaded[format_name] = uploaded
    
    # Summary
    print(f"\n📊 Conversion Summary:")
    for format_name, uploaded in all_uploaded.items():
        print(f"   {format_name}: {len(uploaded)} files uploaded")
    
    print(f"\n🎉 All formats created and uploaded!")
    print(f"\nS3 Prefixes created:")
    for format_name in formats.keys():
        print(f"   - mbti_{format_name.lower()}/")
    
    return all_uploaded

if __name__ == "__main__":
    main()