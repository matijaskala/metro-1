[section path/mirror]

target/basename: $[target/name].iso
target/latest: $[target/name/latest].iso
target/full_latest: $[target/name/full_latest].iso

[section steps]

capture: [
#!/bin/bash

# create cd root
cdroot=$[path/mirror/target]
cdroot=${cdroot%.*}
if [ ! -d $cdroot ]
then
	install -d $cdroot || exit 1
fi
touch $cdroot/livecd

# create livecd filesystem with squashfs
squashout=$cdroot/image.squashfs
mksquashfs $[path/chroot/stage] $squashout -comp $[target/compression]
if [ $? -ge 1 ]
then
	rm -f "$squashout" "$cdroot" "$[path/mirror/target]"
	exit 1
fi

# copy bootloader and kernel
install -d $cdroot/isolinux || exit 1
cp "/usr/share/syslinux/isolinux.bin" "$cdroot/isolinux" || exit 1
for module in $[livecd/isolinux/modules:lax] ; do
cp "/usr/share/syslinux/$module.c32" "$cdroot/isolinux" || exit 1
done
cp -T $[path/chroot/stage]/boot/kernel* $cdroot/isolinux/kernel || exit 1
cp -T $[path/chroot/stage]/boot/initramfs* $cdroot/isolinux/initramfs || exit 1
cp -T $[path/chroot/stage]/boot/System.map* $cdroot/isolinux/System.map || exit 1

cat > $cdroot/isolinux/isolinux.cfg << "EOF"
prompt 1
timeout 30
default $[target/build]

label $[target/build]
  kernel kernel
  append root=/dev/ram0 looptype=squashfs loop=/image.squashfs cdroot dosshd overlayfs quiet
  append root=/dev/ram0 looptype=squashfs loop=/image.squashfs cdroot dosshd overlayfs quiet passwd=$[livecd/passwd:zap]
  initrd initramfs
EOF

# install memtest boot option
if test "$[livecd/memtest?]" = "yes" && test -f "$[livecd/memtest:lax]"; then
	cp "$[livecd/memtest]" "$cdroot/isolinux/$(basename "$[livecd/memtest]")"
	cat >> $cdroot/isolinux/isolinux.cfg << EOF

label memtest
  kernel $(basename "$[livecd/memtest]")
EOF
fi

# create iso image
mkisofs -r -J -l \
	-o $[path/mirror/target] \
	-b isolinux/isolinux.bin \
	-c isolinux/boot.cat \
	-no-emul-boot -boot-load-size 4 -boot-info-table \
	$cdroot/ || exit 1

isohybrid $[path/mirror/target]

rm -rf $cdroot || exit 1
]
