#!/usr/bin/env python3.11
"""
Script de validação completa do projeto.
Verifica sintaxe, estrutura de arquivos, imports e testes.
"""
import ast
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# --- Configuração ---
# Tenta detectar a raiz do projeto procurando pela pasta 'backend'
current_path = Path(".").resolve()
if (current_path / "backend").exists():
    PROJECT_ROOT = current_path
elif (current_path.parent / "backend").exists():
    PROJECT_ROOT = current_path.parent
else:
    PROJECT_ROOT = Path(".")

BACKEND_DIR = PROJECT_ROOT / "backend"
SRC_DIR = BACKEND_DIR / "src"
TESTS_DIR = BACKEND_DIR / "tests"

REQUIRED_FILES = [
    "README.md",
    ".env",
    "backend/requirements.txt",
    "backend/src/main.py",
    "backend/pytest.ini",
    "backend/tests/conftest.py",
    "frontend/package.json",
    "docker/docker-compose.yml",
    ".gitignore",
]

TEST_SUBDIRS = [
    "unit",
    "integration",
    "e2e",
]

def print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(f"{title}")
    print("=" * 80)

def check_python_syntax() -> bool:
    """Verifica sintaxe de todos os arquivos Python."""
    print_header("1. VERIFICANDO SINTAXE PYTHON")
    
    errors = []
    checked_count = 0
    
    # Encontra todos os arquivos .py, ignorando venv e cache
    for py_file in SRC_DIR.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                ast.parse(f.read(), filename=str(py_file))
            checked_count += 1
        except SyntaxError as e:
            errors.append(f"{py_file}: {e}")
        except Exception as e:
            errors.append(f"{py_file}: Erro ao ler arquivo - {e}")
    
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
    """Tenta resolver o caminho de um módulo importado."""
    if not module_name.startswith("src."):
        return None
        
    module_path = module_name.replace("src.", "").replace(".", "/")
    
    # Tenta como arquivo .py
    file_path = SRC_DIR / f"{module_path}.py"
    if file_path.exists():
        return file_path
        
    # Tenta como diretório (pacote)
    dir_path = SRC_DIR / module_path
    if dir_path.exists():
        return dir_path
        
    return None

def check_imports() -> bool:
    """Verifica se imports internos (src.*) apontam para arquivos existentes."""
    print_header("3. VERIFICANDO IMPORTS")
    
    problematic = []
    
    for py_file in SRC_DIR.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
            
        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith("src."):
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
    """Verifica existência de arquivos na pasta docker."""
    print_header("4. VERIFICANDO ARQUIVOS DOCKER")
    
    docker_dir = PROJECT_ROOT / "docker"
    if not docker_dir.exists():
        print("✗ Diretório 'docker' não encontrado")
        return False
        
    docker_files = list(docker_dir.glob("*"))
    print(f"✓ Arquivos Docker encontrados: {len(docker_files)}")
    for df in docker_files:
        print(f"  - {df.name}")
    
    return len(docker_files) > 0

def check_tests() -> bool:
    """Verifica estrutura e existência de testes."""
    print_header("5. VERIFICANDO TESTES")
    
    total_tests = 0
    
    for subdir in TEST_SUBDIRS:
        dir_path = TESTS_DIR / subdir
        if dir_path.exists():
            tests = list(dir_path.rglob("test_*.py"))
            count = len(tests)
            total_tests += count
            print(f"✓ {subdir}: {count} arquivos de teste")
        else:
            print(f"⚠️  {subdir}: Diretório não encontrado")
    
    print(f"\n✓ Total de arquivos de teste: {total_tests}")
    return total_tests > 0

def main() -> int:
    print("\n" + "="*80)
    print("VALIDAÇÃO COMPLETA DO PROJETO - AGENTE LLM AUTÔNOMO")
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
