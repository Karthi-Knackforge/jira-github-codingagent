# Deployment Checklist

Use this checklist to deploy the enhanced Jira to GitHub Copilot workflow.

---

## 📋 Pre-Deployment

### ✅ Prerequisites

- [ ] GitHub organization/account with Copilot enabled
- [ ] Jira Cloud instance with automation capability
- [ ] Admin access to both GitHub and Jira
- [ ] Target repositories identified
- [ ] Python 3.11+ installed (for local testing)

### ✅ Repository Setup

- [ ] `jira-github-codingagent` repository exists
- [ ] Repository has Actions enabled
- [ ] You have admin access to the repository
- [ ] Default branch is `main` or `master`

---

## 🔐 Security Configuration

### ✅ GitHub Personal Access Token

- [ ] Create GitHub PAT at: https://github.com/settings/tokens
- [ ] Select scopes:
- [ ] `repo` (Full control of private repositories)
- [ ] `workflow` (Update GitHub Action workflows)
- [ ] Copy token (you won't see it again!)
- [ ] Store token securely (password manager)

### ✅ Add Token to Repository

- [ ] Go to `jira-github-codingagent` repository
- [ ] Navigate to: Settings → Secrets and variables → Actions
- [ ] Click "New repository secret"
- [ ] Name: `GB_TOKEN`
- [ ] Value: [Paste your GitHub PAT]
- [ ] Click "Add secret"
- [ ] Verify secret appears in list

---

## 📁 Repository Content

### ✅ Verify Files Exist

- [ ] `.github/workflows/jira-to-copilot-with-context.yml`
- [ ] `scripts/sync_context_to_branch.py`
- [ ] `scripts/create_issue_with_context.py`
- [ ] `scripts/assign_to_copilot.py`
- [ ] `requirements.txt`
- [ ] `docs/architecture/overview.md`
- [ ] `docs/api-standards/naming-conventions.md`
- [ ] `docs/api-standards/crud-api-spec.md`
- [ ] `docs/laravel/core-patterns.md`
- [ ] `docs/laravel/database-access-layer.md`
- [ ] `docs/laravel/error-handling.md`
- [ ] `docs/laravel/unit-testing-standards.md`
- [ ] `docs/react/component-structure.md`
- [ ] `docs/react/state-management.md`
- [ ] `docs/react/api-consumption.md`
- [ ] `docs/react/testing-library-patterns.md`

### ✅ Verify Scripts are Executable

```bash
ls -la scripts/*.py
# Should show -rwxr-xr-x permissions
```

---

## 🔧 Jira Configuration

### ✅ Jira Automation Rule Setup

For each target repository, complete these steps:

#### Rule 1: [Project Name] - e.g., CMS

- [ ] Go to Jira → Project Settings → Automation
- [ ] Click "Create rule"
- [ ] Name: `Auto-Assign to GitHub Copilot - CMS`

**Trigger:**
- [ ] Select: "Issue" → "Field value changed"
- [ ] Field: Labels
- [ ] Condition: Label equals `Auto-Copilot-CMS`

**Action:**
- [ ] Add action: "Send web request"
- [ ] URL: `https://api.github.com/repos/Karthi-Knackforge/jira-github-codingagent/dispatches`
- [ ] HTTP method: `POST`
- [ ] Headers:
  ```
  Authorization: Bearer YOUR_GITHUB_TOKEN
  Accept: application/vnd.github+json
  X-GitHub-Api-Version: 2022-11-28
  Content-Type: application/json
  ```
- [ ] HTTP body - Custom data:
  ```json
  {
    "event_type": "jira-to-copilot-with-context",
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

- [ ] Click "Save"
- [ ] Turn rule ON

#### Repeat for Other Projects

- [ ] Rule for API project (label: `Auto-Copilot-API`)
- [ ] Rule for Frontend project (label: `Auto-Copilot-Frontend`)
- [ ] Rule for other projects as needed

---

## 🧪 Testing

### ✅ Manual Webhook Test

Test webhook manually before Jira rule:

```bash
curl -X POST \
  https://api.github.com/repos/Karthi-Knackforge/jira-github-codingagent/dispatches \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  -d '{
    "event_type": "jira-to-copilot-with-context",
    "client_payload": {
      "target_owner": "Karthi-Knackforge",
      "target_repo": "cms-project",
      "jira_key": "TEST-1",
      "summary": "Test Issue",
      "description": "This is a test",
      "url": "https://your-jira.atlassian.net/browse/TEST-1",
      "priority": "Medium",
      "issue_type": "Task"
    }
  }'
