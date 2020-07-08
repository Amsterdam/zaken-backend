echo Installing pre-commit hooks
rm -f .git/hooks/pre-commit
ln -s app/development/pre-commit.sh .git/hooks/pre-commit