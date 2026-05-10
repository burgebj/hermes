"""
Kanban Review Gate — post-implementation review agent.

Runs after Hermes/subagents implement a task, before marking it done.
1. Collects what changed
2. Builds a review brief
3. Asks Codex to review the implementation
4. Asks DeepSeek V4 Pro for independent review
5. Compares both reviews
6. Creates fix cards if needed, or marks done
"""

import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests

logger = logging.getLogger(__name__)


class KanbanReviewGate:
    """Post-implementation review gate for Hermes."""
    
    def __init__(self, vault_path: str, codex_wrapper: str = "/Users/chrismarkert/.hermes/bin/codex-planner"):
        self._vault_path = Path(vault_path)
        self._codex_wrapper = codex_wrapper
        self._deepseek_api_key = self._load_deepseek_key()
        
    def _load_deepseek_key(self) -> str:
        """Load DeepSeek API key from environment or .env file."""
        key = os.getenv("DEEPSEEK_API_KEY", "")
        if not key:
            env_file = Path.home() / ".hermes" / ".env"
            if env_file.exists():
                with open(env_file) as f:
                    for line in f:
                        if line.startswith("DEEPSEEK_API_KEY="):
                            key = line.split("=", 1)[1].strip().strip('"').strip("'")
                            break
        return key
    
    def run_review(
        self,
        original_goal: str,
        chosen_plan: str,
        files_changed: List[str],
        commands_run: List[str],
        services_restarted: List[str],
        kanban_cards_changed: List[str],
        evidence: Dict[str, str],
        known_concerns: List[str]
    ) -> Dict[str, Any]:
        """Run the full review gate.
        
        Returns:
            {
                "decision": "approve" | "fix_first" | "ask_chris",
                "codex_findings": str,
                "deepseek_findings": str,
                "consolidated_fixes": List[str],
                "recommendation": str
            }
        """
        # Build review brief
        brief = self._build_review_brief(
            original_goal, chosen_plan, files_changed, commands_run,
            services_restarted, kanban_cards_changed, evidence, known_concerns
        )
        
        # Save brief to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(brief)
            brief_path = f.name
        
        # Run Codex review
        codex_findings = self._codex_review(brief_path)
        
        # Run DeepSeek review
        deepseek_findings = self._deepseek_review(brief)
        
        # Consolidate
        result = self._consolidate_reviews(
            codex_findings, deepseek_findings, files_changed
        )
        
        # Cleanup
        Path(brief_path).unlink(missing_ok=True)
        
        return result
    
    def _build_review_brief(
        self,
        original_goal: str,
        chosen_plan: str,
        files_changed: List[str],
        commands_run: List[str],
        services_restarted: List[str],
        kanban_cards_changed: List[str],
        evidence: Dict[str, str],
        known_concerns: List[str]
    ) -> str:
        """Build the review brief markdown."""
        parts = [
            "# Review Brief",
            "",
            "## Original Goal",
            original_goal,
            "",
            "## Chosen Plan",
            chosen_plan,
            "",
            "## What Hermes Changed",
        ]
        
        if files_changed:
            parts.append("### Files Modified")
            for f in files_changed:
                parts.append(f"- `{f}`")
            parts.append("")
            
        if commands_run:
            parts.append("### Commands Run")
            for c in commands_run:
                parts.append(f"- `{c}`")
            parts.append("")
            
        if services_restarted:
            parts.append("### Services Restarted")
            for s in services_restarted:
                parts.append(f"- `{s}`")
            parts.append("")
            
        if kanban_cards_changed:
            parts.append("### Kanban Cards Changed")
            for k in kanban_cards_changed:
                parts.append(f"- `{k}`")
            parts.append("")
        
        parts.extend([
            "## Evidence",
            ""
        ])
        
        for key, value in evidence.items():
            parts.append(f"### {key}")
            # Truncate long values
            if len(value) > 500:
                value = value[:500] + "..."
            parts.append(value)
            parts.append("")
        
        if known_concerns:
            parts.extend([
                "## Known Concerns",
                ""
            ])
            for c in known_concerns:
                parts.append(f"- {c}")
            parts.append("")
        
        parts.extend([
            "## Requested Review Output",
            "Return:",
            "1. bugs or regressions",
            "2. missing tests/checks",
            "3. unsafe assumptions",
            "4. whether the work satisfies the original goal",
            "5. fixes required before Chris should trust it",
            "6. approval recommendation: approve / fix first / ask Chris"
        ])
        
        return "\n".join(parts)
    
    def _codex_review(self, brief_path: str) -> str:
        """Send brief to Codex for review."""
        prompt = """You are Codex acting as Chris's implementation reviewer for Hermes.

Hermes has implemented the work described in the review brief.

Do not implement changes yourself unless explicitly asked. Review the work.

Prioritise:
- bugs
- broken assumptions
- missing verification
- changes that do not satisfy Chris's actual request
- risky memory/config/service changes
- places where Hermes is about to say "done" too early

Return:
- Findings ordered by severity
- Exact files/commands/logs to inspect
- Required fixes
- Whether Hermes may mark the Kanban card done
- Whether Chris approval is needed
"""
        
        try:
            # Write prompt to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(prompt)
                f.write("\n\n---\n\n")
                f.write(Path(brief_path).read_text())
                prompt_path = f.name
            
            # Run Codex planner
            result = subprocess.run(
                [self._codex_wrapper, prompt_path],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            Path(prompt_path).unlink(missing_ok=True)
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Codex review failed: {result.stderr[:200]}"
                
        except subprocess.TimeoutExpired:
            return "Codex review timed out after 120s"
        except Exception as e:
            return f"Codex review error: {e}"
    
    def _deepseek_review(self, brief: str) -> str:
        """Send brief to DeepSeek V4 Pro for review."""
        if not self._deepseek_api_key:
            return "DeepSeek review skipped: no API key"
        
        prompt = """You are DeepSeek V4 Pro acting as an independent implementation reviewer.

You cannot inspect local files unless they are included in the brief, so base your review only on the supplied evidence.

Review Hermes's implementation for:
- strategic mismatch
- over-engineering
- missing safety checks
- incomplete execution
- likely hidden failure modes
- whether this should go back to Chris before more work is done

Return:
- Findings ordered by severity
- Required fixes
- Questions for Chris, if any
- Approval recommendation: approve / fix first / ask Chris
"""
        
        try:
            headers = {
                'Authorization': f'Bearer {self._deepseek_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'deepseek-v4-pro',
                'messages': [
                    {'role': 'system', 'content': prompt},
                    {'role': 'user', 'content': brief}
                ],
                'max_tokens': 4000
            }
            
            response = requests.post(
                'https://api.deepseek.com/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"DeepSeek review failed: {response.status_code}"
                
        except requests.Timeout:
            return "DeepSeek review timed out after 60s"
        except Exception as e:
            return f"DeepSeek review error: {e}"
    
    def _consolidate_reviews(
        self,
        codex_findings: str,
        deepseek_findings: str,
        files_changed: List[str]
    ) -> Dict[str, Any]:
        """Consolidate both reviews into a decision."""
        
        # Extract severity counts
        codex_critical = len(re.findall(r'critical|severe|bug|broken|unsafe', codex_findings.lower()))
        deepseek_critical = len(re.findall(r'critical|severe|bug|broken|unsafe', deepseek_findings.lower()))
        
        total_critical = codex_critical + deepseek_critical
        
        # Determine decision
        if total_critical > 3:
            decision = "fix_first"
        elif total_critical > 0:
            decision = "ask_chris"
        else:
            decision = "approve"
        
        # Extract fix items
        fixes = []
        for text in [codex_findings, deepseek_findings]:
            # Look for bullet points that mention fixes
            for line in text.splitlines():
                if any(marker in line.lower() for marker in ['fix', 'should', 'need to', 'must', 'required']):
                    fixes.append(line.strip())
        
        # Build recommendation
        if decision == "approve":
            recommendation = "Both reviews found no critical issues. Ready to mark done."
        elif decision == "fix_first":
            recommendation = f"{total_critical} critical issues found. Create fix cards before marking done."
        else:
            recommendation = "Minor concerns found. Ask Chris before proceeding."
        
        return {
            "decision": decision,
            "codex_findings": codex_findings,
            "deepseek_findings": deepseek_findings,
            "consolidated_fixes": fixes[:10],  # Top 10
            "recommendation": recommendation
        }
    
    def create_fix_cards(self, review_result: Dict[str, Any], original_card_id: str) -> List[Dict[str, str]]:
        """Create Kanban fix cards from review findings.
        
        Returns list of card dicts ready for Kanban creation.
        """
        cards = []
        
        for i, fix in enumerate(review_result.get("consolidated_fixes", [])):
            cards.append({
                "title": f"Fix: {fix[:60]}",
                "owner": "Hermes",
                "goal": f"Address review finding from {original_card_id}",
                "steps": [
                    f"Review: {fix}",
                    "Implement fix",
                    "Re-run review gate"
                ],
                "acceptance_criteria": [
                    "Fix addresses the review finding",
                    "No regressions introduced"
                ],
                "do_not_touch": [],
                "status": "Backlog",
                "parent_card": original_card_id,
                "source": "review_gate"
            })
        
        return cards
