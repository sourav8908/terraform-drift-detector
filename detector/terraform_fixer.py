"""
Generates Terraform code to fix detected drift
"""

class TerraformFixer:
    """Generates Terraform fix code for drifted resources"""
    
    def __init__(self):
        """Initialize Terraform fixer"""
        pass
    
    def generate_fix_code(self, drift_results):
        """
        Generate Terraform code to fix all drifted resources
        
        Args:
            drift_results: List of drift analysis results
        
        Returns:
            dict: Fix code for each resource
        """
        fixes = []
        
        for result in drift_results:
            if not result['has_drift']:
                continue
            
            resource_type = result['resource_type']
            resource_name = result['resource_name']
            
            if result['drift_type'] == 'resource_deleted':
                # Resource was deleted from AWS
                fix = self._generate_import_command(result)
            else:
                # Attributes changed
                fix = self._generate_update_code(result)
            
            fixes.append(fix)
        
        return fixes
    
    def _generate_import_command(self, result):
        """Generate terraform import command for deleted resources"""
        resource_type = result['resource_type']
        resource_name = result['resource_name']
        
        # Get resource ID based on type
        resource_id = "RESOURCE_ID"  # Placeholder
        
        if resource_type == 'aws_instance':
            import_cmd = f"terraform import {resource_type}.{resource_name} <instance-id>"
            explanation = "Resource was deleted from AWS but exists in state"
            
        elif resource_type == 'aws_security_group':
            import_cmd = f"terraform import {resource_type}.{resource_name} <sg-id>"
            explanation = "Security group deleted from AWS"
            
        elif resource_type == 'aws_s3_bucket':
            import_cmd = f"terraform import {resource_type}.{resource_name} <bucket-name>"
            explanation = "S3 bucket deleted from AWS"
        
        else:
            import_cmd = f"terraform import {resource_type}.{resource_name} <resource-id>"
            explanation = "Resource deleted from AWS"
        
        return {
            'resource': f"{resource_type}.{resource_name}",
            'fix_type': 'import',
            'severity': result['severity'],
            'explanation': explanation,
            'command': import_cmd,
            'code': None,
            'manual_steps': [
                "1. Verify the resource no longer exists in AWS",
                "2. Remove from Terraform state: terraform state rm " + f"{resource_type}.{resource_name}",
                "3. Or recreate in AWS: terraform apply"
            ]
        }
    
    def _generate_update_code(self, result):
        """Generate updated Terraform code for drifted attributes"""
        resource_type = result['resource_type']
        resource_name = result['resource_name']
        drifted_attrs = result.get('drifted_attributes', [])
        
        # Generate HCL code based on resource type
        if resource_type == 'aws_instance':
            code = self._generate_instance_code(resource_name, drifted_attrs)
        elif resource_type == 'aws_security_group':
            code = self._generate_sg_code(resource_name, drifted_attrs)
        elif resource_type == 'aws_s3_bucket':
            code = self._generate_s3_code(resource_name, drifted_attrs)
        else:
            code = f"# Manual update required for {resource_type}.{resource_name}"
        
        return {
            'resource': f"{resource_type}.{resource_name}",
            'fix_type': 'update',
            'severity': result['severity'],
            'explanation': f"{len(drifted_attrs)} attribute(s) drifted",
            'drifted_attributes': drifted_attrs,
            'code': code,
            'command': "terraform apply",
            'manual_steps': [
                "1. Review the drifted attributes below",
                "2. Update your .tf file with the suggested changes",
                "3. Run: terraform plan (to verify changes)",
                "4. Run: terraform apply (to fix drift)"
            ]
        }
    
    def _generate_instance_code(self, resource_name, drifted_attrs):
        """Generate EC2 instance Terraform code"""
        lines = [
            f'resource "aws_instance" "{resource_name}" {{',
        ]
        
        for attr in drifted_attrs:
            attr_name = attr['attribute']
            aws_value = attr['aws_value']
            state_value = attr['state_value']
            
            # Format based on attribute type
            if attr_name == 'instance_type':
                lines.append(f'  instance_type = "{aws_value}"  # Changed from "{state_value}"')
            
            elif attr_name == 'ami':
                lines.append(f'  ami = "{aws_value}"  # Changed from "{state_value}"')
            
            elif attr_name == 'tags':
                lines.append(f'  # Tags changed:')
                lines.append(f'  # State: {state_value}')
                lines.append(f'  # AWS:   {aws_value}')
                lines.append(f'  tags = {self._format_dict_as_hcl(aws_value)}')
            
            elif attr_name == 'vpc_security_group_ids':
                lines.append(f'  vpc_security_group_ids = {self._format_list_as_hcl(aws_value)}')
            
            else:
                lines.append(f'  # {attr_name} changed: "{state_value}" -> "{aws_value}"')
        
        lines.append('}')
        lines.append('')
        lines.append('# Note: Update your actual .tf file with values from AWS (shown above)')
        lines.append('# Or run "terraform apply" to revert AWS to match your Terraform state')
        
        return '\n'.join(lines)
    
    def _generate_sg_code(self, resource_name, drifted_attrs):
        """Generate Security Group Terraform code"""
        lines = [
            f'resource "aws_security_group" "{resource_name}" {{',
        ]
        
        for attr in drifted_attrs:
            attr_name = attr['attribute']
            aws_value = attr['aws_value']
            state_value = attr['state_value']
            
            if attr_name == 'ingress':
                lines.append('  # Ingress rules changed')
                lines.append('  # State had:')
                for rule in (state_value or []):
                    lines.append(f'  #   - Port {rule.get("from_port")}-{rule.get("to_port")}, Protocol: {rule.get("protocol")}')
                lines.append('  # AWS now has:')
                for rule in (aws_value or []):
                    lines.append(f'  #   - Port {rule.get("from_port")}-{rule.get("to_port")}, Protocol: {rule.get("protocol")}')
                
                lines.append('')
                lines.append('  # Example ingress block (update with actual rules):')
                if aws_value:
                    for idx, rule in enumerate(aws_value[:3]):  # Show first 3
                        lines.append('  ingress {')
                        lines.append(f'    from_port   = {rule.get("from_port", 0)}')
                        lines.append(f'    to_port     = {rule.get("to_port", 0)}')
                        lines.append(f'    protocol    = "{rule.get("protocol", "tcp")}"')
                        cidr = rule.get("cidr_blocks", ["0.0.0.0/0"])
                        lines.append(f'    cidr_blocks = {self._format_list_as_hcl(cidr)}')
                        lines.append('  }')
            
            elif attr_name == 'description':
                lines.append(f'  description = "{aws_value}"  # Changed from "{state_value}"')
        
        lines.append('}')
        return '\n'.join(lines)
    
    def _generate_s3_code(self, resource_name, drifted_attrs):
        """Generate S3 bucket Terraform code"""
        lines = [
            f'resource "aws_s3_bucket" "{resource_name}" {{',
        ]
        
        for attr in drifted_attrs:
            attr_name = attr['attribute']
            aws_value = attr['aws_value']
            state_value = attr['state_value']
            
            if attr_name == 'versioning':
                lines.append(f'  # Versioning changed: "{state_value}" -> "{aws_value}"')
                lines.append('  versioning {')
                lines.append(f'    enabled = {str(aws_value == "Enabled").lower()}')
                lines.append('  }')
            
            elif attr_name == 'tags':
                lines.append(f'  tags = {self._format_dict_as_hcl(aws_value)}')
        
        lines.append('}')
        return '\n'.join(lines)
    
    def _format_dict_as_hcl(self, d):
        """Format Python dict as HCL map"""
        if not d or not isinstance(d, dict):
            return '{}'
        
        items = [f'{k} = "{v}"' for k, v in d.items()]
        return '{\n    ' + '\n    '.join(items) + '\n  }'
    
    def _format_list_as_hcl(self, lst):
        """Format Python list as HCL list"""
        if not lst or not isinstance(lst, list):
            return '[]'
        
        items = [f'"{item}"' for item in lst]
        return '[' + ', '.join(items) + ']'
    
    def generate_fix_summary(self, fixes):
        """Generate summary of all fixes"""
        if not fixes:
            return "✅ No drift detected - no fixes needed!"
        
        summary = []
        summary.append(f"# Terraform Drift Fix Summary")
        summary.append(f"# Total fixes needed: {len(fixes)}")
        summary.append("")
        
        # Group by severity
        critical = [f for f in fixes if f['severity'] == 'CRITICAL']
        high = [f for f in fixes if f['severity'] == 'HIGH']
        medium = [f for f in fixes if f['severity'] == 'MEDIUM']
        
        if critical:
            summary.append(f"## CRITICAL ({len(critical)})")
            for fix in critical:
                summary.append(f"- {fix['resource']}: {fix['explanation']}")
            summary.append("")
        
        if high:
            summary.append(f"## HIGH ({len(high)})")
            for fix in high:
                summary.append(f"- {fix['resource']}: {fix['explanation']}")
            summary.append("")
        
        if medium:
            summary.append(f"## MEDIUM ({len(medium)})")
            for fix in medium:
                summary.append(f"- {fix['resource']}: {fix['explanation']}")
            summary.append("")
        
        return '\n'.join(summary)
    
    def save_fixes_to_file(self, fixes, output_file='terraform_fixes.tf'):
        """Save all fix code to a file"""
        with open(output_file, 'w') as f:
            f.write("# Terraform Drift Fixes\n")
            f.write("# Generated by Terraform Drift Detector\n")
            f.write(f"# Generated at: {__import__('datetime').datetime.now()}\n")
            f.write("\n")
            f.write("# INSTRUCTIONS:\n")
            f.write("# 1. Review each resource below\n")
            f.write("# 2. Update your actual .tf files with the changes\n")
            f.write("# 3. Run 'terraform plan' to verify\n")
            f.write("# 4. Run 'terraform apply' to fix drift\n")
            f.write("\n")
            f.write("# " + "="*70 + "\n\n")
            
            for fix in fixes:
                f.write(f"# Resource: {fix['resource']}\n")
                f.write(f"# Severity: {fix['severity']}\n")
                f.write(f"# Issue: {fix['explanation']}\n")
                f.write("\n")
                
                if fix['fix_type'] == 'import':
                    f.write(f"# This resource was deleted from AWS\n")
                    f.write(f"# Command: {fix['command']}\n")
                    f.write("\n# Manual steps:\n")
                    for step in fix['manual_steps']:
                        f.write(f"# {step}\n")
                
                elif fix['code']:
                    f.write(fix['code'])
                    f.write("\n\n# Manual steps:\n")
                    for step in fix['manual_steps']:
                        f.write(f"# {step}\n")
                
                f.write("\n" + "# " + "-"*70 + "\n\n")
        
        return output_file