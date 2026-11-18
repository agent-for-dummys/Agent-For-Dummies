# Git

## 1. Git 简介

假设你改了一下午的代码，终于跑通，准备继续加功能。半小时以后程序又报错了，你已经记不清刚才动过哪些地方，只好开始比较 `main.py`、`main-final.py` 和 `main-final2.py`。

项目里的人多了以后，问题还会增加。两个人可能同时修改同一个文件，复制文件夹很难看出每一处改动来自谁，也很难把其中一个功能单独拿出来。

Git 可以为项目保存一系列提交。你可以查看某次提交改了哪些文件、比较两个版本，也可以在独立分支上开发功能，完成以后再合并。每次提交都能附上一段说明，解释这次修改解决了什么问题。

### Git 与 GitHub

Git 在本地管理提交历史。GitHub 提供远端仓库托管、Pull Request、Issue 等协作功能。本地完成提交以后，可以把它推送到 GitHub，让其他人获取这些提交。

普通克隆得到的本地仓库通常包含项目的提交历史，许多查看和提交操作可以离线完成。连接远端时才需要网络，以及对应的访问权限。[Git 的基本概念](https://git-scm.com/book/en/v2/Getting-Started-What-is-Git%3F)

## 2. 创建仓库

### 用户配置

安装 Git 后，先在终端确认命令可用。

```bash
git --version
```

提交里会记录作者名字和邮箱。把下面的示例换成自己的信息，配置一次即可。用户名和邮箱用于提交记录，推送时的身份认证另外由远端服务处理。

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

`--global` 表示配置当前系统用户使用的默认值。如果一个项目要用另一套作者信息，可以进入那个仓库，省略 `--global` 再设置。[Git 配置说明](https://git-scm.com/docs/git-config)

### 初始化

下面的例子会新建一个练习仓库。选一处适合放项目的位置，在终端里执行。

```bash
mkdir git-practice
cd git-practice
git init -b main
git status
```

现在目录里多了一个隐藏的 `.git`，Git 会在里面保存提交对象、分支引用和仓库配置。`git status` 会告诉你当前在 `main` 分支，还没有提交。

接着在编辑器里新建 `hello.txt`，写入 `Hello from Git!` 并保存。后面的例子使用这个文件，Git 命令在 PowerShell、Git Bash 和 Ubuntu 终端中都可以执行。

### 克隆

如果项目已经在 GitHub 上，可以直接克隆。下面是命令格式，执行时把示例地址换成真实仓库地址，把`<destination project>`替换成需要存放项目的文件夹。执行完这个命令之后，Git 将仓库内容克隆到目标文件夹中。如果不输入`<destination project>`，Git 会自动创建一个名为 `REPO`  的文件夹，并将仓库内容克隆进去。这个目录就会自动和远程仓库链接起来，之后的push、pull等操作都可以更方便地进行。

```bash
git clone https://github.com/OWNER/REPO.git <destination project>
cd REPO
```

进入后可以用 `git remote -v` 查看地址。

## 3. 提交流程

### 工作区与暂存区

刚才编辑器保存的 `hello.txt` 位于工作区。Git 的暂存区记录准备放进下一次提交的内容，执行 `git add` 就可以更新这部分内容。执行 `git commit` 时，Git 根据暂存区创建一次提交。

```bash
git status
git add -- hello.txt
git diff --cached
git commit -m "添加问候语"
```

提交完成后，再执行 `git status`，应该会看到工作区干净。以后每次修改 `hello.txt`，都可以重复查看、暂存和提交的过程。

这里有个容易忽略的地方。如果先执行 `git add hello.txt`，接着又在编辑器里多写了一行，这一行还没有进入暂存区。提交前要再检查一次，想把新内容一起提交时，就再次执行 `git add hello.txt`。

### 提交历史

提交会形成一个可引用的项目快照，并关联父提交等信息。你可以用 `git log --oneline` 查看历史。每行前面的一串字符是提交 ID 的缩写，后面是提交说明。第一次提交没有父提交，以后的普通提交会沿着这条历史继续连接。[Git 的基本概念](https://git-scm.com/book/en/v2/Getting-Started-What-is-Git%3F)

## 4. 查看改动

### status

```bash
git status --short
```

简短输出用两列显示状态。第一列描述暂存区相对当前提交的变化，第二列描述工作区相对暂存区的变化。

| 示例 | 含义 |
| --- | --- |
| `?? notes.txt` | 新文件尚未被 Git 跟踪 |
| `A  hello.txt` | 新文件已加入暂存区 |
| ` M hello.txt` | 已跟踪文件在工作区被修改，还没暂存 |
| `M  hello.txt` | 修改已经暂存 |
| `MM hello.txt` | 暂存过一次，之后工作区又有新修改 |
| `D  hello.txt` | 文件删除已经暂存 |

`??` 文件在加入暂存区以前，会继续留在本地。想确认一次提交准备带走什么，可以同时查看文件列表和实际内容。[git status 手册](https://git-scm.com/docs/git-status)

### diff

```bash
git diff
git diff --cached
git diff --cached --stat
```

`git diff` 查看工作区里尚未暂存的修改，`git diff --cached` 查看暂存区相对当前提交的修改。`--stat` 用文件名和增删行数概括变化，适合在提交前确认范围。

新文件处于 `??` 状态时，普通的 `git diff` 通常不会列出它的内容。对这个文件执行 `git add` 后，就能在 `git diff --cached` 中检查。

### 中文路径

终端里出现 `\347\254...` 这样的名字时，可以临时关闭 Git 对非 ASCII 路径的转义。

```bash
git -c core.quotepath=false status --short
```

`-c` 只给这一次命令设置配置。文件内容和文件名都保留原样。[Git 路径显示配置](https://git-scm.com/docs/git-config)

## 5. 文件管理

### 暂存文件

假设这次更新了项目内容，同时产生了一份临时草稿。可以明确列出准备提交的文件。

```bash
git add -- "你要添加修改的文件"
git diff --cached --stat
git diff --cached
git commit -m "你要提交的信息"
```

`git add .` 会把当前目录及其子目录中的可暂存改动一起处理，执行前先看看 `git status`，就能知道还夹着哪些文件。

### .gitignore

项目可能有依赖目录、缓存和本地配置，可以把对应模式写进仓库根目录的 `.gitignore`。例如：

```gitignore
node_modules/
.venv/
__pycache__/
*.pyc
.env
work/
```

`.gitignore` 也可以提交，让其他人克隆后使用相同规则。已经被跟踪的文件需要另外处理。例如决定让 `local.log` 留在本地、退出版本管理时，可以执行 `git rm --cached -- local.log`，再提交这次移除记录。如果想确认某条忽略规则是否生效，可以用 `git check-ignore -v work/output.txt`。[gitignore 手册](https://git-scm.com/docs/gitignore)

::: git-practice 1
:::

## 6. 远端同步

### origin 与 push

```bash
git remote -v
```

输出会列出远端名和对应地址。克隆项目时自动登记的远端通常叫 `origin`，这个名字也可以由你自行配置。如果从 `git init` 开始，并且已经在 GitHub 上创建好空仓库，可以登记它的地址。

```bash
git remote add origin https://github.com/OWNER/REPO.git
git push -u origin main
```

把示例地址换成自己的仓库。`push` 会尝试把本地 `main` 的提交发送给 `origin` 上的同名分支。`-u` 会在成功推送时建立上游关系，后续可以按配置使用简写。

提交记录已经引用的文件会随提交一起传送。还处于未跟踪状态、或者只有工作区修改的内容，得先进入提交才会出现在远端。[git push 手册](https://git-scm.com/docs/git-push)

### fetch 和 pull

```bash
git fetch origin
git log --oneline --graph --decorate --all -n 12
```

`fetch` 获取远端的新对象并更新相应的远端跟踪引用，例如 `origin/main`。它完成以后，可以先查看本地与远端的提交关系，再决定怎么整合。

假设当前就在 `main`，本地没有未提交修改，可以尝试让本地跟上远端。

```bash
git pull --ff-only origin main
```

如果本地和远端各自新增了提交，命令会停下来，需要由你决定用合并还是变基。当你的项目团队约定使用变基时，可以在确认当前分支和工作区状态后，执行 `git pull --rebase origin main`。变基会把本地提交重新放到新基础之上，提交 ID 也会变化。[git pull 手册](https://git-scm.com/docs/git-pull)

## 7. 分支管理

### 创建分支

你想做项目的另一个功能，但同时还需要保留主分支现在的状态，可以先建立一个分支。

```bash
git switch -c 分支名
```

当前分支会指向新的提交位置。接着新建 `linux.txt`，写几行内容，然后提交。

```bash
git add -- "修改的文件"
git commit -m "提交信息"
```

### 合并分支

确认当前没有未提交修改以后，可以切回主分支合并。

```bash
git switch main
git merge 你刚刚创建的新分支
```

需要提交自己的功能分支时，可以执行 `git push -u origin 分支名`，再按项目流程发起 Pull Request，由维护者审阅后合并。[Git 分支与合并](https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging)

::: git-practice 2
:::

## 8. 合并冲突

假设你把你的项目里的某个文档标题改成了“Linux 入门”，另一位同学在另一条分支上把同一行改成了“Linux 开发基础”。两份提交都没有代码错误，Git 合并时是无法替你选择最后保留哪一版的，这个时候就会发生冲突。

发生冲突以后，先执行 `git status` 看哪些文件需要处理。打开冲突文件时，会看到类似下面的标记。

```text
<<<<<<< HEAD
# Linux 入门
=======
# Linux 开发基础
>>>>>>> 分支名
```

在一次普通的 `git merge` 中，`HEAD` 这边是当前分支的内容，下面是正合入分支的内容。和团队成员确认最后要用的版本，把它写好，并删掉这几行冲突标记。然后把解决后的文件重新暂存。

```bash
git add -- linux.txt
git merge --continue
```

如果决定放弃这次合并，可以用 `git merge --abort` 回退本次合并操作。处理变基冲突时，继续和退出分别用 `git rebase --continue` 与 `git rebase --abort`，具体以 `git status` 的提示为准。[Git 合并冲突](https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging)

## 9. 撤销与暂存

### 取消暂存

下面的例子假设仓库已经至少有一次提交。如果某个文件暂存早了，可以先取消暂存，继续在编辑器里处理。

```bash
git restore --staged -- hello.txt
```

这会调整暂存区，工作区文件的现有内容仍然留着。[git restore 手册](https://git-scm.com/docs/git-restore)

### 恢复文件

如果已经确认某个文件的未暂存改动都不需要，可以先看差异，再恢复。

```bash
git diff -- hello.txt
git restore -- hello.txt
```

默认情况下，这会让工作区的 `hello.txt` 恢复成暂存区里的版本。被覆盖的未提交修改可能无法通过 Git 找回，所以先看 `diff`，确认要舍弃的是哪一部分。[git restore 手册](https://git-scm.com/docs/git-restore)

### stash

手头改到一半，又需要切去处理另一件事时，可以先暂存到 stash。

```bash
git stash push -u -m "暂存"
git stash list
```

`-u` 把未跟踪文件也包含进去，已经忽略的文件继续留在本地。回来以后可以先用 `git stash apply` 恢复最近一份，确认文件正确，再用 `git stash drop` 删除最近这份 stash。恢复时也可能发生冲突，需要检查 `git status` 并处理。[git stash 手册](https://git-scm.com/docs/git-stash)

## 10. 提交实践

假设已经克隆项目，当前在自己的工作分支。你需要提交一个修改，如下：

```bash
git status --short --branch
git add -- 文件名
git diff --cached
git commit -m "提交信息"
```

`git diff --cached`能看到自己准备保存的内容。提交后查看当前分支和远端，再推送到对应分支。例如当前分支叫 `docs/docker` 时，可以这样执行。

```bash
git remote -v
git push -u origin 分支名
```

### 换行符

Windows 终端里出现 `LF will be replaced by CRLF` 时，Git 正在提示工作区换行符可能按配置转换。`LF` 和 `CRLF` 是两种行结束方式。可以先看 `git status` 确认暂存结果，项目如果已经有 `.gitattributes`，就按其中的约定处理。[Git 换行符配置](https://git-scm.com/docs/git-config)

## 参考资料

- [Pro Git 中文版](https://git-scm.com/book/zh/v2)
- [Git 命令参考](https://git-scm.com/docs)
- [git status 手册](https://git-scm.com/docs/git-status)
- [git restore 手册](https://git-scm.com/docs/git-restore)
