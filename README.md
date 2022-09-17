## Instructions to setup environment

To generate the pages that will be published on the website, you need to install the Pelican framework and its dependencies. To do so, you need a working python 3 environment. It is recommended to install all python packages in a virtual environement (venv).

The setup is done with the command line :

    > pip install -r requirements.txt

You are ready to contribute to the website with the [Pelican framework](https://docs.getpelican.com/en/latest/quickstart.html).

## Instructions to publish

Once you are satisfied with your local development, you are ready to publish your pages. To do so, I recommend to use Make with the 2 following commands:

    > make publish
    > make ftp_upload

Go to the website and verify that everything is working as expected. If not, just roll back.