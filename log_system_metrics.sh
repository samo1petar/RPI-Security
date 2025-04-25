#!/bin/bash

OUTPUT_FILE="system_metrics_log.csv"

# Write CSV header if file doesn't exist
if [ ! -f "$OUTPUT_FILE" ]; then
    echo "timestamp,temperature,load_avg_1min,mem_used_MB,mem_total_MB,disk_used_GB,disk_total_GB" > "$OUTPUT_FILE"
fi

echo "Logging system metrics to $OUTPUT_FILE. Press Ctrl+C to stop."

while true; do
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

    # Temperature
    RAW_TEMP=$(vcgencmd measure_temp)  # e.g. temp=42.8'C
    TEMP_VALUE=$(echo "$RAW_TEMP" | grep -oP "[0-9]+\.[0-9]+")

    # CPU load (1-minute avg)
    LOAD_AVG=$(cut -d ' ' -f1 /proc/loadavg)

    # Memory (in MB)
    MEM_TOTAL=$(free -m | awk '/^Mem:/ {print $2}')
    MEM_USED=$(free -m | awk '/^Mem:/ {print $3}')

    # Disk (in GB, root partition)
    DISK_TOTAL=$(df -BG / | awk 'NR==2 {gsub("G",""); print $2}')
    DISK_USED=$(df -BG / | awk 'NR==2 {gsub("G",""); print $3}')

    echo "$TIMESTAMP,$TEMP_VALUE,$LOAD_AVG,$MEM_USED,$MEM_TOTAL,$DISK_USED,$DISK_TOTAL" >> "$OUTPUT_FILE"

    sleep 1
done
