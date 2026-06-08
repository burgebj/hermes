# Captcha Test Script

**File:** `scripts/captcha_test.py` (in the skill directory)

A standalone test server using Google's official test reCAPTCHA v2 sitekey (`6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI`) that **always passes No CAPTCHA** with no image challenges.

## Why Test Keys

Google provides test keys that always pass verification:
- **Site key:** `6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI`
- **Secret key:** `6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe`
- No CAPTCHA is ever shown — just a checkbox
- Widget shows warning banner: "This key is for testing purposes only"
- All server-side verification requests pass unconditionally

## Usage

```bash
# From the skill's scripts directory:
python3 scripts/captcha_test.py

# Or directly:
cd ~/.hermes/skills/software-development/human-in-the-loop-captcha-solver/scripts && python3 captcha_test.py
```

### Step 2: Tunnel

```bash
cloudflared tunnel --url http://localhost:8443
```

1. Open the tunnel URL on your phone
2. Tap "I'm not a robot" checkbox
3. Token auto-submits back via XHR
4. Server prints the token and shuts down

## What This Verifies

- cloudflared tunnel works (HTTPS → HTTP)
- reCAPTCHA JS loads correctly on mobile
- Token callback fires and XHR submits back through the tunnel
- Server receives and saves the token
- Full round-trip: user → tunnel → server → token returned

## Port

Uses port **8443** to avoid conflict with SearXNG (port 8080).
