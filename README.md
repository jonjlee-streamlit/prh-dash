# prh-dash

Sample financial dashboard built on [Streamlit](https://streamlit.io/)

# Development Setup

* This application is built in Python using the Streamlit library
* Set up (GitHub Codespaces)[https://github.com/codespaces/]
    * Start a new Codespace and clone the latest version of the main branch of this project.
    * [`.devcontainer/devcontainer.json`](.devcontainer/devcontainer.json) defines that Python 3.10 is used. This is the [latest version supported by Streamlit](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app) as of 4/2023.
    * On launch, running [`bin/upgrade.sh`](bin/upgrade.sh). This upgrades `pip`, `pipenv`, and all dependencies to the latest versions. 
    
        *Note, since dependency versions are specified as `= "*"`, dependencies with new major versions may include breaking changes require code updates.*
* Running locally
    * [`bin/start.sh`](bin/start.sh) starts the streamlit server and disables CORS protection as required to run in Codespaces [(see forum)](https://github.com/orgs/community/discussions/18038).
    * The interactive commands to run in Codespaces:
        ```
        pipenv shell
        streamlit run app.py --server.enableCORS false --server enableXsrfProtection false
        ```
    * This project uses a Python virtual environment, managed by [`pipenv`](https://pipenv-fork.readthedocs.io/en/latest/). To run python locally, first enter the projects virtual environment using: 
        ```
        pipenv shell
        python
        ````
* VSCode
    * To be able to run debugger, point to the correct Python instance: `Python: Select Interpreter > select virtual env from pipenv`