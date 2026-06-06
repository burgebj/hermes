#!/usr/bin/env python3
"""
SkillHub skill installer for Hermes.
Downloads a skill from SkillHub (skillhub.cn) and installs to Hermes.

Usage:
    python3 install_skill.py <skill-slug>
    python3 install_skill.py <skillhub-url>

Examples:
    python3 install_skill.py baidu-search
    python3 install_skill.py https://skillhub.cn/skills/baidu-search
"""
import sys, os, json, re, zipfile, tempfile, shutil, urllib.request, urllib.parse

HERMES_SKILLS_DIR = os.path.expanduser("~/.hermes/skills")
API_BASE = "https://api.skillhub.cn"
DOWNLOAD_URL = f"{API_BASE}/api/v1/download?slug={{slug}}"
SKILL_DETAIL_URL = f"{API_BASE}/api/v1/skills/{{slug}}"

# Map SkillHub keywords to Hermes categories
CATEGORY_MAP = {
    "web": "productivity", "search": "productivity", "baidu": "productivity",
    "google": "productivity", "browser": "productivity",
    "github": "github", "git": "github", "code": "software-development",
    "dev": "software-development", "pr": "github", "issue": "github",
    "mlops": "mlops", "ml": "mlops", "train": "mlops", "model": "mlops",
    "inference": "mlops", "fine-tuning": "mlops", "llm": "mlops",
    "creative": "creative", "art": "creative", "image": "creative",
    "video": "creative", "music": "creative", "ascii": "creative",
    "data": "data-science", "analysis": "data-science", "jupyter": "data-science",
    "email": "email", "mail": "email",
    "game": "gaming", "minecraft": "gaming", "pokemon": "gaming",
    "home": "smart-home", "hue": "smart-home", "light": "smart-home",
    "social": "social-media", "twitter": "social-media", "x": "social-media",
    "note": "note-taking", "obsidian": "note-taking",
    "research": "research", "paper": "research", "arxiv": "research",
    "cron": "devops", "webhook": "devops", "docker": "devops",
    "mcp": "mcp",
    "media": "media", "youtube": "media", "gif": "media",
    "red-team": "red-teaming", "godmode": "red-teaming",
}


def parse_slug(input_str):
    """Extract slug from URL or direct input."""
    if input_str.startswith("http"):
        parts = input_str.rstrip("/").split("/")
        if len(parts) >= 2:
            return parts[-1]
    # Direct slug
    if re.match(r'^[\w-]+$', input_str):
        return input_str
    return None


def get_skill_detail(slug):
    """Get skill metadata from SkillHub API."""
    url = SKILL_DETAIL_URL.format(slug=slug)
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; Hermes-Skill-Installer/1.0)",
            "Accept": "application/json",
        })
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [Skill detail fetch failed: {e}]")
        return None


def download_skill(slug, tmpdir):
    """Download skill zip from SkillHub API."""
    url = DOWNLOAD_URL.format(slug=slug)
    zip_path = os.path.join(tmpdir, f"{slug}.zip")

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; Hermes-Skill-Installer/1.0)"
        })
        resp = urllib.request.urlopen(req, timeout=60)
        with open(zip_path, "wb") as f:
            f.write(resp.read())
        return zip_path
    except Exception as e:
        print(f"  [Download failed: {e}]")
        return None


def extract_package(zip_path, tmpdir):
    """Extract zip and return file list."""
    extract_dir = os.path.join(tmpdir, "extracted")
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(extract_dir)
        return z.namelist()


def convert_frontmatter(md_content):
    """Convert OpenClaw frontmatter to Hermes format."""
    fm_match = re.match(r'^---\n(.*?)\n---', md_content, re.DOTALL)
    if not fm_match:
        return md_content

    old_fm = fm_match.group(1)

    name_match = re.search(r'name:\s*(.+)', old_fm)
    desc_match = re.search(r'description:\s*(.+)', old_fm)

    tags = []
    meta_match = re.search(r'metadata.*?"env".*?\[(.*?)\]', old_fm, re.DOTALL)
    if meta_match:
        env_vars = [v.strip().strip('"').strip("'") for v in meta_match.group(1).split(',')]
        tags.extend([v.lower().replace('_', '-') for v in env_vars[:3]])

    bins_match = re.search(r'"bins".*?\[(.*?)\]', old_fm, re.DOTALL)
    if bins_match:
        bins = [v.strip().strip('"').strip("'") for v in bins_match.group(1).split(',')]
        tags.extend([f"requires-{b.lower()}" for b in bins[:2]])

    name = name_match.group(1).strip() if name_match else "unknown"
    desc = desc_match.group(1).strip() if desc_match else ""
    desc = re.sub(r'OpenClaw', 'Hermes', desc)

    new_fm = f'---\nname: {name}\ndescription: {desc}\ntags: [{", ".join(tags)}]\n---'

    body = md_content[fm_match.end():]
    body = re.sub(r'OpenClaw', 'Hermes', body)
    body = re.sub(r'openclaw skills install', 'skill_manage', body)

    return new_fm + body


