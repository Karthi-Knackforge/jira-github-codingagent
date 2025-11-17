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
GITHUB_COPILOT_USERNAME = "Copilot"


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
    Create a new GitHub issue with Copilot assignment using GraphQL.
    Uses the official createIssue mutation to assign Copilot atomically.
    Falls back to REST API if GraphQL fails.
    
    Returns:
        Dict containing the created issue data
    """
    # Create issue title with Jira key
    title = f"[{JIRA_ISSUE_KEY}] {JIRA_SUMMARY}"
    body = create_copilot_optimized_issue_body()
    label_names = ["jira-sync", "copilot-agent", f"priority-{JIRA_PRIORITY.lower()}"]
    
    print(f"📝 Creating issue in {TARGET_REPO_OWNER}/{TARGET_REPO_NAME}")
    print(f"   Title: {title}")
    
    # Try GraphQL createIssue mutation first (official approach for Copilot assignment)
    try:
        print("🔍 Attempting GraphQL createIssue mutation with Copilot assignment...")
        
        # Get Copilot agent ID
        copilot_id = get_copilot_agent_id()
        if not copilot_id:
            print("⚠️  Copilot agent ID not found, falling back to REST API")
            raise Exception("Copilot agent not found")
        
        # Get repository ID
        repo_query = """
        query($owner: String!, $name: String!) {
            repository(owner: $owner, name: $name) {
                id
            }
        }
        """
        
        repo_response = requests.post(
            "https://api.github.com/graphql",
            json={
                "query": repo_query,
                "variables": {
                    "owner": TARGET_REPO_OWNER,
                    "name": TARGET_REPO_NAME
                }
            },
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        repo_data = repo_response.json()
        if "errors" in repo_data:
            print(f"❌ GraphQL errors getting repo ID: {repo_data['errors']}")
            raise Exception("Failed to get repository ID")
        
        repo_id = repo_data["data"]["repository"]["id"]
        print(f"✅ Found repository ID: {repo_id}")
        
        # Create issue with Copilot assigned
        create_mutation = """
        mutation($input: CreateIssueInput!) {
            createIssue(input: $input) {
                issue {
                    id
                    number
                    url
                    title
                    body
                    assignees(first: 10) {
                        nodes {
                            login
                        }
                    }
                }
            }
        }
        """
        
        create_response = requests.post(
            "https://api.github.com/graphql",
            json={
                "query": create_mutation,
                "variables": {
                    "input": {
                        "repositoryId": repo_id,
                        "title": title,
                        "body": body,
                        "assigneeIds": [copilot_id]
                    }
                }
            },
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        create_data = create_response.json()
        
        if "errors" in create_data:
            print(f"❌ GraphQL createIssue errors: {create_data['errors']}")
            raise Exception("GraphQL createIssue mutation failed")
        
        issue_data = create_data["data"]["createIssue"]["issue"]
        issue_number = issue_data["number"]
        
        print(f"✅ Issue #{issue_number} created via GraphQL with Copilot assigned!")
        
        # Add labels via REST API (simpler than GraphQL)
        label_url = f"{GITHUB_API_BASE}/repos/{TARGET_REPO_OWNER}/{TARGET_REPO_NAME}/issues/{issue_number}/labels"
        label_response = requests.post(
            label_url,
            json={"labels": label_names},
            headers=get_github_headers(),
            timeout=10
        )
        if label_response.status_code == 200:
            print(f"✅ Labels added: {', '.join(label_names)}")
        
        # Convert GraphQL response to REST API format for consistency
        return {
            "number": issue_data["number"],
            "html_url": issue_data["url"],
            "title": issue_data["title"],
            "body": issue_data["body"],
            "assignees": [{"login": a["login"]} for a in issue_data["assignees"]["nodes"]],
            "labels": [{"name": name} for name in label_names]
        }
        
    except Exception as e:
        print(f"⚠️  GraphQL approach failed: {e}")
        print("📝 Falling back to REST API...")
        
        # Fallback: REST API with assignees
        create_url = f"{GITHUB_API_BASE}/repos/{TARGET_REPO_OWNER}/{TARGET_REPO_NAME}/issues"
        
        issue_data = {
            "title": title,
            "body": body,
            "labels": label_names,
            "assignees": [GITHUB_COPILOT_USERNAME],
        }
        
        try:
            response = requests.post(
                create_url,
                headers=get_github_headers(),
                json=issue_data,
                timeout=10
            )
            response.raise_for_status()
            
            issue = response.json()
            print(f"✅ Issue created via REST API with @{GITHUB_COPILOT_USERNAME}")
            return issue
        
        except requests.exceptions.HTTPError as e:
            # Check if error is due to invalid assignee
            if e.response.status_code == 422 and "assignees" in e.response.text:
                print(f"⚠️  @{GITHUB_COPILOT_USERNAME} not available, creating without assignment...")
                
                # Retry without assignees
                issue_data_no_assignee = {
                    "title": title,
                    "body": body,
                    "labels": label_names,
                }
                
                response = requests.post(
                    create_url,
                    headers=get_github_headers(),
                    json=issue_data_no_assignee,
                    timeout=10
                )
                response.raise_for_status()
                
                issue = response.json()
                print(f"✅ Issue created (manual @{GITHUB_COPILOT_USERNAME} assignment needed)")
                return issue
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


def get_copilot_agent_id() -> Optional[str]:
    """
    Get the Copilot coding agent's GraphQL node ID using suggestedActors query.
    
    This is the official way to find Copilot agent according to GitHub docs:
    https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-a-pr
    
    Returns:
        Copilot agent's GraphQL ID (e.g., "BOT_...") or None if not found
    """
    graphql_url = f"{GITHUB_API_BASE}/graphql"
    
    # Query to find suggested actors with CAN_BE_ASSIGNED capability
    query = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        suggestedActors(capabilities: [CAN_BE_ASSIGNED], first: 100) {
          nodes {
            login
            __typename
            ... on Bot {
              id
            }
            ... on User {
              id
            }
          }
        }
      }
    }
    """
    
    variables = {
        "owner": TARGET_REPO_OWNER,
        "name": TARGET_REPO_NAME
    }
    
    try:
        response = requests.post(
            graphql_url,
            headers=get_github_headers(),
            json={"query": query, "variables": variables}
        )
        
        if response.status_code != 200:
            print(f"⚠️  Failed to query suggestedActors: {response.status_code}")
            return None
        
        data = response.json()
        
        if "errors" in data:
            print(f"⚠️  GraphQL errors: {data['errors']}")
            return None
        
        actors = data.get("data", {}).get("repository", {}).get("suggestedActors", {}).get("nodes", [])
        
        # Look for copilot-swe-agent (the official Copilot coding agent login)
        for actor in actors:
            if actor.get("login") == "copilot-swe-agent":
                agent_id = actor.get("id")
                if agent_id:
                    print(f"✅ Found Copilot agent ID: {agent_id}")
                    return agent_id
        
        print("⚠️  Copilot coding agent not found in suggestedActors")
        print("💡 Ensure Copilot is enabled for this repository")
        return None
        
    except Exception as e:
        print(f"❌ Error finding Copilot agent: {e}")
        return None


