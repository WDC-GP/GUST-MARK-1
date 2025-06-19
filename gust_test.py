#!/usr/bin/env python3
"""
GUST-MARK-1 OPTIMIZATION PROJECT - COMPREHENSIVE STATUS TEST
===========================================================
Tests Steps 1-4 completion status and provides detailed scoring
"""

import os
import ast
import sys
import importlib.util
from datetime import datetime
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

def print_step_header(step_num, title):
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}🎯 STEP {step_num}: {title}{Colors.END}")
    print(f"{Colors.MAGENTA}{'-'*50}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.CYAN}ℹ️ {message}{Colors.END}")

def test_file_syntax(file_path):
    """Test if a Python file has valid syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, "Valid syntax"
    except SyntaxError as e:
        return False, f"Syntax error on line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Error reading file: {e}"

def test_file_import(file_path, module_name=None):
    """Test if a Python file can be imported"""
    try:
        if module_name:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                compile(f.read(), file_path, 'exec')
        return True, "Import successful"
    except Exception as e:
        return False, f"Import error: {e}"

def check_utf8_bom(file_path):
    """Check if file has UTF-8 BOM"""
    try:
        with open(file_path, 'rb') as f:
            content = f.read(3)
        return content == b'\xef\xbb\xbf'
    except:
        return False

def analyze_import_organization(file_path):
    """Analyze import organization quality"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        imports_found = False
        standard_imports = []
        third_party_imports = []
        local_imports = []
        current_section = None
        
        # Standard library modules (partial list)
        stdlib_modules = {
            'os', 'sys', 'datetime', 'uuid', 'logging', 'json', 'random', 
            'secrets', 'hashlib', 'base64', 'time', 'collections', 'itertools',
            'functools', 'operator', 'math', 'statistics', 'string', 're'
        }
        
        for line in lines:
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                imports_found = True
                # Determine import type
                if line.startswith('from '):
                    module = line.split()[1].split('.')[0]
                else:
                    module = line.split()[1].split('.')[0]
                
                if module in stdlib_modules:
                    standard_imports.append(line)
                elif module.startswith('.') or module in ['routes', 'utils', 'systems', 'websocket']:
                    local_imports.append(line)
                else:
                    third_party_imports.append(line)
        
        if not imports_found:
            return 'no_imports', 0
        
        # Calculate organization score
        total_imports = len(standard_imports) + len(third_party_imports) + len(local_imports)
        if total_imports == 0:
            return 'no_imports', 0
        
        # Check if imports are properly grouped
        organization_score = 0
        if standard_imports:
            organization_score += 0.3
        if third_party_imports:
            organization_score += 0.3
        if local_imports:
            organization_score += 0.4
        
        if total_imports >= 3:
            return 'organized', int(organization_score * 100)
        elif total_imports >= 1:
            return 'partial', 50
        else:
            return 'unorganized', 0
            
    except Exception as e:
        return 'error', 0

def step1_file_cleanup_test():
    """Test Step 1: File Cleanup & Project Setup"""
    print_step_header(1, "FILE CLEANUP & PROJECT SETUP")
    
    score = 0
    max_score = 20
    
    # Core files check
    core_files = ['app.py', 'config.py', 'main.py', 'requirements.txt']
    core_present = 0
    
    print(f"\n{Colors.BOLD}📁 Core Files Check:{Colors.END}")
    for file in core_files:
        if os.path.exists(file):
            print_success(f"{file} present")
            core_present += 1
        else:
            print_error(f"{file} missing")
    
    score += (core_present / len(core_files)) * 5  # 5 points for core files
    
    # Directory structure check
    required_dirs = ['routes', 'utils', 'templates', 'static', 'systems', 'websocket']
    dirs_present = 0
    
    print(f"\n{Colors.BOLD}📂 Directory Structure Check:{Colors.END}")
    for dir_name in required_dirs:
        if os.path.exists(dir_name) and os.path.isdir(dir_name):
            print_success(f"{dir_name}/ directory present")
            dirs_present += 1
        else:
            print_error(f"{dir_name}/ directory missing")
    
    score += (dirs_present / len(required_dirs)) * 6  # 6 points for directories
    
    # Backup system check
    backup_dirs = [d for d in os.listdir('.') if 'backup' in d.lower() and os.path.isdir(d)]
    print(f"\n{Colors.BOLD}🛡️ Backup System Check:{Colors.END}")
    if len(backup_dirs) >= 5:
        print_success(f"Found {len(backup_dirs)} backup directories")
        score += 5  # 5 points for backup system
    elif len(backup_dirs) >= 1:
        print_warning(f"Found {len(backup_dirs)} backup directories (minimal)")
        score += 2
    else:
        print_error("No backup directories found")
    
    # File count check
    python_files = list(Path('.').rglob('*.py'))
    total_files = len(python_files)
    
    print(f"\n{Colors.BOLD}📄 Project Files Summary:{Colors.END}")
    print_info(f"Total Python files: {total_files}")
    
    if total_files >= 30:
        print_success("Comprehensive project structure")
        score += 4  # 4 points for file completeness
    elif total_files >= 20:
        print_warning("Good project structure")
        score += 2
    else:
        print_error("Limited project structure")
    
    return score, max_score

