import streamlit.web.cli as stcli
import sys

# the following are needed for PyInstaller:
import streamlit.runtime.scriptrunner.magic_funcs

if __name__ == "__main__":

    if len(sys.argv) == 1:
        print('ERROR: please provide path to streamlit script')
        sys.exit(1)

    script_path = sys.argv[1]  # first argument should be the path to the streamlit script
    script_args = sys.argv[2:]  # additional arguments are passed along to the streamlit script
    
    # monkey-patch sys arguments to be picked up by streamlit main
    sys.argv = [
        "streamlit",
        "run",
        script_path,
        "--global.developmentMode=false",
        "--"
    ] + script_args
    sys.exit(stcli.main())