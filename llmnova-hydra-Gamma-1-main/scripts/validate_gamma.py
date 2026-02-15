#!/usr/bin/env python3
"""
Script de validação adaptado para o Gamma Engine (fka NovaLLM/Hydra).
Verifica sintaxe, estrutura de arquivos, imports e testes.
"""
import ast
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# --- Configuração ---
# Tenta detectar a raiz do projeto procurando por 'gamma_server.py'
current_path = Path(".").resolve()
if (current_path / "gamma_server.py").exists():
    PROJECT_ROOT = current_path
elif (current_path.parent / "gamma_server.py").exists():
    PROJECT_ROOT = current_path.parent
else:
    # Fallback to current dir
    PROJECT_ROOT = Path(".")

# Diretórios principais do Gamma
GAMMA_ENGINE_DIR = PROJECT_ROOT / "gamma_engine"
BACKEND_DIR = PROJECT_ROOT / "backend" # Pode ser redundante com gamma_server.py na raiz, mas mantemos verificação
FRONTEND_DIR = PROJECT_ROOT / "gamma-frontend"
TESTS_DIR = PROJECT_ROOT / "tests"

REQUIRED_FILES = [
    "README.md",
    "requirements.txt",
    "gamma_server.py",
    "gamma_engine/__init__.py",
    "gamma-frontend/package.json",
    "docker-compose.yml",
    ".gitignore",
]

# Gamma seems to use a flat test structure or specific files
TEST_FILES_PATTERN = "test_*.py"

def print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(f"{title}")
    print("=" * 80)

def check_python_syntax() -> bool:
    """Verifica sintaxe de todos os arquivos Python no gamma_engine e raiz."""
    print_header("1. VERIFICANDO SINTAXE PYTHON")
    
    errors = []
    checked_count = 0
    
    # Lista de diretórios/arquivos para verificar
    paths_to_check = [GAMMA_ENGINE_DIR, PROJECT_ROOT]

    for path in paths_to_check:
        if path.is_file() and path.suffix == ".py":
             files = [path]
        elif path.is_dir():
             files = path.rglob("*.py")
        else:
            continue

        for py_file in files:
            if "__pycache__" in str(py_file) or "venv" in str(py_file) or ".git" in str(py_file):
                continue

            # Avoid checking legacy folder itself if running from root
            if "llmnova-core" in str(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    ast.parse(f.read(), filename=str(py_file))
                checked_count += 1
            except SyntaxError as e:
                errors.append(f"{py_file}: {e}")
            except Exception as e:
                # errors.append(f"{py_file}: Erro ao ler arquivo - {e}")
                pass # Ignore read errors (e.g. encoding issues on non-utf8 files)
    
    print(f"✓ Arquivos verificados: {checked_count}")
    
    if errors:
        print(f"✗ Erros encontrados: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("✓ Nenhum erro de sintaxe encontrado")
    return True

def check_file_structure() -> bool:
    """Verifica presença de arquivos essenciais."""
    print_header("2. VERIFICANDO ESTRUTURA DE ARQUIVOS")
    
    missing = []
    for file_path in REQUIRED_FILES:
        path = PROJECT_ROOT / file_path
        if not path.exists():
            # Check alternatives (e.g. docker-compose.prod.yml)
            if "docker-compose.yml" in file_path and (PROJECT_ROOT / "docker-compose.prod.yml").exists():
                 print(f"✓ {file_path} (found variant docker-compose.prod.yml)")
                 continue
            missing.append(file_path)
        else:
            print(f"✓ {file_path}")
    
    if missing:
        print(f"\n✗ Arquivos faltando: {len(missing)}")
        for file_path in missing:
            print(f"  - {file_path}")
        return False
    
    print("\n✓ Todos os arquivos essenciais presentes")
    return True

def resolve_import_path(module_name: str) -> Optional[Path]:
    """Tenta resolver o caminho de um módulo importado (gamma_engine.*)."""
    if not module_name.startswith("gamma_engine."):
        return None
        
    module_path = module_name.replace("gamma_engine.", "").replace(".", "/")
    
    # Tenta como arquivo .py dentro de gamma_engine
    file_path = GAMMA_ENGINE_DIR / f"{module_path}.py"
    if file_path.exists():
        return file_path
        
    # Tenta como diretório (pacote)
    dir_path = GAMMA_ENGINE_DIR / module_path
    if dir_path.exists():
        return dir_path
        
    return None

def check_imports() -> bool:
    """Verifica se imports internos (gamma_engine.*) apontam para arquivos existentes."""
    print_header("3. VERIFICANDO IMPORTS")
    
    problematic = []
    
    for py_file in GAMMA_ENGINE_DIR.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
            
        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith("gamma_engine."):
                        if not resolve_import_path(node.module):
                            problematic.append(
                                f"{py_file}: Import '{node.module}' não encontrado"
                            )
        except (SyntaxError, UnicodeDecodeError) as e:
             problematic.append(f"{py_file}: Falha ao analisar: {e}")
    
    if problematic:
        print(f"✗ Imports problemáticos: {len(problematic)}")
        for prob in problematic[:10]:
            print(f"  - {prob}")
        if len(problematic) > 10:
            print(f"  ... e mais {len(problematic) - 10} erros.")
        return False
        
    print("✓ Nenhum import problemático encontrado")
    return True

def check_docker_files() -> bool:
    """Verifica existência de arquivos Docker."""
    print_header("4. VERIFICANDO ARQUIVOS DOCKER")
    
    docker_files = list(PROJECT_ROOT.glob("Dockerfile*"))

    if not docker_files:
         print("✗ Nenhum Dockerfile encontrado na raiz")
         return False

    print(f"✓ Arquivos Docker encontrados: {len(docker_files)}")
    for df in docker_files:
        print(f"  - {df.name}")
    
    return True

def check_tests() -> bool:
    """Verifica estrutura e existência de testes."""
    print_header("5. VERIFICANDO TESTES")
    
    total_tests = 0
    
    # Check root tests and tests/ directory
    test_locations = [PROJECT_ROOT, TESTS_DIR]

    for loc in test_locations:
        if loc.exists():
             tests = list(loc.rglob("test_*.py"))
             count = len(tests)
             total_tests += count
             if count > 0:
                 print(f"✓ {loc.name}: {count} arquivos de teste")
    
    print(f"\n✓ Total de arquivos de teste: {total_tests}")
    return total_tests > 0

def main() -> int:
    print("\n" + "="*80)
    print("VALIDAÇÃO COMPLETA DO PROJETO GAMMA - BASEADO EM LEGADO HYDRA")
    print("="*80 + "\n")
    
    checks = [
        ("Sintaxe Python", check_python_syntax),
        ("Estrutura de Arquivos", check_file_structure),
        ("Imports", check_imports),
        ("Docker", check_docker_files),
        ("Testes", check_tests),
    ]
    
    results = []
    for name, func in checks:
        try:
            passed = func()
            results.append((name, passed))
        except Exception as e:
            print(f"✗ Erro fatal ao executar verificação '{name}': {e}")
            results.append((name, False))
    
    print_header("RESUMO DA VALIDAÇÃO")
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASSOU" if passed else "✗ FALHOU"
        print(f"{name:30} {status}")
        if not passed:
            all_passed = False
    
    print("="*80)
    if all_passed:
        print("✓ PROJETO VALIDADO COM SUCESSO!")
        return 0
    else:
        print("✗ PROJETO TEM PROBLEMAS QUE PRECISAM SER CORRIGIDOS")
        return 1

if __name__ == "__main__":
    sys.exit(main())
