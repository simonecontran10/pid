"""Carica un file su Cloudflare R2."""
import os
import sys
import boto3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

if len(sys.argv) < 2:
    print("Uso: python3 upload_to_r2.py <local_file_path> [remote_key]")
    sys.exit(1)

local_path = Path(sys.argv[1])
remote_key = sys.argv[2] if len(sys.argv) >= 3 else local_path.name

if not local_path.exists():
    print(f"File non esiste: {local_path}")
    sys.exit(1)

s3 = boto3.client(
    's3',
    endpoint_url=os.environ['R2_ENDPOINT'],
    aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
    region_name='auto',
)

bucket = os.environ['R2_BUCKET']
size_mb = local_path.stat().st_size / 1024 / 1024
print(f"Upload {local_path} ({size_mb:.1f} MB) -> R2 {bucket}/{remote_key}")

uploaded = [0]
total = local_path.stat().st_size

def progress(n):
    uploaded[0] += n
    pct = uploaded[0] * 100 / total
    print(f"\r  {pct:5.1f}%  ({uploaded[0]/1024/1024:.1f}/{size_mb:.1f} MB)", end='', flush=True)

s3.upload_file(
    str(local_path), bucket, remote_key,
    ExtraArgs={'ContentType': 'application/json'},
    Callback=progress,
)

print()
print(f"\nUpload completato!")
print(f"URL pubblico: {os.environ['R2_PUBLIC_URL']}/{remote_key}")
