using System;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Threading;
using System.Collections.Generic;
using VMS.TPS.Common.Model.API;
using VMS.TPS.Common.Model.Types;
using System.Reflection;
using System.IO;
using System.Diagnostics;
using System.Runtime.CompilerServices;

[assembly: ESAPIScript(IsWriteable = true)]

//TODO: move this to python (PyESAPI) to unify the code base. Still, check for dose object before launching.

namespace VMS.TPS
{
    public class Script
    {
        public void Execute(ScriptContext context, System.Windows.Window window, ScriptEnvironment environment){
            (new DashboardPro()).Execute(context,window);  // avoids intellisense conflicts with duplicate definitions
        }
    }

    public class DashboardPro
    {
        const string PYTHON_ENV = "env";
        const string PYTHON_EXE = "python.exe";
        public void Execute(ScriptContext context, System.Windows.Window window)
        {
            this.LaunchDoseRateCalculator(context);
        }
        public void LaunchDoseRateCalculator(ScriptContext context, [CallerFilePath] string pathHere = "")
        {
            var workingDirectory = Path.GetDirectoryName(pathHere);
            var pythonPath = Path.Combine(workingDirectory, PYTHON_ENV, "Scripts", PYTHON_EXE);
            var runnerPath = Path.Combine(workingDirectory, "dashboard_runner.py");
            var scrptPath = Path.Combine(workingDirectory, "dashboard.py");
            var startInfo = new ProcessStartInfo(pythonPath);  // encountered some unexpected behavior with default cmd shell (poor timer resolution affected pynetdicom implementation)
            startInfo.UseShellExecute = false;
                        
        
            startInfo.Arguments = runnerPath + " " + scrptPath +
                ArgBuilder("plan-id", context.PlanSetup.Id) +
                ArgBuilder("course-id", context.PlanSetup.Course.Id) +
                ArgBuilder("patient-id", context.Patient.Id);

            MessageBox.Show(pythonPath + startInfo.Arguments,"Arguments (press ctrl+c to copy to clipboard)");
            startInfo.CreateNoWindow = true;
            startInfo.UseShellExecute = true;
            var py = Process.Start(startInfo);
            MessageBox.Show("Click ok to stop dashboard","Dashboard running");
            py.Kill();
        }
        
        public static String ArgBuilder(String key, String value)
        {
            var cleanValue = value == null ? "" : value;
            return " --" + key + " \"" + cleanValue + "\"";
        }

    }
}