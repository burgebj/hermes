---
title: "Drug Discovery — фармацевтичний помічник для робочих процесів відкриття препаратів"
sidebar_label: "Drug Discovery"
description: "Фармацевтичний асистент досліджень для робочих процесів відкриття препаратів"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Відкриття ліків

Помічник у фармацевтичних дослідженнях для робочих процесів відкриття ліків. Пошук біоактивних сполук у ChEMBL, розрахунок drug‑likeness (Lipinski Ro5, QED, TPSA, synthetic accessibility), пошук взаємодій препарат‑препарат через OpenFDA, інтерпретація профілів ADMET та допомога у оптимізації лід‑з’єднань. Використовуй для питань медичної хімії, аналізу властивостей молекул, клінічної фармакології та відкритих досліджень ліків.

## Метадані навички

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/research/drug-discovery` |
| Path | `optional-skills/research/drug-discovery` |
| Version | `1.0.0` |
| Author | bennytimz |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `science`, `chemistry`, `pharmacology`, `research`, `health` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Відкриття ліків та фармацевтичні дослідження

Ти — експерт‑фахівець у фармацевтичній науці та медичній хімії з глибокими знаннями у відкритті ліків, хемоінформатиці та клінічній фармакології. Використовуй цю навичку для усіх завдань досліджень у фармації/хімії.

## Основні робочі процеси

### 1 — Пошук біоактивних сполук (ChEMBL)

Пошук у ChEMBL (найбільшої у світі відкритої бази біоактивності) за цільовими об’єктами, активністю або назвою молекули. Ключ API не потрібен.

```bash
# Search compounds by target name (e.g. "EGFR", "COX-2", "ACE")
TARGET="$1"
ENCODED=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$TARGET")
curl -s "https://www.ebi.ac.uk/chembl/api/data/target/search?q=${ENCODED}&format=json" \
  | python3 -c "
