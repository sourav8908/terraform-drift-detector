from datetime import datetime

class ReportGenerator:
    """Generates HTML reports for drift analysis"""
    
    def __init__(self, drift_results, metadata=None):
        """
        Initialize report generator
        
        Args:
            drift_results: List of drift analysis results
            metadata: Additional metadata (region, state file, etc.)
        """
        self.drift_results = drift_results
        self.metadata = metadata or {}
    
    def generate_html_report(self, output_file='drift_report.html'):
        """Generate HTML drift report"""
        
        total_resources = len(self.drift_results)
        drifted_resources = [r for r in self.drift_results if r['has_drift']]
        critical_drift = [r for r in drifted_resources if r['severity'] == 'CRITICAL']
        high_drift = [r for r in drifted_resources if r['severity'] == 'HIGH']
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terraform Drift Detection Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #5E35B1 0%, #311B92 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 42px;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .header .metadata {{
            font-size: 14px;
            opacity: 0.9;
            margin-top: 15px;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .card {{
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
        }}
        
        .card.total {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        .card.drifted {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }}
        
        .card.critical {{
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            color: white;
        }}
        
        .card.clean {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
        }}
        
        .card h3 {{
            font-size: 48px;
            margin-bottom: 10px;
        }}
        
        .card p {{
            font-size: 16px;
            opacity: 0.95;
        }}
        
        .section {{
            margin: 50px 0;
        }}
        
        .section-title {{
            font-size: 28px;
            color: #333;
            margin-bottom: 25px;
            padding-bottom: 10px;
            border-bottom: 3px solid #5E35B1;
        }}
        
        .resource-card {{
            background: #f8f9fa;
            border-left: 5px solid #5E35B1;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 10px;
        }}
        
        .resource-card.critical {{
            border-left-color: #d32f2f;
            background: #ffebee;
        }}
        
        .resource-card.high {{
            border-left-color: #f57c00;
            background: #fff3e0;
        }}
        
        .resource-card.medium {{
            border-left-color: #fbc02d;
            background: #fffde7;
        }}
        
        .resource-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .resource-title {{
            font-size: 20px;
            font-weight: bold;
            color: #333;
        }}
        
        .severity-badge {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            color: white;
        }}
        
        .severity-critical {{
            background: #d32f2f;
        }}
        
        .severity-high {{
            background: #f57c00;
        }}
        
        .severity-medium {{
            background: #fbc02d;
        }}
        
        .drift-details {{
            margin-top: 15px;
        }}
        
        .drift-item {{
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 3px solid #5E35B1;
        }}
        
        .drift-item h4 {{
            color: #5E35B1;
            margin-bottom: 10px;
        }}
        
        .comparison {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 10px;
        }}
        
        .comparison-box {{
            padding: 10px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
        }}
        
        .state-value {{
            background: #e3f2fd;
            border: 1px solid #90caf9;
        }}
        
        .aws-value {{
            background: #fff3e0;
            border: 1px solid #ffb74d;
        }}
        
        .no-drift {{
            text-align: center;
            padding: 40px;
            color: #11998e;
            font-size: 18px;
        }}
        
        .footer {{
            text-align: center;
            padding: 30px;
            background: #f8f9fa;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Terraform Drift Detection Report</h1>
            <div class="metadata">
                <strong>Region:</strong> {self.metadata.get('region', 'N/A')} | 
                <strong>Analysis Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
                <strong>State File:</strong> {self.metadata.get('state_file', 'N/A')}
            </div>
        </div>
        
        <div class="content">
            <div class="summary-cards">
                <div class="card total">
                    <h3>{total_resources}</h3>
                    <p>📦 Total Resources</p>
                </div>
                <div class="card drifted">
                    <h3>{len(drifted_resources)}</h3>
                    <p>⚠️ Resources with Drift</p>
                </div>
                <div class="card critical">
                    <h3>{len(critical_drift)}</h3>
                    <p>🚨 Critical Drift</p>
                </div>
                <div class="card clean">
                    <h3>{total_resources - len(drifted_resources)}</h3>
                    <p>✅ Clean Resources</p>
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">⚠️ Resources with Drift</h2>
                {self._generate_drift_section(drifted_resources)}
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by <strong>Terraform Drift Detector</strong> | Built by Sourav Mohanty</p>
            <p style="margin-top: 10px;">💡 Tip: Review drift and update Terraform configuration or fix manual changes in AWS</p>
        </div>
    </div>
</body>
</html>
        """
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n✅ Report generated: {output_file}")
    
    def _generate_drift_section(self, drifted_resources):
        """Generate HTML for drifted resources"""
        if not drifted_resources:
            return '<div class="no-drift">🎉 No drift detected! All resources match Terraform state.</div>'
        
        html = ""
        for resource in drifted_resources:
            severity_class = resource['severity'].lower()
            
            html += f"""
            <div class="resource-card {severity_class}">
                <div class="resource-header">
                    <div class="resource-title">
                        {resource['resource_type']}.{resource['resource_name']}
                    </div>
                    <span class="severity-badge severity-{severity_class}">
                        {resource['severity']}
                    </span>
                </div>
                <p><strong>Issue:</strong> {resource['message']}</p>
            """
            
            if resource['drift_type'] == 'resource_deleted':
                html += """
                <div class="drift-details">
                    <p style="color: #d32f2f; font-weight: bold;">
                        ⚠️ This resource exists in Terraform state but was deleted from AWS!
                    </p>
                </div>
                """
            elif resource['drifted_attributes']:
                html += '<div class="drift-details">'
                for attr in resource['drifted_attributes']:
                    html += f"""
                    <div class="drift-item">
                        <h4>📌 Attribute: {attr['attribute']}</h4>
                        <div class="comparison">
                            <div class="comparison-box state-value">
                                <strong>Terraform State:</strong><br>
                                {self._format_value(attr['state_value'])}
                            </div>
                            <div class="comparison-box aws-value">
                                <strong>AWS Actual:</strong><br>
                                {self._format_value(attr['aws_value'])}
                            </div>
                        </div>
                    </div>
                    """
                html += '</div>'
            
            html += '</div>'
        
        return html
    
    def _format_value(self, value):
        """Format value for display"""
        if value is None:
            return '<em>null</em>'
        if isinstance(value, (dict, list)):
            import json
            return f'<pre>{json.dumps(value, indent=2)}</pre>'
        return str(value)