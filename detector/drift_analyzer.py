from datetime import datetime, timedelta

# Attributes that commonly appear as null in AWS but aren't real drift
IGNORE_NULL_DRIFT = {
    'aws_instance': [
        'get_password_data', 'key_name', 'hibernation', 'placement_partition_number',
        'private_dns', 'user_data_replace_on_change', 'root_block_device',
        'ebs_optimized', 'disable_api_termination', 'disable_api_stop',
        'source_dest_check', 'ipv6_address_count', 'outpost_arn', 'security_groups',
        'tenancy', 'ephemeral_block_device', 'metadata_options', 'ebs_block_device',
        'cpu_core_count', 'host_id', 'private_dns_name_options', 'public_dns',
        'instance_lifecycle', 'instance_initiated_shutdown_behavior', 'tags_all',
        'associate_public_ip_address', 'password_data', 'capacity_reservation_specification',
        'instance_state', 'launch_template', 'credit_specification', 'ipv6_addresses',
        'cpu_threads_per_core', 'monitoring', 'primary_network_interface_id',
        'spot_instance_request_id', 'enclave_options', 'placement_group',
        'secondary_private_ips', 'maintenance_options', 'network_interface',
        'cpu_options', 'iam_instance_profile', 'instance_market_options', 'state'
    ],
    'aws_security_group': [
        'owner_id', 'arn', 'revoke_rules_on_delete', 'timeouts'
    ],
    'aws_s3_bucket': [
        'arn', 'bucket_domain_name', 'bucket_regional_domain_name',
        'hosted_zone_id', 'region', 'website_endpoint', 'website_domain'
    ]
}

