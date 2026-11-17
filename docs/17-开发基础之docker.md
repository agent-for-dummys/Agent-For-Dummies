# 开发基础之 Docker

## 1. Docker 是什么

假设你拿到一个项目，仓库里有源码和 README。要把它跑起来，你得安装指定版本的 Python、装好依赖，再配上数据库和环境变量。如果换一台机器，又要再做一遍这些步骤（还不一定能成功）。因此，Docker 就成为一个非常重要的开发工具。

Docker 可以把应用和它依赖的运行环境做成一个镜像，再用镜像启动容器。接手项目的人拿到镜像以后，可以用镜像中准备好的 Python 和依赖启动应用。数据库地址之类随环境变化的配置都可以在启动容器时传进去。

## 2. 为什么要用容器

其实用虚拟机也能保存一套配好的开发环境。不过，每开一台虚拟机，都要启动一套带内核的操作系统。Linux 容器里的程序以进程的形式运行，多个容器可以共用同一个 Linux 内核，同时各自有独立的文件系统、进程和网络视图。在 Linux 上，容器共享宿主机的内核。在 Windows 或 macOS 上用 Docker Desktop 跑 Linux 容器时，它们共享的是 Docker Desktop 启动的 Linux 虚拟机的内核。

比如，你手上一个项目需要 Python 3.11，另一个需要 Python 3.12。可以分别用对应版本的 Python 镜像构建，再把两个项目各自的依赖装进镜像。启动后，每个容器里的 `python` 都是该项目需要的版本。两个项目可以在同一台机器上同时运行，给其中一个项目换 Python 版本也不会影响另一个。

## 3. 镜像、容器和仓库

### 镜像里有什么

镜像包含应用启动需要的文件，例如程序、运行时、库和配置，也可以带上默认工作目录、环境变量和启动命令。打开一个基于 Ubuntu 的容器会看到熟悉的 `/usr` 和 `/etc`，这些目录里的文件来自镜像提供的用户空间。

镜像由只读层叠加得到。如果两个应用都基于同一个 Python 镜像，它们可以共享底下相同的镜像层，只在上面各自增加项目的依赖和文件。

### 从同一个镜像启动两个容器

把镜像想成类，容器就像用这个类创建的实例。Docker 给每个容器加一层独立的可写层。在其中一个容器里新建文件，另一个容器看不到这个文件，原来的镜像也不会被改动。

停止容器后，可写层还在，用 `docker start` 可以再启动原来的容器。删掉容器以后，它的可写层也会被移除。如果只是想升级后端镜像，但还要留住原来的数据库文件，就得提前把数据存到卷或宿主机目录里。

### 镜像从哪里来

Registry 是存放和分发镜像的服务，Docker Hub 就是一个常见的 Registry。一个 Registry 里有多个镜像仓库，同一个仓库里可以用不同的标签区分版本。比如 `ubuntu:24.04` 中，`ubuntu` 是仓库名，`24.04` 是标签。Docker 在省略标签时使用 `latest`，其指向由仓库维护者决定。想让团队按同一个 Ubuntu 版本构建时，可以把版本标签直接写进 Dockerfile。

## 4. 先跑一个容器看看吧

###  `docker run` 做了什么

```bash
docker run --name first-run alpine:3.22 echo "Hello from Docker"
docker ps -a
```

本地没有 `alpine:3.22` 时，Docker 默认会先拉取镜像。接着它创建并启动容器，在里面执行 `echo`。文字打印出来以后，主进程退出，容器进入停止状态。此时 `docker ps` 看不到它，加上 `-a` 就能找到处于 `Exited` 状态的 `first-run`。如果再执行一次同样的 `docker run`，会遇到名字冲突，因为上一条命令创建的容器还在。

想临时进 Ubuntu 试几条命令，可以用下面的写法。

```bash
docker run --rm -it ubuntu:24.04 bash
```

`-i` 保持标准输入开启，`-t` 分配终端。输入 `exit` 后，作为主进程的 Bash 结束，`--rm` 会让 Docker 自动删除这个容器。跑后台服务时常用 `-d`，应用要读取环境变量时可以加 `-e 键=值`。需要从宿主机访问容器内的服务时，可以用 `-p 宿主机端口:容器端口` 发布端口。

### 基本命令

| 命令 | 什么时候用 |
| --- | --- |
| `docker images` | 查看本地有哪些镜像和标签 |
| `docker pull ubuntu:24.04` | 提前下载一个指定的镜像 |
| `docker ps` / `docker ps -a` | 查看运行中的容器，或连同停止的容器一起查看 |
| `docker logs web` | 查看名为 `web` 的容器输出，持续查看可以加 `-f` |
| `docker exec -it web sh` | 在运行中的 `web` 容器里另外启动一个 shell |
| `docker attach web` | 接到容器主进程的输入和输出 |
| `docker cp web:/app/report.txt .` | 把容器里的文件复制到宿主机当前目录，也可以调换方向 |
| `docker stop web` / `docker start web` | 停止或重新启动已有的容器 |
| `docker rm first-run` | 删除前面已经停止的容器 |
| `docker rmi ubuntu:24.04` | 移除本地的镜像标签，镜像还被容器引用时可能需要先处理该容器 |

