"""
PolicyUpdate Professional - Modern Desktop Application
Built with CustomTkinter for a sleek, modern interface
"""

import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

# Add project root to path
GUI_DIR = Path(__file__).parent
PROJECT_ROOT = GUI_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    import customtkinter as ctk
    from PIL import Image
    CUSTOMTKINTER_AVAILABLE = True
except ImportError:
    CUSTOMTKINTER_AVAILABLE = False
    print("CustomTkinter not available. Install with: pip install customtkinter pillow")


# Color scheme
COLORS = {
    "primary": "#2563EB",
    "primary_hover": "#1D4ED8",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "sidebar_bg": "#1E293B",
    "sidebar_hover": "#334155",
    "card_bg": "#FFFFFF",
    "card_bg_dark": "#1E293B",
    "text": "#1F2937",
    "text_secondary": "#6B7280",
    "text_dark": "#F9FAFB",
    "border": "#E5E7EB",
}


class ModernCard(ctk.CTkFrame):
    """Modern card component with shadow effect"""

    def __init__(self, parent, title: str = None, **kwargs):
        super().__init__(parent, corner_radius=12, **kwargs)

        if title:
            self.title_label = ctk.CTkLabel(
                self, text=title,
                font=ctk.CTkFont(size=16, weight="bold"),
                anchor="w"
            )
            self.title_label.pack(fill="x", padx=20, pady=(15, 10))

        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))


class StatCard(ctk.CTkFrame):
    """Statistics card with large number and label"""

    def __init__(self, parent, title: str, value: str, color: str = None, icon: str = None, **kwargs):
        super().__init__(parent, corner_radius=12, **kwargs)

        self.configure(height=120)

        # Icon/indicator
        if color:
            indicator = ctk.CTkFrame(self, width=4, height=60, corner_radius=2, fg_color=color)
            indicator.place(x=15, rely=0.5, anchor="w")

        # Value
        self.value_label = ctk.CTkLabel(
            self, text=value,
            font=ctk.CTkFont(size=36, weight="bold")
        )
        self.value_label.place(x=35, y=25)

        # Title
        self.title_label = ctk.CTkLabel(
            self, text=title,
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"]
        )
        self.title_label.place(x=35, y=75)

    def update_value(self, value: str):
        self.value_label.configure(text=value)


class SidebarButton(ctk.CTkButton):
    """Sidebar navigation button"""

    def __init__(self, parent, text: str, icon: str = None, **kwargs):
        super().__init__(
            parent,
            text=f"  {text}",
            anchor="w",
            height=45,
            corner_radius=8,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            text_color="#94A3B8",
            hover_color=COLORS["sidebar_hover"],
            **kwargs
        )

    def set_active(self, active: bool):
        if active:
            self.configure(fg_color=COLORS["primary"], text_color="white")
        else:
            self.configure(fg_color="transparent", text_color="#94A3B8")


