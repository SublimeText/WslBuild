# WSL Build

A [Sublime Text](https://www.sublimetext.com) package to create build systems running in WSL2.

It adds a `wsl_exec` target that:

- executes Linux commands within **W**indows **S**ubsystem for **L**inux 2
- provides Linux paths in variables such as `$unix_file`
- properly sets environment variables for Linux commands

Execution and printing output is performed by Sublime Text's default `exec` build target.


## Installation

### Package Control

The easiest way to install is using [Package Control](https://packagecontrol.io). It's listed as `WslBuild`.

1. Open `Command Palette` using <kbd>ctrl+shift+P</kbd> or menu item `Tools → Command Palette...`
2. Choose `Package Control: Install Package`
3. Find `WslBuild` and hit <kbd>Enter</kbd>

### Manual Install

1. Download appropriate [WslBuild.sublime-package](https://github.com/SublimeText/WslBuild/releases) for your Sublime Text build.
2. Copy it into _Installed Packages_ directory
   
> To find _Installed Packages_...
>
> 1. call _Menu > Preferences > Browse Packages.._
> 2. Navigate to parent folder

### Clone repository

You can clone this repository into your _Sublime Text/Packages_

> **Note**
>
> To find _Packages_ folder call _Menu > Preferences > Browse Packages..._

##### Mac OS

```shell
cd ~/Library/Application\ Support/Sublime\ Text/Packages/
git clone https://github.com/SublimeText/WslBuild.git
```

##### Linux

```shell
cd ~/.config/sublime-text/Packages
git clone https://github.com/SublimeText/WslBuild.git
```

##### Windows

```shell
cd "%APPDATA%\Sublime Text\Packages"
git clone https://github.com/SublimeText/WslBuild.git
```


## Usage

### Defining a Build

Set `"target": "wsl_exec"` and `"cancel": {"kill": true}` to be able to cancel a command.

> **Note**
> 
> For more information about defining Sublime Text builds see [the official documentation](https://www.sublimetext.com/docs/build_systems.html)

#### Required Keys

##### wsl_cmd

Set `"wsl_cmd"` instead of `"cmd"`.  The command array will be executed through WSL.

> **Note**
> 
> Build variables such as $file have a $unix_file counter part with unix style paths.

#### Optional Keys

##### wsl_working_dir

Set `"wsl_working_dir"` instead of `"working_dir"`.

> **Note**
> 
> Build variables such as $file have a $unix_file counter part with unix style paths.

##### wsl_env

Set `"wsl_env"` instead of `"env"` to set environment variables that are available to
the Linux command.

> **Note**
> 
> Build variables such as $file have a $unix_file counter part with unix style paths.

Environment variables can be suffixed by conversion flags
to specify how their values are treated by WSL.

    "MY_PATH/p": "C:\\Path\\to\\File"

is converted to:

  1. `MY_PATH=/mnt/c/Path/to/File` when running unix commands
  2. `MY_PATH=C:\\Path\\to\\File` when running windows commands

| flag | description
|:----:| ---
| `/p` | This flag indicates that a path should be translated between WSL paths and Win32 paths. Notice in the example below how we set the var in WSL, add it to WSLENV with the `/p` flag, and then read the variable from cmd.exe and the path translates accordingly.
| `/l` | This flag indicates the value is a list of paths. In WSL, it is a colon-delimited list. In Win32, it is a semicolon-delimited list.
| `/u` | This flag indicates the value should only be included when invoking WSL from Win32.
| `/w` | Notice how it does not convert the path automatically—we need to specify the /p flag to do this.

For more information about it, visit:
https://devblogs.microsoft.com/commandline/share-environment-vars-between-wsl-and-windows

##### Example Build System to run file in WSL:

```json
{
    "target": "wsl_exec",
    "cancel": {"kill": true},
    "wsl_cmd": ["./$unix_file"],
    "wsl_working_dir": "$unix_file_path",
}
```

##### Example Builds for a Rails app in WSL:

```json
"build_systems": [
    {
        "name": "🧪 Run Current Spec",
        "target": "wsl_exec",
        "cancel": {"kill": true},
        "wsl_cmd": [
            "bundle", "exec", "rake", "spec" 
        ],
        "wsl_env": {
            "SPEC/p": "$file"
        },
        "wsl_working_dir": "$unix_folder"
    },
    {
        "name": "🧪 Run All Specs",
        "target": "wsl_exec",
        "cancel": {"kill": true},
        "wsl_cmd": [
            "bundle", "exec", "rake", "spec"
        ],
        "wsl_working_dir": "$unix_folder",
    },
    {
        "name": "🗃️ Run Database Migrations",
        "target": "wsl_exec",
        "cancel": {"kill": true},
        "wsl_cmd": [
            "bundle", "exec", "rake", "db:migrate"
        ],
        "wsl_working_dir": "$unix_folder"
    }
]
```

### Variables

#### Default Variables

All default variables are provided in unconverted form
in case a windows command is being executed within WSL2.

| variable              | description
| ---                   | ---
| `$packages`           | The path to the _Packages/_ folder.
| `$platform`           | The platform Sublime Text is running on: "windows", "osx" or "linux".
| `$file`               | The full path, including folder, to the file in the active view.
| `$file_path`          | The path to the folder that contains the file in the active view.
| `$file_name`          | The file name (sans folder path) of the file in the active view.
| `$file_base_name`     | The file name, excluding the extension, of the file in the active view.
| `$file_extension`     | The extension of the file name of the file in the active view.
| `$folder`             | The full path to the first folder open in the side bar.
| `$project`            | The full path to the current project file.
| `$project_path`       | The path to the folder containing the current project file.
| `$project_name`       | The file name (sans folder path) of the current project file.
| `$project_base_name`  | The file name, excluding the extension, of the current project file.
| `$project_extension`  | The extension of the current project file.

see: https://www.sublimetext.com/docs/build_systems.html#variables

#### Unix Variables

Converted path variables are provided for unix commands being executed within WSL.

| variable (unix style) | original variable (windows style)
| ---                   | ---
| `$unix_file`          | `$file`
| `$unix_file_path`     | `$file_path`
| `$unix_folder`        | `$folder`
| `$unix_packages`      | `$packages`
| `$unix_project`       | `$project`
| `$unix_project_path`  | `$project_path`

### Acknowledgments

Inspired by 

- https://github.com/existentialmutt/wsl_build
- OdatNurd's technique here https://github.com/STealthy-and-haSTy/SublimeScraps/blob/master/build_enhancements/custom_build_variables.py
