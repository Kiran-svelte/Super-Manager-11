"""
Behavioral Tests: MCP Client
==============================
Tests that the MCP client ACTUALLY works:
- MCPServerConfig dataclass
- Risk classification patterns
- _classify_mcp_tool_risk function
- MCPClientManager class

README Requirements:
- MCP server integration
- Tool namespacing (mcp__{server}__{tool})
- Risk classification for MCP tools
"""

import pytest

from backend.core.mcp_client import (
    MCPServerConfig,
    SAFE_PATTERNS,
    RISKY_PATTERNS,
    BLOCKED_PATTERNS,
    _classify_mcp_tool_risk,
    MCPClientManager,
    MCP_AVAILABLE,
)


class TestMCPFeatureDetection:
    """Test MCP feature detection"""
    
    def test_mcp_available_is_bool(self):
        """MCP_AVAILABLE should be boolean"""
        assert isinstance(MCP_AVAILABLE, bool)


class TestMCPServerConfig:
    """Test MCPServerConfig dataclass"""
    
    def test_can_create_server_config(self):
        """MCPServerConfig should be creatable"""
        config = MCPServerConfig(
            name="test-server",
            command="node",
            args=["server.js"],
            env={"API_KEY": "secret"}
        )
        assert config is not None
    
    def test_has_name(self):
        """MCPServerConfig should have name"""
        config = MCPServerConfig(
            name="github",
            command="node",
            args=["server.js"],
            env={}
        )
        assert config.name == "github"
    
    def test_has_command(self):
        """MCPServerConfig should have command"""
        config = MCPServerConfig(
            name="test",
            command="python",
            args=["-m", "mcp_server"],
            env={}
        )
        assert config.command == "python"
    
    def test_has_args(self):
        """MCPServerConfig should have args"""
        config = MCPServerConfig(
            name="test",
            command="node",
            args=["--port", "8080"],
            env={}
        )
        assert config.args == ["--port", "8080"]
    
    def test_has_env(self):
        """MCPServerConfig should have env"""
        config = MCPServerConfig(
            name="test",
            command="node",
            args=[],
            env={"TOKEN": "abc123"}
        )
        assert config.env == {"TOKEN": "abc123"}
    
    def test_enabled_default_true(self):
        """MCPServerConfig should have enabled=True by default"""
        config = MCPServerConfig(
            name="test",
            command="node",
            args=[],
            env={}
        )
        assert config.enabled is True
    
    def test_enabled_can_be_false(self):
        """MCPServerConfig.enabled can be set to False"""
        config = MCPServerConfig(
            name="test",
            command="node",
            args=[],
            env={},
            enabled=False
        )
        assert config.enabled is False


class TestRiskPatterns:
    """Test risk classification patterns"""
    
    def test_safe_patterns_is_list(self):
        """SAFE_PATTERNS should be a list"""
        assert isinstance(SAFE_PATTERNS, list)
    
    def test_safe_patterns_not_empty(self):
        """SAFE_PATTERNS should not be empty"""
        assert len(SAFE_PATTERNS) > 0
    
    def test_safe_patterns_all_strings(self):
        """SAFE_PATTERNS should contain strings"""
        assert all(isinstance(p, str) for p in SAFE_PATTERNS)
    
    def test_risky_patterns_is_list(self):
        """RISKY_PATTERNS should be a list"""
        assert isinstance(RISKY_PATTERNS, list)
    
    def test_risky_patterns_not_empty(self):
        """RISKY_PATTERNS should not be empty"""
        assert len(RISKY_PATTERNS) > 0
    
    def test_risky_patterns_all_strings(self):
        """RISKY_PATTERNS should contain strings"""
        assert all(isinstance(p, str) for p in RISKY_PATTERNS)
    
    def test_blocked_patterns_is_list(self):
        """BLOCKED_PATTERNS should be a list"""
        assert isinstance(BLOCKED_PATTERNS, list)
    
    def test_blocked_patterns_not_empty(self):
        """BLOCKED_PATTERNS should not be empty"""
        assert len(BLOCKED_PATTERNS) > 0
    
    def test_blocked_patterns_all_strings(self):
        """BLOCKED_PATTERNS should contain strings"""
        assert all(isinstance(p, str) for p in BLOCKED_PATTERNS)
    
    def test_safe_patterns_contents(self):
        """SAFE_PATTERNS should include read-only operations"""
        expected = ["list", "get", "read", "search"]
        for pattern in expected:
            assert pattern in SAFE_PATTERNS
    
    def test_risky_patterns_contents(self):
        """RISKY_PATTERNS should include write operations"""
        expected = ["create", "update", "delete", "send"]
        for pattern in expected:
            assert pattern in RISKY_PATTERNS
    
    def test_blocked_patterns_contents(self):
        """BLOCKED_PATTERNS should include dangerous operations"""
        expected = ["exec", "execute", "rm", "drop"]
        for pattern in expected:
            assert pattern in BLOCKED_PATTERNS


