# PyFoto

> In active development

PyFoto is a simple image gallery and tagging system.

It allows for directory ingests of images, and will automatically create thumbnails and register them in a local
database. This allows for fast access during searches and prevents duplicate photos being ingested.


## Install

> Python 3 only

> Pillow is a requirement that may require additional libraries,
> refer to [their documentation](http://pillow.readthedocs.org/en/3.0.x/installation.html) for help.

PyFoto is currently in development. Do NOT install to your main system. There will be unmigrated DB changes
as well as API switches that will completely screw you over if you do. Instead, simply download the entire package
and install it in a virtual environment.

```
   pyvenv-3.4 venv
   venv/bin/python setup.py develop
```



