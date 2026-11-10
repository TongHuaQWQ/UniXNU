<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/logo-light.svg">
    <img alt="UniXNU" src="assets/logo-light.svg" width="200">
  </picture>
</p>

<p align="center">
  <a href="https://unixnu.com"><img alt="Documentation" src="https://img.shields.io/badge/docs-unixnu.com-2A5BD7?logo=readthedocs&logoColor=white"></a>
  <a href="https://t.me/unixnu"><img alt="Telegram" src="https://img.shields.io/badge/Telegram-@unixnu-26A5E4?logo=telegram&logoColor=white"></a>
  <a href="https://qun.qq.com/universal-share/share?ac=1&authKey=Pubz23DOCY76nxjlGuSms2zesk4jRvas4zrXJRYk7omf7CprXbGQigLEI%2BCoYR8D&busi_data=eyJncm91cENvZGUiOiIxMTI2MTE2NzU5IiwidG9rZW4iOiJwSHJsUDN1UnN2Vi8yM210TjJRbzBIcERmcUpyOS9lb0hHVVpadWdvVFdScVpSYUFLT1YzTk5TWC9mN2xWYmtIIiwidWluIjoiMzE1MTEwOTc0MSJ9&data=_cJgr-jX9yJ2-GXwVjRN5FOhDyk5B-HAfIk5LSunbW_XkkmKqNXbpH33wzP93J0p9DI1fbjgBUrUfTVhwDcxjg&svctype=4&tempid=h5_group_info"><img alt="QQ Group" src="https://img.shields.io/badge/QQ%20Group-join-12B7F5?logo=qq&logoColor=white"></a>
  <a href="https://x.com/UniXNU_new"><img alt="X" src="https://img.shields.io/badge/X-@UniXNU__new-000000?logo=x&logoColor=white"></a>
</p>

<p align="center">
  English | <a href="README.zh-CN.md">简体中文</a>
</p>

# UniXNU

