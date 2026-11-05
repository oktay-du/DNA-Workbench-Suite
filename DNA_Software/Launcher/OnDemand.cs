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
        async Task<Dictionary<string, object>> DemandAction(string action, params string[] values)
        {
            var si = new ProcessStartInfo(python, Quote(Path.Combine(appdir, "on_demand.py")) + " " + action + " " + String.Join(" ", values.Select(Quote))) { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true, StandardOutputEncoding = Encoding.UTF8, StandardErrorEncoding = Encoding.UTF8 };
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
                return json.Deserialize<Dictionary<string, object>>(text);
            }
        }
        async Task<bool> EnsureRequirements(TaskInfo task, bool force)
        {
            string filename = "";
            Control input;
            if (fields.TryGetValue("file", out input))
                filename = input.Text;
            string[] statusArgs = String.IsNullOrEmpty(filename) ? new string[] { task.id } : new string[] { task.id, "--file", filename };
            Dictionary<string, object> report;
            try
            {
                report = await DemandAction("status", statusArgs);
            }
            catch (Exception e) { MessageBox.Show(this, e.Message, "Tool testing not possible"); return false; }
            var requirements = json.ConvertToType<List<Dictionary<string, object>>>(report["requirements"]);
            bool rfmix = requirements.Any(r => V(r, "id") == "rfmix");
            bool reviewed = report.ContainsKey("license_reviewed") && Convert.ToBoolean(report["license_reviewed"], System.Globalization.CultureInfo.InvariantCulture);
            if (!force && Convert.ToBoolean(report["ready"], System.Globalization.CultureInfo.InvariantCulture) && (!rfmix || reviewed))
                return true;
            if (requirements.Count == 0)
            {
                if (force)
                    MessageBox.Show(this, "This function does not require any additional analysis tools.", "App-Basis bereit");
                return true;
            }
            using (var form = new Form { Text = "Bei Bedarf vorbereiten · " + task.title, ClientSize = new Size(1040, 640), MinimumSize = new Size(800, 540), StartPosition = FormStartPosition.CenterParent, BackColor = paper, Font = new Font("Segoe UI", 10), AutoScaleMode = AutoScaleMode.Dpi, AutoScaleDimensions = new SizeF(96, 96) })
            {
                var top = new Label { Dock = DockStyle.Top, Height = 70, Padding = new Padding(15), Text = "Only components required for this function, nothing is automatically installed or downloaded, and tools that are already installed are checked.", ForeColor = ink };
                form.Controls.Add(top);
                var buttons = new FlowLayoutPanel { Dock = DockStyle.Bottom, Height = 110, Padding = new Padding(12) };
                form.Controls.Add(buttons);
                var start = Button("Linux starten", teal, Color.White);
                start.Width = 145;
                buttons.Controls.Add(start);
                var ubuntu = Button("Ubuntu einrichten", Color.White, ink);
                ubuntu.Width = 160;
                buttons.Controls.Add(ubuntu);
                var install = Button("Install selection", teal, Color.White);
                install.Width = 185;
                buttons.Controls.Add(install);
                var download = Button("Archiv herunterladen", Color.White, ink);
                download.Width = 185;
                buttons.Controls.Add(download);
                var source = Button("Opening Project / GitHub", Color.White, ink);
                source.Width = 195;
                buttons.Controls.Add(source);
                var refresh = Button("Review required", Color.White, ink);
                refresh.Width = 145;
                buttons.Controls.Add(refresh);
                var accept = Button("Funktion verwenden", teal, Color.White);
                accept.Width = 185;
                buttons.Controls.Add(accept);
                var status = new Label { Dock = DockStyle.Bottom, Height = 64, Padding = new Padding(12), ForeColor = ink };
                form.Controls.Add(status);
                var license = new CheckBox { Dock = DockStyle.Bottom, Height = 90, Padding = new Padding(12), Visible = rfmix, Checked = reviewed, Text = "RFMix is free for academic research only. Other use requires a separate Stanford license. I have reviewed the project license and am eligible for intended use. This selection does not grant a license." };
                form.Controls.Add(license);
                var grid = new DataGridView { Dock = DockStyle.Fill, ReadOnly = true, AllowUserToAddRows = false, RowHeadersVisible = false, SelectionMode = DataGridViewSelectionMode.FullRowSelect, MultiSelect = false, BackgroundColor = Color.White, AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.None };
                foreach (string col in new string[] { "Werkzeug", "Status", "Version / pinned revision", "Download", "Einrichtung" })
                    grid.Columns.Add(col, col);
                grid.Columns[0].Width = 150;
                grid.Columns[1].Width = 240;
                grid.Columns[2].Width = 260;
                grid.Columns[3].Width = 130;
                grid.Columns[4].Width = 190;
                form.Controls.Add(grid);
                grid.BringToFront();
                top.BringToFront();
                bool busy = false;
                Action updateButtons = delegate
                {
                    if (form.IsDisposed)
                        return;
                    var r = grid.SelectedRows.Count > 0 ? grid.SelectedRows[0].Tag as Dictionary<string, object> : null;
                    var state = json.ConvertToType<Dictionary<string, object>>(report["linux"]);
                    bool needs = Convert.ToBoolean(report["needs_linux"], System.Globalization.CultureInfo.InvariantCulture);
                    start.Enabled = !busy && needs && Convert.ToBoolean(state["disk"], System.Globalization.CultureInfo.InvariantCulture) && !Convert.ToBoolean(state["running"], System.Globalization.CultureInfo.InvariantCulture) && !Convert.ToBoolean(state["wrong_location"], System.Globalization.CultureInfo.InvariantCulture);
                    ubuntu.Enabled = !busy && needs && !Convert.ToBoolean(state["wrong_location"], System.Globalization.CultureInfo.InvariantCulture);
                    install.Enabled = !busy && r != null && Convert.ToBoolean(r["installable"], System.Globalization.CultureInfo.InvariantCulture) && (!needs || Convert.ToBoolean(state["running"], System.Globalization.CultureInfo.InvariantCulture)) && (!rfmix || license.Checked);
                    download.Enabled = !busy && r != null && Convert.ToBoolean(r["downloadable"], System.Globalization.CultureInfo.InvariantCulture) && (!rfmix || license.Checked);
                    source.Enabled = !busy && r != null;
                    refresh.Enabled = !busy;
                    accept.Enabled = !busy && Convert.ToBoolean(report["ready"], System.Globalization.CultureInfo.InvariantCulture) && (!rfmix || license.Checked);
                };
                Action render = delegate
                {
                    if (form.IsDisposed)
                        return;
                    grid.Rows.Clear();
                    requirements = json.ConvertToType<List<Dictionary<string, object>>>(report["requirements"]);
                    foreach (var r in requirements)
                    {
                        int n = grid.Rows.Add(V(r, "id"), V(r, "state"), V(r, "version"), Convert.ToBoolean(r["downloaded"], System.Globalization.CultureInfo.InvariantCulture) ? "Archive cached" : "Not yet loaded", Convert.ToBoolean(r["installable"], System.Globalization.CultureInfo.InvariantCulture) ? "There is an installation recipe" : "Project instructions / manual");
                        grid.Rows[n].Tag = r;
                        grid.Rows[n].Cells[0].ToolTipText = V(r, "source");
                    }
                    var state = json.ConvertToType<Dictionary<string, object>>(report["linux"]);
                    status.Text = V(state, "state") + " · " + V(report, "note") + "\nAn archive is not an installed application. Check again after setup.";
                    updateButtons();
                };
                Func<string, Task> work = async delegate (string action)
                {
                    if (busy)
                        return;
                    var r = grid.SelectedRows.Count > 0 ? grid.SelectedRows[0].Tag as Dictionary<string, object> : null;
                    busy = true;
                    updateButtons();
                    try
                    {
                        status.Text = "Procedure is ongoing:" + action + "Large downloads/compilation can take time.";
                        if (action == "ubuntu")
                        {
                            var si = new ProcessStartInfo("powershell.exe", "-NoProfile -ExecutionPolicy Bypass -File " + Quote(Path.Combine(appdir, "setup.ps1")) + " -Root " + Quote(Path.Combine(root, ".")) + " -Mode Linux -InstallWslHost") { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
                            using (var p = Process.Start(si))
                            {
                                var output = p.StandardOutput.ReadToEndAsync();
                                var error = p.StandardError.ReadToEndAsync();
                                await Task.Run(() => p.WaitForExit());
                                string text = await output + await error;
                                string log = Path.Combine(root, "DNA_Software", "Logs", "Setup", "bei-bedarf.log");
                                Directory.CreateDirectory(Path.GetDirectoryName(log));
                                File.WriteAllText(log, text);
                                if (p.ExitCode != 0)
                                    throw new InvalidOperationException("Ubuntu setup is not complete." + log);
                            }
                        }
                        else if (action == "install" || action == "download")
                        {
                            if (r == null)
                                throw new InvalidOperationException("Select the tool.");
                            Process.Start(new ProcessStartInfo(V(r, "source")) { UseShellExecute = true });
                            await DemandAction(action, V(r, "id"), license.Checked ? "--license-reviewed" : "--no-license-ack");
                        }
                        else if (action == "start")
                            await DemandAction("start");
                        report = await DemandAction("status", statusArgs);
                        render();
                    }
                    catch (Exception e) { if (!form.IsDisposed) status.Text = e.Message; }
                    finally { busy = false; updateButtons(); }
                };
                grid.SelectionChanged += delegate
                {
                    updateButtons();
                };
                license.CheckedChanged += delegate
                {
                    updateButtons();
                };
                start.Click += async delegate { await work("start"); };
                ubuntu.Click += async delegate { await work("ubuntu"); };
                install.Click += async delegate { await work("install"); };
                download.Click += async delegate { await work("download"); };
                refresh.Click += async delegate { await work("refresh"); };
                source.Click += delegate
                {
                    if (grid.SelectedRows.Count > 0)
                    {
                        var r = (Dictionary<string, object>)grid.SelectedRows[0].Tag;
                        Process.Start(new ProcessStartInfo(V(r, "source")) { UseShellExecute = true });
                    }
                };
                accept.Click += async delegate { try { if (rfmix && license.Checked) await DemandAction("acknowledge", "rfmix", "--license-reviewed"); form.DialogResult = DialogResult.OK; form.Close(); } catch (Exception e) { status.Text = e.Message; } };
                render();
                return form.ShowDialog(this) == DialogResult.OK;
            }
        }
    }
}
