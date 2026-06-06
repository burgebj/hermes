---
name: scientific-skills
description: Gateway to 134+ specialized scientific skills from scientific-agent-skills. Covers 17 high-level domains including Bioinformatics, Cheminformatics, Medical Imaging, Physics, Laboratory Automation, and more. Fetches expert reference material on demand.
version: 1.1.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [science, biology, chemistry, physics, engineering, research, bioinformatics, cheminformatics, medical, data-science, analytics, lab-automation]
    category: research
---

# Scientific Agent Skills Gateway

Use when asked about molecular analysis, drug discovery, genomic/transcriptomic data processing, physics simulations, astronomical calculations, professional scientific writing, grant preparation, clinical reports, or any high-level scientific research task.

This skill is a gateway to the **scientific-agent-skills** library. Instead of bundling 134+ domain-specific skills, it indexes them across 17 specialized domains and fetches what you need on demand.

## Sources

◆ **scientific-agent-skills** — 134+ specialized scientific and research skills
  Repo: https://github.com/K-Dense-AI/scientific-agent-skills
  Format: SKILL.md per domain with expert patterns, references, and executable scripts.

## How to fetch and use a skill

1. Identify the domain and skill name from the index below.
2. Clone the repository to a temporary directory (e.g., `/tmp/science-library`).
   *   URL: `https://github.com/K-Dense-AI/scientific-agent-skills.git`
   *   Command Pattern: `git clone --depth 1 <URL> <TARGET_DIR>`
3. Read the specific skill:
   *   Path: `scientific-skills/<domain-name>/SKILL.md`
4. Use the fetched file as expert reference material for valid workflows and parameters.

## Skill Index (17 Official Domains)

### Bioinformatics & Genomics
scientific-agent-skills:
  anndata/ arboreto/ biopython/ bioservices/ cellxgene-census/ deeptools/ etetoolkit/ gget/
  gtars/ latchbio-integration/ phylogenetics/ polars-bio/ pydeseq2/ pysam/ scanpy/ scikit-bio/
  scvelo/ tiledbvcf/

### Cheminformatics & Drug Discovery
scientific-agent-skills:
  adaptyv/ datamol/ diffdock/ medchem/ molfeat/ rdkit/ rowan/ torchdrug/

### Proteomics & Mass Spectrometry
scientific-agent-skills:
  pyopenms/

### Clinical Research & Precision Medicine
scientific-agent-skills:
  clinical-decision-support/ clinical-reports/ pharmacogenomics/ treatment-plans/

### Healthcare AI & Clinical ML
scientific-agent-skills:
  pyhealth/ neurokit2/

### Medical Imaging & Digital Pathology
scientific-agent-skills:
  pydicom/ pathml/ histolab/ imaging-data-commons/ omero-integration/

### Machine Learning & AI
scientific-agent-skills:
  aeon/ geniml/ optimize-for-gpu/ pytorch-lightning/ scikit-learn/ scikit-survival/ shap/ stable-baselines3/
  transformers/ umap-learn/

### Materials Science & Chemistry
scientific-agent-skills:
  cobrapy/ molecular-dynamics/ pymatgen/

### Physics & Astronomy
scientific-agent-skills:
  astropy/ cirq/ pennylane/ qiskit/ qutip/ sympy/

### Engineering & Simulation
scientific-agent-skills:
  fluidsim/ simpy/ pymoo/

### Data Analysis & Visualization
scientific-agent-skills:
  dask/ exploratory-data-analysis/ matplotlib/ polars/ seaborn/ statistical-analysis/ statsmodels/ vaex/
  zarr-python/

### Geospatial Science & Remote Sensing
scientific-agent-skills:
  geomaster/ geopandas/

### Laboratory Automation
scientific-agent-skills:
  ginkgo-cloud-lab/ opentrons-integration/ pylabrobot/ protocolsio-integration/

### Scientific Communication
scientific-agent-skills:
  citation-management/ docx/ infographics/ latex-posters/ literature-review/ markdown-mermaid-writing/ market-research-reports/ markitdown/
  paper-lookup/ paperzilla/ parallel-web/ pdf/ peer-review/ pptx-posters/ pptx/ research-grants/
  scientific-schematics/ scientific-slides/ scientific-visualization/ scientific-writing/ venue-templates/ xlsx/ zotero/

### Multi-omics & Systems Biology
scientific-agent-skills:
  lamindb/ primekg/

### Protein Engineering & Design
scientific-agent-skills:
  esm/

### Research Methodology
scientific-agent-skills:
  consciousness-council/ hypogenic/ hypothesis-generation/ research-lookup/ scholar-evaluation/ scientific-brainstorming/ scientific-critical-thinking/ what-if-oracle/

### Specialized & Advanced Research Domains
scientific-agent-skills:
  generate-image/ pymc/ networkx/ depmap/ labarchive-integration/ flowio/ open-notebook/ pyzotero/
  neuropixels-analysis/ glycoengineering/ bgpt-paper-search/ matlab/ dnanexus-integration/ dhdna-profiler/ iso-13485-certification/ database-lookup/
  pytdc/ timesfm-forecasting/ usfiscaldata/ pufferlib/ deepchem/ benchling-integration/ torch-geometric/ matchms/
  scvi-tools/ get-available-resources/ modal/

## Environment Setup

These skills assume a scientific research workstation with Python 3.10+ installed.

### Required Packages
*   **Core**: `numpy`, `pandas`, `scipy`, `matplotlib`, `seaborn`, `scikit-learn`
*   **Domain Specific**: `biopython`, `pysam`, `rdkit`, `scanpy`, `anndata`, `astropy`, `qiskit`, `pennylane`

Example installation:
`pip install numpy pandas biopython rdkit scanpy`

## Pitfalls
- Skills are expert reference material, not Hermes-native bundles.
- API keys may be required for cloud-based tools (Benchling, Ginkgo, etc.).
- `uv` is recommended for high-performance dependency isolation.
