sudo tee /etc/systemd/system/techtitans.service >/dev/null <<'UNIT'
[Unit]
Description=TechTitans Flask API (Gunicorn)
After=network.target

[Service]
User=root
Group=root

WorkingDirectory=/root/Tech-Titans
Environment=PATH=/root/Tech-Titans/.venv/bin
Environment=FLASK_ENV=production
Environment=DATABASE_URL=postgresql+psycopg://postgres.eyusgrqfqybajhkgbuvv:wuO6reVRa60iWqzY@aws-0-ap-southeast-2.pooler.supabase.com:5432/postgres?sslmode=require

ExecStart=/root/Tech-Titans/.venv/bin/gunicorn \
  --bind 127.0.0.1:4000 \
  --workers 2 --threads 2 --timeout 60 \
	wsgi:app

Restart=always

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now techtitans
sudo systemctl status techtitans --no-pager
