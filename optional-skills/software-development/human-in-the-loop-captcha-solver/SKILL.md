---
name: human-in-the-loop-captcha-solver
description: Relay a reCAPTCHA widget to a human's phone for solving.
version: 1.0.0
author: Nathan (Argus-Metis)
license: MIT
platforms: [linux, macos]
prerequisites:
  commands: [cloudflared]
metadata:
  hermes:
    tags: [captcha, recaptcha, relay, tunnel, cloudflared, human-in-the-loop]
    related_skills: [hermes-skill-pr-prep]
    requires_toolsets: [terminal]
---

# Human-in-the-Loop Captcha Solver

Relay a reCAPTCHA v2/v2 Enterprise widget to a human's device via a temporary tunnel. The human solves it on their phone; the token comes back for injection into the target form.

No captcha solving services, no API keys, no headless browser. Just Python stdlib and a `cloudflared` binary.

## How It Works

reCAPTCHA tokens are scoped to **sitekey + domain**, not IP address or browser fingerprint. A token generated in Chrome on a phone works in headless Chromium on a VPS.

1. Agent starts a tiny HTTP server (Python stdlib)
2. Server serves a page containing the target's reCAPTCHA widget
3. `cloudflared` tunnel exposes it via HTTPS (free, no account needed)
4. Human opens the tunnel URL on their phone and ticks "I'm not a robot"
5. JS callback fires → XHR sends the token back through the tunnel
6. Server captures the token and shuts down
7. Agent injects the token into the target form and submits

Total time: ~30 seconds setup, ~5 seconds to solve. Page auto-destructs after 2 minutes.

## When to Use

- An automated workflow hits a reCAPTCHA v2 or v2 Enterprise challenge
- No paid captcha-solving service (2Captcha, Capsolver, etc.) is available
- A human is online and can solve a single checkbox in seconds
- The target form has a `g-recaptcha-response` textarea or sends a `g-recaptcha-response` field

## Prerequisites

- Python 3.8+ (stdlib only — no pip packages needed)
- `cloudflared` binary — [download](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) or `brew install cloudflared` / `apt install cloudflared`
- A phone or second device on a different network (mobile data recommended)

## How to Run

Two terminals are needed — one for the relay server, one for the tunnel.

```bash
# Terminal 1: start the relay server
cd ~/.hermes/skills/software-development/human-in-the-loop-captcha-solver
python3 scripts/captcha_relay.py --sitekey YOUR_SITEKEY --port 8443

# Terminal 2: expose via tunnel
cloudflared tunnel --url http://localhost:8443
```

Open the printed `trycloudflare.com` URL on a phone. Tap "I'm not a robot." The token prints to stdout and is saved to `/tmp/captcha_token.txt`.

## Quick Reference

| Action | Command |
|--------|---------|
| Start relay server | `python3 scripts/captcha_relay.py --sitekey SK --port 8443` |
| Test with Google test keys | `python3 scripts/captcha_test.py --port 8443` |
| Expose via tunnel | `cloudflared tunnel --url http://localhost:8443` |
| No-server alternative | Open `https://recaptcha-demo.appspot.com/recaptcha-v2-checkbox.php?sitekey=SK` on phone |
| Verify token | `curl -s "https://www.google.com/recaptcha/api/siteverify" -d "secret=TEST_SECRET" -d "response=$(cat /tmp/captcha_token.txt)"` |
| Google test sitekey | `6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI` |
| Google test secret | `6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe` |

## Procedure

### 1. Find the sitekey

```bash
web_extract(urls=["https://target-site.com/form"])
# Look for data-sitekey="..." or grecaptcha.render(...) in the page source
```

### 2. Start the relay

```bash
cd ~/.hermes/skills/software-development/human-in-the-loop-captcha-solver
python3 scripts/captcha_relay.py --sitekey SITEKEY --port 8443
```

The canonical script is at `scripts/captcha_relay.py`. It serves a mobile-optimised page with the reCAPTCHA widget and waits for a token submission.

If you prefer to test first: `python3 scripts/captcha_test.py --port 8443` uses Google's always-pass test sitekey.

### 3. Create the tunnel

In a separate terminal:

```bash
cloudflared tunnel --url http://localhost:8443
```

Copy the `https://<random>.trycloudflare.com` URL.

