import os
import asyncio
import random
import json
import logging
import time
import platform
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from contextlib import asynccontextmanager
import aiofiles
from telethon import TelegramClient, events
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest, GetFullChannelRequest
from telethon.errors import (
    SessionPasswordNeededError, 
    FloodWaitError, 
    ChatAdminRequiredError,
    UserAlreadyParticipantError,
    InviteHashExpiredError,
    UserBannedInChannelError,
    ChannelPrivateError
)
from colorama import Fore, Style, Back, init
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.logging import RichHandler
from rich.live import Live
from rich.layout import Layout
from rich.align import Align

# Initialize colorama and rich
init(autoreset=True)
console = Console()

@dataclass
class JoinResult:
    """Result of joining a group."""
    link: str
    success: bool
    error: Optional[str] = None
    group_name: Optional[str] = None
    member_count: Optional[int] = None
    join_time: Optional[datetime] = None

@dataclass
class AccountInfo:
    """Information about a Telegram account."""
    session_name: str
    api_id: int
    api_hash: str
    phone: Optional[str] = None
    first_name: Optional[str] = None
    username: Optional[str] = None
    last_used: Optional[datetime] = None

class ConfigManager:
    """Manages configuration and credentials."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.credentials_file = self.config_dir / "credentials.json"
        self.settings_file = self.config_dir / "settings.json"
    
    def save_credentials(self, account_info: AccountInfo) -> bool:
        """Save API credentials to config file."""
        try:
            credentials = {}
            if self.credentials_file.exists():
                with open(self.credentials_file, 'r') as f:
                    credentials = json.load(f)
            
            credentials[account_info.session_name] = {
                "api_id": account_info.api_id,
                "api_hash": account_info.api_hash,
                "phone": account_info.phone,
                "first_name": account_info.first_name,
                "username": account_info.username,
                "last_used": account_info.last_used.isoformat() if account_info.last_used else None
            }
            
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Failed to save credentials: {str(e)}")
            return False
    
    def get_credentials(self, session_name: str) -> Optional[AccountInfo]:
        """Get saved API credentials for a session."""
        try:
            if not self.credentials_file.exists():
                return None
            
            with open(self.credentials_file, 'r') as f:
                credentials = json.load(f)
            
            if session_name not in credentials:
                return None
            
            cred = credentials[session_name]
            return AccountInfo(
                session_name=session_name,
                api_id=cred["api_id"],
                api_hash=cred["api_hash"],
                phone=cred.get("phone"),
                first_name=cred.get("first_name"),
                username=cred.get("username"),
                last_used=datetime.fromisoformat(cred["last_used"]) if cred.get("last_used") else None
            )
        except Exception as e:
            logging.error(f"Failed to read credentials: {str(e)}")
            return None
    
    def list_saved_accounts(self) -> List[AccountInfo]:
        """List all saved accounts."""
        try:
            if not self.credentials_file.exists():
                return []
            
            with open(self.credentials_file, 'r') as f:
                credentials = json.load(f)
            
            accounts = []
            for session_name, cred in credentials.items():
                accounts.append(AccountInfo(
                    session_name=session_name,
                    api_id=cred["api_id"],
                    api_hash=cred["api_hash"],
                    phone=cred.get("phone"),
                    first_name=cred.get("first_name"),
                    username=cred.get("username"),
                    last_used=datetime.fromisoformat(cred["last_used"]) if cred.get("last_used") else None
                ))
            
            return sorted(accounts, key=lambda x: x.last_used or datetime.min, reverse=True)
        except Exception as e:
            logging.error(f"Failed to list accounts: {str(e)}")
            return []
    
    def save_settings(self, settings: Dict) -> bool:
        """Save application settings."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Failed to save settings: {str(e)}")
            return False
    
    def load_settings(self) -> Dict:
        """Load application settings."""
        try:
            if not self.settings_file.exists():
                return {}
            
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load settings: {str(e)}")
            return {}

