<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/logo-light.svg">
    <img alt="UniXNU" src="assets/logo-light.svg" width="200">
  </picture>
</p>

<p align="center">
  <a href="https://unixnu.com"><img alt="文档" src="https://img.shields.io/badge/docs-unixnu.com-2A5BD7?logo=readthedocs&logoColor=white"></a>
  <a href="https://t.me/unixnu"><img alt="Telegram" src="https://img.shields.io/badge/Telegram-@unixnu-26A5E4?logo=telegram&logoColor=white"></a>
  <a href="https://qun.qq.com/universal-share/share?ac=1&authKey=Pubz23DOCY76nxjlGuSms2zesk4jRvas4zrXJRYk7omf7CprXbGQigLEI%2BCoYR8D&busi_data=eyJncm91cENvZGUiOiIxMTI2MTE2NzU5IiwidG9rZW4iOiJwSHJsUDN1UnN2Vi8yM210TjJRbzBIcERmcUpyOS9lb0hHVVpadWdvVFdScVpSYUFLT1YzTk5TWC9mN2xWYmtIIiwidWluIjoiMzE1MTEwOTc0MSJ9&data=_cJgr-jX9yJ2-GXwVjRN5FOhDyk5B-HAfIk5LSunbW_XkkmKqNXbpH33wzP93J0p9DI1fbjgBUrUfTVhwDcxjg&svctype=4&tempid=h5_group_info"><img alt="QQ 群" src="https://img.shields.io/badge/QQ%20Group-join-12B7F5?logo=qq&logoColor=white"></a>
  <a href="https://x.com/UniXNU_new"><img alt="X" src="https://img.shields.io/badge/X-@UniXNU__new-000000?logo=x&logoColor=white"></a>
</p>

