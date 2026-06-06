---
title: "Domain Intel — Пассивный сбор информации о домене с использованием стандартной библиотеки Python"
sidebar_label: "Domain Intel"
description: "Пассивное исследование домена с использованием стандартной библиотеки Python"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Domain Intel

Пассивный сбор информации о домене с использованием стандартной библиотеки Python. Обнаружение поддоменов, проверка SSL‑сертификатов, WHOIS‑запросы, DNS‑записи, проверка доступности домена и массовый анализ нескольких доменов. Не требуется никаких API‑ключей.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/research/domain-intel` |
| Path | `optional-skills/research/domain-intel` |
| Platforms | linux, macos, windows |

## Reference: full SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# Domain Intelligence — Passive OSINT

Пассивный сбор информации о домене, используя только стандартную библиотеку Python.
**Никаких зависимостей. Никаких API‑ключей. Работает на Linux, macOS и Windows.**

## Helper script

Этот навык включает `scripts/domain_intel.py` — полноценный CLI‑инструмент для всех операций по разведке доменов.

```bash
# Subdomain discovery via Certificate Transparency logs
python3 SKILL_DIR/scripts/domain_intel.py subdomains example.com

# SSL certificate inspection (expiry, cipher, SANs, issuer)
python3 SKILL_DIR/scripts/domain_intel.py ssl example.com

# WHOIS lookup (registrar, dates, name servers — 100+ TLDs)
python3 SKILL_DIR/scripts/domain_intel.py whois example.com

# DNS records (A, AAAA, MX, NS, TXT, CNAME)
python3 SKILL_DIR/scripts/domain_intel.py dns example.com

# Domain availability check (passive: DNS + WHOIS + SSL signals)
python3 SKILL_DIR/scripts/domain_intel.py available coolstartup.io

# Bulk analysis — multiple domains, multiple checks in parallel
python3 SKILL_DIR/scripts/domain_intel.py bulk example.com github.com google.com
python3 SKILL_DIR/scripts/domain_intel.py bulk example.com github.com --checks ssl,dns
```

`SKILL_DIR` — каталог, содержащий этот файл SKILL.md. Весь вывод структурирован в JSON.

## Available commands

| Command | What it does | Data source |
|---------|-------------|-------------|
| `subdomains` | Find subdomains from certificate logs | crt.sh (HTTPS) |
| `ssl` | Inspect TLS certificate details | Direct TCP:443 to target |
| `whois` | Registration info, registrar, dates | WHOIS servers (TCP:43) |
| `dns` | A, AAAA, MX, NS, TXT, CNAME records | System DNS + Google DoH |
| `available` | Check if domain is registered | DNS + WHOIS + SSL signals |
| `bulk` | Run multiple checks on multiple domains | All of the above |

## When to use this vs built-in tools

- **Use this skill** for infrastructure questions: subdomains, SSL certs, WHOIS, DNS records, availability
- **Use `web_search`** for general research about what a domain/company does
- **Use `web_extract`** to get the actual content of a webpage
- **Use `terminal` with `curl -I`** for a simple “is this URL reachable” check

| Task | Better tool | Why |
|------|-------------|-----|
| "What does example.com do?" | `web_extract` | Gets page content, not DNS/WHOIS data |
| "Find info about a company" | `web_search` | General research, not domain-specific |
| "Is this website safe?" | `web_search` | Reputation checks need web context |
| "Check if a URL is reachable" | `terminal` with `curl -I` | Simple HTTP check |
| "Find subdomains of X" | **This skill** | Only passive source for this |
| "When does the SSL cert expire?" | **This skill** | Built-in tools can't inspect TLS |
| "Who registered this domain?" | **This skill** | WHOIS data not in web search |
| "Is coolstartup.io available?" | **This skill** | Passive availability via DNS+WHOIS+SSL |

## Platform compatibility

Чистая стандартная библиотека Python (`socket`, `ssl`, `urllib`, `json`, `concurrent.futures`). Работает одинаково на Linux, macOS и Windows без дополнительных зависимостей.

- **crt.sh queries** используют HTTPS (порт 443) — работают за большинством межсетевых экранов
- **WHOIS queries** используют TCP‑порт 43 — могут быть заблокированы в ограниченных сетях
- **DNS queries** используют Google DoH (HTTPS) для MX/NS/TXT — дружественно к межсетевым экранам
- **SSL checks** подключаются к цели на порт 443 — единственная «активная» операция

## Data sources

Все запросы **пассивные** — нет сканирования портов, нет тестирования уязвимостей:

- **crt.sh** — журналы Certificate Transparency (обнаружение поддоменов, только HTTPS)
- **WHOIS servers** — прямой TCP к более чем 100 авторитетным регистраторам TLD
- **Google DNS-over-HTTPS** — разрешение MX, NS, TXT, CNAME (дружественно к межсетевым экранам)
- **System DNS** — разрешение записей A/AAAA
- **SSL check** — единственная «активная» операция (TCP‑соединение к target:443)

## Notes

- WHOIS queries use TCP port 43 — могут быть заблокированы в ограниченных сетях.
- Некоторые WHOIS‑серверы скрывают данные о регистранте (GDPR) — обязательно сообщай об этом пользователю.
- crt.sh может работать медленно для очень популярных доменов (тысячи сертификатов) — устанавливай реалистичные ожидания.
- Проверка доступности основана на эвристиках (3 пассивных сигнала) — не является официальным подтверждением, как у API регистратора.

---

*Contributed by [@FurkanL0](https://github.com/FurkanL0)*