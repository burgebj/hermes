
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const profileDir = '/root/.hermes/browser_profiles/linkedin';
  const out = {
    profileDir,
    session_ok: false,
    checks: [],
    markets: {}
  };

  function textOrEmpty(v) { return (v || '').replace(/\s+/g, ' ').trim(); }

  async function ensureLoggedIn(page) {
    await page.goto('https://www.linkedin.com/jobs/', { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(2500);
    const url = page.url();
    const title = await page.title();
    const body = textOrEmpty(await page.locator('body').innerText()).slice(0, 4000);
    out.checks.push({ step: 'jobs_landing', url, title, body_preview: body.slice(0, 400) });
    return !/login|signin|checkpoint|challenge/i.test(url) && /Jobs|My Jobs|Job alert|Preferences|Recommended for you/i.test(body + ' ' + title);
  }

  async function collectMarket(page, marketName, keywords, location) {
    const searchUrl = 'https://www.linkedin.com/jobs/search/?' + new URLSearchParams({
      keywords,
      location,
      f_WT: '2',
      f_JT: 'F',
      f_TPR: 'r2592000',
      position: '1',
      pageNum: '0'
    }).toString();
    await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(5000);

    // Gather top result cards quickly from search URL results
    const cards = page.locator('a[href*="/jobs/view/"]');
    const count = Math.min(await cards.count(), 12);
    const items = [];
    const seen = new Set();
    for (let i = 0; i < count; i++) {
      try {
        const a = cards.nth(i);
        const href = await a.getAttribute('href');
        if (!href) continue;
        const absHref = href.startsWith('http') ? href : ('https://www.linkedin.com' + href);
        const cleanHref = absHref.split('?')[0];
        if (seen.has(cleanHref)) continue;
        seen.add(cleanHref);
        const text = textOrEmpty(await a.innerText());
        if (!/jobs\/view\//.test(cleanHref)) continue;
        items.push({ href: cleanHref, text });
      } catch {}
    }

    // Visit a few top jobs and collect detail text
    const detailed = [];
    for (const item of items.slice(0, 6)) {
      try {
        await page.goto(item.href, { waitUntil: 'domcontentloaded', timeout: 60000 });
        await page.waitForTimeout(2500);
        const title = await page.title();
        const body = textOrEmpty(await page.locator('body').innerText()).slice(0, 5000);
        detailed.push({
          href: item.href,
          card_text: item.text,
          title,
          body_preview: body,
          closed: /No longer accepting applications/i.test(body)
        });
      } catch (e) {
        detailed.push({ href: item.href, card_text: item.text, error: String(e) });
      }
    }

    out.markets[marketName] = {
      search_keywords: keywords,
      location,
      items: detailed
    };
  }

  const context = await chromium.launchPersistentContext(profileDir, {
    headless: true,
    args: ['--disable-blink-features=AutomationControlled'],
    viewport: { width: 1440, height: 1024 },
  });
  const page = context.pages()[0] || await context.newPage();
  try {
    out.session_ok = await ensureLoggedIn(page);
    if (!out.session_ok) {
      console.log(JSON.stringify(out));
      await context.close();
      return;
    }
    await collectMarket(page, 'united_kingdom', 'Java OR JavaScript', 'United Kingdom');
    await collectMarket(page, 'emea', 'Java OR JavaScript remote EMEA', 'EMEA');
    // Language-agnostic searches — some senior roles don't care about specific languages
    await collectMarket(page, 'uk_lang_agnostic', 'Senior Software Engineer remote', 'United Kingdom');
    await collectMarket(page, 'emea_lang_agnostic', 'Senior Full Stack Developer remote EMEA', 'EMEA');
    console.log(JSON.stringify(out));
  } catch (e) {
    out.error = String(e);
    console.log(JSON.stringify(out));
  } finally {
    await context.close();
  }
})();
