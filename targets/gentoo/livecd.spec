[collect ./source/stage3.spec]
[collect ./target/stage4.spec]
[collect ./steps/capture/livecd.spec]

[section stage4]

target/name: livecd

[section steps]

chroot/run: [
#!/bin/bash
$[[steps/setup]]

emerge --oneshot $eopts portage || exit 1
export USE="$[portage/USE] bindist"
emerge -DNu $eopts @world || exit 1
emerge -DNu $eopts $[emerge/packages:zap] || exit 1
emerge --noreplace $eopts $[emerge/packages/livecd:zap] || exit 1

echo > /etc/fstab || exit 1
ln -sf /proc/self/mounts /etc/mtab || exit 1
emerge $eopts --noreplace --oneshot sys-kernel/genkernel-next $[livecd/kernel/package] || exit 1
echo "CONFIG_OVERLAY_FS=y" >> /usr/share/genkernel/arch/x86_64/kernel-config || exit 1
sed -i 's/^[# ]*SPLASH=".*"$/SPLASH="yes"/' /etc/genkernel.conf
sed -i 's/^[# ]*SPLASH_THEME=".*"$/SPLASH_THEME="bstheme-tuxosx"/' /etc/genkernel.conf
genkernel $[livecd/kernel/opts:lax] \
	--cachedir=/var/tmp/cache/kernel \
	--modulespackage=/var/tmp/cache/kernel/modules.tar.bz2 \
	--minkernpackage=/var/tmp/cache/kernel/kernel-initrd.tar.bz2 \
	all || exit 1

echo 'hostname="slontoo"' > /etc/conf.d/hostname

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

which sddm &> /dev/null && ! [ -e /etc/sddm.conf ] && sddm --example-config > /etc/sddm.conf 2> /dev/null

if [ -f /etc/lxdm/lxdm.conf ]
then
	sed -i 's/^[# ]*\(autologin=\).*$/\1liveuser/' /etc/lxdm/lxdm.conf
	sed -i 's/^[# ]*\(gtk_theme=\).*$/\1$[desktop/theme/gtk:zap]/' /etc/lxdm/lxdm.conf
fi

if [ -f /etc/lightdm/lightdm.conf ]
then
	sed -i 's/^[# ]*\(autologin-user=\).*$/\1liveuser/' /etc/lightdm/lightdm.conf
	sed -i 's/^[# ]*\(autologin-session=\).*$/\1$[desktop/session:zap]/' /etc/lightdm/lightdm.conf
	sed -i 's/^[# ]*\(greeter-session=\).*$/\1$[desktop/lightdm_greeter:zap]/' /etc/lightdm/lightdm.conf
	sed -i 's/^[# ]*\(user-session=\).*$/\1$[desktop/session:zap]/' /etc/lightdm/lightdm.conf
fi

case '$[desktop/lightdm_greeter:lax]' in
	lightdm-gtk-greeter)
		if [ -f /etc/lightdm/lightdm-gtk-greeter.conf ]
		then
			sed -i 's/^[# ]*\(background=\).*$/\1#295377/' /etc/lightdm/lightdm-gtk-greeter.conf
			sed -i 's/^[# ]*\(theme-name=\).*$/\1$[desktop/theme/gtk:zap]/' /etc/lightdm/lightdm-gtk-greeter.conf
			sed -i 's/^[# ]*\(icon-theme-name=\).*$/\1$[desktop/theme/icons:zap]/' /etc/lightdm/lightdm-gtk-greeter.conf
		fi
	;;
	lightdm-webkit-greeter)
		sed -i 's/^[# ]\(webkit-theme=\).*$/\1$[desktop/lightdm_theme:zap]/' /etc/lightdm/lightdm-webkit-greeter.conf
	;;
	slick-greeter)
		install -d /etc/lightdm
		cat > /etc/lightdm/slick-greeter.conf << EOF
[Greeter]
background=#295377
theme-name=$[desktop/theme/gtk:zap]
icon-theme-name=$[desktop/theme/icons:zap]
EOF
	;;
