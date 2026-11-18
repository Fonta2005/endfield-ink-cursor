# 发布到 GitHub · 全流程

> 适用于本仓库（Windows）。全程 PowerShell，每条命令都能直接复制。
> 目标：把一个本地文件夹变成 `https://github.com/<你>/<仓库名>` 上的公开项目。

---

## 第 0 步 · 发布前检查（5 分钟）

### 0.1 改版权署名

打开 `LICENSE`，第 3 行：

```
Copyright (c) 2026 <your-name>
```

把 `<your-name>` 换成你的 GitHub ID，例如：

```
Copyright (c) 2026 xiaojianwu
```

### 0.2 决定仓库名

建议 ASCII、小写、连字符：

```
endfield-ink-cursor
```

记下来，后面要用两次（本地 remote 和网页新建）。

### 0.3 确认没有隐私内容

- `previews/` 里不应出现聊天窗口、文件名、桌面图标等私人信息
- 图片里不要有别人 ID、群号、二维码
- 检查 `cursors/README.txt` 是否需要保留（安装说明，可留）

### 0.4 确认体积

```powershell
cd D:\deepseek\out\repo
"{0:N1} MB" -f ((Get-ChildItem -Recurse -File | Measure-Object Length -Sum).Sum/1MB)
```

小于 100 MB 直接推；超过就先精简或改用 Git LFS。本仓库约 7.9 MB，没问题。

---

## 第 1 步 · 安装 Git

```powershell
winget install --id Git.Git -e --source winget
```

装完**关掉当前终端，重新开一个**（PATH 才会刷新）。

验证：

```powershell
git --version
```

应输出类似 `git version 2.47.1.windows.1`。

> 如果 winget 报权限错误，改用官网安装包：https://git-scm.com/download/win
> 安装时全部默认，只在 "Adjusting your PATH" 一步选 **Git from the command line and also from 3rd-party software**。

---

## 第 2 步 · 配置身份（只需一次）

```powershell
git config --global user.name  "你的名字或ID"
git config --global user.email "你的GitHub邮箱"
```

**邮箱必须是 GitHub 账号里验证过的那个**，否则提交不会关联到你的头像。

顺便设置换行策略（Windows 必做，否则每次提交都会报"整个文件被修改"）：

```powershell
git config --global core.autocrlf true
```

---

## 第 3 步 · 初始化本地仓库

```powershell
cd D:\deepseek\out\repo
git init -b main
```

输出 `Initialized empty Git repository in D:/deepseek/out/repo/.git/`。

检查一下将要提交什么：

```powershell
git status
```

应该看到 `cursors/`、`previews/`、`assets/`、`tools/`、`README.md`、`LICENSE` 都是未跟踪文件；
`.gitignore` 会被识别（里面排除了日志和 `__pycache__`）。

---

## 第 4 步 · 首次提交

```powershell
git add .
git commit -m "feat: 祀的毛笔指针组 + 水墨涟漪 + 画卷文本光标"
```

成功会显示类似：

```
[main (root-commit) 3f2a1b7] feat: ...
 41 files changed, 1204 insertions(+)
```

查看提交：

```powershell
git log --oneline
```

---

## 第 5 步 · 在 GitHub 上建空仓库

1. 浏览器打开 https://github.com/new
2. **Repository name** 填 `endfield-ink-cursor`
3. **Description** 填简介（例如：`《终末地》祀的毛笔 · Windows 指针组 + 水墨点击涟漪 + 画卷光标`）
4. 选 **Public**
5. **以下三个都不要勾**：
   - ☐ Add a README file
   - ☐ Add .gitignore
   - ☐ Choose a license
   （勾了会产生一个初始提交，和本地历史冲突，push 会被拒）
6. 点 **Create repository**

创建后页面会显示一段 "…or push an existing repository from the command line"，里面有你仓库的地址，形如：

```
https://github.com/你的用户名/endfield-ink-cursor.git
```

---

## 第 6 步 · 关联远程并推送

### 6.1 关联

```powershell
git remote add origin https://github.com/你的用户名/endfield-ink-cursor.git
git remote -v
```

`git remote -v` 应显示两行（fetch / push），地址正确才行。

### 6.2 准备凭证（Personal Access Token）

GitHub 从 2021 年起**不再接受账号密码**，必须用 token：

1. 打开 https://github.com/settings/tokens
2. 点 **Generate new token** → **Generate new token (classic)**
3. **Note** 填 `cursor-kit-push`
4. **Expiration** 选 30 days（够用，安全）
5. **Select scopes** 勾选 **`repo`**（整个大类，包含下面所有子项）
6. 拉到底点 **Generate token**
7. 页面只显示一次，**立刻复制**（形如 `ghp_xxxxxxxxxxxx`），存到密码管理器