```

Expected: HTTP 204 No Content

- [ ] Manual webhook test successful

### ✅ Verify GitHub Actions

- [ ] Go to: https://github.com/Karthi-Knackforge/jira-github-codingagent/actions
- [ ] See workflow run for "repository_dispatch"
- [ ] Workflow status: ✅ Success
- [ ] Review logs for each step

### ✅ Verify Target Repository

- [ ] Go to target repository (e.g., cms-project)
- [ ] Branches: See new branch `jira/test-1`
- [ ] Check branch contents: See `docs/` directory
- [ ] Check branch `docs/` has all markdown files
- [ ] Issues: See new issue
- [ ] Issue title: `[TEST-1] Test Issue`
- [ ] Issue labels: `copilot-ready`, `has-context`, `priority-medium`
- [ ] Issue assigned to: `@copilot` or `copilot-swe-agent`
- [ ] Issue has comment with instructions

### ✅ Full Jira Test

- [ ] Create or open test Jira issue
- [ ] Add label: `Auto-Copilot-CMS`
- [ ] Wait 1-2 minutes
- [ ] Check Jira automation audit log
- [ ] Verify webhook sent successfully
- [ ] Check GitHub Actions (should see new run)
- [ ] Verify all items from "Verify Target Repository" above
- [ ] Monitor Copilot activity on the issue

---

## 📊 Post-Deployment

### ✅ Documentation

- [ ] Share README.md with team
- [ ] Document label naming convention
- [ ] Create team guide for using the system
- [ ] Add to onboarding documentation

### ✅ Team Training

- [ ] Demo the workflow to team
- [ ] Explain label usage
- [ ] Show where to find docs
- [ ] Explain review process
- [ ] Share troubleshooting guide

### ✅ Monitoring

Set up monitoring for:

- [ ] GitHub Actions success rate
- [ ] Workflow execution time
- [ ] Branch creation success
- [ ] Issue creation success
- [ ] Copilot assignment rate
- [ ] PR creation rate from Copilot

### ✅ Metrics Collection

Track these metrics weekly:

- [ ] Number of issues created
- [ ] Success rate (% successful runs)
- [ ] Average time to issue creation
- [ ] Number of PRs created by Copilot
- [ ] PR acceptance rate
- [ ] Developer satisfaction score

---

## 🔧 Troubleshooting Setup

### ✅ Common Issues - Solutions Ready

**Workflow not triggering:**
- [ ] Verified event_type matches workflow file
- [ ] Checked GitHub Actions are enabled
- [ ] Reviewed Jira automation rule logs

**401 Unauthorized:**
- [ ] Token is valid and not expired
- [ ] Token has correct scopes (repo, workflow)
- [ ] Token is correctly formatted in secret

**Branch creation fails:**
- [ ] GB_TOKEN has access to target repository
- [ ] Target repository exists
- [ ] Default branch name is correct

**Docs not syncing:**
- [ ] docs/ directory exists in agent repo
- [ ] Markdown files are valid
- [ ] File paths are correct

**Copilot not assigned:**
- [ ] Copilot is enabled for organization
- [ ] copilot-swe-agent has access
- [ ] Assignment API is available

---

## ✅ Rollback Plan

If issues arise, rollback steps:

- [ ] Disable Jira automation rules
- [ ] Remove labels from active issues
- [ ] Revert to basic workflow if needed
- [ ] Document issues encountered
- [ ] Fix and re-test before re-enabling

---

## 📞 Support Contacts

Document your support contacts:

- [ ] GitHub admin: _______________
- [ ] Jira admin: _______________
- [ ] DevOps lead: _______________
- [ ] Technical contact: _______________

---

## ✅ Sign-Off

### Deployment Completed By

- [ ] Name: _______________
- [ ] Date: _______________
- [ ] Time: _______________

### Verified By

- [ ] Name: _______________
- [ ] Date: _______________
- [ ] Time: _______________

### Issues Encountered

Document any issues:

```
Issue 1: _______________________________________________
Resolution: ____________________________________________

Issue 2: _______________________________________________
Resolution: ____________________________________________
```

### Production Ready

- [ ] All tests passed
- [ ] Team trained
- [ ] Monitoring in place
- [ ] Documentation complete
- [ ] Rollback plan tested
- [ ] Sign-off obtained

---

## 🎉 Next Steps After Deployment

1. **Week 1:**
   - [ ] Monitor closely for issues
   - [ ] Collect initial feedback
   - [ ] Address any bugs quickly
   - [ ] Document lessons learned

2. **Week 2-4:**
   - [ ] Review Copilot implementation quality
   - [ ] Gather team feedback
   - [ ] Optimize documentation based on results
   - [ ] Expand to more projects if successful

3. **Month 2:**
   - [ ] Analyze metrics and ROI
   - [ ] Present results to leadership
   - [ ] Plan additional automation
   - [ ] Scale to entire organization

---

## 📈 Success Criteria

This deployment is successful when:

- [ ] 90%+ of workflow runs succeed
- [ ] Issues created within 2 minutes of label
- [ ] All docs sync correctly to branches
- [ ] Copilot successfully assigned to all issues
- [ ] Team adopts label usage consistently
- [ ] PRs created by Copilot follow standards
- [ ] Developer satisfaction improves

---

**🚀 Ready for Production Deployment!**

Print this checklist and complete it step-by-step during deployment.
