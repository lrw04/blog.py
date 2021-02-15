# blog.py

blog.py is a flexible static blog generator written
in Python.

## Prerequisites

- Python 3
- rjsmin and rcssmin
- bs4
- Pandoc

blog.py is tested only with the latest version of the
beforementioned software.

## Blog Repository Structure

```
- (repo)
  - documents: root for documents
    - folders or files representing categories and documents
  - static: root for static resources
  - templates: root for HTML templates
  - blog.py: a copy of blog.py
  - config.yaml: global blog generation configuration
```

An example is in the `example` folder of the repository.

## Category Structure

A category is the `documents` folder in the root,
containing subcategories represented by subfolders,
documents as Markdown files, and `config.yaml`
containing category configuration.

In `config.yaml`, the following keys are processed
by blog.py:

- `title`: a required string representing the title of
the category. Specifically, the title of the root
category represents the blog title.
- `brief`: an optional boolean indicating whether the
category has further description. When this is `True`,
blog.py will add `brief.html` in the folder to the
respective blob folder. Defaults to `False`.

The subcategories and documents under a category will
be recongnized by blog.py and put into the
`subcategories` and `documents` keys of the category
object, each being dictionaries with keys filenames,
and points to the child objects. For this reason, if
the category config has these keys, they will be
ignored and overwritten.

Since `blob` and `static` serve special purposes in
the generated website, these names should be avoided
as names for subcategories of root.

## Document Structure

A document is a `.md` file in the folder of any
category. It must contain a metadata header represented by a YAML section.

The following keys in metadata are processed by
blog.py:

- `title`: a required string representing the title of
the document.
- `modification`: a required string representing the
modification time of the document. It is required that
the time is in the format specified in global
configuration. The time will be converted into UNIX
timestamps.
- `hidden_until`: an optional string in the same
format as `modification` representing the publication
time. blog.py will ignore the document if the current
date is before `hidden_until`.

The document content will be taken the first few
characters to generate content peeks. The peek content
will be equivallent to a `peek` key in the metadata,
but will be overrided by it.

Since `index.html` is used for the index page by many
servers, you are advised to not use `index.md` as
names for documents. Currently, document templates are
copied after the index templates, so index page would
not work.

For a similar reason, `brief.md` should also be
avoided, though the clash happens in the blob
directory.

## Templates

In `templates`, HTML templates for document and
category pages must exist. Templates will be copied as
the respective HTML files in the site. Note that no
processing will be done by blog.py, so loaders written
in JavaScript are required to make the website
functional.

In particular, `document.html` and `index.html` are
the templates for documents and indexes respectively,
and no other file will be processed.

## Global Configuration

In `config.yaml` in the root, there are several keys
processed by blog.py, all of which are required:

- `pandoc_args`: a list of strings, which will be
passed to Pandoc in addition to specification of input
output.
- `artifacts_dir`: a string representing the output
folder relative to the root.
- `datetime_format`: a string representing the format
of times, in the format used by Python's `datetime
strptime`.
- `timezone`: a number representing the timezone of
times written in document headers.
- `peek_length`: a number, the maximum length of
content peeks.
- `rss`:
  - `desc`: a string, the feed description.
  - `domain`: a string, the domain used in feed URLs.
  - `lang`: a string, the feed language.

## Artifacts

blog.py puts the generated site in the location
specified in the global configuration.

Assuming `site` is the output directory, for a
category at path `x`, `site/x/index.html` be a copy of
the index template, and `site/blob/x` will contain
`brief.html` if it is enabled.

For a document at path `x`, `site/x` will be a copy of
the document template, and `site/blog/x` will be the
converted HTML.

`site/index.json` will be the object of the root
category. `site/rss.xml` will be the RSS feed. `site
static` will be `static` copied over.
