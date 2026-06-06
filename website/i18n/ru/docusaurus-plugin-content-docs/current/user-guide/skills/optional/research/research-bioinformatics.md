---
title: "Биоинформатика — Gateway к 400+ навыкам биоинформатики от bioSkills и ClawBio"
sidebar_label: "Bioinformatics"
description: "Шлюз к 400+ биоинформатических skills от bioSkills и ClawBio"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Биоинформатика

Шлюз к более чем 400 биоинформатическим навыкам из bioSkills и ClawBio. Охватывает геномику, транскриптомику, одноклеточные исследования, выявление вариантов, фармакогеномику, метагеномику, структурную биологию и многое другое. По запросу получает специализированные справочные материалы по домену.
## Метаданные навыка

| | |
|---|---|
| Источник | Опционально — установить с помощью `hermes skills install official/research/bioinformatics` |
| Путь | `optional-skills/research/bioinformatics` |
| Версия | `1.0.0` |
| Платформы | linux, macos |
| Теги | `bioinformatics`, `genomics`, `sequencing`, `biology`, `research`, `science` |
:::info
Следующее — полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# Шлюз навыков биоинформатики

Используй, когда тебя спрашивают о биоинформатике, геномике, секвенировании, определении вариантов, экспрессии генов, анализе одиночных клеток, структуре белков, фармакогеномике, метагеномике, филогенетике или любой задаче вычислительной биологии.

Этот навык представляет собой шлюз к двум открытым библиотекам навыков биоинформатики. Вместо того чтобы включать сотни специализированных навыков, он индексирует их и получает необходимое по запросу.
## Источники

◆ **bioSkills** — 385 справочных **skill** (шаблоны кода, руководства по параметрам, деревья решений)
Repo: https://github.com/GPTomics/bioSkills
Format: `SKILL.md` по теме с примерами кода. Python/R/CLI.

◆ **ClawBio** — 33 исполняемых **skill** конвейера (исполняемые скрипты, пакеты воспроизводимости)
Repo: https://github.com/ClawBio/ClawBio
Format: Python‑скрипты с демонстрациями. Каждый анализ экспортирует `report.md` + `commands.sh` + `environment.yml`.
## Как получить и использовать skill

1. Определи домен и название skill из индекса ниже.
2. Выполни поверхностное клонирование нужного репозитория, чтобы сэкономить время:
   ```bash
   # bioSkills (reference material)
   git clone --depth 1 https://github.com/GPTomics/bioSkills.git /tmp/bioSkills

   # ClawBio (runnable pipelines)
   git clone --depth 1 https://github.com/ClawBio/ClawBio.git /tmp/ClawBio
   ```
3. Ознакомься с конкретным skill:
   ```bash
   # bioSkills — each skill is at: <category>/<skill-name>/SKILL.md
   cat /tmp/bioSkills/variant-calling/gatk-variant-calling/SKILL.md

   # ClawBio — each skill is at: skills/<skill-name>/
   cat /tmp/ClawBio/skills/pharmgx-reporter/README.md
   ```
4. Используй полученный skill как справочный материал. Это **НЕ** skill в формате Hermes — рассматривай их как экспертные руководства по домену. Они содержат корректные параметры, правильные флаги инструментов и проверенные конвейеры.
## Индекс навыков по областям

### Основы последовательностей
bioSkills:
  sequence-io/ — read-sequences, write-sequences, format-conversion, batch-processing, compressed-files, fastq-quality, filter-sequences, paired-end-fastq, sequence-statistics
  sequence-manipulation/ — seq-objects, reverse-complement, transcription-translation, motif-search, codon-usage, sequence-properties, sequence-slicing
ClawBio:
  seq-wrangler — контроль качества последовательностей, выравнивание и обработка BAM (обёртка над FastQC, BWA, SAMtools)

### Контроль качества чтения и выравнивание
bioSkills:
  read-qc/ — quality-reports, fastp-workflow, adapter-trimming, quality-filtering, umi-processing, contamination-screening, rnaseq-qc
  read-alignment/ — bwa-alignment, star-alignment, hisat2-alignment, bowtie2-alignment
  alignment-files/ — sam-bam-basics, alignment-sorting, alignment-filtering, bam-statistics, duplicate-handling, pileup-generation

### Вызов вариантов и аннотация
bioSkills:
  variant-calling/ — gatk-variant-calling, deepvariant, variant-calling (bcftools), joint-calling, structural-variant-calling, filtering-best-practices, variant-annotation, variant-normalization, vcf-basics, vcf-manipulation, vcf-statistics, consensus-sequences, clinical-interpretation
ClawBio:
  vcf-annotator — VEP + ClinVar + gnomAD аннотация с учётом происхождения
  variant-annotation — конвейер аннотации вариантов