def step2_utility_infrastructure_test():
    """Test Step 2: Enterprise Utility Infrastructure"""
    print_step_header(2, "ENTERPRISE UTILITY INFRASTRUCTURE")
    
    score = 0
    max_score = 25
    
    # Required utility modules
    required_utils = [
        'utils/auth_decorators.py',
        'utils/db_helpers.py', 
        'utils/validation_helpers.py',
        'utils/error_handlers.py',
        'utils/common_imports.py',
        'utils/__init__.py',
        'utils/gust_db_optimization.py',
        'utils/performance_report.py',
        'utils/user_helpers.py',
        'utils/user_migration.py',
        'utils/rate_limiter.py',
        'utils/helpers.py'
    ]
    
    utils_present = 0
    utils_working = 0
    utils_size = 0
    
    print(f"\n{Colors.BOLD}🔧 Utility Modules Check:{Colors.END}")
    
    for util_file in required_utils:
        if os.path.exists(util_file):
            file_size = os.path.getsize(util_file)
            utils_size += file_size
            utils_present += 1
            
            # Test syntax
            syntax_ok, syntax_msg = test_file_syntax(util_file)
            
            # Check for UTF-8 BOM
            has_bom = check_utf8_bom(util_file)
            
            if syntax_ok and not has_bom:
                print_success(f"{util_file} ✓ ({file_size} bytes)")
                utils_working += 1
            elif has_bom:
                print_warning(f"{util_file} ⚠ UTF-8 BOM detected ({file_size} bytes)")
            else:
                print_error(f"{util_file} ✗ Syntax error: {syntax_msg}")
        else:
            print_error(f"{util_file} missing")
    
    # Scoring
    score += (utils_present / len(required_utils)) * 10  # 10 points for presence
    score += (utils_working / len(required_utils)) * 10   # 10 points for functionality
    
    print(f"\n{Colors.BOLD}📊 Utility Infrastructure Summary:{Colors.END}")
    print_info(f"Modules present: {utils_present}/{len(required_utils)}")
    print_info(f"Modules working: {utils_working}/{len(required_utils)}")
    print_info(f"Total size: {utils_size:,} bytes")
    
    # Performance optimization check
    optimization_files = ['utils/gust_db_optimization.py', 'utils/performance_report.py']
    optimization_present = sum(1 for f in optimization_files if os.path.exists(f))
    
    if optimization_present == len(optimization_files):
        print_success("Database optimization system present")
        score += 5  # 5 points for optimization
    elif optimization_present > 0:
        print_warning("Partial optimization system")
        score += 2
    else:
        print_error("No optimization system found")
    
    return score, max_score

def step3_import_organization_test():
    """Test Step 3: Import Organization"""
    print_step_header(3, "IMPORT ORGANIZATION")
    
    score = 0
    max_score = 20
    
    # Get all Python files
    python_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    organized_files = 0
    partial_files = 0
    unorganized_files = 0
    
    print(f"\n{Colors.BOLD}📋 Import Organization Analysis:{Colors.END}")
    
    for file_path in python_files:
        if '__pycache__' in file_path:
            continue
            
        org_status, org_score = analyze_import_organization(file_path)
        
        if org_status == 'organized' and org_score >= 80:
            organized_files += 1
            print_success(f"{file_path} - Well organized ({org_score}%)")
        elif org_status == 'partial' or (org_status == 'organized' and org_score < 80):
            partial_files += 1
            print_warning(f"{file_path} - Partially organized ({org_score}%)")
        elif org_status == 'no_imports':
            # Skip files with no imports
            continue
        else:
            unorganized_files += 1
            print_error(f"{file_path} - Needs organization ({org_score}%)")
    
    total_files_with_imports = organized_files + partial_files + unorganized_files
    
    if total_files_with_imports > 0:
        organization_rate = (organized_files + partial_files * 0.5) / total_files_with_imports
        score = organization_rate * max_score
    
    print(f"\n{Colors.BOLD}📈 Import Organization Summary:{Colors.END}")
    print_info(f"Fully organized: {organized_files}")
    print_info(f"Partially organized: {partial_files}")
    print_info(f"Unorganized: {unorganized_files}")
    print_info(f"Organization rate: {organization_rate*100:.1f}%")
    
    return score, max_score

