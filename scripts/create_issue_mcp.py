#!/usr/bin/env python3
"""
Create GitHub issue from Jira ticket in target repository and assign to Copilot.
Prevents duplicate issues by checking for existing Jira key references.

This centralized agent repo orchestrates issue creation across multiple target repos.
Routes to different repos based on Jira payload (target_owner, target_repo).
"""

import os
import sys
from typing import Optional, Dict, Any
import requests

# Configuration from environment variables
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
TARGET_REPO_OWNER = os.environ.get("TARGET_REPO_OWNER", "Karthi-Knackforge")
TARGET_REPO_NAME = os.environ.get("TARGET_REPO_NAME", "cms-project")
JIRA_ISSUE_KEY = os.environ.get("JIRA_ISSUE_KEY")
JIRA_SUMMARY = os.environ.get("JIRA_SUMMARY", "")
JIRA_DESCRIPTION = os.environ.get("JIRA_DESCRIPTION", "")
JIRA_ISSUE_URL = os.environ.get("JIRA_ISSUE_URL", "")
JIRA_PRIORITY = os.environ.get("JIRA_PRIORITY", "Medium")
JIRA_ISSUE_TYPE = os.environ.get("JIRA_ISSUE_TYPE", "Task")

# GitHub API configuration
GITHUB_API_BASE = "https://api.github.com"
GITHUB_COPILOT_USERNAME = "github"