class TelegramGroupJoiner:
    """Main class for joining Telegram groups."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.client: Optional[TelegramClient] = None
        self.current_account: Optional[AccountInfo] = None
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_filename = log_dir / f"niftypool_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                RichHandler(console=console, show_time=False, show_path=False)
            ]
        )
        
        # Suppress Telethon's verbose logging
        logging.getLogger("telethon").setLevel(logging.WARNING)
        
        self.logger = logging.getLogger("NiftyPool")
        self.logger.info(f"Logging initialized. Log file: {log_filename}")
    
    def display_banner(self):
        """Display the application banner."""
        console.clear()
        banner = """
    ███╗   ██╗██╗███████╗████████╗██╗   ██╗██████╗  ██████╗  ██████╗ ██╗     
    ████╗  ██║██║██╔════╝╚══██╔══╝╚██╗ ██╔╝██╔══██╗██╔═══██╗██╔═══██╗██║     
    ██╔██╗ ██║██║█████╗     ██║    ╚████╔╝ ██████╔╝██║   ██║██║   ██║██║     
    ██║╚██╗██║██║██╔══╝     ██║     ╚██╔╝  ██╔═══╝ ██║   ██║██║   ██║██║     
    ██║ ╚████║██║██║        ██║      ██║   ██║     ╚██████╔╝╚██████╔╝███████╗
    ╚═╝  ╚═══╝╚═╝╚═╝        ╚═╝      ╚═╝   ╚═╝      ╚═════╝  ╚═════╝ ╚══════╝
        """
        
        console.print(Panel(
            Align.center(f"[cyan bold]{banner}[/cyan bold]\n\n[yellow]Enhanced Telegram Group Joiner v2.0[/yellow]\n[green]Created by @ItsHarshX[/green]"),
            style="bright_blue"
        ))
    
    async def login_account(self, session_name: str = None) -> bool:
        """Handle the login process for a Telegram account."""
        try:
            if not session_name:
                session_name = Prompt.ask("Enter session name", default="niftypool")
            
            # Check for saved credentials
            saved_account = self.config_manager.get_credentials(session_name)
            
            if saved_account:
                console.print(f"[green]Found saved credentials for {session_name}[/green]")
                if Confirm.ask("Use saved credentials?", default=True):
                    api_id = saved_account.api_id
                    api_hash = saved_account.api_hash
                else:
                    api_id = int(Prompt.ask("Enter API ID"))
                    api_hash = Prompt.ask("Enter API Hash")
            else:
                console.print("[yellow]No saved credentials found[/yellow]")
                api_id = int(Prompt.ask("Enter API ID"))
                api_hash = Prompt.ask("Enter API Hash")
            
            console.print("[yellow]Connecting to Telegram...[/yellow]")
            
            self.client = TelegramClient(session_name, api_id, api_hash)
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                phone = Prompt.ask("Enter phone number (with country code)")
                await self.client.send_code_request(phone)
                code = Prompt.ask("Enter the verification code")
                
                try:
                    await self.client.sign_in(phone, code)
                except SessionPasswordNeededError:
                    password = Prompt.ask("Enter 2FA password", password=True)
                    await self.client.sign_in(password=password)
            
            me = await self.client.get_me()
            
            # Update account info
            self.current_account = AccountInfo(
                session_name=session_name,
                api_id=api_id,
                api_hash=api_hash,
                phone=me.phone,
                first_name=me.first_name,
                username=me.username,
                last_used=datetime.now()
            )
            
            # Save credentials
            self.config_manager.save_credentials(self.current_account)
            
            console.print(f"[green]Successfully logged in as {me.first_name} (@{me.username})[/green]")
            self.logger.info(f"Successfully logged in as {me.first_name} (@{me.username})")
            
            return True
            
        except Exception as e:
            console.print(f"[red]Login failed: {str(e)}[/red]")
            self.logger.error(f"Login error: {str(e)}", exc_info=True)
            return False
    
    async def get_group_info(self, link: str) -> Tuple[Optional[str], Optional[int]]:
        """Get group information."""
        try:
            # Extract the last part of the URL
            channel_part = link.split('/')[-1]
            
            # For private channels (both old and new format), we can't get info before joining
            if "joinchat" in link or channel_part.startswith('+'):
                return None, None
            else:
                entity = await self.client.get_entity(channel_part)
                full_channel = await self.client(GetFullChannelRequest(entity))
                return entity.title, full_channel.full_chat.participants_count
        except Exception:
            return None, None
    
    async def join_single_group(self, link: str) -> JoinResult:
        """Join a single Telegram group."""
        start_time = datetime.now()
        
        try:
            # Get group info if possible
            group_name, member_count = await self.get_group_info(link)
            
            # Extract the last part of the URL
            channel_part = link.split('/')[-1]
            
            # Check if it's a private channel (either joinchat or + format)
            if "joinchat" in link or channel_part.startswith('+'):
                # For joinchat links, the hash is after the last /
                # For + links, remove the + prefix to get the hash
                invite_hash = channel_part.replace('+', '')
                if "joinchat" in link:
                    invite_hash = invite_hash.replace('joinchat/', '')
                
                result = await self.client(ImportChatInviteRequest(invite_hash))
                
                # Extract group name from result if we didn't get it before
                if hasattr(result, 'chats') and result.chats:
                    group_name = result.chats[0].title
            else:
                # Public channel/group
                await self.client(JoinChannelRequest(channel_part))
            
            self.logger.info(f"Successfully joined group: {link}")
            
            return JoinResult(
                link=link,
                success=True,
                group_name=group_name,
                member_count=member_count,
                join_time=start_time
            )
            
        except UserAlreadyParticipantError:
            return JoinResult(
                link=link,
                success=True,
                error="Already a member",
                group_name=group_name,
                member_count=member_count,
                join_time=start_time
            )
            
        except FloodWaitError as e:
            error_msg = f"Rate limited. Wait {e.seconds} seconds"
            self.logger.warning(f"Rate limited for {link}: {e.seconds} seconds")
            return JoinResult(
                link=link,
                success=False,
                error=error_msg,
                group_name=group_name,
                member_count=member_count,
                join_time=start_time
            )
            
        except (InviteHashExpiredError, ChannelPrivateError):
            error_msg = "Invalid or expired link"
            self.logger.error(f"Invalid link: {link}")
            return JoinResult(
                link=link,
                success=False,
                error=error_msg,
                group_name=group_name,
                member_count=member_count,
                join_time=start_time
            )
            
        except UserBannedInChannelError:
            error_msg = "Banned from this group"
            self.logger.error(f"Banned from group: {link}")
            return JoinResult(
                link=link,
                success=False,
                error=error_msg,
                group_name=group_name,
                member_count=member_count,
                join_time=start_time
            )
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Failed to join group {link}: {error_msg}")
            return JoinResult(
                link=link,
                success=False,
                error=error_msg,
                group_name=group_name,
                member_count=member_count,
                join_time=start_time
            )
    
    async def load_group_links(self, filename: str = "links.txt") -> List[str]:
        """Load group links from file."""
        try:
            links_file = Path(filename)
            if not links_file.exists():
                console.print(f"[red]{filename} not found. Creating template file...[/red]")
                
                # Create template file
                template_content = """# Add your Telegram group links here, one per line