### Дифференциальная экспрессия (Bulk RNA‑seq)
bioSkills:
  differential-expression/ — deseq2-basics, edger-basics, batch-correction, de-results, de-visualization, timeseries-de
  rna-quantification/ — alignment-free-quant (Salmon/kallisto), featurecounts-counting, tximport-workflow, count-matrix-qc
  expression-matrix/ — counts-ingest, gene-id-mapping, metadata-joins, sparse-handling
ClawBio:
  rnaseq-de — полный конвейер DE с контролем качества, нормализацией и визуализацией
  diff-visualizer — расширенная визуализация и отчётность результатов DE

### Одноклеточный RNA‑seq
bioSkills:
  single-cell/ — preprocessing, clustering, batch-integration, cell-annotation, cell-communication, doublet-detection, markers-annotation, trajectory-inference, multimodal-integration, perturb-seq, scatac-analysis, lineage-tracing, metabolite-communication, data-io
ClawBio:
  scrna-orchestrator — полный конвейер Scanpy (QC, кластеризация, маркеры, аннотация)
  scrna-embedding — латентное встраивание на основе scVI и интеграция батчей

### Пространственная транскриптомика
bioSkills:
  spatial-transcriptomics/ — spatial-data-io, spatial-preprocessing, spatial-domains, spatial-deconvolution, spatial-communication, spatial-neighbors, spatial-statistics, spatial-visualization, spatial-multiomics, spatial-proteomics, image-analysis

### Эпигеномика
bioSkills:
  chip-seq/ — peak-calling, differential-binding, motif-analysis, peak-annotation, chipseq-qc, chipseq-visualization, super-enhancers
  atac-seq/ — atac-peak-calling, atac-qc, differential-accessibility, footprinting, motif-deviation, nucleosome-positioning
  methylation-analysis/ — bismark-alignment, methylation-calling, dmr-detection, methylkit-analysis
  hi-c-analysis/ — hic-data-io, tad-detection, loop-calling, compartment-analysis, contact-pairs, matrix-operations, hic-visualization, hic-differential
ClawBio:
  methylation-clock — оценка эпигенетического возраста

### Фармакогеномика и клинические данные
bioSkills:
  clinical-databases/ — clinvar-lookup, gnomad-frequencies, dbsnp-queries, pharmacogenomics, polygenic-risk, hla-typing, variant-prioritization, somatic-signatures, tumor-mutational-burden, myvariant-queries
ClawBio:
  pharmgx-reporter — PGx‑отчёт из 23andMe/AncestryDNA (12 генов, 31 SNP, 51 препарат)
  drug-photo — фото лекарства → персонализированная карта дозировки PGx (через зрение)
  clinpgx — ClinPGx API для данных «ген‑лекарство» и рекомендаций CPIC
  gwas-lookup — федеративный поиск вариантов по 9 геномным базам
  gwas-prs — полигенные рисковые оценки из потребительских генетических данных
  nutrigx_advisor — персонализированное питание из потребительских генетических данных

### Популяционная генетика и GWAS
bioSkills:
  population-genetics/ — association-testing (PLINK GWAS), plink-basics, population-structure, linkage-disequilibrium, scikit-allel-analysis, selection-statistics
  causal-genomics/ — mendelian-randomization, fine-mapping, colocalization-analysis, mediation-analysis, pleiotropy-detection
  phasing-imputation/ — haplotype-phasing, genotype-imputation, imputation-qc, reference-panels
ClawBio:
  claw-ancestry-pca — PCA предков против референс‑панели SGDP

### Метагеномика и микробиом
bioSkills:
  metagenomics/ — kraken-classification, metaphlan-profiling, abundance-estimation, functional-profiling, amr-detection, strain-tracking, metagenome-visualization
  microbiome/ — amplicon-processing, diversity-analysis, differential-abundance, taxonomy-assignment, functional-prediction, qiime2-workflow
ClawBio:
  claw-metagenomics — профилирование shotgun‑метагеномики (таксономия, резистом, функциональные пути)

### Сборка и аннотация генома
bioSkills:
  genome-assembly/ — hifi-assembly, long-read-assembly, short-read-assembly, metagenome-assembly, assembly-polishing, assembly-qc, scaffolding, contamination-detection
  genome-annotation/ — eukaryotic-gene-prediction, prokaryotic-annotation, functional-annotation, ncrna-annotation, repeat-annotation, annotation-transfer
  long-read-sequencing/ — basecalling, long-read-alignment, long-read-qc, clair3-variants, structural-variants, medaka-polishing, nanopore-methylation, isoseq-analysis