**本项目始终免费、自由、开源，且不分发 Apple 和任何厂商的私有二进制以合规。请不要通过盈利性质的网盘分发或销售预编译镜像。若您执意如此，请[参见](https://baidu.ma/?q=5a2k5YS/5oCO5LmI5Yqe55CG5oi35Y+j5pys)。**

<p align="center">
  <a href="README.md">English</a> | 简体中文
</p>

# UniXNU

> **迁移通知：** 请按[迁移指南](https://unixnu.com/zh/porting/migration)更新设备仓库，接入共享 SoC 支持并统一组件名称。

> **本 fork** 是 `TongHuaQWQ/UniXNU` 的 `macos` 分支（基于上游 `feat/macos`），是小米平板 7
> （`uke`，SM7675）移植 macOS 26.5.2（25F84）的**内核侧**。设备仓库是 `TongHuaQWQ/macOS-ForUke`，
> 从那里开始读。本分支在 `feat/macos` 之上额外携带：把 fileset 预链接读取的对照内核固定到独立链接
> （`XNU_KERNEL_CHAINED_FIXUPS=0`）；预链接改为从随仓库发布的对照表
> （`reference-names.json[.gz]`）读取同名证据，而不是重编一个带符号内核；`/chosen/pram` 取两侧的并集；
> `UniXNUPkg` 读取本固件发布的 `gUkeMemStatusGuid` 表并在菜单上显示上次 panic；bootstrap 轮次把预期
> 的链接失败报告出来而不是整轮判失败；`.gitmodules` 里 `drivers/ArmCpu`、`drivers/DarwinBoot`、
> `kits/XnuPrelink` 指向各自的 fork。用法与上游完全一致：`./unixnu <命令> -D <设备仓库>`。

## 1. 这是什么

UniXNU 是一个独立项目，通过 UEFI 在非 Apple ARM64 硬件上运行 iOS 与 macOS。UniXNU 类似 OpenCore，
是通用的 UEFI 环境和驱动加载系统：通过统一的 UEFI 层加载设备所需的驱动并启动系统。

本仓库是这套体系的**构建驱动**。`./unixnu` 解析 ARM64、SoC、OS 与设备四层配置，补全组件依赖，在
`out/<device>/<os_profile>/<config>/tree` 组装目标树，然后按顺序执行各步骤：XNU 内核构建（含板级
归档列表）、把自建内核与原始 kernelcache 的 kext 配对并输出集合的**预链接**、**payload** FAT 卷、
UEFI **固件**构建，以及**启动镜像**打包。设备仓库所固定的共享输入也在这里：`profiles/arch/{arm64,arm64e}`、
`profiles/os/<profile>`、`components.toml`（组件目录）、`feeds.toml`（Apple 与 edk2 源码）、
UEFI package `package/UniXNUPkg`，以及 `drivers/`、`kits/` 下的组件子模块。

它是构建期仓库：产出设备仓库要刷写的内核、payload 和启动镜像，运行期只有 `UniXNU.efi` 来自这里。

## 2. 在这条链上的位置

它 fork 自 **`https://github.com/UniXNU/UniXNU.git`**（本分支 `macos` = `feat/macos` + 上述提交）。

固定*本仓库*的地方：

| 消费者 | 固定值 | 位置 |
| --- | --- | --- |
| `TongHuaQWQ/macOS-ForUke` | `UKE_CORE_REPO=TongHuaQWQ/UniXNU`、`UKE_CORE_REF=macos`，以 `UniXNU/` 检出在设备仓库旁 | `.github/workflows/build-kernel-min.yml`（`env:` 与 checkout 步骤） |
| `TongHuaQWQ/UniXNU-uke`（已被取代） | `core_repository` / `core_ref` 输入；旧的 `build-kernel.yml` 用 `Allenwdk/UniXNU@uke-gpu` | `.github/workflows/build-kernel-min.yml`、`.github/workflows/build-kernel.yml` |

本仓库在仓库内固定的依赖：

| 依赖 | 固定值 | 位置 |
| --- | --- | --- |
| `drivers/ArmCpu` → `https://github.com/UniXNU/ArmCpu.git` | 子模块 `93a5030…`；目录 `revision = "93a5030c5d983d0ef90f0fca93879d6e36ad1ba8"` | `.gitmodules`、`components.toml`（`id = "ArmCpu"`） |
| `drivers/DarwinBoot` → **fork** `https://github.com/TongHuaQWQ/DarwinBoot.git` | 子模块 `80d1695…`；`revision = "80d1695e9b8f8f83d94ecd04b0d702706dd0f0c9"` | `.gitmodules`（注明原因：加载器读 `<kernel>.lzma` 并接受集合大小的镜像）、`components.toml` |
| `kits/XnuPrelink` → **fork** `https://github.com/TongHuaQWQ/XnuPrelink.git` | 子模块 `a771457…`；`revision = "a7714579cb9f1243a74abe386dc18a5174da881e"`、`path = "kits/XnuPrelink"` | `.gitmodules`（注明原因：macOS 26 没有 KDK，配对需要按 kernelcache 构建逐条人工复核的身份）、`components.toml` |

设备仓库在其 `feeds.toml` 中再覆盖一层（first-wins，优先于子模块）：`sm7675` SoC 层、
`ArmCpu` 的板级副本（`local = "drivers/ArmCpu"`）、`XnuPrelink` 的板级副本
（`local = "kits/XnuPrelink"`）、A732 GPU/显示 fork，以及板级自己的 UFS 与触控驱动。

## 3. 依赖

| 输入 | 来源 | 缺失后果 |
| --- | --- | --- |
| Python 3.11+ | python.org / Homebrew | 什么都跑不起来：`./unixnu` 是 Python 程序。 |
| `git`、`make`、`clang`、`cmake`、`ninja`、`unifdef`、`mtools`、`dtc` | Xcode 命令行工具 / Homebrew（`brew install cmake ninja unifdef llvm mtools dtc`）；glibc Linux 用 `scripts/linux/setup-toolchain.py` | 驱动按名字检查这些工具并停止；`unifdef` 用于 libdispatch 头、`mtools` 用于 payload 卷、`dtc` 用于设备树属性。 |
| **macOS + Xcode**（`xcodebuild`、`iphoneos` SDK、MIG） | App Store / developer.apple.com，或 GitHub macOS runner | **内核**步骤无法运行。Linux 上 `scripts/linux/setup-toolchain.py` 安装带 XNU 类型内建函数的 clang，以及 cctools-port 的 ld64/mig/iig 代替 Xcode。 |
| `xnu` `apple-oss-distributions/xnu` @ `xnu-10063.141.1`（`d8b8029…`） | `feeds.toml`（`name = "xnu"`，另有 `darwin`、`driverkit_tag`、`trustcache_tag`） | 没有内核源码，内核步骤无事可做。 |
| `libplatform` 316.100.10、`libdispatch` 1477.100.9、`AvailabilityVersions` 141.1、`libpthread` 519.120.4、`IOStorageFamily` `e45fbe3…` | `apple-oss-distributions`（提交固定在 `feeds.toml`） | 缺少内核库：前四者是链接输入，`IOStorageFamily` 提供公共存储头文件。 |
| `corecrypto-2023` | `https://github.com/ONLYA/corecrypto-2023.git` @ `11fba65…` | 没有源码 corecrypto provider，`CONFIG_XNU_CRYPTO_BOOTSTRAP="source"` 的配置无法链接。 |
| `edk2` = **Mu_Basecore** `microsoft/mu_basecore` @ `release/202608`（`cfb9372…`）加五个子模块 | `feeds.toml` | 没有 UEFI package，也没有固件构建。 |
| 设备仓库（`-D ../UniXNU-<device>`） | 板级自己的 Git 仓库（例如 `TongHuaQWQ/macOS-ForUke`） | 没有可配置对象：`board.toml`、defconfig、补丁序列和归档列表都来自那里。 |
| 目标 IPSW / kernelcache | 设备 `board.toml` 的 `[ipsw] url`，或 `--ipsw` / `UNIXNU_IPSW`，或 `--kernelcache` / `UNIXNU_KERNELCACHE` | 预链接没有可配对的原始集合；`unixnu ipsw fetch` 失败。Apple 数据，可下载但体积大。 |
| Mu-Silicium UEFI 树（`uefi-<device>`） | 移植的第二个仓库，`--uefi DIR` / `UNIXNU_UEFI`；uke 的这份**未公开发布**——设备仓库以 `firmware/` 下的补丁形式携带其改动 | 没有 `boot.img`/固件卷；`build firmware` 与 `bootimg` 无法产出固件那一半。 |
| trust cache、Data ramdisk、平台种子（`--unique-chip-id`） | 设备或 IPSW；种子**无法从任何公开来源获取** | payload 步骤拒绝，或写入一个内核不认的占位值。 |
| `./unixnu fetch` 的网络访问 | GitHub | 子模块与 Apple/Mu_Basecore 源码拉不下来，`unixnu.lock` 无法写入。 |

## 4. 构建与使用

在本检出执行，设备仓库放在旁边（`-D` 会记进 `out/state.json`）：

```sh
git clone --recurse-submodules https://github.com/TongHuaQWQ/UniXNU
cd UniXNU
./unixnu defconfig uke-macos_defconfig -D ../macOS-ForUke
./unixnu fetch
./unixnu status --json
./unixnu tree
./unixnu build kernel -D ../macOS-ForUke          # 内核、归档、预链接
./unixnu build payload -D ../macOS-ForUke --kernel <kernel.macho>
./unixnu build firmware --uefi ../uefi-uke -D ../macOS-ForUke
./unixnu bootimg -D ../macOS-ForUke --uefi ../uefi-uke --dtb <firmware.dtb>
```

`./unixnu --help` 列出完整命令集：`defconfig`、`fetch`、`tree`、`build`
（以及 `kernel`、`package`、`firmware`、`payload`、`userdata`、`runtime`、`prelink` 快捷命令）、
`bootimg`、`vendor_boot`、`ipsw`、`status`、`clean`、`release`。`./unixnu release` 一次跑完依赖、
补丁、构建步骤和启动镜像并写清单，与设备仓库里 `templates/package.sh` 驱动的步骤相同。

驱动自身的宿主机检查：

```sh
python3 -m pytest scripts/unixnu            # 驱动单元测试（test_kernel.py、test_udif.py、test_vendor_boot.py）
python3 scripts/porting-record.py check --device ../macOS-ForUke
```

## 5. 相关文档

- [移植设备](https://unixnu.com/zh/porting/steps)——八个步骤及每步产出；本仓库对应步骤 2 的
  `UniXNU` 一行，以及步骤 4 与 7 的 `./unixnu` 命令；
- [设备仓库](https://unixnu.com/zh/porting/device-repository)——布局、`board.toml`、`feeds.toml`、
  完成与发布要求；
- [设备打包脚本](https://unixnu.com/zh/porting/packaging)、[驱动适配](https://unixnu.com/zh/porting/drivers)、
  [UEFI 固件](https://unixnu.com/zh/porting/uefi-firmware)、[日志抓取](https://unixnu.com/zh/porting/log-capture)；
- [构建与启动](https://unixnu.com/zh/building)、[构建环境](https://unixnu.com/zh/guide/requirements)、
  [CLI 参考](https://unixnu.com/zh/reference/cli)、[预链接](https://unixnu.com/zh/concepts/prelink)、
  [启动链](https://unixnu.com/zh/concepts/boot-chain)；
- 本仓库内：`docs/`（站点文档源码）、`docs/building.md`、`docs/concepts/`、`docs/drivers/`、
  `docs/porting/`、`components.toml`、`feeds.toml`、`profiles/`。

## 仓库

| 仓库 | 内容 |
| --- | --- |
| [UniXNU](https://github.com/UniXNU/UniXNU) | 构建工具、组件目录、ARM64 支持、OS 配置、UEFI package、文档 |
| [UniXNU-sm8550-common](https://github.com/UniXNU/UniXNU-sm8550-common) | SM8550 共享支持 |
| [UniXNU-sheng](https://github.com/UniXNU/UniXNU-sheng) | 小米平板 6S Pro |
| [uefi-sheng](https://github.com/UniXNU/uefi-sheng) | 小米平板 6S Pro 的 UEFI 固件 |

克隆时使用 `--recurse-submodules`。

## 参与贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

BSD-2-Clause-Patent，见 [LICENSE](LICENSE)。
