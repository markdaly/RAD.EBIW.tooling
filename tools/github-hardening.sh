#!/bin/bash
# github-hardening.sh: apply the branch rule and security settings this repo wants. Needs `gh`
# logged in as an admin of the repo. Branch protection, secret scanning and private
# vulnerability reporting are free only on PUBLIC repos (or GitHub Pro), so run this after
# flipping visibility; Dependabot alerts + security updates work either way.
# Usage: tools/github-hardening.sh [owner/repo]   (default: the origin remote)
set -u
R="${1:-$(git remote get-url origin | sed -E 's#.*github\.com[:/]##; s#\.git$##')}"
echo "repo: $R  visibility: $(gh repo view "$R" --json visibility -q .visibility)"
ok(){ [ -z "$1" ] && echo "  ok" || echo "  $1" | head -c 200; echo; }
echo "dependabot alerts";            ok "$(gh api -X PUT "repos/$R/vulnerability-alerts" 2>&1)"
echo "dependabot security updates";  ok "$(gh api -X PUT "repos/$R/automated-security-fixes" 2>&1)"
echo "private vulnerability reporting"; ok "$(gh api -X PUT "repos/$R/private-vulnerability-reporting" 2>&1)"
echo "secret scanning + push protection"
gh api -X PATCH "repos/$R" --input - <<'JSON' 2>&1 | python3 -c 'import sys,json; d=json.loads(sys.stdin.read().split("\n")[0]); print("  ", d.get("message") or d.get("security_and_analysis"))'
{"security_and_analysis": {"secret_scanning": {"status": "enabled"}, "secret_scanning_push_protection": {"status": "enabled"}}}
JSON
echo "CodeQL default setup (python); needs Actions enabled on the repo"
gh api -X PATCH "repos/$R/code-scanning/default-setup" --input - <<'JSON' 2>&1 | python3 -c 'import sys,json; d=json.loads(sys.stdin.read().split("\n")[0] or "{}"); print("  ", d.get("message") or d.get("state") or d)'
{"state": "configured", "query_suite": "default", "languages": ["python"]}
JSON
echo "branch protection on main: PRs for everyone but admins, no force-push, no delete, linear history"
gh api -X PUT "repos/$R/branches/main/protection" --input - <<'JSON' 2>&1 | python3 -c 'import sys,json; d=json.loads(sys.stdin.read().split("\n")[0]); print("  ", d.get("message") or {k: d[k].get("enabled") for k in ("enforce_admins","required_linear_history","allow_force_pushes","allow_deletions") if k in d})'
{"required_status_checks": null, "enforce_admins": false, "required_pull_request_reviews": {"required_approving_review_count": 0, "dismiss_stale_reviews": true}, "restrictions": null, "required_linear_history": true, "allow_force_pushes": false, "allow_deletions": false, "required_conversation_resolution": true}
JSON
