---
title: Geração de Imagens
description: Gere imagens via FAL.ai — 9 modelos incluindo FLUX 2, GPT Image (1.5 e 2), Nano Banana Pro, Ideogram, Recraft V4 Pro e mais, selecionáveis em `hermes tools`.
sidebar_label: Geração de Imagens
sidebar_position: 6
---

# Geração de Imagens

O Hermes Agent gera imagens a partir de prompts de texto via FAL.ai. Nove modelos são suportados de fábrica, cada um com diferentes trade-offs de velocidade, qualidade e custo. O modelo ativo é configurável pelo usuário via `hermes tools` e fica persistido em `config.yaml`.

## Modelos Suportados

| Modelo | Velocidade | Pontos fortes | Preço |
|---|---|---|---|
| `fal-ai/flux-2/klein/9b` *(padrão)* | `<1s` | Rápido, texto nítido | $0,006/MP |
| `fal-ai/flux-2-pro` | ~6s | Fotorrealismo de estúdio | $0,03/MP |
| `fal-ai/z-image/turbo` | ~2s | Bilíngue EN/CN, 6B parâmetros | $0,005/MP |
| `fal-ai/nano-banana-pro` | ~8s | Gemini 3 Pro, raciocínio profundo, renderização de texto | $0,15/imagem (1K) |
| `fal-ai/gpt-image-1.5` | ~15s | Aderência ao prompt | $0,034/imagem |
| `fal-ai/gpt-image-2` | ~20s | Renderização de texto SOTA + CJK, fotorrealismo com noção de mundo | $0,04–0,06/imagem |
| `fal-ai/ideogram/v3` | ~5s | Melhor tipografia | $0,03–0,09/imagem |
| `fal-ai/recraft/v4/pro/text-to-image` | ~8s | Design, sistemas de marca, pronto pra produção | $0,25/imagem |
| `fal-ai/qwen-image` | ~12s | Baseado em LLM, texto complexo | $0,02/MP |