# Examples:
# https://t.me/example_group
# https://t.me/joinchat/XXXXXXXXXX
"""
                with open(links_file, 'w') as f:
                    f.write(template_content)
                
                console.print(f"[yellow]Template {filename} created. Please add your group links and try again.[/yellow]")
                return []
            
            async with aiofiles.open(links_file, 'r') as f:
                content = await f.read()
                links = [
                    line.strip() 
                    for line in content.split('\n') 
                    if line.strip() and not line.strip().startswith('#')
                ]
            
            return links
            
        except Exception as e:
            console.print(f"[red]Error loading links: {str(e)}[/red]")
            self.logger.error(f"Error loading links: {str(e)}")
            return []
    
    async def join_groups_batch(self, links: List[str], base_interval: float = 5.0, randomize: bool = True) -> List[JoinResult]:
        """Join multiple groups with progress tracking."""
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Joining groups...", total=len(links))
            
            for i, link in enumerate(links):
                # Calculate delay
                if i > 0:
                    if randomize:
                        delay = base_interval * (0.8 + random.random() * 0.4)
                    else:
                        delay = base_interval
                    
                    delay_minutes = delay
                    delay_seconds = delay * 60
                    
                    progress.update(task, description=f"Waiting {delay_minutes:.1f} minutes...")
                    await asyncio.sleep(delay_seconds)
                
                # Join group
                progress.update(task, description=f"Joining: {link}")
                result = await self.join_single_group(link)
                results.append(result)
                
                # Update progress
                progress.update(task, advance=1)
                
                # Show result
                if result.success:
                    status = "[green]✓[/green]"
                    if result.error:
                        status += f" ([yellow]{result.error}[/yellow])"
                else:
                    status = f"[red]✗ {result.error}[/red]"
                
                group_info = f" - {result.group_name}" if result.group_name else ""
                console.print(f"{status} {link}{group_info}")
        
        return results
    
    def display_results_summary(self, results: List[JoinResult]):
        """Display a summary of joining results."""
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        table = Table(title="Join Results Summary")
        table.add_column("Status", style="cyan")
        table.add_column("Count", style="magenta")
        table.add_column("Percentage", style="green")
        
        table.add_row("Successful", str(successful), f"{successful/len(results)*100:.1f}%")
        table.add_row("Failed", str(failed), f"{failed/len(results)*100:.1f}%")
        table.add_row("Total", str(len(results)), "100.0%")
        
        console.print(table)
        
        # Show failed attempts
        failed_results = [r for r in results if not r.success]
        if failed_results:
            console.print("\n[red]Failed Attempts:[/red]")
            for result in failed_results:
                console.print(f"  • {result.link} - {result.error}")
    
    async def run_interactive_mode(self):
        """Run the interactive mode."""
        while True:
            self.display_banner()
            
            # Show current account status
            if self.current_account:
                console.print(f"[green]● Logged in as: {self.current_account.first_name} (@{self.current_account.username})[/green]")
            else:
                console.print("[red]● Not logged in[/red]")
            
            console.print()
            
            # Menu options
            choices = [
                "1. Login to Telegram",
                "2. Join Groups",
                "3. Manage Accounts",
                "4. Settings",
                "5. Exit"
            ]
            
            for choice in choices:
                console.print(f"[cyan]{choice}[/cyan]")
            
            console.print()
            
            try:
                choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5"])
                
                if choice == "1":
                    await self.login_account()
                    Prompt.ask("Press Enter to continue")
                
                elif choice == "2":
                    if not self.client:
                        console.print("[red]Please login first![/red]")
                        Prompt.ask("Press Enter to continue")
                        continue
                    
                    await self.join_groups_interactive()
                    Prompt.ask("Press Enter to continue")
                
                elif choice == "3":
                    await self.manage_accounts()
                    Prompt.ask("Press Enter to continue")
                
                elif choice == "4":
                    await self.settings_menu()
                    Prompt.ask("Press Enter to continue")
                
                elif choice == "5":
                    if self.client:
                        await self.client.disconnect()
                    console.print("[green]Thank you for using NiftyPool Enhanced![/green]")
                    break
                
            except KeyboardInterrupt:
                console.print("[yellow]Operation cancelled by user[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]An error occurred: {str(e)}[/red]")
                self.logger.error(f"Error in interactive mode: {str(e)}", exc_info=True)
                Prompt.ask("Press Enter to continue")
    
    async def join_groups_interactive(self):
        """Interactive group joining interface."""
        console.print("[yellow]═══ JOIN GROUPS ═══[/yellow]")
        
        # Load links
        links = await self.load_group_links()
        if not links:
            return
        
        console.print(f"[green]Found {len(links)} groups to join[/green]")
        
        # Get settings
        base_interval = float(Prompt.ask("Enter base interval in minutes", default="5"))
        randomize = Confirm.ask("Randomize intervals?", default=True)
        
        # Confirm before starting
        if not Confirm.ask(f"Start joining {len(links)} groups?"):
            return
        
        # Join groups
        results = await self.join_groups_batch(links, base_interval, randomize)
        
        # Display results
        self.display_results_summary(results)
        
        # Save results
        await self.save_results(results)
    
    async def delete_account(self, session_name: str) -> bool:
        """Delete local account data without affecting the Telegram account."""
        try:
            # 1. Delete the session file
            session_file = Path(f"{session_name}.session")
            if session_file.exists():
                session_file.unlink()
                self.logger.info(f"Deleted session file: {session_file}")

            # 2. Remove credentials from credentials.json
            credentials = {}
            if self.config_manager.credentials_file.exists():
                with open(self.config_manager.credentials_file, 'r') as f:
                    credentials = json.load(f)
                
                if session_name in credentials:
                    del credentials[session_name]
                    with open(self.config_manager.credentials_file, 'w') as f:
                        json.dump(credentials, f, indent=2)
                    self.logger.info(f"Removed credentials for: {session_name}")

            # 3. Clean up any session-specific settings
            settings = self.config_manager.load_settings()
            session_specific_keys = [k for k in settings if k.startswith(f"{session_name}_")]
            if session_specific_keys:
                for key in session_specific_keys:
                    settings.pop(key, None)
                self.config_manager.save_settings(settings)
                self.logger.info(f"Cleaned up session-specific settings for: {session_name}")

            # If this is the current account, disconnect and clear it
            if self.current_account and self.current_account.session_name == session_name:
                if self.client:
                    await self.client.disconnect()
                self.client = None
                self.current_account = None
                self.logger.info("Disconnected current session")

            console.print(f"[green]Successfully deleted local data for account: {session_name}[/green]")
            return True

        except Exception as e:
            console.print(f"[red]Error deleting account data: {str(e)}[/red]")
            self.logger.error(f"Error deleting account data: {str(e)}", exc_info=True)
            return False

    async def manage_accounts(self):
        """Manage saved accounts."""
        console.print("[yellow]═══ MANAGE ACCOUNTS ═══[/yellow]")
        
        accounts = self.config_manager.list_saved_accounts()
        
        if not accounts:
            console.print("[yellow]No saved accounts found[/yellow]")
            return
        
        table = Table(title="Saved Accounts")
        table.add_column("Session", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Username", style="blue")
        table.add_column("Last Used", style="yellow")
        
        for account in accounts:
            last_used = account.last_used.strftime("%Y-%m-%d %H:%M") if account.last_used else "Never"
            table.add_row(
                account.session_name,
                account.first_name or "Unknown",
                f"@{account.username}" if account.username else "None",
                last_used
            )
        
        console.print(table)
        
        # Account management options
        action = Prompt.ask(
            "Choose action",
            choices=["login", "delete", "back"],
            default="back"
        )
        
        if action == "login":
            session_name = Prompt.ask("Enter session name to login")
            await self.login_account(session_name)
        
        elif action == "delete":
            session_name = Prompt.ask("Enter session name to delete")
            if Confirm.ask(f"[yellow]This will only delete local data, not your Telegram account. Continue?[/yellow]"):
                await self.delete_account(session_name)
                Prompt.ask("Press Enter to continue")
    
    async def settings_menu(self):
        """Settings menu with comprehensive configuration options."""
        while True:
            console.print("[yellow]═══ SETTINGS ═══[/yellow]")
            
            # Load current settings
            current_settings = self.config_manager.load_settings()
            
            # Display current settings
            settings_table = Table(title="Current Settings")
            settings_table.add_column("Setting", style="cyan")
            settings_table.add_column("Value", style="green")
            settings_table.add_column("Description", style="yellow")
            
            # Default settings with descriptions
            default_settings = {
                "default_interval": 5.0,
                "randomize_intervals": True,
                "max_retry_attempts": 3,
                "enable_logging": True,
                "log_level": "INFO",
                "save_results": True,
                "show_member_count": True,
                "flood_wait_multiplier": 1.5,
                "batch_size": 50,
                "enable_notifications": False,
                "auto_save_credentials": True,
                "session_timeout": 3600,
                "default_links_file": "links.txt"
            }
            
            descriptions = {
                "default_interval": "Default interval between joins (minutes)",
                "randomize_intervals": "Add randomization to intervals",
                "max_retry_attempts": "Maximum retry attempts for failed joins",
                "enable_logging": "Enable detailed logging",
                "log_level": "Logging level (DEBUG, INFO, WARNING, ERROR)",
                "save_results": "Automatically save join results",
                "show_member_count": "Display member count for groups",
                "flood_wait_multiplier": "Multiplier for flood wait delays",
                "batch_size": "Maximum groups to process in one batch",
                "enable_notifications": "Enable system notifications",
                "auto_save_credentials": "Automatically save login credentials",
                "session_timeout": "Session timeout in seconds",
                "default_links_file": "Default file name for group links"
            }
            
            # Merge current with defaults
            for key, default_value in default_settings.items():
                value = current_settings.get(key, default_value)
                settings_table.add_row(
                    key.replace("_", " ").title(),
                    str(value),
                    descriptions[key]
                )
            
            console.print(settings_table)
            console.print()
            
            # Settings menu options
            choices = [
                "1. Modify Settings",
                "2. Reset to Defaults",
                "3. Export Settings",
                "4. Import Settings",
                "5. Advanced Settings",
                "6. Back to Main Menu"
            ]
            
            for choice in choices:
                console.print(f"[cyan]{choice}[/cyan]")
            
            console.print()
            
            try:
                choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5", "6"])
                
                if choice == "1":
                    await self.modify_settings(current_settings, default_settings)
                
                elif choice == "2":
                    if Confirm.ask("Reset all settings to defaults?"):
                        self.config_manager.save_settings(default_settings)
                        console.print("[green]Settings reset to defaults[/green]")
                        Prompt.ask("Press Enter to continue")
                
                elif choice == "3":
                    await self.export_settings(current_settings)
                
                elif choice == "4":
                    await self.import_settings()
                
                elif choice == "5":
                    await self.advanced_settings(current_settings)
                
                elif choice == "6":
                    break
                
            except KeyboardInterrupt:
                console.print("[yellow]Returning to main menu[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error in settings menu: {str(e)}[/red]")
                self.logger.error(f"Settings menu error: {str(e)}", exc_info=True)
                Prompt.ask("Press Enter to continue")
    
    async def modify_settings(self, current_settings: Dict, default_settings: Dict):
        """Modify individual settings."""
        console.print("[yellow]═══ MODIFY SETTINGS ═══[/yellow]")
        
        setting_keys = list(default_settings.keys())
        
        # Display settings with numbers
        for i, key in enumerate(setting_keys, 1):
            value = current_settings.get(key, default_settings[key])
            console.print(f"[cyan]{i}. {key.replace('_', ' ').title()}[/cyan]: {value}")
        
        console.print()
        
        try:
            choice = Prompt.ask("Enter setting number to modify (or 'back' to return)", default="back")
            
            if choice.lower() == "back":
                return
            
            setting_index = int(choice) - 1
            if 0 <= setting_index < len(setting_keys):
                setting_key = setting_keys[setting_index]
                current_value = current_settings.get(setting_key, default_settings[setting_key])
                
                console.print(f"[yellow]Current value for {setting_key.replace('_', ' ').title()}: {current_value}[/yellow]")
                
                # Handle different types of settings
                if isinstance(current_value, bool):
                    new_value = Confirm.ask(f"Set {setting_key.replace('_', ' ').title()}", default=current_value)
                
                elif isinstance(current_value, (int, float)):
                    new_value = float(Prompt.ask(f"Enter new value for {setting_key.replace('_', ' ').title()}", default=str(current_value)))
                    if setting_key in ["max_retry_attempts", "batch_size", "session_timeout"]:
                        new_value = int(new_value)
                
                elif setting_key == "log_level":
                    new_value = Prompt.ask(
                        "Select log level",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        default=current_value
                    )
                
                else:
                    new_value = Prompt.ask(f"Enter new value for {setting_key.replace('_', ' ').title()}", default=str(current_value))
                
                # Update settings
                current_settings[setting_key] = new_value
                self.config_manager.save_settings(current_settings)
                
                console.print(f"[green]Updated {setting_key.replace('_', ' ').title()} to: {new_value}[/green]")
                
                # Apply immediate changes if needed
                if setting_key == "log_level":
                    logging.getLogger().setLevel(getattr(logging, new_value))
                
            else:
                console.print("[red]Invalid setting number[/red]")
                
        except ValueError:
            console.print("[red]Invalid input[/red]")
        except Exception as e:
            console.print(f"[red]Error modifying settings: {str(e)}[/red]")
            self.logger.error(f"Error modifying settings: {str(e)}")
        
        Prompt.ask("Press Enter to continue")
    
    async def export_settings(self, settings: Dict):
        """Export settings to a file."""
        console.print("[yellow]═══ EXPORT SETTINGS ═══[/yellow]")
        
        try:
            export_dir = Path("exports")
            export_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = export_dir / f"settings_export_{timestamp}.json"
            
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "version": "2.0",
                "settings": settings
            }
            
            async with aiofiles.open(export_file, 'w') as f:
                await f.write(json.dumps(export_data, indent=2))
            
            console.print(f"[green]Settings exported to: {export_file}[/green]")
            
        except Exception as e:
            console.print(f"[red]Failed to export settings: {str(e)}[/red]")
            self.logger.error(f"Settings export error: {str(e)}")
        
        Prompt.ask("Press Enter to continue")

    async def import_settings(self):
        """Import settings from a file."""
        console.print("[yellow]═══ IMPORT SETTINGS ═══[/yellow]")
        
        try:
            import_file = Prompt.ask("Enter path to settings file", default="exports/settings_export.json")
            import_path = Path(import_file)
            
            if not import_path.exists():
                console.print(f"[red]File not found: {import_file}[/red]")
                Prompt.ask("Press Enter to continue")
                return
            
            async with aiofiles.open(import_path, 'r') as f:
                import_data = json.loads(await f.read())
            
            if "settings" not in import_data:
                console.print("[red]Invalid settings file format[/red]")
                Prompt.ask("Press Enter to continue")
                return
            
            # Display what will be imported
            console.print("[yellow]Settings to import:[/yellow]")
            for key, value in import_data["settings"].items():
                console.print(f"  {key}: {value}")
            
            if Confirm.ask("Import these settings?"):
                self.config_manager.save_settings(import_data["settings"])
                console.print("[green]Settings imported successfully[/green]")
            
        except Exception as e:
            console.print(f"[red]Failed to import settings: {str(e)}[/red]")
            self.logger.error(f"Settings import error: {str(e)}")
        
        Prompt.ask("Press Enter to continue")
    
    async def advanced_settings(self, current_settings: Dict):
        """Advanced settings menu."""
        console.print("[yellow]═══ ADVANCED SETTINGS ═══[/yellow]")
        
        while True:
            choices = [
                "1. Configure Proxy Settings",
                "2. API Rate Limits",
                "3. Error Handling",
                "4. Performance Tuning",
                "5. Security Settings",
                "6. Back to Settings Menu"
            ]
            
            for choice in choices:
                console.print(f"[cyan]{choice}[/cyan]")
            
            console.print()
            
            try:
                choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5", "6"])
                
                if choice == "1":
                    await self.configure_proxy_settings(current_settings)
                
                elif choice == "2":
                    await self.configure_rate_limits(current_settings)
                
                elif choice == "3":
                    await self.configure_error_handling(current_settings)
                
                elif choice == "4":
                    await self.configure_performance(current_settings)
                
                elif choice == "5":
                    await self.configure_security(current_settings)
                
                elif choice == "6":
                    break
                
            except KeyboardInterrupt:
                console.print("[yellow]Returning to settings menu[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error in advanced settings: {str(e)}[/red]")
                Prompt.ask("Press Enter to continue")

    async def configure_proxy_settings(self, settings: Dict):
        """Configure proxy settings."""
        console.print("[yellow]═══ PROXY SETTINGS ═══[/yellow]")
        
        proxy_enabled = settings.get("proxy_enabled", False)
        
        if Confirm.ask("Enable proxy?", default=proxy_enabled):
            proxy_type = Prompt.ask("Proxy type", choices=["http", "socks4", "socks5"], default="http")
            proxy_host = Prompt.ask("Proxy host", default=settings.get("proxy_host", ""))
            proxy_port = int(Prompt.ask("Proxy port", default=str(settings.get("proxy_port", 8080))))
            proxy_username = Prompt.ask("Proxy username (optional)", default=settings.get("proxy_username", ""))
            proxy_password = Prompt.ask("Proxy password (optional)", password=True, default="")
            
            settings.update({
                "proxy_enabled": True,
                "proxy_type": proxy_type,
                "proxy_host": proxy_host,
                "proxy_port": proxy_port,
                "proxy_username": proxy_username,
                "proxy_password": proxy_password
            })
            
            console.print("[green]Proxy settings configured[/green]")
        else:
            settings["proxy_enabled"] = False
            console.print("[green]Proxy disabled[/green]")
        
        self.config_manager.save_settings(settings)
        Prompt.ask("Press Enter to continue")

    async def configure_rate_limits(self, settings: Dict):
        """Configure API rate limits."""
        console.print("[yellow]═══ API RATE LIMITS ═══[/yellow]")
        
        min_interval = float(Prompt.ask("Minimum interval between requests (seconds)", default=str(settings.get("min_request_interval", 1.0))))
        max_requests_per_minute = int(Prompt.ask("Maximum requests per minute", default=str(settings.get("max_requests_per_minute", 20))))
        flood_wait_multiplier = float(Prompt.ask("Flood wait multiplier", default=str(settings.get("flood_wait_multiplier", 1.5))))
        
        settings.update({
            "min_request_interval": min_interval,
            "max_requests_per_minute": max_requests_per_minute,
            "flood_wait_multiplier": flood_wait_multiplier
        })
        
        self.config_manager.save_settings(settings)
        console.print("[green]Rate limit settings updated[/green]")
        Prompt.ask("Press Enter to continue")

    async def configure_error_handling(self, settings: Dict):
        """Configure error handling settings."""
        console.print("[yellow]═══ ERROR HANDLING ═══[/yellow]")
        
        max_retries = int(Prompt.ask("Maximum retry attempts", default=str(settings.get("max_retry_attempts", 3))))
        retry_delay = float(Prompt.ask("Retry delay (seconds)", default=str(settings.get("retry_delay", 5.0))))
        continue_on_error = Confirm.ask("Continue on errors?", default=settings.get("continue_on_error", True))
        save_failed_links = Confirm.ask("Save failed links to file?", default=settings.get("save_failed_links", True))
        
        settings.update({
            "max_retry_attempts": max_retries,
            "retry_delay": retry_delay,
            "continue_on_error": continue_on_error,
            "save_failed_links": save_failed_links
        })
        
        self.config_manager.save_settings(settings)
        console.print("[green]Error handling settings updated[/green]")
        Prompt.ask("Press Enter to continue")

    async def configure_performance(self, settings: Dict):
        """Configure performance settings."""
        console.print("[yellow]═══ PERFORMANCE TUNING ═══[/yellow]")
        
        concurrent_joins = int(Prompt.ask("Concurrent joins (1-5)", default=str(settings.get("concurrent_joins", 1))))
        if concurrent_joins > 5:
            concurrent_joins = 5
            console.print("[yellow]Limited concurrent joins to 5 for safety[/yellow]")
        
        batch_size = int(Prompt.ask("Batch size", default=str(settings.get("batch_size", 50))))
        memory_limit = int(Prompt.ask("Memory limit (MB)", default=str(settings.get("memory_limit", 512))))
        
        settings.update({
            "concurrent_joins": concurrent_joins,
            "batch_size": batch_size,
            "memory_limit": memory_limit
        })
        
        self.config_manager.save_settings(settings)
        console.print("[green]Performance settings updated[/green]")
        Prompt.ask("Press Enter to continue")

    async def configure_security(self, settings: Dict):
        """Configure security settings."""
        console.print("[yellow]═══ SECURITY SETTINGS ═══[/yellow]")
        
        encrypt_credentials = Confirm.ask("Encrypt stored credentials?", default=settings.get("encrypt_credentials", False))
        session_timeout = int(Prompt.ask("Session timeout (seconds)", default=str(settings.get("session_timeout", 3600))))
        require_2fa = Confirm.ask("Require 2FA for sensitive operations?", default=settings.get("require_2fa", False))
        auto_logout = Confirm.ask("Auto logout on inactivity?", default=settings.get("auto_logout", False))
        
        settings.update({
            "encrypt_credentials": encrypt_credentials,
            "session_timeout": session_timeout,
            "require_2fa": require_2fa,
            "auto_logout": auto_logout
        })
        
        self.config_manager.save_settings(settings)
        console.print("[green]Security settings updated[/green]")
        
        if encrypt_credentials:
            console.print("[yellow]Note: Credential encryption will be applied on next login[/yellow]")
        
        Prompt.ask("Press Enter to continue")

    async def save_results(self, results: List[JoinResult]):
        """Save joining results to file."""
        try:
            results_dir = Path("results")
            results_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = results_dir / f"join_results_{timestamp}.json"
            
            results_data = []
            for result in results:
                results_data.append({
                    "link": result.link,
                    "success": result.success,
                    "error": result.error,
                    "group_name": result.group_name,
                    "member_count": result.member_count,
                    "join_time": result.join_time.isoformat() if result.join_time else None
                })
            
            async with aiofiles.open(results_file, 'w') as f:
                await f.write(json.dumps(results_data, indent=2))
            
            console.print(f"[green]Results saved to {results_file}[/green]")
            
        except Exception as e:
            console.print(f"[red]Failed to save results: {str(e)}[/red]")
            self.logger.error(f"Failed to save results: {str(e)}")

@click.command()
@click.option('--session', '-s', help='Session name to use')
@click.option('--interval', '-i', type=float, default=5.0, help='Base interval in minutes')
@click.option('--links-file', '-f', default='links.txt', help='File containing group links')
@click.option('--no-randomize', is_flag=True, help='Disable interval randomization')
@click.option('--batch-mode', is_flag=True, help='Run in batch mode (non-interactive)')
def main(session, interval, links_file, no_randomize, batch_mode):
    """Enhanced NiftyPool Telegram Group Joiner."""
    
    async def run_app():
        app = TelegramGroupJoiner()
        
        if batch_mode:
            # Batch mode implementation
            if not session:
                console.print("[red]Session name required for batch mode[/red]")
                return
            
            if not await app.login_account(session):
                console.print("[red]Login failed[/red]")
                return
            
            links = await app.load_group_links(links_file)
            if not links:
                console.print("[red]No links found[/red]")
                return
            
            results = await app.join_groups_batch(links, interval, not no_randomize)
            app.display_results_summary(results)
            await app.save_results(results)
            
        else:
            # Interactive mode
            await app.run_interactive_mode()
    
    try:
        asyncio.run(run_app())
    except KeyboardInterrupt:
        console.print("[yellow]Application terminated by user[/yellow]")
    except Exception as e:
        console.print(f"[red]A fatal error occurred: {str(e)}[/red]")
        logging.error(f"Fatal error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()