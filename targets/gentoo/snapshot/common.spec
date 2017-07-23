# Common stuff used when actually building a snapshot
[collect ./global.spec]

[section target]

name: $[portage/name/full]

# This defines what internal Metro class is used to build this target
class: snapshot

[section trigger]

ok/run: [
#!/bin/bash
# CREATE latest symlink for the snapshot
snapshot_suffix=".$[snapshot/compression]"
[ "$[snapshot/compression]" = none ] && snapshot_suffix=
ln -sf $[portage/name/full].tar$snapshot_suffix $[path/mirror]/$[path/mirror/snapshot/subpath]/$[portage/name]-$[path/mirror/link/suffix].tar$snapshot_suffix || exit 3
]

[section steps]

run: [
#!/bin/bash

die() {
	rm -f $[path/mirror/tarout]*
	echo "$*"
	exit 1
}

# On keyboard interrupt, clean up our partially-completed file...
trap "die Removing incomplete $[path/mirror/tarout]..." INT

$[[steps/sync]]

echo "Creating $[path/mirror/tarout]..."
install -d `dirname $[path/mirror/tarout]` || die "Couldn't create output directory"
tarout="$[path/mirror/tarout]"

$[[steps/create]]

echo "Compressing $tarout..."
snapshot_suffix=".$[snapshot/compression]"
case "$[snapshot/compression]" in
none)
	snapshot_suffix=
	;;
bz2)
	if [ -e /usr/bin/pbzip2 ]
	then
		pbzip2 -p4 $tarout || die "Snapshot pbzip2 failure"
	else
		bzip2 $tarout || die "Snapshot bzip2 failure"
	fi
	;;
gz)
	gzip -9 $tarout || die "Snapshot gzip failure"
	;;
xz)
	if [ -e /usr/bin/pxz ]; then
		/usr/bin/pxz $tarout || die "Snapshot pxz failure"
	else
		xz $tarout || die "Snapshot xz failure"
	fi
	;;
*)
	echo "Unrecognized compression format $[snapshot/compression] specified for snapshot."
	exit 1
	;;
esac
echo "Snapshot $[path/mirror/tarout]$snapshot_suffix created."
]
