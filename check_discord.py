import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

token = os.getenv('DISCORD_TOKEN', '').strip()

print('─' * 40)
print('  Discord Token Checker')
print('─' * 40)

if not token:
    print('✗  DISCORD_TOKEN is missing from .env')
    exit(1)

print(f'Token: {token[:10]}...{token[-6:]}')
print('Checking...\n')

try:
    r = requests.get(
        'https://discord.com/api/v9/users/@me',
        headers={
            'Authorization': token,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        },
        timeout=8,
    )

    if r.status_code == 200:
        data = r.json()
        print(f'✓  Token is valid')
        print(f'   Username : {data.get("username")}')
        print(f'   User ID  : {data.get("id")}')
        print(f'   Email    : {data.get("email", "N/A")}')
        print(f'   Phone    : {"set" if data.get("phone") else "not set"}')
        print(f'   MFA      : {"enabled" if data.get("mfa_enabled") else "disabled"}')

        # Also test setting a custom status
        print('\nTesting status update...')
        r2 = requests.patch(
            'https://discordapp.com/api/v6/users/@me/settings',
            json={'custom_status': {'text': '✓ LyricSync test', 'expires_at': None}},
            headers={
                'Authorization': token,
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36',
            },
            timeout=8,
        )
        if r2.status_code == 200:
            print('✓  Status update works — check your Discord profile')
        else:
            print(f'✗  Status update failed: {r2.status_code} — {r2.text[:200]}')

    elif r.status_code == 401:
        print('✗  Token is invalid or expired')
        print('   Get a new token and update DISCORD_TOKEN in .env')
    elif r.status_code == 403:
        print('✗  Token is forbidden (possibly flagged by Discord)')
    else:
        print(f'✗  Unexpected response: {r.status_code}')
        print(f'   {r.text[:200]}')

except requests.exceptions.ConnectTimeout:
    print('✗  Connection timed out — check your internet connection')
except requests.exceptions.ConnectionError as e:
    print(f'✗  Connection error: {e}')
except Exception as e:
    print(f'✗  Unexpected error: {e}')

print('─' * 40)
