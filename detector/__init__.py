from .terraform_fixer import TerraformFixer

"""
Terraform Drift Detector
Detects configuration drift between Terraform state and actual AWS resources
"""

__version__ = "1.0.0"
__author__ = "Sourav Mohanty"

from .state_reader import StateReader
from .aws_inspector import AWSInspector
from .drift_analyzer import DriftAnalyzer
from .report_generator import ReportGenerator

__all__ = [
    'StateReader',
    'AWSInspector',
    'DriftAnalyzer',
    'ReportGenerator',
    'TerraformFixer'
]