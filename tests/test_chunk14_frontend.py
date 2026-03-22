"""
Chunk 14: Frontend Core Tests
==============================

Tests for README requirements:
- React 18+ frontend
- Vite build system
- Core components exist
- Streaming chat hooks
"""

import pytest
import os
import json


# Frontend project root
FRONTEND_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")


# =============================================================================
# Frontend Structure Tests
# =============================================================================

class TestFrontendStructure:
    """Test frontend project structure"""
    
    def test_frontend_directory_exists(self):
        """Frontend directory should exist"""
        assert os.path.isdir(FRONTEND_ROOT)
    
    def test_package_json_exists(self):
        """package.json should exist"""
        package_json = os.path.join(FRONTEND_ROOT, "package.json")
        assert os.path.isfile(package_json)
    
    def test_vite_config_exists(self):
        """vite.config.js should exist"""
        vite_config = os.path.join(FRONTEND_ROOT, "vite.config.js")
        assert os.path.isfile(vite_config)
    
    def test_index_html_exists(self):
        """index.html should exist"""
        index_html = os.path.join(FRONTEND_ROOT, "index.html")
        assert os.path.isfile(index_html)


# =============================================================================
# Package.json Tests
# =============================================================================

class TestPackageJson:
    """Test package.json configuration"""
    
    def test_package_json_valid_json(self):
        """package.json should be valid JSON"""
        package_json = os.path.join(FRONTEND_ROOT, "package.json")
        
        with open(package_json, "r") as f:
            data = json.load(f)
        
        assert "name" in data or "dependencies" in data
    
    def test_has_react_dependency(self):
        """package.json should have React dependency"""
        package_json = os.path.join(FRONTEND_ROOT, "package.json")
        
        with open(package_json, "r") as f:
            data = json.load(f)
        
        deps = data.get("dependencies", {})
        dev_deps = data.get("devDependencies", {})
        
        assert "react" in deps or "react" in dev_deps
    
    def test_has_vite_dependency(self):
        """package.json should have Vite dependency"""
        package_json = os.path.join(FRONTEND_ROOT, "package.json")
        
        with open(package_json, "r") as f:
            data = json.load(f)
        
        deps = data.get("dependencies", {})
        dev_deps = data.get("devDependencies", {})
        
        assert "vite" in deps or "vite" in dev_deps


# =============================================================================
# Source Directory Tests
# =============================================================================

class TestSourceDirectory:
    """Test source directory structure"""
    
    def test_src_directory_exists(self):
        """src directory should exist"""
        src_dir = os.path.join(FRONTEND_ROOT, "src")
        assert os.path.isdir(src_dir)
    
    def test_main_jsx_exists(self):
        """main.jsx should exist"""
        main_jsx = os.path.join(FRONTEND_ROOT, "src", "main.jsx")
        assert os.path.isfile(main_jsx)
    
    def test_app_jsx_exists(self):
        """App.jsx should exist"""
        app_jsx = os.path.join(FRONTEND_ROOT, "src", "App.jsx")
        assert os.path.isfile(app_jsx)


# =============================================================================
# Components Directory Tests
# =============================================================================

class TestComponentsDirectory:
    """Test components directory"""
    
    def test_components_directory_exists(self):
        """components directory should exist"""
        components_dir = os.path.join(FRONTEND_ROOT, "src", "components")
        assert os.path.isdir(components_dir)
    
    def test_interactive_ui_component_exists(self):
        """InteractiveUI component should exist"""
        component = os.path.join(FRONTEND_ROOT, "src", "components", "InteractiveUI.jsx")
        assert os.path.isfile(component)
    
    def test_task_panel_component_exists(self):
        """TaskPanel component should exist"""
        component = os.path.join(FRONTEND_ROOT, "src", "components", "TaskPanel.jsx")
        assert os.path.isfile(component)
    
    def test_ai_settings_component_exists(self):
        """AISettings component should exist"""
        component = os.path.join(FRONTEND_ROOT, "src", "components", "AISettings.jsx")
        assert os.path.isfile(component)
    
    def test_human_fallback_component_exists(self):
        """HumanFallback component should exist"""
        component = os.path.join(FRONTEND_ROOT, "src", "components", "HumanFallback.jsx")
        assert os.path.isfile(component)
    
    def test_teaching_mode_component_exists(self):
        """TeachingMode component should exist"""
        component = os.path.join(FRONTEND_ROOT, "src", "components", "TeachingMode.jsx")
        assert os.path.isfile(component)
    
    def test_secure_input_component_exists(self):
        """SecureInput component should exist"""
        component = os.path.join(FRONTEND_ROOT, "src", "components", "SecureInput.jsx")
        assert os.path.isfile(component)
    
    def test_modal_component_exists(self):
        """Modal component should exist"""
        component = os.path.join(FRONTEND_ROOT, "src", "components", "Modal.jsx")
        assert os.path.isfile(component)
    
    def test_toast_component_exists(self):
        """Toast component should exist"""
        component = os.path.join(FRONTEND_ROOT, "src", "components", "Toast.jsx")
        assert os.path.isfile(component)


# =============================================================================
# Hooks Tests
# =============================================================================

class TestHooks:
    """Test custom hooks"""
    
    def test_hooks_directory_exists(self):
        """hooks directory should exist"""
        hooks_dir = os.path.join(FRONTEND_ROOT, "src", "hooks")
        assert os.path.isdir(hooks_dir)
    
    def test_streaming_chat_hook_exists(self):
        """useStreamingChat hook should exist"""
        hook = os.path.join(FRONTEND_ROOT, "src", "useStreamingChat.js")
        assert os.path.isfile(hook)


# =============================================================================
# CSS/Styles Tests
# =============================================================================

class TestStyles:
    """Test styling files"""
    
    def test_app_css_exists(self):
        """App.css should exist"""
        css = os.path.join(FRONTEND_ROOT, "src", "App.css")
        assert os.path.isfile(css)
    
    def test_index_css_exists(self):
        """index.css should exist"""
        css = os.path.join(FRONTEND_ROOT, "src", "index.css")
        assert os.path.isfile(css)
    
    def test_streaming_chat_css_exists(self):
        """StreamingChat.css should exist"""
        css = os.path.join(FRONTEND_ROOT, "src", "StreamingChat.css")
        assert os.path.isfile(css)


# =============================================================================
# Utils Tests
# =============================================================================

class TestUtils:
    """Test utils directory"""
    
    def test_utils_directory_exists(self):
        """utils directory should exist"""
        utils_dir = os.path.join(FRONTEND_ROOT, "src", "utils")
        assert os.path.isdir(utils_dir)


# =============================================================================
# Index HTML Tests
# =============================================================================

class TestIndexHtml:
    """Test index.html content"""
    
    def test_index_html_has_root_div(self):
        """index.html should have root div"""
        index_html = os.path.join(FRONTEND_ROOT, "index.html")
        
        with open(index_html, "r", encoding="utf-8") as f:
            content = f.read()
        
        assert 'id="root"' in content
    
    def test_index_html_references_main(self):
        """index.html should reference main.jsx"""
        index_html = os.path.join(FRONTEND_ROOT, "index.html")
        
        with open(index_html, "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "main.jsx" in content or "/src/main" in content
