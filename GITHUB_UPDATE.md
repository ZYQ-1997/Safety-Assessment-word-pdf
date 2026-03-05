# 将本项目作为 zyq-1997/safety-assessment-2 的一次更新

## 当前状态

- **远程仓库**：`origin` → `https://github.com/zyq-1997/safety-assessment-2.git`
- **当前分支**：`main`

## 操作步骤

### 1. 查看将要提交的变更

```bash
cd "c:\Users\Z2200\Desktop\Safety Assessment - 1"
git status
```

### 2. 添加所有修改（或指定文件）

```bash
git add .
# 若不想提交某些文件，可先编辑 .gitignore，或使用：
# git add streamlit_app.py backend/app.py extract_all_tables.py .streamlit/ requirements.txt .gitignore STREAMLIT_CLOUD.md
```

### 3. 提交

```bash
git commit -m "feat: 表格提取与 Streamlit Cloud 部署准备"
```

（可把 `-m` 里的说明改成你想要的提交信息。）

### 4. 推送到 GitHub

```bash
git push origin main
```

若 GitHub 要求登录，会弹出浏览器或提示输入账号/Token；若已配置 SSH，可先把远程改为 SSH 地址再 push：

```bash
git remote set-url origin git@github.com:zyq-1997/safety-assessment-2.git
git push origin main
```

---

## 若远程还不是 safety-assessment-2

先添加或修改远程后再推送：

```bash
# 若还没有 origin
git remote add origin https://github.com/zyq-1997/safety-assessment-2.git

# 若 origin 指向别的仓库，可改为：
git remote set-url origin https://github.com/zyq-1997/safety-assessment-2.git

git push -u origin main
```

---

## 首次推送到空仓库

若 GitHub 上 `safety-assessment-2` 是新建空仓库，第一次推送可用：

```bash
git push -u origin main
```

`-u` 会设置上游分支，之后直接 `git push` 即可。