### 4. Solve on phone

Open the tunnel URL on a phone (use mobile data). Tap "I'm not a robot." The token auto-submits. The server prints `{"token": "03AFcWeA..."}` and exits.

### 5. Inject into the target form

```bash
# Read the token
TOKEN=$(cat /tmp/captcha_token.txt)
```

**For Playwright (JS-rendered forms):** Use native setters on the hidden `g-recaptcha-response` textarea:

```
page.evaluate("""
t => {
    const ta = document.getElementById('g-recaptcha-response');
    if (ta) {
        var setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
        setter.call(ta, t);
        ta.dispatchEvent(new Event('input', { bubbles: true }));
        ta.dispatchEvent(new Event('change', { bubbles: true }));
    }
}
""", TOKEN)
```

**For server-rendered forms:** POST directly with `g-recaptcha-response` as a form field.

### 6. Verify the submission

```bash
# The g-recaptcha-response value should be ~2100 chars starting with 03AF
head -c 20 /tmp/captcha_token.txt
```

## Pitfalls

- **Tunnel must serve plain HTTP.** Cloudflared sends plain HTTP to the origin. Do not wrap the relay server with SSL — that causes `connection reset by peer`.
- **Token expires in ~2 minutes.** Have your submit script ready before asking the human to solve. A solved token is consumed on first server-side verification and cannot be reused.
- **Token in file, not CLI arg.** Tokens are ~2100 chars with shell-special characters. Always use the token file, never pass as a command-line argument.
- **`print()` buffers in background mode.** If running the server as a background Hermes process, use `flush=True`.
- **Enterprise sitekeys** use `grecaptcha.enterprise.render()`. The relay script supports regular reCAPTCHA; for Enterprise, load `https://www.google.com/recaptcha/enterprise.js` instead of `api.js`. The `templates/captcha_page.html` template uses enterprise.js by default.
- **captcha doesn't appear on phone.** Adblockers, content blockers, or privacy extensions may block reCAPTCHA JS. Try Safari or Chrome incognito.
- **No-server shortcut.** For most reCAPTCHA v2 sitekeys, open `https://recaptcha-demo.appspot.com/recaptcha-v2-checkbox.php?sitekey=SITEKEY` on a phone. The token appears in a text box for copying. Skips the tunnel setup entirely.

## Verification

### Full pipeline test

```bash
# Terminal 1
cd ~/.hermes/skills/software-development/human-in-the-loop-captcha-solver
python3 scripts/captcha_test.py --port 8443

# Terminal 2
cloudflared tunnel --url http://localhost:8443
```

- Open the tunnel URL on a phone
- Tap "I'm not a robot" (uses Google test key — always passes, no image challenge)
- Server prints `{"token": "..."}` and exits
- Verify token file: `wc -c /tmp/captcha_token.txt` → ~2101 chars

### Infrastructure health checks

```bash
# Python HTTP serving works?
python3 -m http.server 8443 --bind 0.0.0.0 &>/dev/null &
curl -s -o /dev/null -w "%{http_code}" http://localhost:8443
# Expected: 200
kill %1 2>/dev/null

# cloudflared tunnels HTTP correctly?
python3 -m http.server 8443 --bind 0.0.0.0 &>/dev/null &
tunnel_url=$(cloudflared tunnel --url http://localhost:8443 2>&1 | grep -oP 'https://\S+\.trycloudflare\.com' | head -1)
curl -s -o /dev/null -w "%{http_code}" "$tunnel_url"
# Expected: 200
```

## File Structure

```
software-development/human-in-the-loop-captcha-solver/
├── SKILL.md                           # This file
├── scripts/
│   ├── captcha_relay.py               # Canonical relay server (Python stdlib)
│   └── captcha_test.py                # Test server with Google test keys
├── references/
│   ├── captcha-test-script.md         # Test key reference and usage
│   └── verification-guide.md          # Full end-to-end test procedure
└── templates/
    └── captcha_page.html              # Standalone HTML template (enterprise.js)
```

## References

- [Issue #12667](https://github.com/NousResearch/hermes-agent/issues/12667) — Feature request this skill addresses
- [reCAPTCHA v2 docs](https://developers.google.com/recaptcha/docs/display)
- [Google test keys](https://developers.google.com/recaptcha/docs/faq)
