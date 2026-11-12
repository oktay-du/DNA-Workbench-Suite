using System;
using System.IO;
using System.IO.Compression;
using System.Collections.Generic;
using System.Reflection;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;
namespace DnaWorkbench
{
    public static class NativeLocale
    {
        static Dictionary<string, string> messages;
        static string loadedLanguage;
        public static string Text(string english, string language)
        {
            if (String.IsNullOrEmpty(language) || language == "en" ||
                !Regex.IsMatch(language, @"\A[a-z]{2,3}(?:-[A-Z][a-z]{3})?\z"))
                return english;
            try
            {
                if (loadedLanguage != language)
                {
                    string path = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "DNA_Software/Launcher/Locales", language + ".json");
                    messages = new JavaScriptSerializer().Deserialize<Dictionary<string, string>>(File.ReadAllText(path));
                    loadedLanguage = language;
                }
                string translated;
                return messages.TryGetValue(english, out translated) ? translated : english;
            }
            catch { return english; }
        }
    }
    public static class LegacyLayout
    {
        static void MoveDirectory(string source, string target)
        {
            if (!Directory.Exists(source))
                return;
            if ((File.GetAttributes(source) & FileAttributes.ReparsePoint) != 0)
                throw new IOException("Layout migration refuses directory links: " + source);
            if (Directory.Exists(target) || File.Exists(target))
                throw new IOException("Both old and new layout paths exist. Resolve this conflict before upgrading: " + source + " / " + target);
            Directory.Move(source, target);
        }
        public static void Migrate(string root)
        {
            Dictionary<string, object> layout;
            using (var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream("DNA.Core.zip"))
            {
                if (stream == null)
                    return;
                using (var archive = new ZipArchive(stream, ZipArchiveMode.Read))
                {
                    var entry = archive.GetEntry("DNA_Software/Launcher/legacy-layout.json");
                    if (entry == null)
                        return;
                    using (var reader = new StreamReader(entry.Open()))
                        layout = new JavaScriptSerializer().Deserialize<Dictionary<string, object>>(reader.ReadToEnd());
                }
            }
            var directories = (Dictionary<string, object>)layout["directories"];
            foreach (var item in directories)
            {
                if (Convert.ToString(item.Value, System.Globalization.CultureInfo.InvariantCulture) == "Results")
                    continue;
                MoveDirectory(Path.Combine(root, item.Key), Path.Combine(root, Convert.ToString(item.Value, System.Globalization.CultureInfo.InvariantCulture)));
                MoveDirectory(Path.Combine(root, "DNA_Software", item.Key), Path.Combine(root, "DNA_Software", Convert.ToString(item.Value, System.Globalization.CultureInfo.InvariantCulture)));
            }
            var files = (Dictionary<string, object>)layout["files"];
            foreach (var item in directories)
                if (Convert.ToString(item.Value, System.Globalization.CultureInfo.InvariantCulture) == "Databases")
                    MoveDirectory(Path.Combine(root, "Projects", item.Key), Path.Combine(root, "Projects/Databases"));
            string profiles = Path.Combine(root, "Profiles");
            if (Directory.Exists(profiles))
                foreach (string profile in Directory.GetDirectories(profiles))
                {
                    string sources = Path.Combine(profile, "Sources");
                    if (!Directory.Exists(sources))
                        continue;
                    foreach (string provider in Directory.GetDirectories(sources))
                        foreach (var item in directories)
                            if (Convert.ToString(item.Value, System.Globalization.CultureInfo.InvariantCulture) == "Imports")
                                MoveDirectory(Path.Combine(provider, item.Key), Path.Combine(provider, "Imports"));
                }
            foreach (string basePath in new[] { Path.Combine(root, "Projects/Databases"), Path.Combine(root, "Projects/Launcher"), Path.Combine(root, "DNA_Software/UserData/Launcher") })
            {
                if (!Directory.Exists(basePath))
                    continue;
                RenameChildren(basePath, directories, files);
            }
        }
        static void RenameChildren(string path, Dictionary<string, object> directories, Dictionary<string, object> files)
        {
            foreach (string child in Directory.GetDirectories(path))
            {
                if ((File.GetAttributes(child) & FileAttributes.ReparsePoint) != 0)
                    continue;
                string name = Path.GetFileName(child);
                object replacement;
                string target = child;
                if (directories.TryGetValue(name, out replacement))
                {
                    target = Path.Combine(path, Convert.ToString(replacement, System.Globalization.CultureInfo.InvariantCulture));
                    MoveDirectory(child, target);
                }
                RenameChildren(target, directories, files);
            }
            foreach (string child in Directory.GetFiles(path))
            {
                object replacement;
                if (!files.TryGetValue(Path.GetFileName(child), out replacement))
                    continue;
                string target = Path.Combine(path, Convert.ToString(replacement, System.Globalization.CultureInfo.InvariantCulture));
                if (File.Exists(target))
                    throw new IOException("Layout migration refuses to replace an existing file: " + target);
                File.Move(child, target);
                if (child.EndsWith(".sqlite", StringComparison.OrdinalIgnoreCase))
                    foreach (string suffix in new[] { "-wal", "-shm" })
                    {
                        if (!File.Exists(child + suffix))
                            continue;
                        if (File.Exists(target + suffix))
                            throw new IOException("Layout migration refuses to replace a database sidecar: " + target + suffix);
                        File.Move(child + suffix, target + suffix);
                    }
            }
        }
    }
}
