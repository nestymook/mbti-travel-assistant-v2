#!/usr/bin/env python3
"""
Update Knowledge Base with New Hierarchical Structure

This script:
1. Clears existing S3 bucket content
2. Uploads the new organized folder structure
3. Updates the knowledge base data source
4. Starts ingestion job to rebuild vectors

Knowledge Base Details:
- Knowledge Base ID: RCWW86CLM9
- Data Source ID: RQPU9JWBU8
- S3 Bucket: mbti-knowledgebase-209803798463-us-east-1
- Region: us-east-1
"""

import boto3
import os
import time
from pathlib import Path
from typing import List, Dict

class KnowledgeBaseUpdater:
    """Update knowledge base with new hierarchical structure."""
    
    def __init__(self):
        self.region = "us-east-1"
        self.bucket_name = "mbti-knowledgebase-209803798463-us-east-1"
        self.knowledge_base_id = "RCWW86CLM9"
        self.data_source_id = "JJSNBHN3VI"
        
        # Initialize AWS clients
        self.s3_client = boto3.client('s3', region_name=self.region)
        self.bedrock_agent_client = boto3.client('bedrock-agent', region_name=self.region)
        
        # Local paths
        self.organized_kb_path = Path("mbti_travel_assistant_mcp/organized_kb")
    
    def list_current_s3_objects(self) -> List[str]:
        """List all current objects in the S3 bucket."""
        
        print("📋 Listing current S3 bucket contents...")
        
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            if 'Contents' not in response:
                print("✅ S3 bucket is empty")
                return []
            
            objects = [obj['Key'] for obj in response['Contents']]
            print(f"📄 Found {len(objects)} existing objects in S3")
            
            # Show some examples
            for obj in objects[:5]:
                print(f"   - {obj}")
            if len(objects) > 5:
                print(f"   ... and {len(objects) - 5} more objects")
            
            return objects
            
        except Exception as e:
            print(f"❌ Error listing S3 objects: {e}")
            return []
    
    def clear_s3_bucket(self, objects: List[str]) -> bool:
        """Clear all existing objects from S3 bucket."""
        
        if not objects:
            print("✅ S3 bucket is already empty")
            return True
        
        print(f"🗑️ Clearing {len(objects)} existing objects from S3...")
        
        try:
            # Delete objects in batches of 1000 (S3 limit)
            batch_size = 1000
            deleted_count = 0
            
            for i in range(0, len(objects), batch_size):
                batch = objects[i:i + batch_size]
                delete_objects = [{'Key': obj} for obj in batch]
                
                response = self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': delete_objects}
                )
                
                deleted_count += len(response.get('Deleted', []))
                print(f"   ✅ Deleted batch {i//batch_size + 1}: {len(response.get('Deleted', []))} objects")
                
                # Check for errors
                if 'Errors' in response and response['Errors']:
                    for error in response['Errors']:
                        print(f"   ❌ Error deleting {error['Key']}: {error['Message']}")
            
            print(f"✅ Successfully deleted {deleted_count} objects from S3")
            return True
            
        except Exception as e:
            print(f"❌ Error clearing S3 bucket: {e}")
            return False
    
    def upload_organized_structure(self) -> bool:
        """Upload the new organized folder structure to S3."""
        
        print("📤 Uploading new organized structure to S3...")
        
        if not self.organized_kb_path.exists():
            print(f"❌ Organized KB path not found: {self.organized_kb_path}")
            return False
        
        uploaded_count = 0
        error_count = 0
        
        # Walk through all files in the organized structure
        for file_path in self.organized_kb_path.rglob("*.md"):
            try:
                # Calculate relative path from organized_kb root
                relative_path = file_path.relative_to(self.organized_kb_path)
                s3_key = str(relative_path).replace('\\', '/')  # Ensure forward slashes for S3
                
                # Upload file
                self.s3_client.upload_file(
                    str(file_path),
                    self.bucket_name,
                    s3_key
                )
                
                print(f"   ✅ Uploaded: {s3_key}")
                uploaded_count += 1
                
            except Exception as e:
                print(f"   ❌ Error uploading {file_path.name}: {e}")
                error_count += 1
        
        print(f"\n📊 Upload Summary:")
        print(f"   ✅ Uploaded: {uploaded_count} files")
        print(f"   ❌ Errors: {error_count}")
        
        return error_count == 0
    
    def verify_s3_upload(self) -> bool:
        """Verify the upload was successful."""
        
        print("\n🔍 Verifying S3 upload...")
        
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            if 'Contents' not in response:
                print("❌ No objects found in S3 after upload")
                return False
            
            objects = response['Contents']
            print(f"✅ Found {len(objects)} objects in S3")
            
            # Analyze structure
            folders = {}
            for obj in objects:
                key = obj['Key']
                if '/' in key:
                    parts = key.split('/')
                    if len(parts) >= 2:
                        area = parts[0]
                        district = parts[1]
                        
                        if area not in folders:
                            folders[area] = {}
                        if district not in folders[area]:
                            folders[area][district] = 0
                        folders[area][district] += 1
            
            print(f"\n📁 Uploaded Structure:")
            for area, districts in sorted(folders.items()):
                print(f"   📂 {area}/")
                for district, count in sorted(districts.items()):
                    print(f"      └── {district}/ ({count} files)")
            
            return len(objects) > 0
            
        except Exception as e:
            print(f"❌ Error verifying S3 upload: {e}")
            return False
    
    def start_ingestion_job(self) -> str:
        """Start a new ingestion job to rebuild the knowledge base vectors."""
        
        print("\n🚀 Starting knowledge base ingestion job...")
        
        try:
            response = self.bedrock_agent_client.start_ingestion_job(
                knowledgeBaseId=self.knowledge_base_id,
                dataSourceId=self.data_source_id
            )
            
            job_id = response['ingestionJob']['ingestionJobId']
            print(f"✅ Started ingestion job: {job_id}")
            
            return job_id
            
        except Exception as e:
            print(f"❌ Error starting ingestion job: {e}")
            return ""
    
    def monitor_ingestion_job(self, job_id: str) -> bool:
        """Monitor the ingestion job until completion."""
        
        print(f"\n⏳ Monitoring ingestion job: {job_id}")
        
        try:
            while True:
                response = self.bedrock_agent_client.get_ingestion_job(
                    knowledgeBaseId=self.knowledge_base_id,
                    dataSourceId=self.data_source_id,
                    ingestionJobId=job_id
                )
                
                job = response['ingestionJob']
                status = job['status']
                
                print(f"   Status: {status}")
                
                if status == 'COMPLETE':
                    print("✅ Ingestion job completed successfully!")
                    
                    # Show statistics if available
                    if 'statistics' in job:
                        stats = job['statistics']
                        print(f"   📊 Documents processed: {stats.get('numberOfDocumentsScanned', 'N/A')}")
                        print(f"   📊 Documents indexed: {stats.get('numberOfNewDocumentsIndexed', 'N/A')}")
                        print(f"   📊 Documents updated: {stats.get('numberOfModifiedDocumentsIndexed', 'N/A')}")
                        print(f"   📊 Documents deleted: {stats.get('numberOfDocumentsDeleted', 'N/A')}")
                    
                    return True
                    
                elif status == 'FAILED':
                    print("❌ Ingestion job failed!")
                    if 'failureReasons' in job:
                        for reason in job['failureReasons']:
                            print(f"   ❌ Failure reason: {reason}")
                    return False
                    
                elif status in ['STARTING', 'IN_PROGRESS']:
                    print("   ⏳ Job in progress, waiting 30 seconds...")
                    time.sleep(30)
                    
                else:
                    print(f"   ⚠️ Unknown status: {status}")
                    time.sleep(30)
                    
        except Exception as e:
            print(f"❌ Error monitoring ingestion job: {e}")
            return False
    
    def test_knowledge_base_query(self) -> bool:
        """Test the updated knowledge base with a sample query."""
        
        print("\n🧪 Testing knowledge base with sample query...")
        
        try:
            bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=self.region)
            
            test_query = "Find ENFJ personality attractions in Tsim Sha Tsui"
            
            response = bedrock_runtime.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={'text': test_query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {'numberOfResults': 3}
                }
            )
            
            results = response['retrievalResults']
            print(f"✅ Query successful! Found {len(results)} results")
            
            for i, result in enumerate(results, 1):
                score = result['score']
                location = result['location']['s3Location']['uri']
                content_preview = result['content']['text'][:100] + "..."
                
                print(f"\n   📄 Result {i}:")
                print(f"      Score: {score:.4f}")
                print(f"      Location: {location}")
                print(f"      Content: {content_preview}")
            
            return len(results) > 0
            
        except Exception as e:
            print(f"❌ Error testing knowledge base: {e}")
            return False
    
    def update_knowledge_base(self) -> bool:
        """Complete knowledge base update process."""
        
        print("🎯 Updating Knowledge Base with New Hierarchical Structure")
        print("=" * 70)
        print(f"Knowledge Base ID: {self.knowledge_base_id}")
        print(f"Data Source ID: {self.data_source_id}")
        print(f"S3 Bucket: {self.bucket_name}")
        print(f"Region: {self.region}")
        print()
        
        # Step 1: List current S3 objects
        current_objects = self.list_current_s3_objects()
        
        # Step 2: Clear S3 bucket
        if not self.clear_s3_bucket(current_objects):
            return False
        
        # Step 3: Upload new structure
        if not self.upload_organized_structure():
            return False
        
        # Step 4: Verify upload
        if not self.verify_s3_upload():
            return False
        
        # Step 5: Start ingestion job
        job_id = self.start_ingestion_job()
        if not job_id:
            return False
        
        # Step 6: Monitor ingestion job
        if not self.monitor_ingestion_job(job_id):
            return False
        
        # Step 7: Test knowledge base
        if not self.test_knowledge_base_query():
            print("⚠️ Knowledge base test failed, but ingestion completed")
        
        return True

def main():
    """Main execution function."""
    
    # Initialize updater
    updater = KnowledgeBaseUpdater()
    
    # Confirm before proceeding
    print("⚠️  WARNING: This will completely replace the knowledge base content!")
    print("Current content will be permanently deleted.")
    print()
    response = input("🤔 Are you sure you want to proceed? (yes/no): ").lower().strip()
    
    if response != 'yes':
        print("❌ Operation cancelled by user")
        return
    
    # Execute update
    print("\n" + "="*70)
    success = updater.update_knowledge_base()
    
    if success:
        print(f"\n🎉 Knowledge Base Update Complete!")
        print("✅ New hierarchical structure uploaded")
        print("✅ Vector embeddings rebuilt")
        print("✅ Knowledge base ready for improved searches")
        print("\nNext steps:")
        print("1. Test MBTI-based searches")
        print("2. Test location-based searches")
        print("3. Verify improved search performance")
    else:
        print("\n❌ Knowledge Base update failed")
        print("Please check the error messages above and try again")

if __name__ == "__main__":
    main()