# pylint: disable=line-too-long

import datetime
import os
import re
import subprocess
import sys

RELEASE_KINDS = {'p': 'patch', 'm': 'minor', 'mj': 'major'}
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
REPOSITORY_URL = "https://github.com/suitenumerique/accounts"


def run_command(cmd):
    sys.stdout.write(f"# Running: {cmd}\n")
    subprocess.check_call(cmd, shell=True)


def update_files(version):
    """Update all files needed with new release version"""
    # pyproject.toml
    sys.stdout.write("Updating pyproject.toml...\n")
    path = "src/backend/pyproject.toml"
    with open(path, 'r') as file:
        lines = file.readlines()
        for index, line in enumerate(lines):
            if line.startswith("version = "):
                lines[index] = re.sub(r'\"(.*?)\"', f'"{version}"', line)
    with open(path, 'w+') as file:
        file.writelines(lines)

    # uv lock file
    sys.stdout.write("Updating uv lock file...\n")
    path = "src/backend/uv.lock"
    with open(path, 'r') as file:
        content = file.read()
    content = re.sub(
        r'(\[\[package\]\]\nname = "accounts"\nversion = )"[^"]*"',
        f'\\1"{version}"',
        content,
    )
    with open(path, 'w+') as file:
        file.write(content)

    # frontend package.json
    sys.stdout.write("Updating package.json...\n")
    files_to_modify = []
    filename = "package.json"
    for root, _dir, files in os.walk("src/frontend"):
        if filename in files and "node_modules" not in root and ".next" not in root:
            files_to_modify.append(os.path.join(root, filename))

    for path in files_to_modify:
        with open(path, 'r') as file:
            lines = file.readlines()
            for index, line in enumerate(lines):
                if "version" in line:
                    lines[index] = re.sub(r'"version": \"(.*?)\"', f'"version": "{version}"', line)
        with open(path, 'w+') as file:
            file.writelines(lines)

    return


def update_helm_files(path, version):
    sys.stdout.write("Updating helm files...\n")
    with open(path, 'r') as file:
        lines = file.readlines()
        for index, line in enumerate(lines):
            if line.strip().startswith("tag:"):
                lines[index] = re.sub(r'\"(.*?)\"', f'"v{version}"', line)
    with open(path, 'w+') as file:
        file.writelines(lines)


def update_changelog(path, version):
    """Update changelog file with release info
    """
    sys.stdout.write("Updating CHANGELOG...\n")
    with open(path, 'r') as file:
        lines = file.readlines()
        for index, line in enumerate(lines):
            if "## [Unreleased]" in line:
                today = datetime.date.today()
                lines.insert(index + 1, f"\n## [v{version}] - {today}\n")
            if line.startswith("[unreleased]"):
                last_tag = lines[index + 1].split("]")[0][1:]
                lines[index] = f"[unreleased]: {REPOSITORY_URL}/compare/v{version}...main\n"
                lines.insert(index + 1, f"[v{version}]: {REPOSITORY_URL}/compare/{last_tag}...v{version}\n")
                break

    with open(path, 'w+') as file:
        file.writelines(lines)


def deployment_part(version):
    """ Update helm file of preprod on deployment repository suitenumerique/mon-compte-deploiement
    """
    # Move to mon-compte-deploiement repository
    try:
        os.chdir('../mon-compte-deploiement')
    except FileNotFoundError:
        sys.stdout.write("\033[1;31m[Error] You must have a clone of https://github.com/suitenumerique/mon-compte-deploiement next to this repository\x1b[0m\n")
        sys.stdout.write("\033[0;32mPlease clone it and re-run script with option --only-deployment-part\x1b[0m\n")
        sys.stdout.write("  >>> python3 bin/release.py --only-deployment-part \x1b[0m\n")
    else:
        run_command("git checkout main")
        run_command("git pull")
        deployment_branch = f"mon-compte/{version}/preprod"
        run_command(f"git checkout -b {deployment_branch}")
        run_command("git pull --rebase origin main")
        path = "manifests/mon-compte/env.d/preprod/values.mon-compte.yaml.gotmpl"
        update_helm_files(path, version)
        run_command(f"git add {path}")
        message = f"""🚀(preprod) bump version to v{version}"""
        run_command(f"git commit -m '{message}'")
        confirm = input(f"""\033[0;32m
### DEPLOYMENT ###
NEXT COMMAND on mon-compte-deploiement repository: 
    >> git push origin {deployment_branch}
Continue ? (y,n) 
\x1b[0m""").strip()
        if confirm == 'y':
            run_command(f"git push origin {deployment_branch}")
        sys.stdout.write(f"""\033[1;34m
PLEASE DO THE FOLLOWING INSTRUCTIONS: 
--> Check if you need to bump chart version in the manifests/mon-compte/helmfile.yaml.gotmpl file
    and settings in the manifests/mon-compte/env.d/preprod/values.mon-compte.yaml.gotmpl file
    add commits into {deployment_branch} branch to do it if needed, then...
--> Please submit PR {deployment_branch} and merge code to main [https://github.com/suitenumerique/mon-compte-deploiement]
\x1b[0m""")


def project_part(version, kind):
    """Manage only the accounts part with update of CHANGELOG, version files and tag"""
    sys.stdout.write('Let\'s go to create branch to release\n')
    branch_to_release = f"release/{version}"
    run_command(f"git checkout -b {branch_to_release}")
    run_command("git pull --rebase origin main")

    update_changelog("CHANGELOG.md", version)
    update_files(version)

    run_command("git add CHANGELOG.md")
    run_command("git add src/")
    message = f"""🔖({RELEASE_KINDS[kind]}) release version {version}

Update all version files and changelog for {RELEASE_KINDS[kind]} release."""
    run_command(f"git commit -m '{message}'")
    confirm = input(f"""\033[0;32m
### RELEASE ###
NEXT COMMAND on current repository:
    >> git push origin {branch_to_release}
Continue ? (y,n)
\x1b[0m""").strip()
    if confirm == 'y':
        run_command(f"git push origin {branch_to_release}")
    sys.stdout.write(f"""
\033[1;34mPLEASE DO THE FOLLOWING INSTRUCTIONS:
--> A github action will download last translations from crowdin and create a PR (i18n/update-translations) to merge into the release branch.
    Please wait for this, approve and merge this translations PR into the release branch {branch_to_release}.
--> Then please submit PR {branch_to_release} and merge code to main [{REPOSITORY_URL}]
--> Then do:
    >> git checkout main
    >> git pull
    >> git tag v{version} 
    >> git push origin v{version} 
--> Please check and wait for the docker image v{version} to be published here:
 - https://hub.docker.com/r/lasuite/accounts-backend/tags 
 - https://hub.docker.com/r/lasuite/accounts-frontend/tags
--> Now please generate release on github interface for the current tag v{version}
 \x1b[0m""")


if __name__ == "__main__":
    version, kind = None, None
    while not version or not VERSION_PATTERN.match(version):
        version = input("Enter your release version (X.Y.Z):").strip()
    while kind not in RELEASE_KINDS:
        kind = input("Enter kind of release (p:patch, m:minor, mj:major):").strip()
    if "--only-deployment-part" not in sys.argv:
        project_part(version, kind)
    deployment_part(version)
