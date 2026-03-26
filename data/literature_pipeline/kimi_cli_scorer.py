#!/usr/bin/env python3
"""Kimi CLI wrapper for LLM scoring in literature discovery."""

import json
import subprocess
import os
from pathlib import Path

def ensure_kimi_config():
    """Ensure Kimi CLI is configured with API key."""
    config_dir = Path.home() / ".kimi"
    config_file = config_dir / "config.toml"
    
    # Read API key from our secure storage
    key_file = Path("/root/.openclaw/.env.d/kimi-api-key.txt")
    if key_file.exists():
        with open(key_file) as f:
            api_key = f.read().strip().replace("KIMI_API_KEY=", "")
    else:
        # Fallback to environment
        api_key = os.environ.get("KIMI_API_KEY", "")
    
    if not api_key:
        raise ValueError("No KIMI_API_KEY found")
    
    # Write config
    config_dir.mkdir(exist_ok=True)
    config_content = f'''[llm]
model = "kimi-k2-5"
api_key = "{api_key}"
'''
    with open(config_file, "w") as f:
        f.write(config_content)
    
    return api_key

def score_with_kimi(title: str, abstract: str = "", research_interests: str = "") -> dict:
    """
    Score a paper using Kimi CLI.
    
    Returns:
        dict with 'score' (1-10), 'verdict' (accept/maybe/reject), 'reasoning'
    """
    ensure_kimi_config()
    
    prompt = f"""You are evaluating academic papers for a research project on digital capitalism, platform labor, and critical theory.

Paper Title: {title}
Abstract: {abstract[:500] if abstract else "Not provided"}

Research Focus Areas: {research_interests or "digital capitalism, platform economy, surveillance capitalism, labor organizing, AI and work, critical theory"}

Rate this paper's relevance (1-10) and provide your reasoning in JSON format:
{{
  "score": <1-10>,
  "verdict": "<accept|maybe|reject>", 
  "reasoning": "<brief explanation>"
}}

Rules:
- 8-10 = accept (highly relevant)
- 4-7 = maybe (somewhat relevant)
- 1-3 = reject (not relevant)

Output ONLY valid JSON, no other text."""

    try:
        # Call Kimi CLI
        result = subprocess.run(
            ["kimi", "--print", "--quiet"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return {
                "score": None,
                "verdict": "maybe",
                "reasoning": f"Kimi CLI error: {result.stderr[:100]}"
            }
        
        # Parse JSON from output
        output = result.stdout.strip()
        # Extract JSON if wrapped in markdown
        if "```json" in output:
            output = output.split("```json")[1].split("```")[0]
        elif "```" in output:
            output = output.split("```")[1].split("```")[0]
        
        parsed = json.loads(output)
        return {
            "score": parsed.get("score", 5),
            "verdict": parsed.get("verdict", "maybe"),
            "reasoning": parsed.get("reasoning", "No reasoning provided")
        }
        
    except subprocess.TimeoutExpired:
        return {
            "score": None,
            "verdict": "maybe",
            "reasoning": "Kimi CLI timeout"
        }
    except json.JSONDecodeError as e:
        return {
            "score": None,
            "verdict": "maybe", 
            "reasoning": f"JSON parse error: {str(e)[:100]}"
        }
    except Exception as e:
        return {
            "score": None,
            "verdict": "maybe",
            "reasoning": f"Error: {str(e)[:100]}"
        }

if __name__ == "__main__":
    # Test
    result = score_with_kimi(
        "Platform Capitalism: The Intermediation and Capitalization of Digital Economic Circulation",
        "This paper examines platform capitalism..."
    )
    print(json.dumps(result, indent=2))