class TestRiskClassification:
    """Test _classify_mcp_tool_risk function"""
    
    def test_returns_string(self):
        """_classify_mcp_tool_risk should return string"""
        result = _classify_mcp_tool_risk("some_tool")
        assert isinstance(result, str)
    
    def test_valid_return_values(self):
        """_classify_mcp_tool_risk should return valid values"""
        result = _classify_mcp_tool_risk("test")
        assert result in ["safe", "risky", "blocked"]
    
    # Safe pattern tests
    def test_list_is_safe(self):
        """list operations should be safe"""
        result = _classify_mcp_tool_risk("list_repositories")
        assert result == "safe"
    
    def test_get_is_safe(self):
        """get operations should be safe"""
        result = _classify_mcp_tool_risk("get_user")
        assert result == "safe"
    
    def test_read_is_safe(self):
        """read operations should be safe"""
        result = _classify_mcp_tool_risk("read_file")
        assert result == "safe"
    
    def test_search_is_safe(self):
        """search operations should be safe"""
        result = _classify_mcp_tool_risk("search_issues")
        assert result == "safe"
    
    def test_find_is_safe(self):
        """find operations should be safe"""
        result = _classify_mcp_tool_risk("find_users")
        assert result == "safe"
    
    def test_query_is_safe(self):
        """query operations should be safe"""
        result = _classify_mcp_tool_risk("query_database")
        assert result == "safe"
    
    # Risky pattern tests
    def test_create_is_risky(self):
        """create operations should be risky"""
        result = _classify_mcp_tool_risk("create_issue")
        assert result == "risky"
    
    def test_update_is_risky(self):
        """update operations should be risky"""
        result = _classify_mcp_tool_risk("update_record")
        assert result == "risky"
    
    def test_delete_is_risky(self):
        """delete operations should be risky"""
        result = _classify_mcp_tool_risk("delete_comment")
        assert result == "risky"
    
    def test_send_is_risky(self):
        """send operations should be risky"""
        result = _classify_mcp_tool_risk("send_email")
        assert result == "risky"
    
    def test_write_is_risky(self):
        """write operations should be risky"""
        result = _classify_mcp_tool_risk("write_file")
        assert result == "risky"
    
    def test_modify_is_risky(self):
        """modify operations should be risky"""
        result = _classify_mcp_tool_risk("modify_settings")
        assert result == "risky"
    
    # Blocked pattern tests
    def test_exec_is_blocked(self):
        """exec operations should be blocked"""
        result = _classify_mcp_tool_risk("exec_command")
        assert result == "blocked"
    
    def test_execute_is_blocked(self):
        """execute operations should be blocked"""
        result = _classify_mcp_tool_risk("execute_shell")
        assert result == "blocked"
    
    def test_run_is_blocked(self):
        """run operations should be blocked"""
        result = _classify_mcp_tool_risk("run_script")
        assert result == "blocked"
    
    def test_eval_is_blocked(self):
        """eval operations should be blocked"""
        result = _classify_mcp_tool_risk("eval_code")
        assert result == "blocked"
    
    def test_sudo_is_blocked(self):
        """sudo operations should be blocked"""
        result = _classify_mcp_tool_risk("sudo_command")
        assert result == "blocked"
    
    def test_rm_is_blocked(self):
        """rm operations should be blocked"""
        result = _classify_mcp_tool_risk("rm_directory")
        assert result == "blocked"
    
    def test_drop_is_blocked(self):
        """drop operations should be blocked"""
        result = _classify_mcp_tool_risk("drop_table")
        assert result == "blocked"
    
    # Default behavior
    def test_unknown_is_risky(self):
        """unknown operations should default to risky"""
        result = _classify_mcp_tool_risk("some_random_tool")
        assert result == "risky"
    
    # Case insensitivity
    def test_case_insensitive(self):
        """classification should be case insensitive"""
        result1 = _classify_mcp_tool_risk("LIST_ITEMS")
        result2 = _classify_mcp_tool_risk("list_items")
        assert result1 == result2 == "safe"
    
    # Description influence
    def test_description_can_block(self):
        """description can influence blocking"""
        result = _classify_mcp_tool_risk("process_data", "execute the data pipeline")
        assert result == "blocked"


