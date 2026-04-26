#!/bin/bash
# Tears down all AWS resources created by deploy-ecs.sh
set -e

AWS_REGION="us-east-1"
CLUSTER_NAME="aceest-cluster"
SERVICE_NAME="aceest-fitness-service"

echo "==> Scaling service to 0..."
aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --desired-count 0 \
  --region $AWS_REGION

echo "==> Deleting ECS service..."
aws ecs delete-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --region $AWS_REGION

echo "==> Deleting ECS cluster..."
aws ecs delete-cluster \
  --cluster $CLUSTER_NAME \
  --region $AWS_REGION

echo "==> Done. ECR repository and CloudWatch logs retained."
echo "    To delete ECR: aws ecr delete-repository --repository-name aceest-fitness --force"
