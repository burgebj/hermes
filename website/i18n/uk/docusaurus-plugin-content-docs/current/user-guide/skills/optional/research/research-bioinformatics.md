---
title: "Біоінформатика — gateway до 400+ навичок біоінформатики від bioSkills та ClawBio"
sidebar_label: "Bioinformatics"
description: "gateway до 400+ навичок біоінформатики від bioSkills та ClawBio"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Біоінформатика

Шлюз до 400+ біоінформатичних навичок від bioSkills та ClawBio. Охоплює геноміку, транскриптоміку, одноклітинний аналіз, виявлення варіантів, фармакогеноміку, метагеноміку, структурну біологію та інше. За потреби отримує специфічний для галузі довідковий матеріал.
## Метадані навички

| | |
|---|---|
| Джерело | Опціонально — встановити за допомогою `hermes skills install official/research/bioinformatics` |
| Шлях | `optional-skills/research/bioinformatics` |
| Версія | `1.0.0` |
| Платформи | linux, macos |
| Теги | `bioinformatics`, `genomics`, `sequencing`, `biology`, `research`, `science` |
:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Шлюз навичок біоінформатики

Використовуй, коли запитують про біоінформатику, геноміку, секвенування, визначення варіантів, експресію генів, аналіз одиничних клітин, структуру білків, фармакогеноміку, метагеномику, філогенетику або будь‑яке завдання комп’ютерної біології.

Ця навичка є шлюзом до двох відкритих бібліотек навичок біоінформатики. Замість того, щоб пакувати сотні спеціалізованих навичок, вона індексує їх і завантажує потрібне за запитом.
## Джерела

◆ **bioSkills** — 385 референсних навичок (шаблони коду, посібники з параметрів, дерева рішень)
  Repo: https://github.com/GPTomics/bioSkills
  Формат: `SKILL.md` за темою з прикладами коду. Python/R/CLI.

◆ **ClawBio** — 33 виконуваних pipeline‑навички (виконувані скрипти, пакети відтворюваності)
  Repo: https://github.com/ClawBio/ClawBio
  Формат: Python‑скрипти з демо. Кожен аналіз експортує `report.md` + `commands.sh` + `environment.yml`.
## Як отримати та використовувати skill

1. Визнач домен і назву skill у індексі нижче.
2. Клонуй відповідний репозиторій (shallow clone, щоб заощадити час):
   ```bash
   # bioSkills (reference material)
   git clone --depth 1 https://github.com/GPTomics/bioSkills.git /tmp/bioSkills

   # ClawBio (runnable pipelines)
   git clone --depth 1 https://github.com/ClawBio/ClawBio.git /tmp/ClawBio
   ```
3. Прочитай конкретну skill:
   ```bash
   # bioSkills — each skill is at: <category>/<skill-name>/SKILL.md
   cat /tmp/bioSkills/variant-calling/gatk-variant-calling/SKILL.md

   # ClawBio — each skill is at: skills/<skill-name>/
   cat /tmp/ClawBio/skills/pharmgx-reporter/README.md
   ```
4. Використовуй отриману skill як довідковий матеріал. Це НЕ skill у форматі Hermes — розглядай їх як експертні посібники за доменом. Вони містять правильні параметри, коректні прапорці інструментів та перевірені конвеєри.
## Індекс навичок за доменом
### Основи послідовностей
bioSkills:
  sequence-io/ — read-sequences, write-sequences, format-conversion, batch-processing, compressed-files, fastq-quality, filter-sequences, paired-end-fastq, sequence-statistics
  sequence-manipulation/ — seq-objects, reverse-complement, transcription-translation, motif-search, codon-usage, sequence-properties, sequence-slicing
ClawBio:
  seq-wrangler — Контроль якості послідовностей, вирівнювання та обробка BAM (wraps FastQC, BWA, SAMtools)
### QC та вирівнювання читань
bioSkills:
  read-qc/ — quality-reports, fastp-workflow, adapter-trimming, quality-filtering, umi-processing, contamination-screening, rnaseq-qc
  read-alignment/ — bwa-alignment, star-alignment, hisat2-alignment, bowtie2-alignment
  alignment-files/ — sam-bam-basics, alignment-sorting, alignment-filtering, bam-statistics, duplicate-handling, pileup-generation
