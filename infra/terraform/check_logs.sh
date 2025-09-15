#!/bin/bash

# BrainLens Log Checker Script
# Check logs from all ECS services

set -e

# Configuration
PROJECT_NAME="brainlens"
AWS_REGION="eu-north-1"
CLUSTER_NAME="${PROJECT_NAME}-cluster"
LOG_GROUP="/ecs/${PROJECT_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Checking BrainLens Service Logs${NC}"
echo -e "${YELLOW}Cluster:${NC} $CLUSTER_NAME"
echo -e "${YELLOW}Log Group:${NC} $LOG_GROUP"
echo -e "${YELLOW}Region:${NC} $AWS_REGION"
echo

# Function to check service status
check_service_status() {
    local service_name=$1
    echo -e "${YELLOW}Checking service: $service_name${NC}"

    # Get service status
    local status=$(aws ecs describe-services \
        --cluster $CLUSTER_NAME \
        --services $service_name \
        --region $AWS_REGION \
        --query 'services[0].serviceArn' \
        --output text 2>/dev/null)

    if [ "$status" == "None" ]; then
        echo -e "${RED}❌ Service $service_name not found${NC}"
        return 1
    fi

    # Get running tasks
    local task_count=$(aws ecs describe-services \
        --cluster $CLUSTER_NAME \
        --services $service_name \
        --region $AWS_REGION \
        --query 'services[0].runningCount' \
        --output text)

    echo -e "${GREEN}✅ Service running with $task_count task(s)${NC}"

    # Get task ARNs
    local task_arns=$(aws ecs list-tasks \
        --cluster $CLUSTER_NAME \
        --service-name $service_name \
        --region $AWS_REGION \
        --query 'taskArns[]' \
        --output text)

    if [ -z "$task_arns" ]; then
        echo -e "${RED}❌ No running tasks found${NC}"
        return 1
    fi

    # Get the first task ARN
    local task_arn=$(echo $task_arns | cut -d' ' -f1)
    local task_id=$(echo $task_arn | awk -F'/' '{print $NF}')

    echo -e "${BLUE}📋 Task ID: $task_id${NC}"

    return 0
}

# Function to show recent logs
show_recent_logs() {
    local service_prefix=$1
    local service_name=$2

    echo -e "\n${BLUE}📄 Recent logs for $service_name:${NC}"
    echo -e "${YELLOW}Log Stream Prefix: $service_prefix${NC}"

    # Get log streams for this service
    local log_streams=$(aws logs describe-log-streams \
        --log-group-name $LOG_GROUP \
        --region $AWS_REGION \
        --query "logStreams[?starts_with(logStreamName, '$service_prefix/')].[logStreamName, lastEventTimestamp]" \
        --output text | sort -k2 -nr | head -5)

    if [ -z "$log_streams" ]; then
        echo -e "${RED}❌ No log streams found for $service_prefix${NC}"
        return
    fi

    # Show logs from the most recent stream
    local recent_stream=$(echo "$log_streams" | head -1 | cut -f1)

    echo -e "${GREEN}📋 Most recent log stream: $recent_stream${NC}"
    echo -e "${YELLOW}Last 20 log entries:${NC}"

    aws logs get-log-events \
        --log-group-name $LOG_GROUP \
        --log-stream-name "$recent_stream" \
        --region $AWS_REGION \
        --limit 20 \
        --query 'events[*].[timestamp, message]' \
        --output text | \
    while read -r timestamp message; do
        # Convert timestamp to readable format
        local readable_time=$(date -d "@$((timestamp/1000))" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "$timestamp")
        echo "[$readable_time] $message"
    done

    echo
}

# Check all services
services=(
    "brainlens-front-svc:front:Frontend Service"
    "brainlens-back-svc:image:Image Service"
    "brainlens-auth-svc:auth:Auth Service"
    "brainlens-colab-svc:colab:Colab Service"
    "brainlens-ann-svc:annotation:Annotation Service"
)

for service_info in "${services[@]}"; do
    IFS=':' read -r service_name log_prefix display_name <<< "$service_info"

    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}🔍 Checking $display_name${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

    if check_service_status "$service_name"; then
        show_recent_logs "$log_prefix" "$display_name"
    fi
done

# Show cluster summary
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}📊 Cluster Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services brainlens-front-svc brainlens-back-svc brainlens-auth-svc brainlens-colab-svc brainlens-ann-svc \
    --region $AWS_REGION \
    --query 'services[*].[serviceName, runningCount, desiredCount, serviceArn]' \
    --output table

echo -e "\n${YELLOW}💡 Tips:${NC}"
echo "- Use 'aws logs tail $LOG_GROUP --follow --region $AWS_REGION' to follow all logs"
echo "- Check specific service: 'aws logs tail $LOG_GROUP --log-stream-name-prefix image/ --follow --region $AWS_REGION'"
echo "- View ALB access logs in CloudWatch if needed"