class DriftAnalyzer:
    """Analyzes drift between Terraform state and actual AWS resources"""
    
    def __init__(self, ignore_attributes=None):
        """
        Initialize drift analyzer
        
        Args:
            ignore_attributes: List of attributes to ignore in comparison
        """
        self.ignore_attributes = ignore_attributes or [
            'id', 'arn', 'create_time', 'owner_id', 'state'
        ]
    
    def compare_values(self, state_value, aws_value, key, resource_type=''):
        """
        Compare two values and determine if there's drift
        
        Args:
            state_value: Value from Terraform state
            aws_value: Value from AWS
            key: Attribute key name
            resource_type: Type of resource (e.g., 'aws_instance')
        
        Returns:
            dict: Comparison result with has_drift and details
        """
        # Skip ignored attributes
        if key in self.ignore_attributes:
            return {'has_drift': False}
        
        # Skip null drift for known false positives
        if aws_value is None and resource_type in IGNORE_NULL_DRIFT:
            if key in IGNORE_NULL_DRIFT[resource_type]:
                return {'has_drift': False}
        
        # Handle None values
        if state_value is None and aws_value is None:
            return {'has_drift': False}
        
        if state_value is None or aws_value is None:
            # Only report as drift if it's a meaningful change
            # Skip if both are empty-like values
            if not state_value and not aws_value:
                return {'has_drift': False}
            
            return {
                'has_drift': True,
                'state_value': state_value,
                'aws_value': aws_value,
                'drift_type': 'value_changed'
            }
        
        # Compare lists (e.g., security group rules)
        if isinstance(state_value, list) and isinstance(aws_value, list):
            if sorted(str(state_value)) != sorted(str(aws_value)):
                return {
                    'has_drift': True,
                    'state_value': state_value,
                    'aws_value': aws_value,
                    'drift_type': 'list_changed'
                }
            return {'has_drift': False}
        
        # Compare dicts (e.g., tags)
        if isinstance(state_value, dict) and isinstance(aws_value, dict):
            if state_value != aws_value:
                return {
                    'has_drift': True,
                    'state_value': state_value,
                    'aws_value': aws_value,
                    'drift_type': 'dict_changed'
                }
            return {'has_drift': False}
        
        # Compare simple values
        if str(state_value) != str(aws_value):
            return {
                'has_drift': True,
                'state_value': state_value,
                'aws_value': aws_value,
                'drift_type': 'value_changed'
            }
        
        return {'has_drift': False}
    
    def compare_resource(self, state_resource, aws_resource):
        """
        Compare a single resource from state with AWS
        
        Args:
            state_resource: Resource from Terraform state
            aws_resource: Resource from AWS (or None if deleted)
        
        Returns:
            dict: Comparison result
        """
        resource_type = state_resource['resource_type']
        resource_name = state_resource['resource_name']
        
        # Resource deleted in AWS
        if aws_resource is None:
            return {
                'resource_type': resource_type,
                'resource_name': resource_name,
                'has_drift': True,
                'severity': 'CRITICAL',
                'drift_type': 'resource_deleted',
                'message': 'Resource exists in Terraform but not in AWS',
                'drifted_attributes': []
            }
        
        # Compare attributes
        state_attrs = state_resource['attributes']
        drifted_attributes = []
        
        # Get all unique keys from both
        all_keys = set(state_attrs.keys()) | set(aws_resource.keys())
        
        for key in all_keys:
            if key in self.ignore_attributes:
                continue
            
            state_value = state_attrs.get(key)
            aws_value = aws_resource.get(key)
            
            comparison = self.compare_values(state_value, aws_value, key, resource_type)
            
            if comparison['has_drift']:
                drifted_attributes.append({
                    'attribute': key,
                    'state_value': comparison.get('state_value'),
                    'aws_value': comparison.get('aws_value'),
                    'drift_type': comparison.get('drift_type')
                })
        
        # Determine severity
        severity = 'LOW'
        if len(drifted_attributes) > 0:
            # Critical attributes
            critical_attrs = ['instance_type', 'ami', 'ingress', 'egress', 'versioning']
            if any(attr['attribute'] in critical_attrs for attr in drifted_attributes):
                severity = 'HIGH'
            elif len(drifted_attributes) > 3:
                severity = 'MEDIUM'
        
        return {
            'resource_type': resource_type,
            'resource_name': resource_name,
            'has_drift': len(drifted_attributes) > 0,
            'severity': severity,
            'drift_type': 'attributes_changed',
            'message': f'{len(drifted_attributes)} attribute(s) have drifted',
            'drifted_attributes': drifted_attributes
        }
    
    def detect_drift(self, state_resources, aws_inspector):
        """
        Detect drift across all resources
        
        Args:
            state_resources: List of resources from Terraform state
            aws_inspector: AWSInspector instance
        
        Returns:
            list: Resources with drift
        """
        drift_results = []
        
        for state_resource in state_resources:
            resource_type = state_resource['resource_type']
            resource_id = state_resource['attributes'].get('id')
            
            print(f"Checking {resource_type}.{state_resource['resource_name']}...", end=" ")
            
            # Get actual resource from AWS
            aws_resource = None
            if resource_type == 'aws_instance':
                aws_resource = aws_inspector.get_instance_details(resource_id)
            elif resource_type == 'aws_security_group':
                aws_resource = aws_inspector.get_security_group_details(resource_id)
            elif resource_type == 'aws_s3_bucket':
                bucket_name = state_resource['attributes'].get('bucket')
                aws_resource = aws_inspector.get_s3_bucket_details(bucket_name)
            
            # Compare
            result = self.compare_resource(state_resource, aws_resource)
            drift_results.append(result)
            
            # Print result
            if result['has_drift']:
                from colorama import Fore, Style
                color = Fore.RED if result['severity'] == 'CRITICAL' else Fore.YELLOW
                print(f"{color}DRIFT DETECTED ({len(result['drifted_attributes'])} real issues){Style.RESET_ALL}")
            else:
                from colorama import Fore, Style
                print(f"{Fore.GREEN}OK{Style.RESET_ALL}")
        
        return drift_results