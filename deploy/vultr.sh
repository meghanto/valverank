#!/usr/bin/env bash
# Create the H2Out API server on Vultr and ship the code + model files.
# Needs VULTR_API_KEY in ../.env. Prints the instance IP. Creating an instance spends account credit.
#   deploy/vultr.sh create    # make the instance (asks for confirmation)
#   deploy/vultr.sh ship IP   # rsync code + data/build, install, start the API (systemd, port 80)
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a
API=https://api.vultr.com/v2
H=(-H "Authorization: Bearer $VULTR_API_KEY" -H "Content-Type: application/json")
PLAN=${PLAN:-vc2-4c-8gb}      # 4 vCPU / 8 GB: one engine needs ~1.5 GB
REGION=${REGION:-dfw}         # Dallas, nearest to Houston
OS_ID=${OS_ID:-2284}          # Ubuntu 24.04 x64

case "${1:-}" in
create)
  KEY_ID=$(curl -s "${H[@]}" "$API/ssh-keys" | python3 -c "import json,sys; k=json.load(sys.stdin)['ssh_keys']; print(k[0]['id'] if k else '')")
  if [ -z "$KEY_ID" ]; then
    KEY_ID=$(curl -s "${H[@]}" -X POST "$API/ssh-keys" -d "{\"name\":\"h2out\",\"ssh_key\":\"$(cat ~/.ssh/id_ed25519.pub 2>/dev/null || cat ~/.ssh/id_rsa.pub)\"}" \
      | python3 -c "import json,sys; print(json.load(sys.stdin)['ssh_key']['id'])")
  fi
  read -r -p "Create $PLAN in $REGION (spends Vultr credit)? [y/N] " ok; [ "$ok" = y ] || exit 1
  curl -s "${H[@]}" -X POST "$API/instances" -d "{\"region\":\"$REGION\",\"plan\":\"$PLAN\",\"os_id\":$OS_ID,\"label\":\"h2out-api\",\"sshkey_id\":[\"$KEY_ID\"]}" \
    | python3 -c "import json,sys; i=json.load(sys.stdin)['instance']; print('instance', i['id'], 'ip (may be 0.0.0.0 until active):', i['main_ip'])"
  ;;
ship)
  IP=$2
  HOST=${API_HOST:-${IP//./-}.sslip.io}   # set API_HOST=api.<your-domain> once DNS points at IP
  rsync -az --exclude node_modules --exclude .venv --exclude .git --exclude 'data/raw' --exclude 'web' \
    --exclude 'data/build/tiles' ./ root@"$IP":/opt/h2out/
  ssh root@"$IP" "export HOST=$HOST; "'set -e
    command -v uv || curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH=$HOME/.local/bin:$PATH
    cd /opt/h2out && uv sync --project pipeline
    cat > /etc/systemd/system/h2out.service <<UNIT
[Unit]
Description=H2Out API
After=network.target
[Service]
WorkingDirectory=/opt/h2out
ExecStart=/root/.local/bin/uv run --project pipeline uvicorn server.app:app --host 127.0.0.1 --port 8787 --workers 2
Restart=always
[Install]
WantedBy=multi-user.target
UNIT
    systemctl daemon-reload && systemctl enable --now h2out
    # HTTPS (the site is served over https, so the API must be too): Caddy + automatic certificate
    command -v caddy || (apt-get update -qq && apt-get install -y -qq caddy)
    printf "%s {\n  reverse_proxy 127.0.0.1:8787\n}\n" "${HOST}" > /etc/caddy/Caddyfile
    systemctl restart caddy
    ufw allow 80/tcp || true; ufw allow 443/tcp || true'
  echo "API: https://$HOST/health"
  ;;
*) echo "usage: $0 create | ship IP"; exit 1 ;;
esac