## 5. Dockerfile

### Dockerfile 基本介绍

假设手头有一个 `main.cpp`，想让没有安装 g++ 的同学也能运行它。手工操作的话，要进 Ubuntu 装编译工具，再把源文件放进去编译。把这些步骤写进 Dockerfile 以后，换人构建也能用同一套操作。

```cpp
#include <iostream>

int main() {
    std::cout << "Hello from C++ in Docker\n";
}
```

把下面的内容保存为与 `main.cpp` 同目录的 `Dockerfile`。

```dockerfile
FROM ubuntu:24.04
WORKDIR /src

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY main.cpp ./
RUN g++ main.cpp -o hello
CMD ["./hello"]
```

`FROM` 选定基础镜像，`WORKDIR` 把后续指令的工作目录设成 `/src`，目录缺失时会自动创建。如果只写一条 `RUN cd /src` ，就只会在当下 shell 进程中切换目录，下一条 `RUN` 有自己的 shell。这里的 `COPY` 把源文件放进镜像，接下来的 `RUN` 在构建时完成编译，`CMD` 则留到容器启动时执行。像 `CMD ["./hello"]` 这样的数组写法会直接执行程序。对于这个没有设置 `ENTRYPOINT` 的例子，也可以在镜像名后面传入命令来替换默认的 `CMD`。

```bash
docker build -t cpp-demo:1.0 .
docker run --rm cpp-demo:1.0
```

`-t` 指定镜像名和标签。改完 `main.cpp` 后，再执行一次构建和运行命令，就能看到新程序的输出。

`docker build` 末尾的 `.` 把当前目录交给 Docker 作为构建上下文。假如 Dockerfile 放在项目根目录下的 `docker/` 中，可以从根目录执行 `docker build -f docker/Dockerfile -t cpp-demo:1.0 .`。此时 `-f` 决定读哪个 Dockerfile，`COPY main.cpp ./` 仍然从项目根目录取 `main.cpp`，目标路径则按镜像内的 `WORKDIR` 计算。

如果 `COPY` 提示找不到文件，先看源文件是否在构建上下文内，以及有没有被 `.dockerignore` 排除。`.dockerignore` 放在构建上下文的根目录，可以排除 `.git`、本地虚拟环境和存放本地配置的 `.env` 等构建用不上的文件。

### 分层和缓存

修改文件系统的指令通常会产生新的镜像层。假如一条 `RUN` 下载了安装文件，下一条 `RUN` 再把它们删掉，容器里虽然看不到这些文件，前一层仍然保存着它们，所以清理软件包索引时，把清理和安装写在同一条 `RUN` 里。像 `CMD` 这样的指令主要设置镜像的运行配置。

Docker 也会尝试复用上次构建的结果。上面的例子把装编译工具放在 `COPY main.cpp` 之前。只改 C++ 源码时，安装工具那一步可以命中缓存，复制和编译再重新执行。

### 写一个 Dockerfile！

假设项目根目录里已经有 `manage.py`、`requirements.txt` 和提交好的数据库迁移文件。可以先复制依赖清单并安装依赖，之后再复制整个项目。这样改了一个视图函数时，通常能复用前面的依赖安装结果。

```dockerfile
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

`ENV` 设置容器启动时也能读到的环境变量，这里让 Python 的标准输出及时出现在容器日志里。开发服务器要监听容器里的 `0.0.0.0`，这样才能接收通过端口映射转发的请求。`EXPOSE` 记录应用使用的端口，在宿主机上发布端口仍要加 `-p`。

项目使用默认 SQLite 配置时，可以先用下面的命令在本地跑起来。启动命令先执行已有的迁移，成功后再启动开发服务器。

```bash
docker build -t django-demo:dev .
docker run --name web -p 127.0.0.1:8000:8000 django-demo:dev sh -c "python manage.py migrate && exec python manage.py runserver 0.0.0.0:8000"
```

访问 `http://127.0.0.1:8000` 时，请求由宿主机的 8000 端口转到容器的 8000 端口。这里的 `runserver` 用于本地开发。等后面换成独立的数据库，再把迁移放到启动项目的命令里执行。

### 多阶段构建

回到 C++ 的例子。编译好的程序在运行时用不到 g++ 和源代码，继续把这两样放在最终镜像里会占空间。可以用两条 `FROM` 把编译和运行分开，每条 `FROM` 开启一个新阶段。

```dockerfile
FROM ubuntu:24.04 AS builder
WORKDIR /src
RUN apt-get update && apt-get install -y --no-install-recommends build-essential
COPY main.cpp ./
RUN g++ -static main.cpp -o hello

FROM scratch
COPY --from=builder /src/hello /hello
CMD ["/hello"]
```

`COPY --from=builder` 的源路径在编译阶段的文件系统里。最终镜像基于空的 `scratch`，只复制可执行文件。这个小程序用 `-static` 把用到的库静态链接进去，可以直接运行。换成需要动态库、证书或其他资源的程序时，运行阶段也要提供相应的文件。

