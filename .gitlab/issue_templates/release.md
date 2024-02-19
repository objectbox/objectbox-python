**Check-list**

- [ ] Update version in `objectbox/__init__.py`
- [ ] Check/update dependencies:
  - [ ] `requirements.txt`: test and increase max. supported versions
  - [ ] Update the C library version in `download-c-lib.py` and `objectbox/c.py`
- [ ] Check GitLab CI passes on main branch
- [ ] Update `README.md`: ensure all info is up-to-date.
- [ ] Commit and push to GitHub
- [ ] Clean, run tests and build: `make all`
- [ ] Publish to PyPI: `make publish`
  - For this, you will need our login data for https://pypi.org/account/login - it can be found in 1pass
- [ ] Create a GitHub release
- [ ] Announce in GitHub issues, create release announcement/blog post.
