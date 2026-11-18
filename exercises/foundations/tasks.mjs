export const foundationTasks = [
  {
    id: 'linux-files', subject: 'linux', title: '第 1 关 · 整理项目文件',
    goal: '项目文件都放在 incoming 目录里。用终端建立目录，把源码和说明文件整理好，并留下原始文件。',
    files: {'incoming/main.py': 'print("Hello from Linux!")\n', 'incoming/notes.txt': 'Linux practice\n'},
    editable: [], entry: 'incoming/notes.txt',
    requirements: ['创建 project/src 和 project/docs。', '把 main.py 复制到 project/src，把 notes.txt 复制到 project/docs 并改名为 README.txt。', '创建 project/docs/backup.txt，内容与 README.txt 相同。incoming 中的文件保留。'],
    expected: 'project/src/main.py\nproject/docs/README.txt\nproject/docs/backup.txt',
    commands: 'find project -type f | sort\ncat project/docs/README.txt\ncmp project/docs/README.txt project/docs/backup.txt',
    hint: 'mkdir -p 可以创建中间目录。cp 可以在复制时指定新名字。cmp 没有输出且退出码为 0，表示两个文件内容相同。',
    example: 'mkdir -p demo/docs\nprintf "%s\\n" "hello" > demo/docs/note.txt\ncp demo/docs/note.txt demo/docs/copy.txt\nfind demo -type f'
  },
  {
    id: 'linux-logs', subject: 'linux', title: '第 2 关 · 筛选运行日志',
    goal: '服务产生了一份日志。编写 report.sh，筛选错误并生成报告，之后可以重复运行这个脚本。',
    files: {'app.log': 'INFO server started\nERROR database unavailable\nINFO retrying\nERROR request timeout\nINFO server stopped\n', 'report.sh': '#!/usr/bin/env bash\n# TODO: 筛选 app.log，生成 errors.txt 和 count.txt\n'},
    editable: ['report.sh'], entry: 'report.sh',
    requirements: ['用 grep 把 app.log 中包含 ERROR 的行写入 errors.txt。', '统计错误行数，把数字写入 count.txt。', '给 report.sh 的所有者增加执行权限，用 ./report.sh 执行。重复运行时覆盖旧报告。'],
    expected: 'errors.txt\nERROR database unavailable\nERROR request timeout\n\ncount.txt\n2',
    commands: './report.sh\ncat errors.txt\ncat count.txt',
    hint: 'grep 可以按内容筛选，wc -l 统计行数，> 会覆盖文件。chmod u+x report.sh 给所有者增加执行权限。',
    example: '#!/usr/bin/env bash\ngrep "INFO" app.log > info.txt\nwc -l < info.txt > info-count.txt'
  },
  {
    id: 'git-commit', subject: 'git', title: '第 1 关 · 创建一次提交',
    goal: '练习目录已经有一个独立的 Git 仓库。修改说明文件，选择本次要保存的内容，并创建一次提交。',
    files: {'README.md': '# Git practice\n', '.gitignore': '# TODO: 忽略 scratch.txt\n', 'scratch.txt': 'temporary notes\n'},
    editable: ['README.md', '.gitignore'], entry: 'README.md',
    requirements: ['在 README.md 中新增一行 Hello from Git!。', '在 .gitignore 中加入 scratch.txt。', '只暂存 README.md 和 .gitignore，提交说明写为 添加项目说明。'],
    expected: '最新提交说明为 添加项目说明。\n提交包含 README.md 和 .gitignore 的修改。\nscratch.txt 保留在本地，git status --short 没有输出。',
    commands: 'git status --short\ngit log -1 --oneline\ngit show --stat HEAD\ngit check-ignore scratch.txt',
    hint: '文件保存以后还要 git add，再用 git diff --cached 检查。仓库已配置练习用的作者信息。',
    example: 'git status --short\ngit add -- README.md\ngit diff --cached\ngit commit -m "更新说明"'
  },
  {
    id: 'git-branch', subject: 'git', title: '第 2 关 · 合并功能分支',
    goal: '在独立分支里修改说明文件，完成提交后再合回 main，观察同一份文件在不同分支上的变化。',
    files: {'README.md': '# Git practice\n'}, editable: ['README.md'], entry: 'README.md',
    requirements: ['从 main 创建并切换到 docs/linux 分支。', '在 README.md 中新增一行 Linux notes ready，然后提交，提交说明写为 添加 Linux 说明。', '切回 main，合并 docs/linux。确认 main 中也有这行内容，工作区干净。'],
    expected: '当前分支为 main。\nREADME.md 包含 Linux notes ready。\nmain 与 docs/linux 指向同一个提交，git status --short 没有输出。',
    commands: 'git branch --show-current\ngit log --oneline --graph --decorate -n 5\ngit status --short',
    hint: '先切换到功能分支，再编辑文件。切换分支后重新选择文件，可在编辑器里读取终端中的最新内容。',
    example: 'git switch -c docs/example\n# 修改文件并提交后\ngit switch main\ngit merge docs/example'
  }
];