## 6. Docker Volume

### 用数据卷保留容器写入的文件

假设第一次启动服务后创建了几条数据，后来为了更新镜像而删掉旧容器。如果这些文件写在旧容器的可写层里，新的容器就找不到它们。命名数据卷由 Docker 管理，删除容器后，重新把同一个卷挂给新容器就可以读到原来的文件。

```bash
docker volume create demo-data
docker run --rm --mount type=volume,source=demo-data,target=/data alpine:3.22 sh -c "echo saved > /data/note.txt"
docker run --rm --mount type=volume,source=demo-data,target=/data alpine:3.22 cat /data/note.txt
```

第一次运行的容器结束后就被删掉了，第二次启动的容器仍会打印 `saved`，因为它挂载了同一个卷。可以用 `docker volume ls` 列出数据卷，用 `docker volume inspect demo-data` 查看卷本身的信息。要确认某个容器挂到了哪个路径，可以在 `docker inspect 容器名` 的 `Mounts` 字段里找。确定数据用完后，用 `docker volume rm demo-data` 删除这个卷，卷仍被容器引用时需要先移除引用它的容器。

### 挂载宿主机文件

开发时有时希望容器直接读到手头的文件，例如容器要使用宿主机上的一份配置。这可以用绑定挂载。下面的 PowerShell 示例在存有 `config.json` 的目录里执行。

```powershell
docker run --rm --mount "type=bind,source=$($PWD.Path)/config.json,target=/config.json,readonly" alpine:3.22 cat /config.json
```

`source` 指向宿主机上已存在的文件，`target` 是容器里的路径。省略 `readonly` 时，容器默认可以尝试写入挂载位置，实际权限还取决于宿主机上的文件权限。如果把宿主机目录挂到容器的 `/app`，镜像自带的 `/app` 内容在挂载期间会被盖住。代码原本已复制进镜像，挂载后却找不到时，可以先检查目标路径。

## 7. Docker Compose

### 把后端和数据库写进同一份配置

如果 Django 改用 MySQL，每次启动就要准备网络、创建数据库容器、挂载数据卷，再把数据库地址交给后端。可以在 Django 项目根目录新建 `compose.yaml`，把这些参数写下来。YAML 用缩进表示归属关系，下面的 `ports` 和 `environment` 都属于各自缩进下的服务。

```yaml
services:
  web:
    build: .
    command:
      - sh
      - -c
      - python manage.py migrate && exec python manage.py runserver 0.0.0.0:8000
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      DB_HOST: db
      DB_PORT: "3306"
      DB_NAME: app
      DB_USER: app
      DB_PASSWORD: local-demo
    depends_on:
      db:
        condition: service_healthy

  db:
    image: mysql:8.4
    environment:
      MYSQL_DATABASE: app
      MYSQL_USER: app
      MYSQL_PASSWORD: local-demo
      MYSQL_ROOT_PASSWORD: local-root-demo
    volumes:
      - mysql-data:/var/lib/mysql
    healthcheck:
      test: ["CMD-SHELL", "MYSQL_PWD=\"$$MYSQL_PASSWORD\" mysql -h 127.0.0.1 -u \"$$MYSQL_USER\" \"$$MYSQL_DATABASE\" -e 'SELECT 1'"]
      interval: 5s
      timeout: 5s
      retries: 20
      start_period: 30s

volumes:
  mysql-data:
```

这个例子假设项目已安装 Django 可用的 MySQL 驱动，且 `settings.py` 中的 `DATABASES` 已配置为从这些 `DB_*` 环境变量读取连接参数。若驱动需要编译，Python 镜像的 Dockerfile 也要补上相应的系统依赖。示例密码用于本地练习。

两个服务默认加入同一个项目网络，`web` 可以用服务名 `db` 访问数据库的 3306 端口。这里无需把 MySQL 的端口发布到宿主机。MySQL 第一次启动时还要初始化数据库和用户，容器刚开始运行时，后端连过去可能会失败。这里用健康检查确认示例账号已经能执行查询，Compose 再启动后端。健康检查里的 `$$` 会把变量引用留给容器内的 shell 展开。[Docker Compose 启动顺序](https://docs.docker.com/compose/how-tos/startup-order/)

### 从项目目录启动和查看日志

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f web
docker compose down
```

如果前面的单容器示例还在占用 8000 端口，可以先执行 `docker stop web`。Compose 启动后仍然从 `http://127.0.0.1:8000` 访问后端。改了 Python 依赖或源码，可以再次执行带 `--build` 的启动命令。普通的 `docker compose down` 会移除服务容器和项目网络，命名卷 `mysql-data` 中的数据会留到下次启动。只有确定要清空这套数据库时，才加上 `--volumes`。

## 参考资料

- [酒井科协暑培 2025 Docker 课程讲义](https://summer25.net9.org/backend/docker/note/)
- [Dockerfile 指令参考](https://docs.docker.com/reference/dockerfile/)
