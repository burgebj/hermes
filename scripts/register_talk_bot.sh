#!/bin/bash
#
# Helper for installing the Hermes bot in Nextcloud Talk.
#
# Usage:
#   ./scripts/register_talk_bot.sh [<lxc-ip>] [<nc-container>]
#
# Environment variables (alternative to positional args):
#   NC_CONTAINER   Name of the Docker container running Nextcloud
#                  (default: nextcloud)
#
# Assumes Nextcloud runs in a Docker container. For bare-metal NC
# installs, replace "docker exec -u www-data <container>" with
# "sudo -u www-data php /var/www/nextcloud/occ" in the printed commands.
#

set -e

LXC_IP="${1:-10.254.1.119}"
NC_CONTAINER="${2:-${NC_CONTAINER:-nextcloud}}"
WEBHOOK_URL="http://${LXC_IP}:8765/talk/webhook"
SECRET="$(openssl rand -hex 32)"

cat <<EOF

=== Hermes Nextcloud Talk bot registration ===

Bot webhook URL: ${WEBHOOK_URL}
NC container:    ${NC_CONTAINER}
Generated secret (one-time, copy carefully):
${SECRET}

Step 1 — On the Docker host, run:

  docker exec -u www-data ${NC_CONTAINER} php occ talk:bot:install \\
      "Hermes" \\
      "${SECRET}" \\
      "${WEBHOOK_URL}" \\
      "Hermes AI Agent" \\
      --feature=webhook --feature=response

  If the command syntax differs, first check what's available:
    docker exec -u www-data ${NC_CONTAINER} php occ talk:bot:install --help

  The command returns a bot ID (e.g. "bot-1"). Remember it.

Step 2 — For each Talk conversation you want Hermes in, run:

  docker exec -u www-data ${NC_CONTAINER} php occ talk:bot:setup <bot-id> <conversation-token>

  (The conversation token is the random string in the Talk URL, e.g.
  https://nextcloud.example.com/call/n3xtc10ud → token is "n3xtc10ud")

Step 3 — On the LXC, add these lines to /home/niko/.hermes/.env:

  NEXTCLOUD_TALK_URL=https://<your-nextcloud-domain>
  NEXTCLOUD_TALK_BOT_SECRET=${SECRET}

  Then: chmod 600 /home/niko/.hermes/.env

Step 4 — Restart the 'hermes gateway' process so it picks up the env vars.

Step 5 — In a Talk DM with the Hermes bot, send "ping". You should get a reply.

=== Notes ===

- For bare-metal (non-Docker) Nextcloud installs, the OCC command is:
    sudo -u www-data php /var/www/nextcloud/occ talk:bot:install ...
  (same args, no docker exec wrapper)

- If the bot replies from the wrong endpoint or never replies at all,
  check /home/niko/.hermes/sessions/request_dump_*.json for the failed
  request details. See docs/superpowers/plans/ for troubleshooting.

EOF
