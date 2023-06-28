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

// [assembly: ESAPIScript(IsWriteable = true)]

namespace VMS.TPS
{
    public class Script
    {
        public void Execute(ScriptContext context)  //, System.Windows.Window window, ScriptEnvironment environment)
        {
            (new DashboardPro()).Execute(context);
        }
    }

    public class DashboardPro
    {
        const string PYTHON_ENV = "env";
        const string PYTHON_EXE = "python.exe";
        public void Execute(ScriptContext context)
        {
            this.LaunchDashboard(context);
        }
        public void LaunchDashboard(ScriptContext context, [CallerFilePath] string pathHere = "")
        {
            var workingDirectory = Path.GetDirectoryName(pathHere);

            var pythonPath = Path.Combine(workingDirectory, PYTHON_ENV, "Scripts", PYTHON_EXE);
            var stRunnerPath = Path.Combine(workingDirectory, "streamlit_runner.py");
            var scriptPath = Path.Combine(workingDirectory, "dashboard.py");
            
            var startInfo = new ProcessStartInfo(pythonPath);
            startInfo.UseShellExecute = false;                        
            startInfo.Arguments = stRunnerPath + " " + scriptPath +
                ArgBuilder("plan-id", context.PlanSetup.Id) +
                ArgBuilder("course-id", context.PlanSetup.Course.Id) +
                ArgBuilder("patient-id", context.Patient.Id);

            //MessageBox.Show(pythonPath + startInfo.Arguments,"Arguments (press ctrl+c to copy to clipboard)");
            var py = Process.Start(startInfo);
        }
        
        public static String ArgBuilder(String key, String value)
        {
            var cleanValue = value == null ? "" : value;
            return " --" + key + " \"" + cleanValue + "\"";
        }

    }
}