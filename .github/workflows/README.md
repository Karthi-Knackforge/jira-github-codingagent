# Jira to GitHub Copilot Agent Integration

This **centralized agent repository** orchestrates GitHub issue creation across multiple target repositories. When a Jira label is added, the workflow connects to the target repository, creates an issue, and assigns it to GitHub Copilot coding agent.

## 🏗️ Architecture

```
Jira Automation (webhook)
    ↓
jira-github-codingagent (this repo - GitHub Actions)
    ↓ (GitHub REST API)
Target Repository (cms-project, api-project, etc.)
    ↓
GitHub Issue + @github assignment
    ↓
Copilot Coding Agent (autonomous implementation)
```

**Benefits:**
- ✅ Centralized orchestration logic in one repo
- ✅ Support multiple target repositories without duplicating workflows
- ✅ Uses official GitHub REST API
- ✅ Easy to extend with additional integrations

## 🔧 Setup Instructions

### 1. Configure GitHub Repository Secrets

Go to this **jira-github-codingagent** repository **Settings → Secrets and variables → Actions** and add:

- `GB_TOKEN` - GitHub Personal Access Token with `repo` and `workflow` scopes for target repositories

### 2. Configure Jira Automation (Label-Based Routing)

Create automation rules in Jira for each target repository:

#### Option A: Single Repository (cms-project)

**Trigger:** Issue labeled with `Auto-Copilot-CMS`

**Action:** Send web request

```
URL: https://api.github.com/repos/Karthi-Knackforge/jira-github-codingagent/dispatches
Method: POST
Headers:
  Authorization: Bearer YOUR_GITHUB_TOKEN
  Accept: application/vnd.github+json
  X-GitHub-Api-Version: 2022-11-28

Body (Custom data - JSON):
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

#### Option B: Multiple Repositories

Create separate rules for each target:

**For API Project:** Label = `Auto-Copilot-API`, `target_repo` = `api-project`
**For Frontend:** Label = `Auto-Copilot-Frontend`, `target_repo` = `frontend-app`
**For Mobile:** Label = `Auto-Copilot-Mobile`, `target_repo` = `mobile-app`

Each rule sends to the **same agent repo** (`jira-github-codingagent/dispatches`) but with different `target_repo` in payload.

### 3. Enable GitHub Actions

Ensure Actions are enabled in:
- **This repo** (`jira-github-codingagent`): Main orchestration
- **Target repos** (`cms-project`, etc.): Where issues are created

## 🎯 How It Works

1. **Jira Trigger**: Add label like `Auto-Copilot-CMS` to a Jira issue
2. **Webhook to Agent Repo**: Jira sends `repository_dispatch` to this centralized agent repo
3. **GitHub API Connection**: GitHub Actions connects to target repository via GitHub REST API
4. **Deduplication**: Searches target repo for existing issue with this Jira key
5. **Issue Creation**: If new, creates GitHub issue in target repo with:
   - Structured format optimized for Copilot understanding
   - Requirements and Acceptance Criteria sections
   - Link back to original Jira ticket
   - Automatic labels: `jira-sync`, `copilot-agent`, `priority-{level}`
6. **Copilot Assignment**: Issue assigned to `@github` (GitHub Copilot coding agent)
7. **Autonomous Work in Target Repo**: Copilot coding agent:
   - Analyzes the requirements
   - Creates a development branch (`copilot/*`)
   - Implements the solution
   - Runs tests and validation
   - Opens a pull request for review

## 📊 Monitoring

- **Workflow runs**: Check `.github/workflows` action runs for execution logs
- **Job summaries**: Each run creates a summary with status and links
- **Issue comments**: Track Copilot's progress in the created issue
- **Pull requests**: Review Copilot's implementation in the PR it creates

## 🚨 Error Handling

If the workflow fails:
- Check the Actions tab for detailed error logs
- An automation-failure issue will be created automatically
- Review the job summary for quick diagnostics

## 🔒 Security Notes

- Copilot can only push to `copilot/*` branches
- All PRs require human review before merge
- CI/CD workflows need approval before running
- Commits are co-authored for traceability

## 📝 Issue Format Example

```markdown
## 📋 Requirements

Implement user authentication with OAuth2 support...

## ✅ Acceptance Criteria

- [ ] Implementation matches the requirements described above
- [ ] Code follows project conventions and best practices
- [ ] Tests are added/updated to cover changes
- [ ] Documentation is updated if needed

## 🔗 Jira Reference

**Jira Issue:** [CGCI-123](https://knackforge-team-xpf6pae3.atlassian.net/browse/CGCI-123)
**Priority:** High
**Type:** Story

---

*This issue was automatically created from Jira and assigned to GitHub Copilot coding agent for implementation.*
```

## 🎓 Learn More

- [GitHub Copilot Coding Agent Documentation](https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent)
- [Repository Dispatch Events](https://docs.github.com/en/rest/repos/repos#create-a-repository-dispatch-event)
- [Jira Automation](https://support.atlassian.com/cloud-automation/docs/jira-automation-triggers/)

## 📋 Jira Automation Configuration Details

### Smart Values Available

You can use these Jira smart values in your webhook:

- `{{issue.key}}` - Issue key (e.g., CGCI-123)
- `{{issue.summary}}` - Issue title
- `{{issue.description}}` - Issue description
- `{{issue.url}}` - Direct link to Jira issue
- `{{issue.priority.name}}` - Priority level
- `{{issue.type.name}}` - Issue type (Story, Bug, Task, etc.)
- `{{issue.assignee.displayName}}` - Assignee name
- `{{issue.reporter.displayName}}` - Reporter name

### Webhook Configuration Steps

1. Go to **Project settings → Automation** in your Jira project
2. Click **Create rule**
3. Set trigger: **Issue → Labeled**
4. Add condition: **Label equals "Auto-Copilot"**
5. Add action: **Send web request**
6. Configure as shown in Setup Instructions above
7. Name your rule: "Sync to GitHub Copilot"
8. Turn it ON

## 🧪 Testing

To test the integration:

1. Create or open a Jira issue in your CGCI project
2. Add the label `Auto-Copilot` to the issue
3. Wait 1-2 minutes for processing
4. Check GitHub Actions tab in cms-project repository
5. Verify new issue was created and assigned to @github
6. Watch for Copilot to start working on a PR

## 🐛 Troubleshooting

### Workflow not triggering?
- Verify the webhook URL is correct
- Check GitHub token has proper permissions
- Ensure repository_dispatch is enabled

### Issue not created?
- Check workflow logs in Actions tab
- Verify all Jira smart values are populated
- Check Python script output for errors

### Copilot not assigned?
- Ensure you have Copilot Pro/Business/Enterprise
- Verify @github user assignment in issue
- Check if Copilot is enabled for the repository
