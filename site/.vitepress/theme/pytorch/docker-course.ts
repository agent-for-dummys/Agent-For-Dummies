import {foundationTasks} from '../../../../exercises/foundations/tasks.mjs';
import type {CourseMap} from './course-navigation';

export const expectedOutput = 'Hello！You will be an excellent coder！';
export const dockerExample = `FROM ubuntu:24.04
CMD ["echo", "Hello, Docker!"]`;

export const cppDockerExample = `FROM ubuntu:24.04
WORKDIR /demo
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \\
    && rm -rf /var/lib/apt/lists/*
COPY main.cpp ./
RUN g++ -std=c++17 main.cpp -o demo
CMD ["./demo"]`;

export const multiStageDockerExample = `FROM ubuntu:24.04 AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY main.cpp ./
RUN g++ -std=c++17 -static main.cpp -o demo

FROM scratch
COPY --from=builder /app/demo /demo
CMD ["/demo"]`;

export const dockerTasks = [
  {
    id: 'docker-build',
    title: '第 1 关 · 构建并运行 C++ 项目',
    search: 'dockerfile Ubuntu make build run',
    goal: '拿到一个 C++ 项目后，怎样让别人只用 Docker 就能编译并运行它？给右侧的项目补上一份 dockerfile。',
    requirements: [
      '使用 ubuntu:24.04 作为基础镜像，安装 make 和 C++ 编译器。',
      '将 main.cpp 和 Makefile 复制到镜像的工作目录，再用 make 生成 hello。',
      '让容器启动时执行 hello，输出下方的一行文字。',
    ],
    hint: 'build-essential 包含 make 和 g++。可以把更新软件包列表和安装写在同一条 RUN 中。CMD 会在容器启动时执行，记得先用 RUN make 生成程序。',
    commands: 'docker build -f dockerfile -t coder:step1 .\ndocker run --rm coder:step1',
  },
  {
    id: 'docker-multi-stage',
    title: '第 2 关 · 用多阶段构建缩小镜像',
    search: 'dockerfile 多阶段 scratch 静态链接',
    goal: '继续修改dockerfile，考虑如何才能让dockerfile占用的空间更小',
    requirements: [
      '在基于 ubuntu:24.04 的编译阶段安装工具，复制文件并调用 Makefile。',
      '最后一个阶段使用 scratch，通过 COPY --from 只复制编译出的 hello。',
      '启动容器后得到与第一关相同的输出，再对比两个镜像的大小。',
    ],
    hint: 'scratch 没有 C++ 动态库，也没有 shell。可以在 Makefile 中加入 LDFLAGS += -static，再照常运行 make。也可以直接运行 make LDFLAGS=-static。最后用 CMD 的数组写法执行 /hello。',
    commands: 'docker build -f dockerfile -t coder:step2 .\ndocker run --rm coder:step2\ndocker image ls coder',
  },
];

export const developmentTasks = [...dockerTasks, ...foundationTasks];

export const developmentMap: CourseMap = {
  sections: [{
    id: 'docker',
    title: 'Docker',
    x: 340,
    y: 76,
    items: dockerTasks.map(({id, title, search}) => ({id, title, search})),
    tasks: dockerTasks.map(({id}) => id),
    entry: dockerTasks[0].id,
  }, {
    id: 'git',
    title: 'Git',
    x: 0,
    y: 0,
    items: foundationTasks.filter(task=>task.subject==='git'),
    tasks: foundationTasks.filter(task=>task.subject==='git').map(task=>task.id),
    entry: 'git-commit',
  }, {
    id: 'linux',
    title: 'Linux',
    x: 0,
    y: 152,
    items: foundationTasks.filter(task=>task.subject==='linux'),
    tasks: foundationTasks.filter(task=>task.subject==='linux').map(task=>task.id),
    entry: 'linux-files',
  }],
  edges: [['git', 'docker'], ['linux', 'docker']],
};
