#!/usr/bin/env python3
"""
Assign GitHub issue to Copilot coding agent with context instructions.

This script:
1. Assigns the issue to @copilot (or copilot-swe-agent)
2. Adds a comment with specific instructions about the context branch
3. Uses GitHub's official API to trigger Copilot agent
"""

import os
import sys
from typing import Optional, Dict, Any
import requests

# Configuration from environment variables
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
TARGET_REPO_OWNER = os.environ.get("TARGET_REPO_OWNER")
TARGET_REPO_NAME = os.environ.get("TARGET_REPO_NAME")
ISSUE_NUMBER = os.environ.get("ISSUE_NUMBER")
CONTEXT_BRANCH = os.environ.get("CONTEXT_BRANCH")

# GitHub API configuration
GITHUB_API_BASE = "https://api.github.com"


def check_required_env_vars():
    """Validate that all required environment variables are set."""
    required_vars = {
        "GITHUB_TOKEN": GITHUB_TOKEN,
        "TARGET_REPO_OWNER": TARGET_REPO_OWNER,
        "TARGET_REPO_NAME": TARGET_REPO_NAME,
        "ISSUE_NUMBER": ISSUE_NUMBER,
        "CONTEXT_BRANCH": CONTEXT_BRANCH,
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


def assign_copilot_to_issue() -> bool:
    """
    Assign GitHub Copilot coding agent to an existing issue using GraphQL API.
    
    Uses the official GitHub GraphQL API method with addAssigneesToAssignable mutation.
    First finds the Copilot agent via suggestedActors, then assigns it to the issue.
    
    This is the proven working approach from create_issue_mcp.py.
    
    Returns:
        True if assignment was successful, False otherwise
    """
    issue_num = int(ISSUE_NUMBER)
    
    try:
        print(f"🤖 Assigning @copilot-swe-agent to issue #{issue_num}...")
        
        # Step 1: Get Copilot agent's GraphQL ID
        copilot_id = get_copilot_agent_id()
        if not copilot_id:
            print("⚠️  Could not find Copilot agent ID")
            return False
        
        # Step 2: Get issue's GraphQL node ID
        issue_url = f"{GITHUB_API_BASE}/repos/{TARGET_REPO_OWNER}/{TARGET_REPO_NAME}/issues/{issue_num}"
        issue_response = requests.get(issue_url, headers=get_github_headers(), timeout=10)
        
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
            json={"query": mutation, "variables": variables},
            timeout=10
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
        
        if "copilot-swe-agent" in assignee_logins:
            print("✅ Successfully assigned Copilot coding agent")
            return True
        else:
            print("⚠️  Copilot not found in assignees after mutation")
            print(f"💡 Assignees: {assignee_logins}")
            return False
            
    except Exception as e:
        print(f"❌ Error assigning Copilot: {e}")
        import traceback
        traceback.print_exc()
        return False


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
            json={"query": query, "variables": variables},
            timeout=10
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
        import traceback
        traceback.print_exc()
        return None


def add_copilot_instructions_comment() -> bool:
    """
    Add a comment to the issue with clear instructions for Copilot.
    
    This ensures Copilot knows about the context branch and documentation.
    
    Returns:
        True if successful, False otherwise
    """
    issue_num = int(ISSUE_NUMBER)
    
    print(f"💬 Adding instructions comment to issue #{issue_num}...")
    
    comment_body = f"""## 🤖 @copilot - Implementation Instructions

Hi @copilot! Please work on this issue following these steps:

### 1️⃣ Switch to Context Branch
```bash
git checkout {CONTEXT_BRANCH}
```

### 2️⃣ Read Project Documentation
Before implementing, please review the project standards in the `docs/` directory:

**Architecture & Standards:**
- `docs/architecture/overview.md` - System architecture, tech stack, patterns
- `docs/api-standards/naming-conventions.md` - Naming conventions for APIs, URLs, fields
- `docs/api-standards/crud-api-spec.md` - CRUD API specification with examples

**Laravel Backend:**
- `docs/laravel/core-patterns.md` - MVC patterns, controllers, models
- `docs/laravel/database-access-layer.md` - Eloquent ORM, queries, migrations
- `docs/laravel/error-handling.md` - Error handling patterns
- `docs/laravel/unit-testing-standards.md` - PHPUnit testing patterns

**React Frontend:**
- `docs/react/component-structure.md` - Component organization and patterns
- `docs/react/state-management.md` - React Query, Context API, state patterns
- `docs/react/api-consumption.md` - Service layer, Axios configuration
- `docs/react/testing-library-patterns.md` - React Testing Library patterns

### 3️⃣ Implementation Guidelines
- ✅ Follow the established patterns from the documentation
- ✅ Adhere to naming conventions
- ✅ Use the specified error handling approach
- ✅ Write tests following the testing standards
- ✅ Make all changes on the `{CONTEXT_BRANCH}` branch

### 4️⃣ Create Pull Request
Once implementation is complete, create a PR from `{CONTEXT_BRANCH}` to the default branch.

---

**Note:** All project coding standards are defined in the documentation above. Please ensure your implementation strictly follows these patterns.
"""
    
    comment_url = f"{GITHUB_API_BASE}/repos/{TARGET_REPO_OWNER}/{TARGET_REPO_NAME}/issues/{issue_num}/comments"
    
    try:
        response = requests.post(
            comment_url,
            headers=get_github_headers(),
            json={"body": comment_body},
            timeout=10
        )
        response.raise_for_status()
        
        print("✅ Instructions comment added successfully")
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error adding comment: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text[:200]}")
        return False


def main():
    """Main execution flow."""
    print("🚀 Starting Copilot assignment with context...")
    print(f"📍 Target Repository: {TARGET_REPO_OWNER}/{TARGET_REPO_NAME}")
    print(f"🎫 Issue Number: #{ISSUE_NUMBER}")
    print(f"🌿 Context Branch: {CONTEXT_BRANCH}")
    
    # Validate environment variables
    check_required_env_vars()
    
    # Add instructions comment FIRST (so Copilot sees it immediately)
    comment_added = add_copilot_instructions_comment()
    
    if not comment_added:
        print("⚠️  Warning: Could not add instructions comment")
    
    # Try to assign Copilot to the issue
    assignment_successful = assign_copilot_to_issue()
    
    if assignment_successful:
        print(f"\n✅ Successfully assigned @copilot-swe-agent to issue #{ISSUE_NUMBER}")
        print(f"📚 Instructions added with full project context")
        print(f"🌿 Copilot will work on branch: {CONTEXT_BRANCH}")
        print(f"🔗 URL: https://github.com/{TARGET_REPO_OWNER}/{TARGET_REPO_NAME}/issues/{ISSUE_NUMBER}")
    else:
        print(f"\n⚠️  Issue created with instructions, but automatic assignment may have failed")
        print(f"💡 Please manually assign @copilot to issue #{ISSUE_NUMBER}")
        print(f"🔗 URL: https://github.com/{TARGET_REPO_OWNER}/{TARGET_REPO_NAME}/issues/{ISSUE_NUMBER}")
        print(f"\n📝 Next steps:")
        print(f"   1. Visit the issue URL above")
        print(f"   2. Click 'Assignees' on the right sidebar")
        print(f"   3. Search for and select '@copilot' or 'copilot-swe-agent'")
        print(f"   4. Copilot will automatically start working on the issue")
        
        # Don't fail the workflow if only assignment failed but comment was added
        if comment_added:
            print(f"\n✅ Instructions are available for manual assignment")
        else:
            print(f"\n❌ Both assignment and comment failed")
            sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
