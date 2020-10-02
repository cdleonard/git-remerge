import subprocess
import re
import os
import pytest
from contextlib import contextmanager
from git_remerge import git_merge_source_from_message
from git_remerge import Main


def test_source_from_message():
    assert git_merge_source_from_message("Merge branch 'feat' into master\n") == 'feat'
    assert git_merge_source_from_message("Merge remote-tracking branch 'origin/blah' into master\n") == 'origin/blah'


def quick_commit(title, filename, text=None):
    if text is None:
        text = title
    with open(filename, "w") as f:
        f.write(text)
    subprocess.check_call(['git', 'add', filename])
    subprocess.check_call(['git', 'commit', '-q', filename, '-m', title])


@contextmanager
def local_chdir(newdir):
    oldcwd = os.getcwd()
    os.chdir(newdir)
    try:
        yield
    finally:
        os.chdir(oldcwd)


@pytest.fixture()
def fakerepo(tmp_path):
    with local_chdir(tmp_path):
        subprocess.check_call('git init -q work', shell=True)

    with local_chdir(tmp_path / 'work'):
        subprocess.check_call('git config user.email pytest@example.com', shell=True)
        subprocess.check_call('git config user.name test', shell=True)
        # Create initial commit on main branch and tag it as v0.1
        quick_commit('base', 'README', 'test repo')
        subprocess.check_call('git branch -q -m main', shell=True)
        subprocess.check_call('git tag -a v0.1 -m "v0.1"', shell=True)


def mainrun(args):
    """Run the tool"""
    main = Main()
    main.main(args)
    return main


def test_remerge(fakerepo, tmp_path):
    with local_chdir(tmp_path / 'work'):
        # commit on feature branch
        subprocess.check_call('git checkout -q -b feat', shell=True)
        quick_commit('feat1', 'feat.txt', 'feat1')

        # commit on main branch, merge feat and commit again
        subprocess.check_call('git checkout -q main', shell=True)
        quick_commit('main1', 'main.txt', 'main1')
        subprocess.check_call('git merge --no-edit --no-ff feat', shell=True)
        quick_commit('main2', 'main.txt', 'main2')

        main = mainrun(['v0.1'])
        assert(re.match('^pick [0-9a-f]+ main1', main.todo[0]))
        assert(re.match('^exec git merge', main.todo[1]))
        assert(re.match('^pick [0-9a-f]+ main2', main.todo[2]))
