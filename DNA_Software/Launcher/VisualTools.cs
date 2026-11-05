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
        async Task<Dictionary<string, object>> VisualAction(string action, params string[] values)
        {
            var si = new ProcessStartInfo(python, Quote(Path.Combine(appdir, "visual_tools.py")) + " " + action + " " + String.Join(" ", values.Select(Quote))) { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true, StandardOutputEncoding = Encoding.UTF8, StandardErrorEncoding = Encoding.UTF8 };
            si.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
            using (var p = Process.Start(si))
            {
                var stdout = p.StandardOutput.ReadToEndAsync();
                var stderr = p.StandardError.ReadToEndAsync();
                await Task.Run(() => p.WaitForExit());
                string text = await stdout;
                string err = await stderr;
                if (p.ExitCode != 0)
                    throw new InvalidOperationException(text + err);
                return json.Deserialize<Dictionary<string, object>>(text);
            }
        }
        async void ShowVisualTools()
        {
            try
            {
                var report = await VisualAction("list");
                var entries = json.ConvertToType<List<Dictionary<string, object>>>(report["tools"]);
                string owner = Person();
                using (var f = new Form { Text = "Genom-Visualisierung · " + owner, ClientSize = new Size(1120, 780), MinimumSize = new Size(900, 650), StartPosition = FormStartPosition.CenterParent, Font = new Font("Segoe UI", 10), BackColor = paper, AutoScaleMode = AutoScaleMode.Dpi, AutoScaleDimensions = new SizeF(96, 96) })
                {
                    var top = new FlowLayoutPanel { Dock = DockStyle.Top, Height = 55, Padding = new Padding(12) };
                    var find = new TextBox { Width = 300 };
                    top.Controls.Add(new Label { Text = "Search tools", AutoSize = true, Padding = new Padding(0, 5, 8, 0) });
                    top.Controls.Add(find);
                    var supported = new CheckBox { Text = "Only runnable adapters", AutoSize = true, Checked = true };
                    top.Controls.Add(supported);
                    f.Controls.Add(top);
                    var bottom = new Panel { Dock = DockStyle.Bottom, Height = 365, Padding = new Padding(12) };
                    f.Controls.Add(bottom);
                    var details = new Label { Dock = DockStyle.Top, Height = 85, Padding = new Padding(4), ForeColor = ink };
                    bottom.Controls.Add(details);
                    var table = new TableLayoutPanel { Dock = DockStyle.Top, Height = 165, ColumnCount = 3, RowCount = 4 };
                    table.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 175));
                    table.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
                    table.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 160));
                    bottom.Controls.Add(table);
                    table.BringToFront();
                    var file = new TextBox { Dock = DockStyle.Fill };
                    var choose = Button("Select the file ...", Color.White, ink);
                    choose.Dock = DockStyle.Fill;
                    var library = new ComboBox { Dock = DockStyle.Fill, DropDownStyle = ComboBoxStyle.DropDownList };
                    library.Items.Add("Select the registered dataset ...");
                    var sources = ReadLibrary();
                    foreach (var row in sources)
                        library.Items.Add(V(row, "provider") + " · " + V(row, "label") + " · " + V(row, "original_name"));
                    library.SelectedIndex = 0;
                    var reference = new TextBox { Dock = DockStyle.Fill };
                    var chooseRef = Button("Select FASTA ...", Color.White, ink);
                    chooseRef.Dock = DockStyle.Fill;
                    var region = new FlowLayoutPanel { Dock = DockStyle.Fill };
                    var chrom = new TextBox { Text = "1", Width = 80 };
                    var from = new NumericUpDown { Minimum = 1, Maximum = 999999999, Value = 1, Width = 125 };
                    var to = new NumericUpDown { Minimum = 1, Maximum = 999999999, Value = 1000000, Width = 125 };
                    region.Controls.Add(new Label { Text = "Chr", AutoSize = true });
                    region.Controls.Add(chrom);
                    region.Controls.Add(new Label { Text = "von", AutoSize = true });
                    region.Controls.Add(from);
                    region.Controls.Add(new Label { Text = "bis", AutoSize = true });
                    region.Controls.Add(to);
                    table.Controls.Add(new Label { Text = "Quelldatei", AutoSize = true }, 0, 0);
                    table.Controls.Add(file, 1, 0);
                    table.Controls.Add(choose, 2, 0);
                    table.Controls.Add(new Label { Text = "Source database", AutoSize = true }, 0, 1);
                    table.Controls.Add(library, 1, 1);
                    table.SetColumnSpan(library, 2);
                    table.Controls.Add(new Label { Text = "Referenz (IGV/JBrowse)", AutoSize = true }, 0, 2);
                    table.Controls.Add(reference, 1, 2);
                    table.Controls.Add(chooseRef, 2, 2);
                    table.Controls.Add(new Label { Text = "Genomfenster · 1-basiert", AutoSize = true }, 0, 3);
                    table.Controls.Add(region, 1, 3);
                    table.SetColumnSpan(region, 2);
                    for (int i = 0; i < 4; i++)
                        table.RowStyles.Add(new RowStyle(SizeType.Absolute, 40));
                    var actions = new FlowLayoutPanel { Dock = DockStyle.Bottom, Height = 85 };
                    bottom.Controls.Add(actions);
                    var install = Button("Install / repair", teal, Color.White);
                    install.Width = 210;
                    actions.Controls.Add(install);
                    var launch = Button("Mit Datensatz starten", teal, Color.White);
                    launch.Width = 200;
                    actions.Controls.Add(launch);
                    var project = Button("Project page", Color.White, ink);
                    project.Width = 140;
                    actions.Controls.Add(project);
                    var refresh = Button("Katalog aktualisieren", Color.White, ink);
                    refresh.Width = 195;
                    actions.Controls.Add(refresh);
                    var results = Button("Result folder", Color.White, ink);
                    results.Width = 160;
                    actions.Controls.Add(results);
                    var status = new Label { Dock = DockStyle.Bottom, Height = 30, Text = "Tested local adapters with optional installation. Other projects are marked as research." };
                    bottom.Controls.Add(status);
                    status.BringToFront();
                    var grid = new DataGridView { Dock = DockStyle.Fill, ReadOnly = true, AllowUserToAddRows = false, RowHeadersVisible = false, SelectionMode = DataGridViewSelectionMode.FullRowSelect, MultiSelect = false, BackgroundColor = Color.White, AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill, ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.AutoSize };
                    foreach (string col in new[] { "Werkzeug", "Status", "Version", "Formate / Eingaben", "License" })
                        grid.Columns.Add(col, col);
                    grid.Columns[0].FillWeight = 24;
                    grid.Columns[1].FillWeight = 22;
                    grid.Columns[2].FillWeight = 10;
                    grid.Columns[3].FillWeight = 35;
                    grid.Columns[4].FillWeight = 12;
                    f.Controls.Add(grid);
                    grid.BringToFront();
                    bool busy = false;
                    string output = "";
                    string openPath = "";
                    Func<Dictionary<string, object>> selectedTool = () => grid.SelectedRows.Count == 0 ? null : grid.SelectedRows[0].Tag as Dictionary<string, object>;
                    Action buttons = delegate
                    {
                        if (f.IsDisposed)
                            return;
                        var row = selectedTool();
                        bool adapter = row != null && Convert.ToBoolean(row["installable"], System.Globalization.CultureInfo.InvariantCulture);
                        install.Enabled = !busy && adapter;
                        launch.Enabled = !busy && adapter && Convert.ToBoolean(row["installed"], System.Globalization.CultureInfo.InvariantCulture) && !String.IsNullOrWhiteSpace(file.Text);
                        refresh.Enabled = choose.Enabled = chooseRef.Enabled = library.Enabled = !busy;
                        results.Enabled = output != "";
                        project.Enabled = row != null;
                    };
                    Action render = delegate
                    {
                        if (f.IsDisposed)
                            return;
                        string id = selectedTool() == null ? "" : V(selectedTool(), "id");
                        grid.Rows.Clear();
                        foreach (var row in entries)
                        {
                            if (supported.Checked && !Convert.ToBoolean(row["installable"], System.Globalization.CultureInfo.InvariantCulture))
                                continue;
                            if ((V(row, "name") + " " + V(row, "description") + " " + V(row, "formats")).IndexOf(find.Text, StringComparison.OrdinalIgnoreCase) < 0)
                                continue;
                            bool adapter = Convert.ToBoolean(row["installable"], System.Globalization.CultureInfo.InvariantCulture);
                            int n = grid.Rows.Add(V(row, "name"), Convert.ToBoolean(row["installed"], System.Globalization.CultureInfo.InvariantCulture) ? "Installed · Checked locally" : adapter ? "Bei Bedarf installieren" : "Research · no adapter", V(row, "version"), V(row, "formats"), V(row, "license"));
                            grid.Rows[n].Tag = row;
                            grid.Rows[n].Cells[0].ToolTipText = V(row, "url");
                            if (V(row, "id") == id)
                                grid.Rows[n].Selected = true;
                        }
                        buttons();
                    };
                    grid.SelectionChanged += delegate
                    {
                        var row = selectedTool();
                        details.Text = row == null ? "Select the tool." : V(row, "description") + "\nEingaben: " + V(row, "formats") + "\nQuelle: " + V(row, "source") + " · " + V(row, "url");
                        buttons();
                    };
                    find.TextChanged += delegate
                    {
                        render();
                    };
                    supported.CheckedChanged += delegate
                    {
                        render();
                    };
                    file.TextChanged += delegate
                    {
                        buttons();
                    };
                    library.SelectedIndexChanged += delegate
                    {
                        if (library.SelectedIndex > 0)
                        {
                            var row = sources[library.SelectedIndex - 1];
                            file.Text = V(row, "path");
                            string build = V(row, "build");
                            if (build == "GRCh37" || build == "GRCh38")
                            {
                                string refdir = Path.Combine(root, "References", "FASTA_" + build);
                                if (Directory.Exists(refdir))
                                    reference.Text = Directory.GetFiles(refdir, "*.fa").FirstOrDefault() ?? "";
                            }
                        }
                    };
                    choose.Click += delegate
                    {
                        using (var d = new OpenFileDialog { Title = "genome file for:" + owner, Filter = "Genome files|*.vcf;*.gz;*.bgz;*.bam;*.cram;*.bed;*.gff;*.gff3|All files|*.*" })
                            if (d.ShowDialog(f) == DialogResult.OK)
                                file.Text = d.FileName;
                    };
                    chooseRef.Click += delegate
                    {
                        using (var d = new OpenFileDialog { Title = "Appropriate local FASTA with .fai", Filter = "FASTA|*.fa;*.fasta;*.fna" })
                            if (d.ShowDialog(f) == DialogResult.OK)
                                reference.Text = d.FileName;
                    };
                    project.Click += delegate
                    {
                        var row = selectedTool();
                        if (row != null)
                            Process.Start(new ProcessStartInfo(V(row, "url")) { UseShellExecute = true });
                    };
                    results.Click += delegate
                    {
                        if (Directory.Exists(output))
                            Process.Start(new ProcessStartInfo(output) { UseShellExecute = true });
                    };
                    Func<string, Task> work = async delegate (string action)
                    {
                        if (busy)
                            return;
                        var row = selectedTool();
                        busy = true;
                        buttons();
                        try
                        {
                            status.Text = action == "refresh" ? "Project lists are updated ..." : "Process runs in the background; large files and installations take time...";
                            if (action == "refresh")
                            {
                                var response = await VisualAction("refresh");
                                status.Text = V(response, "status");
                            }
                            else if (action == "install")
                            {
                                var response = await VisualAction("install", V(row, "id"));
                                status.Text = V(response, "status") + " · " + V(response, "version");
                            }
                            else if (action == "prepare")
                            {
                                if (to.Value < from.Value)
                                    throw new InvalidOperationException("The end position must be after the beginning.");
                                string dir = Path.Combine(root, "DNA_Software", "UserData", "Launcher", "Visualisierungsanfragen");
                                Directory.CreateDirectory(dir);
                                string request = Path.Combine(dir, Guid.NewGuid().ToString("N") + ".json");
                                File.WriteAllText(request, json.Serialize(new Dictionary<string, object> { { "tool", V(row, "id") }, { "person", owner }, { "file", file.Text }, { "reference", reference.Text }, { "chrom", chrom.Text }, { "start", (long)from.Value }, { "end", (long)to.Value } }), new UTF8Encoding(false));
                                var response = await VisualAction("prepare", request);
                                output = V(response, "folder");
                                openPath = V(response, "path");
                                f.Close();
                                return;
                            }
                            report = await VisualAction("list");
                            entries = json.ConvertToType<List<Dictionary<string, object>>>(report["tools"]);
                            render();
                        }
                        catch (Exception e) { if (!f.IsDisposed) status.Text = e.Message; MessageBox.Show(f, e.Message, "Visualization could not be prepared"); }
                        finally { busy = false; buttons(); }
                    };
                    install.Click += async delegate { await work("install"); };
                    launch.Click += async delegate { await work("prepare"); };
                    refresh.Click += async delegate { await work("refresh"); };
                    f.FormClosing += delegate (object s, FormClosingEventArgs e)
                    {
                        if (busy && openPath == "")
                        {
                            e.Cancel = true;
                            status.Text = "The background process is still underway.";
                        }
                    };
                    render();
                    f.ShowDialog(this);
                    if (openPath != "")
                    {
                        if (IsModernShell())
                            familyView.CoreWebView2.PostWebMessageAsJson(json.Serialize(new Dictionary<string, object> { { "action", "suite-view" }, { "path", openPath } }));
                        else
                            OpenWorkspacePath(openPath);
                    }
                }
            }
            catch (Exception e) { MessageBox.Show(this, e.Message, "Visualization catalogue not available"); }
        }
    }
}
