# Contributing

## Bug report and feature suggestion

If you have found an issue with gweatherrouting, first do a search in the [gweatherrouting issue tracker](https://github.com/dakk/gweatherrouting/issues) to ensure that there are no existing issues with
similar content. If you can't find another related issue, open a new one: please try to be as detailed as possible.


## Submit a pull request

If you want to contribute to gweatherrouting, you have to follow this flow:

1. First fork the [gweatherrouting repository](https://github.com/dakk/gweatherrouting) so you can work on your copy of the code
2. Clone it locally by running ```git clone https://github.com/YOUR_USERNAME/gweatherrouting.git```
3. Add the original repo as upstream ```git remote add upstream https://github.com/dakk/gweatherrouting.git```

We also suggest to use `pyenv` to create an isolated pip environment:

- Create a new env: ```pyenv virtualenv gweatherrouting-env```
- Activate it: ```pyenv activate gweatherrouting-env```


### Working on the code

1. Now that you have your local copy of gweatherrouting, you can start working on the code; first, search or create the issue you want to contribute to in the gweatherrouting issue tracker, and ask
to be assigned to that issue in order to avoid duplicate work.

2. Create e new branch with a descriptibe name where you will do the changes; the starting point is always upstream/main:

```bash
git fetch upstream
git checkout -b your-branch-name upstream/master
```

3. Before each commit, use tox (```pip install tox```) in order to check that typechecker, linters and tests run fine:

```tox```

Use short and descriptive commit message, and remember to add tests to check new functionalities.


4. If your branch drifts out of sync from upstream/main, you can fetch and merge the updated version:

```git pull upstream main```

5. Finally push your code in your branch

```git push origin your-branch-name```

6. Once you're happy with your changes, visit [gweatherrouting github](https://github.com/dakk/gweatherrouting) and start a new pull request from `USERNAME:your-branch-name` to `dakk:main`. Maintainers will start reviewing your code and they may ask you to do some changes (in your branch): PR updates automatically every time you push to your working branch.


### Running CI locally

Install `act` and run your workflow:

```bash
act -j build-appimage
```


### Make docs

You can also create docs locally in order to check if everything is as expected:

```bash
pip install sphinx sphinx_rtd_theme sphinx_rtd_dark_mode myst_nb
make docs
```


## Publish a new release (maintainers only)

1. Create the release on github
2. Wait for the CI to build the appimage file
3. Upload the appimage in the new release
4. Update website appimage link

### Flatpak
1. Pin the release tag in the flatpak manifest
2. Build the release
3. flatpak-pip-generator --runtime=org.gnome.Sdk//49 -r requirements.txt --yaml
