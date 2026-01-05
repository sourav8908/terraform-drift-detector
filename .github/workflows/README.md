# GitHub Actions Workflows

## 🔍 Drift Detection Workflow

Automatically detects Terraform drift and posts results on PRs.

### Setup Instructions

#### 1. Add AWS Credentials to GitHub Secrets

Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these secrets:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `AWS_ACCESS_KEY_ID` | Your AWS access key | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_REGION` | Your AWS region | `ap-south-1` |

#### 2. Update State File Path

In `.github/workflows/drift-detection.yml`, line 48:
```yaml
python main.py terraform.tfstate --output drift_report.html
```

Change `terraform.tfstate` to your actual state file path:
- Example: `terraform/prod.tfstate`
- Example: `environments/production/terraform.tfstate`

#### 3. Commit and Push
```bash
git add .github/
git commit -m "Add drift detection GitHub Actions workflow"
git push origin main
```

### Workflow Triggers

| Trigger | Description |
|---------|-------------|
| **Push to main** | Runs on every push to main branch |
| **Pull Request** | Runs on every PR to main |
| **Schedule** | Daily at 9 AM UTC |
| **Manual** | Via Actions tab → "Run workflow" |

### What It Does

1. ✅ Checks out your code
2. ✅ Sets up Python environment
3. ✅ Installs dependencies
4. ✅ Configures AWS credentials (from secrets)
5. ✅ Runs drift detection
6. ✅ Uploads HTML report as artifact
7. ✅ Comments on PR with results (if PR)
8. ✅ Fails workflow if drift detected

### Viewing Results

#### On Pull Requests

The bot will automatically comment with:
- Drift summary
- Auto-generated fix code
- Link to download full report

#### In Actions Tab

1. Go to **Actions** tab
2. Click on the workflow run
3. Download **drift-report-XXX** artifact
4. Unzip and open `drift_report.html`

### Customizing

#### Change Schedule
```yaml
schedule:
  - cron: '0 9 * * *'    # Daily at 9 AM UTC
  - cron: '0 0 * * 1'    # Weekly on Monday
  - cron: '0 9 * * 1-5'  # Weekdays only
```

#### Block PR Merge on Drift

1. Go to **Settings** → **Branches**
2. Add branch protection rule for `main`
3. Enable: "Require status checks to pass"
4. Select: "Check Terraform Drift"

Now PRs with drift cannot be merged!

### Troubleshooting

**Error: AWS credentials not configured**
- Check that secrets are added correctly
- Verify secret names match exactly

**Error: State file not found**
- Update state file path in workflow
- Ensure state file is committed to repo (if not remote)

**Error: Permission denied**
- Ensure workflow has `pull-requests: write` permission
- Check in workflow YAML file

### Cost Considerations

GitHub Actions is free for public repos.

For private repos:
- 2,000 minutes/month free
- Each workflow run ≈ 2-3 minutes
- Daily schedule = ~90 minutes/month (well within free tier)