esac

if [ -e /etc/sddm.conf ]
then
	sed -i 's/^[# ]*\(User=\).*$/\1liveuser/' /etc/sddm.conf
	sed -i 's/^[# ]*\(Session=\).*$/\1$[desktop/session:zap]/' /etc/sddm.conf
fi

if [ -f /etc/xdg/xfce4/helpers.rc ]
then :
	sed -i 's/firefox/$[desktop/web:zap]/' /etc/xdg/xfce4/helpers.rc
	sed -i 's/thunderbird/$[desktop/mail:zap]/' /etc/xdg/xfce4/helpers.rc
fi

if [ -f /etc/xdg/lxpanel/default/panels/panel ]
then
	install -d /etc/skel/.config/lxpanel/LXDE/panels
	cp /etc/xdg/lxpanel/default/panels/panel /etc/skel/.config/lxpanel/LXDE/panels/panel
	sed -i 's/background=1/background=0/' /etc/skel/.config/lxpanel/LXDE/panels/panel
	sed -i 's/usefontcolor=1/usefontcolor=0/' /etc/skel/.config/lxpanel/LXDE/panels/panel
fi

install -d /etc/skel/.config/compiz/compizconfig
cat > /etc/skel/.config/compiz/compizconfig/Default.ini << EOF
[decoration]
as_command = gtk-window-decorator

[core]
as_active_plugins = core;decoration;imgjpeg;move;place;png;resize;svg;text;wall;

EOF

if [ '$[desktop/session:lax]' = xfce ]
then
	install -d /etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml
	cat > /etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml << EOF
<?xml version="1.0" encoding="UTF-8"?>

<channel name="xfce4-desktop" version="1.0">
  <property name="desktop-icons" type="empty">
    <property name="file-icons" type="empty">
      <property name="show-trash" type="bool" value="false"/>
    </property>
  </property>
</channel>
EOF
	cat > /etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml << EOF
<?xml version="1.0" encoding="UTF-8"?>

<channel name="xfce4-panel" version="1.0">
  <property name="configver" type="int" value="2"/>
  <property name="panels" type="array">
    <value type="int" value="1"/>
    <value type="int" value="2"/>
    <property name="panel-1" type="empty">
      <property name="position" type="string" value="p=6;x=0;y=0"/>
      <property name="length" type="uint" value="100"/>
      <property name="position-locked" type="bool" value="true"/>
      <property name="size" type="uint" value="30"/>
      <property name="plugin-ids" type="array">
        <value type="int" value="1"/>
        <value type="int" value="15"/>
        <value type="int" value="6"/>
        <value type="int" value="5"/>
        <value type="int" value="2"/>
      </property>
    </property>
    <property name="panel-2" type="empty">
      <property name="position" type="string" value="p=8;x=0;y=0"/>
      <property name="length" type="uint" value="100"/>
      <property name="position-locked" type="bool" value="true"/>
      <property name="size" type="uint" value="30"/>
      <property name="plugin-ids" type="array">
        <value type="int" value="7"/>
        <value type="int" value="3"/>
        <value type="int" value="16"/>
        <value type="int" value="4"/>
        <value type="int" value="8"/>
      </property>
    </property>
  </property>
  <property name="plugins" type="empty">
    <property name="plugin-1" type="string" value="applicationsmenu"/>
    <property name="plugin-2" type="string" value="actions">
      <property name="items" type="array">
        <value type="string" value="+lock-screen"/>
        <value type="string" value="+switch-user"/>
        <value type="string" value="+separator"/>
        <value type="string" value="+suspend"/>
        <value type="string" value="+hibernate"/>
        <value type="string" value="+separator"/>
        <value type="string" value="+shutdown"/>
        <value type="string" value="+restart"/>
        <value type="string" value="+separator"/>
        <value type="string" value="+logout-dialog"/>
      </property>
    </property>
    <property name="plugin-3" type="string" value="tasklist"/>
    <property name="plugin-15" type="string" value="separator">
      <property name="expand" type="bool" value="true"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-16" type="string" value="separator">
      <property name="expand" type="bool" value="true"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-4" type="string" value="pager"/>
    <property name="plugin-5" type="string" value="clock"/>
    <property name="plugin-6" type="string" value="systray"/>
    <property name="plugin-7" type="string" value="showdesktop"/>
    <property name="plugin-8" type="string" value="thunar-tpa"/>
  </property>
