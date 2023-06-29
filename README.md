# Dashboard Pro
This project is a proof of concept, bringing modern interactive plotting tools to the Eclipse research platform. This is done by leveraging PyESAPI and Streamlit to build a bridge between the Eclipse data model and Plotly (or any other python plotting library of your choice).

## Quickstart
1. Install python (see `azure-pipelines.yml` for version number)
1. Create a local, self contained, python environment:
    * `python -m venv venv`
1. Activate the local environment:
    * `.\env\Scripts\activate`
1. Install the required packages:
    * `python -m pip install --upgrade pip`
    * `pip install -r requirements.txt`
1. Launch `DashboardPro.cs` from Eclipse Scripts window.

## Building for Release
1. Use pyinstaller spec file
    * `pyinstaller .\streamlit_runner.spec --noconfirm`

## Known Issues
* Streamlit is multi-treaded, and ESAPI only supports access from a single thread. Until a workaround is found, this means any access to PyESAPI should only happen once in an isolated function decorated with `@streamlit.cache_data`