### Визначення варіантів та анотація
bioSkills:
  variant-calling/ — gatk-variant-calling, deepvariant, variant-calling (bcftools), joint-calling, structural-variant-calling, filtering-best-practices, variant-annotation, variant-normalization, vcf-basics, vcf-manipulation, vcf-statistics, consensus-sequences, clinical-interpretation
ClawBio:
  vcf-annotator — аннотація VEP + ClinVar + gnomAD з урахуванням контексту походження
  variant-annotation — конвеєр анотації варіантів
### Диференціальна експресія (Bulk RNA‑seq)
bioSkills:
  differential-expression/ — deseq2-basics, edger-basics, batch-correction, de-results, de-visualization, timeseries-de
  rna-quantification/ — alignment-free-quant (Salmon/kallisto), featurecounts-counting, tximport-workflow, count-matrix-qc
  expression-matrix/ — counts-ingest, gene-id-mapping, metadata-joins, sparse-handling
ClawBio:
  rnaseq-de — повний конвеєр DE з QC, нормалізацією та візуалізацією
  diff-visualizer — розширена візуалізація та звітування результатів DE
### Одноклітинна RNA‑seq
bioSkills:
  single-cell/ — попередня обробка, кластеризація, інтеграція пакетів, анотація клітин, взаємодія клітин, виявлення дублетів, анотація маркерів, інференція траєкторій, мульти‑модальна інтеграція, perturb‑seq, аналіз scATAC, трасування ліній, взаємодія метаболітів, ввід‑вивід даних
ClawBio:
  scrna-orchestrator — повний конвеєр Scanpy (QC, кластеризація, маркери, анотація)
  scrna-embedding — латентне вбудовування на основі scVI та інтеграція пакетів
### Просторова транскриптоміка
bioSkills:
  spatial-transcriptomics/ — spatial-data-io, spatial-preprocessing, spatial-domains, spatial-deconvolution, spatial-communication, spatial-neighbors, spatial-statistics, spatial-visualization, spatial-multiomics, spatial-proteomics, image-analysis
### Епігеноміка
bioSkills:
  chip-seq/ — peak-calling, differential-binding, motif-analysis, peak-annotation, chipseq-qc, chipseq-visualization, super-enhancers
  atac-seq/ — atac-peak-calling, atac-qc, differential-accessibility, footprinting, motif-deviation, nucleosome-positioning
  methylation-analysis/ — bismark-alignment, methylation-calling, dmr-detection, methylkit-analysis
  hi-c-analysis/ — hic-data-io, tad-detection, loop-calling, compartment-analysis, contact-pairs, matrix-operations, hic-visualization, hic-differential
ClawBio:
  methylation-clock — оцінка епігенетичного віку
### Фармакогеноміка та клінічні
bioSkills:
  clinical-databases/ — clinvar-lookup, gnomad-frequencies, dbsnp-queries, pharmacogenomics, polygenic-risk, hla-typing, variant-prioritization, somatic-signatures, tumor-mutational-burden, myvariant-queries
ClawBio:
  pharmgx-reporter — PGx‑звіт від 23andMe/AncestryDNA (12 генів, 31 SNP, 51 препарат)
  drug-photo — Фото ліків → персоналізована карта дозування PGx (за допомогою зору)
  clinpgx — ClinPGx API для даних про гени‑препарати та рекомендацій CPIC
  gwas-lookup — Федеративний пошук варіантів у 9 геномних базах даних
  gwas-prs — Полігенні ризикові оцінки з даних споживчої генетики
  nutrigx_advisor — Персоналізоване харчування з даних споживчої генетики
### Генетика популяцій та GWAS
bioSkills:
  population-genetics/ — association-testing (PLINK GWAS), plink-basics, population-structure, linkage-disequilibrium, scikit-allel-analysis, selection-statistics
  causal-genomics/ — mendelian-randomization, fine-mapping, colocalization-analysis, mediation-analysis, pleiotropy-detection
  phasing-imputation/ — haplotype-phasing, genotype-imputation, imputation-qc, reference-panels
