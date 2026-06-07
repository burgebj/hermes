---
name: system-monitor
description: System resource monitoring - CPU, memory, disk, network, and process diagnostics.
version: 1.0.0
author: Alex Chen
license: MIT
metadata:
  hermes:
    tags: [monitoring, diagnostics, linux, devops, system]
    related_skills: [hermes-server-ops]
---

# System Monitor

Use when the operator asks about system health, resource usage, disk space, or process diagnostics.

## Quick Health Check

\`\`\`bash
# CPU and memory overview
top -bn1 | head -5
df -h / /home 2>/dev/null
free -h
uptime
\`\`\`

## Disk Usage

\`\`\`bash
# Find largest directories
du -sh /* 2>/dev/null | sort -rh | head -10

# Find large files (>100MB)
find / -type f -size +100M -exec ls -lh {} \; 2>/dev/null | sort -k5 -rh | head -20

# Inode usage (when df shows space but writes fail)
df -i
\`\`\`

## Process Diagnostics

\`\`\`bash
# Top CPU consumers
ps aux --sort=-%cpu | head -15

# Top memory consumers
ps aux --sort=-%mem | head -15

# Open files by process
lsof -p <PID> | wc -l

# Network connections by state
ss -s
\`\`\`

## Docker/Container Resources

\`\`\`bash
docker stats --no-stream --format \'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\'
\`\`\`

## Pitfalls

- \`df -h\' can show misleading results on overlay filesystems; use \`df -h -x overlay\' to exclude
- \`free -h\' shows cached memory as \used\; look at \"available" column instead
- On systemd systems, \`journalctl --disk-usage\' can reveal hidden log bloat