> 用 Fine-grained token 也行，但要额外选仓库和 Contents: Read and write 权限，classic 更省事。

### 6.3 推送

```powershell
git push -u origin main
```

会弹出一个窗口（Git Credential Manager）：

- **Username**：你的 GitHub 用户名
- **Password**：粘贴刚才那个 `ghp_...` token（**不是**账号密码）

成功后输出：

```
Enumerating objects: 45, done.
Writing objects: 100% (45/45), 7.81 MiB | 2.10 MiB/s, done.
To https://github.com/你的用户名/endfield-ink-cursor.git
 * [new branch]      main -> main
branch 'main' set up to track 'origin/main'.
```

凭证会被 Windows 凭据管理器记住，下次不用再输。

---

## 第 7 步 · 验证

打开 `https://github.com/你的用户名/endfield-ink-cursor`，逐项确认：

| 检查项 | 期望 |
|---|---|
| README 是否渲染成网页 | 有标题、目录、图片 |
| 头图是否显示 | 壁纸实拍那张 |
| GIF 是否动 | 亮底 / 暗底两行 |
| 文件列表 | cursors / previews / assets / tools 四个目录 |
| 右侧 About | 此时可能还是空的，下一步补 |
| 提交记录 | 1 条，头像关联到你的账号 |

图片不显示 = 路径大小写不对或文件没推上去，用 `git ls-files previews/` 核对。

---

## 第 8 步 · 发布 Release（可下载包）

仓库里不放 11 MB 的 zip，改用 Release 附件：

1. 打开仓库页 → 右侧 **Releases** → **Create a new release**
2. **Choose a tag** 输入 `v1.0.0` → 点 "Create new tag on publish"
3. **Release title**：`v1.0.0 · 首次发布`
4. **Describe this release**：
   ```
   完整指针包：11 个 .cur/.ani + 点击涟漪工具 + 安装/还原脚本。
   下载 si-cursor.zip 解压后双击 install.cmd 即可。
   ```
5. 把 `D:\deepseek\out\si-cursor.zip` 拖进 "Attach binaries by dropping them here"
6. 点 **Publish release**

发布后回到仓库，在 README 顶部加一行（编辑网页或本地改完再 push 都行）：

```markdown
**[⬇ 直接下载完整包（v1.0.0）](https://github.com/你的用户名/endfield-ink-cursor/releases/latest)**
```

---

## 第 9 步 · 补全 About 和 Topics

仓库首页右上角 **⚙ 齿轮**（About 旁）：

- **Description**：
  `《终末地》祀的毛笔 · Windows 指针组 + 水墨点击涟漪 + 画卷光标。纯脚本生成，个人同人。`
- **Website**：留空（没有就不填）
- **Topics**（逐个输入回车）：
  `windows` `cursor` `custom-cursor` `arknights-endfield` `cur` `ani` `csharp` `python` `pillow` `fan-art`
- 勾选 **Releases**、**Packages** 视需要

保存。

---

## 第 10 步 · 以后如何更新

改完文件后三行：

```powershell
cd D:\deepseek\out\repo
git add -A
git commit -m "fix: 修正文本光学标的弯弧幅度"
git push
```

（第二次起不用再写 `-u origin main`。）

查看状态 / 撤销：

```powershell
git status              # 当前改动
git diff                # 具体改了什么
git checkout -- 文件名   # 撤销未提交的改动
git log --oneline -10   # 最近 10 条提交
```

---

## 常见错误速查

| 报错 | 原因 | 解决 |
|---|---|---|
| `git: 无法将"git"项识别为...` | PATH 没刷新 | 关掉终端重开 |
| `remote origin already exists` | 已关联过 | `git remote set-url origin 新地址` |
| `rejected ... non-fast-forward` | 远程有本地没有的提交（多半建仓库时勾了 README） | `git pull --rebase origin main` 再 push |
| `Authentication failed` | 用了账号密码 | 改用 PAT token |
| `file is 120 MB; this exceeds GitHub's file size limit` | 大文件 | 从提交里移除，改用 Release 附件 |
| 图片 404 | 路径大小写 / 没提交 | `git ls-files previews/` 核对 |
| 中文文件名显示乱码 | Windows 编码 | 仓库内文件名统一用 ASCII |
| 每次提交都显示整个文件改动 | 换行符 | `git config --global core.autocrlf true` 后重新 `git add` |

---

## 一页速查（假设 git 已装好）

```powershell
cd D:\deepseek\out\repo
git init -b main
git config user.name  "你的ID"
git config user.email "你的邮箱"
git add .
git commit -m "feat: 祀的毛笔指针组"
git remote add origin https://github.com/你的用户名/endfield-ink-cursor.git
git push -u origin main
```
