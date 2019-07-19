[collect ./source/stage2.spec]
[collect ./target/stage3.spec]
[collect ./steps/capture/tar.spec]

[section steps]

chroot/run: [
#!/bin/bash
$[[steps/setup]]

# use python2 if available - if not available, assume we are OK with python3
a=$(eselect python list | sed -n -e '1d' -e 's/^.* \(python[23]\..\).*$/\1/g' -e '/python2/p')
# if python2 is available, "$a" should be set to something like "python2.6":
if [ "$a" != "" ]
then
	eselect python set $a
fi

emerge --oneshot $eopts portage || exit 1
export USE="$[portage/USE] bindist"
export SHELL="/bin/bash"
# handle perl upgrades
perl-cleaner --modules || exit 1
emerge $eopts -e system $[emerge/packages/first:lax] || exit 1

# zap the world file and emerge packages
rm -f /var/lib/portage/world || exit 2

emerge $eopts $[emerge/packages:zap] || exit 1

# add default runlevel services
services=""
services="$[baselayout/services:zap]"

for service in $services
do
	s=${service%%:*}
	l=${service##*:}
	[ "$l" == "$s" ] && l="default"
	[ -x /sbin/rc-update ] && rc-update add $s ${l}
	if [ "$l" = "default" ] && [ -x /usr/bin/systemctl ]
	then
		case "$s" in
			xdm)
				systemctl enable $[desktop/login:zap]
				;;
			*)
				systemctl enable $s
				;;
		esac
	fi
done

[ -f /etc/conf.d/xdm ] && sed -i 's/\(DISPLAYMANAGER=\)".*"/\1"$[desktop/login:zap]"/' /etc/conf.d/xdm

[ -e /usr/share/eselect/modules/vi.eselect ] && eselect vi update --if-unset
[ -e /usr/bin/vi ] || [ -e /bin/vi ] || [ ! -e /bin/busybox ] || ln -s busybox /bin/vi || exit 1
[ -e /usr/bin/vi ] || [ -e /bin/vi ] || [ ! -e /usr/bin/vim ] || ln -s vim /usr/bin/vi || exit 1

$[[steps/chroot/run/extra:lax]]
]

[section portage]

ROOT: /