### Структурная биология и химическая информатика
bioSkills:
  structural-biology/ — alphafold-predictions, modern-structure-prediction, structure-io, structure-navigation, structure-modification, geometric-analysis
  chemoinformatics/ — molecular-io, molecular-descriptors, similarity-searching, substructure-search, virtual-screening, admet-prediction, reaction-enumeration
ClawBio:
  struct-predictor — локальное предсказание структуры AlphaFold/Boltz/Chai с сравнением

### Протеомика
bioSkills:
  proteomics/ — data-import, peptide-identification, protein-inference, quantification, differential-abundance, dia-analysis, ptm-analysis, proteomics-qc, spectral-libraries
ClawBio:
  proteomics-de — дифференциальная экспрессия в протеомике

### Анализ путей и генетические сети
bioSkills:
  pathway-analysis/ — go-enrichment, gsea, kegg-pathways, reactome-pathways, wikipathways, enrichment-visualization
  gene-regulatory-networks/ — scenic-regulons, coexpression-networks, differential-networks, multiomics-grn, perturbation-simulation

### Иммуноинформатика
bioSkills:
  immunoinformatics/ — mhc-binding-prediction, epitope-prediction, neoantigen-prediction, immunogenicity-scoring, tcr-epitope-binding
  tcr-bcr-analysis/ — mixcr-analysis, scirpy-analysis, immcantation-analysis, repertoire-visualization, vdjtools-analysis

### CRISPR и геномное редактирование
bioSkills:
  crispr-screens/ — mageck-analysis, jacks-analysis, hit-calling, screen-qc, library-design, crispresso-editing, base-editing-analysis, batch-correction
  genome-engineering/ — grna-design, off-target-prediction, hdr-template-design, base-editing-design, prime-editing-design

### Управление рабочими процессами
bioSkills:
  workflow-management/ — snakemake-workflows, nextflow-pipelines, cwl-workflows, wdl-workflows
ClawBio:
  repro-enforcer — экспорт любого анализа как пакета воспроизводимости (Conda env + Singularity + checksums)
  galaxy-bridge — доступ к 8 000+ инструментам Galaxy с usegalaxy.org

### Специализированные области
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

### Визуализация данных и отчётность
bioSkills:
  data-visualization/ — ggplot2-fundamentals, heatmaps-clustering, volcano-customization, circos-plots, genome-browser-tracks, interactive-visualization, multipanel-figures, network-visualization, upset-plots, color-palettes, specialized-omics-plots, genome-tracks
  reporting/ — rmarkdown-reports, quarto-reports, jupyter-reports, automated-qc-reports, figure-export
ClawBio:
  profile-report — отчёт профиля анализа
  data-extractor — извлечение числовых данных из изображений научных фигур (через зрение)
  lit-synthesizer — поиск PubMed/bioRxiv, суммирование, графы цитирований
  pubmed-summariser — поиск Gene/Disease в PubMed с структурированным брифингом

### Доступ к базам данных
bioSkills:
  database-access/ — entrez-search, entrez-fetch, entrez-link, blast-searches, local-blast, sra-data, geo-data, uniprot-access, batch-downloads, interaction-databases, sequence-similarity
ClawBio:
  ukb-navigator — семантический поиск по 12 000+ полям UK Biobank
  clinical-trial-finder — поиск клинических испытаний

### Экспериментальный дизайн
bioSkills:
  experimental-design/ — power-analysis, sample-size, batch-design, multiple-testing

### Машинное обучение для омics
bioSkills:
  machine-learning/ — omics-classifiers, biomarker-discovery, survival-analysis, model-validation, prediction-explanation, atlas-mapping
ClawBio:
  claw-semantic-sim — индекс семантической схожести для литературы о болезнях (PubMedBERT)
  omics-target-evidence-mapper — агрегирование доказательств уровня целей из разных омics‑источников
## Настройка окружения

Эти skills предполагают наличие биоинформатической рабочей станции. Общие зависимости:

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
## Подводные камни

- Полученные **skills** НЕ находятся в формате Hermes **SKILL.md**. Они используют собственную структуру (bioSkills: шаблоны кода и кулинарные книги; ClawBio: README + скрипты Python). Читай их как справочный материал для эксперта.
- bioSkills — справочные руководства: они показывают правильные параметры и шаблоны кода, но не являются исполняемыми **pipeline**.
- Навыки ClawBio исполняемы — многие имеют флаг `--demo` и могут быть запущены напрямую.
- Оба репозитория предполагают, что инструменты биоинформатики уже установлены. Проверь предварительные требования перед запуском **pipeline**.
- Для ClawBio сначала выполни `pip install -r requirements.txt` в клонированном репозитории.
- Файлы геномных данных могут быть очень большими. Следи за доступным дисковым пространством при загрузке референсных геномов, наборов данных SRA или построении индексов.