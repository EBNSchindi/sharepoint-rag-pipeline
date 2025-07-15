#!/usr/bin/env python3
"""
Patch für orchestrator.py um AutoGen-Probleme zu beheben
"""
import os
import sys

def apply_orchestrator_fix():
    """Wendet den AutoGen-Fix auf orchestrator.py an"""
    orchestrator_file = "/app/src/pipeline/orchestrator.py"
    
    if not os.path.exists(orchestrator_file):
        print(f"Orchestrator file not found: {orchestrator_file}")
        return False
    
    # Backup erstellen
    backup_file = orchestrator_file + ".backup"
    if not os.path.exists(backup_file):
        os.system(f"cp {orchestrator_file} {backup_file}")
    
    # Patch anwenden
    with open(orchestrator_file, 'r') as f:
        content = f.read()
    
    # Fix 1: ContextEnricherAgent None-Check
    if 'ContextEnricherAgent = None' not in content:
        content = content.replace(
            'ChunkCreatorAgent = None',
            'ContextEnricherAgent = None\n    MetadataExtractorAgent = None\n    ChunkCreatorAgent = None'
        )
    
    # Fix 2: AutoGen user_proxy None-Check
    if 'self.user_proxy = None' not in content:
        content = content.replace(
            '# AutoGen configuration',
            '# AutoGen configuration\n        self.user_proxy = None\n        if autogen:'
        )
    
    # Fix 3: GroupChat None-Check
    if 'self.groupchat = None' not in content:
        content = content.replace(
            '# Create agent group if we have AutoGen agents',
            '# Create agent group if we have AutoGen agents\n        self.groupchat = None\n        self.manager = None\n        \n        if self.agents and autogen:'
        )
    
    # Schreibe gepatchte Datei
    with open(orchestrator_file, 'w') as f:
        f.write(content)
    
    print("Orchestrator patch applied successfully")
    return True

if __name__ == "__main__":
    success = apply_orchestrator_fix()
    sys.exit(0 if success else 1)