echo Running pre-commit
pip3 install black
pip3 install isort
black ./app
isort ./app