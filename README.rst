usage: git_remerge.py [-h] [upstream]

Generate ``git-rebase-todo`` that redoes merges

Compared to a regular git rebase:

* Only the first parent is followed while enumerating commits
* When a commit with multiple parents is found an merge step is generated, as
  ``exec git merge <source>``

positional arguments:
  upstream    Upstream (default is `git rev-parse @{upstream}`

optional arguments:
  -h, --help  show this help message and exit