def assign_copilot_to_issue(issue_number: int) -> bool:
    """
    Assign GitHub Copilot coding agent to an existing issue using GraphQL API.
    
    Uses the official GitHub GraphQL API method with addAssigneesToAssignable mutation.
    First finds the Copilot agent via suggestedActors, then assigns it to the issue.
    
    Reference: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-a-pr
    
    Returns:
        True if assignment was successful, False otherwise
    """
    try:
        print(f"🤖 Assigning @copilot-swe-agent to issue #{issue_number}...")
        
        # Step 1: Get Copilot agent's GraphQL ID
        copilot_id = get_copilot_agent_id()
        if not copilot_id:
            return False
        
        # Step 2: Get issue's GraphQL node ID
        issue_url = f"{GITHUB_API_BASE}/repos/{TARGET_REPO_OWNER}/{TARGET_REPO_NAME}/issues/{issue_number}"
        issue_response = requests.get(issue_url, headers=get_github_headers())
        
        if issue_response.status_code != 200:
            print(f"❌ Failed to fetch issue: {issue_response.status_code}")
            return False
        
        issue_data = issue_response.json()
        issue_node_id = issue_data.get("node_id")
        
        if not issue_node_id:
            print("❌ Could not get issue node_id")
            return False
        
        # Step 3: Use GraphQL mutation to assign Copilot
        graphql_url = f"{GITHUB_API_BASE}/graphql"
        mutation = """
        mutation($issueId: ID!, $assigneeIds: [ID!]!) {
          addAssigneesToAssignable(input: {assignableId: $issueId, assigneeIds: $assigneeIds}) {
            assignable {
              ... on Issue {
                number
                assignees(first: 10) {
                  nodes {
                    login
                  }
                }
              }
            }
          }
        }
        """
        
        variables = {
            "issueId": issue_node_id,
            "assigneeIds": [copilot_id]
        }
        
        response = requests.post(
            graphql_url,
            headers=get_github_headers(),
            json={"query": mutation, "variables": variables}
        )
        
        if response.status_code != 200:
            print(f"⚠️  GraphQL mutation failed with status {response.status_code}")
            print(f"📄 Response: {response.text[:200]}")
            return False
        
        result = response.json()
        
        if "errors" in result:
            print(f"❌ GraphQL errors: {result['errors']}")
            return False
        
        # Check if Copilot is in the assignees list
        assignees_data = result.get("data", {}).get("addAssigneesToAssignable", {}).get("assignable", {}).get("assignees", {}).get("nodes", [])
        assignee_logins = [a["login"] for a in assignees_data]
        
        if "copilot-swe-agent" in assignee_logins or GITHUB_COPILOT_USERNAME in assignee_logins:
            print("✅ Successfully assigned Copilot coding agent")
            return True
        else:
            print("⚠️  Copilot not found in assignees after mutation")
            print(f"💡 Assignees: {assignee_logins}")
            return False
            
    except Exception as e:
        print(f"❌ Error assigning Copilot: {e}")
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
    
    # Create new issue with Copilot assigned
    print("✨ No existing issue found, creating new issue...")
    issue = create_github_issue()
    
    issue_number = issue.get("number")
    issue_url = issue.get("html_url")
    assignees = issue.get("assignees", [])
    labels = [label.get("name") if isinstance(label, dict) else label for label in issue.get("labels", [])]
    
    print(f"\n✅ Successfully created issue #{issue_number}")
    print(f"🔗 URL: {issue_url}")
    
    # Check assignee status
    assignee_names = [a.get("login") for a in assignees]
    if GITHUB_COPILOT_USERNAME in assignee_names or "copilot-swe-agent" in assignee_names:
        print(f"👤 Assigned to: @{GITHUB_COPILOT_USERNAME} (Copilot coding agent)")
    else:
        print(f"⚠️  @{GITHUB_COPILOT_USERNAME} not assigned")
        print(f"💡 Current assignees: {', '.join(assignee_names) if assignee_names else 'None'}")
        print(f"💡 You may need to manually assign - visit {issue_url}")
    
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
