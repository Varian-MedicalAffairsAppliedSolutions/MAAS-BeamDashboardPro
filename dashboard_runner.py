import streamlit
import streamlit.web.cli as stcli
import streamlit.runtime.scriptrunner.magic_funcs  # otherwise it's missed by PyInstaller
import pyarrow.vendored.version  # same, for PyInstaller
import sys

if __name__ == "__main__":
    script_path = sys.argv[1]  # first argument should be the path to the streamlit script
    script_args = sys.argv[2:]  # additional arguments are passed along to the streamlit script
    
    # monkey-patch sys arguments to be picked up by streamlit main
    sys.argv = [
        "streamlit",
        "run",
        script_path,
        "--global.developmentMode=false",
        "--"
    ] + sys.argv[2:]
    sys.exit(stcli.main())