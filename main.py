import argparse
import sys
import yaml
from colorama import Fore, Style, init
from detector.terraform_fixer import TerraformFixer
from detector.state_reader import StateReader
from detector.aws_inspector import AWSInspector
from detector.drift_analyzer import DriftAnalyzer
from detector.report_generator import ReportGenerator

# Initialize colorama
init(autoreset=True)


def load_config():
    """Load configuration from YAML file"""
    try:
        with open("config/config.yaml", "r") as f:
            return yaml.safe_load(f)

    except FileNotFoundError:
        print(
            f"{Fore.YELLOW}⚠️  Warning: config/config.yaml not found, using defaults{Style.RESET_ALL}"
        )
        return {
            "aws": {"region": "ap-south-1", "profile": "default"},
            "detection": {
                "ignore_attributes": [
                    "id",
                    "arn",
                    "create_time",
                    "owner_id",
                    "state",
                ]
            },
            "report": {"output_file": "drift_report.html"},
        }

    except yaml.YAMLError as e:
        print(f"{Fore.RED}❌ Error parsing config.yaml: {e}{Style.RESET_ALL}")
        sys.exit(1)


def print_banner():
    """Print tool banner"""
    print(
        f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🔍  TERRAFORM DRIFT DETECTION TOOL  🔍                ║
║                                                              ║
║   Detect configuration drift between Terraform state         ║
║   and actual AWS resources                                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Terraform Drift Detector - Find configuration drift "
            "between Terraform state and AWS"
        )
    )

    parser.add_argument(
        "statefile",
        help="Path to terraform.tfstate file",
    )

    parser.add_argument(
        "--region",
        help="AWS region (overrides config)",
        default=None,
    )

    parser.add_argument(
        "--profile",
        help="AWS profile (overrides config)",
        default=None,
    )

    parser.add_argument(
        "--output",
        help="Output HTML report file",
        default=None,
    )

    args = parser.parse_args()

    # Load config
    config = load_config()

    # Override with command line args
    region = args.region or config["aws"]["region"]
    profile = args.profile or config["aws"]["profile"]
    output_file = args.output or config["report"]["output_file"]

    print_banner()

    print(f"{Fore.CYAN}📋 Configuration:{Style.RESET_ALL}")
    print(f"   State File : {args.statefile}")
    print(f"   AWS Region : {region}")
    print(f"   AWS Profile: {profile}")
    print(f"   Output     : {output_file}")
    print()

    try:
        # Step 1: Read Terraform state
        print(f"{Fore.CYAN}📖 Reading Terraform state...{Style.RESET_ALL}")
        state_reader = StateReader(args.statefile)
        resources = state_reader.get_resources()

        print(
            f"{Fore.GREEN}✅ Found {len(resources)} resources in state{Style.RESET_ALL}"
        )
        print(
            f"   Terraform Version: {state_reader.get_terraform_version()}"
        )
        print()

        # Step 2: Initialize AWS inspector
        print(f"{Fore.CYAN}🔧 Initializing AWS inspector...{Style.RESET_ALL}")
        aws_inspector = AWSInspector(region=region, profile=profile)
        print(f"{Fore.GREEN}✅ Connected to AWS{Style.RESET_ALL}")
        print()

        # Step 3: Analyze drift
        print(f"{Fore.CYAN}🔍 Analyzing drift...{Style.RESET_ALL}")
        drift_analyzer = DriftAnalyzer(
            ignore_attributes=config["detection"].get(
                "ignore_attributes", []
            )
        )

        drift_results = drift_analyzer.detect_drift(
            resources, aws_inspector
        )
        print()


        # Step 3.5: Generate Terraform fix code
        print(f"\n{Fore.CYAN}🔧 Generating Terraform fix code...{Style.RESET_ALL}")
        fixer = TerraformFixer()
        fixes = fixer.generate_fix_code(drift_results)
        
        if fixes:
            # Save fixes to file
            fix_file = fixer.save_fixes_to_file(fixes, 'terraform_fixes.tf')
            print(f"{Fore.GREEN}✅ Fix code saved to: {fix_file}{Style.RESET_ALL}")
            
            # Print summary
            print(f"\n{Fore.CYAN}📋 Fix Summary:{Style.RESET_ALL}")
            print(fixer.generate_fix_summary(fixes))
        else:
            print(f"{Fore.GREEN}✅ No fixes needed - all resources match!{Style.RESET_ALL}")


        # Step 4: Generate report
        print(f"{Fore.CYAN}📝 Generating drift report...{Style.RESET_ALL}")
        report_generator = ReportGenerator(
            drift_results=drift_results,
            metadata={
                "region": region,
                "state_file": args.statefile,
                "terraform_version": state_reader.get_terraform_version(),
            },
        )
        report_generator.generate_html_report(output_file)

        # Summary
        drifted = [r for r in drift_results if r["has_drift"]]
        critical = [
            r for r in drifted if r["severity"] == "CRITICAL"
        ]
        high = [r for r in drifted if r["severity"] == "HIGH"]

        print()
        print("=" * 60)
        print(f"{Fore.CYAN}📊 DRIFT ANALYSIS SUMMARY{Style.RESET_ALL}")
        print("=" * 60)
        print(f"  Total Resources Checked: {len(resources)}")
        print(
            f"  {Fore.RED}Resources with Drift: {len(drifted)}{Style.RESET_ALL}"
        )
        print(
            f"  {Fore.RED}  - Critical: {len(critical)}{Style.RESET_ALL}"
        )
        print(
            f"  {Fore.YELLOW}  - High: {len(high)}{Style.RESET_ALL}"
        )
        print(
            f"  {Fore.GREEN}Clean Resources: "
            f"{len(resources) - len(drifted)}{Style.RESET_ALL}"
        )
        print("=" * 60)

        if drifted:
            print(
                f"\n{Fore.YELLOW}⚠️  Drift detected! "
                f"Review {output_file} for details.{Style.RESET_ALL}"
            )
            sys.exit(1)
        else:
            print(
                f"\n{Fore.GREEN}✅ No drift detected! "
                f"All resources match Terraform state.{Style.RESET_ALL}"
            )
            sys.exit(0)

    except FileNotFoundError as e:
        print(f"\n{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        sys.exit(1)

    except Exception as e:
        print(
            f"\n{Fore.RED}❌ Unexpected error: {str(e)}{Style.RESET_ALL}"
        )
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