Os preços são da FAL no momento desta escrita; consulte [fal.ai](https://fal.ai/) para os valores atuais.

## Setup

:::tip Assinantes Nous
Se você tem uma assinatura paga do [Nous Portal](https://portal.nousresearch.com), pode usar geração de imagens pelo **[Tool Gateway](tool-gateway.md)** sem chave de API da FAL. Sua escolha de modelo persiste nos dois caminhos.

Se o gateway gerenciado retornar `HTTP 4xx` para um modelo específico, esse modelo ainda não está sendo proxiado pelo lado do portal — o agente vai te avisar, com passos de remediação (defina `FAL_KEY` para acesso direto, ou escolha outro modelo).
:::

### Obtenha uma chave de API da FAL

1. Cadastre-se em [fal.ai](https://fal.ai/)
2. Gere uma chave de API no seu dashboard

### Configure e escolha um modelo

Rode o comando de tools:

```bash
hermes tools
```

Navegue até **🎨 Image Generation**, escolha seu backend (Nous Subscription ou FAL.ai) e o seletor mostra todos os modelos suportados numa tabela alinhada por colunas — setas pra navegar, Enter pra selecionar:

```
  Modelo                         Velocidade  Pontos fortes               Preço
  fal-ai/flux-2/klein/9b         <1s         Rápido, texto nítido        $0,006/MP   ← em uso
  fal-ai/flux-2-pro              ~6s         Fotorrealismo de estúdio    $0,03/MP
  fal-ai/z-image/turbo           ~2s         Bilíngue EN/CN, 6B          $0,005/MP
  ...
```

Sua seleção é salva em `config.yaml`:

```yaml
image_gen:
  model: fal-ai/flux-2/klein/9b
  use_gateway: false            # true se estiver usando Nous Subscription
```

### Qualidade do GPT-Image

A qualidade da requisição em `fal-ai/gpt-image-1.5` e `fal-ai/gpt-image-2` está fixada em `medium` (~$0,034–$0,06/imagem em 1024×1024). Não expomos os tiers `low` / `high` como opção visível ao usuário pra que o billing do Nous Portal fique previsível pra todo mundo — a diferença de custo entre tiers é de 3–22×. Se quiser uma opção mais barata, escolha Klein 9B ou Z-Image Turbo; se quiser maior qualidade, use Nano Banana Pro ou Recraft V4 Pro.

## Uso

O schema voltado pro agente é intencionalmente minimalista — o modelo pega o que você configurou:

```
Gere uma imagem de uma paisagem montanhosa serena com cerejeiras em flor
```

```
Crie um retrato quadrado de uma coruja velha e sábia — use o modelo de tipografia
```

```
Faz uma cidade futurista, orientação landscape
```

## Proporções (Aspect Ratios)

Todo modelo aceita as mesmas três proporções da perspectiva do agente. Internamente, a especificação nativa de tamanho de cada modelo é preenchida automaticamente:

| Entrada do agente | image_size (flux/z-image/qwen/recraft/ideogram) | aspect_ratio (nano-banana-pro) | image_size (gpt-image-1.5) | image_size (gpt-image-2) |
|---|---|---|---|---|
| `landscape` | `landscape_16_9` | `16:9` | `1536x1024` | `landscape_4_3` (1024×768) |
| `square` | `square_hd` | `1:1` | `1024x1024` | `square_hd` (1024×1024) |
| `portrait` | `portrait_16_9` | `9:16` | `1024x1536` | `portrait_4_3` (768×1024) |

GPT Image 2 mapeia pra presets 4:3 em vez de 16:9 porque sua contagem mínima de pixels é 655.360 — o preset `landscape_16_9` (1024×576 = 589.824) seria rejeitado.

Essa tradução acontece em `_build_fal_payload()` — o código do agente nunca precisa saber as diferenças de schema por modelo.

## Upscaling Automático

O upscaling via **Clarity Upscaler** da FAL é controlado por modelo:

| Modelo | Upscale? | Por quê |
|---|---|---|
| `fal-ai/flux-2-pro` | ✓ | Compatibilidade pra trás (era o padrão antes do seletor) |
| Todos os outros | ✗ | Modelos rápidos perderiam o valor de subsegundos; modelos hi-res não precisam |

Quando o upscaling roda, ele usa estas configurações:

| Configuração | Valor |
|---|---|
| Fator de upscale | 2× |
| Criatividade | 0,35 |
| Resemblance | 0,6 |
| Escala de guidance | 4 |
| Passos de inferência | 18 |

Se o upscaling falhar (problema de rede, rate limit), a imagem original é retornada automaticamente.

## Como Funciona Internamente

1. **Resolução do modelo** — `_resolve_fal_model()` lê `image_gen.model` do `config.yaml`, faz fallback pra variável de ambiente `FAL_IMAGE_MODEL` e depois pra `fal-ai/flux-2/klein/9b`.
2. **Construção do payload** — `_build_fal_payload()` traduz seu `aspect_ratio` pro formato nativo do modelo (preset enum, enum de aspect-ratio ou literal do GPT), mescla os parâmetros padrão do modelo, aplica overrides do chamador e depois filtra pela whitelist `supports` do modelo, então chaves não suportadas nunca são enviadas.
3. **Submissão** — `_submit_fal_request()` roteia via credenciais diretas da FAL ou pelo gateway gerenciado da Nous.
4. **Upscaling** — só roda se o metadata do modelo tiver `upscale: True`.
5. **Entrega** — URL final da imagem retornada ao agente, que emite uma tag `MEDIA:<url>` que os adaptadores de plataforma convertem em mídia nativa.

## Debugging

Habilite logs de debug:

```bash
export IMAGE_TOOLS_DEBUG=true
```

Os logs de debug vão pra `./logs/image_tools_debug_<session_id>.json` com detalhes por chamada (modelo, parâmetros, timing, erros).

## Entrega por Plataforma

| Plataforma | Entrega |
|---|---|
| **CLI** | URL da imagem impressa em markdown `![](url)` — clique pra abrir |
| **Telegram** | Mensagem de foto com o prompt como legenda |
| **Discord** | Embed numa mensagem |
| **Slack** | URL desdobrada pelo Slack |
| **WhatsApp** | Mensagem de mídia |
| **Outros** | URL em texto puro |

## Limitações

- **Requer credenciais da FAL** (`FAL_KEY` direta ou Nous Subscription)
- **Apenas text-to-image** — sem inpainting, img2img ou edição por essa ferramenta
- **URLs temporárias** — a FAL retorna URLs hospedadas que expiram em horas/dias; salve localmente se precisar
- **Restrições por modelo** — alguns modelos não suportam `seed`, `num_inference_steps` etc. O filtro `supports` descarta silenciosamente parâmetros não suportados; isso é comportamento esperado