</channel>
EOF
fi

useradd -c "Live Session User" -mp "" -G audio,users,video,wheel liveuser
add_installer() {
	if [ -f "/usr/share/applications/$1.desktop" ]
	then
		install -o liveuser -g liveuser -d /home/liveuser/Desktop
		install -o liveuser -g liveuser /usr/share/applications/$1.desktop /home/liveuser/Desktop
#		sed -i 's/^\(Name=\).*/\1Install Slontoo/' /home/liveuser/Desktop/$1.desktop
#		sed -i 's/^\(Comment=\).*/\1Install the operating system to disk/' /home/liveuser/Desktop/$1.desktop
#		sed -i 's/^\(Icon=\).*/\1drive-harddisk/' /home/liveuser/Desktop/$1.desktop
	fi
}
add_installer calamares
add_installer debian-installer-launcher
sed -i 's/^[# ]*\(%wheel ALL=(ALL) ALL\)$/\1/' /etc/sudoers

XKB_LAYOUT=$[locale/xkb:zap]
if [ -n "$XKB_LAYOUT" ]
then
	install -d /etc/X11/xorg.conf.d
	cat > /etc/X11/xorg.conf.d/00-keyboard.conf << EOF
Section "InputClass"
        Identifier "system-keyboard"
        MatchIsKeyboard "on"
        Option "XkbLayout" "$XKB_LAYOUT"
EndSection
EOF
fi

CURSOR_THEME=$[desktop/theme/cursors]
if [ -n "$CURSOR_THEME" ]
then
	install -d /usr/share/cursors/xorg-x11/default
	cat > /usr/share/cursors/xorg-x11/default/index.theme << EOF
[Icon Theme]
Inherits=$CURSOR_THEME
EOF
fi

#cat > /sbin/setup << EOF
##!/bin/sh
#curl https://raw.githubusercontent.com/matijaskala/funtoo-utils/master/setup > /tmp/setup || exit 1
#chmod +x /tmp/setup || exit 1
#exec sudo /tmp/setup \$@
#EOF
#cat > /sbin/post_unpack << EOF
##!/bin/sh
#userdel -r -f -R "\$1" liveuser
#[ -f "\$1/sbin/setup" ] && rm "\$1/sbin/setup"
#[ -f "\$1/sbin/post_unpack" ] && rm "\$1/sbin/post_unpack"
#EOF
#chmod +x /sbin/setup
#chmod +x /sbin/post_unpack

sed -i 's/keymap="us"/keymap="$[locale/keymap:zap]"/' /etc/conf.d/keymaps
grep -q "$[locale/lang:zap]" /etc/locale.gen || echo "$[locale/lang:zap].UTF-8 UTF-8" >> /etc/locale.gen
echo "LANG=$[locale/lang:zap].utf8" > /etc/env.d/02locale
rm -rf /etc/localtime && cp /usr/share/zoneinfo/$[locale/timezone:zap] /etc/localtime || exit 1

WALLPAPER_PATH=$[desktop/theme/wallpaper:zap]
test -e "$WALLPAPER_PATH" || WALLPAPER_PATH=`find /usr/share/backgrounds -name $[desktop/theme/wallpaper:zap] | head -n1`
test -n "$WALLPAPER_PATH" || WALLPAPER_PATH=$[desktop/theme/wallpaper:zap]
case '$[desktop/session:lax]' in
xfce)
	sed -i 's/"ThemeName" type="empty"/"ThemeName" type="string" value="$[desktop/theme/gtk:zap]"/' /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml
	sed -i 's/"IconThemeName" type="empty"/"IconThemeName" type="string" value="$[desktop/theme/icons:zap]"/' /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml
;;
lxde)
#	sed -i 's/\(window_manager=\)openbox-lxde/\1fusion-icon/' /etc/xdg/lxsession/LXDE/desktop.conf
	sed -i 's/\(sNet\/ThemeName=\).*/\1$[desktop/theme/gtk:zap]/' /etc/xdg/lxsession/LXDE/desktop.conf
	sed -i 's/\(sNet\/IconThemeName=\).*/\1$[desktop/theme/icons:zap]/' /etc/xdg/lxsession/LXDE/desktop.conf
	test -n "$WALLPAPER_PATH" && sed -i "s:\(wallpaper=\).*:\1$WALLPAPER_PATH:" /etc/xdg/pcmanfm/LXDE/pcmanfm.conf
;;
mate)
	sed -i 's/Menta/$[desktop/theme/gtk:zap]/' /usr/share/glib-2.0/schemas/org.mate.interface.gschema.xml
	sed -i 's/menta/$[desktop/theme/icons:zap]/' /usr/share/glib-2.0/schemas/org.mate.interface.gschema.xml
	sed -i 's/Menta/$[desktop/theme/marco:zap]/' /usr/share/glib-2.0/schemas/org.mate.marco.gschema.xml
	test -n "$WALLPAPER_PATH" && sed -i "s:>'/usr/share/backgrounds/mate/.*'</:>'$WALLPAPER_PATH'</:" /usr/share/glib-2.0/schemas/org.mate.background.gschema.xml
	glib-compile-schemas /usr/share/glib-2.0/schemas
;;
*)
	sed -i 's/\(gtk-theme-name \?= \?\).*/\1$[desktop/theme/gtk:zap]/' /etc/gtk-3.0/settings.ini
	sed -i 's/\(gtk-icon-theme-name \?= \?\).*/\1$[desktop/theme/icons:zap]/' /etc/gtk-3.0/settings.ini
	echo 'gtk-theme-name = "$[desktop/theme/gtk:zap]"' >> /etc/gtk-2.0/gtkrc
	echo 'gtk-icon-theme-name = "$[desktop/theme/icons:zap]"' >> /etc/gtk-2.0/gtkrc
;;
esac

sed -i 's/\(theme=\)Default/\1$[desktop/theme/xfwm:zap]/' /usr/share/xfwm4/defaults

case '$[desktop/session:lax]' in
lxde)
	sed -i 's/Onyx/$[desktop/theme/openbox:zap]/' /etc/xdg/openbox/LXDE/rc.xml
;;
lxqt)
	sed -i 's/Onyx/$[desktop/theme/openbox:zap]/' /etc/xdg/openbox/lxqt-rc.xml
;;
*)
	sed -i '/<theme>/{n; s@<name>.*</name>@<name>$[desktop/theme/openbox:zap]</name>@}' /etc/xdg/openbox/rc.xml
;;
esac

if [ '$[desktop/session:lax]' = lumina ] ; then :
	sed -i 's@\(session\.styleFile:..*$\)@\1/usr/share/fluxbox/styles/$[desktop/theme/fluxbox:zap]@' /usr/share/lumina-desktop/fluxbox-init-rc
fi

emerge --depclean --with-bdeps=n

sed -i 's@Icon=display@Icon=preferences-desktop-display@' /usr/share/applications/lxrandr.desktop
sed -i 's@Icon=/usr/share/applications/tilda@Icon=/usr/share/pixmaps/tilda@' /usr/share/applications/tilda.desktop
sed -i 's@Icon=media-cdrom@Icon=media-optical@' /usr/share/applications/xfburn.desktop

if [ -n '$[desktop/web:lax]' ] ; then
install -d /etc/skel/.local/share/applications/mimeapps.list || exit 1
cat > /etc/skel/.local/share/applications/mimeapps.list << EOF
[Default Applications]
text/html=$[desktop/web:zap].desktop
EOF
fi

rm -rf /usr/src/linux-* /usr/src/linux || exit 1
]