ClawBio:
  claw-ancestry-pca — PCA походження щодо референсної панелі SGDP
### Метагеноміка та мікробіом
bioSkills:
  metagenomics/ — kraken-classification, metaphlan-profiling, abundance-estimation, functional-profiling, amr-detection, strain-tracking, metagenome-visualization
  microbiome/ — amplicon-processing, diversity-analysis, differential-abundance, taxonomy-assignment, functional-prediction, qiime2-workflow
ClawBio:
  claw-metagenomics — Shotgun metagenomics profiling (taxonomy, resistome, functional pathways)
### Збірка та анотація геному
bioSkills:
  genome-assembly/ — hifi-assembly, long-read-assembly, short-read-assembly, metagenome-assembly, assembly-polishing, assembly-qc, scaffolding, contamination-detection
  genome-annotation/ — eukaryotic-gene-prediction, prokaryotic-annotation, functional-annotation, ncrna-annotation, repeat-annotation, annotation-transfer
  long-read-sequencing/ — basecalling, long-read-alignment, long-read-qc, clair3-variants, structural-variants, medaka-polishing, nanopore-methylation, isoseq-analysis
### Структурна біологія та хемоінформатика
bioSkills:
  structural-biology/ — alphafold-predictions, modern-structure-prediction, structure-io, structure-navigation, structure-modification, geometric-analysis
  chemoinformatics/ — molecular-io, molecular-descriptors, similarity-searching, substructure-search, virtual-screening, admet-prediction, reaction-enumeration
ClawBio:
  struct-predictor — Local AlphaFold/Boltz/Chai structure prediction with comparison
### Протеоміка
bioSkills:
  proteomics/ — імпорт даних, ідентифікація пептидів, інференція білків, квантифікація, диференціальна абунданція, dia‑аналіз, ptm‑аналіз, протеоміка‑QC, спектральні бібліотеки
ClawBio:
  proteomics-de — диференціальна експресія протеоміки
### Аналіз шляхів та генних мереж
bioSkills:
  pathway-analysis/ — go-enrichment, gsea, kegg-pathways, reactome-pathways, wikipathways, enrichment-visualization
  gene-regulatory-networks/ — scenic-regulons, coexpression-networks, differential-networks, multiomics-grn, perturbation-simulation
### Імуноінформатика
bioSkills:
  immunoinformatics/ — mhc-binding-prediction, epitope-prediction, neoantigen-prediction, immunogenicity-scoring, tcr-epitope-binding
  tcr-bcr-analysis/ — mixcr-analysis, scirpy-analysis, immcantation-analysis, repertoire-visualization, vdjtools-analysis
### CRISPR та інженерія геному
bioSkills:
  crispr-screens/ — mageck-analysis, jacks-analysis, hit-calling, screen-qc, library-design, crispresso-editing, base-editing-analysis, batch-correction
  genome-engineering/ — grna-design, off-target-prediction, hdr-template-design, base-editing-design, prime-editing-design
### Управління робочими процесами
bioSkills:
  workflow-management/ — snakemake-workflows, nextflow-pipelines, cwl-workflows, wdl-workflows
ClawBio:
  repro-enforcer — Експортуй будь‑який аналіз як пакет відтворюваності (Conda env + Singularity + контрольні суми)
  galaxy-bridge — Доступ до 8 000+ інструментів Galaxy з usegalaxy.org