import json,sys
data=json.load(sys.stdin)
targets=data.get('targets',[])[:5]
for t in targets:
    print(f\"ChEMBL ID : {t.get('target_chembl_id')}\")
    print(f\"Name      : {t.get('pref_name')}\")
    print(f\"Type      : {t.get('target_type')}\")
    print()
"
```

```bash
# Get bioactivity data for a ChEMBL target ID
TARGET_ID="$1"   # e.g. CHEMBL203
curl -s "https://www.ebi.ac.uk/chembl/api/data/activity?target_chembl_id=${TARGET_ID}&pchembl_value__gte=6&limit=10&format=json" \
  | python3 -c "
import json,sys
data=json.load(sys.stdin)
acts=data.get('activities',[])
print(f'Found {len(acts)} activities (pChEMBL >= 6):')
for a in acts:
    print(f\"  Molecule: {a.get('molecule_chembl_id')}  |  {a.get('standard_type')}: {a.get('standard_value')} {a.get('standard_units')}  |  pChEMBL: {a.get('pchembl_value')}\")
"
```

```bash
# Look up a specific molecule by ChEMBL ID
MOL_ID="$1"   # e.g. CHEMBL25 (aspirin)
curl -s "https://www.ebi.ac.uk/chembl/api/data/molecule/${MOL_ID}?format=json" \
  | python3 -c "
import json,sys
m=json.load(sys.stdin)
props=m.get('molecule_properties',{}) or {}
print(f\"Name       : {m.get('pref_name','N/A')}\")
print(f\"SMILES     : {m.get('molecule_structures',{}).get('canonical_smiles','N/A') if m.get('molecule_structures') else 'N/A'}\")
print(f\"MW         : {props.get('full_mwt','N/A')} Da\")
print(f\"LogP       : {props.get('alogp','N/A')}\")
print(f\"HBD        : {props.get('hbd','N/A')}\")
print(f\"HBA        : {props.get('hba','N/A')}\")
print(f\"TPSA       : {props.get('psa','N/A')} Å²\")
print(f\"Ro5 violations: {props.get('num_ro5_violations','N/A')}\")
print(f\"QED        : {props.get('qed_weighted','N/A')}\")
"
```

### 2 — Розрахунок drug‑likeness (Lipinski Ro5 + Veber)

Оцінка будь‑якої молекули за встановленими правилами оральної біодоступності за допомогою безкоштовного API властивостей PubChem — без необхідності встановлювати RDKit.

```bash
COMPOUND="$1"
ENCODED=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$COMPOUND")
curl -s "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/${ENCODED}/property/MolecularWeight,XLogP,HBondDonorCount,HBondAcceptorCount,RotatableBondCount,TPSA,InChIKey/JSON" \
  | python3 -c "
import json,sys
data=json.load(sys.stdin)
props=data['PropertyTable']['Properties'][0]
mw   = float(props.get('MolecularWeight', 0))
logp = float(props.get('XLogP', 0))
hbd  = int(props.get('HBondDonorCount', 0))
hba  = int(props.get('HBondAcceptorCount', 0))
rot  = int(props.get('RotatableBondCount', 0))
tpsa = float(props.get('TPSA', 0))
print('=== Lipinski Rule of Five (Ro5) ===')
print(f'  MW   {mw:.1f} Da    {\"✓\" if mw<=500 else \"✗ VIOLATION (>500)\"}')
print(f'  LogP {logp:.2f}       {\"✓\" if logp<=5 else \"✗ VIOLATION (>5)\"}')
print(f'  HBD  {hbd}           {\"✓\" if hbd<=5 else \"✗ VIOLATION (>5)\"}')
print(f'  HBA  {hba}           {\"✓\" if hba<=10 else \"✗ VIOLATION (>10)\"}')
viol = sum([mw>500, logp>5, hbd>5, hba>10])
print(f'  Violations: {viol}/4  {\"→ Likely orally bioavailable\" if viol<=1 else \"→ Poor oral bioavailability predicted\"}')
print()
print('=== Veber Oral Bioavailability Rules ===')
print(f'  TPSA         {tpsa:.1f} Å²   {\"✓\" if tpsa<=140 else \"✗ VIOLATION (>140)\"}')
print(f'  Rot. bonds   {rot}           {\"✓\" if rot<=10 else \"✗ VIOLATION (>10)\"}')
print(f'  Both rules met: {\"Yes → good oral absorption predicted\" if tpsa<=140 and rot<=10 else \"No → reduced oral absorption\"}')
"
```

### 3 — Пошук взаємодій препаратів та безпеки (OpenFDA)

```bash
DRUG="$1"
ENCODED=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$DRUG")
curl -s "https://api.fda.gov/drug/label.json?search=drug_interactions:\"${ENCODED}\"&limit=3" \
  | python3 -c "
import json,sys
data=json.load(sys.stdin)
results=data.get('results',[])
if not results:
    print('No interaction data found in FDA labels.')
    sys.exit()
for r in results[:2]:
    brand=r.get('openfda',{}).get('brand_name',['Unknown'])[0]
    generic=r.get('openfda',{}).get('generic_name',['Unknown'])[0]
    interactions=r.get('drug_interactions',['N/A'])[0]
    print(f'--- {brand} ({generic}) ---')
    print(interactions[:800])
    print()
"
```

```bash
DRUG="$1"
ENCODED=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$DRUG")
curl -s "https://api.fda.gov/drug/event.json?search=patient.drug.medicinalproduct:\"${ENCODED}\"&count=patient.reaction.reactionmeddrapt.exact&limit=10" \
  | python3 -c "
import json,sys
data=json.load(sys.stdin)
results=data.get('results',[])
if not results:
    print('No adverse event data found.')
    sys.exit()
print(f'Top adverse events reported:')
for r in results[:10]:
    print(f\"  {r['count']:>5}x  {r['term']}\")
"
```

### 4 — Пошук сполук у PubChem

```bash
COMPOUND="$1"
ENCODED=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$COMPOUND")
CID=$(curl -s "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/${ENCODED}/cids/TXT" | head -1 | tr -d '[:space:]')
echo "PubChem CID: $CID"
curl -s "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/${CID}/property/IsomericSMILES,InChIKey,IUPACName/JSON" \
  | python3 -c "
import json,sys
p=json.load(sys.stdin)['PropertyTable']['Properties'][0]
print(f\"IUPAC Name : {p.get('IUPACName','N/A')}\")
print(f\"SMILES     : {p.get('IsomericSMILES','N/A')}\")
print(f\"InChIKey   : {p.get('InChIKey','N/A')}\")
"
```

### 5 — Література про цілі та захворювання (OpenTargets)

```bash
GENE="$1"
curl -s -X POST "https://api.platform.opentargets.org/api/v4/graphql" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"{ search(queryString: \\\"${GENE}\\\", entityNames: [\\\"target\\\"], page: {index: 0, size: 1}) { hits { id score object { ... on Target { id approvedSymbol approvedName associatedDiseases(page: {index: 0, size: 5}) { count rows { score disease { id name } } } } } } } }\"}" \
  | python3 -c "
import json,sys
data=json.load(sys.stdin)
hits=data.get('data',{}).get('search',{}).get('hits',[])
if not hits:
    print('Target not found.')
    sys.exit()
obj=hits[0]['object']
print(f\"Target: {obj.get('approvedSymbol')} — {obj.get('approvedName')}\")
assoc=obj.get('associatedDiseases',{})
print(f\"Associated with {assoc.get('count',0)} diseases. Top associations:\")
for row in assoc.get('rows',[]):
    print(f\"  Score {row['score']:.3f}  |  {row['disease']['name']}\")
"
```

## Керівництво з міркувань

При аналізі drug‑likeness або властивостей молекул завжди:

1. **Спочатку вказуй сирі значення** — MW, LogP, HBD, HBA, TPSA, RotBonds
2. **Застосовуй набори правил** — Ro5 (Lipinski), Veber, фільтр Ghose, коли це доречно
3. **Позначай ризики** — метаболічні «гарячі точки», ризик hERG, високий TPSA для проникнення в ЦНС
4. **Пропонуй оптимізації** — біоізостеричні заміни, стратегії пролікворних препаратів, скорочення кільця
5. **Цитуй джерело API** — ChEMBL, PubChem, OpenFDA або OpenTargets

Для питань ADMET розмірковуй систематично через абсорбцію, розподіл, метаболізм, виведення, токсичність. Дивись references/ADMET_REFERENCE.md для докладних рекомендацій.

## Важливі нотатки

- Всі API безкоштовні, публічні, не вимагають автентифікації
- Ліміти запитів ChEMBL: додай паузу 1 секунда між пакетними запитами
- Дані FDA відображають повідомлені небажані події, не обов’язково причинно‑наслідкові
- Завжди рекомендуй консультуватися з ліцензованим фармацевтом або лікарем щодо клінічних рішень

## Швидка довідка

| Завдання | API | Endpoint |
|------|-----|----------|
| Знайти ціль | ChEMBL | `/api/data/target/search?q=` |
| Отримати біоактивність | ChEMBL | `/api/data/activity?target_chembl_id=` |
| Властивості молекули | PubChem | `/rest/pug/compound/name/{name}/property/` |
| Взаємодії препаратів | OpenFDA | `/drug/label.json?search=drug_interactions:` |
| Небажані події | OpenFDA | `/drug/event.json?search=...&count=reaction` |
| Ген‑захворювання | OpenTargets | GraphQL POST `/api/v4/graphql` |