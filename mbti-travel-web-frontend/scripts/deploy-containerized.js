#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Configuration
const AWS_REGION = 'us-east-1';
const AWS_ACCOUNT_ID = '209803798463';
const ECR_REPOSITORY = 'mbti-travel-frontend';
const IMAGE_TAG = 'latest';
const CONTAINER_NAME = 'mbti-travel-frontend';

console.log('🚀 Starting containerized deployment...');

try {
  // Step 1: Build the Docker image
  console.log('📦 Building Docker image...');
  execSync(`docker build -t ${ECR_REPOSITORY}:${IMAGE_TAG} .`, { 
    stdio: 'inherit',
    cwd: path.join(__dirname, '..')
  });

  // Step 2: Create ECR repository if it doesn't exist
  console.log('🏗️ Creating ECR repository...');
  try {
    execSync(`aws ecr create-repository --repository-name ${ECR_REPOSITORY} --region ${AWS_REGION}`, {
      stdio: 'pipe'
    });
    console.log('✅ ECR repository created');
  } catch (error) {
    if (error.message.includes('RepositoryAlreadyExistsException')) {
      console.log('✅ ECR repository already exists');
    } else {
      throw error;
    }
  }

  // Step 3: Get ECR login token
  console.log('🔐 Logging into ECR...');
  const loginCommand = execSync(`aws ecr get-login-password --region ${AWS_REGION}`, { encoding: 'utf8' });
  execSync(`echo "${loginCommand.trim()}" | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com`, {
    stdio: 'inherit'
  });

  // Step 4: Tag and push image
  const ecrImageUri = `${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}`;
  console.log('🏷️ Tagging image...');
  execSync(`docker tag ${ECR_REPOSITORY}:${IMAGE_TAG} ${ecrImageUri}`, { stdio: 'inherit' });

  console.log('📤 Pushing image to ECR...');
  execSync(`docker push ${ecrImageUri}`, { stdio: 'inherit' });

  // Step 5: Create ECS task definition
  console.log('📋 Creating ECS task definition...');
  const taskDefinition = {
    family: 'mbti-travel-frontend',
    networkMode: 'awsvpc',
    requiresCompatibilities: ['FARGATE'],
    cpu: '256',
    memory: '512',
    executionRoleArn: `arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsTaskExecutionRole`,
    containerDefinitions: [
      {
        name: CONTAINER_NAME,
        image: ecrImageUri,
        portMappings: [
          {
            containerPort: 8080,
            protocol: 'tcp'
          }
        ],
        essential: true,
        logConfiguration: {
          logDriver: 'awslogs',
          options: {
            'awslogs-group': `/ecs/${CONTAINER_NAME}`,
            'awslogs-region': AWS_REGION,
            'awslogs-stream-prefix': 'ecs'
          }
        },
        healthCheck: {
          command: ['CMD-SHELL', 'curl -f http://localhost:8080/health || exit 1'],
          interval: 30,
          timeout: 5,
          retries: 3,
          startPeriod: 60
        }
      }
    ]
  };

  // Write task definition to file
  fs.writeFileSync('task-definition.json', JSON.stringify(taskDefinition, null, 2));

  // Register task definition
  execSync(`aws ecs register-task-definition --cli-input-json file://task-definition.json --region ${AWS_REGION}`, {
    stdio: 'inherit'
  });

  console.log('✅ Containerized deployment completed successfully!');
  console.log(`📦 Image URI: ${ecrImageUri}`);
  console.log(`📋 Task Definition: mbti-travel-frontend`);
  console.log('');
  console.log('🔧 Next steps:');
  console.log('1. Create an ECS cluster');
  console.log('2. Create an ECS service using the task definition');
  console.log('3. Configure Application Load Balancer');
  console.log('4. Set up Route 53 DNS (optional)');

} catch (error) {
  console.error('❌ Deployment failed:', error.message);
  process.exit(1);
}