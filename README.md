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
The ``

If you have keys that you want to use, put them in the `.secrets` folder in the root. This folder will not be committed to github should you update the code.

### Virtual Environment

```commandline
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
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
from file_system.utils import in_working

file_path = in_working('sub_folder/file.pdf')
```

### Download folder
`DOWNLOAD_FOLDER` in the `.env` folder represents a folder where we can download files.

Honestly, we're not really using this folder. 

### Temp folder

`TEMP_FOLDER` in the `.env` folder represents a folder where we can put temporary files. A few of the transformation functions need to put a file somewhere while they do their work. 

These files would clutter up the working folder before producing a final result.
