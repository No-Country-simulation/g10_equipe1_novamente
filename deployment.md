# FastAPI Project - Deployment

## Docker Compose

For deployment to your own server, see the [Docker Compose deployment guide](./deployment-docker-compose.md).

## GitHub Repository Automation

Install the following GitHub Apps to enable the included repository automation:

* [PR Push](https://github.com/apps/pr-push) lets the pre-commit workflow push automated fixes to pull request branches.
* [PR Submit](https://github.com/apps/pr-submit) lets the **Bump pre-commit hooks** workflow create pull requests.

To publish code coverage with [Smokeshow](https://github.com/samuelcolvin/smokeshow), add `SMOKESHOW_AUTH_KEY` as a repository secret.