class PolicyUpdatePro(ctk.CTk):
    """Main application window"""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title("PolicyUpdate Pro - GRC Policy Management")
        self.geometry("1400x900")
        self.minsize(1200, 700)

        # Set theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Data holders
        self._builder = None
        self._mapper = None
        self._client_manager = None
        self._all_policies = {}
        self._current_page = "dashboard"

        # Create UI
        self._create_layout()
        self._load_data()

    def _create_layout(self):
        """Create the main application layout"""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self._create_sidebar()

        # Main content area
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#F1F5F9")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Header
        self._create_header()

        # Content container
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 30))
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Create all pages
        self.pages = {}
        self._create_dashboard_page()
        self._create_policies_page()
        self._create_frameworks_page()
        self._create_clients_page()
        self._create_generate_page()

        # Show dashboard by default
        self._show_page("dashboard")

    def _create_sidebar(self):
        """Create the sidebar navigation"""
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=COLORS["sidebar_bg"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Logo/Brand
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=80)
        brand_frame.pack(fill="x", padx=20, pady=(25, 30))
        brand_frame.pack_propagate(False)

        logo_label = ctk.CTkLabel(
            brand_frame,
            text="PolicyUpdate",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white"
        )
        logo_label.pack(anchor="w")

        pro_label = ctk.CTkLabel(
            brand_frame,
            text="Professional Edition",
            font=ctk.CTkFont(size=12),
            text_color="#64748B"
        )
        pro_label.pack(anchor="w")

        # Navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊  Dashboard"),
            ("policies", "📋  Policies"),
            ("frameworks", "🛡️  Frameworks"),
            ("clients", "👥  Clients"),
            ("generate", "⚡  Generate"),
        ]

        for page_id, label in nav_items:
            btn = SidebarButton(self.sidebar, text=label, command=lambda p=page_id: self._show_page(p))
            btn.pack(fill="x", padx=15, pady=3)
            self.nav_buttons[page_id] = btn

        # Separator
        sep = ctk.CTkFrame(self.sidebar, height=1, fg_color="#334155")
        sep.pack(fill="x", padx=20, pady=20)

        # Secondary nav
        secondary_items = [
            ("monitor", "🔔  Monitoring"),
            ("audit", "📝  Audit Log"),
            ("settings", "⚙️  Settings"),
        ]

        for page_id, label in secondary_items:
            btn = SidebarButton(self.sidebar, text=label, command=lambda p=page_id: self._show_page(p))
            btn.pack(fill="x", padx=15, pady=3)
            self.nav_buttons[page_id] = btn

        # Bottom section - Theme toggle
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=20, pady=20)

        theme_label = ctk.CTkLabel(bottom_frame, text="Theme", text_color="#64748B")
        theme_label.pack(anchor="w")

        self.theme_switch = ctk.CTkSwitch(
            bottom_frame,
            text="Dark Mode",
            command=self._toggle_theme,
            text_color="#94A3B8"
        )
        self.theme_switch.pack(anchor="w", pady=5)

    def _create_header(self):
        """Create the header bar"""
        header = ctk.CTkFrame(self.main_frame, height=70, corner_radius=0, fg_color="white")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        # Page title
        self.page_title = ctk.CTkLabel(
            header,
            text="Dashboard",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.page_title.pack(side="left", padx=30, pady=20)

        # Right side - Search and user
        right_frame = ctk.CTkFrame(header, fg_color="transparent")
        right_frame.pack(side="right", padx=30)

        # Search
        self.search_entry = ctk.CTkEntry(
            right_frame,
            placeholder_text="Search policies, frameworks...",
            width=300,
            height=38,
            corner_radius=8
        )
        self.search_entry.pack(side="left", padx=10)

        # User avatar placeholder
        user_btn = ctk.CTkButton(
            right_frame,
            text="👤",
            width=38,
            height=38,
            corner_radius=19,
            fg_color=COLORS["primary"]
        )
        user_btn.pack(side="left")

    def _create_dashboard_page(self):
        """Create the dashboard page"""
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages["dashboard"] = page

        # Stats row
        stats_frame = ctk.CTkFrame(page, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 25))
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.stat_cards = {}
        stats = [
            ("frameworks", "Frameworks", "0", COLORS["primary"]),
            ("policies", "Policies", "0", COLORS["success"]),
            ("clients", "Clients", "0", COLORS["warning"]),
            ("coverage", "Avg Coverage", "0%", COLORS["danger"]),
        ]

        for i, (key, title, value, color) in enumerate(stats):
            card = StatCard(stats_frame, title, value, color)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
            self.stat_cards[key] = card

        # Main content row
        content_row = ctk.CTkFrame(page, fg_color="transparent")
        content_row.pack(fill="both", expand=True)
        content_row.grid_columnconfigure(0, weight=2)
        content_row.grid_columnconfigure(1, weight=1)
        content_row.grid_rowconfigure(0, weight=1)

        # Recent activity card
        activity_card = ModernCard(content_row, title="Recent Activity")
        activity_card.grid(row=0, column=0, padx=(0, 15), sticky="nsew")

        # Activity list
        self.activity_list = ctk.CTkScrollableFrame(activity_card.content_frame, fg_color="transparent")
        self.activity_list.pack(fill="both", expand=True)

        # Placeholder activities
        activities = [
            ("Package generated for Acme Corp", "2 hours ago", COLORS["success"]),
            ("New framework added: DORA", "5 hours ago", COLORS["primary"]),
            ("Policy updated: Access Control", "1 day ago", COLORS["warning"]),
            ("Client added: TechStart Inc", "2 days ago", COLORS["primary"]),
        ]

        for text, time, color in activities:
            item = ctk.CTkFrame(self.activity_list, fg_color="transparent", height=50)
            item.pack(fill="x", pady=5)

            indicator = ctk.CTkFrame(item, width=8, height=8, corner_radius=4, fg_color=color)
            indicator.pack(side="left", padx=(0, 15))

            ctk.CTkLabel(item, text=text, anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(item, text=time, text_color=COLORS["text_secondary"]).pack(side="right")

        # Quick actions card
        actions_card = ModernCard(content_row, title="Quick Actions")
        actions_card.grid(row=0, column=1, sticky="nsew")

        actions = [
            ("Generate Package", COLORS["primary"], lambda: self._show_page("generate")),
            ("Add Client", COLORS["success"], lambda: self._show_page("clients")),
            ("View Frameworks", COLORS["warning"], lambda: self._show_page("frameworks")),
            ("Browse Policies", COLORS["danger"], lambda: self._show_page("policies")),
        ]

        for text, color, command in actions:
            btn = ctk.CTkButton(
                actions_card.content_frame,
                text=text,
                height=45,
                corner_radius=8,
                fg_color=color,
                hover_color=color,
                command=command
            )
            btn.pack(fill="x", pady=5)

    def _create_policies_page(self):
        """Create the policies page"""
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages["policies"] = page

        # Search and filter bar
        filter_frame = ctk.CTkFrame(page, fg_color="white", corner_radius=12, height=70)
        filter_frame.pack(fill="x", pady=(0, 20))
        filter_frame.pack_propagate(False)

        # Search
        self.policy_search = ctk.CTkEntry(
            filter_frame,
            placeholder_text="Search policies...",
            width=400,
            height=40
        )
        self.policy_search.pack(side="left", padx=20, pady=15)
        self.policy_search.bind("<KeyRelease>", self._filter_policies_list)

        # Category filter
        ctk.CTkLabel(filter_frame, text="Category:").pack(side="left", padx=(20, 10))
        self.category_filter = ctk.CTkComboBox(
            filter_frame,
            values=["All Categories"],
            width=200,
            height=40,
            command=self._filter_policies_list
        )
        self.category_filter.pack(side="left")

        # Policy count
        self.policy_count_label = ctk.CTkLabel(
            filter_frame,
            text="0 policies",
            text_color=COLORS["text_secondary"]
        )
        self.policy_count_label.pack(side="right", padx=20)

        # Policies list
        self.policies_scroll = ctk.CTkScrollableFrame(page, fg_color="white", corner_radius=12)
        self.policies_scroll.pack(fill="both", expand=True)

        # Column headers
        header_frame = ctk.CTkFrame(self.policies_scroll, fg_color="#F8FAFC", height=45)
        header_frame.pack(fill="x", padx=5, pady=5)
        header_frame.pack_propagate(False)

        headers = [("Policy ID", 200), ("Title", 350), ("Category", 150), ("Frameworks", 200)]
        for text, width in headers:
            lbl = ctk.CTkLabel(
                header_frame, text=text, width=width,
                font=ctk.CTkFont(weight="bold"),
                anchor="w"
            )
            lbl.pack(side="left", padx=10, pady=10)

        # Policy rows container
        self.policy_rows_frame = ctk.CTkFrame(self.policies_scroll, fg_color="transparent")
        self.policy_rows_frame.pack(fill="both", expand=True)

    def _create_frameworks_page(self):
        """Create the frameworks page"""
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages["frameworks"] = page

        # Frameworks grid
        self.frameworks_scroll = ctk.CTkScrollableFrame(page, fg_color="transparent")
        self.frameworks_scroll.pack(fill="both", expand=True)

        # Will be populated in _load_data
        self.framework_cards_frame = ctk.CTkFrame(self.frameworks_scroll, fg_color="transparent")
        self.framework_cards_frame.pack(fill="both", expand=True)

    def _create_clients_page(self):
        """Create the clients page"""
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages["clients"] = page

        # Header with add button
        header = ctk.CTkFrame(page, fg_color="transparent", height=50)
        header.pack(fill="x", pady=(0, 20))

        add_btn = ctk.CTkButton(
            header,
            text="+ Add Client",
            height=40,
            corner_radius=8,
            fg_color=COLORS["primary"],
            command=self._show_add_client_dialog
        )
        add_btn.pack(side="right")

        # Clients list
        self.clients_scroll = ctk.CTkScrollableFrame(page, fg_color="white", corner_radius=12)
        self.clients_scroll.pack(fill="both", expand=True)

        self.clients_container = ctk.CTkFrame(self.clients_scroll, fg_color="transparent")
        self.clients_container.pack(fill="both", expand=True, padx=20, pady=20)

    def _create_generate_page(self):
        """Create the generate page"""
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages["generate"] = page

        # Two column layout
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=1)
        page.grid_rowconfigure(0, weight=1)

        # Left - Configuration
        config_card = ModernCard(page, title="Package Configuration")
        config_card.grid(row=0, column=0, padx=(0, 15), sticky="nsew")

        # Form
        form = config_card.content_frame

        # Client name
        ctk.CTkLabel(form, text="Organization Name", anchor="w").pack(fill="x", pady=(10, 5))
        self.gen_org_name = ctk.CTkEntry(form, height=40, placeholder_text="Enter organization name")
        self.gen_org_name.pack(fill="x", pady=(0, 15))

        # Frameworks
        ctk.CTkLabel(form, text="Target Frameworks", anchor="w").pack(fill="x", pady=(0, 5))

        self.framework_checkboxes = {}
        frameworks_frame = ctk.CTkFrame(form, fg_color="transparent")
        frameworks_frame.pack(fill="x", pady=(0, 15))

        common_frameworks = ["SOC 2", "ISO 27001", "HIPAA", "PCI DSS", "GDPR", "NIST CSF"]
        for i, fw in enumerate(common_frameworks):
            var = ctk.BooleanVar()
            cb = ctk.CTkCheckBox(frameworks_frame, text=fw, variable=var)
            cb.grid(row=i // 2, column=i % 2, sticky="w", padx=10, pady=5)
            self.framework_checkboxes[fw.lower().replace(" ", "_")] = var

        # Output format
        ctk.CTkLabel(form, text="Output Format", anchor="w").pack(fill="x", pady=(10, 5))
        self.gen_format = ctk.CTkComboBox(
            form,
            values=["Word Document (.docx)", "PDF", "Markdown", "All Formats"],
            height=40
        )
        self.gen_format.pack(fill="x", pady=(0, 20))
        self.gen_format.set("Word Document (.docx)")

        # Generate button
        gen_btn = ctk.CTkButton(
            form,
            text="Generate Policy Package",
            height=50,
            corner_radius=8,
            fg_color=COLORS["primary"],
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._generate_package
        )
        gen_btn.pack(fill="x", pady=10)

        # Right - Preview/Output
        preview_card = ModernCard(page, title="Generation Output")
        preview_card.grid(row=0, column=1, sticky="nsew")

        self.gen_output = ctk.CTkTextbox(preview_card.content_frame, height=400)
        self.gen_output.pack(fill="both", expand=True)
        self.gen_output.insert("1.0", "Configure your package and click Generate.\n\nThe package will include:\n• Customized policies for your organization\n• Compliance mapping documentation\n• Gap analysis report\n• Implementation checklist")
        self.gen_output.configure(state="disabled")

    def _show_page(self, page_id: str):
        """Show the specified page"""
        # Hide all pages
        for page in self.pages.values():
            page.pack_forget()

        # Show requested page (or dashboard if not found)
        if page_id in self.pages:
            self.pages[page_id].pack(fill="both", expand=True)
            self._current_page = page_id

            # Update header title
            titles = {
                "dashboard": "Dashboard",
                "policies": "Policy Library",
                "frameworks": "Compliance Frameworks",
                "clients": "Client Management",
                "generate": "Generate Package",
                "monitor": "Monitoring",
                "audit": "Audit Log",
                "settings": "Settings"
            }
            self.page_title.configure(text=titles.get(page_id, page_id.title()))

        # Update nav buttons
        for btn_id, btn in self.nav_buttons.items():
            btn.set_active(btn_id == page_id)

    def _toggle_theme(self):
        """Toggle between light and dark mode"""
        current = ctk.get_appearance_mode()
        new_mode = "dark" if current == "Light" else "light"
        ctk.set_appearance_mode(new_mode)

    def _get_builder(self):
        """Lazy load package builder"""
        if self._builder is None:
            try:
                from generation.package_builder import PackageBuilder
                self._builder = PackageBuilder(
                    str(PROJECT_ROOT / "policies"),
                    str(PROJECT_ROOT / "config" / "frameworks")
                )
            except Exception as e:
                print(f"Could not load PackageBuilder: {e}")
        return self._builder

    def _get_mapper(self):
        """Lazy load compliance mapper"""
        if self._mapper is None:
            try:
                from core.compliance_mapper import ComplianceMapper
                self._mapper = ComplianceMapper()
                self._mapper.load_all_frameworks(str(PROJECT_ROOT / "config" / "frameworks"))
            except Exception as e:
                print(f"Could not load ComplianceMapper: {e}")
        return self._mapper

    def _get_client_manager(self):
        """Lazy load client manager"""
        if self._client_manager is None:
            try:
                from crm.client_manager import ClientManager
                self._client_manager = ClientManager(str(PROJECT_ROOT / "data" / "clients.db"))
            except Exception as e:
                print(f"Could not load ClientManager: {e}")
        return self._client_manager

    def _load_data(self):
        """Load initial data"""
        def load():
            try:
                # Load policies
                builder = self._get_builder()
                if builder:
                    policies = builder.get_all_policies()
                    self._all_policies = policies
                    self.after(0, lambda: self._populate_policies(policies))
                    self.after(0, lambda: self.stat_cards["policies"].update_value(str(len(policies))))

                    # Get categories
                    categories = ["All Categories"] + sorted(set(
                        p.get('category', 'Uncategorized') for p in policies.values()
                    ))
                    self.after(0, lambda: self.category_filter.configure(values=categories))

                # Load frameworks
                mapper = self._get_mapper()
                if mapper:
                    self.after(0, lambda: self._populate_frameworks(mapper))
                    self.after(0, lambda: self.stat_cards["frameworks"].update_value(str(len(mapper.frameworks))))

                # Load clients
                client_mgr = self._get_client_manager()
                if client_mgr:
                    clients = client_mgr.list_clients()
                    self.after(0, lambda: self._populate_clients(clients))
                    self.after(0, lambda: self.stat_cards["clients"].update_value(str(len(clients))))

            except Exception as e:
                print(f"Error loading data: {e}")

        threading.Thread(target=load, daemon=True).start()

    def _populate_policies(self, policies: Dict):
        """Populate the policies list"""
        # Clear existing
        for widget in self.policy_rows_frame.winfo_children():
            widget.destroy()

        for pid, policy in sorted(policies.items(), key=lambda x: x[1].get('title', '')):
            row = ctk.CTkFrame(self.policy_rows_frame, fg_color="transparent", height=45)
            row.pack(fill="x", padx=5, pady=2)
            row.pack_propagate(False)

            # Policy ID
            ctk.CTkLabel(row, text=policy.get('id', pid)[:25], width=200, anchor="w").pack(side="left", padx=10)

            # Title
            ctk.CTkLabel(row, text=policy.get('title', '')[:45], width=350, anchor="w").pack(side="left", padx=10)

            # Category
            ctk.CTkLabel(row, text=policy.get('category', ''), width=150, anchor="w").pack(side="left", padx=10)

            # Frameworks
            frameworks = list(policy.get('frameworks', {}).keys())[:3]
            fw_text = ", ".join(fw.upper() for fw in frameworks)
            if len(policy.get('frameworks', {})) > 3:
                fw_text += "..."
            ctk.CTkLabel(row, text=fw_text, width=200, anchor="w", text_color=COLORS["text_secondary"]).pack(side="left", padx=10)

        self.policy_count_label.configure(text=f"{len(policies)} policies")

    def _populate_frameworks(self, mapper):
        """Populate the frameworks grid"""
        # Clear existing
        for widget in self.framework_cards_frame.winfo_children():
            widget.destroy()

        # Configure grid
        cols = 3
        for i in range(cols):
            self.framework_cards_frame.grid_columnconfigure(i, weight=1)

        frameworks = list(mapper.frameworks.items())
        for i, (fw_id, framework) in enumerate(sorted(frameworks)):
            summary = mapper.get_framework_summary(fw_id)

            card = ctk.CTkFrame(self.framework_cards_frame, corner_radius=12, fg_color="white")
            card.grid(row=i // cols, column=i % cols, padx=10, pady=10, sticky="nsew")

            # Header
            header = ctk.CTkFrame(card, fg_color=COLORS["primary"], corner_radius=12, height=80)
            header.pack(fill="x")
            header.pack_propagate(False)

            ctk.CTkLabel(
                header,
                text=fw_id.upper().replace("_", " "),
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color="white"
            ).pack(padx=20, pady=(15, 5), anchor="w")

            ctk.CTkLabel(
                header,
                text=f"v{framework.version}",
                text_color="#93C5FD"
            ).pack(padx=20, anchor="w")

            # Stats
            stats_frame = ctk.CTkFrame(card, fg_color="transparent")
            stats_frame.pack(fill="x", padx=20, pady=15)

            ctk.CTkLabel(stats_frame, text=f"{summary['total_controls']}", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
            ctk.CTkLabel(stats_frame, text=" controls", text_color=COLORS["text_secondary"]).pack(side="left")

            ctk.CTkLabel(stats_frame, text=f"{summary['required_policies']}", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left", padx=(30, 0))
            ctk.CTkLabel(stats_frame, text=" policies", text_color=COLORS["text_secondary"]).pack(side="left")

    def _populate_clients(self, clients: List):
        """Populate the clients list"""
        # Clear existing
        for widget in self.clients_container.winfo_children():
            widget.destroy()

        if not clients:
            ctk.CTkLabel(
                self.clients_container,
                text="No clients yet. Click 'Add Client' to get started.",
                text_color=COLORS["text_secondary"]
            ).pack(pady=50)
            return

        for client in clients:
            card = ctk.CTkFrame(self.clients_container, corner_radius=8, height=80)
            card.pack(fill="x", pady=5)
            card.pack_propagate(False)

            # Client info
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=20, pady=15)

            ctk.CTkLabel(
                info_frame,
                text=client.name,
                font=ctk.CTkFont(size=16, weight="bold"),
                anchor="w"
            ).pack(fill="x")

            details = f"{client.industry or 'N/A'} • {client.size_tier} • {', '.join(client.target_frameworks[:3])}"
            ctk.CTkLabel(
                info_frame,
                text=details,
                text_color=COLORS["text_secondary"],
                anchor="w"
            ).pack(fill="x")

            # Actions
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(side="right", padx=20)

            ctk.CTkButton(btn_frame, text="Generate", width=100, height=35).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="Edit", width=80, height=35, fg_color=COLORS["text_secondary"]).pack(side="left")

    def _filter_policies_list(self, *args):
        """Filter policies based on search and category"""
        search = self.policy_search.get().lower()
        category = self.category_filter.get()

        filtered = {}
        for pid, policy in self._all_policies.items():
            # Category filter
            if category != "All Categories" and policy.get('category') != category:
                continue

            # Search filter
            if search:
                if search not in pid.lower() and search not in policy.get('title', '').lower():
                    continue

            filtered[pid] = policy

        self._populate_policies(filtered)

    def _show_add_client_dialog(self):
        """Show dialog to add a new client"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Client")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()

        # Center on parent
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 500) // 2
        y = self.winfo_y() + (self.winfo_height() - 400) // 2
        dialog.geometry(f"+{x}+{y}")

        # Form
        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30, pady=30)

        ctk.CTkLabel(form, text="Add New Client", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", pady=(0, 20))

        ctk.CTkLabel(form, text="Organization Name", anchor="w").pack(fill="x")
        name_entry = ctk.CTkEntry(form, height=40)
        name_entry.pack(fill="x", pady=(5, 15))

        ctk.CTkLabel(form, text="Industry", anchor="w").pack(fill="x")
        industry_entry = ctk.CTkEntry(form, height=40)
        industry_entry.pack(fill="x", pady=(5, 15))

        ctk.CTkLabel(form, text="Size", anchor="w").pack(fill="x")
        size_combo = ctk.CTkComboBox(form, values=["solopreneur", "small", "medium", "enterprise"], height=40)
        size_combo.pack(fill="x", pady=(5, 15))
        size_combo.set("medium")

        def save():
            name = name_entry.get().strip()
            if not name:
                return

            try:
                mgr = self._get_client_manager()
                if mgr:
                    mgr.create_client(name, industry=industry_entry.get(), size_tier=size_combo.get())
                    clients = mgr.list_clients()
                    self._populate_clients(clients)
                    self.stat_cards["clients"].update_value(str(len(clients)))
                dialog.destroy()
            except Exception as e:
                print(f"Error: {e}")

        ctk.CTkButton(form, text="Save Client", height=45, command=save).pack(fill="x", pady=(20, 0))

    def _generate_package(self):
        """Generate a policy package"""
        org_name = self.gen_org_name.get().strip()
        if not org_name:
            self.gen_output.configure(state="normal")
            self.gen_output.delete("1.0", "end")
            self.gen_output.insert("1.0", "⚠️ Please enter an organization name.")
            self.gen_output.configure(state="disabled")
            return

        # Get selected frameworks
        selected = [fw for fw, var in self.framework_checkboxes.items() if var.get()]

        self.gen_output.configure(state="normal")
        self.gen_output.delete("1.0", "end")
        self.gen_output.insert("1.0", f"🔄 Generating package for {org_name}...\n\n")
        self.gen_output.configure(state="disabled")

        def generate():
            try:
                builder = self._get_builder()
                if not builder:
                    raise Exception("Package builder not available")

                from generation.package_builder import ClientConfig

                config = ClientConfig(
                    name=org_name,
                    variables={
                        'ORGANIZATION_NAME': org_name,
                        'CSO_TITLE': 'Chief Security Officer',
                        'EXEC_MGMT': 'Executive Management',
                    },
                    frameworks=selected if selected else ['soc2']
                )

                result = builder.build_package(config)

                output_dir = PROJECT_ROOT / "output"
                output_dir.mkdir(exist_ok=True)

                safe_name = org_name.lower().replace(' ', '_')
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

                messages = [
                    f"✅ Package generated successfully!\n",
                    f"📊 {result.total_policies} policies included",
                    f"🛡️ Frameworks: {', '.join(selected) if selected else 'SOC 2'}",
                    f"\n📁 Output directory: {output_dir}\n"
                ]

                # Export
                try:
                    from generation.docx_exporter import DocxExporter
                    exporter = DocxExporter()
                    path = output_dir / f"{safe_name}_{timestamp}.docx"
                    exporter.export_package(result, str(path))
                    messages.append(f"📄 Word document: {path.name}")
                except ImportError:
                    messages.append("⚠️ DOCX export requires python-docx")

                self.after(0, lambda: self._update_gen_output('\n'.join(messages)))

            except Exception as e:
                self.after(0, lambda: self._update_gen_output(f"❌ Error: {e}"))

        threading.Thread(target=generate, daemon=True).start()

    def _update_gen_output(self, text: str):
        """Update generation output"""
        self.gen_output.configure(state="normal")
        self.gen_output.delete("1.0", "end")
        self.gen_output.insert("1.0", text)
        self.gen_output.configure(state="disabled")


def main():
    """Launch the application"""
    if not CUSTOMTKINTER_AVAILABLE:
        print("CustomTkinter is required. Install with: pip install customtkinter pillow")
        return

    app = PolicyUpdatePro()
    app.mainloop()


if __name__ == '__main__':
    main()
