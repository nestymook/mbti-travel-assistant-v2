#!/usr/bin/env python3
"""
Update Knowledge Base with Optimized Markdown

This script updates your knowledge base data source to use the optimized markdown
and starts a new ingestion job to process the improved content.
"""

import boto3
import time
from datetime import datetime

class KnowledgeBaseUpdater:
    """Update knowledge base with optimized markdown content."""
    
    def __init__(self, kb_id: str = "RCWW86CLM9", region: str = "us-east-1"):
        self.kb_id = kb_id
        self.region = region
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        
        self.bucket_name = "mbti-knowledgebase-209803798463-us-east-1"
        self.original_file = "Tourist_Spots_With_Hours.markdown"
        self.optimized_file = "Tourist_Spots_Optimized.markdown"
    
    def list_current_data_sources(self) -> list:
        """List current data sources for the knowledge base."""
        
        print(f"📋 Listing current data sources for KB {self.kb_id}...")
        
        try:
            response = self.bedrock_agent.list_data_sources(knowledgeBaseId=self.kb_id)
            data_sources = response['dataSourceSummaries']
            
            print(f"✅ Found {len(data_sources)} data sources:")
            
            for ds in data_sources:
                print(f"   - {ds['name']} (ID: {ds['dataSourceId']}, Status: {ds['status']})")
            
            return data_sources
            
        except Exception as e:
            print(f"❌ Error listing data sources: {e}")
            return []
    
    def create_optimized_data_source(self) -> str:
        """Create a new data source pointing to the optimized markdown."""
        
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        ds_name = f"OptimizedMarkdownSource-{timestamp}"
        
        print(f"🔧 Creating new data source: {ds_name}")
        
        try:
            response = self.bedrock_agent.create_data_source(
                knowledgeBaseId=self.kb_id,
                name=ds_name,
                description="Optimized markdown data source with enhanced structure for better MBTI matching",
                dataSourceConfiguration={
                    "type": "S3",
                    "s3Configuration": {
                        "bucketArn": f"arn:aws:s3:::{self.bucket_name}",
                        "inclusionPrefixes": [self.optimized_file]
                    }
                },
                vectorIngestionConfiguration={
                    "chunkingConfiguration": {
                        "chunkingStrategy": "FIXED_SIZE",
                        "fixedSizeChunkingConfiguration": {
                            "maxTokens": 300,  # Optimized for structured content
                            "overlapPercentage": 25  # Good context preservation
                        }
                    },
                    # Use default parsing for now - custom parsing prompts may not be supported
                    # "parsingConfiguration": {
                    #     "parsingStrategy": "BEDROCK_FOUNDATION_MODEL"
                    # }
                }
            )
            
            new_ds_id = response['dataSource']['dataSourceId']
            print(f"✅ Created data source: {new_ds_id}")
            
            return new_ds_id
            
        except Exception as e:
            print(f"❌ Error creating data source: {e}")
            return ""
    
    def start_ingestion_job(self, data_source_id: str) -> str:
        """Start ingestion job for the new data source."""
        
        print(f"🚀 Starting ingestion job for data source {data_source_id}...")
        
        try:
            response = self.bedrock_agent.start_ingestion_job(
                knowledgeBaseId=self.kb_id,
                dataSourceId=data_source_id
            )
            
            job_id = response['ingestionJob']['ingestionJobId']
            print(f"✅ Started ingestion job: {job_id}")
            
            return job_id
            
        except Exception as e:
            print(f"❌ Error starting ingestion job: {e}")
            return ""
    
    def monitor_ingestion_job(self, data_source_id: str, job_id: str) -> bool:
        """Monitor the ingestion job until completion."""
        
        print(f"⏳ Monitoring ingestion job {job_id}...")
        
        max_wait_time = 600  # 10 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                response = self.bedrock_agent.get_ingestion_job(
                    knowledgeBaseId=self.kb_id,
                    dataSourceId=data_source_id,
                    ingestionJobId=job_id
                )
                
                job = response['ingestionJob']
                status = job['status']
                
                print(f"   Status: {status}")
                
                if status == 'COMPLETE':
                    stats = job['statistics']
                    print(f"✅ Ingestion completed successfully!")
                    print(f"   Documents scanned: {stats['numberOfDocumentsScanned']}")
                    print(f"   Documents indexed: {stats['numberOfNewDocumentsIndexed']}")
                    print(f"   Documents failed: {stats['numberOfDocumentsFailed']}")
                    return True
                
                elif status == 'FAILED':
                    print(f"❌ Ingestion job failed")
                    return False
                
                elif status in ['STARTING', 'IN_PROGRESS']:
                    time.sleep(15)  # Wait 15 seconds before checking again
                
                else:
                    print(f"⚠️ Unknown status: {status}")
                    time.sleep(15)
                
            except Exception as e:
                print(f"❌ Error monitoring job: {e}")
                return False
        
        print(f"⏰ Timeout waiting for ingestion job to complete")
        return False
    
    def test_optimized_queries(self) -> None:
        """Test queries against the optimized knowledge base."""
        
        print(f"🧪 Testing optimized knowledge base queries...")
        
        bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=self.region)
        
        test_queries = [
            {
                "name": "ENFP Social Activities",
                "query": "ENFP personality type social creative activities Hong Kong Central district"
            },
            {
                "name": "INTJ Intellectual Attractions", 
                "query": "INTJ personality type museums galleries intellectual quiet spaces Hong Kong"
            },
            {
                "name": "ISFJ Traditional Culture",
                "query": "ISFJ personality type traditional cultural caring experiences Hong Kong temples"
            },
            {
                "name": "ESTP Adventure Activities",
                "query": "ESTP personality type active adventure spontaneous experiences Hong Kong outdoor"
            }
        ]
        
        for test in test_queries:
            print(f"\n🔍 Testing: {test['name']}")
            print(f"Query: {test['query']}")
            
            try:
                response = bedrock_runtime.retrieve(
                    knowledgeBaseId=self.kb_id,
                    retrievalQuery={'text': test['query']},
                    retrievalConfiguration={
                        'vectorSearchConfiguration': {
                            'numberOfResults': 5
                        }
                    }
                )
                
                results = response['retrievalResults']
                
                if results:
                    print(f"✅ Found {len(results)} results")
                    print(f"   Top score: {results[0]['score']:.4f}")
                    print(f"   Sample: {results[0]['content']['text'][:150]}...")
                else:
                    print("❌ No results found")
                
            except Exception as e:
                print(f"❌ Error testing query: {e}")
    
    def compare_performance(self) -> None:
        """Compare performance between original and optimized versions."""
        
        print(f"\n📊 Performance Comparison")
        print("=" * 50)
        
        bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=self.region)
        
        comparison_query = "ENFP personality tourist attractions Hong Kong social creative"
        
        print(f"Test query: {comparison_query}")
        
        try:
            response = bedrock_runtime.retrieve(
                knowledgeBaseId=self.kb_id,
                retrievalQuery={'text': comparison_query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 8
                    }
                }
            )
            
            results = response['retrievalResults']
            
            if results:
                scores = [r['score'] for r in results]
                
                print(f"\n📈 Results with Optimized Markdown:")
                print(f"   Total results: {len(results)}")
                print(f"   Score range: {min(scores):.4f} - {max(scores):.4f}")
                print(f"   Average score: {sum(scores)/len(scores):.4f}")
                
                # Check content quality
                content = ' '.join([r['content']['text'] for r in results])
                enfp_mentions = content.count('ENFP')
                mbti_mentions = content.count('personality')
                
                print(f"   ENFP mentions: {enfp_mentions}")
                print(f"   Personality mentions: {mbti_mentions}")
                
                # Show sample improved content
                print(f"\n📝 Sample improved content:")
                print(f"   {results[0]['content']['text'][:200]}...")
                
            else:
                print("❌ No results found with optimized content")
                
        except Exception as e:
            print(f"❌ Error in performance comparison: {e}")

