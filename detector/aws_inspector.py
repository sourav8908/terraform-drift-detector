import boto3
from botocore.exceptions import ClientError

class AWSInspector:
    """Queries actual AWS resources to compare with Terraform state"""
    
    def __init__(self, region='ap-south-1', profile='default'):
        """
        Initialize AWS inspector
        
        Args:
            region: AWS region
            profile: AWS profile name
        """
        self.region = region
        
        # Create session
        if profile and profile != 'default':
            session = boto3.Session(profile_name=profile, region_name=region)
            self.ec2 = session.client('ec2')
            self.s3 = session.client('s3')
        else:
            self.ec2 = boto3.client('ec2', region_name=region)
            self.s3 = boto3.client('s3')
    
    def get_instance_details(self, instance_id):
        """
        Get actual EC2 instance details from AWS
        
        Args:
            instance_id: EC2 instance ID
        
        Returns:
            dict: Instance details or None if not found
        """
        try:
            response = self.ec2.describe_instances(InstanceIds=[instance_id])
            
            if not response['Reservations']:
                return None
            
            instance = response['Reservations'][0]['Instances'][0]
            
            # Normalize to Terraform format
            return {
                'id': instance['InstanceId'],
                'instance_type': instance['InstanceType'],
                'ami': instance['ImageId'],
                'availability_zone': instance['Placement']['AvailabilityZone'],
                'subnet_id': instance.get('SubnetId', ''),
                'vpc_security_group_ids': [sg['GroupId'] for sg in instance.get('SecurityGroups', [])],
                'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])},
                'state': instance['State']['Name'],
                'private_ip': instance.get('PrivateIpAddress', ''),
                'public_ip': instance.get('PublicIpAddress', '')
            }
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidInstanceID.NotFound':
                return None
            raise
    
    def get_security_group_details(self, sg_id):
        """
        Get actual Security Group details from AWS
        
        Args:
            sg_id: Security Group ID
        
        Returns:
            dict: Security group details or None if not found
        """
        try:
            response = self.ec2.describe_security_groups(GroupIds=[sg_id])
            
            if not response['SecurityGroups']:
                return None
            
            sg = response['SecurityGroups'][0]
            
            # Normalize ingress rules
            ingress = []
            for rule in sg.get('IpPermissions', []):
                ingress.append({
                    'from_port': rule.get('FromPort', 0),
                    'to_port': rule.get('ToPort', 0),
                    'protocol': rule.get('IpProtocol', '-1'),
                    'cidr_blocks': [ip['CidrIp'] for ip in rule.get('IpRanges', [])],
                    'security_groups': [sg['GroupId'] for sg in rule.get('UserIdGroupPairs', [])]
                })
            
            # Normalize egress rules
            egress = []
            for rule in sg.get('IpPermissionsEgress', []):
                egress.append({
                    'from_port': rule.get('FromPort', 0),
                    'to_port': rule.get('ToPort', 0),
                    'protocol': rule.get('IpProtocol', '-1'),
                    'cidr_blocks': [ip['CidrIp'] for ip in rule.get('IpRanges', [])],
                    'security_groups': [sg['GroupId'] for sg in rule.get('UserIdGroupPairs', [])]
                })
            
            return {
                'id': sg['GroupId'],
                'name': sg['GroupName'],
                'description': sg['Description'],
                'vpc_id': sg.get('VpcId', ''),
                'ingress': ingress,
                'egress': egress,
                'tags': {tag['Key']: tag['Value'] for tag in sg.get('Tags', [])}
            }
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidGroup.NotFound':
                return None
            raise
    
    def get_s3_bucket_details(self, bucket_name):
        """
        Get actual S3 bucket details from AWS
        
        Args:
            bucket_name: S3 bucket name
        
        Returns:
            dict: Bucket details or None if not found
        """
        try:
            # Check if bucket exists
            self.s3.head_bucket(Bucket=bucket_name)
            
            # Get bucket details
            location = self.s3.get_bucket_location(Bucket=bucket_name)
            versioning = self.s3.get_bucket_versioning(Bucket=bucket_name)
            
            try:
                tags_response = self.s3.get_bucket_tagging(Bucket=bucket_name)
                tags = {tag['Key']: tag['Value'] for tag in tags_response.get('TagSet', [])}
            except ClientError:
                tags = {}
            
            return {
                'bucket': bucket_name,
                'region': location.get('LocationConstraint', 'us-east-1'),
                'versioning': versioning.get('Status', 'Disabled'),
                'tags': tags
            }
        except ClientError as e:
            if e.response['Error']['Code'] in ['404', 'NoSuchBucket']:
                return None
            raise
    
    def resource_exists(self, resource_type, resource_id):
        """
        Check if a resource exists in AWS
        
        Args:
            resource_type: Type of resource (e.g., "aws_instance")
            resource_id: Resource identifier
        
        Returns:
            bool: True if exists, False otherwise
        """
        if resource_type == 'aws_instance':
            return self.get_instance_details(resource_id) is not None
        elif resource_type == 'aws_security_group':
            return self.get_security_group_details(resource_id) is not None
        elif resource_type == 'aws_s3_bucket':
            return self.get_s3_bucket_details(resource_id) is not None
        
        return False