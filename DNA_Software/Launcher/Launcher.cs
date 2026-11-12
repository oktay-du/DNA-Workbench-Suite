using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Text;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using System.Threading.Tasks;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

[assembly: System.Reflection.AssemblyVersion("1.0.1.0")]
[assembly: System.Reflection.AssemblyFileVersion("1.0.5.0")]
[assembly: System.Reflection.AssemblyInformationalVersion("1.0.5")]

namespace DnaWorkbench
{
    public class Field
    {
        public string key
        {
            get; set;
        }
        public string label
        {
            get; set;
        }
        public string kind
        {
            get; set;
        }
        public string help
        {
            get; set;
        }
        public string @default
        {
            get; set;
        }
        public bool required
        {
            get; set;
        }
        public bool multi
        {
            get; set;
        }
        public string[] choices
        {
            get; set;
        }
    }
    public class TaskInfo
    {
        public string id
        {
            get; set;
        }
        public string category
        {
            get; set;
        }
        public string title
        {
            get; set;
        }
        public string description
        {
            get; set;
        }
        public string tools
        {
            get; set;
        }
        public string action
        {
            get; set;
        }
        public string help
        {
            get; set;
        }
        public string button
        {
            get; set;
        }
        public string platform
        {
            get; set;
        }
        public string kind
        {
            get; set;
        }
        public string core
        {
            get; set;
        }
        public int step
        {
            get; set;
        }
        public Field[] fields
        {
            get; set;
        }
    }
    public class Catalog
    {
        public int version
        {
            get; set;
        }
        public string[] categories
        {
            get; set;
        }
        public TaskInfo[] tasks
        {
            get; set;
        }
    }
    public static class Program
    {
        [STAThread]
        public static void Main(string[] args)
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.ThreadException += delegate (object s, System.Threading.ThreadExceptionEventArgs e)
            {
                ShowCrash(e.Exception);
            };
            string identity;
            using (var sha = System.Security.Cryptography.SHA256.Create())
                identity = BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(Path.GetFullPath(AppDomain.CurrentDomain.BaseDirectory).ToLowerInvariant()))).Replace("-", "");
            bool created;
            using (var single = new System.Threading.Mutex(true, "Local\\DNAWorkbench_" + identity, out created))
            {
                if (!created)
                {
                    MessageBox.Show("DNA Workbench already runs for this app folder.", "DNA Workbench");
                    return;
                }
                try
                {
                    PortableEnvironment.Configure();
                    BootstrapPayload.Ensure();
                    if (args.Contains("--bootstrap-check"))
                    {
                        File.WriteAllText(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "bootstrap-check.txt"), "Core payload extracted successfully; no services started.");
                        return;
                    }
                    Start(args);
                }
                catch (Exception e) { ShowCrash(e); }
            }
        }
        static void ShowCrash(Exception error)
        {
            string type = error.GetType().Name;
            try
            {
                string folder = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "DNA_Software/UserData/Launcher/Diagnostics");
                Directory.CreateDirectory(folder);
                var record = new Dictionary<string, object> { { "exception_type", type }, { "created_utc", DateTime.UtcNow.ToString("o", System.Globalization.CultureInfo.InvariantCulture) } };
                File.WriteAllText(Path.Combine(folder, "last-crash.json"), new JavaScriptSerializer().Serialize(record), Encoding.UTF8);
            }
            catch (IOException) { }
            catch (UnauthorizedAccessException) { }
            MessageBox.Show("The app encountered an error (" + type + "). A minimal crash record was saved locally; nothing was uploaded. After restarting, open Feedback & bugs and choose optional diagnostics to prepare a report. No DNA, exception message or paths are included in the crash record.", "DNA Workbench · crash report", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.NoInlining)]
        static void Start(string[] args)
        {
            using (var splash = new StartupScreen())
            {
                if (splash.ShowDialog() != DialogResult.OK)
                    return;
                var app = new Workbench(splash.Context);
                if (args.Contains("--plugins"))
                    app.Shown += delegate
                    {
                        app.OpenWorkspacePath("/plugins");
                    };
                if (args.Contains("--research"))
                    app.Shown += delegate
                    {
                        app.OpenWorkspacePath("/research");
                    };
                if (args.Contains("--family") || args.Contains("--visual"))
                    app.Shown += delegate
                    {
                        app.OpenWorkspace(args.Contains("--visual"));
                    };
                int viewIndex = Array.IndexOf(args, "--view-path");
                if (viewIndex >= 0 && viewIndex + 1 < args.Length && System.Text.RegularExpressions.Regex.IsMatch(args[viewIndex + 1], "^/visual-run/[a-f0-9]{32}/index[.]html$"))
                {
                    string viewPath = args[viewIndex + 1];
                    app.Shown += delegate
                    {
                        app.OpenWorkspacePath(viewPath);
                    };
                }
                if (!args.Contains("--legacy") && !args.Contains("--family") && !args.Contains("--visual") && !args.Contains("--research") && !args.Contains("--plugins") && viewIndex < 0)
                    app.Shown += delegate
                    {
                        app.OpenWorkspacePath("/app");
                    };
                Application.Run(app);
            }
        }
    }
    public partial class Workbench : Form
    {
        static readonly string[] AllowedToolViewTasks = new[] { "sequence_stats", "sequence_extract", "seqviz_view", "gatk_validate", "ugene", "kinship", "beagle", "ibd", "pca", "rfmix", "ancient", "roh", "peddy", "whatshap", "truvari", "sarek", "pgs", "pharmcat", "gramps", "chip_vcf" };
        readonly string root, appdir, jobsroot, python;
        readonly Catalog catalog;
        readonly JavaScriptSerializer json = new JavaScriptSerializer { MaxJsonLength = 64 * 1024 * 1024 };
        readonly Color ink = Color.FromArgb(25, 43, 63), muted = Color.FromArgb(100, 116, 135), teal = Color.FromArgb(0, 137, 127), paper = Color.FromArgb(245, 247, 250), nav = Color.FromArgb(20, 34, 51);
        readonly ToolTip tips = new ToolTip { InitialDelay = 300, ReshowDelay = 150, AutoPopDelay = 20000, ShowAlways = true };
        ComboBox person; TextBox search; Label subtitle, detailTitle, detailSub, progressText; FlowLayoutPanel cards, inputs; Panel listHost, detail; DataGridView history; RichTextBox log;
        Button run, preview, results, cancel; ProgressBar progress; System.Windows.Forms.Timer timer;
        readonly Dictionary<string, Control> fields = new Dictionary<string, Control>();
        readonly Dictionary<string, object> choices = new Dictionary<string, object>();
        readonly Dictionary<string, Button> categories = new Dictionary<string, Button>();
        string category = "All steps", mode = "Ablauf", viewJob = "", activeJob = "", lastLog = "";
        string editingPerson = ""; bool dpiReady;
        readonly HashSet<string> sourceSelection = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        TaskInfo selected; Process worker; bool previewing;
        Process familyServer; string familyBase = "", pendingPath = "/"; Panel workspace; WebView2 familyView; int viewGeneration;
        private static readonly string[] first = new string[] { "Import" };

        public Workbench(StartupContext startup = null)
        {
            root = Path.GetFullPath(AppDomain.CurrentDomain.BaseDirectory);
            appdir = Path.Combine(root, "DNA_Software", "Launcher");
            jobsroot = Path.Combine(root, "Projects", "Launcher");
            if (!File.Exists(Path.Combine(appdir, "catalog.json")))
                throw new FileNotFoundException("Launcher resources missing. Please leave the EXE in the root folder of the DNA SSD.");
            catalog = json.Deserialize<Catalog>(File.ReadAllText(Path.Combine(appdir, "catalog.json"), Encoding.UTF8));
            python = Directory.GetFiles(Path.Combine(root, "DNA_Software", "Windows", "Python"), "python.exe", SearchOption.AllDirectories).First();
            Directory.CreateDirectory(jobsroot);
            if (startup != null)
            {
                familyServer = startup.Server;
                familyBase = startup.Url;
            }
            Text = "DNA Workbench | Local genomics workspace";
            Font = new Font("Segoe UI", 10);
            BackColor = paper;
            ForeColor = ink;
            ClientSize = new Size(1400, 880);
            MinimumSize = new Size(1000, 620);
            StartPosition = FormStartPosition.CenterScreen;
            WindowState = FormWindowState.Maximized;
            AutoScaleDimensions = new SizeF(96F, 96F);
            AutoScaleMode = AutoScaleMode.Dpi;
            SetStyle(ControlStyles.OptimizedDoubleBuffer, true);
            var icon = Path.Combine(appdir, "dna.ico");
            if (File.Exists(icon))
                Icon = new Icon(icon);
            BuildUI();
            timer = new System.Windows.Forms.Timer { Interval = 1200 };
            timer.Tick += Tick;
            timer.Start();
            FormClosing += delegate
            {
                SavePreferences();
                timer.Stop();
                if (familyView != null)
                    familyView.Dispose();
                if (familyServer != null)
                    try
                    {
                        familyServer.StandardInput.Close();
                    }
                    catch { }
            };
            LoadPreferences();
            RenderCards();
            ShowWelcome();
            if (startup != null)
                progressText.Text = "App bereit · Ubuntu: " + startup.LinuxStatus;
            Shown += delegate
            {
                dpiReady = true;
                RenderCards();
                if (selected != null)
                    SelectTask(selected);
                else
                    ShowWelcome();
            };
        }
        int S(int n)
        {
            return dpiReady ? (int)Math.Round(n * (DeviceDpi / 96.0)) : n;
        }
        void ScaleDynamic(Control c)
        {
            if (!dpiReady || DeviceDpi == 96)
                return;
            var fonts = c.Controls.Cast<Control>().ToDictionary(x => x, x => x.Font);
            c.Scale(new SizeF(DeviceDpi / 96F, DeviceDpi / 96F));
            foreach (var f in fonts)
                f.Key.Font = f.Value;
        }
        static Button Button(string text, Color bg, Color fg)
        {
            var b = new Button { Text = text, UseMnemonic = false, FlatStyle = FlatStyle.Flat, BackColor = bg, ForeColor = fg, Cursor = Cursors.Hand, Height = 38, Font = new Font("Segoe UI", 10) };
            b.FlatAppearance.BorderSize = 0;
            return b;
        }
        Label Label(string text, int size, bool bold)
        {
            return new Label { Text = text, UseMnemonic = false, AutoSize = false, ForeColor = ink, Font = new Font("Segoe UI", size, bold ? FontStyle.Bold : FontStyle.Regular) };
        }
        void BuildUI()
        {
            var side = new Panel { Dock = DockStyle.Left, Width = 220, BackColor = nav, Padding = new Padding(18) };
            Controls.Add(side);
            var brand = Label("DNA", 21, true);
            brand.ForeColor = Color.White;
            brand.SetBounds(20, 24, 190, 78);
            side.Controls.Add(brand);
            var local = Label("WORKBENCH · LOKAL", 8, false);
            local.ForeColor = Color.FromArgb(107, 203, 194);
            local.SetBounds(22, 110, 190, 26);
            side.Controls.Add(local);
            int y = 158;
            foreach (string cat in first.Concat(catalog.categories))
            {
                var b = Button(cat, nav, Color.FromArgb(202, 215, 229));
                b.TextAlign = ContentAlignment.MiddleLeft;
                b.Padding = new Padding(10, 0, 0, 0);
                b.SetBounds(12, y, 196, 42);
                y += 48;
                string c = cat;
                b.Click += delegate
                {
                    NavigateCategory(c);
                };
                side.Controls.Add(b);
                categories[c] = b;
            }
            var familyButton = Button("Family tree & DNA", Color.FromArgb(0, 102, 103), Color.White);
            familyButton.SetBounds(12, y, 196, 42);
            familyButton.Click += delegate
            {
                OpenWorkspace(false);
            };
            side.Controls.Add(familyButton);
            y += 48;
            var visualButton = Button("Ancestry and appearance", Color.FromArgb(0, 102, 103), Color.White);
            visualButton.SetBounds(12, y, 196, 42);
            visualButton.Click += delegate
            {
                OpenWorkspace(true);
            };
            side.Controls.Add(visualButton);
            y += 48;
            var researchButton = Button("DNA comparisons", Color.FromArgb(0, 102, 103), Color.White);
            researchButton.SetBounds(12, y, 196, 42);
            researchButton.Click += delegate
            {
                OpenWorkspacePath("/research#person=" + Uri.EscapeDataString(Person()));
            };
            side.Controls.Add(researchButton);
            y += 48;
            var dependencyButton = Button("Dependencies", Color.FromArgb(0, 102, 103), Color.White);
            dependencyButton.SetBounds(12, y, 196, 42);
            dependencyButton.Click += delegate
            {
                CloseWorkspace();
                ShowDependencies();
            };
            tips.SetToolTip(dependencyButton, "Versions, data statuses, updates and set-up");
            side.Controls.Add(dependencyButton);
            y += 48;
            var genomeToolsButton = Button("Genom-Visualisierung", Color.FromArgb(0, 102, 103), Color.White);
            genomeToolsButton.SetBounds(12, y, 196, 42);
            genomeToolsButton.Click += delegate
            {
                ShowVisualTools();
            };
            tips.SetToolTip(genomeToolsButton, "Select genome views, reload locally and start with a data set");
            side.Controls.Add(genomeToolsButton);
            y += 48;
            var pluginButton = Button("Plugins & sources", Color.FromArgb(0, 102, 103), Color.White);
            pluginButton.SetBounds(12, y, 196, 42);
            pluginButton.Click += delegate
            {
                OpenWorkspacePath("/plugins#person=" + Uri.EscapeDataString(Person()));
            };
            side.Controls.Add(pluginButton);
            side.AutoScroll = true;
            var bottom = Label("Local · Windows + Ubuntu\nOriginals are preserved\n\nWorkspace: " + root, 9, false);
            bottom.ForeColor = Color.FromArgb(161, 180, 201);
            bottom.SetBounds(12, y + 54, 196, 98);
            side.AutoScrollMinSize = new Size(0, y + 165);
            side.Controls.Add(bottom);
            var main = new Panel { Dock = DockStyle.Fill, Padding = new Padding(24, 20, 24, 14) };
            Controls.Add(main);
            main.BringToFront();
            var header = new Panel { Dock = DockStyle.Top, Height = 124 };
            main.Controls.Add(header);
            var title = Label("Dein DNA-Arbeitsplatz", 23, true);
            title.SetBounds(0, 0, 600, 44);
            header.Controls.Add(title);
            subtitle = Label("From the original to the comprehensible result. Choose a step and its inputs.", 10, false);
            subtitle.ForeColor = muted;
            subtitle.SetBounds(2, 48, 820, 30);
            header.Controls.Add(subtitle);
            person = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Width = 190 };
            string people = Path.Combine(root, "Profiles");
            var persons = Directory.Exists(people) ? Directory.GetDirectories(people).Select(Path.GetFileName).Where(x => x.StartsWith("P", StringComparison.Ordinal)).OrderBy(x => x).ToArray() : new string[] { "P001_Ich" };
            person.Items.AddRange(persons.Cast<object>().ToArray());
            if (person.Items.Count > 0)
                person.SelectedIndex = 0;
            person.SetBounds(0, 88, 170, 30);
            person.SelectedIndexChanged += delegate
            {
                RememberFields();
                sourceSelection.Clear();
                if (selected != null)
                    SelectTask(selected);
                RenderCards();
                SavePreferences();
            };
            header.Controls.Add(person);
            var addPerson = Button("+", Color.White, teal);
            addPerson.SetBounds(178, 85, 27, 33);
            addPerson.Click += delegate
            {
                NewPerson();
            };
            tips.SetToolTip(addPerson, "Create a new person with their own source database");
            header.Controls.Add(addPerson);
            var sourceButton = Button("Selecting Sources", Color.White, ink);
            sourceButton.SetBounds(830, 2, 170, 38);
            sourceButton.Click += delegate
            {
                ChooseSources();
            };
            header.Controls.Add(sourceButton);
            search = new TextBox { Width = 250 };
            search.SetBounds(208, 88, 265, 30);
            search.TextChanged += delegate
            {
                RenderCards();
            };
            tips.SetToolTip(search, "Browse steps, functions and tool names");
            header.Controls.Add(search);
            var all = Button("Alle Werkzeuge", Color.White, ink);
            all.SetBounds(489, 83, 142, 35);
            all.Click += delegate
            {
                CloseWorkspace();
                mode = "Werkzeuge";
                category = "All steps";
                ShowHistory(false);
                RenderCards();
                ShowWelcome();
            };
            header.Controls.Add(all);
            var flow = Button("Guided sequence", Color.White, ink);
            flow.SetBounds(643, 83, 148, 35);
            flow.Click += delegate
            {
                NavigateCategory("All steps");
            };
            header.Controls.Add(flow);
            var jobs = Button("Contracts", Color.White, ink);
            jobs.SetBounds(803, 83, 100, 35);
            jobs.Click += delegate
            {
                CloseWorkspace();
                ShowHistory(true);
                LoadHistory();
            };
            header.Controls.Add(jobs);
            var statusbar = new Panel { Dock = DockStyle.Bottom, Height = 32 };
            main.Controls.Add(statusbar);
            progressText = Label("Ready · No automatic analysis when opened", 9, false);
            progressText.Dock = DockStyle.Fill;
            statusbar.Controls.Add(progressText);
            progress = new ProgressBar { Dock = DockStyle.Right, Width = 150, Style = ProgressBarStyle.Continuous };
            statusbar.Controls.Add(progress);
            var logpanel = new Panel { Dock = DockStyle.Bottom, Height = 170, Padding = new Padding(0, 12, 0, 8) };
            main.Controls.Add(logpanel);
            log = new RichTextBox { Dock = DockStyle.Fill, ReadOnly = true, BackColor = nav, ForeColor = Color.FromArgb(195, 222, 220), BorderStyle = BorderStyle.None, Font = new Font("Consolas", 9), WordWrap = false };
            logpanel.Controls.Add(log);
            var loghead = Label("CONTRACT PROTOCOL · Commands, progress and errors remain on the SSD", 9, true);
            loghead.Dock = DockStyle.Top;
            loghead.Height = 26;
            logpanel.Controls.Add(loghead);
            var body = new SplitContainer { Dock = DockStyle.Fill, FixedPanel = FixedPanel.Panel2, SplitterWidth = 12, BackColor = paper };
            main.Controls.Add(body);
            body.BringToFront();
            body.SizeChanged += delegate
            {
                if (body.Width > S(660))
                {
                    body.Panel1MinSize = S(250);
                    body.Panel2MinSize = S(350);
                    body.SplitterDistance = Math.Min(body.Width - S(350) - body.SplitterWidth, Math.Max(S(270), body.Width - S(510)));
                }
            };
            listHost = new Panel { Dock = DockStyle.Fill };
            body.Panel1.Controls.Add(listHost);
            cards = new FlowLayoutPanel { Dock = DockStyle.Fill, FlowDirection = FlowDirection.TopDown, WrapContents = false, AutoScroll = true, Padding = new Padding(0, 4, 8, 0) };
            listHost.Controls.Add(cards);
            cards.SizeChanged += delegate
            {
                foreach (Control c in cards.Controls)
                    c.Width = Math.Max(S(280), cards.ClientSize.Width - S(27));
            };
            history = new DataGridView { Dock = DockStyle.Fill, ReadOnly = true, AllowUserToAddRows = false, AllowUserToDeleteRows = false, AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill, RowHeadersVisible = false, BackgroundColor = Color.White, BorderStyle = BorderStyle.None, SelectionMode = DataGridViewSelectionMode.FullRowSelect, Visible = false };
            history.Columns.Add("date", "Date");
            history.Columns.Add("title", "Job");
            history.Columns.Add("status", "Status");
            history.CellClick += delegate (object sender, DataGridViewCellEventArgs e)
            {
                if (e.RowIndex >= 0)
                {
                    viewJob = (string)history.Rows[e.RowIndex].Tag;
                    lastLog = "";
                    DisplayJob();
                }
            };
            listHost.Controls.Add(history);
            detail = new Panel { Dock = DockStyle.Fill, BackColor = Color.White, Padding = new Padding(20) };
            body.Panel2.Controls.Add(detail);
            var detailHead = new Panel { Dock = DockStyle.Top, Height = 134 };
            detail.Controls.Add(detailHead);
            detailTitle = Label("Select the step", 17, true);
            detailTitle.SetBounds(0, 0, 400, 62);
            detailTitle.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            detailHead.Controls.Add(detailTitle);
            var help = Button("?", Color.FromArgb(232, 246, 244), teal);
            help.SetBounds(412, 0, 34, 34);
            help.Anchor = AnchorStyles.Top | AnchorStyles.Right;
            help.Click += delegate
            {
                if (selected != null)
                    Help(selected);
            };
            detailHead.Controls.Add(help);
            tips.SetToolTip(help, "What does this step do? Click for explanation, prerequisites and tools.");
            detailSub = Label("", 10, false);
            detailSub.ForeColor = muted;
            detailSub.SetBounds(0, 68, 445, 62);
            detailSub.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            detailHead.Controls.Add(detailSub);
            var actions = new Panel { Dock = DockStyle.Bottom, Height = 119 };
            detail.Controls.Add(actions);
            run = Button("Start job", teal, Color.White);
            run.SetBounds(0, 0, 250, 40);
            run.Click += delegate
            {
                Run(false);
            };
            actions.Controls.Add(run);
            preview = Button("Preview command", Color.FromArgb(234, 240, 246), ink);
            preview.SetBounds(262, 0, 180, 40);
            preview.Click += delegate
            {
                Run(true);
            };
            actions.Controls.Add(preview);
            results = Button("Result folder", Color.FromArgb(234, 240, 246), ink);
            results.SetBounds(0, 50, 250, 36);
            results.Click += delegate
            {
                OpenResult();
            };
            actions.Controls.Add(results);
            cancel = Button("Cancellation of order", Color.FromArgb(255, 238, 235), Color.FromArgb(160, 61, 50));
            cancel.SetBounds(262, 50, 180, 36);
            cancel.Enabled = false;
            cancel.Click += delegate
            {
                if (activeJob != "")
                    File.WriteAllText(Path.Combine(activeJob, "abbrechen.request"), DateTime.Now.ToString("o"));
            };
            actions.Controls.Add(cancel);
            var note = Label("Own order per start. Closing the app does not stop running orders.", 8, false);
            note.ForeColor = muted;
            note.SetBounds(0, 92, 445, 25);
            actions.Controls.Add(note);
            inputs = new FlowLayoutPanel { Dock = DockStyle.Fill, AutoScroll = true, FlowDirection = FlowDirection.TopDown, WrapContents = false, Padding = new Padding(0, 4, 8, 0) };
            detail.Controls.Add(inputs);
            inputs.BringToFront();
            inputs.SizeChanged += delegate
            {
                foreach (Control c in inputs.Controls)
                    c.Width = Math.Max(S(280), inputs.ClientSize.Width - S(25));
            };
        }
        void ShowHistory(bool enabled)
        {
            history.Visible = enabled;
            cards.Visible = !enabled;
            if (enabled)
                history.BringToFront();
        }
        void RenderCards()
        {
            if (cards == null)
                return;
            cards.SuspendLayout();
            cards.Controls.Clear();
            foreach (var pair in categories)
            {
                pair.Value.BackColor = pair.Key == category ? Color.FromArgb(35, 76, 85) : nav;
                pair.Value.ForeColor = pair.Key == category ? Color.White : Color.FromArgb(202, 215, 229);
            }
            string term = search == null ? "" : search.Text.Trim();
            var items = catalog.tasks.Where(t => t.id != "import" && t.id != "archive_index" && (category == "All steps" || t.category == category) && (mode == "Werkzeuge" || category == "Tools & system" || t.step > 0 || t.category != "Tools & system") && (term == "" || (t.title + " " + t.tools + " " + t.description).IndexOf(term, StringComparison.OrdinalIgnoreCase) >= 0));
            foreach (TaskInfo task in items)
            {
                var card = new Panel { Width = Math.Max(280, cards.ClientSize.Width - 27), Height = 120, BackColor = Color.White, Margin = new Padding(0, 0, 0, 12), Cursor = Cursors.Hand, Padding = new Padding(12) };
                var number = Label(task.step > 0 ? task.step.ToString("00", System.Globalization.CultureInfo.InvariantCulture) : "•", 11, true);
                number.ForeColor = teal;
                number.BackColor = Color.FromArgb(231, 246, 243);
                number.TextAlign = ContentAlignment.MiddleCenter;
                number.SetBounds(12, 16, 42, 42);
                card.Controls.Add(number);
                var title = Label(task.title, 11, true);
                title.SetBounds(66, 15, card.Width - 112, 29);
                title.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
                card.Controls.Add(title);
                var desc = Label(task.description, 9, false);
                desc.ForeColor = muted;
                desc.SetBounds(66, 46, card.Width - 90, 39);
                desc.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
                card.Controls.Add(desc);
                var tool = Label(task.tools + "  ·  " + task.platform, 8, false);
                tool.ForeColor = teal;
                tool.SetBounds(66, 91, card.Width - 90, 18);
                tool.Anchor = AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
                card.Controls.Add(tool);
                var hint = Button("?", Color.FromArgb(238, 243, 247), muted);
                hint.SetBounds(card.Width - 39, 12, 27, 27);
                hint.Anchor = AnchorStyles.Top | AnchorStyles.Right;
                hint.Click += delegate
                {
                    Help(task);
                };
                card.Controls.Add(hint);
                tips.SetToolTip(hint, task.help);
                EventHandler pick = delegate
                {
                    SelectTask(task);
                };
                card.Click += pick;
                title.Click += pick;
                desc.Click += pick;
                tool.Click += pick;
                number.Click += pick;
                ScaleDynamic(card);
                card.Width = Math.Max(S(280), cards.ClientSize.Width - S(27));
                card.Tag = task.id;
                cards.Controls.Add(card);
            }
            cards.ResumeLayout();
            subtitle.Text = (mode == "Werkzeuge" ? "All functions and programs" : "Guided sequence") + " · " + cards.Controls.Count + "Entries ·" + Person() + " · " + sourceSelection.Count + "Source files selected";
        }
        string Person()
        {
            return person.SelectedItem == null ? "P001_Ich" : person.SelectedItem.ToString();
        }
        void NavigateCategory(string target)
        {
            CloseWorkspace();
            search.Text = "";
            if (target == "Import")
            {
                var menu = new ContextMenuStrip();
                menu.Items.Add("Check and import DNA files", null, delegate
                {
                    ShowImport();
                });
                menu.Items.Add("Import origin/feature result", null, delegate
                {
                    OpenWorkspacePath("/visual#person=" + Uri.EscapeDataString(Person()) + "&import=1");
                });
                menu.Show(categories["Import"], new Point(0, categories["Import"].Height));
                return;
            }
            category = target;
            mode = target == "Tools & system" ? "Werkzeuge" : "Ablauf";
            ShowHistory(false);
            RenderCards();
            var first = cards.Controls.Cast<Control>().FirstOrDefault();
            if (target == "All steps" || first == null)
                ShowWelcome();
            else
                SelectTask(catalog.tasks.First(t => t.id == (string)first.Tag));
        }
        void ShowWelcome()
        {
            RememberFields();
            selected = null;
            fields.Clear();
            inputs.Controls.Clear();
            detailTitle.Text = "Your workspace";
            detailSub.Text = "Select a category or work step on the left.";
            var intro = Label("Add files through Import.\n\nOpen the family tree, comparisons and ancestry views from the navigation.", 11, false);
            intro.Width = Math.Max(S(280), inputs.ClientSize.Width - S(25));
            intro.Height = S(220);
            inputs.Controls.Add(intro);
            run.Text = "Select the step";
            run.Enabled = false;
            preview.Enabled = false;
        }
        void SelectTask(TaskInfo task)
        {
            run.Enabled = worker == null || worker.HasExited;
            RememberFields();
            selected = task;
            editingPerson = Person();
            fields.Clear();
            inputs.Controls.Clear();
            detailTitle.Text = (task.step > 0 ? task.step.ToString("00", System.Globalization.CultureInfo.InvariantCulture) + " · " : "") + task.title;
            detailSub.Text = task.description + "\n" + task.tools + " · " + task.platform;
            run.Text = task.button;
            preview.Enabled = worker == null || worker.HasExited;
            foreach (Control c in cards.Controls)
                c.BackColor = (string)c.Tag == task.id ? Color.FromArgb(228, 245, 241) : Color.White;
            if (task.platform == "WSL" || task.kind == "launch")
            {
                var prepare = Button("Checking tools / installing them when necessary", Color.FromArgb(230, 245, 241), teal);
                prepare.Width = 420;
                prepare.Height = 42;
                prepare.Click += async delegate { await EnsureRequirements(task, true); };
                inputs.Controls.Add(prepare);
            }
            if (task.fields.Length == 0)
            {
                var intro = Label(task.help, 10, false);
                intro.Height = 200;
                intro.Width = 420;
                inputs.Controls.Add(intro);
            }
            foreach (Field f in task.fields)
            {
                var box = new Panel { Width = 420, Height = f.kind == "text" ? 118 : 100, Margin = new Padding(0, 0, 0, 13) };
                var title = Label(f.label + (f.required ? " *" : ""), 10, true);
                title.SetBounds(0, 0, 370, 29);
                title.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
                box.Controls.Add(title);
                var q = Button("?", Color.FromArgb(238, 243, 247), muted);
                q.SetBounds(388, 0, 26, 26);
                q.Anchor = AnchorStyles.Top | AnchorStyles.Right;
                q.Click += delegate
                {
                    TextDialog(f.label, f.help == "" ? task.help : f.help);
                };
                box.Controls.Add(q);
                tips.SetToolTip(q, f.help == "" ? task.help : f.help);
                Control edit;
                if (f.kind == "choice")
                {
                    var combo = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList };
                    combo.Items.AddRange(f.choices.Cast<object>().ToArray());
                    combo.SelectedIndex = 0;
                    if (!String.IsNullOrEmpty(f.@default))
                        combo.SelectedItem = f.@default;
                    edit = combo;
                }
                else
                {
                    var text = new TextBox { Text = f.@default ?? "", ReadOnly = f.kind == "file" || f.kind == "folder", Multiline = f.kind == "text", ScrollBars = f.kind == "text" ? ScrollBars.Vertical : ScrollBars.None };
                    if (f.kind == "text")
                        text.Height = 70;
                    edit = text;
                }
                edit.SetBounds(0, 34, f.kind == "file" || f.kind == "folder" ? 325 : 414, f.kind == "text" ? 70 : 29);
                edit.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
                box.Controls.Add(edit);
                fields[f.key] = edit;
                string pref = Person() + "/" + task.id + "/" + f.key;
                object savedChoice;
                if (choices.TryGetValue(pref, out savedChoice))
                {
                    edit.Tag = savedChoice;
                    edit.Text = savedChoice is object[]? String.Join("; ", ((object[])savedChoice).Select(x => x.ToString())) : Convert.ToString(savedChoice, System.Globalization.CultureInfo.InvariantCulture);
                }
                if (f.kind == "file" || f.kind == "folder")
                {
                    edit.Width = 235;
                    var library = Button("Sources", Color.FromArgb(230, 245, 241), teal);
                    library.SetBounds(244, 32, 80, 32);
                    library.Anchor = AnchorStyles.Top | AnchorStyles.Right;
                    library.Click += delegate
                    {
                        ChooseFieldSources(f, edit);
                    };
                    box.Controls.Add(library);
                    var browse = Button("File ...", Color.FromArgb(234, 240, 246), ink);
                    browse.SetBounds(334, 32, 80, 32);
                    browse.Anchor = AnchorStyles.Top | AnchorStyles.Right;
                    browse.Click += delegate
                    {
                        Browse(f, edit);
                    };
                    box.Controls.Add(browse);
                    var pathHint = Label(f.multi ? "Multiple selection possible · Originals are preserved" : "Full file path is stored locally", 8, false);
                    pathHint.ForeColor = muted;
                    pathHint.SetBounds(0, 72, 410, 24);
                    box.Controls.Add(pathHint);
                    tips.SetToolTip(edit, edit.Text);
                }
                ScaleDynamic(box);
                inputs.Controls.Add(box);
            }
            foreach (Control c in inputs.Controls)
                c.Width = Math.Max(S(280), inputs.ClientSize.Width - S(25));
        }
        void Browse(Field f, Control edit)
        {
            if (f.kind == "folder")
            {
                using (var d = new FolderBrowserDialog { Description = f.label, SelectedPath = Directory.Exists(edit.Text) ? edit.Text : Path.Combine(root, "Projects") })
                {
                    if (d.ShowDialog(this) == DialogResult.OK)
                    {
                        edit.Text = d.SelectedPath;
                        edit.Tag = d.SelectedPath;
                    }
                }
            }
            else
            {
                using (var d = new OpenFileDialog { Title = f.label, Multiselect = f.multi, CheckFileExists = true, Filter = "All files|*.*", InitialDirectory = Path.Combine(root, "Profiles") })
                {
                    if (d.ShowDialog(this) == DialogResult.OK)
                    {
                        edit.Text = String.Join("; ", d.FileNames);
                        edit.Tag = f.multi ? (object)d.FileNames : (object)d.FileName;
                        tips.SetToolTip(edit, edit.Text);
                    }
                }
            }
            RememberFields();
        }
        void RememberFields()
        {
            if (selected == null || person == null || editingPerson == "")
                return;
            foreach (var f in selected.fields)
            {
                Control c;
                if (fields.TryGetValue(f.key, out c))
                    choices[editingPerson + "/" + selected.id + "/" + f.key] = (f.kind == "file" || f.kind == "folder") ? (c.Tag ?? (object)c.Text) : (object)c.Text;
            }
        }
        async void Run(bool plan)
        {
            if (selected == null)
                return;
            if (!plan && selected.id == "import")
            {
                ShowImport();
                return;
            }
            if (!plan && selected.id == "archive_index")
            {
                ShowImport(true);
                return;
            }
            if (!plan && selected.id == "profile_view")
            {
                ShowProfile();
                return;
            }
            if (!plan && (selected.id == "family" || selected.id == "visual"))
            {
                OpenWorkspace(selected.id == "visual");
                return;
            }
            if (worker != null && !worker.HasExited)
            {
                MessageBox.Show(this, "There's an order already underway. You can track his protocol or cancel it.", "Order under way");
                return;
            }
            try
            {
                var values = new Dictionary<string, object>();
                foreach (var f in selected.fields)
                {
                    var c = fields[f.key];
                    object val = (f.kind == "file" || f.kind == "folder") ? (c.Tag ?? (object)c.Text) : (object)c.Text;
                    string text = c.Text.Trim();
                    if (f.required && (text == "" || text.StartsWith("Please select", StringComparison.Ordinal)))
                    {
                        MessageBox.Show(this, "Please select:" + f.label, "Eingabe fehlt");
                        c.Focus();
                        return;
                    }
                    values[f.key] = val;
                }
                RememberFields();
                SavePreferences();
                var task = selected;
                if (!plan && !await EnsureRequirements(task, false))
                    return;
                StartJob(task, values, plan);
            }
            catch (Exception e) { MessageBox.Show(this, e.Message, "Start not possible", MessageBoxButtons.OK, MessageBoxIcon.Error); }
        }
        void StartJob(TaskInfo task, Dictionary<string, object> values, bool plan)
        {
            if (worker != null && !worker.HasExited)
            {
                MessageBox.Show(this, "Please terminate or cancel the current order first.", "Order under way");
                return;
            }
            try
            {
                string name = DateTime.Now.ToString("yyyyMMdd-HHmmss", System.Globalization.CultureInfo.InvariantCulture) + "_" + task.id + "_" + Guid.NewGuid().ToString("N").Substring(0, 6);
                activeJob = Path.Combine(jobsroot, Person(), name);
                Directory.CreateDirectory(activeJob);
                viewJob = activeJob;
                lastLog = "";
                var request = new Dictionary<string, object> { { "task", task.id }, { "person", Person() }, { "inputs", values }, { "source_selection", sourceSelection.ToArray() } };
                string req = Path.Combine(activeJob, "inputs.json");
                File.WriteAllText(req, json.Serialize(request), new UTF8Encoding(false));
                var si = new ProcessStartInfo(python, Quote(Path.Combine(appdir, "engine.py")) + " " + Quote(req) + (plan ? " --preview" : "")) { UseShellExecute = false, CreateNoWindow = true, WorkingDirectory = root, RedirectStandardError = true };
                si.EnvironmentVariables["PYTHONNOUSERSITE"] = "1";
                si.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
                worker = new Process { StartInfo = si };
                worker.ErrorDataReceived += delegate (object s, DataReceivedEventArgs e)
                {
                    if (!String.IsNullOrEmpty(e.Data))
                        try
                        {
                            File.AppendAllText(Path.Combine(viewJob, "startfehler.log"), e.Data + Environment.NewLine);
                        }
                        catch { }
                };
                worker.Start();
                worker.BeginErrorReadLine();
                previewing = plan;
                run.Enabled = preview.Enabled = false;
                cancel.Enabled = !plan;
                progress.Style = ProgressBarStyle.Marquee;
                progressText.Text = (plan ? "Command Preview is created:" : "Order under way:") + task.title;
                log.Text = "Preparing job ...\n";
            }
            catch (Exception e) { MessageBox.Show(this, e.Message, "Start not possible", MessageBoxButtons.OK, MessageBoxIcon.Error); }
        }
        static string Quote(string s)
        {
            return "\"" + s.Replace("\"", "\\\"") + "\"";
        }
        public void OpenWorkspace(bool visual)
        {
            OpenWorkspacePath((visual ? "/visual" : "/") + "#person=" + Uri.EscapeDataString(Person()));
        }
        public async void OpenWorkspacePath(string path)
        {
            if (path.StartsWith("/visual-run/", StringComparison.Ordinal) && !path.Contains("?"))
                path += "?native=1";
            pendingPath = path;
            int generation = viewGeneration;
            try
            {
                if (workspace != null)
                {
                    workspace.BringToFront();
                    if (familyView != null && familyView.CoreWebView2 != null)
                        familyView.CoreWebView2.Navigate(familyBase + pendingPath);
                    return;
                }
                bool shell = path.StartsWith("/app", StringComparison.Ordinal);
                workspace = new Panel { Dock = DockStyle.Fill, BackColor = paper };
                Controls.Add(workspace);
                workspace.BringToFront();
                if (shell)
                    foreach (Control c in Controls)
                        if (c != workspace)
                            c.Hide();
                var bar = new FlowLayoutPanel { Dock = DockStyle.Top, Height = S(58), Padding = new Padding(S(10)) };
                workspace.Controls.Add(bar);
                if (shell)
                    bar.Visible = false;
                var back = Button("← Arbeitsablauf", nav, Color.White);
                back.Width = S(180);
                bar.Controls.Add(back);
                back.Click += delegate
                {
                    CloseWorkspace();
                };
                var tree = Button("Family tree & DNA", teal, Color.White);
                tree.Width = S(190);
                bar.Controls.Add(tree);
                tree.Click += delegate
                {
                    if (familyView != null && familyView.CoreWebView2 != null)
                        familyView.CoreWebView2.Navigate(familyBase + "/");
                };
                var map = Button("Ancestry and appearance", teal, Color.White);
                map.Width = S(200);
                bar.Controls.Add(map);
                map.Click += delegate
                {
                    if (familyView != null && familyView.CoreWebView2 != null)
                        familyView.CoreWebView2.Navigate(familyBase + "/visual");
                };
                var message = Label("Local view is started...", 10, false);
                message.Dock = DockStyle.Fill;
                message.TextAlign = ContentAlignment.MiddleCenter;
                workspace.Controls.Add(message);
                bar.BringToFront();
                if (familyServer == null || familyServer.HasExited)
                {
                    string folder = Path.Combine(root, "DNA_Software", "UserData", "Launcher", "Sitzungen", Guid.NewGuid().ToString("N"));
                    Directory.CreateDirectory(folder);
                    string info = Path.Combine(folder, "service.json");
                    var start = new ProcessStartInfo(python, Quote(Path.Combine(appdir, "family.py")) + " --embedded " + Quote(info)) { UseShellExecute = false, CreateNoWindow = true, RedirectStandardInput = true, RedirectStandardError = true, WorkingDirectory = root };
                    start.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
                    start.EnvironmentVariables["PYTHONNOUSERSITE"] = "1";
                    familyServer = new Process { StartInfo = start };
                    familyServer.ErrorDataReceived += delegate (object s, DataReceivedEventArgs e)
                    {
                        if (e.Data != null)
                            try
                            {
                                File.AppendAllText(Path.Combine(folder, "dienst.log"), e.Data + Environment.NewLine);
                            }
                            catch { }
                    };
                    familyServer.Start();
                    familyServer.BeginErrorReadLine();
                    for (int i = 0; i < 150 && !File.Exists(info); i++)
                    {
                        if (familyServer.HasExited)
                            throw new InvalidOperationException("The local family service could not start." + folder);
                        await Task.Delay(200);
                    }
                    if (!File.Exists(info))
                        throw new InvalidOperationException("Time-out at the start of the local family service.");
                    var config = json.Deserialize<Dictionary<string, object>>(File.ReadAllText(info));
                    familyBase = V(config, "url");
                }
                if (generation != viewGeneration || workspace == null || workspace.IsDisposed)
                    return;
                string fixedRuntime = Path.Combine(root, "DNA_Software", "Windows", "WebView2Runtime");
                if (Directory.Exists(fixedRuntime))
                {
                    string executable = Directory.GetFiles(fixedRuntime, "msedgewebview2.exe", SearchOption.AllDirectories).FirstOrDefault();
                    fixedRuntime = executable == null ? null : Path.GetDirectoryName(executable);
                }
                else
                    fixedRuntime = null;
                string userData = Path.GetFullPath(Path.Combine(root, "DNA_Software", "UserData", "Launcher", "WebView2"));
                Directory.CreateDirectory(userData);
                familyView = new WebView2 { Dock = DockStyle.Fill, CreationProperties = new CoreWebView2CreationProperties { UserDataFolder = userData, BrowserExecutableFolder = fixedRuntime } };
                workspace.Controls.Add(familyView);
                familyView.BringToFront();
                bar.BringToFront();
                var thisView = familyView;
                await thisView.EnsureCoreWebView2Async();
                if (generation != viewGeneration || thisView.IsDisposed || thisView != familyView)
                    return;
                string assets = Path.Combine(root, "DNA_Software", "Windows", "VisualTools");
                Directory.CreateDirectory(assets);
                familyView.CoreWebView2.SetVirtualHostNameToFolderMapping("dna-assets.local", assets, CoreWebView2HostResourceAccessKind.Allow);
                familyView.CoreWebView2.AddWebResourceRequestedFilter("*", CoreWebView2WebResourceContext.All);
                familyView.CoreWebView2.WebResourceRequested += delegate (object s, CoreWebView2WebResourceRequestedEventArgs e)
                {
                    Uri target;
                    if (Uri.TryCreate(e.Request.Uri, UriKind.Absolute, out target) && (target.Scheme == "https" || target.Scheme == "http") && target.GetLeftPart(UriPartial.Authority) != familyBase && target.Host != "dna-assets.local")
                        e.Response = thisView.CoreWebView2.Environment.CreateWebResourceResponse(new MemoryStream(Array.Empty<byte>()), 403, "Only local resources allowed", "Content-Type: text/plain");
                };
                familyView.CoreWebView2.NavigationStarting += delegate (object s, CoreWebView2NavigationStartingEventArgs e)
                {
                    Uri target;
                    if (Uri.TryCreate(e.Uri, UriKind.Absolute, out target) && target.GetLeftPart(UriPartial.Authority) != familyBase && e.Uri != "about:blank")
                    {
                        e.Cancel = true;
                        if (e.IsUserInitiated && (target.Scheme == "https" || target.Scheme == "http"))
                            Process.Start(new ProcessStartInfo(e.Uri) { UseShellExecute = true });
                    }
                };
                familyView.CoreWebView2.NewWindowRequested += delegate (object s, CoreWebView2NewWindowRequestedEventArgs e)
                {
                    e.Handled = true;
                    if (e.IsUserInitiated && e.Uri.StartsWith("https://", StringComparison.Ordinal))
                        Process.Start(new ProcessStartInfo(e.Uri) { UseShellExecute = true });
                };
                familyView.CoreWebView2.WebMessageReceived += delegate (object sender, CoreWebView2WebMessageReceivedEventArgs e)
                {
                    try
                    {
                        Uri origin;
                        if (!Uri.TryCreate(e.Source, UriKind.Absolute, out origin) || origin.GetLeftPart(UriPartial.Authority) != familyBase || (origin.AbsolutePath != "/research" && origin.AbsolutePath != "/plugins" && origin.AbsolutePath != "/app"))
                            return;
                        var request = json.Deserialize<Dictionary<string, object>>(e.TryGetWebMessageAsString());
                        if (origin.AbsolutePath == "/app")
                        {
                            ModernMessage(thisView, request);
                            return;
                        }
                        if (V(request, "action") == "open-visual-tools")
                        {
                            BeginInvoke(new Action(delegate
                            {
                                string profile = V(request, "person");
                                if (person.Items.Contains(profile))
                                    person.SelectedItem = profile;
                                ShowVisualTools();
                            }));
                            return;
                        }
                        string taskId = V(request, "task");
                        if (V(request, "action") != "workbench-task" || !AllowedToolViewTasks.Contains(taskId))
                            return;
                        var task = catalog.tasks.FirstOrDefault(t => t.id == taskId);
                        if (task == null)
                        {
                            MessageBox.Show(this, "This workflow is not yet set up in the current catalog.", "DNA Workbench");
                            return;
                        }
                        if (IsModernShell())
                        {
                            familyView.CoreWebView2.PostWebMessageAsJson(json.Serialize(new Dictionary<string, object> { { "action", "suite-navigate" }, { "task", taskId }, { "person", V(request, "person") } }));
                            return;
                        }
                        BeginInvoke(new Action(delegate
                        {
                            string profile = V(request, "person");
                            if (person.Items.Contains(profile))
                                person.SelectedItem = profile;
                            NavigateCategory(task.category);
                            SelectTask(task);
                            string chosen = V(request, "file");
                            Control value;
                            if (!String.IsNullOrEmpty(chosen) && File.Exists(chosen) && fields.TryGetValue("vcf", out value) && value is TextBox)
                                ((TextBox)value).Text = chosen;
                        }));
                    }
                    catch (Exception error) { MessageBox.Show(this, error.Message, "Opening up the workflow"); }
                };
                familyView.CoreWebView2.Navigate(familyBase + pendingPath);
                message.Dispose();
            }
            catch (Exception e) { if (generation != viewGeneration || IsDisposed) return; MessageBox.Show(this, "The integrated view could not start:\n" + e.Message, "DNA Workbench"); CloseWorkspace(); }
        }
        void CloseWorkspace()
        {
            viewGeneration++;
            var oldView = familyView;
            var oldPanel = workspace;
            familyView = null;
            workspace = null;
            if (oldPanel != null)
            {
                oldPanel.Hide();
                Controls.Remove(oldPanel);
            }
            try
            {
                if (oldView != null)
                    oldView.Dispose();
            }
            catch (Exception e) { try { File.AppendAllText(Path.Combine(appdir, "navigation.log"), e.Message + Environment.NewLine); } catch { } }
            if (oldPanel != null)
                try
                {
                    oldPanel.Dispose();
                }
                catch { }
            foreach (Control c in Controls)
                c.Show();
        }
        void Tick(object sender, EventArgs e)
        {
            DisplayJob();
            if (worker != null && worker.HasExited)
            {
                bool ok = worker.ExitCode == 0;
                worker.Dispose();
                worker = null;
                run.Enabled = preview.Enabled = true;
                cancel.Enabled = false;
                progress.Style = ProgressBarStyle.Continuous;
                progressText.Text = ok ? (previewing ? "Previewed. No analysis was started." : "Results folder and protocol are available.") : "Job unsuccessful. Check notes in the log / starter error.log.";
                if (previewing && ok)
                {
                    string p = Path.Combine(activeJob, "command.txt");
                    if (File.Exists(p))
                        TextDialog("Command Preview — not yet executed", File.ReadAllText(p, Encoding.UTF8));
                }
                if (history.Visible)
                    LoadHistory();
            }
        }
        void DisplayJob()
        {
            if (String.IsNullOrEmpty(viewJob))
                return;
            string file = Path.Combine(viewJob, "auftrag.log");
            try
            {
                if (File.Exists(file))
                {
                    string text;
                    using (var stream = new FileStream(file, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete))
                    {
                        if (stream.Length > 100000)
                            stream.Seek(-100000, SeekOrigin.End);
                        using (var reader = new StreamReader(stream, Encoding.UTF8))
                            text = reader.ReadToEnd();
                    }
                    if (text != lastLog)
                    {
                        bool follow = log.SelectionStart + log.SelectionLength >= log.TextLength - 3;
                        log.Text = text;
                        lastLog = text;
                        if (follow)
                        {
                            log.SelectionStart = log.TextLength;
                            log.ScrollToCaret();
                        }
                    }
                }
            }
            catch (IOException) { }
        }
        void LoadHistory()
        {
            history.Rows.Clear();
            var entries = new List<Tuple<string, Dictionary<string, object>>>();
            foreach (string file in Directory.GetFiles(jobsroot, "status.json", SearchOption.AllDirectories))
                try
                {
                    var j = json.Deserialize<Dictionary<string, object>>(File.ReadAllText(file, Encoding.UTF8));
                    if (Convert.ToString(j["person"], System.Globalization.CultureInfo.InvariantCulture) == Person())
                        entries.Add(Tuple.Create(Path.GetDirectoryName(file), j));
                }
                catch { }
            foreach (var entry in entries.OrderByDescending(x => Convert.ToString(x.Item2["started"], System.Globalization.CultureInfo.InvariantCulture)).Take(200))
            {
                var j = entry.Item2;
                int i = history.Rows.Add(Convert.ToString(j["started"], System.Globalization.CultureInfo.InvariantCulture), Convert.ToString(j["title"], System.Globalization.CultureInfo.InvariantCulture), Convert.ToString(j["status"], System.Globalization.CultureInfo.InvariantCulture));
                history.Rows[i].Tag = entry.Item1;
            }
            subtitle.Text = "Orders and results ·" + Person() + "· Clicking on an order shows its protocol.";
        }
        void OpenResult()
        {
            string dir = viewJob == "" ? jobsroot : Path.Combine(viewJob, "Results");
            if (!Directory.Exists(dir))
                dir = viewJob == "" ? jobsroot : viewJob;
            Process.Start("explorer.exe", Quote(dir));
        }
        string QueryEngine(string args)
        {
            UseWaitCursor = true;
            try
            {
                var si = new ProcessStartInfo(python, Quote(Path.Combine(appdir, "engine.py")) + " " + args) { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true, StandardOutputEncoding = Encoding.UTF8, StandardErrorEncoding = Encoding.UTF8 };
                si.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
                using (var p = Process.Start(si))
                {
                    string output = p.StandardOutput.ReadToEnd();
                    string error = p.StandardError.ReadToEnd();
                    p.WaitForExit();
                    if (p.ExitCode != 0)
                        throw new InvalidOperationException(error);
                    return output.Trim();
                }
            }
            finally { UseWaitCursor = false; }
        }
        List<Dictionary<string, object>> ReadLibrary()
        {
            return json.Deserialize<List<Dictionary<string, object>>>(QueryEngine("--library " + Quote(Person())));
        }
        static string V(Dictionary<string, object> row, string key)
        {
            object value;
            return row.TryGetValue(key, out value) && value != null ? Convert.ToString(value, System.Globalization.CultureInfo.InvariantCulture) : "";
        }
        void NewPerson()
        {
            using (var f = new Form { Text = "Neue Person", ClientSize = new Size(480, 165), StartPosition = FormStartPosition.CenterParent, Font = new Font("Segoe UI", 10), FormBorderStyle = FormBorderStyle.FixedDialog, MaximizeBox = false, MinimizeBox = false, AutoScaleMode = AutoScaleMode.Dpi, AutoScaleDimensions = new SizeF(96, 96) })
            {
                var label = Label("Name or pseudonym for your own database", 10, true);
                label.SetBounds(18, 16, 440, 28);
                f.Controls.Add(label);
                var name = new TextBox();
                name.SetBounds(18, 53, 440, 28);
                f.Controls.Add(name);
                var ok = Button("Add person", teal, Color.White);
                ok.SetBounds(268, 102, 190, 38);
                ok.DialogResult = DialogResult.OK;
                f.AcceptButton = ok;
                f.Controls.Add(ok);
                if (f.ShowDialog(this) == DialogResult.OK && name.Text.Trim() != "")
                {
                    try
                    {
                        string id = QueryEngine("--new-person " + Quote(name.Text.Trim()));
                        person.Items.Add(id);
                        person.SelectedItem = id;
                    }
                    catch (Exception e) { MessageBox.Show(this, e.Message, "Person could not be created"); }
                }
            }
        }
        void ShowImport(bool existing = false)
        {
            using (var f = new Form { Text = "Check files and import them locally ·" + Person(), ClientSize = new Size(980, 650), MinimumSize = new Size(780, 520), StartPosition = FormStartPosition.CenterParent, Font = new Font("Segoe UI", 10), BackColor = paper, AutoScaleMode = AutoScaleMode.Dpi, AutoScaleDimensions = new SizeF(96, 96) })
            {
                var tabs = new TabControl { Dock = DockStyle.Fill };
                var sourceTab = new TabPage("1 · Files and source");
                var checkTab = new TabPage("2 · Test result per file");
                tabs.TabPages.Add(sourceTab);
                tabs.TabPages.Add(checkTab);
                f.Controls.Add(tabs);
                var footerPanel = new Panel { Dock = DockStyle.Bottom, Height = 100, Padding = new Padding(15) };
                f.Controls.Add(footerPanel);
                var status = Label("Select files, check them and see the result. There is no upload to the Internet.", 9, false);
                status.SetBounds(15, 58, 920, 34);
                status.Anchor = AnchorStyles.Left | AnchorStyles.Right | AnchorStyles.Bottom;
                footerPanel.Controls.Add(status);
                var check = Button("1 · Checking files", Color.White, ink);
                check.SetBounds(15, 9, 230, 40);
                footerPanel.Controls.Add(check);
                var import = Button("2 · Datensatz importieren", teal, Color.White);
                import.SetBounds(660, 9, 280, 40);
                import.Anchor = AnchorStyles.Top | AnchorStyles.Right;
                import.Enabled = false;
                footerPanel.Controls.Add(import);
                var table = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(18), ColumnCount = 2, RowCount = 9 };
                table.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 200));
                table.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
                sourceTab.Controls.Add(table);
                var provider = new ComboBox { Dock = DockStyle.Fill, DropDownStyle = ComboBoxStyle.DropDownList };
                provider.Items.AddRange(json.Deserialize<string[]>(QueryEngine("--providers")).Cast<object>().ToArray());
                provider.SelectedIndex = 0;
                var dataset = new TextBox { Dock = DockStyle.Fill, Text = existing ? "Existing profile archive" : "Import " + DateTime.Now.ToString("dd.MM.yyyy HH:mm", System.Globalization.CultureInfo.InvariantCulture) };
                var build = new ComboBox { Dock = DockStyle.Fill, DropDownStyle = ComboBoxStyle.DropDownList };
                build.Items.AddRange(new object[] { "Unknown", "GRCh37", "GRCh38" });
                build.SelectedIndex = 0;
                var measure = new ComboBox { Dock = DockStyle.Fill, DropDownStyle = ComboBoxStyle.DropDownList };
                measure.Items.AddRange(new object[] { "Unknown / mixed", "Measured", "Imputed", "Phased/derived" });
                measure.SelectedIndex = 0;
                var note = new TextBox { Dock = DockStyle.Fill };
                var storage = new ComboBox { Dock = DockStyle.Fill, DropDownStyle = ComboBoxStyle.DropDownList };
                storage.Items.AddRange(new object[] { "Move · Remove after checked import at source location", "Kopieren · Quelldateien am bisherigen Ort behalten" });
                storage.SelectedIndex = 0;
                tips.SetToolTip(storage, "Ziel: " + Path.Combine(root, "Profiles", Person(), "Sources") + "Identical file bytes are not re-stored. Archive files are registered at the existing location.");
                string[] labels = { "Platform / Provider *", "Datensatzname", "Build-Angabe (optional)", "Genotype origin", "Notiz / Kit / Probe", "File handling" };
                Control[] edits = { provider, dataset, build, measure, note, storage };
                for (int i = 0; i < labels.Length; i++)
                {
                    table.RowStyles.Add(new RowStyle(SizeType.Absolute, 38));
                    var l = Label(labels[i], 10, false);
                    l.Dock = DockStyle.Fill;
                    table.Controls.Add(l, 0, i);
                    table.Controls.Add(edits[i], 1, i);
                }
                var files = new ListBox { Dock = DockStyle.Fill, HorizontalScrollbar = true, SelectionMode = SelectionMode.MultiExtended };
                table.Controls.Add(files, 0, 6);
                table.SetColumnSpan(files, 2);
                table.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
                if (existing)
                {
                    string dir = Path.Combine(root, "Profiles", Person(), "Sources");
                    if (Directory.Exists(dir))
                        foreach (string p in Directory.GetFiles(dir, "*", SearchOption.AllDirectories).Where(x => !x.Contains("Imports") && !x.EndsWith(".importing", StringComparison.Ordinal)))
                            files.Items.Add(p);
                }
                var tools = new FlowLayoutPanel { Dock = DockStyle.Fill };
                var add = Button("Add files ...", Color.White, ink);
                add.Width = 200;
                tools.Controls.Add(add);
                var clear = Button("Liste leeren", Color.White, ink);
                clear.Width = 140;
                tools.Controls.Add(clear);
                table.Controls.Add(tools, 0, 7);
                table.SetColumnSpan(tools, 2);
                table.RowStyles.Add(new RowStyle(SizeType.Absolute, 48));
                var explain = Label("Automatic: header, content and structure recognition. File names are hints only. A hosting platform such as Sequencing.com or GEDmatch may contain data from another original laboratory. Unproven origin remains unknown.", 9, false);
                explain.Dock = DockStyle.Fill;
                table.Controls.Add(explain, 0, 8);
                table.SetColumnSpan(explain, 2);
                table.RowStyles.Add(new RowStyle(SizeType.Absolute, 76));
                var grid = new DataGridView { Dock = DockStyle.Fill, ReadOnly = true, AllowUserToAddRows = false, RowHeadersVisible = false, AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.DisplayedCells, AutoSizeRowsMode = DataGridViewAutoSizeRowsMode.AllCells, BackgroundColor = Color.White };
                grid.Columns.Add("quality", "Quality");
                grid.Columns[0].Width = 110;
                grid.Columns[0].AutoSizeMode = DataGridViewAutoSizeColumnMode.None;
                foreach (string c in new string[] { "File", "Recognised source", "Format", "Build", "Genotypen", "QC points", "Erkennung / Hinweise" })
                    grid.Columns.Add(c, c);
                grid.Columns[7].AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill;
                grid.CellPainting += PaintQuality;
                checkTab.Controls.Add(grid);
                grid.ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.AutoSize;
                grid.Columns.Add("scope", "Datenumfang / Testart");
                grid.Columns["scope"].AutoSizeMode = DataGridViewAutoSizeColumnMode.None;
                grid.Columns["scope"].Width = 390;
                grid.Columns[7].MinimumWidth = 220;
                grid.CellDoubleClick += delegate (object s, DataGridViewCellEventArgs e)
                {
                    if (e.RowIndex >= 0)
                        TextDialog("File verification", json.Serialize(grid.Rows[e.RowIndex].Tag));
                };
                string checkFolder = Path.Combine(root, "Projects", "Source verification", Person(), Guid.NewGuid().ToString("N"));
                Directory.CreateDirectory(checkFolder);
                Process checking = null;
                bool approved = false;
                Action invalidate = delegate
                {
                    approved = false;
                    import.Enabled = false;
                    status.Text = "Selection changed: Check files before importing.";
                };
                provider.SelectedIndexChanged += delegate
                {
                    invalidate();
                };
                build.SelectedIndexChanged += delegate
                {
                    invalidate();
                };
                measure.SelectedIndexChanged += delegate
                {
                    invalidate();
                };
                add.Click += delegate
                {
                    using (var d = new OpenFileDialog { Multiselect = true, Title = "Files of a data set", Filter = "All files|*.*", InitialDirectory = Path.Combine(root, "Profiles", Person(), "Sources") })
                        if (d.ShowDialog(f) == DialogResult.OK)
                        {
                            foreach (string p in d.FileNames)
                                if (!files.Items.Contains(p))
                                    files.Items.Add(p);
                            invalidate();
                        }
                };
                clear.Click += delegate
                {
                    files.Items.Clear();
                    invalidate();
                };
                var poll = new System.Windows.Forms.Timer { Interval = 700 };
                check.Click += delegate
                {
                    if (files.Items.Count == 0)
                    {
                        MessageBox.Show(f, "Please select at least one file.");
                        return;
                    }
                    string request = Path.Combine(checkFolder, "pruefanfrage.json");
                    File.WriteAllText(request, json.Serialize(new Dictionary<string, object> { { "person", Person() }, { "files", files.Items.Cast<string>().ToArray() } }), new UTF8Encoding(false));
                    var si = new ProcessStartInfo(python, Quote(Path.Combine(appdir, "engine.py")) + " --inspect " + Quote(request)) { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
                    si.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
                    checking = new Process { StartInfo = si };
                    checking.OutputDataReceived += delegate
                    {
                    };
                    checking.ErrorDataReceived += delegate (object a, DataReceivedEventArgs b)
                    {
                        if (b.Data != null)
                            File.AppendAllText(Path.Combine(checkFolder, "fehler.log"), b.Data + Environment.NewLine);
                    };
                    checking.Start();
                    checking.BeginOutputReadLine();
                    checking.BeginErrorReadLine();
                    check.Enabled = add.Enabled = clear.Enabled = false;
                    status.Text = "Content and checksums are checked. Large files take time.";
                    import.Enabled = false;
                    poll.Start();
                };
                poll.Tick += delegate
                {
                    if (checking == null)
                        return;
                    if (!checking.HasExited)
                    {
                        try
                        {
                            string p = Path.Combine(checkFolder, "inspection-status.json");
                            if (File.Exists(p))
                            {
                                var r = json.Deserialize<Dictionary<string, object>>(File.ReadAllText(p, Encoding.UTF8));
                                status.Text = V(r, "completed") + " / " + V(r, "total") + "checked ·" + V(r, "last_file");
                            }
                        }
                        catch { }
                        return;
                    }
                    poll.Stop();
                    check.Enabled = add.Enabled = clear.Enabled = true;
                    if (checking.ExitCode != 0)
                    {
                        status.Text = "Test failed. See" + Path.Combine(checkFolder, "fehler.log");
                        return;
                    }
                    var report = json.Deserialize<Dictionary<string, object>>(File.ReadAllText(Path.Combine(checkFolder, "inspection.json"), Encoding.UTF8));
                    var records = json.ConvertToType<List<Dictionary<string, object>>>(report["files"]);
                    grid.Rows.Clear();
                    approved = true;
                    foreach (var r in records)
                    {
                        bool mismatch = build.Text != "Unknown" && V(r, "build") != "" && V(r, "build") != build.Text;
                        if (mismatch || V(r, "color") == "red" || V(r, "color") == "black")
                            approved = false;
                        var issues = json.ConvertToType<string[]>(r["issues"]);
                        int n = grid.Rows.Add("", V(r, "name"), V(r, "provider"), V(r, "format"), V(r, "build"), V(r, "called_points"), r["qc_supported_points"] == null ? "Not available" : V(r, "qc_supported_points"), String.Join(" · ", issues) + (mismatch ? " · MANUELLE BUILD-ANGABE WIDERSPRICHT DEM HEADER" : ""));
                        grid.Rows[n].Tag = r;
                        grid.Rows[n].Height = Math.Max(grid.Rows[n].Height, 44);
                        object scopeData;
                        if (r.TryGetValue("data_scope", out scopeData))
                        {
                            var scope = json.ConvertToType<Dictionary<string, object>>(scopeData);
                            grid.Rows[n].Cells["scope"].Value = V(scope, "summary");
                            grid.Rows[n].Cells["scope"].ToolTipText = json.Serialize(scope);
                        }
                    }
                    import.Enabled = approved;
                    tabs.SelectedTab = checkTab;
                    status.Text = approved ? "Verify origin / build; after that import is possible. Green is not a guarantee for a complete genome." : "Import stopped: check red/black findings or conflicting build information.";
                };
                import.Click += delegate
                {
                    if (!approved)
                        return;
                    if (worker != null && !worker.HasExited)
                    {
                        MessageBox.Show(f, "Please finish the current order first.");
                        return;
                    }
                    var vals = new Dictionary<string, object> { { "files", files.Items.Cast<string>().ToArray() }, { "provider", provider.Text }, { "label", dataset.Text }, { "declared_build", build.Text }, { "measurement", measure.Text }, { "note", note.Text }, { "checked_folder", checkFolder }, { "storage_mode", storage.SelectedIndex == 0 ? "move" : "copy" } };
                    f.Close();
                    StartJob(catalog.tasks.First(t => t.id == "import"), vals, false);
                };
                f.FormClosed += delegate
                {
                    poll.Stop();
                    poll.Dispose();
                };
                f.ShowDialog(this);
            }
        }
        void LegacyImport()
        {
            using (var f = new Form { Text = "Import DNA files locally ·" + Person(), ClientSize = new Size(880, 620), MinimumSize = new Size(720, 500), StartPosition = FormStartPosition.CenterParent, Font = new Font("Segoe UI", 10), BackColor = paper, AutoScaleMode = AutoScaleMode.Dpi, AutoScaleDimensions = new SizeF(96, 96) })
            {
                var table = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(22), ColumnCount = 2, RowCount = 10 };
                table.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 210));
                table.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
                f.Controls.Add(table);
                var info = Label("Local import to the SSD. Multiple files form a record with one vendor. For another vendor, you can import again.", 11, true);
                info.Dock = DockStyle.Fill;
                table.Controls.Add(info, 0, 0);
                table.SetColumnSpan(info, 2);
                table.RowStyles.Add(new RowStyle(SizeType.Absolute, 66));
                var provider = new ComboBox { Dock = DockStyle.Fill, DropDownStyle = ComboBoxStyle.DropDown };
                provider.Items.AddRange(new object[] { "Nebula", "Sequencing.com", "23andMe", "MyHeritage", "National Geographic", "Andere" });
                provider.SelectedIndex = 0;
                var dataset = new TextBox { Dock = DockStyle.Fill, Text = "Import " + DateTime.Now.ToString("dd.MM.yyyy HH:mm", System.Globalization.CultureInfo.InvariantCulture) };
                var build = new ComboBox { Dock = DockStyle.Fill, DropDownStyle = ComboBoxStyle.DropDownList };
                build.Items.AddRange(new object[] { "Unknown", "GRCh37", "GRCh38" });
                build.SelectedIndex = 0;
                var measure = new ComboBox { Dock = DockStyle.Fill, DropDownStyle = ComboBoxStyle.DropDownList };
                measure.Items.AddRange(new object[] { "Unknown / mixed", "Measured", "Imputed", "Phased/derived" });
                measure.SelectedIndex = 0;
                var note = new TextBox { Dock = DockStyle.Fill };
                string[] labels = { "Provider *", "Datensatzname", "Reference build", "Messart", "Notiz / Probe / Kit" };
                Control[] edits = { provider, dataset, build, measure, note };
                for (int i = 0; i < labels.Length; i++)
                {
                    table.RowStyles.Add(new RowStyle(SizeType.Absolute, 39));
                    var l = Label(labels[i], 10, false);
                    l.Dock = DockStyle.Fill;
                    table.Controls.Add(l, 0, i + 1);
                    table.Controls.Add(edits[i], 1, i + 1);
                }
                var fileList = new ListBox { Dock = DockStyle.Fill, HorizontalScrollbar = true, SelectionMode = SelectionMode.MultiExtended };
                table.Controls.Add(fileList, 0, 6);
                table.SetColumnSpan(fileList, 2);
                table.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
                var buttons = new FlowLayoutPanel { Dock = DockStyle.Fill };
                var choose = Button("Add files ...", Color.White, ink);
                choose.Width = 200;
                buttons.Controls.Add(choose);
                var clear = Button("Clear selection", Color.White, ink);
                clear.Width = 150;
                buttons.Controls.Add(clear);
                table.Controls.Add(buttons, 0, 7);
                table.SetColumnSpan(buttons, 2);
                table.RowStyles.Add(new RowStyle(SizeType.Absolute, 47));
                choose.Click += delegate
                {
                    using (var d = new OpenFileDialog { Multiselect = true, Title = "Files of this provider dataset", Filter = "All DNA files and reports|*.*", InitialDirectory = Path.Combine(root, "Profiles", Person(), "Sources") })
                        if (d.ShowDialog(f) == DialogResult.OK)
                            foreach (string path in d.FileNames)
                                if (!fileList.Items.Contains(path))
                                    fileList.Items.Add(path);
                };
                clear.Click += delegate
                {
                    fileList.Items.Clear();
                };
                var footer = Label("Originals outside the personal archive are copied; existing originals are registered at the previous location; identical file bytes are recognized; genotypes are brought together only in a separate step.", 9, false);
                footer.Dock = DockStyle.Fill;
                table.Controls.Add(footer, 0, 8);
                table.SetColumnSpan(footer, 2);
                table.RowStyles.Add(new RowStyle(SizeType.Absolute, 64));
                var import = Button("Import dataset", teal, Color.White);
                import.Dock = DockStyle.Right;
                import.Width = 240;
                table.Controls.Add(import, 1, 9);
                table.RowStyles.Add(new RowStyle(SizeType.Absolute, 43));
                import.Click += delegate
                {
                    if (fileList.Items.Count == 0 || provider.Text.Trim() == "")
                    {
                        MessageBox.Show(f, "Please select provider and at least one file.");
                        return;
                    }
                    var vals = new Dictionary<string, object> { { "files", fileList.Items.Cast<string>().ToArray() }, { "provider", provider.Text.Trim() }, { "label", dataset.Text.Trim() }, { "declared_build", build.Text }, { "measurement", measure.Text }, { "note", note.Text } };
                    f.DialogResult = DialogResult.OK;
                    f.Close();
                    StartJob(catalog.tasks.First(t => t.id == "import"), vals, false);
                };
                f.ShowDialog(this);
            }
        }
        List<Dictionary<string, object>> LibraryDialog(bool single, bool fieldMode)
        {
            List<Dictionary<string, object>> rows;
            try
            {
                rows = ReadLibrary();
            }
            catch (Exception e) { MessageBox.Show(this, e.Message, "Source register not available"); return null; }
            var chosen = new HashSet<string>(fieldMode ? (IEnumerable<string>)Array.Empty<string>() : (IEnumerable<string>)sourceSelection, StringComparer.OrdinalIgnoreCase);
            var result = new List<Dictionary<string, object>>();
            bool importNext = false, indexNext = false;
            using (var f = new Form { Text = "Source database ·" + Person(), ClientSize = new Size(1120, 650), MinimumSize = new Size(850, 500), StartPosition = FormStartPosition.CenterParent, Font = new Font("Segoe UI", 10), AutoScaleMode = AutoScaleMode.Dpi, AutoScaleDimensions = new SizeF(96, 96), BackColor = paper })
            {
                var top = new FlowLayoutPanel { Dock = DockStyle.Top, Height = 85, Padding = new Padding(14) };
                f.Controls.Add(top);
                var provider = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Width = 230 };
                provider.Items.Add("All providers");
                provider.Items.AddRange(rows.Select(r => V(r, "provider")).Distinct().OrderBy(x => x).Cast<object>().ToArray());
                provider.SelectedIndex = 0;
                top.Controls.Add(provider);
                var selectedOnly = new CheckBox { Text = "Only current source selection", AutoSize = true, Checked = fieldMode && sourceSelection.Count > 0, Enabled = sourceSelection.Count > 0 };
                top.Controls.Add(selectedOnly);
                var mark = Button("Sichtbare markieren", Color.White, ink);
                mark.Width = 185;
                top.Controls.Add(mark);
                var unmark = Button("Clear selection", Color.White, ink);
                unmark.Width = 160;
                top.Controls.Add(unmark);
                var grid = new DataGridView { Dock = DockStyle.Fill, AllowUserToAddRows = false, AllowUserToDeleteRows = false, AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.DisplayedCells, RowHeadersVisible = false, BackgroundColor = Color.White, BorderStyle = BorderStyle.None, SelectionMode = DataGridViewSelectionMode.FullRowSelect };
                grid.Columns.Add(new DataGridViewCheckBoxColumn { Name = "pick", HeaderText = "Selection", Width = 65 });
                grid.Columns.Add("quality", "Quality");
                grid.Columns[1].Width = 110;
                grid.Columns[1].AutoSizeMode = DataGridViewAutoSizeColumnMode.None;
                grid.CellPainting += PaintQuality;
                foreach (string c in new string[] { "Provider", "Dataset", "File", "Format", "Build", "Messart", "MiB", "Variantenindex", "QC points" })
                    grid.Columns.Add(c, c);
                foreach (DataGridViewColumn col in grid.Columns)
                    col.ReadOnly = col.Index != 0;
                grid.Columns[4].AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill;
                grid.AutoSizeRowsMode = DataGridViewAutoSizeRowsMode.AllCells;
                grid.ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.AutoSize;
                grid.Columns.Add("scope", "Datenumfang / Testart");
                grid.Columns["scope"].AutoSizeMode = DataGridViewAutoSizeColumnMode.None;
                grid.Columns["scope"].Width = 390;
                grid.Columns["scope"].ReadOnly = true;
                f.Controls.Add(grid);
                grid.BringToFront();
                var bottom = new FlowLayoutPanel { Dock = DockStyle.Bottom, Height = 110, Padding = new Padding(14) };
                f.Controls.Add(bottom);
                var import = Button("Weiteren Datensatz importieren", Color.White, ink);
                import.Width = 260;
                bottom.Controls.Add(import);
                import.Click += delegate
                {
                    importNext = true;
                    f.Close();
                };
                var archive = Button("Register existing archive", Color.White, ink);
                archive.Width = 250;
                bottom.Controls.Add(archive);
                archive.Click += delegate
                {
                    indexNext = true;
                    f.Close();
                };
                var accept = Button(single ? "Use this file" : "Auswahl verwenden", teal, Color.White);
                accept.Width = 230;
                bottom.Controls.Add(accept);
                var counts = Label("", 9, false);
                counts.Width = 1000;
                counts.Height = 42;
                bottom.Controls.Add(counts);
                Action refresh = delegate
                {
                    grid.Rows.Clear();
                    int count = 0;
                    foreach (var row in rows)
                    {
                        if (provider.SelectedIndex > 0 && V(row, "provider") != provider.Text)
                            continue;
                        if (selectedOnly.Checked && !sourceSelection.Contains(V(row, "id")))
                            continue;
                        int n = grid.Rows.Add(chosen.Contains(V(row, "id")), "", V(row, "provider"), V(row, "label"), V(row, "original_name"), V(row, "kind"), V(row, "build"), V(row, "measurement"), (Convert.ToInt64(row["bytes"], System.Globalization.CultureInfo.InvariantCulture) / 1048576.0).ToString("N1", System.Globalization.CultureInfo.InvariantCulture), V(row, "index_state") + " · " + V(row, "call_count"), row["qc_points"] == null ? "Not used" : V(row, "qc_points"));
                        grid.Rows[n].Tag = row;
                        grid.Rows[n].Height = Math.Max(grid.Rows[n].Height, 44);
                        grid.Rows[n].Cells[4].ToolTipText = V(row, "path") + "\nSHA-256: " + V(row, "sha256");
                        grid.Rows[n].Cells[1].ToolTipText = V(row, "qc_issues") + "\nCheckmark = file/checksum verification. Not clinical or identity verification.";
                        if (!Convert.ToBoolean(row["available"], System.Globalization.CultureInfo.InvariantCulture))
                            grid.Rows[n].DefaultCellStyle.ForeColor = Color.Firebrick;
                        count++;
                        grid.Rows[n].Cells["scope"].Value = V(row, "scope_summary");
                        object scopeData;
                        grid.Rows[n].Cells["scope"].ToolTipText = row.TryGetValue("data_scope", out scopeData) ? json.Serialize(scopeData) : "Check again in the import submenu.";
                    }
                    counts.Text = rows.Count == 0 ? "Not yet collecting any sources. Import or register the existing personal archive." : count + "visible files ·" + chosen.Count + "· Files and providers remain traceable separately.";
                };
                provider.SelectedIndexChanged += delegate
                {
                    refresh();
                };
                selectedOnly.CheckedChanged += delegate
                {
                    refresh();
                };
                grid.CurrentCellDirtyStateChanged += delegate
                {
                    if (grid.IsCurrentCellDirty)
                        grid.CommitEdit(DataGridViewDataErrorContexts.Commit);
                };
                grid.CellValueChanged += delegate (object sender, DataGridViewCellEventArgs e)
                {
                    if (e.RowIndex < 0 || e.ColumnIndex != 0)
                        return;
                    var r = (Dictionary<string, object>)grid.Rows[e.RowIndex].Tag;
                    if (r == null)
                        return;
                    string id = V(r, "id");
                    bool check = Convert.ToBoolean(grid.Rows[e.RowIndex].Cells[0].Value, System.Globalization.CultureInfo.InvariantCulture);
                    if (check)
                    {
                        if (single)
                            chosen.Clear();
                        chosen.Add(id);
                    }
                    else
                        chosen.Remove(id);
                    counts.Text = chosen.Count + "Provider filters do not change the selection of other providers.";
                };
                mark.Click += delegate
                {
                    foreach (DataGridViewRow r in grid.Rows)
                    {
                        chosen.Add(V((Dictionary<string, object>)r.Tag, "id"));
                        if (single)
                            break;
                    }
                    refresh();
                };
                unmark.Click += delegate
                {
                    chosen.Clear();
                    refresh();
                };
                accept.Click += delegate
                {
                    if (single && chosen.Count != 1)
                    {
                        MessageBox.Show(f, "For this input field, please select exactly one file.");
                        return;
                    }
                    result = rows.Where(r => chosen.Contains(V(r, "id"))).ToList();
                    f.DialogResult = DialogResult.OK;
                    f.Close();
                };
                refresh();
                if (f.ShowDialog(this) != DialogResult.OK)
                    result = null;
            }
            if (importNext)
                ShowImport();
            if (indexNext)
                StartJob(catalog.tasks.First(t => t.id == "archive_index"), new Dictionary<string, object>(), false);
            return result;
        }
        void ChooseSources()
        {
            var rows = LibraryDialog(false, false);
            if (rows == null)
                return;
            sourceSelection.Clear();
            foreach (var row in rows)
                sourceSelection.Add(V(row, "id"));
            RenderCards();
        }
        void ChooseFieldSources(Field f, Control edit)
        {
            if (f.kind == "folder")
            {
                Browse(f, edit);
                return;
            }
            var rows = LibraryDialog(!f.multi, true);
            if (rows == null || rows.Count == 0)
                return;
            string[] paths = rows.Select(r => V(r, "path")).Distinct(StringComparer.OrdinalIgnoreCase).ToArray();
            edit.Tag = f.multi ? (object)paths : (object)paths[0];
            edit.Text = String.Join("; ", paths);
            tips.SetToolTip(edit, edit.Text);
            RememberFields();
            string key = f.key == "a" ? "build_a" : f.key == "b" ? "build_b" : "build";
            Control value;
            if (paths.Length == 1 && fields.TryGetValue(key, out value) && (V(rows[0], "build") == "GRCh37" || V(rows[0], "build") == "GRCh38") && value.Text.StartsWith("Please", StringComparison.Ordinal))
                value.Text = V(rows[0], "build");
        }
        void PaintQuality(object sender, DataGridViewCellPaintingEventArgs e)
        {
            var grid = (DataGridView)sender;
            if (e.RowIndex < 0 || e.ColumnIndex < 0 || grid.Columns[e.ColumnIndex].Name != "quality")
                return;
            e.PaintBackground(e.ClipBounds, true);
            var row = grid.Rows[e.RowIndex].Tag as Dictionary<string, object>;
            if (row == null)
                return;
            string state = V(row, row.ContainsKey("color") ? "color" : "qc_color");
            object verifiedValue;
            bool verified = Convert.ToBoolean(row.TryGetValue("verified", out verifiedValue) ? verifiedValue : row.TryGetValue("qc_verified", out verifiedValue) ? verifiedValue : false, System.Globalization.CultureInfo.InvariantCulture);
            Color color = state == "green" ? Color.SeaGreen : state == "red" ? Color.Firebrick : state == "black" ? Color.Black : state == "gray" ? Color.SlateGray : Color.DarkOrange;
            e.Graphics.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
            float w = Math.Min(52, e.CellBounds.Width * .55F), h = w * .65F, x = e.CellBounds.Left + 7, y = e.CellBounds.Top + (e.CellBounds.Height - h) / 2;
            using (var pen = new Pen(color, 4))
            {
                e.Graphics.DrawArc(pen, x, y, w, h, 180, 180);
                float score = state == "green" ? .88F : state == "orange" ? .5F : .12F;
                double angle = Math.PI + (Math.PI * score);
                float cx = x + w / 2, cy = y + h / 2;
                e.Graphics.DrawLine(pen, cx, cy, cx + (float)Math.Cos(angle) * w * .42F, cy + (float)Math.Sin(angle) * h * .43F);
            }
            string mark = state == "black" || state == "red" ? "×" : verified ? "✓" : "?";
            Color markColor = state == "black" || state == "red" ? Color.Firebrick : verified ? Color.SeaGreen : Color.DarkOrange;
            using (var brush = new SolidBrush(markColor))
            using (var font = new Font("Segoe UI", 14, FontStyle.Bold))
                e.Graphics.DrawString(mark, font, brush, x + w + 6, e.CellBounds.Top + (e.CellBounds.Height - 28) / 2);
            e.Handled = true;
        }
        void ShowProfile()
        {
            try
            {
                var p = json.Deserialize<Dictionary<string, object>>(QueryEngine("--profile " + Quote(Person())));
                TextDialog("DNA profile ·" + Person(), V(p, "summary"));
            }
            catch (Exception e) { MessageBox.Show(this, e.Message, "Profiles not achievable"); }
        }
        void Help(TaskInfo task)
        {
            TextDialog(task.title, task.description + "\n\nTOOLS\n" + task.tools + " · " + task.platform + "\n\nDESCRIPTION\n" + task.help + "\n\nINPUTS\n" + String.Join("\n", task.fields.Select(f => "• " + f.label + (f.required ? " (required)" : " (optional)") + "\n   " + f.help)) + "\n\nOUTPUT\nEach run gets its own folder under Projects\\Launcher. Original files are preserved. Launched tools may require additional input before analysis.");
        }
        void TextDialog(string title, string text)
        {
            using (var f = new Form { Text = title, ClientSize = new Size(780, 540), StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false, Font = new Font("Segoe UI", 11), BackColor = Color.White })
            {
                var t = new RichTextBox { Dock = DockStyle.Fill, ReadOnly = true, BorderStyle = BorderStyle.None, BackColor = Color.White, ForeColor = ink, Text = text, Font = new Font("Segoe UI", 11) };
                f.Padding = new Padding(24);
                f.Controls.Add(t);
                f.ShowDialog(this);
            }
        }
        string PrefFile()
        {
            return Path.Combine(root, "DNA_Software", "UserData", "Launcher", "settings.json");
        }
        void SavePreferences()
        {
            try
            {
                RememberFields();
                Directory.CreateDirectory(Path.GetDirectoryName(PrefFile()));
                File.WriteAllText(PrefFile(), json.Serialize(new Dictionary<string, object> { { "person", Person() }, { "choices", choices } }), new UTF8Encoding(false));
            }
            catch { }
        }
        void LoadPreferences()
        {
            try
            {
                if (File.Exists(PrefFile()))
                {
                    var p = json.Deserialize<Dictionary<string, object>>(File.ReadAllText(PrefFile(), Encoding.UTF8));
                    object value;
                    if (p.TryGetValue("person", out value) && person.Items.Contains(value))
                        person.SelectedItem = value;
                    if (p.TryGetValue("choices", out value))
                    {
                        var c = (Dictionary<string, object>)value;
                        foreach (var pair in c)
                            choices[pair.Key] = pair.Value;
                    }
                }
            }
            catch { }
        }
    }
}
