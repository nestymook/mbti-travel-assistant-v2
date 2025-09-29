#!/usr/bin/env python3
"""
Knowledge Base Configuration Automation Script

This script automates the configuration and validation of the Amazon Bedrock
Knowledge Base for the MBTI Travel Assistant, including data source management,
ingestion job monitoring, and query optimization.
"""

import json
import os
import sys
import logging
import time
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KnowledgeBaseConfigurator:
    """
    Automates knowledge base configuration and management.
    
    Handles data source configuration, ingestion job management,
    query optimization, and validation for the MBTI Travel Assistant.
    """
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize knowledge base configurator.
        
        Args:
            region: AWS region
        """
        self.region = region
        
        try:
            self.session = boto3.Session()
            self.bedrock_agent = self.session.client('bedrock-agent', region_name=region)
            self.bedrock_agent_runtime = self.session.client('bedrock-agent-runtime', region_name=region)
            self.s3 = self.session.client('s3', region_name=region)
            self.sts = self.session.client('sts', region_name=region)
            
            # Get account ID
            self.account_id = self.sts.get_caller_identity()['Account']
            
            logger.info(f"Initialized Knowledge Base Configurator for account {self.account_id} in {region}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            sys.exit(1)
    
    async def configure_complete_knowledge_base(
        self,
        kb_id: str,
        environment: str = "development",
        validate_data: bool = True,
        optimize_queries: bool = True
    ) -> Dict[str, Any]:
        """
        Configure complete knowledge base setup.
        
        Args:
            kb_id: Knowledge base ID
            environment: Environment name
            validate_data: Whether to validate data sources
            optimize_queries: Whether to optimize query performance
            
        Returns:
            Configuration result dictionary
        """
        logger.info(f"Configuring complete knowledge base setup for {kb_id}")
        
        config_result = {
            "knowledge_base_id": kb_id,
            "environment": environment,
            "timestamp": datetime.utcnow().isoformat(),
            "phases": {}
        }
        
        try:
            # Phase 1: Validate knowledge base exists and is accessible
            logger.info("Phase 1: Knowledge base validation")
            validation_result = await self._validate_knowledge_base_access(kb_id)
            config_result["phases"]["validation"] = validation_result
            
            if not validation_result["success"]:
                raise Exception(f"Knowledge base validation failed: {validation_result['error']}")
            
            # Phase 2: Configure data sources
            logger.info("Phase 2: Data source configuration")
            data_source_result = await self._configure_data_sources(kb_id, environment)
            config_result["phases"]["data_sources"] = data_source_result
            
            # Phase 3: Validate and sync data
            if validate_data:
                logger.info("Phase 3: Data validation and sync")
                sync_result = await self._validate_and_sync_data(kb_id)
                config_result["phases"]["data_sync"] = sync_result
            
            # Phase 4: Optimize query performance
            if optimize_queries:
                logger.info("Phase 4: Query optimization")
                optimization_result = await self._optimize_query_performance(kb_id)
                config_result["phases"]["optimization"] = optimization_result
            
            # Phase 5: Test knowledge base functionality
            logger.info("Phase 5: Functionality testing")
            test_result = await self._test_knowledge_base_functionality(kb_id)
            config_result["phases"]["testing"] = test_result
            
            # Phase 6: Create monitoring and alerts
            logger.info("Phase 6: Monitoring setup")
            monitoring_result = await self._setup_knowledge_base_monitoring(kb_id, environment)
            config_result["phases"]["monitoring"] = monitoring_result
            
            config_result["status"] = "success"
            config_result["summary"] = self._generate_configuration_summary(config_result)
            
            logger.info(f"Knowledge base configuration completed successfully")
            return config_result
            
        except Exception as e:
            logger.error(f"Knowledge base configuration failed: {e}")
            config_result["status"] = "failed"
            config_result["error"] = str(e)
            return config_result
    
    async def _validate_knowledge_base_access(self, kb_id: str) -> Dict[str, Any]:
        """Validate knowledge base access and permissions."""
        try:
            # Get knowledge base details
            kb_response = self.bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
            kb_info = kb_response['knowledgeBase']
            
            # Check status
            if kb_info['status'] != 'ACTIVE':
                return {
                    "success": False,
                    "error": f"Knowledge base status is {kb_info['status']}, expected ACTIVE",
                    "kb_info": kb_info
                }
            
            # Validate storage configuration
            storage_config = kb_info.get('storageConfiguration', {})
            storage_type = storage_config.get('type')
            
            if storage_type == 'S3_VECTORS':
                s3_config = storage_config.get('s3VectorsConfiguration', {})
                vector_bucket = s3_config.get('vectorBucketName')
                
                # Validate S3 vectors access
                try:
                    s3vectors_client = self.session.client('s3vectors', region_name=self.region)
                    s3vectors_client.get_vector_bucket(vectorBucketName=vector_bucket)
                    
                    vector_access = True
                except Exception as e:
                    logger.warning(f"S3 vectors access validation failed: {e}")
                    vector_access = False
            else:
                vector_access = True  # Other storage types
            
            # Test basic query access
            try:
                test_response = self.bedrock_agent_runtime.retrieve(
                    knowledgeBaseId=kb_id,
                    retrievalQuery={'text': 'test'},
                    retrievalConfiguration={
                        'vectorSearchConfiguration': {'numberOfResults': 1}
                    }
                )
                query_access = True
            except Exception as e:
                logger.warning(f"Query access test failed: {e}")
                query_access = False
            
            return {
                "success": True,
                "kb_info": kb_info,
                "storage_type": storage_type,
                "vector_access": vector_access,
                "query_access": query_access,
                "validation_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Knowledge base access validation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _configure_data_sources(self, kb_id: str, environment: str) -> Dict[str, Any]:
        """Configure and validate data sources."""
        try:
            # List existing data sources
            data_sources_response = self.bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)
            data_sources = data_sources_response['dataSourceSummaries']
            
            configured_sources = []
            failed_sources = []
            
            for ds_summary in data_sources:
                try:
                    # Get detailed data source information
                    ds_response = self.bedrock_agent.get_data_source(
                        knowledgeBaseId=kb_id,
                        dataSourceId=ds_summary['dataSourceId']
                    )
                    
                    data_source = ds_response['dataSource']
                    
                    # Validate data source configuration
                    validation_result = await self._validate_data_source_config(data_source, environment)
                    
                    if validation_result["valid"]:
                        configured_sources.append({
                            "data_source_id": data_source['dataSourceId'],
                            "name": data_source['name'],
                            "status": data_source['status'],
                            "validation": validation_result
                        })
                    else:
                        failed_sources.append({
                            "data_source_id": data_source['dataSourceId'],
                            "name": data_source['name'],
                            "error": validation_result["error"]
                        })
                        
                except Exception as e:
                    logger.error(f"Failed to configure data source {ds_summary['name']}: {e}")
                    failed_sources.append({
                        "data_source_id": ds_summary['dataSourceId'],
                        "name": ds_summary['name'],
                        "error": str(e)
                    })
            
            return {
                "success": len(failed_sources) == 0,
                "configured_sources": configured_sources,
                "failed_sources": failed_sources,
                "total_sources": len(data_sources)
            }
            
        except Exception as e:
            logger.error(f"Data source configuration failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _validate_data_source_config(self, data_source: Dict[str, Any], environment: str) -> Dict[str, Any]:
        """Validate individual data source configuration."""
        try:
            ds_config = data_source.get('dataSourceConfiguration', {})
            
            if ds_config.get('type') == 'S3':
                s3_config = ds_config.get('s3Configuration', {})
                bucket_arn = s3_config.get('bucketArn', '')
                
                # Extract bucket name from ARN
                bucket_name = bucket_arn.split(':')[-1] if bucket_arn else ''
                
                if not bucket_name:
                    return {
                        "valid": False,
                        "error": "Invalid S3 bucket ARN"
                    }
                
                # Check bucket access
                try:
                    self.s3.head_bucket(Bucket=bucket_name)
                    bucket_accessible = True
                except Exception as e:
                    logger.warning(f"S3 bucket {bucket_name} not accessible: {e}")
                    bucket_accessible = False
                
                # Check for required files based on environment
                required_files = self._get_required_files_for_environment(environment)
                missing_files = []
                
                for file_path in required_files:
                    try:
                        self.s3.head_object(Bucket=bucket_name, Key=file_path)
                    except ClientError as e:
                        if e.response['Error']['Code'] == '404':
                            missing_files.append(file_path)
                
                return {
                    "valid": bucket_accessible and len(missing_files) == 0,
                    "bucket_name": bucket_name,
                    "bucket_accessible": bucket_accessible,
                    "missing_files": missing_files,
                    "error": f"Missing files: {missing_files}" if missing_files else None
                }
            
            else:
                # Other data source types
                return {
                    "valid": True,
                    "type": ds_config.get('type', 'unknown')
                }
                
        except Exception as e:
            logger.error(f"Data source validation failed: {e}")
            return {
                "valid": False,
                "error": str(e)
            }
    
    def _get_required_files_for_environment(self, environment: str) -> List[str]:
        """Get required files for specific environment."""
        base_files = [
            "Tourist_Spots_With_Hours.markdown"
        ]
        
        if environment == "production":
            # Production might require additional files
            return base_files + [
                "MBTI_Tourist_Spots_Production.markdown"
            ]
        elif environment == "staging":
            return base_files + [
                "MBTI_Tourist_Spots_Staging.markdown"
            ]
        else:
            return base_files
    
    async def _validate_and_sync_data(self, kb_id: str) -> Dict[str, Any]:
        """Validate and sync knowledge base data."""
        try:
            # Get data sources
            data_sources_response = self.bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)
            data_sources = data_sources_response['dataSourceSummaries']
            
            sync_results = []
            
            for ds_summary in data_sources:
                try:
                    # Check if ingestion is needed
                    ingestion_jobs = self.bedrock_agent.list_ingestion_jobs(
                        knowledgeBaseId=kb_id,
                        dataSourceId=ds_summary['dataSourceId'],
                        maxResults=5
                    )
                    
                    latest_job = None
                    if ingestion_jobs['ingestionJobSummaries']:
                        latest_job = ingestion_jobs['ingestionJobSummaries'][0]
                    
                    # Determine if new ingestion is needed
                    needs_ingestion = (
                        not latest_job or
                        latest_job['status'] in ['FAILED', 'STOPPED'] or
                        self._is_data_stale(latest_job)
                    )
                    
                    if needs_ingestion:
                        logger.info(f"Starting ingestion for data source: {ds_summary['name']}")
                        
                        # Start ingestion job
                        ingestion_response = self.bedrock_agent.start_ingestion_job(
                            knowledgeBaseId=kb_id,
                            dataSourceId=ds_summary['dataSourceId']
                        )
                        
                        job_id = ingestion_response['ingestionJob']['ingestionJobId']
                        
                        # Monitor ingestion job
                        job_result = await self._monitor_ingestion_job(kb_id, ds_summary['dataSourceId'], job_id)
                        
                        sync_results.append({
                            "data_source_id": ds_summary['dataSourceId'],
                            "name": ds_summary['name'],
                            "ingestion_started": True,
                            "job_id": job_id,
                            "job_result": job_result
                        })
                    else:
                        sync_results.append({
                            "data_source_id": ds_summary['dataSourceId'],
                            "name": ds_summary['name'],
                            "ingestion_started": False,
                            "reason": "Data is up to date"
                        })
                        
                except Exception as e:
                    logger.error(f"Failed to sync data source {ds_summary['name']}: {e}")
                    sync_results.append({
                        "data_source_id": ds_summary['dataSourceId'],
                        "name": ds_summary['name'],
                        "ingestion_started": False,
                        "error": str(e)
                    })
            
            successful_syncs = [r for r in sync_results if not r.get("error")]
            failed_syncs = [r for r in sync_results if r.get("error")]
            
            return {
                "success": len(failed_syncs) == 0,
                "sync_results": sync_results,
                "successful_syncs": len(successful_syncs),
                "failed_syncs": len(failed_syncs)
            }
            
        except Exception as e:
            logger.error(f"Data validation and sync failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _is_data_stale(self, latest_job: Dict[str, Any], max_age_hours: int = 24) -> bool:
        """Check if data is stale based on last ingestion job."""
        try:
            if latest_job['status'] != 'COMPLETE':
                return True
            
            # Check job age
            updated_at = latest_job.get('updatedAt')
            if updated_at:
                job_age = datetime.utcnow() - updated_at.replace(tzinfo=None)
                return job_age > timedelta(hours=max_age_hours)
            
            return True
            
        except Exception:
            return True
    
    async def _monitor_ingestion_job(
        self,
        kb_id: str,
        data_source_id: str,
        job_id: str,
        timeout_minutes: int = 15
    ) -> Dict[str, Any]:
        """Monitor ingestion job until completion."""
        logger.info(f"Monitoring ingestion job: {job_id}")
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while time.time() - start_time < timeout_seconds:
            try:
                job_response = self.bedrock_agent.get_ingestion_job(
                    knowledgeBaseId=kb_id,
                    dataSourceId=data_source_id,
                    ingestionJobId=job_id
                )
                
                job = job_response['ingestionJob']
                status = job['status']
                
                logger.info(f"Ingestion job {job_id} status: {status}")
                
                if status == 'COMPLETE':
                    return {
                        "success": True,
                        "status": status,
                        "job_info": job
                    }
                elif status in ['FAILED', 'STOPPED']:
                    return {
                        "success": False,
                        "status": status,
                        "error": job.get('failureReasons', ['Unknown failure']),
                        "job_info": job
                    }
                
                # Wait before next check
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error monitoring ingestion job: {e}")
                await asyncio.sleep(30)
        
        # Timeout reached
        return {
            "success": False,
            "status": "timeout",
            "error": f"Ingestion job monitoring timed out after {timeout_minutes} minutes"
        }
    
    async def _optimize_query_performance(self, kb_id: str) -> Dict[str, Any]:
        """Optimize knowledge base query performance."""
        try:
            optimization_results = []
            
            # Test different query configurations
            test_queries = [
                "What tourist spots are available for INFJ personality?",
                "Find attractions suitable for extroverted personalities",
                "Show me cultural sites in Hong Kong",
                "What are the operating hours for tourist attractions?"
            ]
            
            for query in test_queries:
                # Test with different configurations
                configs = [
                    {"numberOfResults": 5, "overrideSearchType": "HYBRID"},
                    {"numberOfResults": 10, "overrideSearchType": "SEMANTIC"},
                    {"numberOfResults": 15, "overrideSearchType": "HYBRID"}
                ]
                
                query_results = []
                
                for config in configs:
                    try:
                        start_time = time.time()
                        
                        response = self.bedrock_agent_runtime.retrieve(
                            knowledgeBaseId=kb_id,
                            retrievalQuery={'text': query},
                            retrievalConfiguration={
                                'vectorSearchConfiguration': config
                            }
                        )
                        
                        end_time = time.time()
                        response_time = end_time - start_time
                        
                        results = response.get('retrievalResults', [])
                        
                        query_results.append({
                            "config": config,
                            "response_time": response_time,
                            "results_count": len(results),
                            "has_relevant_content": len(results) > 0 and bool(results[0].get('content', {}).get('text'))
                        })
                        
                    except Exception as e:
                        logger.error(f"Query optimization test failed: {e}")
                        query_results.append({
                            "config": config,
                            "error": str(e)
                        })
                
                optimization_results.append({
                    "query": query,
                    "results": query_results
                })
            
            # Analyze results and recommend optimal configuration
            optimal_config = self._analyze_optimization_results(optimization_results)
            
            return {
                "success": True,
                "optimization_results": optimization_results,
                "optimal_config": optimal_config
            }
            
        except Exception as e:
            logger.error(f"Query optimization failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _analyze_optimization_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze optimization results to recommend optimal configuration."""
        try:
            # Collect performance metrics
            config_performance = {}
            
            for query_result in results:
                for result in query_result["results"]:
                    if "error" not in result:
                        config_key = json.dumps(result["config"], sort_keys=True)
                        
                        if config_key not in config_performance:
                            config_performance[config_key] = {
                                "config": result["config"],
                                "response_times": [],
                                "results_counts": [],
                                "relevance_scores": []
                            }
                        
                        config_performance[config_key]["response_times"].append(result["response_time"])
                        config_performance[config_key]["results_counts"].append(result["results_count"])
                        config_performance[config_key]["relevance_scores"].append(
                            1.0 if result["has_relevant_content"] else 0.0
                        )
            
            # Calculate averages and find optimal configuration
            best_config = None
            best_score = 0
            
            for config_key, metrics in config_performance.items():
                avg_response_time = sum(metrics["response_times"]) / len(metrics["response_times"])
                avg_results_count = sum(metrics["results_counts"]) / len(metrics["results_counts"])
                avg_relevance = sum(metrics["relevance_scores"]) / len(metrics["relevance_scores"])
                
                # Score based on relevance (weight: 0.5), response time (weight: 0.3), results count (weight: 0.2)
                # Lower response time is better, higher relevance and results count are better
                score = (
                    avg_relevance * 0.5 +
                    (1.0 / max(avg_response_time, 0.1)) * 0.3 +
                    min(avg_results_count / 10.0, 1.0) * 0.2
                )
                
                if score > best_score:
                    best_score = score
                    best_config = {
                        "config": metrics["config"],
                        "avg_response_time": avg_response_time,
                        "avg_results_count": avg_results_count,
                        "avg_relevance": avg_relevance,
                        "score": score
                    }
            
            return best_config or {"error": "No optimal configuration found"}
            
        except Exception as e:
            logger.error(f"Optimization analysis failed: {e}")
            return {"error": str(e)}
    
    async def _test_knowledge_base_functionality(self, kb_id: str) -> Dict[str, Any]:
        """Test knowledge base functionality with MBTI-specific queries."""
        try:
            # MBTI-specific test queries
            test_queries = [
                {
                    "query": "What tourist spots are suitable for INFJ personality type?",
                    "expected_keywords": ["quiet", "cultural", "meaningful", "peaceful"],
                    "category": "mbti_specific"
                },
                {
                    "query": "Find attractions for extroverted personalities",
                    "expected_keywords": ["social", "interactive", "vibrant", "group"],
                    "category": "mbti_general"
                },
                {
                    "query": "What are the operating hours for museums in Hong Kong?",
                    "expected_keywords": ["hours", "open", "close", "museum"],
                    "category": "operational"
                },
                {
                    "query": "Show me outdoor activities and adventure spots",
                    "expected_keywords": ["outdoor", "adventure", "hiking", "nature"],
                    "category": "activity_type"
                }
            ]
            
            test_results = []
            
            for test_case in test_queries:
                try:
                    start_time = time.time()
                    
                    response = self.bedrock_agent_runtime.retrieve(
                        knowledgeBaseId=kb_id,
                        retrievalQuery={'text': test_case["query"]},
                        retrievalConfiguration={
                            'vectorSearchConfiguration': {
                                'numberOfResults': 10,
                                'overrideSearchType': 'HYBRID'
                            }
                        }
                    )
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    results = response.get('retrievalResults', [])
                    
                    # Analyze results quality
                    quality_analysis = self._analyze_query_results(results, test_case["expected_keywords"])
                    
                    test_results.append({
                        "query": test_case["query"],
                        "category": test_case["category"],
                        "response_time": response_time,
                        "results_count": len(results),
                        "quality_analysis": quality_analysis,
                        "success": len(results) > 0 and quality_analysis["relevance_score"] > 0.3
                    })
                    
                except Exception as e:
                    logger.error(f"Test query failed: {e}")
                    test_results.append({
                        "query": test_case["query"],
                        "category": test_case["category"],
                        "success": False,
                        "error": str(e)
                    })
            
            # Calculate overall success rate
            successful_tests = [t for t in test_results if t.get("success", False)]
            success_rate = len(successful_tests) / len(test_results) if test_results else 0
            
            return {
                "success": success_rate >= 0.7,  # 70% success rate threshold
                "test_results": test_results,
                "success_rate": success_rate,
                "total_tests": len(test_results),
                "successful_tests": len(successful_tests)
            }
            
        except Exception as e:
            logger.error(f"Functionality testing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _analyze_query_results(self, results: List[Dict[str, Any]], expected_keywords: List[str]) -> Dict[str, Any]:
        """Analyze query results for relevance and quality."""
        try:
            if not results:
                return {
                    "relevance_score": 0.0,
                    "keyword_matches": 0,
                    "content_quality": "no_results"
                }
            
            # Combine all result content
            all_content = ""
            for result in results:
                content = result.get('content', {}).get('text', '')
                all_content += content.lower() + " "
            
            # Count keyword matches
            keyword_matches = 0
            for keyword in expected_keywords:
                if keyword.lower() in all_content:
                    keyword_matches += 1
            
            # Calculate relevance score
            relevance_score = keyword_matches / len(expected_keywords) if expected_keywords else 0.0
            
            # Assess content quality
            content_quality = "good"
            if len(all_content.strip()) < 100:
                content_quality = "poor"
            elif len(all_content.strip()) < 500:
                content_quality = "fair"
            
            return {
                "relevance_score": relevance_score,
                "keyword_matches": keyword_matches,
                "total_keywords": len(expected_keywords),
                "content_length": len(all_content.strip()),
                "content_quality": content_quality
            }
            
        except Exception as e:
            logger.error(f"Query results analysis failed: {e}")
            return {
                "relevance_score": 0.0,
                "error": str(e)
            }
    
    async def _setup_knowledge_base_monitoring(self, kb_id: str, environment: str) -> Dict[str, Any]:
        """Setup monitoring for knowledge base operations."""
        try:
            # Create CloudWatch custom metrics for knowledge base
            cloudwatch = self.session.client('cloudwatch', region_name=self.region)
            
            # Define custom metrics
            metrics_to_create = [
                "KnowledgeBaseQueryLatency",
                "KnowledgeBaseQueryCount",
                "KnowledgeBaseQueryErrors",
                "KnowledgeBaseResultsReturned"
            ]
            
            # Send initial metrics to establish them
            for metric_name in metrics_to_create:
                try:
                    cloudwatch.put_metric_data(
                        Namespace='MBTI/KnowledgeBase',
                        MetricData=[
                            {
                                'MetricName': metric_name,
                                'Value': 0.0,
                                'Unit': 'Count',
                                'Dimensions': [
                                    {
                                        'Name': 'KnowledgeBaseId',
                                        'Value': kb_id
                                    },
                                    {
                                        'Name': 'Environment',
                                        'Value': environment
                                    }
                                ]
                            }
                        ]
                    )
                except Exception as e:
                    logger.warning(f"Failed to create metric {metric_name}: {e}")
            
            # Create CloudWatch alarms
            alarms_created = []
            
            alarm_configs = [
                {
                    'AlarmName': f'KnowledgeBase-{kb_id}-{environment}-HighLatency',
                    'ComparisonOperator': 'GreaterThanThreshold',
                    'EvaluationPeriods': 2,
                    'MetricName': 'KnowledgeBaseQueryLatency',
                    'Namespace': 'MBTI/KnowledgeBase',
                    'Period': 300,
                    'Statistic': 'Average',
                    'Threshold': 5.0,  # 5 seconds
                    'ActionsEnabled': True,
                    'AlarmDescription': f'High query latency for knowledge base {kb_id}',
                    'Dimensions': [
                        {
                            'Name': 'KnowledgeBaseId',
                            'Value': kb_id
                        },
                        {
                            'Name': 'Environment',
                            'Value': environment
                        }
                    ],
                    'Unit': 'Seconds'
                },
                {
                    'AlarmName': f'KnowledgeBase-{kb_id}-{environment}-HighErrorRate',
                    'ComparisonOperator': 'GreaterThanThreshold',
                    'EvaluationPeriods': 2,
                    'MetricName': 'KnowledgeBaseQueryErrors',
                    'Namespace': 'MBTI/KnowledgeBase',
                    'Period': 300,
                    'Statistic': 'Sum',
                    'Threshold': 10.0,  # 10 errors in 5 minutes
                    'ActionsEnabled': True,
                    'AlarmDescription': f'High error rate for knowledge base {kb_id}',
                    'Dimensions': [
                        {
                            'Name': 'KnowledgeBaseId',
                            'Value': kb_id
                        },
                        {
                            'Name': 'Environment',
                            'Value': environment
                        }
                    ],
                    'Unit': 'Count'
                }
            ]
            
            for alarm_config in alarm_configs:
                try:
                    cloudwatch.put_metric_alarm(**alarm_config)
                    alarms_created.append(alarm_config['AlarmName'])
                except Exception as e:
                    logger.warning(f"Failed to create alarm {alarm_config['AlarmName']}: {e}")
            
            return {
                "success": True,
                "metrics_created": metrics_to_create,
                "alarms_created": alarms_created
            }
            
        except Exception as e:
            logger.error(f"Knowledge base monitoring setup failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_configuration_summary(self, config_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate configuration summary."""
        summary = {
            "total_phases": len(config_result["phases"]),
            "successful_phases": 0,
            "failed_phases": 0,
            "warnings": []
        }
        
        for phase_name, phase_result in config_result["phases"].items():
            if isinstance(phase_result, dict):
                if phase_result.get("success", False):
                    summary["successful_phases"] += 1
                else:
                    summary["failed_phases"] += 1
                    if phase_result.get("error"):
                        summary["warnings"].append(f"{phase_name}: {phase_result['error']}")
        
        summary["success_rate"] = (
            summary["successful_phases"] / summary["total_phases"] * 100
            if summary["total_phases"] > 0 else 0
        )
        
        return summary
    
    async def save_configuration_report(self, config_result: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """Save configuration report to file."""
        if not output_file:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = f"kb_configuration_report_{timestamp}.json"
        
        try:
            with open(output_file, 'w') as f:
                json.dump(config_result, f, indent=2, default=str)
            
            logger.info(f"Configuration report saved to: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to save configuration report: {e}")
            raise


async def main():
    """Main configuration function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Configure and validate Knowledge Base for MBTI Travel Assistant'
    )
    parser.add_argument('--kb-id', required=True,
                       help='Knowledge Base ID')
    parser.add_argument('--environment', default='development',
                       choices=['development', 'staging', 'production'],
                       help='Environment name')
    parser.add_argument('--region', default='us-east-1',
                       help='AWS region')
    parser.add_argument('--skip-validation', action='store_true',
                       help='Skip data validation')
    parser.add_argument('--skip-optimization', action='store_true',
                       help='Skip query optimization')
    parser.add_argument('--output-file',
                       help='Output file for configuration report')
    
    args = parser.parse_args()
    
    try:
        configurator = KnowledgeBaseConfigurator(region=args.region)
        
        result = await configurator.configure_complete_knowledge_base(
            kb_id=args.kb_id,
            environment=args.environment,
            validate_data=not args.skip_validation,
            optimize_queries=not args.skip_optimization
        )
        
        # Save configuration report
        report_file = await configurator.save_configuration_report(result, args.output_file)
        
        if result["status"] == "success":
            print("\n" + "="*60)
            print("🎉 KNOWLEDGE BASE CONFIGURATION SUCCESSFUL! 🎉")
            print("="*60)
            print(f"Knowledge Base ID: {args.kb_id}")
            print(f"Environment: {args.environment}")
            print(f"Success Rate: {result['summary']['success_rate']:.1f}%")
            print(f"Report File: {report_file}")
            print("="*60)
            return 0
        else:
            print("\n" + "="*60)
            print("❌ KNOWLEDGE BASE CONFIGURATION FAILED")
            print("="*60)
            print(f"Error: {result.get('error', 'Unknown error')}")
            print(f"Report File: {report_file}")
            print("="*60)
            return 1
            
    except Exception as e:
        logger.error(f"Configuration failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))