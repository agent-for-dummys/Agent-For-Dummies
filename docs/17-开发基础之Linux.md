# Linux

## 1. Linux 简介

通常我们能见到的服务器和软件开发，大多都基于 Linux，在部署后端服务、配置开发环境、运行 Docker 容器时，也经常会用到 Linux。熟悉 Linux 常用命令，是开发的基本功，由 Agent 应用开发往后端开发靠近（bushi）的第一步。

### Linux 发行版与 WSL

严格来说，Linux 指操作系统内核，负责管理进程、内存和硬件资源。我们平时安装的 Ubuntu、Debian 等，会把 Linux 内核与命令行工具、软件包管理器等组合在一起，构成一套可以直接使用的系统，这些系统就叫 **Linux 发行版**。

在 Windows 上，可以通过 WSL（适用于 Linux 的 Windows 子系统）安装并使用 Ubuntu 等 Linux 发行版。通俗地说，就是即使在 Windows系统上，可以不用安装双系统，也不用换系统，就能在电脑里使用 Linux 环境，运行 Linux 的命令和工具。

如果还没有安装，可以参考[微软官方 WSL 安装指南](https://learn.microsoft.com/zh-cn/windows/wsl/install)。在支持的 Windows 10 或 Windows 11 系统中，以管理员身份打开 PowerShell，运行：

```powershell
wsl --install
```

这条命令会安装 WSL，并默认安装 Ubuntu。按提示重启电脑后，打开 Ubuntu，完成首次启动时的用户名和密码设置。

如果已经通过 WSL 安装了 Ubuntu，可以在 PowerShell 中查看已安装的发行版：

```powershell
wsl --list --verbose
```

然后进入 Ubuntu：

```powershell
wsl -d Ubuntu
```

这里的 `Ubuntu` 要与列表中显示的发行版名称一致。如果显示的是 `Ubuntu-24.04`，就改为 `wsl -d Ubuntu-24.04`。

进入以后，就可以在 Ubuntu 中执行本篇的 Bash 命令。退出时输入 `exit`，即可回到原来的 PowerShell。

下面的例子以 Ubuntu 和 Bash 为环境，安装软件使用 `apt`。不同发行版的软件包管理命令可能不同。

## 2. 终端

### 终端和 Shell

终端是输入命令、显示输出的窗口。Shell 负责读取你的输入，解析命令和参数，再启动相应的程序。Ubuntu 里经常使用 Bash，Windows 上则经常使用 PowerShell。

假设终端里显示这样一行。

```text
alice@ubuntu:~/projects$
```

这里的 `alice` 是当前用户名，`ubuntu` 是主机名，`~/projects` 表示当前目录。后面的 `$` 是提示符，复制教程中的命令时，从提示符后面的内容开始复制。

先输入两条命令，看看自己在哪里、正在用哪个用户。

```bash
pwd
whoami
```

`pwd` 输出当前目录的绝对路径，`whoami` 输出当前用户名。遇到文件找不到或权限问题时，这两条命令就能帮我们先确认环境。

### 命令格式

```bash
ls -lah .
```

`ls` 是命令，`-lah` 是三个短选项合并后的写法，最后的 `.` 是要查看的目录。`-l` 显示详细信息，`-a` 包含隐藏项，`-h` 让大小以更容易阅读的单位显示。

敲命令时可以按 Tab 补全路径，用上、下方向键调出历史命令。大部分普通前台程序可以用 Ctrl+C 中断，Ctrl+D 在空输入行时通常会结束当前 Shell。

## 3. 目录与路径

### 常见目录

Linux 的目录就像一个倒着的树一样，所以叫“目录树”。绝对路径从 `/` 开始。例如 `/home/alice/projects` 就是从根目录出发，依次进入 `home`、`alice` 和 `projects`。当前用户的 home 目录可以写成 `~`，所以 Alice 的 `~/projects` 通常就对应这条路径。

| 路径         | 解释            |
| ---------- | ------------- |
| `/home`    | 普通用户的 home 目录 |
| `/etc`     | 系统和服务的配置文件    |
| `/var/log` | 系统或服务写入的日志    |
| `/tmp`     | 临时文件          |
| `/usr/bin` | 许多已经安装的命令     |
| `/root`    | root 用户的家目录   |

需要注意的是，`/root` 和根目录 `/` 是两个路径。

### 路径写法

```bash
cd ~                            # 切换到当前用户的 home 目录
mkdir -p linux-practice/logs    # 创建 linux-practice 目录及其子目录 logs
cd linux-practice               # 进入 linux-practice 目录
pwd                             # 显示当前工作目录的绝对路径
ls -la                          # 显示当前目录下所有文件的详细信息（包括隐藏文件）
```

`mkdir -p` 会在需要时创建中间目录。现在工作目录是 `~/linux-practice`，因此 `logs` 表示它里面的日志目录。

`.` 表示当前目录，`..` 表示上一级。输入 `cd ..` 就会回到家目录，输入 `cd -` 可以返回上一次所在的位置。

Linux 文件名通常**区分大小写**，`Makefile` 和 `makefile` 可以同时存在。路径里如果有空格，要把路径用引号包起来，例如 `cd "my project"`。

### WSL 文件访问

在 WSL 的默认挂载方式下，Windows 的 D 盘可以从 `/mnt/d` 访问。如果项目位于 `D:\expe\agent-for-dummies`，在 Ubuntu 里可以这样进入。

```bash
cd /mnt/d/expe/agent-for-dummies
pwd
```

同一份文件可以从不同系统的路径访问。输入命令前先确认所在的 Shell，Ubuntu 里用 Linux 路径，PowerShell 里用 Windows 路径。[WSL 文件系统说明](https://learn.microsoft.com/en-us/windows/wsl/filesystems)

## 4. 文件操作

### 创建与复制

回到前面创建的练习目录。

```bash
cd ~/linux-practice
printf '%s\n' 'Hello from Linux' > hello.txt
cat hello.txt
cp hello.txt hello-copy.txt
mv hello-copy.txt greeting.txt
ls
```

`printf` 打印一行文字，`>` 把输出写入文件，`cat` 显示文件内容。`cp` 复制出另一份文件，`mv` 可以移动文件，也可以在同一个目录中改名。

这里的 `>` 会覆盖文件原有内容。如果想在后面继续写一行，可以用 `>>`。

```bash
printf '%s\n' 'Another line' >> hello.txt
cat hello.txt
```

### 查看内容

| 命令 | 用法 |
| --- | --- |
| `head -n 10 hello.txt` | 查看前 10 行 |
| `tail -n 10 hello.txt` | 查看后 10 行 |
| `less hello.txt` | 分页阅读，用方向键滚动，按 q 退出 |
| `tail -f logs/app.log` | 文件存在时，持续查看追加的内容 |

`cat` 适合读小文件。如果日志有几十万行，直接全部打印会把终端刷满，这时可以先用 `tail` 看末尾的报错。

### 删除文件

```bash
rm greeting.txt
mkdir empty-dir
rmdir empty-dir
```

`rm` 删除文件，`rmdir` 删除空目录。删除带内容的目录需要递归操作，例如 `rm -r demo-dir`。执行这类命令前，先用 `pwd` 和 `ls demo-dir` 确认目标。命令行删除通常直接作用于文件系统，恢复时需要依靠备份等手段。[Ubuntu 命令行入门](https://ubuntu.com/tutorials/command-line-for-beginners)

::: linux-practice 1
:::

## 5. 文件搜索

### find

项目目录多了以后，你可能记得曾经有一份 Python 文件放在里面，却忘了放在哪一层。于是这个时候可以让 `find` 从当前目录往下查。

```bash
find . -type f -name '*.py'
```

`-type f` 只查普通文件，`-name` 按文件名匹配。给 `*.py` 加引号，是为了把这个模式交给 `find` 处理。如果先被 Shell 展开，就可能只传入当前目录里已经匹配到的几个文件名。[find 手册](https://man7.org/linux/man-pages/man1/find.1.html)

### grep

先准备一份小日志。

```bash
printf '%s\n' 'INFO app started' 'ERROR database unavailable' 'INFO retrying' > logs/app.log
grep -n 'ERROR' logs/app.log
```

输出中的数字是行号。`grep` 会找出包含 `ERROR` 的行，大小写默认有区别。如果不知道日志里写的是 `Error` 还是 `ERROR`，可以加 `-i`。

在代码里查一个函数时，可以写 `grep -rn 'function_name' src`，让它从 `src` 目录递归查找并显示行号。目录里有虚拟环境或依赖包时，先缩小搜索范围会更容易找到。[grep 手册](https://man7.org/linux/man-pages/man1/grep.1.html)

## 6. 管道与重定向

### 管道

前面让 `grep` 读的是文件。如果不指定文件，它也可以从标准输入读取内容。

```bash
grep 'INFO' logs/app.log | wc -l
```

左边的 `grep` 筛选出日志中的 INFO 行，`|` 把这些文字送给右边的 `wc`，`wc -l` 再统计行数。对前面的示例日志，结果是 2。

### 重定向

程序常用标准输出显示运行结果，用标准错误显示报错。Bash 中用 `1` 和 `2` 分别表示它们。

```bash
bash -c 'printf "ready\n"; printf "missing config\n" >&2' > output.log 2> error.log
cat output.log
cat error.log
```

现在两份文件里分别保存正常输出和错误输出。如果希望合到同一份日志，可以写 `> app.log 2>&1`。重定向按从左到右处理，所以顺序也会影响结果。

## 7. 用户与权限

### 文件权限

`ls -l` 的结果里，经常能看到类似 `-rw-r--r--` 的内容。第一个字符表示文件类型，后面每三个字符一组，依次描述所有者、所属组和其他用户的权限。

`r` 表示读，`w` 表示写，`x` 表示执行。普通文件要直接作为程序运行，需要执行权限。对于目录，`x` 则和能否进入、访问目录中的路径有关。

先写一个简单脚本，看看执行权限怎么用。

```bash
printf '%s\n' '#!/usr/bin/env bash' 'printf "Hello from a script\n"' > hello.sh
chmod u+x hello.sh
./hello.sh
```

`chmod u+x` 给文件所有者增加执行权限。`./hello.sh` 中的 `./` 指明脚本就在当前目录。Shell 查找命令时会检查 `PATH` 中的目录，当前目录通常没有被包含进去，所以直接输入 `hello.sh` 可能找不到它。[chmod 手册](https://man7.org/linux/man-pages/man1/chmod.1.html)

### sudo

安装系统软件、修改部分系统配置时，普通用户可能没有权限。`sudo` 可以在授权范围内以另一个用户的身份执行命令，常见情况是以 root 身份执行。

如果执行 `sudo` 时要求输入密码，终端通常不会显示星号，继续输入并按回车即可。项目里的文件报权限错误时，先查看文件所有者和路径权限，确认究竟哪一层无法访问，再决定如何处理。

::: linux-practice 2
:::

## 8. 环境配置

### 软件安装

假设需要编译 C++，可以安装 Docker 笔记中用过的 `build-essential`。

```bash
sudo apt update
sudo apt install build-essential
g++ --version
make --version
```

`apt update` 更新可用软件包及版本的索引，`apt install` 根据索引下载并安装软件。安装过程中可能让你确认，占用空间也会显示出来。在 Dockerfile 里通常用 `apt-get` 配合 `-y`，让脚本完成安装。[Ubuntu 软件包管理](https://ubuntu.com/server/docs/how-to/software/package-management/)

### 环境变量

```bash
export APP_MODE=development
printenv APP_MODE
bash -c 'printf "%s\n" "$APP_MODE"'
```

`export` 把变量放进当前 Shell 的环境，之后启动的子进程也能读到它。这里新开的 Bash 会打印 `development`。退出当前终端以后，这次设置通常也就结束了。

如果只想给一条命令设置变量，可以写 `APP_MODE=test bash -c 'printf "%s\n" "$APP_MODE"'`。查看命令的位置可以用 `command -v python3`，查看可执行文件的搜索路径可以用 `printf '%s\n' "$PATH"`。

## 9. 运行排查

### 进程

如果服务一直在运行，可以在另一个终端里看进程。

```bash
ps -eo pid,ppid,stat,cmd
```

`PID` 是进程编号，`PPID` 是父进程编号，`CMD` 是启动命令。想持续观察 CPU 和内存，可以打开 `top`，按 q 退出。服务器卡住时，可以先看看是哪个进程持续占用资源。[ps 手册](https://man7.org/linux/man-pages/man1/ps.1.html)

### 端口

Python 可用时，可以在练习目录启动一个本地文件服务。

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

这个终端会被服务占用。再开一个 Ubuntu 终端执行下面两条命令。

```bash
ss -ltnp 'sport = :8000'
curl -I http://127.0.0.1:8000
```

`ss` 查看监听端口，`-l` 只看监听项，`-t` 选择 TCP，`-n` 用数字显示地址和端口，`-p` 尝试显示进程。部分进程信息需要额外权限才能看到。`curl -I` 请求响应头，看到 HTTP 状态行说明服务已经回应。结束练习时回到运行服务器的终端按 Ctrl+C。[ss 手册](https://man7.org/linux/man-pages/man8/ss.8.html)

如果只知道某个自己启动的进程编号，也可以用 `kill 进程编号` 发送默认的终止信号。程序有机会处理退出，具体行为由程序决定。

## 10. 编译实践

前面创建的 `~/linux-practice` 可以继续当练习目录。试着创建一个 `src` 目录，写入一份打印问候语的 `main.cpp`，再编译并保存输出。

```bash
cd ~/linux-practice
mkdir -p src
cat > src/main.cpp <<'EOF'
#include <iostream>

int main() {
    std::cout << "Hello from Linux!\n";
    return 0;
}
EOF
g++ src/main.cpp -o hello
./hello > result.txt
cat result.txt
```

`<<'EOF'` 让 Shell 持续读取后面的文字，直到遇到单独一行的 `EOF`，并把这些内容作为输入交给 `cat`。`>` 再让 `cat` 的输出写进源文件。编译成功后，当前目录里会出现 `hello`，最后一条命令应该输出 `Hello from Linux!`。

到这里，再看 Dockerfile 中的 `WORKDIR`、`RUN apt-get install` 和 `RUN g++`，就能把它们和刚才手工执行的操作联系起来了。

## 参考资料

- [Ubuntu 命令行入门](https://ubuntu.com/tutorials/command-line-for-beginners)
- [Ubuntu 软件包管理](https://ubuntu.com/server/docs/how-to/software/package-management/)
- [WSL 文件系统说明](https://learn.microsoft.com/en-us/windows/wsl/filesystems)
- [Bash 的重定向说明](https://www.gnu.org/software/bash/manual/html_node/Redirections.html)
