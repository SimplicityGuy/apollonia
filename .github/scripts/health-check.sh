#!/bin/bash
# Enhanced health check script with consecutive failure tracking

set -euo pipefail

# Configuration
MAX_RETRIES="${MAX_RETRIES:-60}"
CHECK_INTERVAL="${CHECK_INTERVAL:-5}"
MAX_CONSECUTIVE_UNHEALTHY="${MAX_CONSECUTIVE_UNHEALTHY:-3}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Associative arrays to track consecutive unhealthy counts
declare -A unhealthy_counts
declare -A service_names
declare -A last_health_status

echo "⏳ Waiting for services to become healthy..."
echo "Configuration: MAX_RETRIES=$MAX_RETRIES, CHECK_INTERVAL=$CHECK_INTERVAL, MAX_CONSECUTIVE_UNHEALTHY=$MAX_CONSECUTIVE_UNHEALTHY"
echo ""

retry_count=0
while [ $retry_count -lt "$MAX_RETRIES" ]; do
    healthy_count=0
    total_count=0
    all_services_status=""

    # Get all container IDs
    container_ids=$(docker-compose ps -q)

    if [ -z "$container_ids" ]; then
        echo -e "${RED}❌ No containers found. Docker Compose may not be running.${NC}"
        exit 1
    fi

    while read -r container; do
        if [ -n "$container" ]; then
            total_count=$((total_count + 1))

            # Get container name
            container_name=$(docker inspect --format="{{.Name}}" "$container" 2>/dev/null | sed 's/^\/\(.*\)$/\1/')
            service_names["$container"]="$container_name"

            # Get health and state
            health=$(docker inspect --format="{{.State.Health.Status}}" "$container" 2>/dev/null || echo "no health check")
            state=$(docker inspect --format="{{.State.Status}}" "$container" 2>/dev/null || echo "unknown")

            # Initialize unhealthy count if not exists
            if [ -z "${unhealthy_counts[$container]:-}" ]; then
                unhealthy_counts["$container"]=0
            fi

            # Check if healthy
            if [ "$health" = "healthy" ] || ([ "$health" = "no health check" ] && [ "$state" = "running" ]); then
                healthy_count=$((healthy_count + 1))
                unhealthy_counts["$container"]=0
                status_icon="✅"
                status_color="$GREEN"
            else
                # Increment unhealthy count if health status changed or remained unhealthy
                if [ "${last_health_status[$container]:-}" != "healthy" ]; then
                    unhealthy_counts["$container"]=$((unhealthy_counts["$container"] + 1))
                fi

                if [ "$state" = "running" ]; then
                    status_icon="⚠️ "
                    status_color="$YELLOW"
                else
                    status_icon="❌"
                    status_color="$RED"
                fi

                # Check if exceeded max consecutive unhealthy
                if [ "${unhealthy_counts[$container]}" -ge "$MAX_CONSECUTIVE_UNHEALTHY" ]; then
                    echo -e "${RED}❌ ABORT: Service ${service_names[$container]} has been unhealthy for ${unhealthy_counts[$container]} consecutive checks${NC}"
                    echo ""
                    echo "📋 Current service status:"
                    docker-compose ps
                    echo ""
                    echo "📋 Logs from failing service ${service_names[$container]}:"
                    docker logs "$container" --tail=50 2>&1 || true
                    echo ""
                    echo "📋 All service logs:"
                    docker-compose logs
                    exit 1
                fi
            fi

            # Store last health status
            last_health_status["$container"]="$health"

            # Build status line
            status_line="${status_icon} ${container_name}: state=${state}, health=${health}"
            if [ "${unhealthy_counts[$container]}" -gt 0 ]; then
                status_line="${status_line} (unhealthy count: ${unhealthy_counts[$container]})"
            fi

            echo -e "${status_color}${status_line}${NC}"
            all_services_status="${all_services_status}${status_line}\n"
        fi
    done <<< "$container_ids"

    echo -e "${GREEN}✅ Healthy: ${healthy_count}/${total_count} services${NC}"
    echo ""

    # Check if all services are healthy
    if [ "$healthy_count" -eq "$total_count" ] && [ "$total_count" -gt 0 ]; then
        echo -e "${GREEN}✅ All services are ready!${NC}"
        exit 0
    fi

    retry_count=$((retry_count + 1))

    # Show progress
    echo "Retry ${retry_count}/${MAX_RETRIES} - Waiting ${CHECK_INTERVAL}s before next check..."
    echo "---"
    sleep "$CHECK_INTERVAL"
done

# Timeout reached
echo -e "${RED}❌ Timeout: Services did not become healthy within $((MAX_RETRIES * CHECK_INTERVAL)) seconds${NC}"
echo ""
echo "📋 Final service status:"
docker-compose ps
echo ""
echo "📋 Service logs:"
docker-compose logs
exit 1
