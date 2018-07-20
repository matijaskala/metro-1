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

if which sddm &> /dev/null && test ! -e /etc/sddm.conf
then
	sddm --example-config | sed '/^InputMethod/s/qtvirtualkeyboard//' > /etc/sddm.conf 2> /dev/null
fi

if [ -f /etc/lxdm/lxdm.conf ]
then
	sed -i 's/^[# ]*\(autologin=\).*$/\1liveuser/' /etc/lxdm/lxdm.conf
	sed -i 's/^[# ]*\(gtk_theme=\).*$/\1$[desktop/theme/gtk:zap]/' /etc/lxdm/lxdm.conf
	install -d /var/lib/lxdm
	cat > /var/lib/lxdm/lxdm.conf << EOF
[base]
last_session=__default__
last_lang=
EOF
fi

if [ -f /etc/lightdm/lightdm.conf ]
then
	sed -i 's/^[# ]*\(autologin-user=\).*$/\1liveuser/' /etc/lightdm/lightdm.conf
	sed -i 's/^[# ]*\(autologin-session=\).*$/\1$[desktop/session:zap]/' /etc/lightdm/lightdm.conf
	sed -i 's/^[# ]*\(greeter-session=\).*$/\1$[desktop/lightdm_greeter:zap]/' /etc/lightdm/lightdm.conf
	sed -i 's/^[# ]*\(user-session=\).*$/\1$[desktop/session:zap]/' /etc/lightdm/lightdm.conf
fi

case '$[desktop/lightdm_greeter:lax]' in
	''|lightdm-gtk-greeter)
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
	sed -i 's/^[# ]*\(Current=\).*$/\1breeze/' /etc/sddm.conf
fi

if [ -f /etc/xdg/xfce4/helpers.rc ]
then :
	sed -i 's/firefox/$[desktop/web:zap]/' /etc/xdg/xfce4/helpers.rc
	sed -i 's/thunderbird/$[desktop/mail:zap]/' /etc/xdg/xfce4/helpers.rc
fi

if [ -n '$[desktop/web:lax]' ]
then
	install -d /etc/skel/.local/share/applications || exit 1
	cat > /etc/skel/.local/share/applications/mimeapps.list << EOF
