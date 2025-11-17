# Quick Setup Guide

## ✅ What's Been Implemented

Your **centralized agent repository** architecture is now complete:

```
Jira (label trigger) → jira-github-codingagent (MCP orchestrator) → Target Repos (issue creation) → Copilot
```

## 🚀 Next Steps

### 1. Configure GitHub Secret

In this repo (`jira-github-codingagent`):
- Go to **Settings → Secrets and variables → Actions**
- Add secret: `GB_TOKEN` = Your GitHub Personal Access Token
- Required scopes: `repo`, `workflow`

### 2. Create Jira Automation Rules

For each target repository, create a Jira automation rule:

#### Example: CMS Project

**Trigger:** Issue labeled with `Auto-Copilot-CMS`

**Action:** Send web request
```
URL: https://api.github.com/repos/Karthi-Knackforge/jira-github-codingagent/dispatches
Method: POST
Headers:
  Authorization: Bearer YOUR_GITHUB_TOKEN
  Accept: application/vnd.github+json
  X-GitHub-Api-Version: 2022-11-28

Body:
{
  "event_type": "jira-to-github-issue",
  "client_payload": {
    "target_owner": "Karthi-Knackforge",
    "target_repo": "cms-project",
    "jira_key": "{{issue.key}}",
    "summary": "{{issue.summary}}",
    "description": "{{issue.description}}",
    "url": "{{issue.url}}",
    "priority": "{{issue.priority.name}}",
    "issue_type": "{{issue.type.name}}"
  }
}
```

#### Add More Repos

Create additional rules with different labels:
- `Auto-Copilot-API` → `"target_repo": "api-project"`
- `Auto-Copilot-Frontend` → `"target_repo": "frontend-app"`
- `Auto-Copilot-Mobile` → `"target_repo": "mobile-app"`

## 🧪 Test It

1. Create/open a Jira issue in your CGCI project
2. Add label `Auto-Copilot-CMS`
3. Wait 1-2 minutes
4. Check:
   - GitHub Actions in `jira-github-codingagent` repo (workflow logs)
   - New issue in `cms-project` repo
   - Issue assigned to `@github`
5. Watch Copilot create a PR!

## 🏗️ Architecture Benefits

✅ **Centralized Logic**: All orchestration in one repo
✅ **Multi-Repo Support**: Route to any target repo via label
✅ **MCP Abstraction**: Clean API interface via Model Context Protocol
✅ **No Duplication**: Single workflow serves all repos
✅ **Easy Extension**: Add new repos by creating new Jira rules

## 📁 Key Files

- `.github/workflows/jira-to-github-issue.yml` - GitHub Actions workflow
- `scripts/create_issue_mcp.py` - MCP-based issue creation script
- `requirements.txt` - Python dependencies (requests, mcp)
- `.github/workflows/README.md` - Detailed documentation

## 🔧 How MCP Works

The script:
1. Connects to MCP GitHub server via `npx @modelcontextprotocol/server-github`
2. Uses `search_issues` tool to check for duplicates
3. Uses `github_issue_write` tool to create issue
4. Assigns to `@github` (Copilot coding agent)
5. Falls back to direct GitHub API if MCP fails

## 📚 Learn More

- [GitHub Copilot Coding Agent](https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Repository Dispatch Events](https://docs.github.com/en/rest/repos/repos#create-a-repository-dispatch-event)
