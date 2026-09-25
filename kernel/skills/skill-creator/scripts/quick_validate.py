#!/usr/bin/env python3
"""
Quick validation script for skills - minimal version
"""

import sys
import os
import re
import yaml
from pathlib import Path

# Agent Skills spec fields (https://agentskills.io/specification): the only keys that
# claude.ai upload, the Skills API and .skill packaging accept - any other key is a hard error there.
AGENT_SKILLS_SPEC_PROPERTIES = {
    'name', 'description', 'license', 'compatibility', 'metadata', 'allowed-tools',
}

# Every field in the Claude Code frontmatter reference
# (https://code.claude.com/docs/en/skills#frontmatter-reference). Claude Code silently
# ignores an unknown key, so a misspelled one never warns at runtime - catching it is this check's job.
CLAUDE_CODE_PROPERTIES = AGENT_SKILLS_SPEC_PROPERTIES | {
    'when_to_use', 'argument-hint', 'arguments', 'disable-model-invocation', 'user-invocable',
    'disallowed-tools', 'model', 'effort', 'context', 'agent', 'background', 'hooks', 'paths', 'shell',
}

def validate_skill(skill_path, allowed_properties=AGENT_SKILLS_SPEC_PROPERTIES):
    """Basic validation of a skill.

    The default allow-list is the Agent Skills spec set, because package_skill.py calls this
    before building a .skill file for claude.ai. Pass CLAUDE_CODE_PROPERTIES to validate a
    skill that only ever runs in Claude Code.
    """
    skill_path = Path(skill_path)

    # Check SKILL.md exists
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return False, "SKILL.md not found"

    # Read and validate frontmatter
    content = skill_md.read_text()
    if not content.startswith('---'):
        return False, "No YAML frontmatter found"

    # Extract frontmatter
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format"

    frontmatter_text = match.group(1)

    # Parse YAML frontmatter
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        if not isinstance(frontmatter, dict):
            return False, "Frontmatter must be a YAML dictionary"
    except yaml.YAMLError as e:
        return False, f"Invalid YAML in frontmatter: {e}"

    # Check for unexpected properties (excluding nested keys under metadata)
    unexpected_keys = set(frontmatter.keys()) - set(allowed_properties)
    if unexpected_keys:
        return False, (
            f"Unexpected key(s) in SKILL.md frontmatter: {', '.join(sorted(unexpected_keys))}. "
            f"Allowed properties are: {', '.join(sorted(allowed_properties))}"
        )

    # Check required fields
    if 'name' not in frontmatter:
        return False, "Missing 'name' in frontmatter"
    if 'description' not in frontmatter:
        return False, "Missing 'description' in frontmatter"

    # Extract name for validation
    name = frontmatter.get('name', '')
    if not isinstance(name, str):
        return False, f"Name must be a string, got {type(name).__name__}"
    name = name.strip()
    if name:
        # Check naming convention (hyphen-case: lowercase with hyphens)
        if not re.match(r'^[a-z0-9-]+$', name):
            return False, f"Name '{name}' should be hyphen-case (lowercase letters, digits, and hyphens only)"
        if name.startswith('-') or name.endswith('-') or '--' in name:
            return False, f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens"
        # Check name length (max 64 characters per spec)
        if len(name) > 64:
            return False, f"Name is too long ({len(name)} characters). Maximum is 64 characters."

    # Extract and validate description
    description = frontmatter.get('description', '')
    if not isinstance(description, str):
        return False, f"Description must be a string, got {type(description).__name__}"
    description = description.strip()
    if description:
        # Check for angle brackets
        if '<' in description or '>' in description:
            return False, "Description cannot contain angle brackets (< or >)"
        # Check description length (max 1024 characters per spec)
        if len(description) > 1024:
            return False, f"Description is too long ({len(description)} characters). Maximum is 1024 characters."

    return True, "Skill is valid!"

if __name__ == "__main__":
    args = sys.argv[1:]
    spec_only = '--spec' in args
    if spec_only:
        args.remove('--spec')
    if len(args) != 1:
        print("Usage: python quick_validate.py [--spec] <skill_directory>")
        print("  default: allow every Claude Code frontmatter field")
        print("  --spec:  allow only the Agent Skills spec fields (claude.ai upload, .skill packaging)")
        sys.exit(1)

    allowed = AGENT_SKILLS_SPEC_PROPERTIES if spec_only else CLAUDE_CODE_PROPERTIES
    valid, message = validate_skill(args[0], allowed)
    print(message)
    sys.exit(0 if valid else 1)