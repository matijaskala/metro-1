[section target]

arch: x86
arch_desc: x86-32bit

[section portage]

CFLAGS: -O2 -fomit-frame-pointer -mtune=i686 -pipe
CHOST: i686-pc-linux-gnu
HOSTUSE:
