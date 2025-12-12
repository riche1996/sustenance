

import os
import shutil
import subprocess

from urllib.parse import urlparse
import github3

from utility.common_utility import encryption_util
from utility.common_utility.constants import Assets_rootpath
from utility.common_utility.path_manager import safe_join, safe_relpath
from utility.logging import logging_utils as log_utils

ASSETS_DIR = Assets_rootpath
TEMP_DIR = safe_join(ASSETS_DIR,"Data", "tmp_github")
SUCCESS = "success"
FAILED = "failed"


class GitHubConnector:
    """Handle the github connection"""

    def __init__(self, config):
        self.github_url = config["github_url"]
        self.user_name = config["user_name"]
        self.access_token = config["access_token"]
        self.ssl_certificate = config["ssl_certificate"]
        self.filelist = []
        self.selected_files = []

    def init_and_clone_github_repo(self):  # pylint: disable=too-many-return-statements
        """
        Initializes a Git repository if the directory is not already a Git repo.

        :param repo_url: The URL of the GitHub repository.
        :param clone_dir: The directory where the repository should be cloned or pulled.
        """
        try:
            from git import GitCommandError, Repo  # pylint: disable=import-outside-toplevel
        except ImportError:
            return {
                "status": FAILED,
                "message": "Check if git client is installed and configured into \
                    environment variable path.",
                "clone_dir": "",
            }
        try:
            clone_dir = TEMP_DIR
            if not os.path.exists(clone_dir):
                os.makedirs(clone_dir)
            else:
                os.chmod(TEMP_DIR, 0o700)
                shutil.rmtree(TEMP_DIR)

            # Configure SSL settings based on the provided flag
            try:
                ssl_verify = "true" if self.ssl_certificate == 1 else "false"
                subprocess.run(
                    ["git", "config", "--global", "http.sslVerify", ssl_verify],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as config_error:
                return {
                    "status": FAILED,
                    "message": f"Failed to configure SSL: {config_error.stderr}",
                    "clone_dir": "",
                }

            # Decrypt the access token and construct the URL
            decrypted_acces_token = ""
            if self.access_token:
                decrypted_acces_token = encryption_util.decrypt(self.access_token)
            github_url_final = self.github_url.replace("https://", "")
            url = f"https://{self.user_name}:{decrypted_acces_token}@{github_url_final}"

            # Clone the repository
            try:
                Repo.clone_from(url, clone_dir, allow_unsafe_options=True)
            except GitCommandError as e:
                print(f"An error occurred: {e}")
                status_code = e.stderr
                if "not granted" in status_code or "403" in status_code:
                    return {
                        "status": FAILED,
                        "message": "GitHub repository permission denied",
                        "clone_dir": "",
                    }
                if "Authentication failed" in status_code or "401" in status_code:
                    return {
                        "status": FAILED,
                        "message": "Unable to authenticate GitHub repository",
                        "clone_dir": "",
                    }
                if "not found" in status_code or "128" in status_code:
                    return {
                        "status": FAILED,
                        "message": "GitHub repository not found",
                        "clone_dir": "",
                    }

                return {"status": FAILED, "message": str(e), "clone_dir": ""}

            # Remove the `.git` folder after cloning
            self.remove_git_folder(clone_dir)

            # Revert SSL configuration to avoid side effects
            subprocess.run(["git", "config", "--global", "--unset", "http.sslVerify"], check=True)

            return {"status": SUCCESS, "message": "", "clone_dir": clone_dir}
        except Exception as e:
            logger = log_utils.get_logger()
            logger.error(str(e), exc_info=True)
            print(f"An error occurred: {e}")
            return {"status": FAILED, "message": str(e), "clone_dir": ""}

    def remove_git_folder(self, clone_dir):
        """
        This method helps to remove the '.git' folder.
        """
        git_path = safe_join(clone_dir, ".git")

        for root, _dirs, files in os.walk(git_path):
            for file in files:
                file_path = safe_join(root, file)
                os.chmod(file_path, 0o700)
        shutil.rmtree(git_path)

    def list_guthub_data(self):
        """
        This method helps to capture the main dir files list information.
        """

        response = self.init_and_clone_github_repo()
        status = response["status"]
        if status == SUCCESS:
            clone_dir = response["clone_dir"]
            self.process_item(clone_dir)
            return {"status": SUCCESS, "message": "", "data": self.filelist}

        error_msg = response["message"]
        return {"status": FAILED, "message": error_msg, "data": self.filelist}

    def process_item(self, clone_dir):
        """
        This method helps to prepare the files information in required format.
        """
        for root, _dirs, files in os.walk(clone_dir):
            for file in files:
                file_path = safe_join(root, file)
                relative_path = safe_relpath(file_path, clone_dir)

                file_info = {}
                file_info["Build"] = "0.1.1"
                file_info["CodeComponent"] = relative_path.replace("\\", "/")
                file_info["CreatedDate"] = ""
                file_info["Release"] = "0.1"
                file_info["RevisionId"] = ""
                file_info["URL"] = file_path.replace("\\", "/")
                self.filelist.append(file_info)

    def download_files(self, selected_ids, github_data_path):
        """
        This method helps to download the files based on selected ids.
        """
        for file in selected_ids:
            path = file["CodeComponent"]
            _download_url = file["URL"]

            split_path = path.rsplit("/", 1)
            if len(split_path) == 1:
                folder_path = ""
                file_path = split_path[0]
            else:
                folder_path = split_path[0]
                file_path = split_path[1]

            final_save_path = safe_join(github_data_path, folder_path)
            os.makedirs(final_save_path, exist_ok=True)

            src_path = safe_join(TEMP_DIR, path)
            dest_path = safe_join(final_save_path, file_path)
            shutil.copy(src_path, dest_path)

            self.selected_files.append({"fullpath": path})
        return self.selected_files

    def is_public_github(self, url):
        parsed = urlparse(url)
        return parsed.hostname == "github.com"
    
    def get_enterprise_api_url(self, url):
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.hostname}"

    def create_files_and_commit(self, files: list, commit_message: str, branch_name: str = None):
        """
        Create files and commit to the github repository.
        Args:
            files: list of files to be created,[(file_name, binary_content), ...]
            commit_message: commit message
        """
        try:
            token = encryption_util.decrypt(self.access_token)
            if self.is_public_github(self.github_url):
                gh = github3.login(token=token)
                repository_name = self.github_url.split("/")[-1].replace(".git", "")
                repo = gh.repository(self.user_name, repository_name)
            else:
                api_url = self.get_enterprise_api_url(self.github_url)
                gh = github3.github.GitHubEnterprise(api_url, token=token)
                repository_name = self.github_url.split("/")[-1].replace(".git", "")
                org_name = self.github_url.split("/")[-2]
                repo = gh.repository(org_name, repository_name)

            for file_name, content in files:
                try:
                    file = repo.file_contents(file_name, ref=branch_name)
                    file.update(commit_message, content)
                    return {"status": "success", "msg": "File pushed to Github successfully"}
                except github3.exceptions.NotFoundError:
                    repo.create_file(file_name, commit_message, content, branch=branch_name)
                    return {"status": "success", "msg": "File pushed to Github successfully"}
                except Exception as e:
                    return {
                        "status": "failed",
                        "msg": "Failed to push file to Github",
                        "error": str(e),
                    }
        except Exception as e:
            return {"status": "failed", "msg": "Failed to push file to Github", "error": str(e)}
        