### Спеціалізовані домени
bioSkills:
  alternative-splicing/ — splicing-quantification, differential-splicing, isoform-switching, sashimi-plots, single-cell-splicing, splicing-qc
  ecological-genomics/ — edna-metabarcoding, landscape-genomics, conservation-genetics, biodiversity-metrics, community-ecology, species-delimitation
  epidemiological-genomics/ — pathogen-typing, variant-surveillance, phylodynamics, transmission-inference, amr-surveillance
  liquid-biopsy/ — cfdna-preprocessing, ctdna-mutation-detection, fragment-analysis, tumor-fraction-estimation, methylation-based-detection, longitudinal-monitoring
  epitranscriptomics/ — m6a-peak-calling, m6a-differential, m6anet-analysis, merip-preprocessing, modification-visualization
  metabolomics/ — xcms-preprocessing, metabolite-annotation, normalization-qc, statistical-analysis, pathway-mapping, lipidomics, targeted-analysis, msdial-preprocessing
  flow-cytometry/ — fcs-handling, gating-analysis, compensation-transformation, clustering-phenotyping, differential-analysis, cytometry-qc, doublet-detection, bead-normalization
  systems-biology/ — flux-balance-analysis, metabolic-reconstruction, gene-essentiality, context-specific-models, model-curation
  rna-structure/ — secondary-structure-prediction, ncrna-search, structure-probing
### Візуалізація даних та звітність
bioSkills:
  data-visualization/ — ggplot2-fundamentals, heatmaps-clustering, volcano-customization, circos-plots, genome-browser-tracks, interactive-visualization, multipanel-figures, network-visualization, upset-plots, color-palettes, specialized-omics-plots, genome-tracks
  reporting/ — rmarkdown-reports, quarto-reports, jupyter-reports, automated-qc-reports, figure-export
ClawBio:
  profile-report — звіт профілю аналізу
  data-extractor — витяг числових даних із зображень наукових фігур (за допомогою зору)
  lit-synthesizer — пошук у PubMed/bioRxiv, резюмування, графи цитувань
  pubmed-summariser — пошук у PubMed за генами/хворобами зі структурованим брифінгом
### Доступ до бази даних
bioSkills:
  database-access/ — entrez-search, entrez-fetch, entrez-link, blast-searches, local-blast, sra-data, geo-data, uniprot-access, batch-downloads, interaction-databases, sequence-similarity
ClawBio:
  ukb-navigator — семантичний пошук у 12 000+ полях UK Biobank
  clinical-trial-finder — пошук клінічних випробувань
### Експериментальний дизайн
bioSkills:
  experimental-design/ — power-analysis, sample-size, batch-design, multiple-testing
### Машинне навчання для омікс
bioSkills:
  machine-learning/ — омікс‑класифікатори, виявлення біомаркерів, аналіз виживаності, валідація моделі, пояснення прогнозу, картографування атласу
ClawBio:
  claw-semantic-sim — індекс семантичної схожості для літератури про захворювання (PubMedBERT)
  omics-target-evidence-mapper — агрегувати доказову базу на рівні цілей з різних омікс‑джерел
## Налаштування середовища

Ці skills передбачають робочу станцію для біоінформатики. Загальні залежності:

```bash
# Python
pip install biopython pysam cyvcf2 pybedtools pyBigWig scikit-allel anndata scanpy mygene

# R/Bioconductor
Rscript -e 'BiocManager::install(c("DESeq2","edgeR","Seurat","clusterProfiler","methylKit"))'

# CLI tools (Ubuntu/Debian)
sudo apt install samtools bcftools ncbi-blast+ minimap2 bedtools

# CLI tools (macOS)
brew install samtools bcftools blast minimap2 bedtools

# Or via Conda (recommended for reproducibility)
conda install -c bioconda samtools bcftools blast minimap2 bedtools fastp kraken2
```
## Підводні камені

- Отримані навички НЕ у форматі Hermes SKILL.md. Вони використовують власну структуру (bioSkills: шаблони коду cookbooks; ClawBio: README + скрипти Python). Читай їх як експертний довідковий матеріал.
- bioSkills — це довідкові посібники: вони показують правильні параметри та шаблони коду, але не є виконуваними pipeline.
- Навички ClawBio є виконуваними — багато з них мають прапорці `--demo` і їх можна запускати безпосередньо.
- Обидва репозиторії передбачають, що інструменти біоінформатики встановлені. Перевір передумови перед запуском pipeline.
- Для ClawBio спочатку виконай `pip install -r requirements.txt` у клонованому репозиторії.
- Файли геномних даних можуть бути дуже великими. Слідкуй за вільним місцем на диску під час завантаження референсних геномів, наборів даних SRA або створення індексів.