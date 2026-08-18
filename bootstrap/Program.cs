using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Windows.Forms;

internal static class Program
{
    private const string PayloadResource = "KayouInstaller.Payload";
    private const string PayloadVersion = "4.0.1-bootstrap-2";

    [STAThread]
    private static void Main()
    {
        try
        {
            string runtimeDirectory = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "KayouInstaller",
                "runtime"
            );
            Directory.CreateDirectory(runtimeDirectory);

            string payload = Path.Combine(runtimeDirectory, "KayouInstaller.exe");
            string marker = Path.Combine(runtimeDirectory, "bootstrap-version.txt");
            bool installPayload = !File.Exists(payload)
                || !File.Exists(marker)
                || File.ReadAllText(marker).Trim() != PayloadVersion;

            if (installPayload)
            {
                ExtractPayload(payload);
                File.WriteAllText(marker, PayloadVersion);
            }

            // A PyInstaller executable must be treated as a fresh application,
            // never as a worker belonging to the updater that started us.
            Environment.SetEnvironmentVariable("PYINSTALLER_RESET_ENVIRONMENT", "1");
            Environment.SetEnvironmentVariable("_PYI_APPLICATION_HOME_DIR", null);
            Environment.SetEnvironmentVariable("_MEIPASS2", null);

            var start = new ProcessStartInfo(payload)
            {
                UseShellExecute = false,
                WorkingDirectory = runtimeDirectory,
            };
            start.EnvironmentVariables["PYINSTALLER_RESET_ENVIRONMENT"] = "1";
            start.EnvironmentVariables.Remove("_PYI_APPLICATION_HOME_DIR");
            start.EnvironmentVariables.Remove("_MEIPASS2");
            Process.Start(start);
        }
        catch (Exception error)
        {
            MessageBox.Show(
                "Impossible de démarrer KayouInstaller.\n\n" + error.Message,
                "KayouInstaller",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            );
        }
    }

    private static void ExtractPayload(string destination)
    {
        string temporary = destination + ".new";
        using (Stream source = Assembly.GetExecutingAssembly().GetManifestResourceStream(PayloadResource))
        {
            if (source == null)
                throw new InvalidOperationException("Le moteur KayouInstaller est absent du lanceur.");
            using (var output = new FileStream(temporary, FileMode.Create, FileAccess.Write, FileShare.None))
                source.CopyTo(output);
        }

        if (File.Exists(destination))
            File.Delete(destination);
        File.Move(temporary, destination);
    }
}