> **Migration notice:** Update your device repository for shared SoC support and canonical component names. Follow the [migration guide](https://unixnu.com/porting/migration).

> **This fork** is `TongHuaQWQ/UniXNU`, branch `macos`, on top of upstream `feat/macos`. It is the core
> side of a macOS 26.5.2 (25F84) port to the Xiaomi Pad 7 (`uke`, SM7675). The device repository is
> `TongHuaQWQ/macOS-ForUke` and that is the place to start reading; what this branch carries on top of
> `feat/macos`:
>
> - the comparison kernel the fileset prelink reads is pinned to the standalone link
>   (`XNU_KERNEL_CHAINED_FIXUPS=0`); inherited from the defconfig it went down the collection link path,
>   where `-Wl,-undefined,dynamic_lookup` does not apply, and the prelink failed twice with a trimmed
>   export list. With it pinned the pairing names 3470/3826 kext-facing targets with 0 stubs;
> - the prelink reads its same-build naming evidence from a shipped table
>   (`reference-names.json[.gz]`) instead of a re-built symbol-bearing kernel;
> - `/chosen/pram` is the union of both halves rather than the last writer's;
> - `UniXNUPkg` reads the `gUkeMemStatusGuid` table this firmware publishes and shows the last panic on
>   the menu;
> - the bootstrap pass reports the link failure it is expected to hit instead of failing the round;
> - submodule and catalog pins kept consistent with the merged tree (`drivers/ArmCpu`,
>   `drivers/DarwinBoot`, `kits/XnuPrelink` point at their forks in `.gitmodules`).
>
> Use it exactly as upstream: `./unixnu <command> -D <device-repository>`.

## 1. What this is

UniXNU is an independent project to run iOS and macOS on non-Apple ARM64 hardware through UEFI. Like
OpenCore, it is a general UEFI environment and driver-loading system: it loads the drivers a device
needs and boots the OS through a common UEFI layer.

This repository is the **build driver** of that system. `./unixnu` resolves the ARM64, SoC, OS and
device configuration layers, selects component dependencies, assembles a target tree under
`out/<device>/<os_profile>/<config>/tree`, and then runs each step in order: the XNU kernel build (with
the board's archive list), the **prelink** that pairs the built kernel with the original kernelcache
kexts, the **payload** FAT volume, the UEFI **firmware** build, and the **boot image**. It also owns the
shared inputs the device repository pins: `profiles/arch/{arm64,arm64e}`, `profiles/os/<profile>`,
`components.toml` (the component catalog), `feeds.toml` (Apple and edk2 sources), the UEFI package
`package/UniXNUPkg`, and the `drivers/` + `kits/` component submodules.

It is a build-time repository: it produces the kernel image, the payload and the boot image that the
device repository flashes, but nothing from it runs on the device except `UniXNU.efi`.

## 2. Where it sits

It forks **`https://github.com/UniXNU/UniXNU.git`** (this branch `macos` is `feat/macos` plus the
commits listed above).

What pins *this* repository:

| Consumer | Pin | Where |
| --- | --- | --- |
| `TongHuaQWQ/macOS-ForUke` | `UKE_CORE_REPO=TongHuaQWQ/UniXNU`, `UKE_CORE_REF=macos`, checked out beside the device repo as `UniXNU/` | `.github/workflows/build-kernel-min.yml` (`env:` block and the checkout step) |
| `TongHuaQWQ/UniXNU-uke` (superseded) | `core_repository` / `core_ref` inputs; `Allenwdk/UniXNU@uke-gpu` in the older `build-kernel.yml` | `.github/workflows/build-kernel-min.yml`, `.github/workflows/build-kernel.yml` |

What this repository depends on, in-band, at exact pins:

| Dependency | Pin | Where |
| --- | --- | --- |
| `drivers/ArmCpu` → `https://github.com/UniXNU/ArmCpu.git` | submodule `93a5030…`; catalog `revision = "93a5030c5d983d0ef90f0fca93879d6e36ad1ba8"` | `.gitmodules`, `components.toml` (`id = "ArmCpu"`) |
| `drivers/DarwinBoot` → **fork** `https://github.com/TongHuaQWQ/DarwinBoot.git` | submodule `80d1695…`; catalog `revision = "80d1695e9b8f8f83d94ecd04b0d702706dd0f0c9"` | `.gitmodules` (with the reason: the loader reads `<kernel>.lzma` and accepts collection-sized images), `components.toml` |
| `kits/XnuPrelink` → **fork** `https://github.com/TongHuaQWQ/XnuPrelink.git` | submodule `a771457…`; catalog `revision = "a7714579cb9f1243a74abe386dc18a5174da881e"`, `path = "kits/XnuPrelink"` | `.gitmodules` (with the reason: macOS 26 ships no KDK, so the pairing needs hand-reviewed identities per kernelcache build), `components.toml` |

What the device repository adds on top (device `feeds.toml`, first-wins over the submodules):
`sm7675` SoC layer, a board copy of `ArmCpu` (`local = "drivers/ArmCpu"`), a board copy of
`XnuPrelink` (`local = "kits/XnuPrelink"`), the A732 GPU/display forks and the board's UFS and touch
drivers.

## 3. Dependencies

| Input | Comes from | Without it |
| --- | --- | --- |
| Python 3.11+ | python.org / Homebrew | Nothing runs: `./unixnu` is a Python program. |
| `git`, `make`, `clang`, `cmake`, `ninja`, `unifdef`, `mtools`, `dtc` | Xcode command-line tools / Homebrew (`brew install cmake ninja unifdef llvm mtools dtc`); `scripts/linux/setup-toolchain.py` on glibc Linux | The driver checks for these by name and stops; `unifdef` is needed for libdispatch headers, `mtools` for the payload volume, `dtc` for device-tree properties. |
| **macOS + Xcode** (`xcodebuild`, `iphoneos` SDK, MIG) | App Store / developer.apple.com, or a GitHub macOS runner | The **kernel** step cannot run. On Linux, `scripts/linux/setup-toolchain.py` installs clang with the XNU type builtins plus cctools-port ld64/mig/iig to replace Xcode. |
| `xnu` `apple-oss-distributions/xnu` @ `xnu-10063.141.1` (`d8b8029…`) | `feeds.toml` (`name = "xnu"`, plus `darwin`, `driverkit_tag`, `trustcache_tag`) | No kernel source; the kernel step has nothing to build. |
| `libplatform` 316.100.10, `libdispatch` 1477.100.9, `AvailabilityVersions` 141.1, `libpthread` 519.120.4, `IOStorageFamily` `e45fbe3…` | `apple-oss-distributions` (commits pinned in `feeds.toml`) | Missing kernel libraries: `libplatform`/`libdispatch`/`AvailabilityVersions`/`libpthread` are link inputs, `IOStorageFamily` supplies the public storage headers. |
| `corecrypto-2023` | `https://github.com/ONLYA/corecrypto-2023.git` @ `11fba65…` | No source corecrypto provider; configurations with `CONFIG_XNU_CRYPTO_BOOTSTRAP="source"` cannot link. |
| `edk2` = **Mu_Basecore** `microsoft/mu_basecore` @ `release/202608` (`cfb9372…`) plus five submodules | `feeds.toml` | No UEFI package or firmware build. |
| Device repository (`-D ../UniXNU-<device>`) | The board's own Git repository (e.g. `TongHuaQWQ/macOS-ForUke`) | Nothing to configure: `board.toml`, defconfigs, patch series and the archive list all come from there. |
| Target IPSW / kernelcache | `[ipsw] url` in the device `board.toml`, or `--ipsw` / `UNIXNU_IPSW`, or `--kernelcache` / `UNIXNU_KERNELCACHE` | The prelink step has no original collection to pair with; `unixnu ipsw fetch` fails. Apple data, downloadable but large. |
| Mu-Silicium UEFI tree (`uefi-<device>`) | The port's second repository, `--uefi DIR` / `UNIXNU_UEFI`; for uke **not published** — the device repo carries its changes as patches under `firmware/` | No `boot.img`/firmware volume; `build firmware` and `bootimg` cannot produce the firmware half. |
| Trust cache, Data ramdisk, platform seed (`--unique-chip-id`) | Device or IPSW; the seed is **not obtainable from any public source** | The payload step refuses or writes a placeholder the kernel rejects. |
| Network access for `./unixnu fetch` | GitHub | Submodules and Apple/Mu_Basecore sources are not fetched; `unixnu.lock` cannot be written. |

## 4. Build and use

From this checkout, with the device repository beside it (`-D` is remembered in `out/state.json`):

```sh
git clone --recurse-submodules https://github.com/TongHuaQWQ/UniXNU
cd UniXNU
./unixnu defconfig uke-macos_defconfig -D ../macOS-ForUke
./unixnu fetch
./unixnu status --json
./unixnu tree
./unixnu build kernel -D ../macOS-ForUke          # kernel, archives, prelink
./unixnu build payload -D ../macOS-ForUke --kernel <kernel.macho>
./unixnu build firmware --uefi ../uefi-uke -D ../macOS-ForUke
./unixnu bootimg -D ../macOS-ForUke --uefi ../uefi-uke --dtb <firmware.dtb>
```

`./unixnu --help` lists the full command set: `defconfig`, `fetch`, `tree`, `build`
(+ `kernel`, `package`, `firmware`, `payload`, `userdata`, `runtime`, `prelink` shortcuts), `bootimg`,
`vendor_boot`, `ipsw`, `status`, `clean`, `release`. `./unixnu release` runs dependencies, patches,
build steps and the boot image in one pass with a manifest — the same steps
`templates/package.sh` drives in a device repository.

Host checks of the driver itself:

```sh
python3 -m pytest scripts/unixnu            # driver unit tests (test_kernel.py, test_udif.py, test_vendor_boot.py)
python3 scripts/porting-record.py check --device ../macOS-ForUke
```

## 5. See also

- [Port a device](https://unixnu.com/zh/porting/steps) — the eight steps and what each produces; this
  repository is the `UniXNU` row of step 2 and the `./unixnu` commands of steps 4 and 7;
- [Device repository](https://unixnu.com/zh/porting/device-repository) — layout, `board.toml`,
  `feeds.toml`, completion and publishing rules;
- [Packaging](https://unixnu.com/zh/porting/packaging), [drivers](https://unixnu.com/zh/porting/drivers),
  [UEFI firmware](https://unixnu.com/zh/porting/uefi-firmware), [log capture](https://unixnu.com/zh/porting/log-capture);
- [Build and boot](https://unixnu.com/zh/building), [build environment](https://unixnu.com/zh/guide/requirements),
  [CLI reference](https://unixnu.com/zh/reference/cli), [concepts: prelink](https://unixnu.com/zh/concepts/prelink)
  and [boot chain](https://unixnu.com/zh/concepts/boot-chain);
- in this repository: `docs/` (the documentation source for the site), `docs/building.md`,
  `docs/concepts/`, `docs/drivers/`, `docs/porting/`, `components.toml`, `feeds.toml`, `profiles/`.

## Repositories

| Repository | Contents |
| --- | --- |
| [UniXNU](https://github.com/UniXNU/UniXNU) | Build tools, component catalog, ARM64 support, OS profiles, UEFI package, documentation |
| [UniXNU-sm8550-common](https://github.com/UniXNU/UniXNU-sm8550-common) | Shared SM8550 support |
| [UniXNU-sheng](https://github.com/UniXNU/UniXNU-sheng) | Xiaomi Pad 6S Pro |
| [uefi-sheng](https://github.com/UniXNU/uefi-sheng) | UEFI firmware for the Xiaomi Pad 6S Pro |

Clone with `--recurse-submodules`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

The macOS 27 profile follows [macOS-DroidVM](https://github.com/Droid-VM/macOS-DroidVM), the DroidVM port booted with UniXNU, for its kernel patches (the union root volume, code signature pages on a 4K kernel, the 24 MHz timebase, the realtime and mmap fixes, exec denial) and for the account setup in the Data seed.

## License

BSD-2-Clause-Patent. See [LICENSE](LICENSE).
