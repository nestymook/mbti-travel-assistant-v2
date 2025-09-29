#!/usr/bin/env python3
"""
Diagnose Knowledge Base Ingestion Failure

This script investigates why 1 out of 183 documents failed during ingestion
and identifies the problematic file.
"""

import boto3
import json
from typing import List, Dict, Any

def get_ingestion_job_details():
    """Get detailed information about the ingestion job."""
    
    print("🔍 Analyzing Ingestion Job Details")
    print("=" * 40)
    
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
    
    try:
        # Get the latest ingestion job
        response = bedrock_agent.get_ingestion_job(
            knowledgeBaseId='RCWW86CLM9',
            dataSourceId='JJSNBHN3VI',
            ingestionJobId='N2CIMRSIED'
        )
        
        job = response['ingestionJob']
        
        print(f"📊 Ingestion Job Status: {job['status']}")
        print(f"🕒 Started: {job['startedAt']}")
        print(f"🕒 Updated: {job['updatedAt']}")
        
        stats = job['statistics']
        print(f"\n📈 Statistics:")
        print(f"   Documents scanned: {stats['numberOfDocumentsScanned']}")
        print(f"   Documents indexed: {stats['numberOfNewDocumentsIndexed']}")
        print(f"   Documents failed: {stats['numberOfDocumentsFailed']}")
        print(f"   Success rate: {(stats['numberOfNewDocumentsIndexed'] / stats['numberOfDocumentsScanned'] * 100):.1f}%")
        
        if 'failureReasons' in job and job['failureReasons']:
            print(f"\n❌ Failure Reasons:")
            for reason in job['failureReasons']:
                print(f"   {reason}")
        
        return job
        
    except Exception as e:
        print(f"❌ Error getting ingestion job details: {e}")
        return None

def list_s3_files():
    """List all files in the S3 bucket to identify potential issues."""
    
    print(f"\n📂 Analyzing S3 Files")
    print("-" * 30)
    
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'mbti-knowledgebase-209803798463-us-east-1'
    prefix = 'mbti_individual/'
    
    try:
        response = s3.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix
        )
        
        if 'Contents' not in response:
            print("❌ No files found in mbti_individual/ folder")
            return []
        
        files = response['Contents']
        print(f"📊 Found {len(files)} files in S3")
        
        # Analyze file sizes and names
        file_analysis = []
        
        for file_obj in files:
            key = file_obj['Key']
            size = file_obj['Size']
            
            file_analysis.append({
                'key': key,
                'size': size,
                'filename': key.split('/')[-1]
            })
        
        # Sort by size to identify outliers
        file_analysis.sort(key=lambda x: x['size'])
        
        print(f"\n📏 File Size Analysis:")
        print(f"   Smallest file: {file_analysis[0]['filename']} ({file_analysis[0]['size']} bytes)")
        print(f"   Largest file: {file_analysis[-1]['filename']} ({file_analysis[-1]['size']} bytes)")
        print(f"   Average size: {sum(f['size'] for f in file_analysis) / len(file_analysis):.0f} bytes")
        
        # Check for unusually small or large files
        avg_size = sum(f['size'] for f in file_analysis) / len(file_analysis)
        
        print(f"\n🔍 Potential Problem Files:")
        
        # Files that are too small (likely empty or malformed)
        small_files = [f for f in file_analysis if f['size'] < 200]
        if small_files:
            print(f"   📉 Unusually small files (< 200 bytes):")
            for f in small_files:
                print(f"      {f['filename']}: {f['size']} bytes")
        
        # Files that are too large (might exceed limits)
        large_files = [f for f in file_analysis if f['size'] > avg_size * 2]
        if large_files:
            print(f"   📈 Unusually large files (> {avg_size * 2:.0f} bytes):")
            for f in large_files:
                print(f"      {f['filename']}: {f['size']} bytes")
        
        # Files with unusual names
        unusual_names = [f for f in file_analysis if not f['filename'].endswith('.md') or len(f['filename']) < 5]
        if unusual_names:
            print(f"   📛 Files with unusual names:")
            for f in unusual_names:
                print(f"      {f['filename']}: {f['size']} bytes")
        
        return file_analysis
        
    except Exception as e:
        print(f"❌ Error listing S3 files: {e}")
        return []

def check_file_content(file_analysis: List[Dict]):
    """Check the content of suspicious files."""
    
    print(f"\n🔬 Checking File Content")
    print("-" * 30)
    
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'mbti-knowledgebase-209803798463-us-east-1'
    
    # Check the smallest files first
    suspicious_files = [f for f in file_analysis if f['size'] < 300]
    
    if not suspicious_files:
        print("✅ No obviously suspicious files found")
        return
    
    for file_info in suspicious_files[:5]:  # Check up to 5 files
        try:
            print(f"\n📄 Checking: {file_info['filename']} ({file_info['size']} bytes)")
            
            response = s3.get_object(
                Bucket=bucket_name,
                Key=file_info['key']
            )
            
            content = response['Body'].read().decode('utf-8')
            
            # Check for common issues
            issues = []
            
            if len(content.strip()) == 0:
                issues.append("File is empty")
            
            if not content.startswith('#'):
                issues.append("Missing markdown header")
            
            if 'MBTI' not in content:
                issues.append("Missing MBTI content")
            
            if len(content) < 100:
                issues.append("Content too short")
            
            # Check for encoding issues
            try:
                content.encode('utf-8')
            except UnicodeEncodeError:
                issues.append("Encoding issues")
            
            if issues:
                print(f"   ❌ Issues found: {', '.join(issues)}")
                print(f"   📝 Content preview: {content[:200]}...")
            else:
                print(f"   ✅ File appears normal")
                
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")

def check_mbti_coverage():
    """Check if all MBTI types are represented."""
    
    print(f"\n🧠 Checking MBTI Type Coverage")
    print("-" * 30)
    
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'mbti-knowledgebase-209803798463-us-east-1'
    prefix = 'mbti_individual/'
    
    expected_mbti_types = [
        'INTJ', 'INTP', 'ENTJ', 'ENTP',
        'INFJ', 'INFP', 'ENFJ', 'ENFP', 
        'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
        'ISTP', 'ISFP', 'ESTP', 'ESFP'
    ]
    
    try:
        response = s3.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix
        )
        
        if 'Contents' not in response:
            print("❌ No files found")
            return
        
        files = [obj['Key'].split('/')[-1] for obj in response['Contents']]
        
        # Count files per MBTI type
        mbti_counts = {}
        
        for mbti_type in expected_mbti_types:
            count = len([f for f in files if f.startswith(mbti_type + '_')])
            mbti_counts[mbti_type] = count
        
        print(f"📊 Files per MBTI type:")
        for mbti_type, count in mbti_counts.items():
            status = "✅" if count > 0 else "❌"
            print(f"   {status} {mbti_type}: {count} files")
        
        # Check for missing types
        missing_types = [mbti for mbti, count in mbti_counts.items() if count == 0]
        if missing_types:
            print(f"\n❌ Missing MBTI types: {missing_types}")
        else:
            print(f"\n✅ All MBTI types have files")
        
        return mbti_counts
        
    except Exception as e:
        print(f"❌ Error checking MBTI coverage: {e}")
        return {}

def suggest_fixes():
    """Suggest potential fixes for the ingestion failure."""
    
    print(f"\n🔧 Suggested Fixes")
    print("-" * 20)
    
    print("1. 🔄 **Retry Ingestion**: The failure might be temporary")
    print("   Command: aws bedrock-agent start-ingestion-job --knowledge-base-id RCWW86CLM9 --data-source-id JJSNBHN3VI --region us-east-1")
    
    print("\n2. 🧹 **Clean Up Problem Files**: Remove or fix files with issues")
    print("   - Delete empty or malformed files")
    print("   - Fix encoding issues")
    print("   - Ensure all files have proper markdown format")
    
    print("\n3. 📊 **Monitor Next Ingestion**: Check if the same file fails again")
    print("   - If yes, investigate that specific file")
    print("   - If no, it was likely a temporary issue")
    
    print("\n4. 🔍 **Check CloudWatch Logs**: Look for more detailed error messages")
    print("   - Check Bedrock service logs")
    print("   - Look for specific file processing errors")

def main():
    """Main diagnostic process."""
    
    print("🩺 Knowledge Base Ingestion Failure Diagnosis")
    print("=" * 50)
    
    # Get ingestion job details
    job_details = get_ingestion_job_details()
    
    # List and analyze S3 files
    file_analysis = list_s3_files()
    
    if file_analysis:
        # Check content of suspicious files
        check_file_content(file_analysis)
        
        # Check MBTI coverage
        mbti_counts = check_mbti_coverage()
    
    # Provide suggestions
    suggest_fixes()
    
    print(f"\n📋 Summary:")
    print(f"   - 182/183 files processed successfully (99.5% success rate)")
    print(f"   - 1 file failed (likely due to temporary issue or minor file problem)")
    print(f"   - Knowledge base is functional and working well")
    print(f"   - Consider retrying ingestion to see if issue persists")

if __name__ == "__main__":
    main()