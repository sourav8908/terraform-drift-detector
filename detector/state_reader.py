import json
import os

class StateReader:
    """Reads and parses Terraform state files"""
    
    def __init__(self, state_file_path):
        """
        Initialize state reader
        
        Args:
            state_file_path: Path to terraform.tfstate file
        """
        if not os.path.exists(state_file_path):
            raise FileNotFoundError(f"State file not found: {state_file_path}")
        
        self.state_file_path = state_file_path
        self.state_data = self._read_state()
    
    def _read_state(self):
        """Read and parse the state file"""
        try:
            with open(self.state_file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in state file: {e}")
    
    def get_resources(self):
        """
        Extract all managed resources from state
        
        Returns:
            list: List of resource dictionaries
        """
        resources = []
        
        if 'resources' not in self.state_data:
            return resources
        
        for resource in self.state_data['resources']:
            # Only process managed resources (not data sources)
            if resource.get('mode') != 'managed':
                continue
            
            resource_type = resource.get('type')
            resource_name = resource.get('name')
            
            # Get instances (a resource can have multiple instances)
            instances = resource.get('instances', [])
            
            for idx, instance in enumerate(instances):
                attributes = instance.get('attributes', {})
                
                resources.append({
                    'resource_type': resource_type,
                    'resource_name': resource_name,
                    'instance_index': idx,
                    'attributes': attributes,
                    'provider': resource.get('provider', 'unknown')
                })
        
        return resources
    
    def get_resources_by_type(self, resource_type):
        """
        Get all resources of a specific type
        
        Args:
            resource_type: e.g., "aws_instance", "aws_security_group"
        
        Returns:
            list: Filtered resources
        """
        all_resources = self.get_resources()
        return [r for r in all_resources if r['resource_type'] == resource_type]
    
    def get_resource_count(self):
        """Get total number of resources in state"""
        return len(self.get_resources())
    
    def get_terraform_version(self):
        """Get Terraform version used to create state"""
        return self.state_data.get('terraform_version', 'unknown')