````markdown
# Terraform Drift Detection Tool 🔍

Automatically detect configuration drift between Terraform state and actual AWS infrastructure.

## 🎯 Problem It Solves

When teams use Terraform, manual changes in the AWS console can cause "drift" - where the actual infrastructure no longer matches what Terraform expects. This tool:

- ✅ Compares Terraform state with real AWS resources
- ✅ Detects manual changes made outside Terraform
- ✅ Categorizes drift by severity (Critical/High/Medium)
- ✅ Generates beautiful HTML reports
- ✅ Helps prevent configuration inconsistencies

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- AWS credentials configured (`aws configure`)
- Terraform state file

### Installation
```bash
# Clone repository
git clone https://github.com/sourav8908/terraform-drift-detector.git
cd terraform-drift-detector

# Install dependencies
pip install -r requirements.txt
```

### Usage
```bash
# Basic usage
python main.py path/to/terraform.tfstate

# Specify AWS region
python main.py terraform.tfstate --region us-west-2

# Use specific AWS profile
python main.py terraform.tfstate --profile production

# Custom output file
python main.py terraform.tfstate --output my_drift_report.html
```

## 📊 Sample Output
````
🔍  TERRAFORM DRIFT DETECTION TOOL  🔍

📋 Configuration:
   State File: terraform.tfstate
   AWS Region: us-east-1
   AWS Profile: default
   Output: drift_report.html

📖 Reading Terraform state...
✅ Found 8 resources in state
   Terraform Version: 1.5.0

🔧 Initializing AWS inspector...
✅ Connected to AWS

🔍 Analyzing drift...
Checking aws_instance.web_server... DRIFT DETECTED
Checking aws_security_group.main... OK
Checking aws_s3_bucket.data... OK

📝 Generating drift report...
✅ Report generated: drift_report.html

═══════════════════════════════════════════════════════════
📊 DRIFT ANALYSIS SUMMARY
═══════════════════════════════════════════════════════════
  Total Resources Checked: 8
  Resources with Drift: 1
    - Critical: 0
    - High: 1
  Clean Resources: 7
═══════════════════════════════════════════════════════════

⚠️  Drift detected! Review drift_report.html for details.

## 🤖 CI/CD Integration

### GitHub Actions

Automatically detect drift in your CI/CD pipeline!

#### Quick Setup

1. **Add workflow file:**
```bash
   cp .github/workflows/drift-detection.yml .github/workflows/
```

2. **Configure AWS credentials:**
```bash
   # In GitHub repo settings → Secrets
   AWS_ACCESS_KEY_ID: your-key
   AWS_SECRET_ACCESS_KEY: your-secret
```

3. **Commit and push:**
```bash
   git add .github/workflows/
   git commit -m "Add drift detection workflow"
   git push
```

#### Features

- ✅ Automatic drift detection on every PR
- ✅ Daily scheduled scans
- ✅ PR comments with drift summary
- ✅ Auto-generated Terraform fix code
- ✅ Downloadable HTML reports

#### Workflow Triggers

| Trigger | When |
|---------|------|
| **Push** | Every push to main |
| **Pull Request** | Every PR |
| **Schedule** | Daily at 9 AM UTC |
| **Manual** | Via Actions tab |

#### Example PR Comment
```
🚨 Terraform Drift Detected!

Summary:
- 3 resources have drift
- 2 HIGH severity issues
- 1 MEDIUM severity issue

Suggested Fixes:
resource "aws_instance" "web_server" {
  instance_type = "t2.small"  # Changed from t2.micro
}

Download full report from workflow artifacts
```

### Other CI/CD Platforms

**Jenkins:**
```groovy
stage('Drift Detection') {
    steps {
        sh 'python main.py terraform.tfstate'
    }
}
```

**GitLab CI:**
```yaml
drift_check:
  script:
    - python main.py terraform.tfstate
  artifacts:
    paths:
      - drift_report.html
```

## 🔧 Auto-Fix Code Generation

The tool now automatically generates Terraform code to fix detected drift!

### What It Generates

1. **Updated HCL Code** - Modified resource definitions
2. **Import Commands** - For deleted resources
3. **Manual Steps** - Remediation instructions

### Example Output
```hcl
# Resource: aws_instance.web_server
# Severity: HIGH
# Issue: 1 attribute(s) drifted

resource "aws_instance" "web_server" {
  instance_type = "t2.small"  # Changed from "t2.micro"
  
  tags = {
    Name = "web-server"
    Owner = "devops"  # Added manually in AWS
  }
}

# Manual steps:
# 1. Review the drifted attributes above
# 2. Update your .tf file with the suggested changes
# 3. Run: terraform plan (to verify changes)
# 4. Run: terraform apply (to fix drift)
```

### Using Generated Fixes
```bash
# Run drift detection
py main.py terraform-test/terraform.tfstate

# Review generated fixes
cat terraform_fixes.tf

# Apply fixes to your Terraform files
# Then run:
terraform plan
terraform apply
```


## 🤖 CI/CD Integration

### GitHub Actions (Recommended)

Automatically detect drift in your CI/CD pipeline!

#### Quick Setup

1. **Add GitHub Secrets:**
```
   Settings → Secrets → Actions → New secret
   
   - AWS_ACCESS_KEY_ID: your-access-key
   - AWS_SECRET_ACCESS_KEY: your-secret-key
   - AWS_REGION: ap-south-1 (or your region)
```

2. **Workflow is already configured!**
   - File: `.github/workflows/drift-detection.yml`
   - Triggers: Push, PR, Daily at 9 AM, Manual

3. **Update state file path** (if needed):
```yaml
   # In .github/workflows/drift-detection.yml, line 48:
   python main.py YOUR-STATE-FILE.tfstate
```

4. **Push to GitHub:**
```bash
   git add .
   git commit -m "Add drift detection workflow"
   git push
```

#### Features

- ✅ Automatic drift detection on every PR
- ✅ Daily scheduled scans
- ✅ PR comments with drift summary
- ✅ Auto-generated Terraform fix code
- ✅ Downloadable HTML reports
- ✅ Workflow fails if drift detected

#### Example PR Comment
```
🚨 Terraform Drift Detected!

Summary:
  Total Resources Checked: 5
  Resources with Drift: 2
    - Critical: 0
    - High: 2

Auto-Generated Fixes:
resource "aws_instance" "web" {
  instance_type = "t2.small"  # Changed from t2.micro
}

📥 Download Full Report
Go to Actions → This workflow → drift-report artifact

🔧 Next Steps
1. Review drift report
2. Update .tf files
3. Run terraform apply
```

### Other CI/CD Platforms

**Jenkins:**
```groovy
stage('Drift Detection') {
    steps {
        sh 'python main.py terraform.tfstate'
    }
}
```

**GitLab CI:**
```yaml
drift_check:
  script:
    - python main.py terraform.tfstate
  artifacts:
    paths:
      - drift_report.html
```

**CircleCI:**
```yaml
- run:
    name: Check Drift
    command: python main.py terraform.tfstate
```