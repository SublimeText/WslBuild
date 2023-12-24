import re
import sublime
import subprocess

from Default.exec import ExecCommand


class WslExecCommand(ExecCommand):
    """
    The class defines a `wsl_exec` sublime build system target to run commands via WSL2.

    - execute Linux commands
    - provides Linux paths in variables such as `$unix_file`
    - properly set ENV variables for Linux commands

    REQUIRED KEYS
    ===

    wsl_cmd
    ---

    Set `wsl_cmd` instead of `cmd`. The command is executed by WSL.
    Build variables such as $file have a $unix_file counter part with unix style paths.

    Can be a `string` or `list` of strings.

    OPTIONAL KEYS
    ===

    wsl_working_dir
    ---

    Set `wsl_working_dir` instead of `working_dir`.
    Build variables such as $file have a $unix_file counter part with unix style paths.

    wsl_env
    ---

    Set `wsl_env` instead of `env` to set environment variables that are available to
    the Linux command.

    Environment variables can be terminated by conversion flags
    to specify how their values are treated by WSL.

        Example:
            "MY_PATH/p": "C:\\Path\\to\\File"

            is converted to:

            a) MY_PATH=/mnt/c/Path/to/File when running unix commands
            b) MY_PATH=C:\\Path\\to\\File when running windows commands

    `/p` flag
        This flag indicates that a path should be translated between WSL paths and
        Win32 paths. Notice in the example below how we set the var in WSL, add it
        to WSLENV with the `/p` flag, and then read the variable from cmd.exe and
        the path translates accordingly.

    `/l` flag
        This flag indicates the value is a list of paths. In WSL, it is a
        colon-delimited list. In Win32, it is a semicolon-delimited list.

    `/u` flag
        This flag indicates the value should only be included
        when invoking WSL from Win32.

    `/w` flag
        Notice how it does not convert the path automatically—we need to specify
        the /p flag to do this.

    For more information about it, visit:
    https://devblogs.microsoft.com/commandline/share-environment-vars-between-wsl-and-windows

    Example Build System to run file in WSL:
    ===

    ```jsonc
    {
        "target": "wsl_exec",
        "cancel": {"kill": true},
        "wsl_cmd": ["./$unix_file"],
        "wsl_working_dir": "$unix_file_path",
    }
    ```

    Example Build Systems for a Rails app in WSL:
    ===

    ```jsonc
    "build_systems": [
        {
            "name": "Run Current Spec",
            "target": "wsl_exec",
            "wsl_cmd": [
                "bundle", "exec", "rake", "spec"
            ],
            "wsl_env": {
                "PLAIN": "untranslated",
                "SPEC": "$file",
                "LIST/l": "%PATH%",
                "PATH/p": "%USERPROFILE%",
                "UNIX/u": "~/",
                "WIN/w": "%USERPROFILE%"
            },
            "wsl_working_dir": "$unix_folder",
            "cancel": {"kill": true},
        },
        {
            "name": "Run All Specs",
            "target": "wsl_exec",
            "wsl_cmd": [
                "bundle", "exec", "rake", "spec"
            ],
            "wsl_working_dir": "$unix_folder",
            "cancel": {"kill": true},
        },
        {
            "name": "Run Database Migrations",
            "target": "wsl_exec",
            "wsl_cmd": [
                "bundle", "exec", "rake", "db:migrate"
            ],
            "wsl_working_dir": "$unix_folder"
            "cancel": {"kill": true},
        }
    ```

    DEFAULT EXEC VARIABLES
    ===

    Unconverted variables are provided for use by Windows commands
    being executed within WSL.

    - `$file`
          The path to the _Packages/_ folder.
    - `$file_base_name`
          The platform Sublime Text is running on: "windows", "osx" or "linux".
    - `$file_extension`
          The full path, including folder, to the file in the active view.
    - `$file_name`
          The path to the folder that contains the file in the active view.
    - `$file_path`
          The file name (sans folder path) of the file in the active view.
    - `$folder`
          The file name, excluding the extension, of the file in the active view.
    - `$packages`
          The extension of the file name of the file in the active view.
    - `$project`
          The full path to the first folder open in the side bar.
    - `$project_base_name`
          The full path to the current project file.
    - `$project_extension`
          The path to the folder containing the current project file.
    - `$project_name`
          The file name (sans folder path) of the current project file.
    - `$project_path`
          The file name, excluding the extension, of the current project file.
    - `$platform`
          The extension of the current project file.

    UNIX EXEC VARIABLES
    ===

    Converted path variables are provided for Unix commands
    being executed within WSL.

    - `$unix_file`
          unix style `$file`
    - `$unix_file_path`
          unix style `$file_path`
    - `$unix_folder`
          unix style `$folder`
    - `$unix_packages`
          unix style `$packages`
    - `$unix_project`
          unix style `$project`
    - `$unix_project_path`
          unix style `$project_path`
    """

    def run(self, wsl_cmd, wsl_working_dir="", wsl_env=None, external=False, **kwargs):
        # Drop certain arguments, which should not be passed to super class
        wsl_args = {
            k: v for k, v in kwargs.items()
            if k not in {"env", "shell_cmd", "working_dir"}
        }

        # Translate command paramter to what exec expects
        if external is True:
            wsl_args["shell_cmd"] = subprocess.list2cmdline(self.wsl_cmd(wsl_cmd, wsl_working_dir, True))
        else:
            wsl_args["cmd"] = self.wsl_cmd(wsl_cmd, wsl_working_dir, False)

        # Translate environment variables
        if wsl_env:
            wsl_args["env"] = self.wsl_env(wsl_env)

        # Add path variables converted to unix format
        variables = self.window.extract_variables()
        for var in {
            "file",
            "file_path",
            "folder",
            "packages",
            "project",
            "project_path",
        }:
            if var in variables:
                variables["unix_" + var] = self.wsl_path(variables[var])

        # Expanding variables in the arguments given
        wsl_args = sublime.expand_variables(wsl_args, variables)

        super().run(**wsl_args)

    def wsl_cmd(self, cmd, cwd, external=False):
        r"""
        Set working directory within WSL2 and prepend "wsl" command

        Working directory may be given in Windows and Unix style.

        Working directory must be set within WSL via `cd cwd` as normal
        `working_dir` doesn't work for paths within WSL environment
        which start with `\\wsl$\<distro>\` or `\\wsl.localhost\<distro>\`.

        :param cmd:
            The shell command to execute in WSL2
        :param cwd:
            The working directory to set within WSL2

        :returns:
            The full wsl command value to execute.
        """
        wsl = ["start", "cmd", "/k", "wsl"] if external else ["wsl"]
        if cwd:
            wsl += ["cd", self.wsl_path(cwd), ";"]
        if isinstance(cmd, str):
            return wsl + [a.strip() for a in cmd.split(" ")]
        return wsl + cmd

    def wsl_env(self, env):
        """
        Publish environment variables to WSL

        The function sets `WSLENV` variable with colon separated list
        of variable names of `env` dictionary and adds it to returned
        `env` dictionary.

        It strips following conversion flags from environment variables.

        :param env:
            The environment variables to share with WSL
        :returns:
            A dict of environment variables to use to execute the command.
        """
        keys = list(env)
        if keys:
            existing = env.get("WSLENV", "")
            env["WSLENV"] = ":".join(keys)
            if existing:
                env["WSLENV"] += ":" + existing.strip(" :")

            for key in keys:
                if key[-2] == "/" and key[-1] in ("l", "p", "u", "w"):
                    env[key[:-2]] = env.pop(key)
        return env

    def wsl_path(self, path):
        r"""
        Convert Windows path to Unix path

        :param path:
            The windows path string to convert

            May point to folder in WSL:

            - Win 10: ``\\wsl$\<distro>\<path>``
            - Win 11: ``\\wsl.localhost\<distro>\<path>``

            May point to windows folder:

            - ``C:\<path>``

        :returns:
            The converted unix path string
        """
        # remove UNC prefix for paths pointing to WSL environment
        if path.startswith("\\\\"):
            path = re.sub(r"\\\\wsl(?:\.localhost|\$)\\[^\\]*", "", path)
        # convert local windows paths to WSL compliant unix format
        elif path[1:3] == ":\\":
            path = "".join(("/mnt/", path[0].lower(), path[2:]))
        return path.replace("\\", "/")
