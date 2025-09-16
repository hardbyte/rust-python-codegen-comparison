#!/usr/bin/env python3
"""Interactive TUI demo for presentations comparing Axum REST vs ReflectAPI RPC."""

import asyncio
import inspect
import json
import sys
import time
from typing import Any, Dict, List
import threading
import queue

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.align import Align

from axum_server_client import Client as AxumClient
from axum_server_client.api.users import health_get, users_list, user_get
from reflect_api_demo_client import AsyncClient as ReflectClient
from reflect_api_demo_client.generated import ReflectServerGetUserRequest


class DemoTUI:
    """Interactive TUI for comparing REST vs RPC APIs."""

    def __init__(self, auto_advance: bool = False):
        self.console = Console()
        self.axum_client = AxumClient(base_url="http://127.0.0.1:8000")
        self.reflect_client = ReflectClient(base_url="http://127.0.0.1:9000")
        self.auto_advance = auto_advance
        self.input_queue = queue.Queue()
        self.input_thread = None
        
    def create_layout(self) -> Layout:
        """Create the main layout."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )
        
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right"),
        )
        
        layout["left"].split_column(
            Layout(name="rest_title", size=3),
            Layout(name="rest_code"),
            Layout(name="rest_output"),
        )
        
        layout["right"].split_column(
            Layout(name="rpc_title", size=3),
            Layout(name="rpc_code"),
            Layout(name="rpc_output"),
        )
        
        return layout

    def make_header(self) -> Panel:
        """Create the header panel."""
        return Panel(
            Align.center(
                Text("🚀 Rust ↔ Python Codegen Demo", style="bold white on blue")
            ),
            style="blue",
        )

    def make_footer(self, step: str, instruction: str = "") -> Panel:
        """Create the footer panel."""
        if not instruction:
            if self.auto_advance:
                instruction = "[dim]Auto-advancing...[/dim]"
            else:
                instruction = "[dim]Press [bold]Enter[/bold] to continue • [bold]q[/bold] + [bold]Enter[/bold] to quit • [bold]Ctrl+C[/bold] to exit[/dim]"
        
        footer_text = Text()
        footer_text.append(f"Step: {step}", style="bold")
        if instruction:
            footer_text.append(f" | {instruction}")
        
        return Panel(
            Align.center(footer_text),
            style="green",
        )

    def make_code_panel(self, title: str, code: str, lang: str = "python") -> Panel:
        """Create a code panel."""
        syntax = Syntax(code, lang, theme="monokai", line_numbers=True)
        return Panel(syntax, title=f"[bold]{title}[/bold]", border_style="cyan")

    def make_output_panel(self, title: str, content: str) -> Panel:
        """Create an output panel."""
        return Panel(content, title=f"[bold]{title}[/bold]", border_style="green")

    def start_input_thread(self):
        """Start background thread for reading input."""
        def input_reader():
            try:
                while True:
                    key = input()  # This will block until Enter is pressed
                    self.input_queue.put(key.lower().strip())
            except (EOFError, KeyboardInterrupt):
                self.input_queue.put('quit')
        
        self.input_thread = threading.Thread(target=input_reader, daemon=True)
        self.input_thread.start()

    async def wait_for_input(self) -> bool:
        """Wait for user input. Returns True to continue, False to quit."""
        if self.auto_advance:
            await asyncio.sleep(2)
            return True
        
        # Wait for user input
        while True:
            try:
                # Check for input without blocking
                user_input = self.input_queue.get_nowait()
                if user_input in ['q', 'quit', 'exit']:
                    return False
                elif user_input == '' or user_input in ['', 'continue', 'next', 'y', 'yes']:
                    return True
                # For any other input, just continue
                return True
            except queue.Empty:
                # No input yet, wait a bit and check again
                await asyncio.sleep(0.1)

    async def run_demo(self):
        """Run the interactive demo."""
        layout = self.create_layout()
        
        # Demo steps
        steps = [
            ("Health Check", self.demo_health),
            ("List Users", self.demo_list_users),
            ("Get User Details", self.demo_get_user),
            ("Error Handling", self.demo_error_handling),
        ]
        
        # Start input thread for interactive mode
        if not self.auto_advance:
            self.start_input_thread()
        
        try:
            with Live(layout, console=self.console, screen=True, redirect_stderr=False):
                layout["header"].update(self.make_header())
                
                for step_name, step_func in steps:
                    # Show step introduction
                    layout["footer"].update(self.make_footer(step_name, "Ready to execute"))
                    
                    # Show what we're about to do
                    rest_code, rpc_code = step_func(demo_mode=True)
                
                    layout["rest_title"].update(
                        Panel(Align.center("🦀 Axum REST API"), style="blue")
                    )
                    layout["rpc_title"].update(
                        Panel(Align.center("⚡ ReflectAPI RPC"), style="purple")
                    )
                    
                    layout["rest_code"].update(self.make_code_panel("Code", rest_code))
                    layout["rpc_code"].update(self.make_code_panel("Code", rpc_code))
                    
                    layout["rest_output"].update(
                        self.make_output_panel("Output", "[dim]Ready to execute...[/dim]")
                    )
                    layout["rpc_output"].update(
                        self.make_output_panel("Output", "[dim]Ready to execute...[/dim]")
                    )
                    
                    # Wait for user input to proceed
                    if not await self.wait_for_input():
                        break
                    
                    # Show executing state
                    layout["footer"].update(self.make_footer(step_name, "Executing..."))
                    layout["rest_output"].update(
                        self.make_output_panel("Output", "[yellow]Executing...[/yellow]")
                    )
                    layout["rpc_output"].update(
                        self.make_output_panel("Output", "[yellow]Executing...[/yellow]")
                    )
                    
                    # Execute and show results
                    rest_result, rpc_result = await step_func(demo_mode=False)
                    
                    layout["rest_output"].update(
                        self.make_output_panel("Output", rest_result)
                    )
                    layout["rpc_output"].update(
                        self.make_output_panel("Output", rpc_result)
                    )
                    
                    # Show results and wait before next step
                    layout["footer"].update(self.make_footer(step_name, "Results displayed"))
                    if not await self.wait_for_input():
                        break
            
                # Final summary
                layout["footer"].update(self.make_footer("Demo Complete! 🎉", "Press Ctrl+C to exit"))
                try:
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    pass
        except KeyboardInterrupt:
            # Clean exit on Ctrl+C
            pass

    def demo_health(self, demo_mode: bool = False):
        """Demo health check endpoints."""
        rest_code = '''# Axum REST API - Health Check
health = await health_get.asyncio(client=client)
print(f"Status: {health.status}")
print(f"Region: {health.region}")
print(f"Checked: {health.checked_at}")'''

        rpc_code = '''# ReflectAPI RPC - Health Check  
response = await client.health.get()
health = response.data
print(f"Status: {health['status']}")
print(f"Region: {health['region']}")
print(f"Checked: {health['checked_at']}")'''

        if demo_mode:
            return rest_code, rpc_code
            
        return self._execute_health()

    async def _execute_health(self):
        """Execute health check for both APIs."""
        # REST API
        try:
            health = await health_get.asyncio(client=self.axum_client)
            rest_output = f"Status: {health.status}\nRegion: {health.region}\nChecked: {health.checked_at}"
        except Exception as e:
            rest_output = f"Error: {e}"
        
        # RPC API
        try:
            response = await self.reflect_client.health.get()
            if response.data:
                health = response.data
                status = health.get("status") if isinstance(health, dict) else getattr(health, "status", "?")
                region = health.get("region") if isinstance(health, dict) else getattr(health, "region", "?")
                checked_at = health.get("checked_at") if isinstance(health, dict) else getattr(health, "checked_at", "?")
                rpc_output = f"Status: {status}\nRegion: {region}\nChecked: {checked_at}"
            else:
                rpc_output = "No data received"
        except Exception as e:
            rpc_output = f"Error: {e}"
            
        return rest_output, rpc_output

    def demo_list_users(self, demo_mode: bool = False):
        """Demo user listing endpoints."""
        rest_code = '''# Axum REST API - List Users
users = await users_list.asyncio(client=client)
print(f"Found {len(users)} users:")
for user in users[:3]:  # Show first 3
    roles = [r.value for r in user.roles]
    print(f"  #{user.id}: {user.username}")
    print(f"    Roles: {', '.join(roles)}")'''

        rpc_code = '''# ReflectAPI RPC - List Users
response = await client.users.list()
users = response.data
print(f"Found {len(users)} users:")
for user in users[:3]:  # Show first 3
    user_id = user.get("id")
    username = user.get("username")
    roles = user.get("roles", [])
    print(f"  #{user_id}: {username}")
    print(f"    Roles: {', '.join(str(r) for r in roles)}")'''

        if demo_mode:
            return rest_code, rpc_code
            
        return self._execute_list_users()

    async def _execute_list_users(self):
        """Execute user listing for both APIs."""
        # REST API
        try:
            users = await users_list.asyncio(client=self.axum_client)
            rest_lines = [f"Found {len(users)} users:"]
            for user in users[:3]:
                roles = [r.value for r in user.roles] if user.roles else []
                rest_lines.append(f"  #{user.id}: {user.username}")
                rest_lines.append(f"    Roles: {', '.join(roles)}")
            rest_output = "\n".join(rest_lines)
        except Exception as e:
            rest_output = f"Error: {e}"
        
        # RPC API
        try:
            response = await self.reflect_client.users.list()
            if response.data:
                users = response.data
                rpc_lines = [f"Found {len(users)} users:"]
                for user in users[:3]:
                    user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", "?")
                    username = user.get("username") if isinstance(user, dict) else getattr(user, "username", "?")
                    roles = user.get("roles", []) if isinstance(user, dict) else getattr(user, "roles", [])
                    rpc_lines.append(f"  #{user_id}: {username}")
                    rpc_lines.append(f"    Roles: {', '.join(str(r) for r in roles)}")
                rpc_output = "\n".join(rpc_lines)
            else:
                rpc_output = "No data received"
        except Exception as e:
            rpc_output = f"Error: {e}"
            
        return rest_output, rpc_output

    def demo_get_user(self, demo_mode: bool = False):
        """Demo getting specific user."""
        # Get source code from the actual executable functions
        rest_source = inspect.getsource(axum_get_user_demo)
        # Extract just the function body (skip def line and docstring)
        rest_lines = rest_source.split('\n')[2:]  # Skip def and docstring
        rest_code = '\n'.join(line[4:] if line.startswith('    ') else line for line in rest_lines).strip()
        
        rpc_source = inspect.getsource(reflect_get_user_demo)
        # Extract just the function body (skip def line and docstring)  
        rpc_lines = rpc_source.split('\n')[2:]  # Skip def and docstring
        rpc_code = '\n'.join(line[4:] if line.startswith('    ') else line for line in rpc_lines).strip()

        if demo_mode:
            return rest_code, rpc_code
            
        return self._execute_get_user()

    async def _execute_get_user(self):
        """Execute get user for both APIs using single source of truth functions."""
        # REST API
        try:
            rest_output = await axum_get_user_demo(self.axum_client)
        except Exception as e:
            rest_output = f"Error: {e}"
        
        # RPC API
        try:
            rpc_output = await reflect_get_user_demo(self.reflect_client)
        except Exception as e:
            rpc_output = f"Error: {e}"
            
        return rest_output, rpc_output

    def demo_error_handling(self, demo_mode: bool = False):
        """Demo error handling."""
        rest_code = '''# Axum REST API - Error Handling
response = await user_get.asyncio_detailed(
    client=client, id=9999
)
if response.status_code == 404:
    error = response.parsed
    print(f"Error: {error.code}")
    print(f"Message: {error.message}")
else:
    print(f"Unexpected: {response.status_code}")'''

        rpc_code = '''# ReflectAPI RPC - Error Handling
import httpx
async with httpx.AsyncClient() as http_client:
    response = await http_client.post(
        "http://127.0.0.1:9000/user.get",
        json={"id": 9999}
    )
    if response.status_code == 404:
        error = response.json()
        print(f"Error: {error['code']}")
        print(f"Message: {error['message']}")
    else:
        print(f"Unexpected: {response.status_code}")'''

        if demo_mode:
            return rest_code, rpc_code
            
        return self._execute_error_handling()

    async def _execute_error_handling(self):
        """Execute error handling demo for both APIs."""
        # REST API
        try:
            from axum_server_client.api.users import user_get
            from axum_server_client.models import ApiError
            from http import HTTPStatus
            
            response = await user_get.asyncio_detailed(client=self.axum_client, id=9999)
            if response.status_code == HTTPStatus.NOT_FOUND:
                if isinstance(response.parsed, ApiError):
                    rest_output = f"Error: {response.parsed.code}\nMessage: {response.parsed.message}"
                else:
                    rest_output = f"404 but unexpected format: {response.content}"
            else:
                rest_output = f"Unexpected: {response.status_code}"
        except Exception as e:
            rest_output = f"Error: {e}"
        
        # RPC API
        try:
            import httpx
            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(
                    "http://127.0.0.1:9000/user.get",
                    json={"id": 9999}
                )
                if response.status_code == 404:
                    error = response.json()
                    rpc_output = f"Error: {error.get('code', 'unknown')}\nMessage: {error.get('message', 'unknown')}"
                else:
                    rpc_output = f"Unexpected: {response.status_code}"
        except Exception as e:
            rpc_output = f"Error: {e}"
            
        return rest_output, rpc_output


# Standalone executable functions for single source of truth
async def axum_get_user_demo(client: AxumClient) -> str:
    """Axum REST API - Get User"""
    user = await user_get.asyncio(client=client, id=1)
    lines = [
        f"User: {user.username} <{user.email}>",
        f"Status: {user.status.value}",
    ]
    if user.preferences:
        lines.extend([
            f"Theme: {user.preferences.theme.value}",
            f"Timezone: {user.preferences.timezone}"
        ])
    return "\n".join(lines)


async def reflect_get_user_demo(client: ReflectClient) -> str:
    """ReflectAPI RPC - Get User (generated SDK)"""
    request = ReflectServerGetUserRequest(id=1)
    user_response = await client.user.get(data=request)
    if user_response.data:
        user = user_response.data
        username = user.get("username") if isinstance(user, dict) else getattr(user, "username", "?")
        email = user.get("email") if isinstance(user, dict) else getattr(user, "email", "?")
        status_raw = user.get("status") if isinstance(user, dict) else getattr(user, "status", "?")
        # Extract clean status value (remove enum prefix if present)
        status = status_raw.split('.')[-1].lower() if isinstance(status_raw, str) and '.' in str(status_raw) else status_raw
        lines = [
            f"User: {username} <{email}>",
            f"Status: {status}",
        ]
        
        # Extract preferences if available
        preferences = user.get("preferences") if isinstance(user, dict) else getattr(user, "preferences", None)
        if preferences:
            theme_raw = preferences.get("theme") if isinstance(preferences, dict) else getattr(preferences, "theme", "?")
            # Extract clean theme value (remove enum prefix if present)
            theme = theme_raw.split('.')[-1].lower() if isinstance(theme_raw, str) and '.' in str(theme_raw) else theme_raw
            timezone = preferences.get("timezone") if isinstance(preferences, dict) else getattr(preferences, "timezone", "?")
            lines.extend([
                f"Theme: {theme}",
                f"Timezone: {timezone}"
            ])
            
        return "\n".join(lines)
    else:
        return "Error: No data returned"


async def main():
    """Run the demo TUI."""
    import argparse
    parser = argparse.ArgumentParser(description="Interactive TUI demo for Rust-Python API comparison")
    parser.add_argument("--auto", action="store_true", help="Enable auto-advance mode")
    args = parser.parse_args()
    
    demo = DemoTUI(auto_advance=args.auto)
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())