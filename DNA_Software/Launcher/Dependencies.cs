using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
namespace DnaWorkbench
{
    public partial class Workbench
    {
        async Task<Dictionary<string, object>> DependencyAction(string action, IEnumerable<string> ids)
        {
            var args = Quote(Path.Combine(appdir, "dependency_manager.py")) + " " + action + " " + String.Join(" ", ids.Select(Quote));
            var si = new ProcessStartInfo(python, args) { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true, StandardOutputEncoding = Encoding.UTF8, StandardErrorEncoding = Encoding.UTF8 };
            si.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
            using (var p = Process.Start(si))
            {
                var output = p.StandardOutput.ReadToEndAsync();
                var error = p.StandardError.ReadToEndAsync();
                await Task.Run(() => p.WaitForExit());
                string text = await output;
                string err = await error;
                if (p.ExitCode != 0)
                    throw new InvalidOperationException(text + err);
                var result = json.Deserialize<Dictionary<string, object>>(text);
                object errorValue;
                if (result.TryGetValue("error", out errorValue))
                    throw new InvalidOperationException(Convert.ToString(errorValue, System.Globalization.CultureInfo.InvariantCulture));
                return result;
            }
        }
        void ShowDependencies()
        {
            using (var form = new Form { Text = "Dependencies, Data Statuses & Updates", ClientSize = new Size(1180, 700), MinimumSize = new Size(900, 550), StartPosition = FormStartPosition.CenterParent, Font = new Font("Segoe UI", 10), BackColor = paper, AutoScaleMode = AutoScaleMode.Dpi, AutoScaleDimensions = new SizeF(96, 96) })
            {
                var top = new FlowLayoutPanel { Dock = DockStyle.Top, Height = 96, Padding = new Padding(12), AutoScroll = true };
                form.Controls.Add(top);
                var refresh = Button("Check locally", Color.White, ink);
                refresh.Width = 140;
                top.Controls.Add(refresh);
                var online = Button("Check updates", Color.White, ink);
                online.Width = 160;
                top.Controls.Add(online);
                var download = Button("Download selected items separately", teal, Color.White);
                download.Width = 220;
                top.Controls.Add(download);
                var install = Button("Setup assistant", teal, Color.White);
                install.Width = 210;
                top.Controls.Add(install);
                var folder = Button("Update folder", Color.White, ink);
                folder.Width = 160;
                top.Controls.Add(folder);
                var optional = Button("Optional RFMix", Color.White, ink);
                optional.Width = 170;
                top.Controls.Add(optional);
                var project = Button("Project page", Color.White, ink);
                project.Width = 140;
                top.Controls.Add(project);
                var status = new Label { Text = "Versions are determined ...", Dock = DockStyle.Bottom, Height = 90, Padding = new Padding(15), ForeColor = ink };
                form.Controls.Add(status);
                var grid = new DataGridView { Dock = DockStyle.Fill, ReadOnly = true, AllowUserToAddRows = false, RowHeadersVisible = false, SelectionMode = DataGridViewSelectionMode.FullRowSelect, MultiSelect = true, AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.None, BackgroundColor = Color.White };
                foreach (string c in new string[] { "Werkzeug / Datensatz", "Gruppe", "Installed/checked", "Pinned version", "Aktuell online", "Status", "Update", "License" })
                    grid.Columns.Add(c, c);
                int[] widths = { 250, 95, 230, 170, 170, 250, 250, 180 };
                for (int i = 0; i < widths.Length; i++)
                    grid.Columns[i].Width = widths[i];
                grid.Columns[0].Frozen = true;
                form.Controls.Add(grid);
                grid.BringToFront();
                top.BringToFront();
                bool running = false;
                Func<Task> load = async delegate { var report = await DependencyAction("snapshot", Array.Empty<string>()); grid.Rows.Clear(); foreach (var row in json.ConvertToType<List<Dictionary<string, object>>>(report["items"])) { int n = grid.Rows.Add(V(row, "name"), V(row, "group"), V(row, "installed_version"), V(row, "locked_version"), V(row, "latest_version"), V(row, "status"), V(row, "update_status"), V(row, "license")); grid.Rows[n].Tag = row; grid.Rows[n].Cells[0].ToolTipText = V(row, "source") + "\n" + V(row, "path"); } status.Text = "App " + V(report, "app_version") + " · " + V(report, "app_update_status") + "\nUse Ctrl to select several rows. Downloads preserve active versions and personal DNA."; };
                Func<string, Task> work = async delegate (string action) { if (running) return; running = true; online.Enabled = download.Enabled = install.Enabled = refresh.Enabled = false; try { var ids = grid.SelectedRows.Cast<DataGridViewRow>().Select(r => V((Dictionary<string, object>)r.Tag, "id")).Distinct().ToArray(); if (action != "snapshot" && ids.Length == 0) throw new InvalidOperationException("Select tools / data sets."); status.Text = "Procedure is ongoing:" + action + " · " + ids.Length + "Entries. Large downloads can take longer."; var result = await DependencyAction(action, ids); await load(); if (action == "stage") TextDialog("Download report", json.Serialize(result)); } catch (Exception e) { status.Text = e.Message; } finally { running = false; online.Enabled = download.Enabled = install.Enabled = refresh.Enabled = true; } };
                refresh.Click += async delegate { if (!running) try { await load(); } catch (Exception e) { status.Text = e.Message; } };
                online.Click += async delegate { await work("check"); };
                download.Click += async delegate { await work("stage"); };
                folder.Click += delegate
                {
                    string p = Path.Combine(root, "DNA_Software", "Updates");
                    Directory.CreateDirectory(p);
                    Process.Start("explorer.exe", Quote(p));
                };
                install.Click += delegate
                {
                    using (var wizard = new StartupScreen(new StartupContext { Server = familyServer, Url = familyBase, Python = python }, true))
                    {
                        wizard.ShowDialog(form);
                        familyServer = wizard.Context.Server;
                        familyBase = wizard.Context.Url;
                    }
                };
                optional.Click += async delegate { await EnsureRequirements(catalog.tasks.First(t => t.id == "rfmix"), true); };
                project.Click += delegate
                {
                    if (grid.SelectedRows.Count > 0)
                    {
                        var row = grid.SelectedRows[0].Tag as Dictionary<string, object>;
                        string url = V(row, "source");
                        if (url.StartsWith("https://", StringComparison.Ordinal))
                            Process.Start(new ProcessStartInfo(url) { UseShellExecute = true });
                    }
                };
                form.Shown += async delegate { try { await load(); } catch (Exception e) { status.Text = e.Message; } };
                form.ShowDialog(this);
            }
        }
    }
}
