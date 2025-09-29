# MBTI Personality Type Tests

This directory contains comprehensive tests for MBTI personality type-based attraction discovery using the Amazon Bedrock Knowledge Base.

## Test Files

### Core Test Scripts

1. **`test_single_mbti_type.py`** - Tests a specific MBTI personality type
   - Focused, efficient testing for individual personality types
   - Comprehensive filtering and result analysis
   - Generates detailed JSON reports

2. **`test_mbti_prompts_comprehensive.py`** - Tests all MBTI personality types
   - Comprehensive testing across all 16 MBTI types
   - Longer execution time but complete coverage
   - Comparative analysis across personality types

3. **`run_mbti_tests.py`** - Test runner utility
   - Command-line interface for running tests
   - Supports single type or comprehensive testing
   - Lists available MBTI types

### Supporting Files

- **`../services/mbti_prompt_loader.py`** - MBTI prompt loading utility
- **`../mbti_prompts/`** - Directory containing MBTI personality type prompt files
- **`results/`** - Directory containing test result JSON files

## Usage

### Run Single MBTI Type Test
```bash
# Test specific MBTI type
python run_mbti_tests.py --type ENTJ
python run_mbti_tests.py --type INFJ

# Or run directly
python test_single_mbti_type.py ENTJ
```

### Run Comprehensive Test (All Types)
```bash
# Test all MBTI types (long execution time)
python run_mbti_tests.py --comprehensive
```

### List Available MBTI Types
```bash
python run_mbti_tests.py --list-types
```

## Test Cases

Each test includes three filtering scenarios:

1. **Test Case 1**: All Areas, All Districts - Complete results for the MBTI type
2. **Test Case 2**: Central Districts Only - Filtered to Central business districts
3. **Test Case 3**: Hong Kong Island Only - Filtered to Hong Kong Island area

## Results Structure

Test results are saved as JSON files with the following structure:

```json
{
  "test_suite": "Single MBTI Type Test - ENTJ",
  "knowledge_base_id": "1FJ1VHU5OW",
  "mbti_type_tested": "ENTJ",
  "total_execution_time": 101.64,
  "total_documents_discovered": 11,
  "test_cases": {
    "test_case_1": {
      "description": "All Areas, All Districts, Files starting with ENTJ",
      "count": 11,
      "records": [...]
    },
    "test_case_2": {...},
    "test_case_3": {...}
  },
  "prompt_source": "../mbti_prompts/ENTJ.json",
  "all_records": [...]
}
```

## Sample Results

### ENTJ (The Commander) Test Results
- **Documents Found**: 11 attractions
- **Execution Time**: ~102 seconds
- **Geographic Distribution**:
  - Hong Kong Island: 6 attractions (55%)
  - Kowloon: 5 attractions (45%)
- **Key Attractions**: Central District, Tai Kwun, Victoria Peak, Star Ferry

### INFJ (The Advocate) Test Results
- **Documents Found**: 13 attractions
- **Execution Time**: ~104 seconds
- **Geographic Distribution**:
  - Hong Kong Island: 7 attractions (54%)
  - Kowloon: 5 attractions (38%)
  - Islands: 1 attraction (8%)
- **Key Attractions**: Man Mo Temple, M+, Hong Kong Cultural Centre, Po Lin Monastery

## MBTI Personality Types Supported

All 16 MBTI personality types are supported:

**Analysts (NT)**:
- INTJ (The Architect)
- INTP (The Thinker)
- ENTJ (The Commander)
- ENTP (The Debater)

**Diplomats (NF)**:
- INFJ (The Advocate)
- INFP (The Mediator)
- ENFJ (The Protagonist)
- ENFP (The Campaigner)

**Sentinels (SJ)**:
- ISTJ (The Logistician)
- ISFJ (The Protector)
- ESTJ (The Executive)
- ESFJ (The Consul)

**Explorers (SP)**:
- ISTP (The Virtuoso)
- ISFP (The Adventurer)
- ESTP (The Entrepreneur)
- ESFP (The Entertainer)

## Performance Notes

- **Single Type Tests**: ~100-120 seconds per MBTI type
- **Comprehensive Tests**: ~30-40 minutes for all 16 types
- **Knowledge Base**: Uses Amazon Bedrock Knowledge Base with S3 vectors
- **Query Optimization**: Uses personality-specific optimized queries

## Dependencies

- `boto3` - AWS SDK for Python
- `json` - JSON handling
- `time` - Performance timing
- `typing` - Type hints

## Configuration

Tests use the following configuration:
- **Knowledge Base ID**: `1FJ1VHU5OW`
- **AWS Region**: `us-east-1`
- **Prompt Directory**: `../mbti_prompts/`
- **Results Directory**: `results/`

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the tests directory
2. **AWS Credentials**: Verify AWS credentials are configured
3. **Knowledge Base Access**: Confirm access to the Bedrock Knowledge Base
4. **Prompt Files**: Ensure MBTI prompt files exist in `../mbti_prompts/`

### Error Resolution

- Check AWS credentials: `aws sts get-caller-identity`
- Verify Knowledge Base: `aws bedrock-agent get-knowledge-base --knowledge-base-id 1FJ1VHU5OW --region us-east-1`
- Test prompt loading: `python -c "from services.mbti_prompt_loader import MBTIPromptLoader; loader = MBTIPromptLoader(); print(loader.get_all_personality_types())"`

## Future Enhancements

- [ ] Parallel processing for comprehensive tests
- [ ] Additional filtering criteria (meal types, price ranges)
- [ ] Integration with restaurant recommendation system
- [ ] Performance optimization for large-scale testing
- [ ] Automated test scheduling and reporting