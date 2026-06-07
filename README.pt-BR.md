<p align="center">
  <img src="assets/banner.png" alt="Hermes Agent" width="100%">
</p>

# Hermes Agent ☤

<p align="center">
  <a href="https://hermes-agent.nousresearch.com/docs/"><img src="https://img.shields.io/badge/Docs-hermes--agent.nousresearch.com-FFD700?style=for-the-badge" alt="Documentação"></a>
  <a href="https://discord.gg/NousResearch"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
  <a href="https://github.com/NousResearch/hermes-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="Licença: MIT"></a>
  <a href="https://nousresearch.com"><img src="https://img.shields.io/badge/Built%20by-Nous%20Research-blueviolet?style=for-the-badge" alt="Feito por Nous Research"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/Lang-English-lightgrey?style=for-the-badge" alt="English"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/Lang-中文-red?style=for-the-badge" alt="中文"></a>
</p>

**O agente de IA autoaperfeiçoante criado pela [Nous Research](https://nousresearch.com).** É o único agente com um loop de aprendizado embutido — ele cria habilidades a partir da experiência, aprimora elas durante o uso, se autoincentiva a persistir conhecimento, busca nas próprias conversas anteriores e constrói um modelo cada vez mais profundo de quem você é ao longo das sessões. Roda num VPS de $5, num cluster de GPU ou em infraestrutura serverless que custa quase nada quando ociosa. Não fica preso ao seu notebook — fale com ele pelo Telegram enquanto ele trabalha numa VM na nuvem.

Use qualquer modelo que quiser — [Nous Portal](https://portal.nousresearch.com), [OpenRouter](https://openrouter.ai) (200+ modelos), [NVIDIA NIM](https://build.nvidia.com) (Nemotron), [Xiaomi MiMo](https://platform.xiaomimimo.com), [z.ai/GLM](https://z.ai), [Kimi/Moonshot](https://platform.moonshot.ai), [MiniMax](https://www.minimax.io), [Hugging Face](https://huggingface.co), OpenAI ou seu próprio endpoint. Troque com `hermes model` — sem mudar código, sem aprisionamento.

<table>
<tr><td><b>Interface de terminal de verdade</b></td><td>TUI completa com edição multilinha, autocompletar de slash commands, histórico de conversa, interromper-e-redirecionar e saída de ferramenta em streaming.</td></tr>
<tr><td><b>Vive onde você está</b></td><td>Telegram, Discord, Slack, WhatsApp, Signal e CLI — tudo a partir de um único processo de gateway. Transcrição de mensagem de voz, continuidade de conversa entre plataformas.</td></tr>
<tr><td><b>Loop de aprendizado fechado</b></td><td>Memória curada pelo agente com lembretes periódicos. Criação autônoma de habilidades depois de tarefas complexas. Habilidades se aprimoram durante o uso. Busca de sessão FTS5 com sumarização por LLM para resgate entre sessões. Modelagem dialética de usuário com <a href="https://github.com/plastic-labs/honcho">Honcho</a>. Compatível com o padrão aberto <a href="https://agentskills.io">agentskills.io</a>.</td></tr>
<tr><td><b>Automações agendadas</b></td><td>Agendador cron embutido com entrega para qualquer plataforma. Relatórios diários, backups noturnos, auditorias semanais — tudo em linguagem natural, rodando sem supervisão.</td></tr>
<tr><td><b>Delega e paraleliza</b></td><td>Cria subagentes isolados para fluxos de trabalho paralelos. Escreva scripts Python que chamam ferramentas via RPC, comprimindo pipelines de múltiplos passos em turnos com custo de contexto zero.</td></tr>
<tr><td><b>Roda em qualquer lugar, não só no seu notebook</b></td><td>Sete backends de terminal — local, Docker, SSH, Singularity, Modal, Daytona e Vercel Sandbox. Daytona e Modal oferecem persistência serverless — o ambiente do seu agente hiberna quando ocioso e acorda sob demanda, custando quase nada entre sessões. Roda num VPS de $5 ou num cluster de GPU.</td></tr>
<tr><td><b>Pronto para pesquisa</b></td><td>Geração em lote de trajetórias, ambientes de RL Atropos, compressão de trajetórias para treinar a próxima geração de modelos com tool calling.</td></tr>
</table>

---

## Instalação rápida

### Linux, macOS, WSL2, Termux

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

### Windows (nativo, PowerShell) — Beta inicial

> **Atenção:** O suporte nativo ao Windows está em **beta inicial**. Instala e roda, mas ainda não foi testado tão amplamente quanto os caminhos Linux/macOS/WSL2. Por favor [abra issues](https://github.com/NousResearch/hermes-agent/issues) quando encontrar problemas. Para o setup mais estável no Windows hoje, rode o one-liner de Linux/macOS acima dentro do **WSL2**.

Execute no PowerShell:

```powershell
irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1 | iex
```

O instalador cuida de tudo: uv, Python 3.11, Node.js, ripgrep, ffmpeg **e um Git Bash portátil** (MinGit, descompactado em `%LOCALAPPDATA%\hermes\git` — sem precisar de admin, completamente isolado de qualquer instalação de Git do sistema). O Hermes usa esse Git Bash empacotado para rodar comandos shell.

Se você já tem Git instalado, o instalador detecta e usa esse. Caso contrário, um download de ~45MB do MinGit é tudo que você precisa — e ele não toca nem interfere em nenhum Git do sistema.

> **Android / Termux:** O caminho manual testado está documentado no [guia do Termux](https://hermes-agent.nousresearch.com/docs/getting-started/termux). No Termux, o Hermes instala um extra `.[termux]` curado, porque o extra completo `.[all]` puxa dependências de voz incompatíveis com Android.
>
> **Windows:** O Windows nativo é suportado como **beta inicial** — o one-liner do PowerShell acima instala tudo, mas espere imperfeições e por favor abra issues quando encontrar. Se preferir usar WSL2 (nosso caminho de Windows mais testado), o comando do Linux funciona lá também. A instalação nativa do Windows fica em `%LOCALAPPDATA%\hermes`; instalações WSL2 ficam em `~/.hermes` como no Linux. A única feature do Hermes que precisa especificamente de WSL2 hoje é o painel de chat baseado em navegador (usa um PTY POSIX — o CLI clássico e o gateway rodam ambos nativamente).

Após a instalação:

```bash
source ~/.bashrc    # recarrega o shell (ou: source ~/.zshrc)
hermes              # comece a conversar!
```

---

## Primeiros passos

```bash
hermes              # CLI interativo — comece uma conversa
hermes model        # Escolha o provedor de LLM e o modelo
hermes tools        # Configure quais ferramentas estão habilitadas
hermes config set   # Defina valores de configuração individuais
hermes gateway      # Inicia o gateway de mensagens (Telegram, Discord, etc.)
hermes setup        # Roda o assistente de setup completo (configura tudo de uma vez)
hermes claw migrate # Migra do OpenClaw (se estiver vindo do OpenClaw)
hermes update       # Atualiza para a versão mais recente
hermes doctor       # Diagnostica problemas
```

📖 **[Documentação completa →](https://hermes-agent.nousresearch.com/docs/)**

## Referência rápida: CLI x Mensagens

O Hermes tem dois pontos de entrada: inicie a UI do terminal com `hermes`, ou rode o gateway e fale com ele pelo Telegram, Discord, Slack, WhatsApp, Signal ou Email. Uma vez dentro da conversa, muitos slash commands funcionam igual nas duas interfaces.

| Ação | CLI | Plataformas de mensagem |
|---------|-----|---------------------|
| Começar a conversar | `hermes` | Rode `hermes gateway setup` + `hermes gateway start`, depois mande mensagem para o bot |
| Iniciar conversa nova | `/new` ou `/reset` | `/new` ou `/reset` |
| Trocar modelo | `/model [provider:model]` | `/model [provider:model]` |
| Definir personalidade | `/personality [name]` | `/personality [name]` |
| Refazer ou desfazer último turno | `/retry`, `/undo` | `/retry`, `/undo` |
| Comprimir contexto / ver uso | `/compress`, `/usage`, `/insights [--days N]` | `/compress`, `/usage`, `/insights [days]` |
| Listar habilidades | `/skills` ou `/<skill-name>` | `/<skill-name>` |
| Interromper trabalho atual | `Ctrl+C` ou enviar nova mensagem | `/stop` ou enviar nova mensagem |
| Status específico da plataforma | `/platforms` | `/status`, `/sethome` |

Para a lista completa de comandos, veja o [guia do CLI](https://hermes-agent.nousresearch.com/docs/user-guide/cli) e o [guia do Gateway de Mensagens](https://hermes-agent.nousresearch.com/docs/user-guide/messaging).

---

## Documentação

Toda a documentação fica em **[hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs/)**:

| Seção | O que cobre |
|---------|---------------|
| [Quickstart](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart) | Instalar → configurar → primeira conversa em 2 minutos |
| [Uso do CLI](https://hermes-agent.nousresearch.com/docs/user-guide/cli) | Comandos, atalhos de teclado, personalidades, sessões |
| [Configuração](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) | Arquivo de config, provedores, modelos, todas as opções |
| [Gateway de Mensagens](https://hermes-agent.nousresearch.com/docs/user-guide/messaging) | Telegram, Discord, Slack, WhatsApp, Signal, Home Assistant |
| [Segurança](https://hermes-agent.nousresearch.com/docs/user-guide/security) | Aprovação de comandos, pareamento via DM, isolamento por container |
| [Ferramentas e Toolsets](https://hermes-agent.nousresearch.com/docs/user-guide/features/tools) | 40+ ferramentas, sistema de toolsets, backends de terminal |
| [Sistema de Habilidades](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills) | Memória procedural, Skills Hub, criação de habilidades |
| [Memória](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) | Memória persistente, perfis de usuário, boas práticas |
| [Integração MCP](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp) | Conecte qualquer servidor MCP para ampliar capacidades |
| [Agendamento Cron](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron) | Tarefas agendadas com entrega entre plataformas |
| [Arquivos de Contexto](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files) | Contexto de projeto que molda cada conversa |
| [Arquitetura](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture) | Estrutura do projeto, loop do agente, classes principais |
| [Contribuir](https://hermes-agent.nousresearch.com/docs/developer-guide/contributing) | Setup de dev, processo de PR, estilo de código |
| [Referência do CLI](https://hermes-agent.nousresearch.com/docs/reference/cli-commands) | Todos os comandos e flags |
| [Variáveis de Ambiente](https://hermes-agent.nousresearch.com/docs/reference/environment-variables) | Referência completa de variáveis de ambiente |

---

## Migração do OpenClaw

Se você está vindo do OpenClaw, o Hermes pode importar automaticamente suas configurações, memórias, habilidades e chaves de API.

**Durante o setup inicial:** O assistente de setup (`hermes setup`) detecta `~/.openclaw` automaticamente e oferece migrar antes da configuração começar.

**A qualquer momento depois da instalação:**

```bash
hermes claw migrate              # Migração interativa (preset completo)
hermes claw migrate --dry-run    # Visualiza o que seria migrado
hermes claw migrate --preset user-data   # Migra sem segredos
hermes claw migrate --overwrite  # Sobrescreve conflitos existentes
```

O que é importado:
- **SOUL.md** — arquivo de persona
- **Memórias** — entradas de MEMORY.md e USER.md
- **Habilidades** — habilidades criadas pelo usuário → `~/.hermes/skills/openclaw-imports/`
- **Allowlist de comandos** — padrões de aprovação
- **Configurações de mensagem** — configs por plataforma, usuários permitidos, diretório de trabalho
- **Chaves de API** — segredos da allowlist (Telegram, OpenRouter, OpenAI, Anthropic, ElevenLabs)
- **Assets de TTS** — arquivos de áudio do workspace
- **Instruções de workspace** — AGENTS.md (com `--workspace-target`)

Veja `hermes claw migrate --help` para todas as opções, ou use a habilidade `openclaw-migration` para uma migração guiada por agente em modo interativo, com prévia em dry-run.

---

## Contribuir

Contribuições são bem-vindas! Veja o [Guia de Contribuição](https://hermes-agent.nousresearch.com/docs/developer-guide/contributing) para setup de desenvolvimento, estilo de código e processo de PR.

Início rápido para quem vai contribuir — clone e siga com `setup-hermes.sh`:

```bash
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
./setup-hermes.sh     # instala uv, cria venv, instala .[all], cria symlink ~/.local/bin/hermes
./hermes              # detecta o venv automaticamente, sem precisar `source`
```

Caminho manual (equivalente ao acima):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

> **Treinamento RL (opcional):** Para a integração com RL/Atropos (`environments/`) — veja [`CONTRIBUTING.md`](https://github.com/NousResearch/hermes-agent/blob/main/CONTRIBUTING.md#development-setup) para o setup completo.

---

## Comunidade

- 💬 [Discord](https://discord.gg/NousResearch)
- 📚 [Skills Hub](https://agentskills.io)
- 🐛 [Issues](https://github.com/NousResearch/hermes-agent/issues)
- 🔌 [HermesClaw](https://github.com/AaronWong1999/hermesclaw) — Bridge comunitário para WeChat: rode Hermes Agent e OpenClaw na mesma conta de WeChat.

---

## Licença

MIT — veja [LICENSE](LICENSE).

Feito pela [Nous Research](https://nousresearch.com).
