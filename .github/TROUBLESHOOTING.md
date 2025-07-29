# GitHub Actions Troubleshooting

## Common Issues and Solutions

### Issue: "workflow is not reusable as it is missing a `on.workflow_call` trigger"

This error occurs when GitHub Actions tries to use workflow files from an older commit that doesn't
have the required `workflow_call` trigger.

#### Root Cause

- GitHub Actions uses the workflow files from the commit that triggered the run
- If a workflow was triggered on an older commit (before workflow_call was added), it will fail
- This commonly happens with queued or long-running workflows

#### Solution

1. **Cancel old workflow runs**:

   ```bash
   # Run the helper script
   ./.github/scripts/cancel-old-workflows.sh

   # Or manually cancel via GitHub CLI
   gh run list --limit 20
   gh run cancel <run-id>
   ```

1. **Ensure you're on the latest main branch**:

   ```bash
   git checkout main
   git pull origin main
   ```

1. **Re-trigger the workflow**:

   ```bash
   # Via GitHub CLI
   gh workflow run build.yml

   # Or via GitHub UI
   # Go to Actions tab → Select workflow → Run workflow
   ```

#### Prevention

- Always ensure workflows are up to date before triggering
- Use `concurrency` groups to auto-cancel old runs
- Consider adding `if: github.sha == github.event.repository.default_branch` to critical jobs

### Issue: Coverage not being uploaded for all test types

Ensure that:

1. All test commands include coverage flags
1. Coverage files are properly renamed to avoid conflicts
1. The upload-coverage job includes all test job dependencies
1. Codecov.yml includes all necessary flags

### Issue: Workflows timing out

Common causes:

1. Services not starting properly in integration tests
1. Infinite loops in wait conditions
1. Missing timeout configurations

Solutions:

- Add explicit timeouts to all jobs and steps
- Use health checks for service containers
- Implement proper retry logic with exponential backoff
