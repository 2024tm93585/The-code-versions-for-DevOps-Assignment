#!/bin/bash
# =============================================================
# ACEest Fitness — AWS ECS Fargate Deployment Script
# Run from the DevOps-Assignment2/ directory.
# NOTE: Always builds for linux/amd64 (required by ECS Fargate).
#       On Apple Silicon Macs the default build is arm64 which
#       ECS cannot run — the --platform flag fixes this.
# =============================================================

set -e

# ---- CONFIGURE THESE ----
AWS_REGION="us-east-1"
CLUSTER_NAME="aceest-cluster"
SERVICE_NAME="aceest-fitness-service"
TASK_FAMILY="aceest-fitness"
# -------------------------

export AWS_DEFAULT_REGION="$AWS_REGION"

AWS_ACCOUNT_ID=$(aws sts get-caller-identity \
  --region "$AWS_REGION" \
  --query Account \
  --output text)

ECR_IMAGE="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/aceest-fitness:latest"

echo "==> Account : $AWS_ACCOUNT_ID"
echo "==> Region  : $AWS_REGION"
echo "==> Image   : $ECR_IMAGE"

# ---------- 1. CloudWatch log group ----------
echo ""
echo "==> [1/8] Creating CloudWatch log group..."
aws logs create-log-group \
  --log-group-name /ecs/aceest-fitness \
  --region "$AWS_REGION" 2>/dev/null \
  && echo "    Created." \
  || echo "    Already exists — skipping."

# ---------- 2. Register task definition ----------
echo ""
echo "==> [2/8] Registering ECS task definition..."
sed \
  "s/YOUR_ACCOUNT_ID/$AWS_ACCOUNT_ID/g; s/YOUR_REGION/$AWS_REGION/g" \
  aws/ecs-task-definition.json > /tmp/aceest-task-def.json

aws ecs register-task-definition \
  --cli-input-json file:///tmp/aceest-task-def.json \
  --region "$AWS_REGION" \
  --query "taskDefinition.taskDefinitionArn" \
  --output text

# ---------- 3. ECS cluster ----------
echo ""
echo "==> [3/8] Ensuring ECS cluster exists in $AWS_REGION..."
CLUSTER_STATUS=$(aws ecs describe-clusters \
  --clusters "$CLUSTER_NAME" \
  --region "$AWS_REGION" \
  --query "clusters[?clusterName=='$CLUSTER_NAME'].status" \
  --output text 2>/dev/null)

if [ "$CLUSTER_STATUS" = "ACTIVE" ]; then
  echo "    Cluster already ACTIVE — skipping create."
else
  echo "    Creating cluster..."
  # Omit --capacity-providers to avoid the service-linked role requirement.
  # Fargate is available by default on all ECS clusters.
  aws ecs create-cluster \
    --cluster-name "$CLUSTER_NAME" \
    --region "$AWS_REGION" \
    --query "cluster.clusterArn" \
    --output text
fi

# ---------- 4. VPC & subnets ----------
echo ""
echo "==> [4/8] Fetching default VPC and subnets in $AWS_REGION..."
VPC_ID=$(aws ec2 describe-vpcs \
  --filters "Name=isDefault,Values=true" \
  --region "$AWS_REGION" \
  --query "Vpcs[0].VpcId" \
  --output text)

if [ -z "$VPC_ID" ] || [ "$VPC_ID" = "None" ]; then
  echo "ERROR: No default VPC found in $AWS_REGION."
  echo "Create one at: https://console.aws.amazon.com/vpc/home?region=$AWS_REGION#vpcs"
  exit 1
fi

SUBNET_IDS=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --region "$AWS_REGION" \
  --query "Subnets[*].SubnetId" \
  --output text | tr '\t' ',')

echo "    VPC     : $VPC_ID"
echo "    Subnets : $SUBNET_IDS"

# ---------- 5. Security group ----------
echo ""
echo "==> [5/8] Ensuring security group exists..."
SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=aceest-fitness-sg" "Name=vpc-id,Values=$VPC_ID" \
  --region "$AWS_REGION" \
  --query "SecurityGroups[0].GroupId" \
  --output text 2>/dev/null)