[Default Applications]
text/html=$[desktop/web:zap].desktop
EOF
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
sed -i /^[^#]/d /etc/locale.gen
cat >> /etc/locale.gen << EOF
af_ZA.UTF-8 UTF-8
af_ZA ISO-8859-1
ar_EG.UTF-8 UTF-8
ar_EG ISO-8859-6
ast_ES.UTF-8 UTF-8
ast_ES ISO-8859-15
bg_BG.UTF-8 UTF-8
bg_BG CP1251
bn_BD UTF-8
bs_BA.UTF-8 UTF-8
bs_BA ISO-8859-2
ca_ES.UTF-8 UTF-8
ca_ES ISO-8859-1
ca_ES@euro ISO-8859-15
ca_ES.UTF-8@valencia UTF-8
ca_ES@valencia ISO-8859-15
cs_CZ.UTF-8 UTF-8
cs_CZ ISO-8859-2
cy_GB.UTF-8 UTF-8
cy_GB ISO-8859-14
da_DK.UTF-8 UTF-8
da_DK ISO-8859-1
de_BE.UTF-8 UTF-8
de_BE ISO-8859-1
de_BE@euro ISO-8859-15
de_DE.UTF-8 UTF-8
de_DE ISO-8859-1
de_DE@euro ISO-8859-15
el_GR.UTF-8 UTF-8
el_GR ISO-8859-7
en_GB.UTF-8 UTF-8
en_GB ISO-8859-1
en_US.UTF-8 UTF-8
en_US ISO-8859-1
es_ES.UTF-8 UTF-8
es_ES ISO-8859-1
es_ES@euro ISO-8859-15
et_EE.UTF-8 UTF-8
et_EE ISO-8859-1
et_EE.ISO-8859-15 ISO-8859-15
fa_IR UTF-8
fi_FI.UTF-8 UTF-8
fi_FI ISO-8859-1
fi_FI@euro ISO-8859-15
fr_BE.UTF-8 UTF-8
fr_BE ISO-8859-1
fr_BE@euro ISO-8859-15
fr_FR.UTF-8 UTF-8
fr_FR ISO-8859-1
fr_FR@euro ISO-8859-15
gl_ES.UTF-8 UTF-8
gl_ES ISO-8859-1
gl_ES@euro ISO-8859-15
gu_IN UTF-8
he_IL.UTF-8 UTF-8
he_IL ISO-8859-8
hi_IN UTF-8
hr_HR.UTF-8 UTF-8
hr_HR ISO-8859-2
hu_HU.UTF-8 UTF-8
hu_HU ISO-8859-2
id_ID.UTF-8 UTF-8
id_ID ISO-8859-1
it_IT.UTF-8 UTF-8
it_IT ISO-8859-1
it_IT@euro ISO-8859-15
ja_JP.EUC-JP EUC-JP
ja_JP.UTF-8 UTF-8
ka_GE.UTF-8 UTF-8
ka_GE GEORGIAN-PS
km_KH UTF-8
ko_KR.EUC-KR EUC-KR
ko_KR.UTF-8 UTF-8
ky_KG UTF-8
lo_LA UTF-8
lt_LT.UTF-8 UTF-8
lt_LT ISO-8859-13
mk_MK.UTF-8 UTF-8
mk_MK ISO-8859-5
mr_IN UTF-8
nb_NO.UTF-8 UTF-8
nb_NO ISO-8859-1
nl_BE.UTF-8 UTF-8
nl_BE ISO-8859-1
nl_BE@euro ISO-8859-15
nl_NL.UTF-8 UTF-8
nl_NL ISO-8859-1
nl_NL@euro ISO-8859-15
nn_NO.UTF-8 UTF-8
nn_NO ISO-8859-1
pa_IN UTF-8
pl_PL.UTF-8 UTF-8
pl_PL ISO-8859-2
pt_BR.UTF-8 UTF-8
pt_BR ISO-8859-1
pt_PT.UTF-8 UTF-8
pt_PT ISO-8859-1
pt_PT@euro ISO-8859-15
ro_RO.UTF-8 UTF-8
ro_RO ISO-8859-2
ru_RU.KOI8-R KOI8-R
ru_RU.UTF-8 UTF-8
ru_RU ISO-8859-5
si_LK UTF-8
sk_SK.UTF-8 UTF-8
sk_SK ISO-8859-2
sl_SI.UTF-8 UTF-8
sl_SI ISO-8859-2
sr_RS UTF-8
sr_RS@latin UTF-8
sv_SE.UTF-8 UTF-8
sv_SE ISO-8859-1
ta_IN UTF-8
tg_TJ.UTF-8 UTF-8
tg_TJ KOI8-T
th_TH.UTF-8 UTF-8
th_TH TIS-620
tr_TR.UTF-8 UTF-8
tr_TR ISO-8859-9
uk_UA.UTF-8 UTF-8
uk_UA KOI8-U
vi_VN.TCVN TCVN5712-1
vi_VN UTF-8
wa_BE ISO-8859-1
wa_BE@euro ISO-8859-15
wa_BE.UTF-8 UTF-8
xh_ZA.UTF-8 UTF-8
xh_ZA ISO-8859-1
zh_CN.GB18030 GB18030
zh_CN.GBK GBK
zh_CN.UTF-8 UTF-8
zh_CN GB2312
zh_TW.EUC-TW EUC-TW
zh_TW.UTF-8 UTF-8
zh_TW BIG5
zu_ZA.UTF-8 UTF-8
zu_ZA ISO-8859-1
EOF
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

rm -rf /usr/src/linux-* /usr/src/linux || exit 1
]
