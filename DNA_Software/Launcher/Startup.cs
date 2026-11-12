using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;
namespace DnaWorkbench
{
    public class StartupContext
    {
        public Process Server
        {
            get; set;
        }
        public string Url
        {
            get; set;
        }
        public string Python
        {
            get; set;
        }
        public string LinuxStatus
        {
            get; set;
        }
        public StartupContext()
        {
            Url = "";
            Python = "";
            LinuxStatus = "Not started";
        }
    }
    public static class PortableEnvironment
    {
#if DNA_WINDOWS_ARM64
        public const string WindowsArchitecture = "arm64";
        public const string PythonFolder = "Python-arm64";
#else
        public const string WindowsArchitecture = "x64";
        public const string PythonFolder = "Python";
#endif
        public static void Configure()
        {
            LegacyLayout.Migrate(AppDomain.CurrentDomain.BaseDirectory);
            string root = Path.GetFullPath(AppDomain.CurrentDomain.BaseDirectory), basePath = Path.Combine(root, "DNA_Software", "UserData");
            var paths = new Dictionary<string, string> { { "TEMP", "Temp" }, { "TMP", "Temp" }, { "TMPDIR", "Temp" }, { "XDG_CACHE_HOME", "Cache" }, { "XDG_DATA_HOME", "Data" }, { "XDG_CONFIG_HOME", "Config" }, { "PIP_CACHE_DIR", "Cache/pip" }, { "UV_CACHE_DIR", "Cache/uv" }, { "HF_HOME", "Cache/huggingface" }, { "TORCH_HOME", "Cache/torch" }, { "MPLCONFIGDIR", "Cache/matplotlib" }, { "npm_config_cache", "Cache/npm" }, { "APPDATA", "AppData/Roaming" }, { "LOCALAPPDATA", "AppData/Local" }, { "JUPYTER_CONFIG_DIR", "Jupyter/config" }, { "JUPYTER_DATA_DIR", "Jupyter/data" }, { "JUPYTER_RUNTIME_DIR", "Jupyter/runtime" } };
            foreach (var pair in paths)
            {
                string path = Path.GetFullPath(Path.Combine(basePath, pair.Value));
                Directory.CreateDirectory(path);
                Environment.SetEnvironmentVariable(pair.Key, path);
            }
            Environment.SetEnvironmentVariable("DNA_SUITE_ROOT", root);
            Environment.SetEnvironmentVariable("DNA_WORKBENCH_WINDOWS_ARCH", WindowsArchitecture);
            Environment.SetEnvironmentVariable("PYTHONNOUSERSITE", "1");
            Environment.CurrentDirectory = root;
        }
    }
    public static class BootstrapPayload
    {
        public static void Ensure()
        {
            string root = Path.GetFullPath(AppDomain.CurrentDomain.BaseDirectory);
            using (var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream("DNA.Core.zip"))
            {
                if (stream == null)
                    return;
                byte[] payload;
                using (var memory = new MemoryStream())
                {
                    stream.CopyTo(memory);
                    payload = memory.ToArray();
                }
                string hash;
                using (var sha = SHA256.Create())
                    hash = BitConverter.ToString(sha.ComputeHash(payload)).Replace("-", "");
                string marker = Path.Combine(root, "DNA_Software", "UserData", "Launcher", "app-payload.sha256");
                bool update = !File.Exists(marker) || File.ReadAllText(marker) != hash;
                string backup = Path.Combine(root, "DNA_Software", "Backups", "App", DateTime.Now.ToString("yyyyMMdd-HHmmss", System.Globalization.CultureInfo.InvariantCulture) + "_" + hash.Substring(0, 8));
                using (var archive = new ZipArchive(new MemoryStream(payload), ZipArchiveMode.Read))
                {
                    foreach (var entry in archive.Entries)
                    {
                        string relative = entry.FullName.Replace('/', Path.DirectorySeparatorChar);
                        string target = Path.GetFullPath(Path.Combine(root, relative));
                        if (!target.StartsWith(root, StringComparison.OrdinalIgnoreCase))
                            throw new InvalidOperationException("Invalid packet path.");
                        if (entry.FullName.EndsWith("/", StringComparison.Ordinal))
                            continue;
                        if (File.Exists(target) && !update)
                            continue;
                        byte[] content;
                        using (var input = entry.Open())
                        using (var memory = new MemoryStream())
                        {
                            input.CopyTo(memory);
                            content = memory.ToArray();
                        }
                        if (File.Exists(target))
                        {
                            using (var sha = SHA256.Create())
                            {
                                if (sha.ComputeHash(File.ReadAllBytes(target)).SequenceEqual(sha.ComputeHash(content)))
                                    continue;
                            }
                            string saved = Path.Combine(backup, relative);
                            Directory.CreateDirectory(Path.GetDirectoryName(saved));
                            File.Copy(target, saved, false);
                        }
                        Directory.CreateDirectory(Path.GetDirectoryName(target));
                        string temporary = target + ".app-update";
                        File.WriteAllBytes(temporary, content);
                        if (File.Exists(target))
                            File.Copy(temporary, target, true);
                        else
                            File.Move(temporary, target);
                        if (File.Exists(temporary))
                            File.Delete(temporary);
                    }
                }
                Directory.CreateDirectory(Path.GetDirectoryName(marker));
                File.WriteAllText(marker, hash);
            }
        }
    }
    public class StartupScreen : Form
    {
        readonly string root = AppDomain.CurrentDomain.BaseDirectory; readonly JavaScriptSerializer json = new JavaScriptSerializer(); readonly ListView rows; readonly Label status; readonly Button setup, proceed; readonly ComboBox profile; readonly CheckBox linux, host; bool busy; public StartupContext Context
        {
            get; private set;
        }
        bool transferred; readonly bool manual; string language; string L(string english)
        {
            return NativeLocale.Text(english, language);
        }
        static string Q(string s)
        {
            return "\"" + s.Replace("\"", "\\\"") + "\"";
        }
        public StartupScreen(StartupContext context = null, bool stay = false)
        {
            Context = context ?? new StartupContext();
            transferred = context != null;
            manual = stay;
            try
            {
                string config = Path.Combine(root, "DNA_Software", "UserData", "Launcher", "appearance.json");
                if (File.Exists(config))
                    language = Convert.ToString(json.Deserialize<Dictionary<string, object>>(File.ReadAllText(config))["language"], System.Globalization.CultureInfo.InvariantCulture);
            }
            catch { }
            if (language == "ar" || language == "fa" || language == "ur")
            {
                RightToLeft = RightToLeft.Yes;
                RightToLeftLayout = true;
            }
            Text = L("DNA Workbench · Startup check");
            ClientSize = new Size(690, 470);
            StartPosition = FormStartPosition.CenterScreen;
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;
            Font = new Font("Segoe UI", 10);
            BackColor = Color.White;
            var title = new Label { Text = L("Preparing DNA Workbench"), Font = new Font("Segoe UI", 19, FontStyle.Bold), Bounds = new Rectangle(24, 20, 640, 44) };
            Controls.Add(title);
            rows = new ListView { View = View.Details, FullRowSelect = true, Bounds = new Rectangle(24, 80, 640, 190), HeaderStyle = ColumnHeaderStyle.Nonclickable };
            rows.Columns.Add(L("Component"), 170);
            rows.Columns.Add("Status", 180);
            rows.Columns.Add(L("Details"), 270);
            Controls.Add(rows);
            linux = new CheckBox { Text = L("Start Ubuntu now (optional)"), Checked = false, Visible = manual, Bounds = new Rectangle(24, 280, 640, 26) };
            Controls.Add(linux);
            profile = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Visible = manual, Bounds = new Rectangle(24, 319, 220, 30) };
            profile.Items.AddRange(new object[] { "Core", "Linux", "Tools", "References", "Sources" });
            profile.SelectedIndex = 0;
            Controls.Add(profile);
            host = new CheckBox { Text = L("Set up WSL host if needed"), Visible = manual, Bounds = new Rectangle(255, 320, 390, 30) };
            Controls.Add(host);
            setup = new Button { Text = L("Set up / repair"), Bounds = new Rectangle(24, 365, 220, 38) };
            setup.Click += async delegate { await Install(); };
            Controls.Add(setup);
            proceed = new Button { Text = L("Open app"), Bounds = new Rectangle(420, 365, 245, 38), Enabled = false };
            proceed.Click += delegate
            {
                if (Context.Server != null && !Context.Server.HasExited)
                {
                    transferred = true;
                    DialogResult = DialogResult.OK;
                    Close();
                }
            };
            Controls.Add(proceed);
            status = new Label { Bounds = new Rectangle(24, 415, 640, 46), Text = L("Starting checks …") };
            Controls.Add(status);
            Shown += async delegate { await Check(); };
            FormClosed += delegate
            {
                if (!transferred && Context.Server != null)
                    try
                    {
                        Context.Server.StandardInput.Close();
                    }
                    catch { }
            };
        }
        void Row(string name, string value, string note)
        {
            if (IsDisposed || Disposing)
                return;
            var row = rows.Items.Cast<ListViewItem>().FirstOrDefault(r => r.Text == name);
            if (row == null)
            {
                row = new ListViewItem(name);
                row.SubItems.Add("");
                row.SubItems.Add("");
                rows.Items.Add(row);
            }
            row.SubItems[1].Text = value;
            row.SubItems[2].Text = note;
            row.ForeColor = value.StartsWith("✓", StringComparison.Ordinal) ? Color.SeaGreen : value.StartsWith(L("Missing"), StringComparison.Ordinal) ? Color.Firebrick : Color.FromArgb(70, 95, 115);
            try
            {
                string directory = Path.Combine(root, "DNA_Software", "UserData", "Launcher");
                Directory.CreateDirectory(directory);
                var data = rows.Items.Cast<ListViewItem>().Select(r => new Dictionary<string, string> { { "component", r.Text }, { "status", r.SubItems[1].Text }, { "detail", r.SubItems[2].Text } }).ToArray();
                File.WriteAllText(Path.Combine(directory, "start-status.json"), json.Serialize(data), new UTF8Encoding(false));
            }
            catch { }
        }
        async Task Check()
        {
            if (busy)
                return;
            busy = true;
            setup.Enabled = false;
            proceed.Enabled = false;
            try
            {
                Row(L("App directory"), "✓ " + Path.GetPathRoot(root), root);
                var hostProbe = Task.Run(() =>
                {
                    try
                    {
                        var si = new ProcessStartInfo("powershell.exe", "-NoProfile -ExecutionPolicy Bypass -File " + Q(Path.Combine(root, "DNA_Software", "Launcher", "portable-check.ps1")) + " -Root " + Q(Path.Combine(root, "."))) { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
                        using (var process = Process.Start(si))
                        {
                            var output = process.StandardOutput.ReadToEndAsync();
                            var error = process.StandardError.ReadToEndAsync();
                            process.WaitForExit();
                            return process.ExitCode == 0 ? output.Result : "";
                        }
                    }
                    catch { return ""; }
                });
                var probeDone = await Task.WhenAny(hostProbe, Task.Delay(4000));
                if (probeDone == hostProbe && !String.IsNullOrWhiteSpace(hostProbe.Result))
                {
                    var probe = json.Deserialize<Dictionary<string, object>>(hostProbe.Result);
                    Row("WSL-Host", Convert.ToBoolean(probe["wsl_host_ready"], System.Globalization.CultureInfo.InvariantCulture) ? L("✓ present") : L("Optional setup"), Convert.ToString(probe["disk"], System.Globalization.CultureInfo.InvariantCulture));
                }
                else
                    Row("WSL-Host", L("Checking / optional"), L("PowerShell check does not block startup"));

                string basePython = Path.Combine(root, "DNA_Software", "Windows", PortableEnvironment.PythonFolder);
                Context.Python = Directory.Exists(basePython) ? Directory.GetFiles(basePython, "python.exe", SearchOption.AllDirectories).FirstOrDefault(p => !p.Contains("\\venv\\")) : null;
                if (Context.Python == null)
                {
                    Row("Python", L("Missing"), L("Install Core"));
                    status.Text = L("First setup: Core installs portable Python and the interface beside the EXE.");
                    return;
                }
                Row("Python", L("✓ present"), Context.Python);
#if DNA_WINDOWS_ARM64
                string webViewVersion;
                try { webViewVersion = Microsoft.Web.WebView2.Core.CoreWebView2Environment.GetAvailableBrowserVersionString(); }
                catch (Microsoft.Web.WebView2.Core.WebView2RuntimeNotFoundException) { webViewVersion = null; }
                if (String.IsNullOrEmpty(webViewVersion))
                {
                    Row(L("App interface"), L("Missing"), "Microsoft Edge WebView2 Evergreen Runtime (ARM64)");
                    status.Text = "Install the Microsoft Edge WebView2 Evergreen Runtime for ARM64, then restart DNA Workbench.";
                    return;
                }
                Row(L("App interface"), L("✓ present"), webViewVersion);
#else
                string runtime = Path.Combine(root, "DNA_Software", "Windows", "WebView2Runtime");
                bool found = Directory.Exists(runtime) && Directory.GetFiles(runtime, "msedgewebview2.exe", SearchOption.AllDirectories).Length > 0;
                Row(L("App interface"), found ? L("✓ portable runtime") : L("Missing"), L("Install Core if no runtime is present"));
                if (!found)
                {
                    status.Text = L("Portable interface missing: install Core.");
                    return;
                }
#endif
                if (Context.Server == null || Context.Server.HasExited)
                {
                    string folder = Path.Combine(root, "DNA_Software", "UserData", "Launcher", "Sitzungen", Guid.NewGuid().ToString("N"));
                    Directory.CreateDirectory(folder);
                    string info = Path.Combine(folder, "service.json");
                    var si = new ProcessStartInfo(Context.Python, Q(Path.Combine(root, "DNA_Software", "Launcher", "family.py")) + " --embedded " + Q(info)) { UseShellExecute = false, CreateNoWindow = true, RedirectStandardInput = true, RedirectStandardError = true, WorkingDirectory = root };
                    si.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
                    si.EnvironmentVariables["PYTHONNOUSERSITE"] = "1";
                    Context.Server = new Process { StartInfo = si };
                    Context.Server.ErrorDataReceived += delegate (object s, DataReceivedEventArgs e)
                    {
                        if (e.Data != null)
                            try
                            {
                                File.AppendAllText(Path.Combine(folder, "dienst.log"), e.Data + Environment.NewLine);
                            }
                            catch { }
                    };
                    Context.Server.Start();
                    Context.Server.BeginErrorReadLine();
                    Row(L("Local data service"), L("Starting …"), L("Loopback only: 127.0.0.1"));
                    for (int i = 0; i < 150 && !File.Exists(info); i++)
                    {
                        if (Context.Server.HasExited)
                            throw new InvalidOperationException(L("Local service failed. See ") + folder);
                        await Task.Delay(100);
                    }
                    if (!File.Exists(info))
                        throw new InvalidOperationException(L("Local service did not respond."));
                    Context.Url = Convert.ToString(json.Deserialize<Dictionary<string, object>>(File.ReadAllText(info))["url"], System.Globalization.CultureInfo.InvariantCulture);
                }
                Row(L("Local data service"), L("✓ ready"), Context.Url);
                Row(L("Optional tools"), L("On demand"), "OpenCRAVAT, Gramps Web, Haplogrep usw.");
                string disk = Path.Combine(root, "DNA_Linux", "DNA-SSD", "ext4.vhdx");
                if (linux.Checked && File.Exists(disk))
                {
                    Row("Ubuntu / WSL", L("Starting …"), L("Up to 6 seconds before opening the app"));
                    var task = Task.Run(() => ProbeLinux());
                    var result = await Task.WhenAny(task, Task.Delay(6000));
                    Context.LinuxStatus = result == task ? task.Result : L("Starting in background");
                    Row("Ubuntu / WSL", Context.LinuxStatus, L("Unneeded desktop tools are not started"));
                }
                else
                {
                    Context.LinuxStatus = File.Exists(disk) ? L("Not requested") : L("Missing / optional");
                    Row("Ubuntu / WSL", Context.LinuxStatus, L("Linux mode installs Ubuntu beside the EXE"));
                }
                if (IsDisposed || Disposing)
                    return;
                status.Text = L("App ready. Optional tools do not block startup.");
                proceed.Enabled = true;
                if (!manual && (!linux.Checked || File.Exists(disk)))
                {
                    transferred = true;
                    DialogResult = DialogResult.OK;
                    Close();
                }
                else
                {
                    profile.SelectedItem = "Linux";
                    status.Text = L("Core ready. Set up Linux when needed or continue without it.");
                }
            }
            catch (Exception e) { status.Text = e.Message; Row(L("Startup check"), L("Error"), e.Message); }
            finally { busy = false; if (!IsDisposed) setup.Enabled = true; }
        }
        static int WslCommand(string arguments)
        {
            var si = new ProcessStartInfo("wsl.exe", arguments) { UseShellExecute = false, CreateNoWindow = true, RedirectStandardError = true, RedirectStandardOutput = true };
            using (var p = Process.Start(si))
            {
                p.BeginOutputReadLine();
                p.BeginErrorReadLine();
                if (!p.WaitForExit(25000))
                {
                    p.Kill();
                    return -1;
                }
                return p.ExitCode;
            }
        }
        string ProbeLinux()
        {
            try
            {
                string script = Path.Combine(root, "DNA_Software", "Start", "DNA.ps1");
                var si = new ProcessStartInfo("powershell.exe", "-NoProfile -ExecutionPolicy Bypass -File " + Q(script) + " -Action Start") { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
                using (var p = Process.Start(si))
                {
                    var output = p.StandardOutput.ReadToEndAsync();
                    var error = p.StandardError.ReadToEndAsync();
                    p.WaitForExit();
                    return p.ExitCode == 0 ? L("✓ ready") : L("Check PowerShell setup");
                }
            }
            catch { return L("WSL host not ready"); }
        }
        async Task Install()
        {
            if (busy)
                return;
            busy = true;
            setup.Enabled = false;
            proceed.Enabled = false;
            status.Text = L("Setup running. Downloads and checksums are logged.");
            try
            {
                string args = "-NoProfile -ExecutionPolicy Bypass -File " + Q(Path.Combine(root, "DNA_Software", "Launcher", "setup.ps1")) + " -Root " + Q(Path.Combine(root, ".")) + " -Mode " + profile.Text + (host.Checked ? " -InstallWslHost" : "");
                var si = new ProcessStartInfo("powershell.exe", args) { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
                var process = Process.Start(si);
                var output = process.StandardOutput.ReadToEndAsync();
                var error = process.StandardError.ReadToEndAsync();
                await Task.Run(() => process.WaitForExit());
                string text = await output;
                string failure = await error;
                File.WriteAllText(Path.Combine(root, "DNA_Software", "Logs", "Setup", "einrichtung.log"), text + failure);
                if (process.ExitCode != 0)
                    throw new InvalidOperationException(L("Setup incomplete. See DNA_Software/Logs/Setup/einrichtung.log"));
            }
            catch (Exception e) { status.Text = e.Message; busy = false; setup.Enabled = true; return; }
            busy = false;
            await Check();
        }
    }
}
