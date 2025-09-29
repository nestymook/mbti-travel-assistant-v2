#!/usr/bin/env python3
"""
Check current knowledge base structure
"""

import boto3

def check_kb_structure():
    """Check the current structure of the knowledge base."""
    
    print("🔍 Checking Knowledge Base Structure")
    print("=" * 50)
    
    # Initialize S3 client
    s3_client = boto3.client('s3', region_name='us-east-1')
    bucket_name = "mbti-knowledgebase-209803798463-us-east-1"
    
    try:
        # List all objects in the bucket
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        
        if 'Contents' not in response:
            print("❌ No files found in bucket")
            return
        
        files = [obj['Key'] for obj in response['Contents']]
        print(f"✅ Found {len(files)} files")
        
        # Analyze current structure
        print(f"\n📁 Current Files:")
        for file in sorted(files):
            print(f"   {file}")
        
        # Check if already organized
        organized_files = [f for f in files if '/' in f and len(f.split('/')) >= 3]
        flat_files = [f for f in files if '/' not in f]
        
        print(f"\n📊 Structure Analysis:")
        print(f"   Organized files (with folders): {len(organized_files)}")
        print(f"   Flat files (no folders): {len(flat_files)}")
        
        if organized_files:
            print(f"\n📁 Organized Structure Sample:")
            for file in organized_files[:10]:
                print(f"   {file}")
        
        if flat_files:
            print(f"\n📄 Flat Files Sample:")
            for file in flat_files[:10]:
                print(f"   {file}")
        
        return len(organized_files) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    is_organized = check_kb_structure()
    
    if is_organized:
        print(f"\n✅ Knowledge base appears to be organized with folders")
        print("Ready to test folder-based search strategies")
    else:
        print(f"\n⚠️ Knowledge base uses flat file structure")
        print("Consider reorganizing with hierarchical folders for better search performance")