def determine_category(skill_name, description, meta=None):
    """Map skill to Hermes category based on name and description."""
    text = f"{skill_name} {description}".lower()

    if meta:
        env_vars = meta.get("requires", {}).get("env", [])
        bins = meta.get("requires", {}).get("bins", [])
        text += " " + " ".join(env_vars + bins)

    best_score = 0
    best_category = "productivity"

    for keyword, category in CATEGORY_MAP.items():
        if keyword in text:
            score = len(keyword)
            if score > best_score:
                best_score = score
                best_category = category

    return best_category


def install_to_hermes(skill_name, converted_md, scripts_dir, category):
    """Install skill to Hermes."""
    target_dir = os.path.join(HERMES_SKILLS_DIR, category, skill_name)

    existing_md = os.path.join(target_dir, "SKILL.md")
    if os.path.exists(existing_md):
        print(f"  [!] Skill '{skill_name}' already exists in category '{category}'")
        print(f"      Will update existing skill.")

    print(f"\n  Target: {target_dir}")
    print(f"  Category: {category}")

    if os.path.exists(scripts_dir):
        for root, dirs, files in os.walk(scripts_dir):
            for f in files:
                filepath = os.path.join(root, f)
                relpath = os.path.relpath(filepath, scripts_dir)
                print(f"  Script: {relpath}")

    return target_dir


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 install_skill.py <skill-slug>")
        print("       python3 install_skill.py <skillhub-url>")
        print("\nExamples:")
        print("  python3 install_skill.py baidu-search")
        print("  python3 install_skill.py https://skillhub.cn/skills/baidu-search")
        sys.exit(1)

    slug = parse_slug(sys.argv[1])
    if not slug:
        print(f"Error: Could not parse skill slug from '{sys.argv[1]}'")
        sys.exit(1)

    print(f"Installing skill: {slug}")

    tmpdir = tempfile.mkdtemp(prefix="skill-install-")
    try:
        # Step 1: Get skill details
        print("\n[1/5] Fetching skill info...")
        detail = get_skill_detail(slug)
        if detail and detail.get("data"):
            data = detail["data"]
            display_name = data.get("displayName", slug)
            version = data.get("version", "?")
            downloads = data.get("stats", {}).get("downloads", 0)
            print(f"  Name: {display_name}")
            print(f"  Version: {version}")
            print(f"  Downloads: {downloads:,}")

        # Step 2: Download
        print("\n[2/5] Downloading...")
        zip_path = download_skill(slug, tmpdir)
        if not zip_path:
            print("  [!] Download failed.")
            print("  [!] Please download the zip manually from:")
            print(f"  [!]     https://skillhub.cn/skills/{slug}")
            print(f"  [!] And extract it to:")
            print(f"  [!]     ~/.hermes/skills/<category>/{slug}/")
            sys.exit(1)
        print(f"  Downloaded: {zip_path}")

        # Step 3: Extract
        print("\n[3/5] Extracting...")
        files = extract_package(zip_path, tmpdir)
        extract_dir = os.path.join(tmpdir, "extracted")
        for f in files:
            print(f"  {f}")

        # Step 4: Read and convert
        print("\n[4/5] Converting...")
        skill_md_path = os.path.join(extract_dir, "SKILL.md")
        if not os.path.exists(skill_md_path):
            print("  [!] SKILL.md not found in package")
            sys.exit(1)

        with open(skill_md_path, "r", encoding="utf-8") as f:
            original_md = f.read()

        converted_md = convert_frontmatter(original_md)

        meta = None
        meta_path = os.path.join(extract_dir, "_meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

        # Step 5: Determine category and install
        print("\n[5/5] Installing...")
        desc_match = re.search(r'^description:\s*(.+)', converted_md, re.MULTILINE)
        description = desc_match.group(1) if desc_match else ""
        category = determine_category(slug, description, meta)
        print(f"  Category: {category}")

        if meta:
            bins = meta.get("requires", {}).get("bins", [])
            envs = meta.get("requires", {}).get("env", [])
            if bins:
                print(f"  Required binaries: {', '.join(bins)}")
            if envs:
                print(f"  Required env vars: {', '.join(envs)}")
                missing = [e for e in envs if not os.getenv(e)]
                if missing:
                    print(f"  [!] Missing env vars: {', '.join(missing)}")

        scripts_dir = os.path.join(extract_dir, "scripts")
        target_dir = install_to_hermes(slug, converted_md, scripts_dir, category)

        os.makedirs(target_dir, exist_ok=True)
        with open(os.path.join(target_dir, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write(converted_md)

        if os.path.exists(scripts_dir):
            scripts_target = os.path.join(target_dir, "scripts")
            os.makedirs(scripts_target, exist_ok=True)
            for root, dirs, files in os.walk(scripts_dir):
                for fn in files:
                    src = os.path.join(root, fn)
                    rel = os.path.relpath(src, scripts_dir)
                    dst = os.path.join(scripts_target, rel)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)
                    if fn.endswith(".py"):
                        os.chmod(dst, 0o755)

        print(f"\n  [OK] Skill '{slug}' installed to {target_dir}")

        print(f"\n{'='*50}")
        print(f"  Skill: {slug}")
        print(f"  Category: {category}")
        print(f"  Path: {target_dir}")
        if meta:
            envs = meta.get("requires", {}).get("env", [])
            if envs:
                print(f"\n  Next steps:")
                for env in envs:
                    if not os.getenv(env):
                        print(f"    export {env}='your-value'")
        print(f"{'='*50}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