class TestMCPClientManager:
    """Test MCPClientManager class"""
    
    def test_can_instantiate(self):
        """MCPClientManager should be instantiatable"""
        manager = MCPClientManager()
        assert manager is not None
    
    def test_has_servers_dict(self):
        """MCPClientManager should have _servers dict"""
        manager = MCPClientManager()
        assert hasattr(manager, "_servers")
        assert isinstance(manager._servers, dict)
    
    def test_has_sessions_dict(self):
        """MCPClientManager should have _sessions dict"""
        manager = MCPClientManager()
        assert hasattr(manager, "_sessions")
        assert isinstance(manager._sessions, dict)
    
    def test_has_server_tools_dict(self):
        """MCPClientManager should have _server_tools dict"""
        manager = MCPClientManager()
        assert hasattr(manager, "_server_tools")
        assert isinstance(manager._server_tools, dict)
    
    def test_has_initialized_flag(self):
        """MCPClientManager should have _initialized flag"""
        manager = MCPClientManager()
        assert hasattr(manager, "_initialized")
        assert manager._initialized is False
    
    def test_has_load_config_method(self):
        """MCPClientManager should have _load_config method"""
        manager = MCPClientManager()
        assert hasattr(manager, "_load_config")
        assert callable(manager._load_config)
    
    def test_servers_initially_empty(self):
        """_servers should be empty initially"""
        manager = MCPClientManager()
        assert len(manager._servers) == 0
    
    def test_sessions_initially_empty(self):
        """_sessions should be empty initially"""
        manager = MCPClientManager()
        assert len(manager._sessions) == 0


class TestEdgeCases:
    """Test edge cases"""
    
    def test_empty_tool_name(self):
        """Should handle empty tool name"""
        result = _classify_mcp_tool_risk("")
        assert result in ["safe", "risky", "blocked"]
    
    def test_tool_with_multiple_patterns(self):
        """Should prioritize blocked > risky > safe"""
        # Has both "exec" (blocked) and "list" (safe)
        result = _classify_mcp_tool_risk("exec_list_commands")
        assert result == "blocked"
    
    def test_very_long_tool_name(self):
        """Should handle very long tool names"""
        long_name = "get_" + "a" * 1000
        result = _classify_mcp_tool_risk(long_name)
        assert result == "safe"
    
    def test_special_characters(self):
        """Should handle special characters"""
        result = _classify_mcp_tool_risk("get_user-data_v2.0")
        assert result == "safe"


class TestConfigResolution:
    """Test MCPServerConfig resolution"""
    
    def test_empty_args(self):
        """MCPServerConfig should accept empty args"""
        config = MCPServerConfig(
            name="test",
            command="node",
            args=[],
            env={}
        )
        assert config.args == []
    
    def test_empty_env(self):
        """MCPServerConfig should accept empty env"""
        config = MCPServerConfig(
            name="test",
            command="python",
            args=["server.py"],
            env={}
        )
        assert config.env == {}
    
    def test_multiple_args(self):
        """MCPServerConfig should accept multiple args"""
        config = MCPServerConfig(
            name="test",
            command="node",
            args=["--port", "8080", "--host", "localhost"],
            env={}
        )
        assert len(config.args) == 4
    
    def test_multiple_env_vars(self):
        """MCPServerConfig should accept multiple env vars"""
        config = MCPServerConfig(
            name="test",
            command="node",
            args=[],
            env={"API_KEY": "key1", "SECRET": "key2", "TOKEN": "key3"}
        )
        assert len(config.env) == 3
