"""Core Orchestration Engine for TTULA.

Pure Python engine coordinating adapters, execution manager, and data pipelines.
Contains zero Streamlit dependencies so it can run headless or in testing.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import logging

from ttula.core.models import (
    Command,
    ExecutionNode,
    Operation,
    Target,
    TerminalSession,
    ToolResult,
    URLCollection,
)
from ttula.core.operations import OperationRegistry, fill_command_placeholders

logger = logging.getLogger("ttula.core.engine")


class TTULAEngine:
    """Central orchestration engine for TTULA."""

    def __init__(
        self,
        tailscale_adapter: Any = None,
        arsenal_adapter: Any = None,
        tookie_adapter: Any = None,
        uro_adapter: Any = None,
        legba_adapter: Any = None,
        crawler_adapter: Any = None,
        execution_manager: Any = None,
    ):
        self.tailscale = tailscale_adapter
        self.arsenal = arsenal_adapter
        self.tookie = tookie_adapter
        self.uro = uro_adapter
        self.legba = legba_adapter
        self.crawler = crawler_adapter
        self.execution_manager = execution_manager


        self.operations = OperationRegistry()
        self._targets: Dict[str, Target] = {}
        self._execution_nodes: Dict[str, ExecutionNode] = {}
        self._last_url_collection: Optional[URLCollection] = None

    # Target & Node Management
    def register_target(self, target: Target) -> None:
        """Register or update a network target."""
        self._targets[target.name] = target

    def get_target(self, name: str) -> Optional[Target]:
        return self._targets.get(name)

    def list_targets(self) -> List[Target]:
        if self.tailscale:
            # Sync with live tailscale devices if available
            try:
                live_targets = self.tailscale.get_targets()
                for t in live_targets:
                    # Preserve existing local authorization flags
                    if t.name in self._targets:
                        t.is_authorized_lab = self._targets[t.name].is_authorized_lab
                    self._targets[t.name] = t
            except Exception as e:
                logger.warning(f"Failed to refresh live Tailscale targets: {e}")
        return list(self._targets.values())

    def set_target_authorization(self, target_name: str, authorized: bool) -> Target:
        """Explicitly authorize or de-authorize a target as an owned lab."""
        if target_name not in self._targets:
            raise KeyError(f"Target '{target_name}' not found.")
        self._targets[target_name].is_authorized_lab = authorized
        if self.tailscale and hasattr(self.tailscale, "save_lab_authorization"):
            self.tailscale.save_lab_authorization(target_name, authorized)
        return self._targets[target_name]

    def get_authorized_lab_targets(self) -> List[Target]:
        return [t for t in self.list_targets() if t.is_authorized_lab]

    def register_execution_node(self, node: ExecutionNode) -> None:
        self._execution_nodes[node.name] = node

    def get_default_execution_node(self) -> ExecutionNode:
        for node in self._execution_nodes.values():
            if node.local:
                return node
        local_node = ExecutionNode(name="local-kali", local=True, capabilities=["bash", "tailscale", "legba", "tookie", "uro"])
        self._execution_nodes[local_node.name] = local_node
        return local_node

    # Tailscale Operations
    def get_tailscale_status(self) -> Dict[str, Any]:
        if not self.tailscale:
            return {"online": False, "status": "Adapter not initialized", "devices": []}
        return self.tailscale.get_status()

    # Tookie Reconnaissance
    def run_tookie(self, query: str, timeout: int = 60, max_results: Optional[int] = None) -> URLCollection:
        """Run Tookie OSINT discovery for a username or query with optional max_results limit."""
        if not self.tookie:
            raise RuntimeError("Tookie adapter not configured.")
        result_collection = self.tookie.discover(query, timeout=timeout, max_results=max_results)
        self._last_url_collection = result_collection
        return result_collection

    # Uro Processing
    def run_uro(self, url_collection: Optional[URLCollection] = None) -> URLCollection:
        """Run Uro filtering/deduplication on a URLCollection."""
        if not self.uro:
            raise RuntimeError("Uro adapter not configured.")
        collection = url_collection or self._last_url_collection
        if not collection or not collection.items:
            raise ValueError("No URLs provided or available to filter.")
        cleaned = self.uro.process(collection)
        self._last_url_collection = cleaned
        return cleaned

    # End-to-end Tookie -> Uro Pipeline
    def run_tookie_uro_pipeline(self, query: str, timeout: int = 60, max_results: Optional[int] = None) -> Dict[str, Any]:
        """Execute complete recon pipeline without manual file transfer."""
        raw_collection = self.run_tookie(query, timeout=timeout, max_results=max_results)
        cleaned_collection = self.run_uro(raw_collection)
        return {
            "query": query,
            "raw_count": raw_collection.count(),
            "cleaned_count": cleaned_collection.count(),
            "raw_collection": raw_collection,
            "cleaned_collection": cleaned_collection,
        }

    # Web Crawler Operations
    def run_crawler(self, target_url: str, max_pages: int = 15) -> URLCollection:
        """Execute web crawling and endpoint discovery on a target URL."""
        if not self.crawler:
            from ttula.integrations.crawler.adapter import WebCrawlerAdapter
            self.crawler = WebCrawlerAdapter()
        collection = self.crawler.crawl(target_url, max_pages=max_pages)
        self._last_url_collection = collection
        return collection

    def run_crawler_uro_pipeline(self, target_url: str, max_pages: int = 15) -> Dict[str, Any]:
        """Crawl target web service and immediately pipe to Uro for endpoint normalization."""
        raw_collection = self.run_crawler(target_url, max_pages=max_pages)
        cleaned_collection = self.run_uro(raw_collection)
        return {
            "target_url": target_url,
            "raw_count": raw_collection.count(),
            "cleaned_count": cleaned_collection.count(),
            "raw_collection": raw_collection,
            "cleaned_collection": cleaned_collection,
        }

    # Arsenal Cheat Corpus Operations
    def find_commands(self, query_or_category: str) -> List[Command]:
        """Query Arsenal cheat corpus for candidate commands."""
        if not self.arsenal:
            return []
        return self.arsenal.search(query_or_category)

    def search_commands(self, query: str = "", limit: int = 100) -> List[Command]:
        """Search Arsenal cheat commands with optional limit."""
        results = self.find_commands(query)
        if limit and limit > 0:
            return results[:limit]
        return results

    def prepare_command(
        self,
        command: Command,
        target: Optional[Target] = None,
        extra_params: Optional[Dict[str, str]] = None,
    ) -> Command:
        """Prepares a command by filling placeholders and enforcing lab safety."""
        node = self.get_default_execution_node()
        params = dict(self.arsenal.get_variables()) if (self.arsenal and hasattr(self.arsenal, "get_variables")) else {}
        if extra_params:
            params.update(extra_params)
        return fill_command_placeholders(command, target=target, execution_node=node, extra_params=params)

    def set_session_variable(self, key: str, value: str) -> None:
        """Set a global session variable across Arsenal-NG playbooks."""
        if self.arsenal and hasattr(self.arsenal, "set_variable"):
            self.arsenal.set_variable(key, value)

    def get_session_variables(self) -> Dict[str, str]:
        """Retrieve all active Arsenal-NG session variables."""
        if self.arsenal and hasattr(self.arsenal, "get_variables"):
            return self.arsenal.get_variables()
        return {}

    # Legba Authentication Testing
    def build_legba_command(
        self,
        protocol: str,
        target: Target,
        username: str = "",
        password: str = "",
        wordlist_user: str = "",
        wordlist_pass: str = "",
        port: Optional[int] = None,
        concurrency: int = 2,
    ) -> Command:
        """Build validated Legba command, gated on is_authorized_lab=True."""
        if not self.legba:
            raise RuntimeError("Legba adapter not configured.")
        return self.legba.build_command(
            protocol=protocol,
            target=target,
            username=username,
            password=password,
            wordlist_user=wordlist_user,
            wordlist_pass=wordlist_pass,
            port=port,
            concurrency=concurrency,
        )

    # Execution Management
    def execute_command(self, command: Command) -> ToolResult:
        """Execute a non-interactive tool command via Execution Manager."""
        if command.requires_authorized_lab:
            if not command.target or not command.target.validate_lab_authorization():
                raise PermissionError("Refusing execution: target is not an authorized lab!")

        if not self.execution_manager:
            raise RuntimeError("Execution manager not configured.")
        return self.execution_manager.run_command(command)

    def create_terminal_session(self, node: Optional[ExecutionNode] = None) -> TerminalSession:
        if not self.execution_manager:
            raise RuntimeError("Execution manager not configured.")
        n = node or self.get_default_execution_node()
        return self.execution_manager.create_session(n)

    def send_terminal_input(self, session_id: str, data: str) -> None:
        if not self.execution_manager:
            raise RuntimeError("Execution manager not configured.")
        self.execution_manager.send(session_id, data)

    def read_terminal_output(self, session_id: str, timeout: float = 0.5) -> str:
        if not self.execution_manager:
            raise RuntimeError("Execution manager not configured.")
        return self.execution_manager.read(session_id, timeout=timeout)

    def kill_terminal_session(self, session_id: str) -> None:
        if self.execution_manager:
            self.execution_manager.kill(session_id)


def create_default_engine(mock_tailscale: bool = False, force_native_uro: bool = False) -> TTULAEngine:
    """Builds and wires TTULA engine with standard adapters and execution manager."""
    from ttula.integrations.tailscale.adapter import TailscaleAdapter
    from ttula.integrations.arsenal.adapter import ArsenalAdapter
    from ttula.integrations.tookie.adapter import TookieAdapter
    from ttula.integrations.uro.adapter import UroAdapter
    from ttula.integrations.legba.adapter import LegbaAdapter
    from ttula.integrations.crawler.adapter import WebCrawlerAdapter
    from ttula.execution.manager import get_execution_manager

    tailscale = TailscaleAdapter(mock_mode=mock_tailscale)
    arsenal = ArsenalAdapter()
    tookie = TookieAdapter()
    uro = UroAdapter(force_native_fallback=force_native_uro)
    legba = LegbaAdapter()
    crawler = WebCrawlerAdapter()
    exec_mgr = get_execution_manager()

    engine = TTULAEngine(
        tailscale_adapter=tailscale,
        arsenal_adapter=arsenal,
        tookie_adapter=tookie,
        uro_adapter=uro,
        legba_adapter=legba,
        crawler_adapter=crawler,
        execution_manager=exec_mgr,
    )


    # Pre-populate targets from Tailscale
    try:
        engine.list_targets()
    except Exception:
        pass

    return engine

