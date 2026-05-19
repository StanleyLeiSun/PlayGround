# KidsCheck Android

## 先决条件

- Android Studio（建议最新版稳定版）
- JDK 17（Android Studio 自带一般足够）

## 启动步骤

1. 先把后端跑起来：参考 `backend/README.md`，确保 `http://127.0.0.1:8000/docs` 能打开。
2. 用 Android Studio 打开 `android` 目录并 Sync。
3. 选择 emulator 或真机运行。

## 后端地址

工程里默认后端地址为模拟器访问本机的地址（`10.0.2.2`）：

- `android/app/src/main/java/com/kidscheck/app/data/api/RetrofitInstance.kt` 的 `BASE_URL = "http://10.0.2.2:8000"`

真机运行时，需要把 `BASE_URL` 改成你电脑在局域网内的 IP（例如 `http://192.168.1.10:8000`），并保证手机和电脑在同一网络。

