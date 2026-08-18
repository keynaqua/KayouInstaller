using System;
using System.Collections;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using System.Windows.Forms;

internal static class Program
{
    private const string PayloadResource = "KayouInstaller.Payload";

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
            if (!PayloadMatches(payload))
                ExtractPayload(payload);

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

    private static bool PayloadMatches(string destination)
    {
        if (!File.Exists(destination))
            return false;

        using (var algorithm = SHA256.Create())
        using (Stream embedded = Assembly.GetExecutingAssembly().GetManifestResourceStream(PayloadResource))
        using (var installed = new FileStream(destination, FileMode.Open, FileAccess.Read, FileShare.Read))
        {
            if (embedded == null)
                return false;
            byte[] expected = algorithm.ComputeHash(embedded);
            byte[] actual = algorithm.ComputeHash(installed);
            return StructuralComparisons.StructuralEqualityComparer.Equals(expected, actual);
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
