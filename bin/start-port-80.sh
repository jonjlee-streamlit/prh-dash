# Start streamlit on port 80 as background process
# This is not recommended, since streamlit only supports http connections. Deployment should use 
# a reverse proxy to provide https support.
sudo -E env PATH=$PATH nohup pipenv run streamlit run app.py --server.port 80 &> nohup.out &