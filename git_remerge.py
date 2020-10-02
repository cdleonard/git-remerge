#! /usr/bin/env python3

"""Generate rebase todo that redoes merges

Compared to a regular git rebase:
 * Only the first parent is followed when picking
 * When a commit with multiple parents is found an merge step is generated, as
`exec git merge <source>`
"""

import os
import sys
import re
import logging
import pygit2
import typing
import argparse

logger = logging.getLogger()


def create_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "upstream", nargs="?", help="Upstream (default is `git rev-parse @{upstream}`"
    )
    return parser


def git_commit_title(commit: pygit2.Commit) -> str:
    return commit.message.splitlines()[0]


def git_merge_source_from_message(message: str) -> typing.Optional[str]:
    m = re.match(
        r"^Merge remote-tracking branch '(?P<source>[^']+)' into (?P<target>.*)$",
        message,
        re.M,
    )
    if m:
        return m.group("source")
    m = re.match(
        r"^Merge branch '(?P<source>[^']+)' into (?P<target>.*)$",
        message,
        re.M,
    )
    if m:
        return m.group("source")
    m = re.match(
        r"^Merge tag '(?P<source>[^']+)' into (?P<target>.*)$",
        message,
        re.M,
    )
    if m:
        return 'tags/' + m.group("source")
    return None


class Main:
    def format_commit(self, commit):
        hexsha = str(commit.id)
        title = git_commit_title(commit)
        return "%s %s" % (hexsha[: self.commit_abbrev], title)

    def main(self, argv=None):
        self.opts = create_parser().parse_args(argv)
        repo_path = pygit2.discover_repository(os.getcwd())
        self.repo = pygit2.Repository(repo_path)
        try:
            self.commit_abbrev = self.repo.config.get_int("core.abbrev")
        except KeyError:
            self.commit_abbrev = 8
        self.todo: typing.List[str] = []

        logger.info("repo=%r", self.repo)
        if self.opts.upstream is None:
            upstream = self.repo.revparse_single("@{upstream}")
        else:
            upstream = self.repo.revparse_single(self.opts.upstream)
            upstream = upstream.peel(pygit2.GIT_OBJ_COMMIT)
        logger.info("upstream %s", self.format_commit(upstream))

        head = self.repo.head.peel()
        logger.info("head %s", self.format_commit(head))

        logger.info("git merge-base %s %s", upstream.id, head.id)
        base_id = self.repo.merge_base(upstream.id, head.id)
        base = self.repo.get(base_id)
        logger.info("base %s", self.format_commit(base))

        commit = head
        while True:
            logger.info("scan %s", self.format_commit(commit))
            par = commit.parent_ids
            commit_hexsha = str(commit.id)
            title = git_commit_title(commit)
            if len(par) == 1:
                self.todo.insert(0, "pick %s %s" % (commit_hexsha, title))
            elif len(par) > 2:
                raise Exception("Octopus merges not handled")
            else:
                merge_source = git_merge_source_from_message(commit.message)
                if not merge_source:
                    logger.warning(
                        "Failed to determine merge source from message:\n%s",
                        commit.message,
                    )
                    self.todo.insert(0, "# failed to parse commit message so merge by hexsha")
                    self.todo.insert(0, "exec git merge %s" % (par[1]))
                else:
                    self.todo.insert(0, "exec git merge %s" % (merge_source))
            # first parent only
            commit = commit.parents[0]
            # stop when reaching merge-base
            if commit.id == base.id:
                break

        for item in self.todo:
            sys.stdout.write(str(item) + "\n")


if __name__ == "__main__":
    Main().main()