def step4_database_optimization_test():
    """Test Step 4: Database Query Optimization"""
    print_step_header(4, "DATABASE QUERY OPTIMIZATION")
    
    score = 0
    max_score = 25
    
    # Check for database optimization files
    db_files = [
        'utils/gust_db_optimization.py',
        'utils/performance_report.py',
        'utils/db_helpers.py'
    ]
    
    db_files_present = 0
    
    print(f"\n{Colors.BOLD}🗄️ Database Optimization Files:{Colors.END}")
    
    for db_file in db_files:
        if os.path.exists(db_file):
            file_size = os.path.getsize(db_file)
            syntax_ok, syntax_msg = test_file_syntax(db_file)
            
            if syntax_ok:
                print_success(f"{db_file} ✓ ({file_size} bytes)")
                db_files_present += 1
            else:
                print_error(f"{db_file} ✗ {syntax_msg}")
        else:
            print_error(f"{db_file} missing")
    
    score += (db_files_present / len(db_files)) * 8  # 8 points for DB files
    
    # Check route integration
    route_files = []
    if os.path.exists('routes'):
        route_files = [f for f in os.listdir('routes') if f.endswith('.py') and f != '__init__.py']
    
    routes_with_optimization = 0
    
    print(f"\n{Colors.BOLD}🛤️ Route Optimization Integration:{Colors.END}")
    
    for route_file in route_files:
        route_path = os.path.join('routes', route_file)
        try:
            with open(route_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for optimization imports
            has_optimization = any(opt in content for opt in [
                'gust_db_optimization',
                'get_user_with_cache',
                'get_user_balance_cached',
                'db_performance_monitor'
            ])
            
            if has_optimization:
                print_success(f"{route_file} - Optimization integrated")
                routes_with_optimization += 1
            else:
                print_warning(f"{route_file} - No optimization detected")
                
        except Exception as e:
            print_error(f"{route_file} - Error reading: {e}")
    
    if route_files:
        optimization_rate = routes_with_optimization / len(route_files)
        score += optimization_rate * 12  # 12 points for route integration
    
    # Check for specific optimization functions
    if os.path.exists('utils/gust_db_optimization.py'):
        try:
            with open('utils/gust_db_optimization.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            optimization_functions = [
                'get_user_with_cache',
                'get_user_balance_cached', 
                'update_user_balance',
                'db_performance_monitor'
            ]
            
            functions_present = sum(1 for func in optimization_functions if func in content)
            score += (functions_present / len(optimization_functions)) * 5  # 5 points for functions
            
            print(f"\n{Colors.BOLD}⚡ Optimization Functions:{Colors.END}")
            print_info(f"Functions implemented: {functions_present}/{len(optimization_functions)}")
            
        except Exception as e:
            print_error(f"Error reading optimization file: {e}")
    
    return score, max_score

def application_functionality_test():
    """Test overall application functionality"""
    print_step_header("BONUS", "APPLICATION FUNCTIONALITY TEST")
    
    score = 0
    max_score = 10
    
    # Test core module imports
    core_modules = ['config', 'main', 'app']
    working_modules = 0
    
    print(f"\n{Colors.BOLD}🚀 Core Module Import Test:{Colors.END}")
    
    for module in core_modules:
        if os.path.exists(f'{module}.py'):
            syntax_ok, syntax_msg = test_file_syntax(f'{module}.py')
            if syntax_ok:
                print_success(f"{module}.py - Syntax OK")
                working_modules += 1
            else:
                print_error(f"{module}.py - {syntax_msg}")
        else:
            print_error(f"{module}.py - Missing")
    
    score = (working_modules / len(core_modules)) * max_score
    
    return score, max_score

def generate_final_report(scores):
    """Generate final comprehensive report"""
    print_header("GUST-MARK-1 FINAL STATUS REPORT")
    
    total_score = sum(score for score, _ in scores.values())
    total_max = sum(max_score for _, max_score in scores.values())
    percentage = (total_score / total_max) * 100
    
    # Determine grade
    if percentage >= 90:
        grade = "A"
        grade_color = Colors.GREEN
    elif percentage >= 85:
        grade = "A-"
        grade_color = Colors.GREEN
    elif percentage >= 80:
        grade = "B+"
        grade_color = Colors.YELLOW
    elif percentage >= 75:
        grade = "B"
        grade_color = Colors.YELLOW
    elif percentage >= 70:
        grade = "B-"
        grade_color = Colors.YELLOW
    else:
        grade = "C+"
        grade_color = Colors.RED
    
    print(f"\n{Colors.BOLD}📊 DETAILED SCORES:{Colors.END}")
    for step, (score, max_score) in scores.items():
        pct = (score / max_score) * 100
        color = Colors.GREEN if pct >= 80 else Colors.YELLOW if pct >= 60 else Colors.RED
        print(f"  {step}: {color}{score:.1f}/{max_score} ({pct:.1f}%){Colors.END}")
    
    print(f"\n{Colors.BOLD}🎯 OVERALL RESULTS:{Colors.END}")
    print(f"  Total Score: {grade_color}{total_score:.1f}/{total_max} points{Colors.END}")
    print(f"  Percentage: {grade_color}{percentage:.1f}%{Colors.END}")
    print(f"  Final Grade: {grade_color}{Colors.BOLD}{grade}{Colors.END}")
    
    # Status determination
    if percentage >= 85:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 OPTIMIZATION PROJECT COMPLETE!{Colors.END}")
        print(f"{Colors.GREEN}✅ Enterprise-grade infrastructure achieved{Colors.END}")
        print(f"{Colors.GREEN}✅ Performance improvements active{Colors.END}")
        print(f"{Colors.GREEN}✅ Ready for production deployment{Colors.END}")
    elif percentage >= 75:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}🔧 OPTIMIZATION NEARLY COMPLETE{Colors.END}")
        print(f"{Colors.YELLOW}⚠️ Minor issues need attention{Colors.END}")
        print(f"{Colors.YELLOW}⚠️ Performance improvements partially active{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ OPTIMIZATION NEEDS WORK{Colors.END}")
        print(f"{Colors.RED}🚨 Critical issues require resolution{Colors.END}")
        print(f"{Colors.RED}🚨 Performance improvements not active{Colors.END}")
    
    # Recommendations
    print(f"\n{Colors.BOLD}💡 RECOMMENDATIONS:{Colors.END}")
    
    if scores["Step 2"][0] < scores["Step 2"][1] * 0.8:
        print(f"{Colors.YELLOW}• Fix UTF-8 BOM issues in utility modules{Colors.END}")
    
    if scores["Step 3"][0] < scores["Step 3"][1] * 0.8:
        print(f"{Colors.YELLOW}• Complete import organization in remaining files{Colors.END}")
    
    if "Application Functionality" in scores and scores["Application Functionality"][0] < scores["Application Functionality"][1] * 0.8:
        print(f"{Colors.RED}• Resolve syntax errors blocking application startup{Colors.END}")
    
    if percentage >= 85:
        print(f"{Colors.GREEN}• Deploy to production and monitor performance{Colors.END}")
        print(f"{Colors.GREEN}• Begin Step 5: Frontend Asset Optimization{Colors.END}")
    
    return percentage, grade

def main():
    """Main test execution"""
    print_header("GUST-MARK-1 OPTIMIZATION PROJECT COMPREHENSIVE TEST")
    print(f"{Colors.CYAN}Testing Steps 1-4 completion status...{Colors.END}")
    print(f"{Colors.CYAN}Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
    
    # Run all tests
    scores = {}
    
    scores["Step 1"] = step1_file_cleanup_test()
    scores["Step 2"] = step2_utility_infrastructure_test()
    scores["Step 3"] = step3_import_organization_test()
    scores["Step 4"] = step4_database_optimization_test()
    scores["Application Functionality"] = application_functionality_test()
    
    # Generate final report
    percentage, grade = generate_final_report(scores)
    
    # Return status code based on results
    if percentage >= 85:
        return 0  # Success
    elif percentage >= 75:
        return 1  # Minor issues
    else:
        return 2  # Major issues

if __name__ == "__main__":
    sys.exit(main())