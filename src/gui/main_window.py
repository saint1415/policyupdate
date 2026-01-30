"""
PolicyUpdate Desktop GUI
Built with tkinter for cross-platform compatibility
"""

import sys
import threading
from datetime import datetime
from pathlib import Path

# Add project root to path
GUI_DIR = Path(__file__).parent
PROJECT_ROOT = GUI_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False


class PolicyUpdateGUI:
    """Main GUI application window"""

    def __init__(self):
        if not TKINTER_AVAILABLE:
            raise ImportError("tkinter not available")

        self.root = tk.Tk()
        self.root.title("PolicyUpdate - GRC Policy Management")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)

        # Initialize modules lazily
        self._builder = None
        self._mapper = None
        self._client_manager = None

        self._setup_styles()
        self._create_menu()
        self._create_main_layout()
        self._load_data()

    def _setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')

        # Custom colors
        style.configure('Header.TLabel', font=('Helvetica', 14, 'bold'))
        style.configure('Stats.TLabel', font=('Helvetica', 24, 'bold'))

    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Generate Package...", command=self._show_generate_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Policies", command=lambda: self._show_tab(0))
        view_menu.add_command(label="Frameworks", command=lambda: self._show_tab(1))
        view_menu.add_command(label="Clients", command=lambda: self._show_tab(2))

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _create_main_layout(self):
        """Create main application layout"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with stats
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text="PolicyUpdate GRC Platform",
                  style='Header.TLabel').pack(side=tk.LEFT)

        # Stats frame
        stats_frame = ttk.Frame(header_frame)
        stats_frame.pack(side=tk.RIGHT)

        self.stats_labels = {}
        for stat in ['Frameworks', 'Policies', 'Clients']:
            frame = ttk.Frame(stats_frame)
            frame.pack(side=tk.LEFT, padx=10)
            self.stats_labels[stat] = ttk.Label(frame, text="0", style='Stats.TLabel')
            self.stats_labels[stat].pack()
            ttk.Label(frame, text=stat).pack()

        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Policies tab
        policies_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(policies_frame, text="Policies")
        self._create_policies_tab(policies_frame)

        # Frameworks tab
        frameworks_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frameworks_frame, text="Frameworks")
        self._create_frameworks_tab(frameworks_frame)

        # Clients tab
        clients_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(clients_frame, text="Clients")
        self._create_clients_tab(clients_frame)

        # Generate tab
        generate_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(generate_frame, text="Generate")
        self._create_generate_tab(generate_frame)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var,
                               relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(10, 0))

    def _create_policies_tab(self, parent):
        """Create policies tab content"""
        # Search frame
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.policy_search_var = tk.StringVar()
        self.policy_search_var.trace('w', self._filter_policies)
        search_entry = ttk.Entry(search_frame, textvariable=self.policy_search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=5)

        # Category filter
        ttk.Label(search_frame, text="Category:").pack(side=tk.LEFT, padx=(20, 0))
        self.category_var = tk.StringVar(value="All")
        self.category_combo = ttk.Combobox(search_frame, textvariable=self.category_var,
                                           state='readonly', width=25)
        self.category_combo.pack(side=tk.LEFT, padx=5)
        self.category_combo.bind('<<ComboboxSelected>>', self._filter_policies)

        # Policy list
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ('id', 'title', 'category', 'frameworks')
        self.policy_tree = ttk.Treeview(list_frame, columns=columns, show='headings')

        self.policy_tree.heading('id', text='ID')
        self.policy_tree.heading('title', text='Title')
        self.policy_tree.heading('category', text='Category')
        self.policy_tree.heading('frameworks', text='Frameworks')

        self.policy_tree.column('id', width=150)
        self.policy_tree.column('title', width=300)
        self.policy_tree.column('category', width=150)
        self.policy_tree.column('frameworks', width=200)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.policy_tree.yview)
        self.policy_tree.configure(yscrollcommand=scrollbar.set)

        self.policy_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_frameworks_tab(self, parent):
        """Create frameworks tab content"""
        columns = ('id', 'name', 'version', 'controls', 'policies')
        self.framework_tree = ttk.Treeview(parent, columns=columns, show='headings')

        self.framework_tree.heading('id', text='ID')
        self.framework_tree.heading('name', text='Framework Name')
        self.framework_tree.heading('version', text='Version')
        self.framework_tree.heading('controls', text='Controls')
        self.framework_tree.heading('policies', text='Required Policies')

        self.framework_tree.column('id', width=120)
        self.framework_tree.column('name', width=250)
        self.framework_tree.column('version', width=100)
        self.framework_tree.column('controls', width=80)
        self.framework_tree.column('policies', width=120)

        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.framework_tree.yview)
        self.framework_tree.configure(yscrollcommand=scrollbar.set)

        self.framework_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_clients_tab(self, parent):
        """Create clients tab content"""
        # Buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(btn_frame, text="Add Client", command=self._add_client).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Delete", command=self._delete_client).pack(side=tk.LEFT, padx=5)

        # Client list
        columns = ('id', 'name', 'industry', 'size', 'frameworks')
        self.client_tree = ttk.Treeview(parent, columns=columns, show='headings')

        self.client_tree.heading('id', text='ID')
        self.client_tree.heading('name', text='Name')
        self.client_tree.heading('industry', text='Industry')
        self.client_tree.heading('size', text='Size')
        self.client_tree.heading('frameworks', text='Frameworks')

        self.client_tree.column('id', width=100)
        self.client_tree.column('name', width=200)
        self.client_tree.column('industry', width=150)
        self.client_tree.column('size', width=100)
        self.client_tree.column('frameworks', width=200)

        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.client_tree.yview)
        self.client_tree.configure(yscrollcommand=scrollbar.set)

        self.client_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_generate_tab(self, parent):
        """Create generation tab content"""
        # Form
        form_frame = ttk.LabelFrame(parent, text="Generate Policy Package", padding="10")
        form_frame.pack(fill=tk.X, pady=10)

        # Client name
        ttk.Label(form_frame, text="Client Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.gen_client_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.gen_client_var, width=40).grid(row=0, column=1, pady=5)

        # Frameworks
        ttk.Label(form_frame, text="Frameworks:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.gen_frameworks_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.gen_frameworks_var, width=40).grid(row=1, column=1, pady=5)
        ttk.Label(form_frame, text="(comma-separated: soc2,hipaa,gdpr)").grid(row=1, column=2, padx=5)

        # Format
        ttk.Label(form_frame, text="Format:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.gen_format_var = tk.StringVar(value="docx")
        format_combo = ttk.Combobox(form_frame, textvariable=self.gen_format_var,
                                    values=['docx', 'pdf', 'md', 'all'], state='readonly', width=20)
        format_combo.grid(row=2, column=1, sticky=tk.W, pady=5)

        # Generate button
        ttk.Button(form_frame, text="Generate Package", command=self._generate_package).grid(
            row=3, column=1, pady=20, sticky=tk.W)

        # Output
        output_frame = ttk.LabelFrame(parent, text="Output", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.gen_output = tk.Text(output_frame, height=10, state=tk.DISABLED)
        self.gen_output.pack(fill=tk.BOTH, expand=True)

    def _get_builder(self):
        """Lazy load package builder"""
        if self._builder is None:
            from generation.package_builder import PackageBuilder
            self._builder = PackageBuilder(
                str(PROJECT_ROOT / "policies"),
                str(PROJECT_ROOT / "config" / "frameworks")
            )
        return self._builder

    def _get_mapper(self):
        """Lazy load compliance mapper"""
        if self._mapper is None:
            from core.compliance_mapper import ComplianceMapper
            self._mapper = ComplianceMapper()
            self._mapper.load_all_frameworks(str(PROJECT_ROOT / "config" / "frameworks"))
        return self._mapper

    def _get_client_manager(self):
        """Lazy load client manager"""
        if self._client_manager is None:
            from crm.client_manager import ClientManager
            self._client_manager = ClientManager(str(PROJECT_ROOT / "data" / "clients.db"))
        return self._client_manager

    def _load_data(self):
        """Load initial data"""
        self.status_var.set("Loading...")
        self.root.update()

        try:
            # Load policies
            builder = self._get_builder()
            policies = builder.get_all_policies()
            self._all_policies = policies

            # Get categories
            categories = set()
            for p in policies.values():
                categories.add(p.get('category', 'Uncategorized'))
            self.category_combo['values'] = ['All'] + sorted(categories)

            # Populate policy tree
            self._populate_policy_tree(policies)

            # Load frameworks
            mapper = self._get_mapper()
            self._populate_framework_tree(mapper)

            # Load clients
            self._refresh_clients()

            # Update stats
            self.stats_labels['Frameworks'].config(text=str(len(mapper.frameworks)))
            self.stats_labels['Policies'].config(text=str(len(policies)))
            clients = self._get_client_manager().list_clients()
            self.stats_labels['Clients'].config(text=str(len(clients)))

            self.status_var.set(f"Loaded {len(policies)} policies, {len(mapper.frameworks)} frameworks")

        except Exception as e:
            self.status_var.set(f"Error: {e}")
            messagebox.showerror("Error", str(e))

    def _populate_policy_tree(self, policies):
        """Populate the policy tree view"""
        self.policy_tree.delete(*self.policy_tree.get_children())

        for pid, policy in sorted(policies.items(), key=lambda x: (x[1].get('category', ''), x[1].get('title', ''))):
            frameworks = ', '.join(list(policy.get('frameworks', {}).keys())[:3])
            if len(policy.get('frameworks', {})) > 3:
                frameworks += '...'

            self.policy_tree.insert('', tk.END, values=(
                policy.get('id', pid),
                policy.get('title', ''),
                policy.get('category', ''),
                frameworks
            ))

    def _populate_framework_tree(self, mapper):
        """Populate the framework tree view"""
        self.framework_tree.delete(*self.framework_tree.get_children())

        for fw_id, framework in sorted(mapper.frameworks.items()):
            summary = mapper.get_framework_summary(fw_id)
            self.framework_tree.insert('', tk.END, values=(
                fw_id.upper(),
                framework.name,
                framework.version,
                summary['total_controls'],
                summary['required_policies']
            ))

    def _refresh_clients(self):
        """Refresh client list"""
        self.client_tree.delete(*self.client_tree.get_children())

        try:
            manager = self._get_client_manager()
            clients = manager.list_clients()

            for client in clients:
                frameworks = ', '.join(client.target_frameworks[:3])
                if len(client.target_frameworks) > 3:
                    frameworks += '...'

                self.client_tree.insert('', tk.END, values=(
                    client.id[:8],
                    client.name,
                    client.industry or 'N/A',
                    client.size_tier,
                    frameworks
                ))
        except Exception:
            pass

    def _filter_policies(self, *args):
        """Filter policies based on search and category"""
        search = self.policy_search_var.get().lower()
        category = self.category_var.get()

        filtered = {}
        for pid, policy in self._all_policies.items():
            # Category filter
            if category != 'All' and policy.get('category') != category:
                continue

            # Search filter
            if search:
                if (search not in pid.lower() and
                    search not in policy.get('title', '').lower()):
                    continue

            filtered[pid] = policy

        self._populate_policy_tree(filtered)

    def _show_tab(self, index):
        """Show specific tab"""
        self.notebook.select(index)

    def _show_generate_dialog(self):
        """Show generate dialog"""
        self.notebook.select(3)  # Generate tab

    def _generate_package(self):
        """Generate policy package"""
        client_name = self.gen_client_var.get().strip()
        if not client_name:
            messagebox.showwarning("Warning", "Please enter a client name")
            return

        frameworks = [f.strip() for f in self.gen_frameworks_var.get().split(',') if f.strip()]
        output_format = self.gen_format_var.get()

        self.status_var.set("Generating package...")
        self.root.update()

        def generate():
            try:
                from generation.package_builder import PackageBuilder, ClientConfig

                builder = self._get_builder()

                variables = {
                    'ORGANIZATION_NAME': client_name,
                    'CSO_TITLE': 'Chief Security Officer',
                    'EXEC_MGMT': 'Executive Management',
                    'IT_STAFF': 'IT Staff',
                    'HR_DEPARTMENT': 'Human Resources',
                    'LEGAL_DEPARTMENT': 'Legal Department',
                    'RMO_TITLE': 'Risk Management Officer'
                }

                config = ClientConfig(
                    name=client_name,
                    variables=variables,
                    frameworks=frameworks
                )

                result = builder.build_package(config)

                output_dir = PROJECT_ROOT / "output"
                output_dir.mkdir(exist_ok=True)
                safe_name = client_name.lower().replace(' ', '_')
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

                messages = [f"Generated {result.total_policies} policies"]

                if output_format in ['docx', 'all']:
                    try:
                        from generation.docx_exporter import DocxExporter
                        exporter = DocxExporter()
                        path = output_dir / f"{safe_name}_{timestamp}.docx"
                        exporter.export_package(result, str(path))
                        messages.append(f"DOCX: {path.name}")
                    except ImportError:
                        messages.append("DOCX: python-docx not installed")

                if output_format in ['pdf', 'all']:
                    try:
                        from generation.pdf_exporter import PdfExporter
                        exporter = PdfExporter()
                        path = output_dir / f"{safe_name}_{timestamp}.pdf"
                        exporter.export_package(result, str(path))
                        messages.append(f"PDF: {path.name}")
                    except ImportError:
                        messages.append("PDF: weasyprint not installed")

                self.root.after(0, lambda: self._update_gen_output('\n'.join(messages)))
                self.root.after(0, lambda: self.status_var.set("Generation complete"))

            except Exception as e:
                self.root.after(0, lambda: self._update_gen_output(f"Error: {e}"))
                self.root.after(0, lambda: self.status_var.set("Generation failed"))

        threading.Thread(target=generate, daemon=True).start()

    def _update_gen_output(self, text):
        """Update generation output text"""
        self.gen_output.config(state=tk.NORMAL)
        self.gen_output.delete(1.0, tk.END)
        self.gen_output.insert(tk.END, text)
        self.gen_output.config(state=tk.DISABLED)

    def _add_client(self):
        """Add new client dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Client")
        dialog.geometry("400x300")
        dialog.transient(self.root)

        ttk.Label(dialog, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var, width=30).grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(dialog, text="Industry:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        industry_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=industry_var, width=30).grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(dialog, text="Size:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        size_var = tk.StringVar(value='medium')
        ttk.Combobox(dialog, textvariable=size_var,
                     values=['solopreneur', 'small', 'medium', 'enterprise'],
                     state='readonly', width=27).grid(row=2, column=1, padx=10, pady=10)

        ttk.Label(dialog, text="Frameworks:").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        frameworks_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=frameworks_var, width=30).grid(row=3, column=1, padx=10, pady=10)

        def save():
            if not name_var.get().strip():
                messagebox.showwarning("Warning", "Name required")
                return

            try:
                manager = self._get_client_manager()
                frameworks = [f.strip() for f in frameworks_var.get().split(',') if f.strip()]
                manager.create_client(
                    name_var.get().strip(),
                    industry=industry_var.get(),
                    size_tier=size_var.get(),
                    target_frameworks=frameworks
                )
                self._refresh_clients()
                clients = manager.list_clients()
                self.stats_labels['Clients'].config(text=str(len(clients)))
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(dialog, text="Save", command=save).grid(row=4, column=1, pady=20)

    def _delete_client(self):
        """Delete selected client"""
        selection = self.client_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a client first")
            return

        if messagebox.askyesno("Confirm", "Delete selected client?"):
            item = self.client_tree.item(selection[0])
            client_id = item['values'][0]
            # Need to get full ID from manager
            try:
                manager = self._get_client_manager()
                clients = manager.list_clients()
                for c in clients:
                    if c.id.startswith(client_id):
                        manager.delete_client(c.id)
                        break
                self._refresh_clients()
                self.stats_labels['Clients'].config(text=str(len(manager.list_clients())))
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About PolicyUpdate",
            "PolicyUpdate GRC Platform\n\n"
            "Version 1.0\n\n"
            "11 Compliance Frameworks\n"
            "619 Controls Mapped\n"
            "186 Security Policies\n\n"
            "Frameworks: NIST CSF 2.0, ISO 27001,\n"
            "SOC 2, PCI DSS, HIPAA, GDPR, CCPA,\n"
            "SEC Cyber, NIST 800-171, NIS2, EU AI Act")

    def run(self):
        """Start the application"""
        self.root.mainloop()


def main():
    """Launch the GUI application"""
    if not TKINTER_AVAILABLE:
        print("Error: tkinter not available")
        print("On some systems, install with: apt-get install python3-tk")
        return

    app = PolicyUpdateGUI()
    app.run()


if __name__ == '__main__':
    main()