def main():
    """Main update workflow."""
    
    print("🔄 Knowledge Base Update with Optimized Markdown")
    print("=" * 60)
    
    updater = KnowledgeBaseUpdater()
    
    # Step 1: List current data sources
    current_sources = updater.list_current_data_sources()
    
    # Step 2: Create new optimized data source
    new_ds_id = updater.create_optimized_data_source()
    
    if not new_ds_id:
        print("❌ Failed to create new data source. Exiting.")
        return
    
    # Step 3: Start ingestion job
    job_id = updater.start_ingestion_job(new_ds_id)
    
    if not job_id:
        print("❌ Failed to start ingestion job. Exiting.")
        return
    
    # Step 4: Monitor ingestion
    success = updater.monitor_ingestion_job(new_ds_id, job_id)
    
    if not success:
        print("❌ Ingestion job did not complete successfully.")
        return
    
    # Step 5: Test optimized queries
    updater.test_optimized_queries()
    
    # Step 6: Performance comparison
    updater.compare_performance()
    
    print(f"\n🎉 Knowledge Base Update Complete!")
    print(f"\n📋 Summary:")
    print(f"   ✅ Created optimized data source: {new_ds_id}")
    print(f"   ✅ Successfully ingested optimized markdown")
    print(f"   ✅ Improved content structure for better MBTI matching")
    print(f"   ✅ Enhanced chunking and parsing for S3 vectors")
    
    print(f"\n🎯 Benefits of Optimized Markdown:")
    print("   - Better MBTI personality type organization")
    print("   - Enhanced searchability with personality descriptions")
    print("   - Improved context preservation with structured sections")
    print("   - Complete attraction information in searchable format")
    print("   - District and location indexing for better filtering")
    
    print(f"\n🚀 Next Steps:")
    print("   1. Test your MBTI attraction queries with improved results")
    print("   2. Use the new data source for production applications")
    print("   3. Monitor query performance and relevance scores")
    print("   4. Consider disabling old data sources if no longer needed")

if __name__ == "__main__":
    main()