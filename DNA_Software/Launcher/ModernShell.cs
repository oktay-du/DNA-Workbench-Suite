using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Windows.Forms;
using Microsoft.Web.WebView2.WinForms;
namespace DnaWorkbench
{
    public partial class Workbench
    {
        bool IsModernShell()
        {
            return familyView != null && familyView.Source != null && familyView.Source.AbsolutePath == "/app";
        }
        void ModernMessage(WebView2 view, Dictionary<string, object> request)
        {
            string action = V(request, "action");
            if (action == "suite-pick-file")
            {
                Guid id;
                if (!Guid.TryParse(V(request, "requestId"), out id))
                    return;
                BeginInvoke(new Action(delegate
                {
                    var files = new List<string>();
                    bool folder = request.ContainsKey("folder") && Convert.ToBoolean(request["folder"], System.Globalization.CultureInfo.InvariantCulture);
                    bool multi = request.ContainsKey("multi") && Convert.ToBoolean(request["multi"], System.Globalization.CultureInfo.InvariantCulture);
                    if (folder)
                    {
                        using (var d = new FolderBrowserDialog { Description = "Select local data folder" })
                            if (d.ShowDialog(this) == DialogResult.OK)
                                files.Add(d.SelectedPath);
                    }
                    else
                        using (var d = new OpenFileDialog { Multiselect = multi, Title = "Select local files", Filter = "Files|*.*" })
                            if (d.ShowDialog(this) == DialogResult.OK)
                                files.AddRange(d.FileNames);
                    if (!view.IsDisposed && view.CoreWebView2 != null)
                        view.CoreWebView2.PostWebMessageAsJson(json.Serialize(new Dictionary<string, object> { { "action", "suite-files" }, { "requestId", V(request, "requestId") }, { "files", files.ToArray() } }));
                }));
                return;
            }
            if (action == "suite-native-import")
            {
                BeginInvoke(new Action(delegate
                {
                    string profile = V(request, "person");
                    if (person.Items.Contains(profile))
                        person.SelectedItem = profile;
                    ShowImport(request.ContainsKey("existing") && Convert.ToBoolean(request["existing"], System.Globalization.CultureInfo.InvariantCulture));
                }));
                return;
            }
            if (action == "suite-dependencies")
            {
                var task = catalog.tasks.FirstOrDefault(t => t.id == V(request, "task"));
                if (task != null)
                    BeginInvoke(new Action(async delegate { await EnsureRequirements(task, false); }));
                return;
            }
            if (action == "suite-open-results")
            {
                string pid = V(request, "person"), job = V(request, "job");
                if (!System.Text.RegularExpressions.Regex.IsMatch(pid, "^[A-Za-z0-9_-]+$") || !System.Text.RegularExpressions.Regex.IsMatch(job, "^[A-Za-z0-9_-]+$"))
                    return;
                string path = job.StartsWith("transfer_", StringComparison.Ordinal) ? Path.Combine(root, "Projects", "Profile transfers", job, "Results") : Path.Combine(jobsroot, pid, job, "Results");
                if (Directory.Exists(path))
                    Process.Start("explorer.exe", Quote(path));
                return;
            }
            if (action == "suite-open-report")
            {
                string pid = V(request, "person");
                if (!System.Text.RegularExpressions.Regex.IsMatch(pid, "^[A-Za-z0-9_-]+$"))
                    return;
                string file = Path.GetFullPath(V(request, "path"));
                string[] allowed = { ".pdf", ".txt", ".csv", ".tsv", ".json", ".md" };
                string reports = Path.GetFullPath(Path.Combine(root, "Profiles", pid)) + Path.DirectorySeparatorChar;
                string results = Path.GetFullPath(Path.Combine(jobsroot, pid)) + Path.DirectorySeparatorChar;
                if ((file.StartsWith(reports, StringComparison.OrdinalIgnoreCase) || file.StartsWith(results, StringComparison.OrdinalIgnoreCase)) && File.Exists(file) && allowed.Contains(Path.GetExtension(file).ToLowerInvariant()))
                    Process.Start(new ProcessStartInfo(file) { UseShellExecute = true });
                return;
            }
            if (action == "suite-open-root")
                Process.Start("explorer.exe", Quote(root));
            if (action == "suite-open-artifact")
            {
                string pid = V(request, "person"), job = V(request, "job");
                if (!System.Text.RegularExpressions.Regex.IsMatch(pid, "^[A-Za-z0-9_-]+$") || !System.Text.RegularExpressions.Regex.IsMatch(job, "^[A-Za-z0-9_-]+$"))
                    return;
                string basePath = Path.GetFullPath(Path.Combine(jobsroot, pid, job, "Results")) + Path.DirectorySeparatorChar;
                string path = Path.GetFullPath(Path.Combine(basePath, V(request, "file")));
                string[] allowed = { ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".txt", ".csv", ".tsv", ".json", ".md" };
                if (path.StartsWith(basePath, StringComparison.OrdinalIgnoreCase) && File.Exists(path) && allowed.Contains(Path.GetExtension(path).ToLowerInvariant()))
                    Process.Start(new ProcessStartInfo(path) { UseShellExecute = true });
            }
        }
    }
}
