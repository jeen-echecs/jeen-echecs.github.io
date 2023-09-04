[![Contribute with Gitpod](https://img.shields.io/badge/Contribute%20with-Gitpod-908a85?logo=gitpod)](https://gitpod.io/#https://github.com/jeen-echecs/jeen-echecs.github.io)

## Instructions to setup environment

I recommend to use the Gitpod environment for development. Everything works fine and you don’t have to deal with the configuration of your workstation. If you prefer to use your workstation, follow the instructions below.

To generate the pages that will be published on the website, you need to install the Pelican framework and its dependencies. To do so, you need a working python 3 environment. It is recommended to install all python packages in a virtual environement (venv).

The setup is done with the command line :

    > pip install -r requirements.txt

You are ready to contribute to the website with the [Pelican framework](https://docs.getpelican.com/en/latest/quickstart.html).

## Testing locally

Before publishing to the website, you must test your change locally. I recommend to use Make by running `make devserver`

## Instructions to publish

Once you are satisfied with your local development, you are ready to publish your pages. Just commit your code in the main branch and the deployment will be triggered automatically by GitHub Action. Once the deployment is done, go to the website and verify that everything is working as expected. If not, just revert your change.