def check_required_env_vars():
    """Validate that all required environment variables are set."""
    required_vars = {
        "GITHUB_TOKEN": GITHUB_TOKEN,
        "TARGET_REPO_OWNER": TARGET_REPO_OWNER,
        "TARGET_REPO_NAME": TARGET_REPO_NAME,
        "JIRA_ISSUE_KEY": JIRA_ISSUE_KEY,
    }
    
    missing = [var for var, value in required_vars.items() if not value]
    
    if missing:
        print(f"❌ Error: Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)


def get_github_headers() -> Dict[str, str]:
    """Return headers for GitHub API requests."""
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def create_copilot_optimized_issue_body() -> str:
    """
    Create a structured issue body optimized for GitHub Copilot coding agent.
    
    Uses clear sections that help Copilot understand:
    - What needs to be done (Requirements)
    - How to verify completion (Acceptance Criteria)
    - Where to find more info (Jira Link)
    """
    # Clean and format the description
    description = JIRA_DESCRIPTION.strip() if JIRA_DESCRIPTION else "No description provided."
    
    # Build structured issue body
    issue_body = f"""## 📋 Requirements

{description}

## ✅ Acceptance Criteria

- [ ] Implementation matches the requirements described above
- [ ] Code follows project conventions and best practices
- [ ] Tests are added/updated to cover changes
- [ ] Documentation is updated if needed

## 🔗 Jira Reference

**Jira Issue:** [{JIRA_ISSUE_KEY}]({JIRA_ISSUE_URL})
**Priority:** {JIRA_PRIORITY}
**Type:** {JIRA_ISSUE_TYPE}

---

*This issue was automatically created from Jira and assigned to GitHub Copilot coding agent for implementation.*
"""
    
    return issue_body


def search_existing_issue(jira_key: str) -> Optional[Dict[str, Any]]:
    """
    Search for existing OPEN GitHub issues containing the Jira key.
    Returns the first matching OPEN issue or None if not found.
    Closed issues are ignored - we can create new issues for the same Jira key if previous ones are closed.
    """
    print(f"🔍 Searching for existing OPEN issues with key: {jira_key} in {TARGET_REPO_OWNER}/{TARGET_REPO_NAME}")
    
    search_url = f"{GITHUB_API_BASE}/search/issues"
    # Only search for OPEN issues - closed ones are ignored
    search_query = f"repo:{TARGET_REPO_OWNER}/{TARGET_REPO_NAME} {jira_key} in:title,body type:issue state:open"
    
    params = {"q": search_query, "per_page": 1}
    
    try:
        response = requests.get(search_url, headers=get_github_headers(), params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("total_count", 0) > 0:
            issue = data["items"][0]
            print(f"   Found open issue: #{issue.get('number')} - {issue.get('state')}")
            return issue
        
        print("   No open issues found")
        return None
    
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Warning: Failed to search for existing issues: {e}")
        return None


def create_github_issue() -> Dict[str, Any]:
    """
    Create a new GitHub issue with Copilot-optimized formatting.
    Tries to assign to @github, falls back to creating without assignment if not available.
    
    Returns:
        Dict containing the created issue data
    """
    create_url = f"{GITHUB_API_BASE}/repos/{TARGET_REPO_OWNER}/{TARGET_REPO_NAME}/issues"
    
    # Create issue title with Jira key
    title = f"[{JIRA_ISSUE_KEY}] {JIRA_SUMMARY}"
    
    print(f"📝 Creating issue in {TARGET_REPO_OWNER}/{TARGET_REPO_NAME}")
    print(f"   Title: {title}")
    
    # Build issue payload with Copilot assignment
    issue_data = {
        "title": title,
        "body": create_copilot_optimized_issue_body(),
        "labels": ["jira-sync", "copilot-agent", f"priority-{JIRA_PRIORITY.lower()}"],
        "assignees": [GITHUB_COPILOT_USERNAME],
    }
    
    try:
        response = requests.post(
            create_url,
            headers=get_github_headers(),
            json=issue_data
        )
        response.raise_for_status()
        
        issue = response.json()
        print(f"✅ Issue created with @{GITHUB_COPILOT_USERNAME} assignment")
        return issue
    
    except requests.exceptions.HTTPError as e:
        # Check if error is due to invalid assignee (Copilot not available)
        if e.response.status_code == 422 and "assignees" in e.response.text:
            print(f"⚠️  @{GITHUB_COPILOT_USERNAME} not available in this repo, creating issue without assignment...")
            
            # Retry without assignees
            issue_data_no_assignee = {
                "title": title,
                "body": create_copilot_optimized_issue_body(),
                "labels": ["jira-sync", "copilot-agent", f"priority-{JIRA_PRIORITY.lower()}"],
            }
            
            try:
                response = requests.post(
                    create_url,
                    headers=get_github_headers(),
                    json=issue_data_no_assignee
                )
                response.raise_for_status()
                
                issue = response.json()
                print(f"✅ Issue created (assign @{GITHUB_COPILOT_USERNAME} manually if needed)")
                return issue
            
            except requests.exceptions.RequestException as retry_error:
                print(f"❌ Error creating issue without assignee: {retry_error}")
                if hasattr(retry_error, 'response') and retry_error.response is not None:
                    print(f"Response: {retry_error.response.text}")
                sys.exit(1)
        else:
            print(f"❌ Error creating GitHub issue: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            sys.exit(1)
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating GitHub issue: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)


def assign_copilot_via_api(issue_number: int) -> bool:
    """
    Assign GitHub Copilot coding agent to the issue using GitHub's official API.
    Uses the repository_dispatch endpoint to trigger Copilot assignment.
    
    Returns:
        True if assignment was successful, False otherwise
    """
    # GitHub's official method: Use GraphQL mutation to assign Copilot
    graphql_url = "https://api.github.com/graphql"
    
    # First, get the issue's node ID
    issue_url = f"{GITHUB_API_BASE}/repos/{TARGET_REPO_OWNER}/{TARGET_REPO_NAME}/issues/{issue_number}"
    
    try:
        # Get issue details including node_id
        response = requests.get(issue_url, headers=get_github_headers())
        response.raise_for_status()
        issue_data = response.json()
        issue_node_id = issue_data.get("node_id")
        
        if not issue_node_id:
            print("⚠️  Could not get issue node ID")
            return False
        
        # Use GraphQL to assign Copilot (this is the official method used by GitHub UI)
        mutation = """
        mutation AssignCopilot($issueId: ID!) {
          assignCopilot(input: {issueId: $issueId}) {
            issue {
              id
              number
              title
            }
          }
        }
        """
        
        graphql_payload = {
            "query": mutation,
            "variables": {"issueId": issue_node_id}
        }
        
        response = requests.post(
            graphql_url,
            headers=get_github_headers(),
            json=graphql_payload
        )
        
        if response.status_code == 200:
            result = response.json()
            if "errors" not in result:
                print(f"✅ Successfully assigned @{GITHUB_COPILOT_USERNAME} via GraphQL API")
                return True
            else:
                print(f"⚠️  GraphQL errors: {result.get('errors')}")
                return False
        else:
            print(f"⚠️  GraphQL request failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"⚠️  Could not assign Copilot via API: {e}")
        return False


def main():
    """Main execution flow."""
    print("🚀 Starting Jira to GitHub Issue workflow...")
    print(f"📍 Target Repository: {TARGET_REPO_OWNER}/{TARGET_REPO_NAME}")
    print(f"📝 Jira Issue: {JIRA_ISSUE_KEY}")
    
    # Validate environment variables
    check_required_env_vars()
    
    # Check for existing OPEN issue with this Jira key
    existing_issue = search_existing_issue(JIRA_ISSUE_KEY)
    
    if existing_issue:
        issue_number = existing_issue.get("number")
        issue_url = existing_issue.get("html_url")
        issue_state = existing_issue.get("state")
        print(f"ℹ️  Open issue already exists: #{issue_number} (state: {issue_state})")
        print(f"🔗 URL: {issue_url}")
        print("✅ Skipping creation - no duplicate will be created")
        return
    
    # Create new issue
    print("✨ No existing issue found, creating new issue...")
    issue = create_github_issue()
    
    issue_number = issue.get("number")
    issue_url = issue.get("html_url")
    assignees = issue.get("assignees", [])
    
    print(f"✅ Successfully created issue #{issue_number}")
    print(f"🔗 URL: {issue_url}")
    
    # Check if Copilot was successfully assigned during creation
    if any(assignee.get("login") == GITHUB_COPILOT_USERNAME for assignee in assignees):
        print(f"🤖 Assigned to: @{GITHUB_COPILOT_USERNAME} (GitHub Copilot coding agent)")
    else:
        print(f"⚠️  @{GITHUB_COPILOT_USERNAME} assignment not available during creation")
        print("💬 Attempting to assign Copilot via GraphQL API...")
        assign_copilot_via_api(issue_number)
    
    labels = [label.get("name") if isinstance(label, dict) else label for label in issue.get("labels", [])]
    print(f"🏷️  Labels: {', '.join(labels)}")
    
    # Output for GitHub Actions summary
    print(f"\n::notice title=Issue Created::Created issue #{issue_number} in {TARGET_REPO_OWNER}/{TARGET_REPO_NAME}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
