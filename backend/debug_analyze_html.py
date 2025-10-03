# backend/simple_debug.py
import os
import re
import glob
from datetime import datetime

def quick_analysis():
    """Quick analysis without external dependencies"""
    debug_dir = "debug_html"
    
    if not os.path.exists(debug_dir):
        print("❌ No debug_html directory - run scraper first")
        return
    
    files = glob.glob(os.path.join(debug_dir, "*"))
    
    if not files:
        print("❌ No files found")
        return
    
    print(f"📁 Found {len(files)} files:")
    for file in files:
        size = os.path.getsize(file)
        print(f"  {os.path.basename(file)} ({size} bytes)")
    
    # Analyze most recent file
    latest = max(files, key=os.path.getctime)
    print(f"\n🔍 Analyzing: {latest}")
    
    with open(latest, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    print(f"📊 Size: {len(content)} chars")
    
    # Quick checks
    print("\n🔎 Quick Analysis:")
    checks = {
        'LinkedIn': 'LinkedIn' in content,
        'Job Title': any(word in content for word in ['Director', 'Manager', 'Engineer']),
        'Company': 'Partners' in content or 'Inc' in content or 'Corp' in content,
        'Location': any(word in content for word in ['Miami', 'FL', 'Remote']),
        'Description': any(phrase in content for phrase in ['About the job', 'Role Description']),
        'Applicants': 'applicants' in content,
        'HTML Tags': '<div' in content or '<h1' in content,
    }
    
    for check, result in checks.items():
        print(f"  {'✅' if result else '❌'} {check}")
    
    # Show what we found
    print(f"\n🎯 Found Data:")
    
    # Title
    title_match = re.search(r'([A-Z][A-Za-z\s\/]+Manager|[A-Z][A-Za-z\s\/]+Director)', content)
    if title_match:
        print(f"  📝 Title: {title_match.group(0)}")
    
    # Company
    company_match = re.search(r'Oolite Partners|([A-Z][A-Za-z\s&]+)(?=\s•)', content)
    if company_match:
        print(f"  🏢 Company: {company_match.group(0)}")
    
    # Location
    location_match = re.search(r'Miami,\s*FL|([A-Za-z]+(?:,\s*[A-Z]{2}))', content)
    if location_match:
        print(f"  📍 Location: {location_match.group(0)}")
    
    # Description preview
    if 'About the job' in content:
        start = content.find('About the job') + len('About the job')
        preview = content[start:start+100].strip()
        print(f"  📄 Description: {preview}...")
    
    print(f"\n💡 Recommendation: {'Use text parser' if not checks['HTML Tags'] else 'Use HTML parser'}")

if __name__ == "__main__":
    quick_analysis()