if [ -z "$SG_ID" ] || [ "$SG_ID" = "None" ]; then
  echo "    Creating security group..."
  SG_ID=$(aws ec2 create-security-group \
    --group-name aceest-fitness-sg \
    --description "ACEest Fitness security group" \
    --vpc-id "$VPC_ID" \
    --region "$AWS_REGION" \
    --query GroupId \
    --output text)

  aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp \
    --port 5000 \
    --cidr 0.0.0.0/0 \
    --region "$AWS_REGION"
  echo "    Created SG: $SG_ID"
else
  echo "    Security group already exists: $SG_ID"
fi

# ---------- 6. ecsTaskExecutionRole ----------
echo ""
echo "==> [6/8] Ensuring ecsTaskExecutionRole exists..."
ROLE_EXISTS=$(aws iam get-role \
  --role-name ecsTaskExecutionRole \
  --query "Role.RoleName" \
  --output text 2>/dev/null || echo "")

if [ -z "$ROLE_EXISTS" ]; then
  echo "    Creating ecsTaskExecutionRole..."
  aws iam create-role \
    --role-name ecsTaskExecutionRole \
    --assume-role-policy-document '{
      "Version":"2012-10-17",
      "Statement":[{
        "Effect":"Allow",
        "Principal":{"Service":"ecs-tasks.amazonaws.com"},
        "Action":"sts:AssumeRole"
      }]
    }' \
    --query "Role.Arn" --output text

  aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
  echo "    Role created and policy attached."
else
  echo "    Role already exists — skipping."
fi

# ---------- 7. Create or update ECS service ----------
echo ""
echo "==> [7/8] Deploying ECS service in $AWS_REGION..."

SERVICE_STATUS=$(aws ecs describe-services \
  --cluster "$CLUSTER_NAME" \
  --services "$SERVICE_NAME" \
  --region "$AWS_REGION" \
  --query "services[?serviceName=='$SERVICE_NAME'].status" \
  --output text 2>/dev/null)

if [ "$SERVICE_STATUS" = "ACTIVE" ]; then
  echo "    Updating existing service..."
  aws ecs update-service \
    --cluster "$CLUSTER_NAME" \
    --service "$SERVICE_NAME" \
    --task-definition "$TASK_FAMILY" \
    --force-new-deployment \
    --region "$AWS_REGION" \
    --query "service.serviceArn" \
    --output text
else
  echo "    Creating new service..."
  aws ecs create-service \
    --cluster "$CLUSTER_NAME" \
    --service-name "$SERVICE_NAME" \
    --task-definition "$TASK_FAMILY" \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration \
      "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
    --region "$AWS_REGION" \
    --query "service.serviceArn" \
    --output text
fi

# ---------- 8. Wait and print URL ----------
echo ""
echo "==> [8/8] Waiting for service to stabilise (~2 min)..."
aws ecs wait services-stable \
  --cluster "$CLUSTER_NAME" \
  --services "$SERVICE_NAME" \
  --region "$AWS_REGION"

echo ""
echo "==> Fetching public IP of running task..."
TASK_ARN=$(aws ecs list-tasks \
  --cluster "$CLUSTER_NAME" \
  --service-name "$SERVICE_NAME" \
  --region "$AWS_REGION" \
  --query "taskArns[0]" \
  --output text)

ENI_ID=$(aws ecs describe-tasks \
  --cluster "$CLUSTER_NAME" \
  --tasks "$TASK_ARN" \
  --region "$AWS_REGION" \
  --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" \
  --output text)

PUBLIC_IP=$(aws ec2 describe-network-interfaces \
  --network-interface-ids "$ENI_ID" \
  --region "$AWS_REGION" \
  --query "NetworkInterfaces[0].Association.PublicIp" \
  --output text)

echo ""
echo "============================================"
echo " ACEest Fitness deployed successfully!"
echo " App URL : http://$PUBLIC_IP:5000"
echo " Health  : http://$PUBLIC_IP:5000/health"
echo "============================================"
