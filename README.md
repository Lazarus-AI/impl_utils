# Implementation Toolkit

## Overview

So... you have some files and you need to do some stuff with them in order to onboard a new customer.

Well... this is the place for you!

## Getting Started

```commandline
cp .env.example .env
```

Then edit the `.env` and set up the appropriate secrets.

The `WORKING_FOLDER` is where you are wanting to put the files you intend to edit and be actively working on.
The `DOWNLOAD_FOLDER` is where you want to store files that you've downloaded from external services like firebase. There's no rule that this couldn't also be your working folder or a subfolder inside of it.

If you have keys that you want to use, put them in the `.secrets` folder in the root. This folder will not be committed to github should you update the code.

### Docs

You can read the documentation [here](docs/_build/index.html)

### Virtual Environment

```commandline
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

#### Additional installs

To use OCR and some PDF conversions, you'll need poppler installed on your computer.

For a mac:
```commandline
brew install poppler
```

### Using Jupyter Notebook

If you want to use these methods in a jupyter notebook, you'll need to install a new kernal based on virtual environment.

After you've created and activate the virtual environment, you can do that by running this command:

```commandline

python -m ipykernel install --user --name=impl_utils --display-name="Implementation Utilities"
```

This will create a new notebook type. So, the next time you create a notebook, it will have this environment as an option. Which will auto include all external libraries in this virtual environment for import and use.

Running the above command is necessary to make the "scratch_pad" notebook that is included and already set up to work with this toolkit.

To start jupyter:
```commandline
jupyter notebook
```


### PDF Conversion

To power PDF conversions locally, we need LibreOffice installed. You can do that easily through brew.

```commandline
brew install libreoffice
```

### One Drive Capabilities

One drive is a proper file system. To enable integrating with one drive with our package, the following steps must be completed:

1. Go to Azure Portal (https://portal.azure.com/)
2. Sign in with your Microsoft account
3. In the Azure Portal, search for "App registrations" in the top search bar
4. Click on "App registrations" from the results
5. Click "+ New registration" button
6. Select Accounts in any organizational directory and personal Microsoft accounts
7. For Redirect URI:
    1. select "Web" from the dropdown.
    2. Enter http://localhost:3000/auth/callback (this is your ONE_DRIVE_REDIRECT_URI)
    3. Click Register.
8. Copy the "Application (client) ID" - this is your ONE_DRIVE_CLIENT_ID
9. Copy the "Directory (tenant) ID" - this is your ONE_DRIVE_TENANT_ID
10. For client secret:
    1. In the left sidebar, click "Certificates & secrets"
    2. Click "+ New client secret"
    3. Add a description
    4. Choose an expiry period
    5. Click "Add"
    6. IMMEDIATELY COPY THE SECRET VALUE - this is your ONE_DRIVE_CLIENT_SECRET (you will not see this value again)
11. Set API Permissions
    1. In the left sidebar, click "API permissions"
    2. Click "+ Add a permission"
    3. Select "Microsoft Graph"
    4. Choose "Delegated permissions"
    5. Search for and add these permissions:
        1. Files.ReadWrite (Read and write user files)
        2. Files.ReadWrite.All (Read and write all files user can access)
        3. User.Read (Sign in and read user profile)
    6. Click "Add permissions"
12. You can see the onedrive operations here: https://onedrive.live.com

### Common Recipes

Upload a document to firebase and get a signed url:

```python
import os

from config import WORKING_FOLDER
from sync.firebase.utils import upload


results = upload(os.path.join(WORKING_FOLDER, "sub_dir/empty.txt"))
print(f"Uploading {results[0]} to {results[1]}")
```


## Contributing

Feel free to add more utilites. Be sure to try and keep a stand practice when organizing the utilites.

Also, run pre-commit when adding new code:

```commandline
pre-commit install
```

## Concepts

### Folders
Our AIs need documents to work on. When we want to programmatically work with files we need to work with file paths.

We wanted to take the confusion out of trying to figure out absolute file paths so there are a number of helpers to make this easier.

We have 3 folders that are specified in the code:

#### Working folder
This is the folder that you are putting the materials that you want to work with. Feel free to organize this how you choose.

Set the `WORKING_FOLDER` in your `.env` file to this folder. To short cut referring to files in this folder, there's a function called `in_working()`

```python
from file_system.utils import in_working, in_downloads, in_tmp

file_path = in_working('sub_folder/file.pdf')
```

### Download folder
`DOWNLOAD_FOLDER` in the `.env` folder represents a folder where we can download files.

Honestly, we're not really using this folder.

### Updating the docs

```commandline
cd docs
sphinx-apidoc -o . ../src
make html
```
